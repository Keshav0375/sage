---
key: "E1-T4"
title: "Migration: tenants and advisors tables"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T3"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.1", "deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.12", "decision-logs.md#adr-002", "decision-logs.md#adr-031", "decision-logs.md#adr-032"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 20, "id": 6155592486, "url": "https://github.com/Keshav0375/FinAdvisor/issues/20"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The tenants and advisors tables exist with all target columns, constraints and FORCE RLS, and the PUBLIC tenant row is seeded.

## Description
Add an Alembic revision (0002 or later; E0 owns the immutable baseline 0001 = MVP schema.sql) creating, as `fa_owner`, the two identity tables per deep-dive/05-data-model-and-storage.md §5.2:

- `tenants` (key `id uuid`): `slug` unique, `display_name`, `kind` CHECK in (`firm`,`public`), `idp_tenant_id` unique (nullable for the PUBLIC row), `corpus_version bigint` default 0, `acl_version bigint` default 0, `budgets jsonb` default `{}` (values set in E4), `shard_id text` (seam, D2), `status`, `created_at`.
- `advisors` (key `(tenant_id, id)`): `idp_uid` (token `sub`) with unique `(tenant_id, idp_uid)`, `display_name`, `role` CHECK in (`advisor`,`compliance_officer`,`tenant_admin`), `tier smallint CHECK 1..4`, `jurisdictions text[]` CHECK subset of (`US`,`EU`,`UK`), `licenses text[]`, `entitlement_version bigint` default 0, `status`, FK `tenant_id` to `tenants(id)`.

Both tables: `ALTER TABLE ... ENABLE ROW LEVEL SECURITY; ... FORCE ROW LEVEL SECURITY;` at creation (no policy yet, so they deny everything until E1-T9 adds policies and grants). Seed the reserved PUBLIC row: id = `PUBLIC_TENANT_ID` (from Settings, substituted by the migration), `kind='public'`, `slug='public'`. Every table in the target model carries `tenant_id uuid NOT NULL` (on `tenants` the key `id`).

Out of scope: policies and grants (E1-T9), the other tables (E1-T5 to E1-T7), advisor seeding (E1-T11).

Round 4 (ADR-031, ADR-032, ADR-027): `tenants` gains `cell_id text NOT NULL` (the tenant's home cell; equals the `cells.json` entry, section 5.12), `residency_class text NOT NULL DEFAULT 'none' CHECK (residency_class IN ('none','eu_only','uk_only'))` and `source_epoch bigint NOT NULL DEFAULT 0` (meaningful on the PUBLIC row; part of the answer-cache key, bumped by E11 `purge_source`). The seeded PUBLIC row takes `cell_id` from the `HOME_CELL` Settings key (deep-dive/06 section 6.6). `llm_egress_ack` is added by E11-T14 and `active_embed_model` by E12-T25, not here. `advisors` keeps one row per `(tenant_id, idp_uid)`; the same `idp_uid` in two tenants is allowed (ADR-032: one IdP tenant per firm, no identity merge). The subject-pseudonym table is E1-T23. Tables owned by E11 to E13 are created by those epics' migrations.

## Acceptance criteria
- [ ] Given an empty database, when `alembic upgrade head` runs, then `tests/db/test_schema_identity.py` passes: both tables exist with `relrowsecurity` and `relforcerowsecurity` true in `pg_class`.
- [ ] Given an insert of an advisor with `tier = 5`, or `jurisdictions = '{XX}'`, or an unknown `role`, then each raises a CheckViolation (three test cases).
- [ ] Given two advisors with the same `(tenant_id, idp_uid)`, then the second insert raises a UniqueViolation; the same `idp_uid` in two different tenants succeeds.
- [ ] Given the migration ran with `PUBLIC_TENANT_ID=<uuid>`, then `SELECT kind FROM tenants WHERE id = '<uuid>'` returns `public` (test run as `fa_owner`).
- [ ] Given the migration, then `tenants.cell_id` is NOT NULL, `residency_class` rejects `'us_only'` with a CheckViolation and defaults to `'none'`, and `source_epoch` defaults to 0 (`tests/db/test_schema_identity.py::test_round4_tenant_columns`).
- [ ] Given `HOME_CELL=us` when the migration runs, then the PUBLIC row has `cell_id = 'us'`.
