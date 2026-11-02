// Model routing and spawn tiers.
// - The main loop decides and always runs on the main model (opus by default).
// - Depth 1 (spawned by the main loop): the agent's own `model` frontmatter decides for plugin
//   agents (sonnet for judgment, haiku for mechanical work). Built-in types (Explore,
//   general-purpose, Plan) take context/routing.json, then the subagent_model option.
// - Depth 2 (spawned by a subagent): only the leaf agents in routing.json may be spawned, and they
//   always run on the leaf model (haiku). Anything else is refused.
// An explicit model on the Agent call wins at depth 1, never at depth 2.

export type RoutingConfig = {
  agents: Record<string, string>
  leaves: string[]
  leafModel: string
  reportOnly: string[]
}

export function parseRoutingConfig(text: string): RoutingConfig {
  const data = JSON.parse(text)
  const agents: Record<string, string> = {}
  for (const [k, v] of Object.entries(data.agents ?? {})) {
    if (typeof v === 'string' && !k.startsWith('_')) agents[k] = v
  }
  const list = (v: unknown) => (Array.isArray(v) ? v.filter((x) => typeof x === 'string') : [])
  return {
    agents,
    leaves: list(data.leaf_agents),
    leafModel: typeof data.leaf_model === 'string' ? data.leaf_model : 'haiku',
    reportOnly: list(data.report_only_agents),
  }
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

// Report-only agents may write files only under the runtime folder.
export function writeAllowed(agentType: string | undefined, path: string, runtimeDir: string, cfg: RoutingConfig): boolean {
  if (!agentType || !cfg.reportOnly.includes(agentType)) return true
  return !!runtimeDir && path.startsWith(runtimeDir.replace(/\/$/, '') + '/')
}
