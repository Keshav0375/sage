import { expect, test } from 'claude-code/testing'
import { parseRoutingConfig, leafDecision, writeAllowed } from '../hooks/routing.ts'

const CFG = parseRoutingConfig(JSON.stringify({
  agents: { Explore: 'haiku', _doc: 'x' },
  leaf_agents: ['researcher:page-reader', 'Explore'],
  leaf_model: 'haiku',
  report_only_agents: ['researcher:skeptic'],
}))

test('routing config parses agents, leaves, leaf model and report-only agents', () => {
  expect(CFG.agents).toEqual({ Explore: 'haiku' })
  expect(CFG.leaves).toEqual(['researcher:page-reader', 'Explore'])
  expect(CFG.leafModel).toBe('haiku')
  expect(parseRoutingConfig('{}')).toEqual({ agents: {}, leaves: [], leafModel: 'haiku', reportOnly: [] })
})

test('the main loop may spawn anything; a subagent may spawn only leaves, forced to haiku', () => {
  expect(leafDecision('researcher:skeptic', undefined, CFG)).toEqual({})
  expect(leafDecision('researcher:page-reader', 'agent-1', CFG)).toEqual({ model: 'haiku' })
  expect(leafDecision('Explore', 'agent-1', CFG)).toEqual({ model: 'haiku' })
  expect(leafDecision('researcher:skeptic', 'agent-1', CFG).deny).toContain('only spawn leaf agents')
})

test('report-only agents write only under .runtime; others are not limited here', () => {
  expect(writeAllowed('researcher:skeptic', '/c/.runtime/research/p/s.md', '/c/.runtime', CFG)).toBe(true)
  expect(writeAllowed('researcher:skeptic', '/c/projects/p/arch/overview.md', '/c/.runtime', CFG)).toBe(false)
  expect(writeAllowed('researcher:skeptic', '/c/.runtime-evil/x', '/c/.runtime', CFG)).toBe(false)
  expect(writeAllowed('researcher:arch-writer', '/c/projects/p/arch/overview.md', '/c/.runtime', CFG)).toBe(true)
  expect(writeAllowed(undefined, '/anything', '/c/.runtime', CFG)).toBe(true)
})
