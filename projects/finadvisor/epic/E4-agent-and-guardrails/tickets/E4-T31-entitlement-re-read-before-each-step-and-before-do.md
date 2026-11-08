---
key: "E4-T31"
title: "Entitlement re-read before each step and before done"
epic: "E4"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E4-T19", "E1-T14"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.2", "decision-logs.md#adr-033", "decision-logs.md#adr-022", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 137, "id": 6263479553, "url": "https://github.com/Keshav0375/FinAdvisor/issues/137"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Re-read the advisor's entitlement before each retrieval or tool step and before done, and abort the turn with ENTITLEMENT_CHANGED if it changed.

## Description
Implement an `EntitlementWatch` in `agent/` (ADR-033; plan E4 round 4: 'Entitlement re-read before each retrieval or tool step and before `done`; a bump aborts the turn with `ENTITLEMENT_CHANGED` and the message `refused` (#2)'). The principal cache (E1-T14, 60 s TTL) is bypassed for this read: a point read of `advisors.entitlement_version` (and the tenant `acl_version`) under the caller's RLS, in a short transaction, before each retrieval call, before each tool dispatch and before emitting `done`. If the value differs from the one in the Principal at turn start, the turn aborts: emit `error {ENTITLEMENT_CHANGED, retryable: false}`, store the assistant message with status `refused`, release no further delta or citation events, and do not write the answer cache. It registers as a `ReleaseCheck` too, so a sentence is not released after a bump. Out of scope: how entitlements are changed (E1, admin).

## Acceptance criteria
- [ ] Given a slow fake LLM and an entitlement bump at token 20 (#2), when the turn runs, then it aborts with ENTITLEMENT_CHANGED, the stored message status is `refused`, no citation event is emitted after the bump and no answer_cache row is written (test_entitlement_bump_aborts_turn, tier PR).
- [ ] Given no bump, when a turn runs with 2 tool iterations, then the entitlement is re-read once before each retrieval, once before each tool dispatch and once before done, and the turn completes (counted point reads).
- [ ] Given a bump between the last sentence and `done`, when checked before done, then the turn aborts rather than finishing end_turn (test).
- [ ] Given the re-read, when its SQL is captured, then it reads `advisors` directly, never the 60 s principal cache (test).
