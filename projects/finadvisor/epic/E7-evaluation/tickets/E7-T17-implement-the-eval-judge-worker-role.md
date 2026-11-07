---
key: "E7-T17"
title: "Implement the eval-judge worker role"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T14", "E1-T21", "E7-T1", "E7-T16"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/09-observability.md#9.6", "deep-dive/06-interfaces-and-contracts.md#6.4", "ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Consume eval.sample.v1, judge with Haiku 5.5 and write Langfuse scores and eval_scores.

## Description
Add worker role `eval-judge` (selected via WORKER_ROLES) on the E5 Kafka consumer framework, group `cg.eval-judge`. For each `TurnSampled`: envelope check (tenant_id equals key and not PUBLIC, else dlq.v1), dedupe on message_id + metric via `processed_events`, score faithfulness and citation with `LLM_MODEL_JUDGE` (claude-haiku-5-5, must differ from the answer model) using the calibrated prompt from E7-T1, in one transaction with `app.tenant_id` set insert rows into `eval_scores` {message_id, judge_model, metric, score, rationale (redacted), created_at} as `fa_worker`, send scores to Langfuse (no Langfuse-side evaluators), and write a `JudgeScored` outbox row for `eval.events.v1`. Quote 4.7: "scores the redacted question / answer / cited excerpts with `claude-haiku-5-5` ..., writes scores to Langfuse and `eval_scores`, emits `JudgeScored` on `eval.events.v1`." Out of scope: the sampler (T16), the table and grants (E1).

## Acceptance criteria
- [ ] Unit test: a message whose envelope tenant_id differs from the key goes to dlq.v1 with a reason and writes no score.
- [ ] Unit test: delivering the same message twice yields one eval_scores row per metric.
- [ ] Unit test: worker raises at boot if the judge model equals the answer model.
- [ ] Integration test (CI Postgres + Kafka, stub judge): a TurnSampled message produces rows in eval_scores for the right tenant and an outbox JudgeScored row.
