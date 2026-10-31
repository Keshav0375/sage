// Pure functions over brain/registry.json. No mods API calls here:
// register.ts reads the files and passes text in.

export type Project = {
  kind?: string
  status?: string
  summary?: string
  repos?: Record<string, string>
}

export type Registry = {
  version: number
  projects: Record<string, Project>
}

export type Match = { project: string; repo: string; path: string }

export function parseRegistry(text: string): Registry {
  const data = JSON.parse(text)
  if (typeof data !== 'object' || data === null || typeof data.projects !== 'object') {
    throw new Error('registry.json must be an object with a "projects" object')
  }
  return { version: data.version ?? 1, projects: data.projects }
}

export function expandHome(path: string, home: string): string {
  if (path === '~') return home
  if (path.startsWith('~/')) return home + path.slice(1)
  return path
}

function stripSlash(path: string): string {
  return path.length > 1 && path.endsWith('/') ? path.slice(0, -1) : path
}

// The repo whose path is the longest prefix of cwd wins, so nested repos resolve correctly.
export function resolveCwd(reg: Registry, cwd: string, home: string): Match | undefined {
  const dir = stripSlash(cwd)
  let best: Match | undefined
  for (const [project, p] of Object.entries(reg.projects)) {
    for (const [repo, raw] of Object.entries(p.repos ?? {})) {
      const path = stripSlash(expandHome(raw, home))
      const inside = dir === path || dir.startsWith(path + '/')
      if (inside && (!best || path.length > best.path.length)) best = { project, repo, path }
    }
  }
  return best
}

// Keeps the card small: only the "Open decisions" and "Blockers" sections of STATE.md.
export function stateHighlights(state: string, maxLines = 12): string[] {
  const out: string[] = []
  let keep = false
  for (const line of state.split('\n')) {
    if (line.startsWith('## ')) keep = /open decisions|blockers/i.test(line)
    if (keep && line.trim() !== '') out.push(line)
    if (out.length >= maxLines) break
  }
  return out
}

export function renderCard(
  reg: Registry,
  name: string,
  home: string,
  repoExists: Record<string, boolean>,
  state: string | undefined,
  match?: Match,
  tracker?: string,
): string {
  const p = reg.projects[name]
  if (!p) return `Unknown project "${name}". Known: ${Object.keys(reg.projects).join(', ')}`
  const lines = [`Project: ${name} (${p.kind ?? 'project'}, ${p.status ?? 'active'})`]
  if (p.summary) lines.push(p.summary)
  if (match) lines.push(`You are in repo "${match.repo}" at ${match.path}`)
  const repos = Object.entries(p.repos ?? {})
  if (repos.length) {
    lines.push('Repos:')
    for (const [repo, raw] of repos) {
      const path = expandHome(raw, home)
      lines.push(`- ${repo}: ${path}${repoExists[repo] === false ? '  (MISSING on disk)' : ''}`)
    }
  }
  lines.push(`Brain folder: projects/${name}/ (arch/, tracker.json, STATE.md, lessons.jsonl)`)
  const hl = state ? stateHighlights(state) : []
  if (hl.length) lines.push('From STATE.md:', ...hl)
  if (tracker) {
    try {
      lines.push(...trackerSummary(tracker))
    } catch {
      lines.push('Tracker: tracker.json does not parse.')
    }
  }
  return lines.join('\n')
}

// A short summary of brain/projects/<p>/tracker.json: the GitHub project, epic progress, and
// the next tickets whose dependencies are done.
export function trackerSummary(text: string, maxNext = 3): string[] {
  const t = JSON.parse(text)
  const lines: string[] = []
  if (t.github?.project_url) lines.push(`GitHub project: ${t.github.project_url}`)
  const done = new Set<string>()
  const all: any[] = []
  for (const epic of t.epics ?? []) {
    for (const tk of epic.tickets ?? []) {
      all.push(tk)
      if (tk.status === 'done') done.add(tk.key)
    }
  }
  for (const epic of t.epics ?? []) {
    const tickets = epic.tickets ?? []
    const n = tickets.filter((tk) => tk.status === 'done').length
    lines.push(`- ${epic.key} ${epic.title} [${n}/${tickets.length} done]${epic.issue?.url ? ` ${epic.issue.url}` : ''}`)
  }
  const next = all.filter((tk) => tk.status === 'todo' && (tk.depends_on ?? []).every((d) => done.has(d)))
  if (next.length) lines.push(`Ready: ${next.slice(0, maxNext).map((tk) => `${tk.key} ${tk.title}`).join('; ')}`)
  return lines.length ? ['Tracker:', ...lines] : []
}

export function renderBoard(reg: Registry, home: string): string {
  const rows = Object.entries(reg.projects).map(([name, p]) => {
    const repos = Object.entries(p.repos ?? {})
      .map(([r, path]) => `${r}=${expandHome(path, home)}`)
      .join(', ')
    return `- ${name} [${p.status ?? 'active'}] ${p.kind ?? ''}${repos ? ` :: ${repos}` : ''}`
  })
  return rows.length ? `Projects:\n${rows.join('\n')}` : 'No projects registered.'
}
