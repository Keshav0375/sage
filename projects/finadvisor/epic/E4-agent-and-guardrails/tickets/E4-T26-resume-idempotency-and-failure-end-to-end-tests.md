---
key: "E4-T26"
title: "Resume, idempotency and failure end-to-end tests"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T19", "E4-T15", "E4-T6", "E4-T9"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.2", "decision-logs.md#ADR-007"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Integration tests for dropped connections, key reuse, fallback gating and meta consistency.

## Description
Add the epic's integration tests against a real Postgres: (1) drop the connection mid-stream, resume with Last-Event-ID, final event list equals an uninterrupted run; (2) same Idempotency-Key twice -> one LLM call; different body -> 409; (3) meta.retrieval_degraded equals messages.retrieval_degraded for degraded and non-degraded turns; (4) with primary forced to fail, fallback used only when LLM_FALLBACK_ENABLED is true; (5) Model Armor 500 ms timeout -> GUARD_UNAVAILABLE; (6) every emitted [n] is within retrieved chunk ids. Wire into CI.

## Acceptance criteria
- [ ] Test (1) fails if any event is missing or duplicated after resume.
- [ ] Test (2) fails if the LLM stub call count is not 1, or the status is not 409 on a different body.
- [ ] Test (3) fails if the two flags differ for either case.
- [ ] Tests (4)-(6) fail as described in their assertions and run in CI on every PR.
