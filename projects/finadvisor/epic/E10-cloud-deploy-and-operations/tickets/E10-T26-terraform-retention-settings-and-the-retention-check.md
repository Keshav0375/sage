---
key: "E10-T26"
title: "Terraform retention settings and the retention check"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T6", "E10-T14", "E5-T13", "E12-T13"]
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.14", "deep-dive/06-interfaces-and-contracts.md#6.6", "deep-dive/04-components-and-responsibilities.md#4.12", "decision-logs.md#adr-029", "decision-logs.md#adr-039"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Set and check every retention value of the erasure promise in Terraform: BigQuery 48 h time travel, GCS soft delete 0, Cloud SQL backups and PITR 7 d, delete-policy topics, logs 7 d.

## Description
Implements the E10 round-4 line "Retention settings in Terraform and checked" (ADR-029, ADR-039 V2, 5.14 table). Values and owners:
- BigQuery: the project default `default_max_time_travel_hours = 48` through `ALTER PROJECT ... SET OPTIONS` per region (a DDL, not a Terraform resource, V2), run as a step of the terraform-apply workflow (E10-T14) by `scripts/bq_set_default_time_travel.sh` of E12-T13 after apply; plus `max_time_travel_hours = 48` on the `fa_analytics` dataset in Terraform (variable `bq_max_time_travel_hours`, validation equal to 48, the config `BQ_MAX_TIME_TRAVEL_HOURS`); dbt sets no dataset options.
- GCS data bucket (`GCS_DATA_BUCKET`): `soft_delete_policy { retention_duration_seconds = 0 }`, versioning off, no retention policy or lock (5.14: "soft_delete_policy 0; versioning off; never a retention lock").
- Cloud SQL: backups 7 d and PITR log retention 7 d are set in E10-T6; this ticket only checks them.
- Kafka: the subject-bearing topics of 6.4 are created by E5-T13 with cleanup.policy delete, `retention.ms` 7 d and `segment.ms` 1 d; this ticket only checks the plan.
- Logs: the Cloud Logging `_Default` bucket retention 7 d (`google_logging_project_bucket_config`, no PII in logs is tested by E9-T9).
Add `scripts/check_retention.py` with `--plan plan.json` (static) and `--live`: Cloud SQL `retained_backups` 7 and `transaction_log_retention_days` 7; bucket soft delete 0, versioning false, no retention policy; BigQuery project default and every dataset including dbt-created ones equal 48 (the live mode calls `check_bq_time_travel()` of E12-T13); the subject-bearing topic list (a tfvar) all have delete, 604800000 ms and 86400000 ms; `_Default` retention 7 d. Run it in the terraform-plan workflow and by `make check-retention`. Where the arch says a value is a documented window and not observable (BigQuery fail-safe, PITR logs), the script prints it as `documented` and never as measured.

Out of scope: the E12 spike on backup expiry while stopped (E12-T1), the reconcile alert on settings (E9-T19).

## Acceptance criteria
- [ ] Unit tests with fixture plan JSON: a clean fixture passes; a bucket with soft delete 604800 fails; versioning true fails; a retention policy present fails; `retained_backups` 8 fails; PITR days 3 fails; a topic with `retention.ms` 1209600000 fails; `_Default` retention 30 fails; a dataset with `max_time_travel_hours` 168 fails (one test per case, `test_check_retention.py`).
- [ ] Given a plan without the apply workflow's BigQuery step, When the workflow lint test runs, Then it fails naming `bq_set_default_time_travel.sh`.
- [ ] `terraform plan` shows the data bucket with soft delete 0 and the dataset with `max_time_travel_hours` 48; `bq_max_time_travel_hours = 72` fails validation.
- [ ] `make check-retention --live` on the real project exits 0 and prints each value with its source; output attached.
- [ ] The output marks BigQuery fail-safe and Cloud SQL PITR logs `documented` (a test asserts the word `measured` does not appear on those lines).
