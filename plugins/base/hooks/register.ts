import { parseRegistry, resolveCwd, renderCard, renderBoard, expandHome } from './registry.ts'
import { checkBash } from './guard.ts'
import { parseRouting, routeModel } from './routing.ts'

// Reads brain/registry.json. Returns undefined when brain_dir is unset or the file is missing.
async function loadRegistry($, brainDir) {
  if (!brainDir) return undefined
  const path = `${brainDir}/registry.json`
  if (!(await $.fs.exists(path))) return undefined
  return parseRegistry(await $.fs.read(path))
}

// The project card for one project, with repo existence and STATE.md highlights.
async function projectCard($, brainDir, reg, home, name, match) {
  const exists = {}
  for (const [repo, raw] of Object.entries(reg.projects[name]?.repos ?? {})) {
    exists[repo] = await $.fs.exists(expandHome(raw, home))
  }
  const statePath = `${brainDir}/projects/${name}/STATE.md`
  const state = (await $.fs.exists(statePath)) ? await $.fs.read(statePath) : undefined
  return renderCard(reg, name, home, exists, state, match)
}

// The context text for the session's working directory.
async function contextFor($, brainDir, cwd) {
  if (!brainDir) return 'base: brain_dir is not set. Run /base:setup.'
  const home = (await $.env.get('HOME')) ?? ''
  const reg = await loadRegistry($, brainDir)
  if (!reg) return `base: no registry at ${brainDir}/registry.json. Run /base:setup.`
  const match = resolveCwd(reg, cwd, home)
  if (match) return await projectCard($, brainDir, reg, home, match.project, match)
  const brainRoot = brainDir.replace(/\/brain\/?$/, '')
  if (cwd === brainRoot || cwd.startsWith(brainRoot + '/')) {
    return `You are in the harness repo (brain at ${brainDir}). Architecture planning happens here.\n${renderBoard(reg, home)}`
  }
  return `Directory ${cwd} is not in the registry. Run /base:register to add it to a project.`
}

export function register(on, options) {
  const brainDir = options?.brain_dir ? String(options.brain_dir).replace(/\/$/, '') : ''

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
    const text = await contextFor($, brainDir, await $.session.cwd())
    return next({ ...e, blocks: [...e.blocks, { name: 'project', text }] })
  })

  on('tool.call', { tool: 'mcp__base__where' }, async ($, e) => {
    const home = (await $.env.get('HOME')) ?? ''
    const reg = await loadRegistry($, brainDir)
    if (!reg) return { result: 'No registry. Run /base:setup.' }
    if (!e.project) return { result: await contextFor($, brainDir, await $.session.cwd()) }
    return { result: await projectCard($, brainDir, reg, home, e.project) }
  })

  on('tool.call', { tool: 'mcp__base__projects' }, async ($) => {
    const home = (await $.env.get('HOME')) ?? ''
    const reg = await loadRegistry($, brainDir)
    return { result: reg ? renderBoard(reg, home) : 'No registry. Run /base:setup.' }
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

  // Model routing: the orchestrator's explicit choice, then brain/routing.json, then defaults.
  on('agent.spawn', async ($, e, next) => {
    let overrides = {}
    const path = `${brainDir}/routing.json`
    if (brainDir && (await $.fs.exists(path))) overrides = parseRouting(await $.fs.read(path))
    const model = routeModel(e.subagentType, e.model, overrides)
    return next(model ? { ...e, model } : e)
  })

  // Lazy MCP: every MCP tool except this plugin's own stays behind tool search.
  on('tool.describe', async ($, e, next) => {
    const r = await next(e)
    if (e.tool.startsWith('mcp__') && !e.tool.startsWith('mcp__base__')) return { ...r, isDeferred: true }
    return r
  })
}
