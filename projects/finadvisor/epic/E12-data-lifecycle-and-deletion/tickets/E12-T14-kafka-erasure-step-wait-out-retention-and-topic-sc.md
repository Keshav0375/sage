---
key: "E12-T14"
title: "Kafka erasure step: wait out retention and topic-scan probe"
epic: "E12"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E12-T7", "E5-T13"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.14", "decision-logs.md#adr-29", "decision-logs.md#adr-30", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#7"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 291, "id": 6263767461, "url": "https://github.com/Keshav0375/FinAdvisor/issues/291"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Verify subject-bearing topics are delete-policy with 7 d retention and 1 d segments, and probe them after the window.

## Description
StoreStep `kafka`: Kafka is never written to for deletes. The step (a) asserts, through the admin API, that each subject-bearing topic of deep-dive/06 6.4 has cleanup.policy delete, `retention.ms` 7 d and `segment.ms` 1 d, and records a failure if not; (b) records `window_closes_at` = request time + 8 d (7 d retention + segment); (c) the probe, run by erasure-verify after the window (E12-T17), scans the topics for the subject's `pseudonym_id` and event ids and expects none. If the broker is unreachable the step stays `pending` (it must not fail the request; #7). Out of scope: topic creation (E5).

## Acceptance criteria
- [ ] Given a topic with `cleanup.policy=compact`, when the step runs, then it records `KAFKA_TOPIC_POLICY_VIOLATION` for that topic and the receipt step is not `done`.
- [ ] Given Kafka stopped, when an erasure is issued, then Postgres steps finish, the kafka step is `pending`, and after Kafka restarts all steps finish and phase-1 receipt is issued exactly once (#7; compose integration test).
- [ ] Given a fixture topic holding the subject's pseudonym id after the window, when the scan probe runs, then it reports the leftover and the step is not closed.
- [ ] The step issues no produce or delete-records call to Kafka (spy on the client).
