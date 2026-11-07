---
key: "E5-T11"
title: "acl-applier worker role (polls acl_change_requests)"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T9", "E5-T10", "E1-T7", "E1-T10"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/04-2-source-lifecycle-and-cells.md#4.17", "deep-dive/05-data-model-and-storage.md#5.2", "decision-logs.md#adr-022", "decision-logs.md#adr-028"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 88, "id": 6155673894, "url": "https://github.com/Keshav0375/FinAdvisor/issues/88"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Poll acl_change_requests in Postgres and apply ACL and reclassification changes under the document lock, with no Kafka on this path.

## Description
Implement role `acl-applier` (round 4, ADR-022 amended, R4-D7). Quote ADR-022 amended: 'The `acl-applier` polls `acl_change_requests` in Postgres with `FOR UPDATE SKIP LOCKED`; the outbox row and `acl.changes.v1` remain for analytics only. A Kafka outage therefore cannot delay an ACL tightening'; and 'Applying a change takes the per-document advisory lock first and the tenant `corpus_version` row last (ADR-028)'. The role is a POLLING worker: no Kafka consumer, no consumer group, no topic subscription; it needs no Kafka credentials. `acl.changes.v1` is no longer consumed by the applier (it stays a topic for `cg.bq-sink`).

Loop (ACL_APPLIER_POLL_MS, default 500; ACL_APPLIER_BATCH, default 10, both added to 6.6): as `fa_worker`, in one transaction per request with `app.tenant_id` set from the row's tenant: `SELECT ... FROM acl_change_requests WHERE status='pending' ORDER BY requested_at LIMIT 1 FOR UPDATE SKIP LOCKED` (partial index from E1-T7); take `pg_advisory_xact_lock(hash(tenant_id, document_id))` first (same lock as the indexer and erasure, 4.17); UPDATE only the ACL columns (`tier_required`, `jurisdiction`) on `documents` and `chunks` of that document (own-tenant WITH CHECK); set the request `applied` with `applied_at`; DELETE `answer_cache` rows whose `source_document_ids` contain the document (GIN index); `UPDATE tenants SET acl_version = acl_version + 1` on the own row LAST. Insert one outbox row `AclChangeApplied {request_id, acl_version}` on `acl.changes.v1` for analytics. The request actions are `update_acl` and reclassification only; document delete is not handled here (it is a `deletion_requests` row executed by the erasure-worker, E12; an `acl_change_requests` row with action `delete` is marked `failed` with `error_code='UNSUPPORTED_ACTION'`). Idempotent: an `applied` request is skipped. A document that is missing gives `failed` with `error_code` and no version bump. No embedding call is made. Emit `acl_apply_lag_s` (applied_at - requested_at) as an OTel histogram. Out of scope: the admin endpoint (E4-T24), entitlement changes, the end-to-end Kafka-down test (E5-T12).

## Acceptance criteria
- [ ] Given a pending update_acl request on document D, when the applier polls once, then all `chunks` rows of D have the new tier_required/jurisdiction, the request is `applied`, and `tenants.acl_version` is previous + 1 (integration test, no Kafka broker running).
- [ ] Given the applier module and its worker role, when `lint-imports` and a grep run, then it imports no Kafka consumer or producer and `WORKER_ROLES=acl-applier` starts with KAFKA_* unset (test_acl_applier_no_kafka).
- [ ] Given answer_cache rows citing D and rows citing another document, when applied, then only the rows citing D are deleted; the Voyage mock records 0 calls.
- [ ] Given two applier instances and 50 pending requests, when both poll, then each request is applied exactly once (acl_version increments by 50, no row locked twice; SKIP LOCKED test).
- [ ] Given a transaction trace, when a request is applied, then the statements run in the order advisory lock, document UPDATEs, cache purge, `tenants` UPDATE last (test asserting order from pg_stat_statements or a statement log).
- [ ] Given a request for a missing document or action `delete`, when polled, then status is `failed` with a non-null error_code and acl_version is unchanged; `acl_apply_lag_s` has one sample within 1 s of applied_at - requested_at for an applied request.
