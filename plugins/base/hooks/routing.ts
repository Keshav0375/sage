// Model routing for subagents. Order of precedence:
//   1. a model the orchestrator passed on the Agent call
//   2. brain/routing.json overrides (keyed by subagent type)
//   3. DEFAULTS below
//   4. the agent file's own `model` frontmatter (Claude Code's resolution)
// "Opus decides, Sonnet builds, Haiku checks."

export const DEFAULTS: Record<string, string> = {
  Explore: 'haiku',
  'general-purpose': 'sonnet',
  Plan: 'opus',
}

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
): string | undefined {
  if (requested) return undefined
  return overrides[subagentType] ?? DEFAULTS[subagentType]
}
