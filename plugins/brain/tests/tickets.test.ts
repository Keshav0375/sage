import { expect, test } from 'claude-code/testing'
import { parseFrontmatter, renderFrontmatter, setTicketFields, ticketFileFor, planOf, activeTickets } from '../hooks/tickets.ts'

const T2 = `---
key: "E1-T2"
title: "API"
epic: "E1"
status: "in_progress"
depends_on: ["E1-T1"]
pr: null
updated: "2026-01-01"
---

## Summary
Build the API.
`

test('frontmatter round-trips JSON values and keeps the body', () => {
  const { fields, body } = parseFrontmatter(T2)
  expect(fields).toEqual({ key: 'E1-T2', title: 'API', epic: 'E1', status: 'in_progress', depends_on: ['E1-T1'], pr: null, updated: '2026-01-01' })
  expect(body).toContain('Build the API.')
  expect(parseFrontmatter(renderFrontmatter(fields, body))).toEqual({ fields, body })
  expect(parseFrontmatter('no frontmatter').fields).toEqual({})
})

test('ticket updates change only allowed fields and stamp updated', () => {
  const out = parseFrontmatter(setTicketFields(T2, { status: 'review', pr: 'u' }, '2026-11-07'))
  expect(out.fields.status).toBe('review')
  expect(out.fields.pr).toBe('u')
  expect(out.fields.title).toBe('API')
  expect(out.fields.updated).toBe('2026-11-07')
  expect(out.body).toContain('Build the API.')
  expect(() => setTicketFields(T2, { title: 'x' }, 'd')).toThrow('not allowed')
  expect(() => setTicketFields(T2, { status: 'finished' }, 'd')).toThrow('status must be')
  expect(() => setTicketFields('plain', { status: 'done' }, 'd')).toThrow('not a ticket file')
})

test('ticket file lookup matches the exact key, not a longer one', () => {
  const names = ['E1-T1-schema.md', 'E1-T10-ui.md', 'E1-T2-api.md']
  expect(ticketFileFor(names, 'E1-T1')).toBe('E1-T1-schema.md')
  expect(ticketFileFor(names, 'E1-T10')).toBe('E1-T10-ui.md')
  expect(ticketFileFor(names, 'E1-T3')).toBeUndefined()
})

test('plan from files sorts epics and tickets and finds active ones', () => {
  const epic = (k) => `---\nkey: "${k}"\ntitle: "Epic ${k}"\n---\n`
  const tk = (k, s) => `---\nkey: "${k}"\ntitle: "${k}"\nstatus: "${s}"\n---\n`
  const plan = planOf({
    readme: '---\ngithub: {"project_url":"https://x/3"}\n---\n',
    epics: [
      { epic: epic('E10'), tickets: [tk('E10-T1', 'todo')] },
      { epic: epic('E2'), tickets: [tk('E2-T10', 'blocked'), tk('E2-T2', 'in_progress'), 'junk'] },
    ],
  })
  expect(plan.github).toEqual({ project_url: 'https://x/3' })
  expect(plan.epics.map((e) => e.key)).toEqual(['E2', 'E10'])
  expect(plan.epics[0].tickets.map((t) => t.key)).toEqual(['E2-T2', 'E2-T10'])
  expect(activeTickets(plan).map((t) => t.ticket)).toEqual(['E2-T2', 'E2-T10'])
})
