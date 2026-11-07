---
key: "E4-T26"
title: "Integration tests: resume, idempotency, fallback, guard flag"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T19", "E4-T15", "E4-T6", "E4-T9"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.2", "decision-logs.md#adr-007", "decision-logs.md#adr-036"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 132, "id": 6263474646, "url": "https://github.com/Keshav0375/FinAdvisor/issues/132"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Integration tests for dropped connections, key reuse, fallback gating, meta consistency and the Model Armor fallback.

## Description
Add the epic's integration tests against a real Postgres: (1) drop the connection mid-stream, resume with Last-Event-ID, final event list equals an uninterrupted run; (2) same Idempotency-Key twice -> one LLM call; different body -> 409; (3) meta.retrieval_degraded equals messages.retrieval_degraded for degraded and non-degraded turns; (4) with primary forced to fail, fallback used only when LLM_FALLBACK_ENABLED is true; (5) Model Armor timeout with MODEL_ARMOR_ENABLED=true (round 4, ADR-036 amended): the turn CONTINUES via the Presidio plus heuristics fallback and the stored turn carries the `guard_degraded` flag; a heuristic injection hit still gives INPUT_BLOCKED; GUARD_UNAVAILABLE only when the fallback itself fails; (6) every emitted [n] is within retrieved chunk ids. Wire into CI, tiers per 07 §7.4.

## Acceptance criteria
- [ ] Test (1) fails if any event is missing or duplicated after resume.
- [ ] Test (2) fails if the LLM stub call count is not 1, or the status is not 409 on a different body.
- [ ] Test (3) fails if the two flags differ for either case; test (4) fails if the fallback is called with the flag off or not called with it on.
- [ ] Test (5) fails if a Model Armor timeout stops the turn, if `guard_degraded` is absent from the chat.audit flags, or if GUARD_UNAVAILABLE appears while the fallback works.
- [ ] Test (6) and all of the above run in CI on every PR.
