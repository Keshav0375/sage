// Pure functions for the builder run ledger. No mods API calls here: register.ts reads the files,
// runs git, and passes text in.
//
// The ledger is the files on disk, not a separate state file, so it cannot drift from the work:
//   <context>/.runtime/builder/<p>/<ticket>/context.md     fetcher
//   <context>/.runtime/worktrees/<p>/<ticket>/              brancher (the git worktree)
//   <context>/.runtime/builder/<p>/<ticket>/{review,security,tests,arch-check}.md   checkers
//   <context>/.runtime/builder/<p>/<ticket>/verdict.md      verifier
//   <context>/.runtime/builder/<p>/<ticket>/claim.json      which session owns the ticket
//   <context>/.runtime/builder/<p>/<ticket>/log.jsonl       one line per builder agent spawn
// Each report starts with `sha: <HEAD>` and `status: <keyword>`, so a report about an older commit
// is stale and counts as not done.

export const CHECKS = ['review', 'security', 'tests', 'arch-check'] as const
export const CLAIM_MS = 2 * 60 * 60 * 1000

export type Header = { project?: string; ticket?: string; worktree?: string; mode?: string }
export type Report = { sha?: string; status?: string }
export type Claim = { session: string; expires: number }
export type Step =
  | 'todo' | 'fetched' | 'branched' | 'checking' | 'checked' | 'red' | 'verified' | 'shipped'
  | 'done' | 'blocked'

const KEY = /^[A-Z]\d+-T\d+$/

// The `key: value` lines at the top of a builder agent's prompt.
export function parseHeader(prompt: string): Header {
  const out: Header = {}
  for (const line of prompt.split('\n').slice(0, 12)) {
    const m = line.match(/^\s*(project|ticket|worktree|mode)\s*[:=]\s*(\S+)\s*$/i)
    if (m) out[m[1].toLowerCase() as keyof Header] = m[2]
  }
  return out
}

export function isTicketKey(key: string | undefined): boolean {
  return !!key && KEY.test(key)
}

// The `sha:` and `status:` lines at the top of a report file.
export function parseReport(text: string | undefined): Report {
  if (!text) return {}
  const out: Report = {}
  for (const line of text.split('\n').slice(0, 8)) {
    const m = line.match(/^\s*(sha|status)\s*:\s*(\S+)/i)
    if (m) out[m[1].toLowerCase() as keyof Report] = m[2]
  }
  return out
}

// Full or abbreviated SHAs of the same commit. At least 7 characters each.
export function shaMatches(a: string | undefined, b: string | undefined): boolean {
  if (!a || !b || a.length < 7 || b.length < 7) return false
  const x = a.toLowerCase()
  const y = b.toLowerCase()
  return x.startsWith(y) || y.startsWith(x)
}

// The checker reports that are missing or describe another commit than head.
export function staleChecks(reports: Record<string, string | undefined>, head: string): string[] {
  return CHECKS.filter((name) => !shaMatches(parseReport(reports[name]).sha, head))
}

// Where a ticket's ledger files and worktree live.
export function ticketPaths(contextDir: string, project: string, ticket: string) {
  const dir = `${contextDir}/.runtime/builder/${project}/${ticket}`
  return {
    dir,
    worktree: `${contextDir}/.runtime/worktrees/${project}/${ticket}`,
    claim: `${dir}/claim.json`,
    log: `${dir}/log.jsonl`,
    context: `${dir}/context.md`,
    verdict: `${dir}/verdict.md`,
    report: (name: string) => `${dir}/${name}.md`,
  }
}

// The project and ticket of a path inside a harness worktree.
export function ticketOfPath(contextDir: string, path: string): { project: string; ticket: string } | undefined {
  const root = `${contextDir}/.runtime/worktrees/`
  if (!path.startsWith(root)) return undefined
  const [project, ticket] = path.slice(root.length).split('/')
  return project && isTicketKey(ticket) ? { project, ticket } : undefined
}

export type ShipTarget = { kind: 'push' | 'pr'; path?: string; branch?: string }

