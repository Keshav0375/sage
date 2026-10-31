// Pure helpers for the status line: token buckets and the text. No mods API calls here.

export type Bucket = { input: number; output: number; cacheRead: number; cacheWrite: number }

export function emptyBucket(): Bucket {
  return { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }
}

export function addUsage(a: Bucket, b: Partial<Bucket> | undefined): Bucket {
  return {
    input: a.input + (b?.input ?? 0),
    output: a.output + (b?.output ?? 0),
    cacheRead: a.cacheRead + (b?.cacheRead ?? 0),
    cacheWrite: a.cacheWrite + (b?.cacheWrite ?? 0),
  }
}

// The same session-day counted by two sources: keep the higher value of each count.
export function maxBucket(a: Partial<Bucket> | undefined, b: Partial<Bucket> | undefined): Bucket {
  return {
    input: Math.max(a?.input ?? 0, b?.input ?? 0),
    output: Math.max(a?.output ?? 0, b?.output ?? 0),
    cacheRead: Math.max(a?.cacheRead ?? 0, b?.cacheRead ?? 0),
    cacheWrite: Math.max(a?.cacheWrite ?? 0, b?.cacheWrite ?? 0),
  }
}

// All four token counts, as the API bills them.
export function totalTokens(b: Bucket): number {
  return b.input + b.output + b.cacheRead + b.cacheWrite
}

export function formatTokens(n: number): string {
  if (n < 1000) return String(n)
  if (n < 1_000_000) return (n / 1000).toFixed(n < 10_000 ? 1 : 0) + 'k'
  if (n < 1_000_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  return (n / 1_000_000_000).toFixed(2) + 'B'
}

export function formatUsd(n: number): string {
  return '$' + (n < 100 ? n.toFixed(2) : n.toFixed(0))
}

export function localDay(d: Date): string {
  const p = (x: number) => String(x).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

export function clock(d: Date): string {
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const LIMIT_NAMES: Record<string, string> = { five_hour: '5h', seven_day: '7d' }

export type LineInput = {
  now: Date
  today: Bucket
  all: Bucket
  sessionUsd?: number
  contextPercent?: number
  rateLimits?: { kind: string; percentUsed: number }[]
  showCost: boolean
}

// The status line. Parts drop from the right until the line fits the width.
export function bandLine(x: LineInput, columns = 160): string {
  const parts = [
    clock(x.now),
    `today ${formatTokens(totalTokens(x.today))} tok`,
    `all-time ${formatTokens(totalTokens(x.all))} tok`,
  ]
  if (x.showCost && x.sessionUsd !== undefined) parts.push(`session ${formatUsd(x.sessionUsd)}`)
  if (x.contextPercent !== undefined) parts.push(`ctx ${Math.round(x.contextPercent)}%`)
  const limits = (x.rateLimits ?? []).map((r) => `${LIMIT_NAMES[r.kind] ?? r.kind} ${Math.round(r.percentUsed)}%`)
  if (limits.length) parts.push(limits.join(' '))
  let line = parts.join('  │  ')
  while (line.length > columns && parts.length > 1) {
    parts.pop()
    line = parts.join('  │  ')
  }
  return line
}
