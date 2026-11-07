---
key: "E12-T6"
title: "Migration: source_purges and reconciliation tables"
epic: "E12"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T3", "E1-T8"]
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.11", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.12", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.13", "decision-logs.md#adr-26", "decision-logs.md#adr-34"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Create the PUBLIC source_purges table and the reconciliation manifest and findings tables with their grants.

## Description
Implement deep-dive/05-1 5.11 `source_purges (tenant_id = PUBLIC, purge_id)` with `source_id`, `reason`, `requested_at`; INSERT granted to `fa_etl_public` on the PUBLIC tenant only, SELECT to every runtime role under own-or-PUBLIC, no UPDATE or DELETE for anyone. Implement 5.12 `reconciliation_manifests (tenant_id, version_id, hop, parser_version)` with `hop` in (bronze, silver, chunks, bigquery), `n_chunks`, `chunk_set_hash`, `computed_at`, and `reconciliation_findings (tenant_id, id, pair, detail, status, opened_at)`. Both reconciliation tables: ENABLE and FORCE RLS, pipeline roles own tenant, `fa_etl_public` for PUBLIC, no `fa_app` grant (5.13). Out of scope: the reconcile job and the purge command.

## Acceptance criteria
- [ ] Given the migration, when role `fa_etl_public` inserts a `source_purges` row for tenant PUBLIC, then it succeeds; for a firm tenant id it fails.
- [ ] Given tenant A under `fa_worker`, when it SELECTs `source_purges`, then it sees PUBLIC rows only, and an UPDATE or DELETE fails for every role (grants test).
- [ ] Given `fa_app`, when it SELECTs `reconciliation_manifests` or `reconciliation_findings`, then permission is denied.
- [ ] Given a manifest key `(tenant, version, hop, parser_version)` inserted twice, then the second violates the primary key; the same version with a new `parser_version` is accepted (parser bump re-baseline).
