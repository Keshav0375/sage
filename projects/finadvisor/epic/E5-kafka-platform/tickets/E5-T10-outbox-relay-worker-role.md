---
key: "E5-T10"
title: "outbox-relay worker role"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T9", "E1-T7", "E1-T10"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/06-interfaces-and-contracts.md#6.4", "decision-logs.md#adr-013"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 87, "id": 6155672699, "url": "https://github.com/Keshav0375/FinAdvisor/issues/87"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Publish unpublished outbox rows per tenant in order with at-least-once delivery.

## Description
Implement the `outbox-relay` role (deep-dive/04-components-and-responsibilities.md#4.7; ADR-013; no Debezium). The `outbox` table (E1-T7: `topic, key, event_type, schema_version, payload jsonb, created_at, published_at, attempts`; `id` is the Kafka event_id; partial index on unpublished) and the fa_worker SELECT/INSERT/UPDATE grants (E1-T10) exist. Loop: for each tenant, in a transaction with `app.tenant_id` set, SELECT unpublished rows ORDER BY created_at, id FOR UPDATE SKIP LOCKED (OUTBOX_RELAY_BATCH default 100, OUTBOX_RELAY_POLL_MS default 500, added to deep-dive/06-interfaces-and-contracts.md#6.6 per R53), build the envelope (event_id = outbox id, event_type, schema_version, tenant_id, occurred_at = created_at, payload), produce with the E5-T6 idempotent producer and wait for delivery, then set published_at; on a delivery failure increment `attempts`, stop that tenant's batch (preserving order) and back off, do not skip rows. Emit `outbox_unpublished` (count of unpublished rows) as an OTel gauge now (R55; the metrics conventions module is E9). Several relay instances may run: SKIP LOCKED prevents double claim. Out of scope: writing outbox rows from chat-api/admin (E2-E4), the ACL applier.

## Acceptance criteria
- [ ] Given 5 unpublished outbox rows for tenant A in order, when the relay runs, then 5 records appear on their topics with key = tenant A, in created_at order, and published_at is set on all 5.
- [ ] Given the broker is stopped, when the relay runs, then no row gets published_at, `attempts` increments, the relay stays up, and after the broker restarts all rows are published in order.
- [ ] Given the process is killed after produce but before the published_at commit, when the relay restarts, then the row is produced again with the same event_id (at-least-once) and a consumer using processed_events applies it once (integration test).
- [ ] Given two relay instances and 100 rows, when both run, then every row is published (sink has all 100 event_ids) and the sink dedupes any duplicates to exactly 100.
- [ ] Given rows for tenants A and B, when the relay runs under a connection with app.tenant_id = A, then tenant B's rows are not read in that transaction (RLS test).
- [ ] Given 3 unpublished rows, when the relay has not yet run, then the `outbox_unpublished` gauge reads 3, and 0 after all are published (test with an in-memory OTel metric reader).
