---
key: "E6-T12"
title: "Dagster partitions and the etl job entrypoint"
epic: "E6"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E6-T4", "E6-T2"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/04-components-and-responsibilities.md#4.14", "decision-logs.md#adr-014"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Make tenant x dt partitions materialize end to end as one Cloud Run job invocation.

## Description
Arch (4.8 `etl`; Flow 2): 'trigger tenant x date partition' from Cloud Scheduler; 'Daemon-less'. Add the bronze asset (E6-T4) to the Dagster definitions with a static tenant partition set read from `tenants` (kind='firm') crossed with a daily partition; `jobs etl --tenant <slug> --dt <date>` (and `--backfill-from/--to`) materializes that partition and exits non-zero on failure; downstream stages are Kafka consumers so the job only produces `docs.bronze.v1`. Replays republish `docs.bronze.v1` for the partition without refetching. Role `fa_etl`. Out of scope: Terraform for Cloud Run job and Scheduler (infra epic).

## Acceptance criteria
- [ ] Given tenant slug and date, when `jobs etl --tenant a --dt 2026-01-01` runs, then only that partition's documents are published (test counts messages)
- [ ] Given an invalid tenant slug, when run, then exit code != 0 and nothing is published (test)
- [ ] Given `--backfill-from/--to` over 3 days, when run, then 3 partition runs are recorded in the dagster DB (integration)
