---
key: "E8-T16"
title: "Add Playwright specs for firm switching, 421, as-of and footers"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T12", "E8-T13", "E8-T14", "E8-T15"]
arch_refs: ["deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/06-interfaces-and-contracts.md#6.11", "decision-logs.md#adr-032", "decision-logs.md#adr-036"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
End-to-end browser tests for the round-4 Done-when: two sessions in one context, 421 and 503 handling, the as-of echo and one footer per licence class.

## Description
Added to the E8 Done-when (R4 changes). Specs on the E8-T10 harness (stub API, scripted SSE):
1. #17 browser part: sign in to firm A and firm B in one browser context; each keeps its own `currentUser` (the `/v1/me` display name) after switching back and forth; a request for firm B's resource with token A returns 403 or 421 from the stub and the UI shows the mapped state, not a crash.
2. 421: the stub answers `WRONG_CELL` with `cell_hint` pointing at a second stub host; the SPA follows once, the chat works, and a second 421 shows the state without a loop. `TENANT_MOVED` the same.
3. 503 `CELL_UNAVAILABLE` for firm A: A shows the outage state, firm B still answers.
4. As-of: set the chip, send a question; the request body has `as_of`; the stub's `meta` says `as_of_source: parsed` with a different date; the echo shows the parsed date (E8-T13).
5. Footers: a stream with `footer` events for `ogl` and `publisher`: two footer lines and the 'Private demo document' label show (E8-T15); a stream with no footer event shows none.
6. `ENTITLEMENT_CHANGED` mid-stream: text kept, banner shown, a later citation not rendered (E8-T6).
The Playwright run fails on any `pageerror`. Out of scope: the quarantine view (see the report's questions).

## Acceptance criteria
- [ ] Given two firms in one context, when the test switches A -> B -> A, then the displayed advisor name per firm is unchanged and `page.on('pageerror')` count is 0 (spec `firm-switch.spec.ts`).
- [ ] Given a stub `WRONG_CELL` with a hint, when a message is sent, then the request log shows the retry to the hinted host exactly once and the answer renders; given a second 421 the log shows no third request (spec `cells.spec.ts::follow_once`).
- [ ] Given `CELL_UNAVAILABLE` for firm A, then firm B's send still returns an answer in the same test (spec `cells.spec.ts::cell_down_isolated`).
- [ ] Given the as-of chip 2024-03-04 and a `meta` with parsed date 2024-04-03, then `getByText('Answered as of 3 Apr 2024')` is visible (spec `as-of.spec.ts`).
- [ ] Given footers for `ogl` and `publisher`, then `getByText` finds both footer texts and 'Private demo document'; with no footer events neither is present (spec `footers.spec.ts`).
- [ ] Given `ENTITLEMENT_CHANGED` after two deltas, then the access banner is visible and a later scripted citation is absent from the DOM (spec `entitlement.spec.ts`).