// A Bash command that pushes a branch or opens a PR, and where it points.
export function shipTarget(command: string): ShipTarget | undefined {
  const cd = command.match(/(?:^|[;&|]\s*)cd\s+("[^"]+"|'[^']+'|\S+)/)
  const cdPath = cd ? cd[1].replace(/^["']|["']$/g, '') : undefined
  const push = command.match(/\bgit\s+(?:-C\s+("[^"]+"|'[^']+'|\S+)\s+)?push\b/)
  if (push) return { kind: 'push', path: push[1]?.replace(/^["']|["']$/g, '') ?? cdPath }
  if (/\bgh\s+pr\s+create\b/.test(command)) {
    const head = command.match(/--head[=\s]+("[^"]+"|'[^']+'|\S+)/)
    return { kind: 'pr', path: cdPath, branch: head?.[1].replace(/^["']|["']$/g, '') }
  }
  return undefined
}

// Why a push or PR from this ticket's worktree must wait, or undefined when the verifier said
// GREEN for exactly this commit.
export function shipBlock(verdict: string | undefined, head: string | undefined): string | undefined {
  const v = parseReport(verdict)
  if (!head) return 'Cannot read HEAD of the ticket worktree.'
  if (!verdict) return 'No verdict.md. Run builder:verifier first.'
  if (!shaMatches(v.sha, head)) return `verdict.md is for ${v.sha ?? 'no sha'}, HEAD is ${head.slice(0, 7)}. Run the checks and builder:verifier again.`
  if ((v.status ?? '').toUpperCase() !== 'GREEN') return `verdict.md says ${v.status ?? 'nothing'}, not GREEN.`
  return undefined
}

export function parseClaim(text: string | undefined): Claim | undefined {
  if (!text) return undefined
  try {
    const c = JSON.parse(text)
    return typeof c.session === 'string' && typeof c.expires === 'number' ? c : undefined
  } catch {
    return undefined
  }
}

// True when another live session owns the ticket.
export function claimedByOther(claim: Claim | undefined, session: string, now: number): boolean {
  return !!claim && claim.session !== session && claim.expires > now
}

// The number of fix loops so far: builder:editor spawns with mode=fix in log.jsonl.
export function fixAttempts(log: string | undefined): number {
  if (!log) return 0
  let n = 0
  for (const line of log.split('\n')) {
    if (!line.trim()) continue
    try {
      const row = JSON.parse(line)
      if (row.agent === 'builder:editor' && row.mode === 'fix') n++
    } catch {
      // A torn line from an interrupted write is skipped.
    }
  }
  return n
}

export type Evidence = {
  status?: string
  pr?: string | null
  hasContext: boolean
  hasWorktree: boolean
  head?: string
  reports: Record<string, string | undefined>
  verdict?: string
}

// The step a ticket has reached, from the evidence on disk.
export function deriveStep(ev: Evidence): Step {
  if (ev.status === 'done') return 'done'
  if (ev.status === 'blocked') return 'blocked'
  if (ev.pr) return 'shipped'
  if (!ev.hasContext) return 'todo'
  if (!ev.hasWorktree || !ev.head) return 'fetched'
  const v = parseReport(ev.verdict)
  if (shaMatches(v.sha, ev.head)) return (v.status ?? '').toUpperCase() === 'GREEN' ? 'verified' : 'red'
  const stale = staleChecks(ev.reports, ev.head)
  if (stale.length === 0) return 'checked'
  if (stale.length < CHECKS.length) return 'checking'
  return 'branched'
}

// What the orchestrator does next for a ticket at a step.
export const NEXT: Record<Step, string> = {
  todo: 'fetch',
  fetched: 'branch',
  branched: 'edit, then check',
  checking: 'finish the checks',
  checked: 'verify',
  red: 'fix, then check',
  verified: 'ship',
  shipped: 'wait for CI and merge',
  done: '-',
  blocked: 'see STATE.md',
}

export type TicketRow = { project: string; ticket: string; title?: string; step: Step; attempts: number; claim?: Claim }

export function renderRuns(rows: TicketRow[], session: string, now: number): string {
  if (rows.length === 0) return 'No unfinished builder tickets.'
  const lines = ['Unfinished builder tickets (resume with /builder:build <project> <epic>):']
  for (const r of rows) {
    const owner = claimedByOther(r.claim, session, now) ? '  [claimed by another session]' : ''
    const tries = r.attempts ? `, fix loop ${r.attempts}` : ''
    lines.push(`- ${r.project} ${r.ticket}${r.title ? ` ${r.title}` : ''}: ${r.step}${tries} → next: ${NEXT[r.step]}${owner}`)
  }
  return lines.join('\n')
}

// Applies allowed field changes to one ticket in tracker text. Returns the new text.
export const TICKET_FIELDS = ['status', 'branch', 'pr'] as const
export const STATUSES = ['todo', 'in_progress', 'review', 'done', 'blocked']

export function updateTicket(text: string, ticket: string, fields: Record<string, unknown>, today: string): string {
  const data = JSON.parse(text)
  for (const key of Object.keys(fields)) {
    if (!(TICKET_FIELDS as readonly string[]).includes(key)) throw new Error(`field "${key}" is not allowed; use ${TICKET_FIELDS.join(', ')}`)
  }
  if (fields.status !== undefined && !STATUSES.includes(String(fields.status))) {
    throw new Error(`status must be one of ${STATUSES.join(', ')}`)
  }
  for (const epic of data.epics ?? []) {
    for (const t of epic.tickets ?? []) {
      if (t.key !== ticket) continue
      Object.assign(t, fields)
      data.updated = today
      return JSON.stringify(data, null, 2) + '\n'
    }
  }
  throw new Error(`ticket ${ticket} is not in tracker.json`)
}

// Tickets that are in progress in a tracker, with titles.
export function activeTickets(text: string): { ticket: string; title?: string; status?: string; pr?: string | null }[] {
  const data = JSON.parse(text)
  const out = []
  for (const epic of data.epics ?? []) {
    for (const t of epic.tickets ?? []) {
      if (t.status === 'in_progress' || t.status === 'blocked') out.push({ ticket: t.key, title: t.title, status: t.status, pr: t.pr })
    }
  }
  return out
}
