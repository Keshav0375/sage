import { parseRegistry, resolveCwd, renderCard, renderBoard, expandHome } from './registry.ts'
import { checkBash } from './guard.ts'
import { parseRouting, routeModel } from './routing.ts'

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
    return next(e)
  })

  // Context: the project card goes into the first message of each conversation.
  on('prompt.context', async ($, e, next) => {
    const text = await contextFor($, contextDir, await $.session.cwd())
    return next({ ...e, blocks: [...e.blocks, { name: 'project', text }] })
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
    const reason = checkBash(String(e.command ?? ''))
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
    let overrides = {}
    const path = `${contextDir}/routing.json`
    if (contextDir && (await $.fs.exists(path))) overrides = parseRouting(await $.fs.read(path))
    const model = routeModel(e.subagentType, e.model, overrides, subagentModel)
    return next(model ? { ...e, model } : e)
  })

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
