---
key: "E7-T13"
title: "Add the weekly full eval run with CI lower bounds"
epic: "E7"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E7-T4", "E7-T11"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Run the full golden set weekly and before demos, reporting lower bounds.

## Description
Add a scheduled workflow `eval-full.yml` (cron weekly plus workflow_dispatch for before-demo runs) that runs `jobs eval --subset full --layers l1,l2,l3` against the answer model, applies `scripts.eval_gate` using CI lower bounds for faithfulness and citation, publishes a Markdown report (metrics, CI low/high, per-category breakdown, comparison with baseline) to the workflow summary and to Langfuse, and emits EvalRunCompleted. Quote ADR-017: "the full set runs weekly and before demos". Cloud Scheduler/Cloud Run job scheduling is E10; this ticket is the CI/GitHub-hosted run only.

## Acceptance criteria
- [ ] After a workflow_dispatch run the summary contains ci_low for faithfulness and citation as numbers; a test on the report generator fails if any is missing.
- [ ] The run uses the full set (>= 280 cases) asserted by the result JSON `n_cases`.
- [ ] A forced faithfulness lower bound below 0.90 in a stub run makes the job fail (unit test on the report/gate step).
