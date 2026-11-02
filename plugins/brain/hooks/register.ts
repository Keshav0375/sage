import { parseRegistry, resolveCwd, renderCard, renderBoard, expandHome } from './registry.ts'
import { checkBash } from './guard.ts'
import { parseRoutingConfig, routeModel, leafDecision, writeAllowed } from './routing.ts'
import {
  parseHeader, isTicketKey, parseReport, staleChecks, ticketPaths, ticketOfPath, shipTarget, shipBlock,
  parseClaim, claimedByOther, fixAttempts, deriveStep, renderRuns, updateTicket, activeTickets, CHECKS, CLAIM_MS,
} from './ledger.ts'

// Reads context/registry.json. Returns undefined when context_dir is unset or the file is missing.
async function loadRegistry($, contextDir) {
  if (!contextDir) return undefined
  const path = `${contextDir}/registry.json`
  if (!(await $.fs.exists(path))) return undefined
  return parseRegistry(await $.fs.read(path))
}

// The project card for one project, with repo existence and STATE.md highlights.
async function projectCard($, contextDir, reg, home, name, match) {
  const exists = {}
  for (const [repo, raw] of Object.entries(reg.projects[name]?.repos ?? {})) {
    exists[repo] = await $.fs.exists(expandHome(raw, home))
  }
  const statePath = `${contextDir}/projects/${name}/STATE.md`
  const state = (await $.fs.exists(statePath)) ? await $.fs.read(statePath) : undefined
  const trackerPath = `${contextDir}/projects/${name}/tracker.json`
  const tracker = (await $.fs.exists(trackerPath)) ? await $.fs.read(trackerPath) : undefined
  return renderCard(reg, name, home, exists, state, match, tracker)
}

// The context text for the session's working directory.
async function contextFor($, contextDir, cwd) {
  if (!contextDir) return 'brain: context_dir is not set. Run /brain:setup.'
  const home = (await $.env.get('HOME')) ?? ''
  const reg = await loadRegistry($, contextDir)
  if (!reg) return `brain: no registry at ${contextDir}/registry.json. Run /brain:setup.`
  const match = resolveCwd(reg, cwd, home)
  if (match) return await projectCard($, contextDir, reg, home, match.project, match)
  const brainRoot = contextDir.replace(/\/context\/?$/, '')
  if (cwd === brainRoot || cwd.startsWith(brainRoot + '/')) {
    return `You are in the harness repo (context at ${contextDir}). Architecture planning happens here.\n${renderBoard(reg, home)}`
  }
  return `Directory ${cwd} is not in the registry. Run /brain:register to add it to a project.`
}

async function readOr($, path) {
  return (await $.fs.exists(path)) ? await $.fs.read(path) : undefined
}

async function headOf($, worktree) {
  if (!(await $.fs.exists(worktree))) return undefined
  const r = await $.process.run(['git', '-C', worktree, 'rev-parse', 'HEAD'])
  return r.exitCode === 0 ? r.stdout.trim() : undefined
}

// The ledger rows for every in-progress or blocked ticket, from the trackers and the files on disk.
async function collectRuns($, contextDir, reg, only) {
  const rows = []
  for (const project of Object.keys(reg.projects)) {
    if (only && project !== only) continue
    const tracker = await readOr($, `${contextDir}/projects/${project}/tracker.json`)
    if (!tracker) continue
    for (const t of activeTickets(tracker)) {
      const p = ticketPaths(contextDir, project, t.ticket)
      const reports = {}
      for (const name of CHECKS) reports[name] = await readOr($, p.report(name))
      const head = await headOf($, p.worktree)
      const step = deriveStep({
        status: t.status, pr: t.pr, hasContext: await $.fs.exists(p.context),
        hasWorktree: await $.fs.exists(p.worktree), head, reports, verdict: await readOr($, p.verdict),
      })
      rows.push({ project, ticket: t.ticket, title: t.title, step, attempts: fixAttempts(await readOr($, p.log)), claim: parseClaim(await readOr($, p.claim)) })
    }
  }
  return rows
}

async function runsText($, contextDir, only) {
  const reg = contextDir ? await loadRegistry($, contextDir) : undefined
  if (!reg) return undefined
  return renderRuns(await collectRuns($, contextDir, reg, only), await $.session.id(), Date.now())
}

