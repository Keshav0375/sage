import { expect, test } from 'claude-code/testing'
import { parseRoutingConfig, leafDecision, writeAllowed, spawnTier, budgetGuard } from '../hooks/routing.ts'

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
  expect(parseRoutingConfig('{}')).toEqual({ agents: {}, leaves: [], leafModel: 'haiku', reportOnly: [], tiers: {} })
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

const TIERED = parseRoutingConfig(JSON.stringify({
  agents: { Explore: 'haiku' },
  leaf_agents: ['researcher:page-reader'],
  leaf_model: 'haiku',
  leaf_effort: 'low',
  tiers: {
    _doc: 'x',
    'researcher:web-scout': { model: 'haiku', effort: 'low' },
    'researcher:skeptic': { model: 'sonnet', effort: 'medium' },
    'builder:editor': { model: 'sonnet', effort: 'bogus' },
  },
}))

test('tiers parse model and effort; bad effort and _doc keys are dropped', () => {
  expect(TIERED.tiers['researcher:web-scout']).toEqual({ model: 'haiku', effort: 'low' })
  expect(TIERED.tiers['builder:editor']).toEqual({ model: 'sonnet' })
  expect(TIERED.tiers._doc).toBeUndefined()
  expect(TIERED.leafEffort).toBe('low')
})

test('spawn tier: explicit model wins at depth 1, tier next, then built-in map, then fallback', () => {
  expect(spawnTier('researcher:web-scout', false, undefined, TIERED, 'sonnet')).toEqual({ model: 'haiku', effort: 'low' })
  expect(spawnTier('researcher:web-scout', false, 'opus', TIERED, 'sonnet')).toEqual({ model: 'opus', effort: 'low' })
  expect(spawnTier('Explore', false, undefined, TIERED, 'sonnet')).toEqual({ model: 'haiku' })
  expect(spawnTier('general-purpose', false, undefined, TIERED, 'sonnet')).toEqual({ model: 'sonnet' })
  expect(spawnTier('other:agent', false, undefined, TIERED, 'sonnet')).toEqual({})
})

test('spawn tier at depth 2 is always the leaf model and leaf effort', () => {
  expect(spawnTier('researcher:page-reader', true, undefined, TIERED, 'sonnet')).toEqual({ model: 'haiku', effort: 'low' })
})

test('budget guard speaks only past a threshold', () => {
  expect(budgetGuard({ context: 30, window: 10 }, 50, 75)).toBeUndefined()
  expect(budgetGuard({ context: 62, window: 10 }, 50, 75)).toContain('/clear')
  expect(budgetGuard({ context: 10, window: 80 }, 50, 75)).toContain('one agent at a time')
  expect(budgetGuard({}, 50, 75)).toBeUndefined()
})
