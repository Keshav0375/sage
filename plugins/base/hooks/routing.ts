// Model routing. The main loop decides and always runs on the main model (opus by default).
// Subagents do small, delegated tasks and run on the subagent model (sonnet by default).
// Subagent order of precedence:
//   1. a model the orchestrator passed on the Agent call
//   2. brain/routing.json overrides (keyed by subagent type)
//   3. the subagent_model plugin option

export function parseRouting(text: string): Record<string, string> {
  const data = JSON.parse(text)
  const out: Record<string, string> = {}
  for (const [k, v] of Object.entries(data.agents ?? {})) {
    if (typeof v === 'string' && !k.startsWith('_')) out[k] = v
  }
  return out
}

export function routeModel(
  subagentType: string,
  requested: string | undefined,
  overrides: Record<string, string>,
  fallback: string,
): string | undefined {
  if (requested) return undefined
  return overrides[subagentType] ?? (fallback || undefined)
}
