import { expect, test } from 'claude-code/testing'
import { emptyBucket, addUsage, maxBucket, totalTokens, formatTokens, formatUsd, bandLine, localDay, clock } from '../hooks/format.ts'

test('buckets add, and a missing bucket counts as zero', () => {
  const a = { input: 10, output: 5, cacheRead: 100, cacheWrite: 20 }
  expect(totalTokens(addUsage(a, a))).toBe(270)
  expect(totalTokens(addUsage(a, undefined))).toBe(135)
})

test('two sources for one session-day keep the higher value of each count', () => {
  const history = { input: 10, output: 50, cacheRead: 1000, cacheWrite: 5 }
  const live = { input: 12, output: 40, cacheRead: 900, cacheWrite: 9 }
  expect(maxBucket(history, live)).toEqual({ input: 12, output: 50, cacheRead: 1000, cacheWrite: 9 })
  expect(maxBucket(undefined, live)).toEqual(live)
})

test('token and cost formats', () => {
  expect(formatTokens(950)).toBe('950')
  expect(formatTokens(1234)).toBe('1.2k')
  expect(formatTokens(48_700)).toBe('49k')
  expect(formatTokens(12_400_000)).toBe('12.4M')
  expect(formatTokens(1_207_698_760)).toBe('1.21B')
  expect(formatUsd(3.4)).toBe('$3.40')
  expect(formatUsd(212.1)).toBe('$212')
})

test('clock and day use local time', () => {
  const d = new Date(2026, 9, 31, 9, 5)
  expect(clock(d)).toBe('09:05')
  expect(localDay(d)).toBe('2026-10-31')
})

const input = {
  now: new Date(2026, 9, 31, 0, 37),
  today: { ...emptyBucket(), cacheRead: 67_000 },
  all: { ...emptyBucket(), cacheRead: 1_207_698_760 },
  sessionUsd: 0.33,
  contextPercent: 7.2,
  rateLimits: [{ kind: 'five_hour', percentUsed: 44 }, { kind: 'seven_day', percentUsed: 17 }],
  showCost: true,
}

test('the line shows every part when it fits', () => {
  expect(bandLine(input)).toBe('00:37  │  today 67k tok  │  all-time 1.21B tok  │  session $0.33  │  ctx 7%  │  5h 44% 7d 17%')
})

test('the line drops parts from the right to fit, and hides cost when asked', () => {
  expect(bandLine(input, 50)).toBe('00:37  │  today 67k tok  │  all-time 1.21B tok')
  expect(bandLine({ ...input, showCost: false })).not.toContain('session')
})
