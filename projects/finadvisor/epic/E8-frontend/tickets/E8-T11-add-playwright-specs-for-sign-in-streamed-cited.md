---
key: "E8-T11"
title: "Add Playwright specs for sign-in, streamed cited answer and feedback"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T10"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.4", "deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/08-security-and-privacy.md#8.2"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 192, "id": 6263567775, "url": "https://github.com/Keshav0375/FinAdvisor/issues/192"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
E2E proves two-tenant sign-in, a streamed cited answer, a stale badge and thumbs feedback.

## Description
Part of E8 Done-when. Specs: (1) sign in as advisor of acme and as advisor of globex; each sees its own firm name and `/v1/me` display_name; a tenant-mismatched token attempt shows the UNAUTHENTICATED state. (2) ask a question: deltas stream into the answer incrementally (assert partial text before `done`), `meta` degraded notice appears when scripted, citations with excerpts render, one stale=true citation shows the stale badge. (3) thumbs-up and thumbs-down send the correct feedback request. (4) conversation history shows the turn after reload. Out of scope: failure scenarios (E8-T12).

## Acceptance criteria
- [ ] Given two seeded tenants, when each signs in, then each page shows its own firm name and no cross-tenant data (Playwright assertion).
- [ ] Given a scripted stream of 3 deltas then done, when asked, then the answer text is observed with partial content before the final delta.
- [ ] Given a citation scripted with stale=true, when rendered, then `getByText` for the stale badge is visible; a stale=false citation has none.
- [ ] Given thumbs-up click, when sent, then page.waitForRequest sees POST /v1/messages/<id>/feedback with `{score:1}`.
