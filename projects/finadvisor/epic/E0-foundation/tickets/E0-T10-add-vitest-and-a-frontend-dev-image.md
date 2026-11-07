---
key: "E0-T10"
title: "Add vitest and a frontend dev image"
epic: "E0"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/01-context-and-goals.md#1", "decision-logs.md#adr-019", "decision-logs.md#adr-021", "deep-dive/11-tech-stack.md#frontend-tests"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 11, "id": 6155581154, "url": "https://github.com/Keshav0375/FinAdvisor/issues/11"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
The frontend has a working unit-test runner, a type-check script and a dev Dockerfile so CI and compose can use them.

## Description
Why: plan.md E0 CI scope lists eslint, tsc and vitest, and the compose scope lists "a frontend dev image" (G-13: no frontend Dockerfile). ADR-019 moves the product frontend to a Vite SPA in E8; this ticket works on the current Next.js 14 app in `frontend/` and does not migrate it (see questions).

Do in `frontend/`:
- Add `vitest` (pin in `package-lock.json`) with `vitest.config.ts` (node or jsdom environment as needed), scripts `"test": "vitest run"` and `"typecheck": "tsc --noEmit"`; keep `"lint": "next lint"`.
- Add one real test file for the existing pure function `src/lib/parseCitations.ts` (plain text, one citation marker, multiple markers, malformed marker) so the suite asserts behaviour.
- Add `frontend/Dockerfile` with a `dev` target: Node 20 base referenced by `@sha256:` digest, `npm ci` from the lockfile, runs `npm run dev -- -H 0.0.0.0 -p 3000` as a non-root user; and `frontend/.dockerignore` (`node_modules`, `.next`, `.env*`).

Out of scope: Vite migration and any UI change (E8), Playwright, the compose service (E0-T11), CI wiring (E0-T13).

## Acceptance criteria
- [ ] `cd frontend && npm ci && npm test` exits 0 and reports at least 4 passing tests in `parseCitations`; changing the expected value of one assertion makes `npm test` exit non-zero (verified once).
- [ ] `cd frontend && npm run typecheck` exits 0 on the repo and exits non-zero after introducing `const x: number = "a"` in a source file (verified once).
- [ ] `cd frontend && npm run lint` exits 0 on the repo.
- [ ] `docker build --target dev -t fa-frontend:dev frontend` succeeds; `docker run --rm -d -p 13000:3000 fa-frontend:dev` then `curl -fsS localhost:13000/` returns HTTP 200 within 60 s.
- [ ] The `FROM` line of `frontend/Dockerfile` contains `@sha256:`.
