---
key: "E5-T14"
title: "bq-sink worker role"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T7", "E5-T8", "E5-T9", "E5-T15", "E6-T17"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.8", "deep-dive/06-interfaces-and-contracts.md#6.4", "decision-logs.md#adr-013", "decision-logs.md#adr-028"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 91, "id": 6155677330, "url": "https://github.com/Keshav0375/FinAdvisor/issues/91"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Consume the analytics-bound topics and write the fa_analytics tables idempotently on event id, guarded by the uncached ledger helper.

## Description
Implement role `bq-sink` (4.7: consumes audit, usage, eval, ingest and ACL topics; writes BigQuery with event-id dedupe). Group `cg.bq-sink` on the topics whose 6.4 row lists it: acl.changes.v1 (analytics and audit only), chat.audit.v1, chat.usage.v1, eval.events.v1; chunks.indexed.v1 and ingest.analytics.v1 go to `ingest_events` through the mapping owned by E6-T18 (plug-in point only). Built on the E5-T7/T8 framework with the PUBLIC exemption flag on (envelope.tenant_id must still equal the key). Write each event as a row to the fa_analytics tables from E6-T17 (do not create datasets or tables here), using BigQuery insert with `insertId` or MERGE on `event_id`; respect BQ_DATASET and BQ_MAX_BYTES_BILLED. Map event_type to table by a registry in code. Failed writes retry then go to dlq.v1 (E5-T8).

Round 4 additions. (1) Sink guard (ADR-028): before each write the sink calls the E5-T15 uncached helper for events that carry a document reference; a hit drops the message with a counted reason `tombstoned`; if the ledger cannot be read the sink PAUSES (no write, no offset commit, no DLQ). (2) No text in BigQuery (ADR-013 amended, R4-D19 M5, test #15): the sink rejects (to dlq.v1, reason `text_field_rejected`) any payload containing a name from `FORBIDDEN_TEXT_FIELDS` (E5-T4), and rejects any event whose payload `source` is `fca_api` (reason `fca_content_rejected`); FCA content never lands in BigQuery (ADR-026). (3) `acl.changes.v1` carries `pseudonym_id`, not `advisor_id`. Out of scope: the ingest_events mapping (E6-T18), dbt models, dataset DDL.

## Acceptance criteria
- [ ] Given one event of each consumed event type and a BigQuery fake, when consumed, then exactly one row per event lands in its mapped table (test_bq_sink_routes_event_types).
- [ ] Given the same event_id delivered twice, when consumed, then the target table holds one row (test_bq_sink_dedupes_event_id).
- [ ] Given an event for a document with an unreleased ledger tombstone, when consumed, then no row is written and a `tombstoned` drop is counted; given the ledger read raises, then nothing is written, the offset is not committed and the dlq.v1 topic is unchanged (test_bq_sink_guard_blocks_and_pauses).
- [ ] Given a chat.audit.v1 payload with an `answer` or `excerpt` field, and given a payload with `source='fca_api'`, when consumed, then each lands in dlq.v1 with reasons `text_field_rejected` and `fca_content_rejected` and no BigQuery row exists (test_bq_sink_rejects_text_and_fca).
- [ ] Given a PUBLIC ingest.analytics.v1 event, when consumed, then it is written and not sent to the DLQ; given a PUBLIC event on chat.audit.v1 with mismatching key, then it goes to dlq.v1.
- [ ] Given the BigQuery client raises on every write, when an event is consumed, then after KAFKA_CONSUMER_MAX_ATTEMPTS attempts one dlq.v1 record exists and the offset is committed; given WORKER_ROLES=`bq-sink`, the role boots.
