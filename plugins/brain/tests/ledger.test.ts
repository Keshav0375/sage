import { expect, test } from 'claude-code/testing'
import {
  parseHeader, parseReport, shaMatches, staleChecks, ticketOfPath, shipTarget, shipBlock, claimedByOther,
  fixAttempts, deriveStep, renderRuns, updateTicket, activeTickets,
} from '../hooks/ledger.ts'

const CTX = '/h/sage/context'
const HEAD = 'a1b2c3d4e5f60718293a4b5c6d7e8f9012345678'
const report = (sha: string, status = 'CLEAN') => `sha: ${sha}\nstatus: ${status}\n\n# Report\n`
const fresh = { review: report(HEAD), security: report(HEAD), tests: report(HEAD, 'RESULTS'), 'arch-check': report(HEAD) }

test('the prompt header gives project, ticket, worktree and mode', () => {
  const h = parseHeader('project: finadvisor\nticket: E1-T3\nworktree: /w/E1-T3\nmode=fix\n\nFix these findings.')
  expect(h).toEqual({ project: 'finadvisor', ticket: 'E1-T3', worktree: '/w/E1-T3', mode: 'fix' })
  expect(parseHeader('Do the thing.')).toEqual({})
})

test('a report gives its sha and status', () => {
  expect(parseReport(report('abc1234', 'GREEN'))).toEqual({ sha: 'abc1234', status: 'GREEN' })
  expect(parseReport(undefined)).toEqual({})
})

test('short and full SHAs of the same commit match; short ones under 7 do not', () => {
  expect(shaMatches('a1b2c3d', HEAD)).toBe(true)
  expect(shaMatches(HEAD, 'A1B2C3D4')).toBe(true)
  expect(shaMatches('a1b2c3', HEAD)).toBe(false)
  expect(shaMatches('ffffff0', HEAD)).toBe(false)
})

test('a check about an older commit is stale', () => {
  expect(staleChecks(fresh, HEAD)).toEqual([])
  expect(staleChecks({ ...fresh, security: report('0000000') }, HEAD)).toEqual(['security'])
  expect(staleChecks({ review: report(HEAD) }, HEAD)).toEqual(['security', 'tests', 'arch-check'])
})

test('a path inside a harness worktree names its ticket', () => {
  expect(ticketOfPath(CTX, `${CTX}/.runtime/worktrees/finadvisor/E1-T3/backend`)).toEqual({ project: 'finadvisor', ticket: 'E1-T3' })
  expect(ticketOfPath(CTX, '/Users/k/Projects/FinAdvisor')).toBe(undefined)
  expect(ticketOfPath(CTX, `${CTX}/.runtime/worktrees/finadvisor/notes`)).toBe(undefined)
})

test('push and PR commands are found with their target', () => {
  expect(shipTarget('git -C /w/E1-T3 push -u origin feat/E1-T3-x')).toEqual({ kind: 'push', path: '/w/E1-T3' })
  expect(shipTarget('cd "/w/E1-T3" && git push origin HEAD')).toEqual({ kind: 'push', path: '/w/E1-T3' })
  expect(shipTarget('gh pr create --repo k/f --head feat/E1-T3-x --base main')).toEqual({ kind: 'pr', path: undefined, branch: 'feat/E1-T3-x' })
  expect(shipTarget('git status && git log')).toBe(undefined)
  expect(shipTarget('gh pr view 12')).toBe(undefined)
})

test('the ship gate opens only for a GREEN verdict on HEAD', () => {
  expect(shipBlock(report(HEAD, 'GREEN'), HEAD)).toBe(undefined)
  expect(shipBlock(report('0000000', 'GREEN'), HEAD)).toContain('Run the checks')
  expect(shipBlock(report(HEAD, 'RED'), HEAD)).toContain('not GREEN')
  expect(shipBlock(undefined, HEAD)).toContain('No verdict.md')
  expect(shipBlock(report(HEAD, 'GREEN'), undefined)).toContain('Cannot read HEAD')
})