// Ledger checks for a builder agent spawn. Returns { deny } or { model } (an escalation) or {}.
async function ledgerSpawn($, contextDir, e) {
  const h = parseHeader(String(e.prompt ?? ''))
  if (!h.project || !isTicketKey(h.ticket)) {
    return { deny: 'Builder agents work on one ticket. Start the prompt with the lines "project: <p>" and "ticket: <E1-T1>" (and "worktree: <path>" after branching).' }
  }
  const p = ticketPaths(contextDir, h.project, h.ticket)
  const session = await $.session.id()
  const now = Date.now()
  const claim = parseClaim(await readOr($, p.claim))
  if (claimedByOther(claim, session, now)) {
    return { deny: `Ticket ${h.ticket} is claimed by another session until ${new Date(claim.expires).toISOString()}. Pick another ticket.` }
  }
  if (e.subagentType === 'builder:verifier') {
    const head = await headOf($, h.worktree ?? p.worktree)
    if (!head) return { deny: `No worktree with commits for ${h.ticket}. Branch and edit first.` }
    const reports = {}
    for (const name of CHECKS) reports[name] = await readOr($, p.report(name))
    const stale = staleChecks(reports, head)
    if (stale.length) return { deny: `The verifier needs fresh reports for HEAD ${head.slice(0, 7)}. Missing or stale: ${stale.map((n) => n + '.md').join(', ')}. Run those checkers first.` }
  }
  const log = await readOr($, p.log)
  const mode = h.mode ?? (String(e.prompt).match(/mode=(\w+)/)?.[1])
  await $.fs.write(p.claim, JSON.stringify({ session, expires: now + CLAIM_MS }) + '\n')
  await $.fs.write(p.log, (log ?? '') + JSON.stringify({ ts: new Date(now).toISOString(), session, agent: e.subagentType, mode, ticket: h.ticket }) + '\n')
  // Escalation: the second and later fix loops run the editor on the main model.
  if (e.subagentType === 'builder:editor' && mode === 'fix' && fixAttempts(log) >= 1 && !e.model) return { model: 'opus' }
  return {}
}

// The ship gate: a push or PR from a ticket worktree needs a GREEN verdict for its HEAD.
async function shipGate($, contextDir, command) {
  const target = shipTarget(command)
  if (!target || !contextDir) return undefined
  let found = target.path ? ticketOfPath(contextDir, target.path) : undefined
  if (!found && target.branch) {
    const key = target.branch.match(/([A-Z]\d+-T\d+)/)?.[1]
    if (key) {
      const root = `${contextDir}/.runtime/worktrees`
      for (const entry of (await $.fs.exists(root)) ? await $.fs.list(root) : []) {
        if (await $.fs.exists(`${root}/${entry.name}/${key}`)) found = { project: entry.name, ticket: key }
      }
    }
  }
  if (!found && !target.path) found = ticketOfPath(contextDir, await $.session.cwd())
  if (!found) return undefined
  const p = ticketPaths(contextDir, found.project, found.ticket)
  const reason = shipBlock(await readOr($, p.verdict), await headOf($, p.worktree))
  return reason ? `Ship gate (${found.ticket}): ${reason}` : undefined
}

let trackerWrites = Promise.resolve()

// Subagent id → type, filled at spawn, read by the write guard.
const agentTypes = new Map()

async function loadRoutingConfig($, contextDir) {
  const path = `${contextDir}/routing.json`
  if (!contextDir || !(await $.fs.exists(path))) return { agents: {}, leaves: [], leafModel: 'haiku', reportOnly: [] }
  return parseRoutingConfig(await $.fs.read(path))
}

