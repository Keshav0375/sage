---
key: "E7-T17"
title: "Implement the eval-judge worker role"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T14", "E1-T21", "E7-T1", "E7-T16"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/09-observability.md#9.6", "deep-dive/06-interfaces-and-contracts.md#6.4", "decision-logs.md#adr-017", "decision-logs.md#adr-039"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 172, "id": 6263545314, "url": "https://github.com/Keshav0375/FinAdvisor/issues/172"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Consume eval.sample.v1, read the redacted text from Postgres by message_id, judge with Haiku 5.5 and write Langfuse scores and eval_scores.

## Description
Add worker role `eval-judge` (selected via WORKER_ROLES) on the E5 Kafka consumer framework, group `cg.eval-judge`. For each `TurnSampled` (ids, hashes, flags; no text, E7-T16): envelope check (tenant_id equals key and not PUBLIC, else dlq.v1); dedupe on message_id + metric via `processed_events`; in a transaction with `app.tenant_id` set, read the redacted question, answer and cited excerpts from Postgres `messages` by `message_id` under the tenant's `fa_worker` role (06 9.6; text never travels on Kafka, ADR-039 M5). If the message row is gone (erased by E12) skip the message, count `eval_judge_skipped_erased_total`, write no score and no outbox row. Otherwise score faithfulness and citation with `LLM_MODEL_JUDGE` (claude-haiku-5-5, must differ from the answer model) using the calibrated prompt from E7-T1, insert rows into `eval_scores` {message_id, judge_model, metric, score, rationale (redacted), created_at}, send scores to Langfuse (no Langfuse-side evaluators), and write a `JudgeScored` outbox row for `eval.events.v1` (ids and scores only).

Quote 4.7: "scores the redacted question / answer / cited excerpts with `claude-haiku-5-5` ..., writes scores to Langfuse and `eval_scores`, emits `JudgeScored` on `eval.events.v1`." Out of scope: the sampler (E7-T16), the table and grants (E1).

## Acceptance criteria
- [ ] Unit test: a message whose envelope tenant_id differs from the key goes to dlq.v1 with a reason and writes no score.
- [ ] Unit test: delivering the same message twice yields one eval_scores row per metric.
- [ ] Unit test: worker raises at boot if the judge model equals the answer model.
- [ ] Unit test: a TurnSampled whose `messages` row has been deleted writes no eval_scores row, no outbox row and increments the skipped counter (test `test_eval_judge.py::test_erased_message_skipped`).
- [ ] Integration test (CI Postgres + Kafka, stub judge): a TurnSampled message with no text in its payload produces rows in eval_scores for the right tenant, the judge input is the `messages` text, and an outbox JudgeScored row exists.
