---
key: "E8-T10"
title: "Set up Playwright and an auditable test harness for the SPA"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T9"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.4"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Playwright runs against the built SPA with a controllable API and IdP stub, wired into CI.

## Description
Implements deep-dive/04-components-and-responsibilities.md §4.4 'Tests: vitest + Playwright'. Add @playwright/test (pinned), playwright.config.ts that serves `vite preview` of the production build, a fixture API stub (route-level mocking via page.route, plus a small SSE stub server able to emit scripted events with ids, drop the connection at a given seq and honour Last-Event-ID) and an Identity Platform auth stub or the Firebase Auth emulator (decision in questions; default the emulator with two tenants `acme` and `globex`). Add npm script `test:e2e` and a CI job step. One smoke spec: /t/acme loads and shows the firm name. Out of scope: the scenario specs (E8-T11, E8-T12) and running against the real deployed stack.

## Acceptance criteria
- [ ] Given `npm run test:e2e`, when run in CI, then the smoke spec passes and the HTML report is uploaded as an artifact.
- [ ] Given the SSE stub scripted to drop after seq 2, when a client reconnects with `Last-Event-ID: 2`, then the stub replays from seq 3 (stub self-test).
- [ ] Given tenants acme and globex are seeded, when /t/acme and /t/globex load, then each shows its own display_name.
- [ ] Given the workflow file, when parsed, then the e2e job runs after the build step (CI config check).
