// Markdown epics and tickets (see the brain:layout skill).
// projects/<p>/epic/README.md                      github info
// projects/<p>/epic/<E>-<slug>/epic.md             epic frontmatter
// projects/<p>/epic/<E>-<slug>/tickets/<key>-*.md  ticket frontmatter + body
// Frontmatter values are JSON, one `key: <json>` per line, so parsing needs no YAML library.

export type Fields = Record<string, unknown>

const FENCE = '---'

export function parseFrontmatter(text: string): { fields: Fields; body: string } {
  const lines = text.split('\n')
  if (lines[0]?.trim() !== FENCE) return { fields: {}, body: text }
  const end = lines.indexOf(FENCE, 1)
  if (end < 0) return { fields: {}, body: text }
  const fields: Fields = {}
  for (const line of lines.slice(1, end)) {
    const m = line.match(/^([A-Za-z_][\w-]*):\s?(.*)$/)
    if (!m) continue
    const raw = m[2].trim()
    try {
      fields[m[1]] = raw === '' ? null : JSON.parse(raw)
    } catch {
      fields[m[1]] = raw
    }
  }
  return { fields, body: lines.slice(end + 1).join('\n') }
}

export function renderFrontmatter(fields: Fields, body: string): string {
  const head = Object.entries(fields).map(([k, v]) => `${k}: ${JSON.stringify(v ?? null)}`)
  return [FENCE, ...head, FENCE, body].join('\n')
}

export const TICKET_FIELDS = ['status', 'branch', 'pr', 'issue'] as const
export const STATUSES = ['todo', 'in_progress', 'review', 'done', 'blocked']

// Applies allowed field changes to one ticket file's text. Returns the new text.
export function setTicketFields(text: string, fields: Fields, today: string): string {
  for (const key of Object.keys(fields)) {
    if (!(TICKET_FIELDS as readonly string[]).includes(key)) throw new Error(`field "${key}" is not allowed; use ${TICKET_FIELDS.join(', ')}`)
  }
  if (fields.status !== undefined && !STATUSES.includes(String(fields.status))) {
    throw new Error(`status must be one of ${STATUSES.join(', ')}`)
  }
  const { fields: fm, body } = parseFrontmatter(text)
  if (!fm.key) throw new Error('not a ticket file: no key in frontmatter')
  return renderFrontmatter({ ...fm, ...fields, updated: today }, body)
}

// The ticket file for a key among a directory listing of names, or undefined.
export function ticketFileFor(names: string[], key: string): string | undefined {
  return names.find((n) => n === `${key}.md` || n.startsWith(`${key}-`) && n.endsWith('.md') && !n.slice(key.length + 1).match(/^T\d/))
}

export type PlanFiles = {
  readme?: string
  epics: { epic?: string; tickets: string[] }[]
}

// The plan in the shape older helpers expect: { github, epics: [{ ...epic, tickets: [...] }] }.
export function planOf(files: PlanFiles): { github?: unknown; epics: any[] } {
  const github = files.readme ? parseFrontmatter(files.readme).fields.github : undefined
  const epics = files.epics
    .map((e) => ({
      ...(e.epic ? parseFrontmatter(e.epic).fields : {}),
      tickets: e.tickets.map((t) => parseFrontmatter(t).fields).filter((f) => f.key),
    }))
    .filter((e: any) => e.key)
    .sort((a: any, b: any) => Number(String(a.key).slice(1)) - Number(String(b.key).slice(1)))
  for (const e of epics) e.tickets.sort((a: any, b: any) => Number(String(a.key).split('-T')[1]) - Number(String(b.key).split('-T')[1]))
  return { github, epics }
}

// Tickets that are in progress or blocked, with titles.
export function activeTickets(plan: { epics: any[] }): { ticket: string; title?: string; status?: string; pr?: string | null }[] {
  const out = []
  for (const epic of plan.epics) {
    for (const t of epic.tickets ?? []) {
      if (t.status === 'in_progress' || t.status === 'blocked') out.push({ ticket: t.key, title: t.title, status: t.status, pr: t.pr })
    }
  }
  return out
}
