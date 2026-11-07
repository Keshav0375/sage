---
key: "E5-T7"
title: "Consumer framework: dedupe, tenant transaction, envelope check"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T6", "E1-T7", "E1-T10"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/06-interfaces-and-contracts.md#6.4", "deep-dive/05-data-model-and-storage.md#5.2", "decision-logs.md#adr-013"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 84, "id": 6155669333, "url": "https://github.com/Keshav0375/FinAdvisor/issues/84"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Provide a consumer base that dedupes on processed_events and rejects envelope/key mismatch and PUBLIC.

## Description
In `events/consumer.py` build a base consumer (confluent-kafka Consumer, manual commit after the handler transaction, at-least-once). For each message: deserialise via Schema Registry; run the envelope check (deep-dive/04-components-and-responsibilities.md#4.7 and #6.4 consumer rule): if `envelope.tenant_id` != message key or the tenant equals PUBLIC_TENANT_ID, the message is routed to the DLQ hook with reason `envelope_key_mismatch` or `public_tenant_rejected` and is not handled; `bq-sink` is exempt for PUBLIC analytics events via a constructor flag. Otherwise open a DB transaction as `fa_worker` with `app.tenant_id` set from the message key, check/insert `(tenant_id, consumer, event_id)` in `processed_events` (table and RLS exist from E1-T7/E1-T10, do not recreate), run the handler in the same transaction, commit, then commit the Kafka offset. A duplicate (already in processed_events) is skipped without calling the handler. Out of scope: retries and DLQ publishing (E5-T8).

## Acceptance criteria
- [ ] Given the same event delivered twice, when the consumer handles both, then the handler ran once and the state it wrote is unchanged after the second delivery (integration test with Postgres and Kafka).
- [ ] Given a message whose envelope.tenant_id differs from its key, when consumed, then the handler is not called and the DLQ hook receives reason `envelope_key_mismatch`.
- [ ] Given a message for PUBLIC_TENANT_ID on a non-bq-sink consumer, when consumed, then the handler is not called and the hook receives `public_tenant_rejected`; the same message on a consumer with the bq-sink exemption is handled.
- [ ] Given a handler that raises after writing, when consumed, then the handler's write and the processed_events row are both absent (rolled back together) and the offset is not committed.
- [ ] Given the transaction, when the handler runs, then `current_setting('app.tenant_id')` equals the key (test inside the handler).
