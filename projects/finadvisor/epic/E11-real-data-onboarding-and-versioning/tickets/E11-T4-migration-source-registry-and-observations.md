---
key: "E11-T4"
title: "Migration: source_registry and source_observations"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T5", "E1-T8", "E1-T3"]
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.9", "deep-dive/06-interfaces-and-contracts.md#6.8", "decision-logs.md#adr-26"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Create the source registry and the append-only observations table with RLS and grants.

## Description
Alembic migration for two tables, owned by E11 (planning note: E11 to E13 tables are created by their owning epic).

Arch (deep-dive/05-1 section 5.9): `source_registry` key `(tenant_id, source_id)`; `connector` (`ecfr`, `sec`, `eurlex`, `legislation_gov_uk`, `fca_api`, `publisher`), `source_class` (`law`, `qa`, `fca_api`, `publisher`), `on_withdraw` (`retire`, `erase`), `cursor jsonb`, `overlap_s` default 172800, `last_listing_at`, `frozen boolean`, `frozen_reason`, `rate_limit_rps`, `enabled`. `source_observations` key `(tenant_id, id)`: append-only; `source_id` composite FK, `external_id`, `version_key`, `content_sha256`, `source_ts`, `observed_at` (DB clock, `clock_timestamp()`), `state` in (`present`, `revoked`, `withdrawn`, `pending`), `listing_run_id`; unique on `(source_id, external_id, version_key, content_sha256)`; index `(tenant_id, source_id, external_id, observed_at DESC)`; "No UPDATE or DELETE grant except the erasure of an erased source".

Add ENABLE + FORCE RLS with tenant-match policies in the pattern of E1-T8 (PUBLIC rows readable by every tenant per the "own-or-PUBLIC SELECT" rule only where the arch says so; `source_registry` for a firm source is that tenant's). Writers are the ETL roles only; `fa_app` gets no write.

Out of scope: `document_versions` (E11-T5), connector code.

## Acceptance criteria
- [ ] Given the migration applied then `source_registry` and `source_observations` exist with the columns, check constraints on the enumerated values and the unique index of 5.9 (test `backend/tests/test_source_tables_schema.py::test_columns_and_unique_index`).
- [ ] Given `fa_etl` role when it tries UPDATE or DELETE on `source_observations` then it is denied; INSERT is allowed (test `test_observations_append_only_grants`, `integration`).
- [ ] Given a row of tenant A when tenant B's role selects `source_registry` then zero rows are returned; `relforcerowsecurity` is true for both tables (test `test_source_tables_rls_leak`, part of the L0 leak matrix).
- [ ] Given `alembic upgrade head` then `downgrade -1` then `upgrade head` the schema is identical (migration round-trip test).
