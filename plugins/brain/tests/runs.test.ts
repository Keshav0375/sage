import { expect, test } from 'claude-code/testing'
import { parseRun, updateRun, runBlock, shouldCompact } from '../hooks/runs.ts'

test('run files parse only with a project and a known status', () => {
  expect(parseRun('{"project":"p","status":"active","stage":3}')?.stage).toBe(3)
  expect(parseRun('{"project":"p","status":"paused"}')).toBeUndefined()
  expect(parseRun('not json')).toBeUndefined()
  expect(parseRun(undefined)).toBeUndefined()
})

test('run updates accept only known fields and valid values', () => {
  const r = updateRun(undefined, 'p', { stage: 4, step: 'wave B', next: 'check tickets' }, 't1')
  expect(r).toEqual({ project: 'p', status: 'active', stage: 4, step: 'wave B', next: 'check tickets', updated: 't1' })
  const r2 = updateRun(r, 'p', { status: 'waiting_keshav', waiting: ['budget?'] }, 't2')
  expect(r2.stage).toBe(4)
  expect(r2.waiting).toEqual(['budget?'])
  expect(() => updateRun(r, 'p', { owner: 'x' }, 't')).toThrow('not allowed')
  expect(() => updateRun(r, 'p', { status: 'paused' }, 't')).toThrow('status must be')
  expect(() => updateRun(r, 'p', { stage: 9 }, 't')).toThrow('stage must be')
  expect(() => updateRun(r, 'p', { waiting: [1] }, 't')).toThrow('waiting must be')
})

test('run block lists unfinished runs only, with the next action', () => {
  expect(runBlock([{ project: 'p', status: 'done' }])).toBeUndefined()
  const text = runBlock([{ project: 'p', status: 'active', stage: 5, next: 'publish' }, { project: 'q', status: 'waiting_keshav', stage: 1, waiting: ['money?'] }])
  expect(text).toContain('p: stage 5')
  expect(text).toContain('next action: publish')
  expect(text).toContain('waiting for Keshav: money?')
  expect(text).toContain('continue the next action without asking')
})

test('compaction triggers only in an active run past the limit and after the cooldown', () => {
  expect(shouldCompact(60, 50, true, 0, 20 * 60_000)).toBe(true)
  expect(shouldCompact(40, 50, true, 0, 20 * 60_000)).toBe(false)
  expect(shouldCompact(60, 50, false, 0, 20 * 60_000)).toBe(false)
  expect(shouldCompact(60, 50, true, 15 * 60_000, 20 * 60_000)).toBe(false)
})
