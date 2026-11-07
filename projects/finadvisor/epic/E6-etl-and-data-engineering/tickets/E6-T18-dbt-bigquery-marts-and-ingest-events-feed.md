---
key: "E6-T18"
title: "dbt-bigquery marts and the ingest_events feed"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T17", "E6-T13", "E5-T7", "E5-T9", "E5-T11", "E5-T15"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.11", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.8", "decision-logs.md#adr-014", "decision-logs.md#adr-028", "decision-logs.md#adr-029"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 151, "id": 6263506716, "url": "https://github.com/Keshav0375/FinAdvisor/issues/151"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Build dbt-bigquery marts over fa_analytics and map ingest analytics events into ingest_events with a ledger-guarded sink.

## Description
Arch (4.11, 4.8 `dbt`, 5.8): 'Marts are built by `dbt-bigquery`'; 'bq-sink: consumes audit, usage, eval, ingest and ACL topics; writes BigQuery with event-id dedupe' (framework E5-T14; PUBLIC analytics events exempt from the envelope check). Add a dbt-bigquery target with incremental, partition-aware marts (daily ingest summary per tenant from `ingest_events`, rejects per rule per day) using insert_overwrite on day partitions, `maximum_bytes_billed` in the profile, and a `partition_filter` on every source read. Implement the `ingest_events` row mapping for `ingest.analytics.v1` and `chunks.indexed.v1` so the E5-T14 role writes them with event-id dedupe. Round 4: the mapping carries `document_id` and, where the event has it, the ledger key, so E5-T14 calls the E5-T15 guard before writing (tombstoned documents produce no row); the mapping rejects events whose payload has `source='fca_api'` or any text field (FCA content and text never land in BigQuery, ADR-013 amended, ADR-026). dbt sets NO dataset options: time travel comes from the project default of E6-T17 (ADR-029 amended); the dbt profile contains no `max_time_travel_hours`. OpenLineage is not used (dropped, ADR-014 amended). Out of scope: chat/eval/gateway marts, the sink framework.

## Acceptance criteria
- [ ] Given duplicate `ingest.analytics.v1` events with the same event_id, when mapped and written twice, then `ingest_events` has one row.
- [ ] Given an event for a tombstoned document, when the sink writes, then no `ingest_events` row exists; given an event with `source='fca_api'`, then it is rejected and no row exists (test_ingest_mapping_guard_and_fca).
- [ ] Given the dbt-bigquery profile, when parsed, then `maximum_bytes_billed` equals `BQ_MAX_BYTES_BILLED` and no dataset option such as max_time_travel_hours is set (test); a dataset created by a dbt run reads 48 h after the E6-T17 project default (gated job).
- [ ] Given a mart run twice over the same day, when finished, then the row count equals the first run and the query log shows only that day partition; a PUBLIC analytics event is visible only to the PUBLIC view.
