---
key: "E10-T12"
title: "Terraform Cloud Scheduler triggers and paused-state drift"
epic: "E10"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E10-T10"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.12", "deep-dive/04-components-and-responsibilities.md#4.8", "ADR-020"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Create the seven Scheduler triggers for the jobs with ignore_changes so demo scripts can pause and resume them.

## Description
4.12: 'Cloud Scheduler: triggers etl, etl-public, dbt, maintenance, eval, redteam and demo-ttl. demo-down pauses all except demo-ttl.' 4.8: maintenance runs hourly while the demo is up; demo-ttl hourly. Schedule expressions for etl, etl-public, dbt, eval, redteam are not given in the arch (see questions); use variables with the defaults documented in the PR and keep the paused state controlled by the scripts.

Build terraform/scheduler.tf: google_cloud_scheduler_job for each of the 7, each calling the Cloud Run Admin API run endpoint for its job with an OAuth token of a dedicated scheduler SA that has run.invoker/run.jobs.run on those jobs only. maintenance cron `0 * * * *`, demo-ttl `0 * * * *`. Initial state: all paused except demo-ttl. lifecycle.ignore_changes covering the pause state attribute so `terraform apply` does not fight the scripts (see questions: the arch lists activation_policy, min_instance_count and manual_instance_count only; this ticket adds the Scheduler state because the demo scripts change it).

Out of scope: job code and the pause/resume calls themselves (E10-T18, E10-T17).

## Acceptance criteria
- [ ] `terraform plan` lists 7 google_cloud_scheduler_job resources named after the jobs; demo-ttl and maintenance have schedule `0 * * * *` (terraform test)
- [ ] After `gcloud scheduler jobs resume etl` then `terraform plan -detailed-exitcode` returns 0
- [ ] Triggering `gcloud scheduler jobs run demo-ttl` starts an execution of the demo-ttl Cloud Run job (execution count +1 in `gcloud run jobs executions list`)
