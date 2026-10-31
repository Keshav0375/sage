import { expect, test } from 'claude-code/testing'
import { parseRegistry, resolveCwd, renderCard, stateHighlights, trackerSummary } from '../hooks/registry.ts'
import { checkBash } from '../hooks/guard.ts'
import { routeModel } from '../hooks/routing.ts'

const HOME = '/Users/k'
const REG = parseRegistry(JSON.stringify({
  version: 1,
  projects: {
    shop: { kind: 'product', repos: { api: '~/Projects/shop-api', web: '~/Projects/shop-web' } },
    mono: { repos: { root: '~/Projects/mono', svc: '~/Projects/mono/services/svc' } },
  },
}))

test('cwd resolves to the project that owns the repo', () => {
  expect(resolveCwd(REG, '/Users/k/Projects/shop-api/src/x', HOME)?.project).toBe('shop')
  expect(resolveCwd(REG, '/Users/k/Projects/shop-web', HOME)?.repo).toBe('web')
})

test('the longest repo path wins for nested repos', () => {
  expect(resolveCwd(REG, '/Users/k/Projects/mono/services/svc/a', HOME)?.repo).toBe('svc')
  expect(resolveCwd(REG, '/Users/k/Projects/mono/lib', HOME)?.repo).toBe('root')
})

test('a sibling directory with a shared prefix does not match', () => {
  expect(resolveCwd(REG, '/Users/k/Projects/shop-api-old', HOME)).toBe(undefined)
})

test('the card lists repos and marks missing ones', () => {
  const card = renderCard(REG, 'shop', HOME, { api: true, web: false }, undefined)
  expect(card).toContain('api: /Users/k/Projects/shop-api')
  expect(card).toContain('web: /Users/k/Projects/shop-web  (MISSING on disk)')
})

test('STATE.md highlights keep only open decisions and blockers', () => {
  const state = '# S\n## Now\nworking\n## Open decisions\n- pick db\n## Done\n- x\n## Blockers\n- none'
  expect(stateHighlights(state)).toEqual(['## Open decisions', '- pick db', '## Blockers', '- none'])
})

test('guard blocks destructive commands and attribution', () => {
  expect(checkBash('rm -rf build')).toBeDefined()
  expect(checkBash('git push --force origin main')).toBeDefined()
  expect(checkBash('git reset --hard HEAD~1')).toBeDefined()
  expect(checkBash('git commit -m "x\n\nCo-Authored-By: Claude <noreply@anthropic.com>"')).toBeDefined()
})

test('guard allows normal commands', () => {
  expect(checkBash('git rm -r old/')).toBe(undefined)
  expect(checkBash('git push origin main')).toBe(undefined)
  expect(checkBash('ls -la && rm notes.tmp')).toBe(undefined)
})

test('routing keeps an explicit model, then overrides, then the subagent model', () => {
  expect(routeModel('Explore', 'opus', {}, 'sonnet')).toBe(undefined)
  expect(routeModel('Explore', undefined, { Explore: 'haiku' }, 'sonnet')).toBe('haiku')
  expect(routeModel('builder:editor', undefined, {}, 'sonnet')).toBe('sonnet')
  expect(routeModel('builder:editor', undefined, {}, '')).toBe(undefined)
})

test('tracker summary shows epic progress and ready tickets', () => {
  const tracker = JSON.stringify({
    github: { project_url: 'https://github.com/users/k/projects/3' },
    epics: [{
      key: 'E1', title: 'Auth', tickets: [
        { key: 'E1-T1', title: 'Schema', status: 'done' },
        { key: 'E1-T2', title: 'Login API', status: 'todo', depends_on: ['E1-T1'] },
        { key: 'E1-T3', title: 'SSO', status: 'todo', depends_on: ['E1-T2'] },
      ],
    }],
  })
  expect(trackerSummary(tracker)).toEqual([
    'Tracker:',
    'GitHub project: https://github.com/users/k/projects/3',
    '- E1 Auth [1/3 done]',
    'Ready: E1-T2 Login API',
  ])
})

test('the mod denies a destructive Bash call', async ($, on) => {
  on('tool.call', () => ({ result: 'ran' }))
  const r = await $.tool.call({ tool: 'Bash', command: 'rm -rf /tmp/x' }).catch((err) => ({ deny: String(err) }))
  expect(JSON.stringify(r)).toContain('deletes without recovery')
})
