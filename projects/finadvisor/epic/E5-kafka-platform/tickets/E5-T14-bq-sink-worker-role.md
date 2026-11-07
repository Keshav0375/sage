---
key: "E5-T14"
title: "bq-sink worker role"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T7", "E5-T8", "E5-T9", "E6-T17"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/05-data-model-and-storage.md#5.8", "deep-dive/06-interfaces-and-contracts.md#6.4", "decision-logs.md#adr-013"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 91, "id": 6155677330, "url": "https://github.com/Keshav0375/FinAdvisor/issues/91"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Consume the analytics-bound topics and write the fa_analytics BigQuery tables idempotently on event id.

## Description
Implement role `bq-sink` (deep-dive/04-components-and-responsibilities.md#4.7: 'consumes audit, usage, eval, ingest and ACL topics; writes BigQuery with event-id dedupe'; ADR-013; storage in deep-dive/05-data-model-and-storage.md#5.8). Group `cg.bq-sink` on the topics whose catalogue row (deep-dive/06-interfaces-and-contracts.md#6.4) lists it as consumer: acl.changes.v1 (all event types), chat.audit.v1, chat.usage.v1, eval.events.v1; the chunks.indexed.v1 and ingest.analytics.v1 rows go to `ingest_events` through the mapping owned by E6-T18 (plug-in point only here). Built on the E5-T7/T8 consumer framework with the PUBLIC exemption flag on (PUBLIC analytics events are accepted; envelope.tenant_id must still equal the key). Write each event as a row to the fa_analytics tables created by the dataset DDL in E6-T17 (do not create datasets or tables here), using BigQuery insert with `insertId`/MERGE on `event_id` so redelivery does not add a row; respect BQ_DATASET and BQ_MAX_BYTES_BILLED. Map event_type to table by a registry in code. Failed writes retry then go to dlq.v1 via E5-T8. Out of scope: the ingest_events mapping (E6-T18), dbt models, dataset DDL.

## Acceptance criteria
- [ ] Given one event of each consumed event type and a BigQuery emulator or fake client, when consumed, then exactly one row per event lands in the table mapped for its event_type (unit/integration test test_bq_sink_routes_event_types).
- [ ] Given the same event_id delivered twice, when consumed, then the target table holds one row for it (test_bq_sink_dedupes_event_id).
- [ ] Given a PUBLIC-tenant ingest.analytics.v1 event, when consumed, then it is written and not sent to the DLQ; given a PUBLIC event on chat.audit.v1, then the envelope check still applies and mismatching tenant/key goes to dlq.v1 (test_bq_sink_public_exemption).
- [ ] Given the BigQuery client raises on every write, when an event is consumed, then after KAFKA_CONSUMER_MAX_ATTEMPTS attempts one dlq.v1 record exists and the offset is committed (test_bq_sink_failure_dlq).
- [ ] Given WORKER_ROLES=`bq-sink`, when the worker boots, then the role starts (the not-implemented stub from E5-T9 is replaced; test_worker_boots_bq_sink).
