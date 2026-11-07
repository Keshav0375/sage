---
key: "E6-T18"
title: "dbt-bigquery marts and ingest_events feed"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T17", "E6-T13", "E5-T7", "E5-T9", "E5-T11"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.11", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.8", "decision-logs.md#adr-014"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Build dbt-bigquery marts over fa_analytics and land ingest analytics events into ingest_events.

## Description
Arch (4.11, 4.8 `dbt`, 5.8): 'Marts are built by `dbt-bigquery`'; 'bq-sink: consumes audit, usage, eval, ingest and ACL topics; writes BigQuery with event-id dedupe' (bq-sink framework is E5; PUBLIC analytics events are exempt from the envelope check). Add a dbt-bigquery target with incremental, partition-aware marts (e.g. daily ingest summary per tenant from `ingest_events`, rejects per rule per day) using insert_overwrite on day partitions, `maximum_bytes_billed` set in the profile, and a `partition_filter` on every source read. Implement the `ingest_events` row mapping for `ingest.analytics.v1` and the ingest topic events so the E5 bq-sink role can write them with event-id dedupe. Out of scope: chat/eval/gateway marts (other epics) and the sink framework.

## Acceptance criteria
- [ ] Given duplicate `ingest.analytics.v1` events with the same event_id, when mapped and written twice, then `ingest_events` has one row (test)
- [ ] Given the dbt-bigquery profile, when parsed, then `maximum_bytes_billed` is set and equals `BQ_MAX_BYTES_BILLED` (test)
- [ ] Given a mart run twice over the same day, when finished, then the row count equals the first run (no duplicates, no full-table rewrite: query log shows only that day partition)
- [ ] A PUBLIC analytics event is written with PUBLIC tenant id and visible only to the PUBLIC view (test)
