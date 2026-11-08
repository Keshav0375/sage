---
key: "E12-T13"
title: "BigQuery erasure step: batched DML and settings check"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T8", "E6-T17", "E12-T2"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.14", "decision-logs.md#adr-29", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#23", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#31"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 290, "id": 6263761853, "url": "https://github.com/Keshav0375/FinAdvisor/issues/290"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Run hourly batched DML on references older than 30 min across every table and view, and verify the 48 h time-travel setting.

## Description
StoreStep `bigquery`: enumerate every table and view of the tenant's dataset from INFORMATION_SCHEMA (including dbt-created ones) and, once per `ERASURE_BQ_BATCH_INTERVAL_MIN` (60) run one batched DML per table deleting rows whose `event_id` or `pseudonym_id` is in the pending reference set AND whose event time is older than `ERASURE_BQ_MIN_AGE_MIN` (30; the streaming buffer blocks DML on younger rows, #23). Younger references stay pending and are picked up by the next batch. Probe: current-row count 0, and `bq_time_travel_probe` from E12-T2 for the 48 h window; `window_closes_at` = now + 14 d, `window_kind` documented for the fail-safe. Add a check `check_bq_time_travel()` (also called by reconcile in E12-T23) that fails when the project default `default_max_time_travel_hours` or any dataset has `max_time_travel_hours` other than 48, and a `scripts/bq_set_default_time_travel.sh` that runs `ALTER PROJECT ... SET OPTIONS (default_max_time_travel_hours = 48)` per region (ADR-029 amendment 2). Out of scope: dbt models, Terraform.

## Acceptance criteria
- [ ] Given events inserted 5 min ago for a subject and erasure requested, when the first batch runs, then those rows remain and the step stays pending; after the clock passes 30 min the next batch deletes them and none remain (#23; BigQuery emulator or scratch dataset).
- [ ] Given a dbt-created view-backed table and a plain table both holding the subject, when the step runs, then both have 0 rows (enumeration covers dbt-created objects).
- [ ] Given a dataset with `max_time_travel_hours = 168`, when `check_bq_time_travel()` runs, then it returns a violation naming the dataset (#31).
- [ ] Given two tenants' rows in separate datasets, when A is erased, then B's counts are unchanged (#4).
- [ ] The step records `window_closes_at` 14 d out and marks the fail-safe `documented`, never `observed`.
