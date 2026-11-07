---
key: "E7-T18"
title: "Verify eval-judge end to end with RLS on eval_scores"
epic: "E7"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E7-T17"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/09-observability.md#9.6", "deep-dive/05-data-model-and-storage.md#5", "ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Show one sampled turn scored into Langfuse and eval_scores with tenant isolation and no fa_app access.

## Description
Add an end-to-end test and a short runbook docs/eval/online-judge.md: chat turn on the eval tenant sampled at rate 1.0 in test -> outbox -> relay -> eval.sample.v1 -> eval-judge -> row in eval_scores and a Langfuse score (Langfuse local container or recorded API call in CI). Also assert the DB-level properties: tenant B's session cannot read tenant A's eval_scores rows; `fa_app` has no privilege on the table. Set the shipped default `EVAL_SAMPLE_RATE` (0.05-0.10) in the demo profile and note the value in the runbook. Quote the done-when: "The `eval-judge` scores at least one sampled turn end to end into Langfuse and `eval_scores` (tenant RLS applies; `fa_app` has no access to the table)."

## Acceptance criteria
- [ ] E2E test passes: after one sampled turn, `select count(*) from eval_scores where message_id = :id` returns >= 2 (faithfulness and citation) and the Langfuse score exists for the trace.
- [ ] Test: as fa_app, `select * from eval_scores` fails with permission denied.
- [ ] Test: with app.tenant_id set to tenant B, selecting tenant A's eval_scores rows returns 0 rows.
- [ ] A feedback POST in the same test run results in a FeedbackRecorded message on eval.events.v1.
