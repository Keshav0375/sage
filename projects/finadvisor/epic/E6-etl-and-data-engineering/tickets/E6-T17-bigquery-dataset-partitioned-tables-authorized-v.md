---
key: "E6-T17"
title: "BigQuery dataset: partitioned tables, views, 48 h time travel"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T2"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.11", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.8", "decision-logs.md#adr-014", "decision-logs.md#adr-029", "decision-logs.md#adr-039"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 150, "id": 6263505830, "url": "https://github.com/Keshav0375/FinAdvisor/issues/150"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Create fa_analytics tables with partitioning, tenant clustering, authorized views, row policies and the project-default 48 h max time travel.

## Description
Arch (4.11, 5.8): dataset `fa_analytics`, tables `chat_audit`, `chat_usage`, `eval_events`, `gateway_audit`, `acl_changes`, `ingest_events`; 'day-partitioned, clustered by `tenant_id`; per-tenant authorized views (primary isolation) plus row access policies (second layer); `maximum_bytes_billed` on every query'. DDL as code in the repo (`etl/bq/schema.py` or `bigquery/` SQL, applied by an idempotent `jobs`-callable command) with BQ_DATASET and BQ_MAX_BYTES_BILLED; partition by `DATE(event_time)` with `require_partition_filter`; cluster by `tenant_id`; `ensure_tenant_view(tenant_id)` in a separate views dataset authorized on the base dataset; a row access policy per tenant; all query helpers pass `maximum_bytes_billed`. Subject-bearing tables (`chat_audit`, `chat_usage`, `eval_events`, `acl_changes`) have a `pseudonym_id` column and no text columns; no table holds FCA content or answer text (ADR-013 amended, ADR-026).

Round 4 (ADR-029 amended 2026-11-07, R4-D18 V2, ADR-039): BigQuery time travel is set by the PROJECT default: the DDL command runs `ALTER PROJECT ... SET OPTIONS (default_max_time_travel_hours = 48)` for the dataset region (idempotent), so every new dataset, including dbt-created ones, inherits it; dbt-bigquery sets NO dataset options (not documented). The per-dataset `max_time_travel_hours = 48` is kept only as a CHECK: the same command reads `INFORMATION_SCHEMA.SCHEMATA_OPTIONS` for every dataset in the project and exits non-zero if any value differs. Out of scope: the bq-sink writer (E5-T14), onboarding hook wiring.

## Acceptance criteria
- [ ] Given the applied DDL, when table metadata is read, then each of the 6 tables has `time_partitioning.type=DAY` and `clustering_fields[0]=='tenant_id'`; no column named answer, excerpt, question or text exists in any table (test).
- [ ] Given the DDL command run on a project whose default is unset, when finished, then the project default is 48 h and a dataset created afterwards (by a plain CREATE SCHEMA) reads `max_time_travel_hours = 48` (test_project_default_time_travel_48h; gated job on a real test project, since an emulator may not model it).
- [ ] Given a dataset whose time travel is 168 h, when the check runs, then it exits non-zero naming the dataset (negative control).
- [ ] Given rows for tenants A and B, when a query runs through tenant A's authorized view, then only tenant A rows return; a query without `maximum_bytes_billed` is rejected by the wrapper; running the DDL twice is a no-op.
