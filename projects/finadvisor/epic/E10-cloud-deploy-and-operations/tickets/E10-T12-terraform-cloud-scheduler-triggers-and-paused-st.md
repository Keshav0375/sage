---
key: "E10-T12"
title: "Terraform Cloud Scheduler triggers and paused-state drift"
epic: "E10"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E10-T10", "E10-T25"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.12", "deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/09-observability.md#9.7", "decision-logs.md#adr-020", "decision-logs.md#adr-034"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 233, "id": 6263641116, "url": "https://github.com/Keshav0375/FinAdvisor/issues/233"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Create the ten Scheduler triggers for the jobs with ignore_changes so demo scripts can pause and resume them.

## Description
4.12: 'Cloud Scheduler: triggers etl, etl-public, dbt, maintenance, reconcile, erasure-verify, eval, redteam and demo-ttl, plus the daily `ledger-export` row (R4-D20 Q5). demo-down pauses all except demo-ttl. The canary and the erasure job are run by demo-up, not by a cron.' 4.8: maintenance runs hourly while the demo is up and demo-ttl hourly; 9.7: `reconcile` runs hourly only while the system runs. Schedule expressions for etl, etl-public, dbt, eval, redteam and erasure-verify are not given in the arch (see the report's questions); use variables with the defaults documented in the PR and keep the paused state controlled by the scripts.

Build terraform/scheduler.tf: google_cloud_scheduler_job for each of the 10, each calling the Cloud Run Admin API run endpoint for its job (the E12 jobs `reconcile` and `erasure-verify` are defined in E10-T25) with an OAuth token of a dedicated scheduler SA that has run.invoker/run.jobs.run on those jobs only. maintenance cron `0 * * * *`, demo-ttl `0 * * * *`, reconcile `0 * * * *`; erasure-verify `30 * * * *` hourly while the system runs (R4-D20 Q8); ledger-export daily `0 3 * * *` (variable; the hour is not in the arch). `erasure-replay` has no trigger: it is manual after any restore. There is NO trigger for `erasure-canary`, `erasure-replay` or the erasure job: `demo-up` runs them (E10-T18, E10-T27) and a test asserts it. Initial state: all paused except demo-ttl. lifecycle.ignore_changes covering the pause state attribute so `terraform apply` does not fight the scripts (the arch lists activation_policy, min_instance_count and manual_instance_count only; this ticket adds the Scheduler state because the demo scripts change it).

Out of scope: job code and the pause/resume calls themselves (E10-T16, E10-T18).

## Acceptance criteria
- [ ] `terraform plan` lists 10 google_cloud_scheduler_job resources named after the jobs; demo-ttl, maintenance and reconcile have schedule `0 * * * *` (terraform test)
- [ ] Given the plan JSON, then no scheduler job targets `erasure-canary`, `erasure-replay` or the erasure job (terraform test `no_cron_for_canary_or_erasure`)
- [ ] After `gcloud scheduler jobs resume reconcile` then `terraform plan -detailed-exitcode` returns 0
- [ ] Triggering `gcloud scheduler jobs run demo-ttl` starts an execution of the demo-ttl Cloud Run job (execution count +1 in `gcloud run jobs executions list`)
