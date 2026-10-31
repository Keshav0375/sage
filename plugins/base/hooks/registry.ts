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
  lines.push(`Brain folder: projects/${name}/ (arch/, decisions.md, STATE.md, lessons.jsonl)`)
  const hl = state ? stateHighlights(state) : []
  if (hl.length) lines.push('From STATE.md:', ...hl)
  return lines.join('\n')
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
