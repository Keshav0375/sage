// Model routing and spawn tiers.
// - The main loop decides and always runs on the main model (opus by default).
// - Depth 1 (spawned by the main loop): the agent's own `model` frontmatter decides for plugin
//   agents (sonnet for judgment, haiku for mechanical work). Built-in types (Explore,
//   general-purpose, Plan) take context/routing.json, then the subagent_model option.
// - Depth 2 (spawned by a subagent): only the leaf agents in routing.json may be spawned, and they
//   always run on the leaf model (haiku). Anything else is refused.
// An explicit model on the Agent call wins at depth 1, never at depth 2.

export type Effort = 'low' | 'medium' | 'high' | 'xhigh' | 'max'
export type Tier = { model?: string; effort?: Effort }

export type RoutingConfig = {
  agents: Record<string, string>
  leaves: string[]
  leafModel: string
  leafEffort?: Effort
  reportOnly: string[]
  // Per agent type: the model and effort every step of that agent runs on. The engine does not
  // apply a plugin agent's frontmatter model reliably (2026-11-07 audit: haiku agents ran on
  // sonnet), so the mod enforces the tier on each model request.
  tiers: Record<string, Tier>
}

const EFFORTS = ['low', 'medium', 'high', 'xhigh', 'max']
const effortOf = (v: unknown): Effort | undefined => (typeof v === 'string' && EFFORTS.includes(v) ? (v as Effort) : undefined)

export function parseRoutingConfig(text: string): RoutingConfig {
  const data = JSON.parse(text)
  const agents: Record<string, string> = {}
  for (const [k, v] of Object.entries(data.agents ?? {})) {
    if (typeof v === 'string' && !k.startsWith('_')) agents[k] = v
  }
  const tiers: Record<string, Tier> = {}
  for (const [k, v] of Object.entries(data.tiers ?? {})) {
    if (k.startsWith('_') || !v || typeof v !== 'object') continue
    const t = v as Record<string, unknown>
    const tier: Tier = {}
    if (typeof t.model === 'string') tier.model = t.model
    const effort = effortOf(t.effort)
    if (effort) tier.effort = effort
    tiers[k] = tier
  }
  const list = (v: unknown) => (Array.isArray(v) ? v.filter((x) => typeof x === 'string') : [])
  const cfg: RoutingConfig = {
    agents,
    leaves: list(data.leaf_agents),
    leafModel: typeof data.leaf_model === 'string' ? data.leaf_model : 'haiku',
    reportOnly: list(data.report_only_agents),
    tiers,
  }
  const leafEffort = effortOf(data.leaf_effort)
  if (leafEffort) cfg.leafEffort = leafEffort
  return cfg
}

// The model and effort a subagent runs on, decided once at spawn and enforced on every step.
// Precedence: an explicit model on the Agent call or a hook escalation (`chosen`), then the leaf
// model at depth 2, then the tier of the agent type, then the built-in map, then the fallback.
export function spawnTier(
  subagentType: string,
  depth2: boolean,
  chosen: string | undefined,
  cfg: RoutingConfig,
  fallback: string,
): Tier {
  const tier = cfg.tiers[subagentType] ?? {}
  if (depth2) return { model: chosen ?? cfg.leafModel, effort: cfg.leafEffort ?? tier.effort }
  const model = chosen ?? tier.model ?? cfg.agents[subagentType] ?? (subagentType.includes(':') ? undefined : fallback || undefined)
  const out: Tier = {}
  if (model) out.model = model
  if (tier.effort) out.effort = tier.effort
  return out
}

// Kept for callers that only need the per-type map.
export function parseRouting(text: string): Record<string, string> {
  return parseRoutingConfig(text).agents
}

// The model to set on a depth-1 spawn, or undefined to leave the choice to the call or the agent.
export function routeModel(
  subagentType: string,
  requested: string | undefined,
  overrides: Record<string, string>,
  fallback: string,
): string | undefined {
  if (requested) return undefined
  if (overrides[subagentType]) return overrides[subagentType]
  // Plugin agents (plugin:name) carry their tier in frontmatter; do not override it.
  if (subagentType.includes(':')) return undefined
  return fallback || undefined
}

// Depth-2 policy: a subagent may spawn only leaf agents, on the leaf model.
export function leafDecision(
  subagentType: string,
  parentAgentId: string | undefined,
  cfg: RoutingConfig,
): { deny?: string; model?: string } {
  if (!parentAgentId) return {}
  if (!cfg.leaves.includes(subagentType)) {
    return { deny: `A subagent may only spawn leaf agents (${cfg.leaves.join(', ') || 'none configured'}) on ${cfg.leafModel}. Do the step yourself or return to the orchestrator.` }
  }
  return { model: cfg.leafModel }
}

// Report-only agents may write files only under the runtime folder or a project's library/.
export function writeAllowed(agentType: string | undefined, path: string, contextDir: string, cfg: RoutingConfig): boolean {
  if (!agentType || !cfg.reportOnly.includes(agentType)) return true
  if (!contextDir) return false
  const root = contextDir.replace(/\/$/, '') + '/'
  if (!path.startsWith(root) || path.includes('/../')) return false
  const rest = path.slice(root.length).split('/')
  if (rest[0] === '.runtime' && rest.length > 1) return true
  return rest.length > 2 && rest[1] === 'library' && !rest[0].startsWith('.')
}

// The orchestrator's budget guard: text for the next prompt when the main loop's context fill or
// the usage window passes its threshold, else undefined.
export function budgetGuard(
  b: { context?: number; window?: number },
  contextLimit: number,
  windowLimit: number,
): string | undefined {
  const lines: string[] = []
  if ((b.context ?? 0) >= contextLimit) {
    lines.push(`Main-loop context is ${Math.round(b.context ?? 0)}% full (limit ${contextLimit}%). Record the run state now with mcp__brain__run_update (stage, step, next action); the brain mod compacts the session by itself and the run continues. Keep agent replies short and read files by section.`)
  }
  if ((b.window ?? 0) >= windowLimit) {
    lines.push(`The usage window is ${Math.round(b.window ?? 0)}% used (limit ${windowLimit}%). Spawn at most one agent at a time, prefer Haiku tiers, and save progress to files before each spawn.`)
  }
  return lines.length ? lines.join('\n') : undefined
}
