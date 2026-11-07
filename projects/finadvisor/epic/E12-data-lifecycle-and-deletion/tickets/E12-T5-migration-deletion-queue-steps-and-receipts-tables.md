---
key: "E12-T5"
title: "Migration: deletion queue, steps, receipts and ledger tables"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T3", "E1-T8"]
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.11", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.13", "decision-logs.md#adr-29", "decision-logs.md#adr-30"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 309, "id": 6263806861, "url": "https://github.com/Keshav0375/FinAdvisor/issues/309"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Create deletion_requests, erasure_steps, erasure_receipts and erasure_ledger with RLS, partial poll index and grants.

## Description
Implement deep-dive/05-1 5.11 and 5.13 in one Alembic migration (four tables). `deletion_requests (tenant_id, id)`: `scope` in (document, source, advisor, tenant), `subject_ref`, `reason` in (erasure, takedown, source_withdrawal, offboarding, source_kill), `requested_by`, `requested_at`, `status` in (pending, running, executed, windows_open, closed, failed), `claimed_at`, `attempts`, `parent_request_id` (reserved, nullable), a partial index `WHERE status = 'pending'`, and a unique index `(tenant_id, subject_ref) WHERE scope = 'source'` so the purge pull is idempotent on `(tenant_id, purge_id)`. `erasure_steps (tenant_id, request_id, store)`: `status`, `executed_at`, `rows_affected`, `probe_result`, `window_closes_at`, `swept_at`. `erasure_receipts (tenant_id, request_id, phase)`: phase 1 or 2, `receipt jsonb`, `hmac`, `gcs_uri`, `issued_at`. All three: ENABLE and FORCE RLS, policies use `current_setting('app.x')` without missing_ok. Grants per 5.13: INSERT on deletion_requests to `fa_app` only when `app.role = 'tenant_admin'` and tenant matches; `fa_worker` SELECT and UPDATE (status, claimed_at, attempts) on its own non-PUBLIC tenant; no INSERT for `fa_etl_public`; `erasure_steps` and `erasure_receipts` `fa_worker` SELECT, INSERT, UPDATE. Also grant `fa_worker` DELETE on the child tables listed in 4.19 (Postgres step order) and on `pseudonym_map`. Also create `erasure_ledger` (5.11): key `(tenant_id, doc_key, sha256)`, append-only, hashes only, columns `request_id`, `scope_type`, `requested_at`, `released_at`, `released_by`; for advisor and tenant scopes `doc_key` holds `subject:<salted hash>` and `sha256` is the empty string; ENABLE and FORCE RLS; `fa_worker` SELECT and INSERT, SELECT also to `fa_etl_public` and to the sink roles (outbox relay, bq-sink, ETL writers) because ingest and the sinks check tombstones with uncached point reads (E5-T15 helper), no DELETE for anyone, UPDATE of `released_at` and `released_by` only for the operator release command role, no `fa_app` grant (5.13). The `lineage_edges` table is not created here (E11); the uncached sink-guard helper is E5. Out of scope: any worker code.

## Acceptance criteria
- [ ] Given the migration is applied to an empty database, when `alembic downgrade -1` then `upgrade head` run, then both succeed and `information_schema` shows the four tables with RLS forced.
- [ ] Given the leak matrix (L0), when role `fa_app` as tenant A inserts a `deletion_requests` row for tenant B, then it fails; as non-admin role for tenant A it also fails.
- [ ] Given `fa_etl_public`, when it tries INSERT on `deletion_requests`, then permission is denied (privilege test via role_table_grants).
- [ ] Given two inserts of scope `source` with the same `(tenant_id, subject_ref)`, then the second violates the unique index.
- [ ] Given `erasure_ledger`, when any role tries DELETE, or the release role UPDATEs a column other than `released_at` and `released_by`, then permission is denied; an INSERT of a duplicate `(tenant_id, doc_key, sha256)` fails, and the same key for another tenant succeeds (tenant-scoped); and `fa_etl_public`, the outbox relay, bq-sink and ETL writer roles can SELECT it but not INSERT/UPDATE (test `test_erasure_ledger_grants_for_sink_roles`).
- [ ] EXPLAIN of the poll query (status = 'pending' ORDER BY requested_at LIMIT 1 FOR UPDATE SKIP LOCKED) uses the partial index on a 10k-row table.