test('a live claim of another session blocks; an expired or own claim does not', () => {
  expect(claimedByOther({ session: 'b', expires: 200 }, 'a', 100)).toBe(true)
  expect(claimedByOther({ session: 'b', expires: 50 }, 'a', 100)).toBe(false)
  expect(claimedByOther({ session: 'a', expires: 200 }, 'a', 100)).toBe(false)
  expect(claimedByOther(undefined, 'a', 100)).toBe(false)
})

test('fix attempts count editor fix spawns and skip torn lines', () => {
  const log = [
    JSON.stringify({ agent: 'builder:editor', mode: 'build' }),
    JSON.stringify({ agent: 'builder:editor', mode: 'fix' }),
    '{"agent":"builder:edi',
    JSON.stringify({ agent: 'builder:runner' }),
    JSON.stringify({ agent: 'builder:editor', mode: 'fix' }),
  ].join('\n')
  expect(fixAttempts(log)).toBe(2)
  expect(fixAttempts(undefined)).toBe(0)
})

test('the step comes from the evidence on disk', () => {
  const base = { hasContext: true, hasWorktree: true, head: HEAD, reports: {} }
  expect(deriveStep({ ...base, hasContext: false })).toBe('todo')
  expect(deriveStep({ ...base, hasWorktree: false })).toBe('fetched')
  expect(deriveStep(base)).toBe('branched')
  expect(deriveStep({ ...base, reports: { review: report(HEAD) } })).toBe('checking')
  expect(deriveStep({ ...base, reports: fresh })).toBe('checked')
  expect(deriveStep({ ...base, reports: fresh, verdict: report(HEAD, 'RED') })).toBe('red')
  expect(deriveStep({ ...base, reports: fresh, verdict: report(HEAD, 'GREEN') })).toBe('verified')
  expect(deriveStep({ ...base, reports: fresh, verdict: report('0000000', 'GREEN') })).toBe('checked')
  expect(deriveStep({ ...base, pr: 'https://github.com/k/f/pull/4' })).toBe('shipped')
  expect(deriveStep({ ...base, status: 'blocked' })).toBe('blocked')
})

test('the run list shows step, loops, next action and foreign claims', () => {
  const text = renderRuns([
    { project: 'finadvisor', ticket: 'E1-T3', title: 'Audit log', step: 'red', attempts: 2 },
    { project: 'finadvisor', ticket: 'E1-T4', step: 'checked', attempts: 0, claim: { session: 'b', expires: 999 } },
  ], 'a', 100)
  expect(text).toContain('- finadvisor E1-T3 Audit log: red, fix loop 2 → next: fix, then check')
  expect(text).toContain('- finadvisor E1-T4: checked → next: verify  [claimed by another session]')
  expect(renderRuns([], 'a', 0)).toBe('No unfinished builder tickets.')
})

const TRACKER = JSON.stringify({
  epics: [{ key: 'E1', tickets: [
    { key: 'E1-T1', title: 'Schema', status: 'done' },
    { key: 'E1-T2', title: 'API', status: 'in_progress', pr: null },
    { key: 'E1-T3', title: 'UI', status: 'blocked' },
  ] }],
  updated: '2026-01-01',
})

test('ticket updates change only allowed fields of one ticket', () => {
  const out = JSON.parse(updateTicket(TRACKER, 'E1-T2', { status: 'review', pr: 'u' }, '2026-11-01'))
  expect(out.epics[0].tickets[1]).toEqual({ key: 'E1-T2', title: 'API', status: 'review', pr: 'u' })
  expect(out.updated).toBe('2026-11-01')
  expect(() => updateTicket(TRACKER, 'E1-T2', { title: 'x' }, 'd')).toThrow('not allowed')
  expect(() => updateTicket(TRACKER, 'E1-T2', { status: 'finished' }, 'd')).toThrow('status must be')
  expect(() => updateTicket(TRACKER, 'E9-T1', { status: 'done' }, 'd')).toThrow('not in tracker')
})

test('active tickets are the in-progress and blocked ones', () => {
  expect(activeTickets(TRACKER).map((t) => t.ticket)).toEqual(['E1-T2', 'E1-T3'])
})
