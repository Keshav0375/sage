---
key: "E7-T13"
title: "Add the weekly full eval run with CI lower bounds"
epic: "E7"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E7-T21", "E7-T11", "E7-T25", "E7-T26"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/02-quality-attributes.md#2.10", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "deep-dive/09-observability.md#9.9", "decision-logs.md#adr-017", "decision-logs.md#adr-037"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 168, "id": 6263537287, "url": "https://github.com/Keshav0375/FinAdvisor/issues/168"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Run the full 200-item set and the guardrail sets weekly and before demos, reporting cluster-level lower bounds.

## Description
Add a scheduled workflow `eval-full.yml` (cron weekly plus workflow_dispatch for before-demo runs) that runs `jobs eval --subset full --layers l1,l2,l3` against the answer model, then the guardrail runs of E7-T25 and E7-T26, applies `scripts.eval_gate` using cluster-level CI lower bounds for faithfulness and citation, and publishes a Markdown report (metrics, CI low/high, per-slice breakdown with slices under 30 items marked exact or exploratory, comparison with baseline, skipped private count) to the workflow summary and to Langfuse, and emits EvalRunCompleted. The weekly run is edge case #21 of deep-dive/07 7.4 (slice G, the injection-in-document slice, plus LLMail-wrapped chunks; ASR line <= 3 of 300). It is capped by `EVAL_BUDGET_USD` (E7-T5). Quote ADR-017: "the full set runs weekly and before demos". Cloud Scheduler/Cloud Run job scheduling is E10; this ticket is the CI/GitHub-hosted run only, where the private bucket is mounted only if the runner provides it.

## Acceptance criteria
- [ ] After a workflow_dispatch run the summary contains ci_low for faithfulness and citation as numbers; a test on the report generator fails if any is missing.
- [ ] The result JSON has `n_cases` equal to 200 when the private bucket is mounted, and `n_cases + skipped_private` equal to 200 otherwise (test on the result schema).
- [ ] The report contains the injection ASR line (count of 300) and the PII recall line from E7-T25 and E7-T26 results; the generator test fails if either is absent.
- [ ] A forced faithfulness lower bound below 0.90 in a stub run makes the job fail (unit test on the report/gate step).