export function register(on, options) {
  const contextDir = options?.context_dir ? String(options.context_dir).replace(/\/$/, '') : ''
  const mainModel = String(options?.main_model ?? 'opus')
  const subagentModel = String(options?.subagent_model ?? 'sonnet')

  on('session.start', async ($, e, next) => {
    await $.tool.register({
      name: 'where',
      description: 'Project card: the project, its local repo paths, open decisions. Omit "project" to resolve from the working directory.',
      inputSchema: { type: 'object', properties: { project: { type: 'string' } } },
    })
    await $.tool.register({
      name: 'projects',
      description: 'Every registered project with status and local repo paths.',
    })
    await $.tool.register({
      name: 'run_status',
      description: 'Builder ledger: each in-progress or blocked ticket, the step it reached (from the files and git on disk), fix loops, claims, and the next action. Use it to resume.',
      inputSchema: { type: 'object', properties: { project: { type: 'string' } } },
    })
    await $.tool.register({
      name: 'ticket_update',
      description: 'Change one ticket in tracker.json (status, branch, pr) with one locked write. Use it instead of editing tracker.json during a build.',
      inputSchema: {
        type: 'object',
        required: ['project', 'ticket', 'fields'],
        properties: { project: { type: 'string' }, ticket: { type: 'string' }, fields: { type: 'object' } },
      },
    })
    return next(e)
  })

  // Context: the project card goes into the first message of each conversation.
  on('prompt.context', async ($, e, next) => {
    const text = await contextFor($, contextDir, await $.session.cwd())
    const runs = await runsText($, contextDir)
    const blocks = [...e.blocks, { name: 'project', text }]
    if (runs && !runs.startsWith('No unfinished')) blocks.push({ name: 'builder-runs', text: runs })
    return next({ ...e, blocks })
  })

  // Compaction keeps the run state, so a long build resumes at the right step.
  on('session.compact', async ($, e, next) => {
    const runs = await runsText($, contextDir)
    if (!runs || runs.startsWith('No unfinished')) return next(e)
    const keep = `Keep this builder run state word for word in the summary:\n${runs}`
    return next({ ...e, instructions: e.instructions ? `${e.instructions}\n\n${keep}` : keep })
  })

  on('tool.call', { tool: 'mcp__brain__run_status' }, async ($, e) => {
    return { result: (await runsText($, contextDir, e.project)) ?? 'No registry. Run /brain:setup.' }
  })

  on('tool.call', { tool: 'mcp__brain__ticket_update' }, async ($, e) => {
    if (!contextDir) return { result: 'No registry. Run /brain:setup.' }
    const path = `${contextDir}/projects/${e.project}/tracker.json`
    const write = trackerWrites.then(async () => {
      const text = await $.fs.read(path)
      await $.fs.write(path, updateTicket(text, String(e.ticket), e.fields ?? {}, new Date().toISOString().slice(0, 10)))
      if (['review', 'done', 'blocked'].includes(String(e.fields?.status))) {
        const p = ticketPaths(contextDir, e.project, String(e.ticket))
        if (await $.fs.exists(p.dir)) await $.fs.write(p.claim, JSON.stringify({ session: await $.session.id(), expires: 0 }) + '\n')
      }
    })
    trackerWrites = write.catch(() => {})
    try {
      await write
      return { result: `Updated ${e.ticket}: ${JSON.stringify(e.fields)}` }
    } catch (err) {
      return { result: `Not updated: ${err instanceof Error ? err.message : String(err)}` }
    }
  })

  on('tool.call', { tool: 'mcp__brain__where' }, async ($, e) => {
    const home = (await $.env.get('HOME')) ?? ''
    const reg = await loadRegistry($, contextDir)
    if (!reg) return { result: 'No registry. Run /brain:setup.' }
    if (!e.project) return { result: await contextFor($, contextDir, await $.session.cwd()) }
    return { result: await projectCard($, contextDir, reg, home, e.project) }
  })

  on('tool.call', { tool: 'mcp__brain__projects' }, async ($) => {
    const home = (await $.env.get('HOME')) ?? ''
    const reg = await loadRegistry($, contextDir)
    return { result: reg ? renderBoard(reg, home) : 'No registry. Run /brain:setup.' }
  })

  // Execution guard: destructive commands and Claude attribution never run.
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const reason = checkBash(String(e.command ?? '')) ?? (await shipGate($, contextDir, String(e.command ?? '')))
    if (reason) return { deny: reason }
    return next(e)
  })

  // Keshav is the sole author: no attribution trailer or PR footer.
  on('attribution.text', async ($, e, next) => {
    if (e.kind === 'commit' || e.kind === 'pr') return { text: '' }
    return next(e)
  })

  // Model routing for subagents: the orchestrator's explicit choice, then context/routing.json,
  // then the subagent_model option.
  on('agent.spawn', async ($, e, next) => {
    const cfg = await loadRoutingConfig($, contextDir)
    const record = async (spawn) => {
      const r = await next(spawn)
      if (r?.agentId) agentTypes.set(r.agentId, String(spawn.subagentType))
      return r
    }
    // Depth 2: leaf agents only, always on the leaf model.
    const leaf = leafDecision(String(e.subagentType), e.parentAgentId, cfg)
    if (leaf.deny) return { deny: leaf.deny }
    if (leaf.model) return record({ ...e, model: leaf.model })
    if (contextDir && String(e.subagentType).startsWith('builder:')) {
      const r = await ledgerSpawn($, contextDir, e)
      if (r.deny) return { deny: r.deny }
      if (r.model) return record({ ...e, model: r.model })
    }
    const model = routeModel(e.subagentType, e.model, cfg.agents, subagentModel)
    return record(model ? { ...e, model } : e)
  })

  // Report-only agents (scouts, skeptics, reviewers) may write only their reports under .runtime/.
  for (const tool of ['Write', 'Edit']) {
    on('tool.call', { tool }, async ($, e, next) => {
      if (!e.agentId || !contextDir) return next(e)
      const cfg = await loadRoutingConfig($, contextDir)
      const path = String(e.file_path ?? '')
      if (!writeAllowed(agentTypes.get(e.agentId), path, `${contextDir}/.runtime`, cfg)) {
        return { deny: `This agent writes reports only, under ${contextDir}/.runtime/. Return the content instead.` }
      }
      return next(e)
    })
  }

  // The main loop always runs on the main model. Subagent steps carry an agentId and pass through.
  on('turn.step', async function* ($, e, next) {
    if (e.agentId || !mainModel || e.model.includes(mainModel)) return yield* next(e)
    return yield* next({ ...e, model: mainModel })
  })

  // Lazy MCP: every MCP tool except this plugin's own stays behind tool search.
  on('tool.describe', async ($, e, next) => {
    const r = await next(e)
    if (e.tool.startsWith('mcp__') && !e.tool.startsWith('mcp__brain__')) return { ...r, isDeferred: true }
    return r
  })
}
