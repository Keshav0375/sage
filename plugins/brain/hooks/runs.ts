// Research run state: one JSON file per project under projects/.runtime/runs/<p>.json, written by
// the orchestrator through mcp__brain__run_update at every stage and wave boundary. The mod puts it
// into every prompt and every compaction, so a run continues by itself after compaction or a
// usage-limit stop, and Keshav is asked only for decisions.

export type RunStatus = 'active' | 'waiting_keshav' | 'done'

export type Run = {
  project: string
  goal?: string
  stage?: number
  step?: string
  next?: string
  status: RunStatus
  waiting?: string[]
  updated?: string
}

const STATUSES: RunStatus[] = ['active', 'waiting_keshav', 'done']
export const RUN_FIELDS = ['goal', 'stage', 'step', 'next', 'status', 'waiting'] as const

export function parseRun(text: string | undefined): Run | undefined {
  if (!text) return undefined
  try {
    const r = JSON.parse(text)
    if (!r || typeof r.project !== 'string' || !STATUSES.includes(r.status)) return undefined
    return r as Run
  } catch {
    return undefined
  }
}

// Applies allowed changes to a run. Throws on unknown fields or a bad status or stage.
export function updateRun(old: Run | undefined, project: string, fields: Record<string, unknown>, now: string): Run {
  for (const k of Object.keys(fields)) {
    if (!(RUN_FIELDS as readonly string[]).includes(k)) throw new Error(`field "${k}" is not allowed; use ${RUN_FIELDS.join(', ')}`)
  }
  if (fields.status !== undefined && !STATUSES.includes(fields.status as RunStatus)) {
    throw new Error(`status must be one of ${STATUSES.join(', ')}`)
  }
  if (fields.stage !== undefined && !(Number.isInteger(fields.stage) && (fields.stage as number) >= 0 && (fields.stage as number) <= 6)) {
    throw new Error('stage must be an integer 0-6')
  }
  if (fields.waiting !== undefined && !(Array.isArray(fields.waiting) && fields.waiting.every((w) => typeof w === 'string'))) {
    throw new Error('waiting must be a list of strings')
  }
  const base: Run = old ?? { project, status: 'active' }
  return { ...base, ...(fields as Partial<Run>), project, updated: now }
}

// The prompt block for unfinished runs, or undefined when none is unfinished.
export function runBlock(runs: Run[]): string | undefined {
  const open = runs.filter((r) => r.status !== 'done')
  if (!open.length) return undefined
  const lines = ['Unfinished research run(s). This is the orchestrator\'s own state, not a request from Keshav.']
  for (const r of open) {
    lines.push(`- ${r.project}: stage ${r.stage ?? '?'}${r.step ? ` (${r.step})` : ''}, status ${r.status}${r.goal ? `; goal: ${r.goal}` : ''}`)
    if (r.next) lines.push(`  next action: ${r.next}`)
    if (r.status === 'waiting_keshav' && r.waiting?.length) lines.push(`  waiting for Keshav: ${r.waiting.join(' | ')}`)
  }
  lines.push('When status is active and Keshav has not asked for something else, continue the next action without asking. Ask Keshav only scope, money or compliance questions, batched in one message, and set status waiting_keshav while you wait.')
  return lines.join('\n')
}

// True when the mod should compact the main loop now.
export function shouldCompact(contextPercent: number | undefined, limit: number, active: boolean, lastCompactMs: number, nowMs: number, cooldownMs = 10 * 60_000): boolean {
  return active && (contextPercent ?? 0) >= limit && nowMs - lastCompactMs >= cooldownMs
}
