---
key: "E6-T17"
title: "BigQuery dataset: partitioned tables, authorized views, row policies"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T2"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.11", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.8", "decision-logs.md#adr-014"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Create fa_analytics tables with day partitioning, tenant clustering, per-tenant authorized views and row access policies.

## Description
Arch (4.11, 5.8): dataset `fa_analytics`, tables `chat_audit`, `chat_usage`, `eval_events`, `gateway_audit`, `acl_changes`, `ingest_events`; 'day-partitioned, clustered by `tenant_id`; per-tenant authorized views (primary isolation) plus row access policies (second layer); `maximum_bytes_billed` on every query'; 'redacted text only'. Implement DDL as code in the repo (`bigquery/` SQL or Python module `etl/bq/schema.py`, applied by an idempotent `jobs`-callable command) with `BQ_DATASET` and `BQ_MAX_BYTES_BILLED`; partition by `DATE(event_time)` with `require_partition_filter`; cluster by `tenant_id`; per-tenant authorized view created on tenant onboarding (a function `ensure_tenant_view(tenant_id)`) in a separate views dataset, authorized on the base dataset; a row access policy per tenant as second layer. All query helpers pass `maximum_bytes_billed=BQ_MAX_BYTES_BILLED`. Out of scope: the bq-sink writer, onboarding hook wiring beyond a callable function.

## Acceptance criteria
- [ ] Given the applied DDL, when table metadata is read, then each of the 6 tables has `time_partitioning.type=DAY` and `clustering_fields[0]=='tenant_id'` (test against BQ emulator or real test dataset)
- [ ] Given rows for tenants A and B, when a query runs through tenant A's authorized view, then only tenant A rows return (integration)
- [ ] Given a client helper, when a query is built, then `maximum_bytes_billed` equals `BQ_MAX_BYTES_BILLED` and a query without it is rejected by the wrapper (unit test)
- [ ] Running the DDL command twice is a no-op (idempotency test)
