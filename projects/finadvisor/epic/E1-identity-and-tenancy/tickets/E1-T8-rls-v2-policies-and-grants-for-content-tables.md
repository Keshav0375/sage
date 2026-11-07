---
key: "E1-T8"
title: "RLS v2 policies and grants for content tables"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T3", "E1-T5"]
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.4", "deep-dive/05-data-model-and-storage.md#5.3", "decision-logs.md#adr-002", "decision-logs.md#adr-004"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 24, "id": 6155597838, "url": "https://github.com/Keshav0375/FinAdvisor/issues/24"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
documents, chunks, suitability_rules and ingest_rejects have the own-or-PUBLIC read policies, own-tenant-only write policies, column grants and the fa_etl_public-only PUBLIC write.

## Description
Add an Alembic revision implementing deep-dive/05-1-rls-indexes-versioning-and-deletion.md §5.4 and the 5.3 grants for the content tables. `<PUBLIC>` is the `PUBLIC_TENANT_ID` uuid literal substituted by the migration; `fa_eval` policies use the `EVAL_TENANT_ID` literal. Policies call `current_setting('app.x')` without `missing_ok`, so an unset setting raises (fail closed).

Policies (policy text for `chunks` is the arch text; `documents` and `suitability_rules` are identical in shape, `suitability_rules` uses `min_tier_required`):
- `*_select_app TO fa_app FOR SELECT`: `(tenant_id = current_setting('app.tenant_id')::uuid OR tenant_id = '<PUBLIC>'::uuid) AND tier_required <= current_setting('app.tier')::int AND jurisdiction = ANY (string_to_array(current_setting('app.jurisdictions'), ','))`.
- `*_select_pipe TO fa_worker, fa_etl, fa_etl_public, fa_dbt FOR SELECT`: own tenant only.
- `*_ins_tenant`, `*_upd_tenant`, `*_del_tenant TO fa_worker`: own tenant and `tenant_id <> '<PUBLIC>'` (USING and WITH CHECK on UPDATE). `fa_etl` gets INSERT and UPDATE on `documents` with the same own non-PUBLIC clause, and SELECT on `chunks`.
- `*_all_public TO fa_etl_public FOR ALL`: USING and WITH CHECK `tenant_id = '<PUBLIC>'::uuid`.
- `fa_eval`: the `fa_app` policies with the tenant literal of the `eval` tenant plus PUBLIC reads.
- `ingest_rejects`: tenant match for the roles holding grants, no PUBLIC clause.
`fa_app` has no INSERT, UPDATE or DELETE policy or grant on `chunks`, `documents`, `suitability_rules` ("document ACL changes and deletes are applied by the `acl-applier` worker (ADR-022)").

Grants per 5.3: `fa_app` SELECT only; `fa_worker` on `chunks` SELECT, INSERT, DELETE and UPDATE (`tier_required`, `jurisdiction`) only, on `documents` SELECT, INSERT, DELETE and UPDATE (`tier_required`, `jurisdiction`, `status`, `parser_version`), on `suitability_rules` SELECT, INSERT, DELETE, on `ingest_rejects` SELECT, INSERT; `fa_etl` SELECT, INSERT, UPDATE (`status`, `parser_version`, `bronze_uri`) on `documents` and SELECT on `chunks`; `fa_etl_public` write on the content tables; `fa_dbt` SELECT; `fa_eval` the `fa_app` grants. Never `GRANT ... ON ALL TABLES` (partitions get no grants).

Out of scope: tenants/advisors (E1-T9), other tables (E1-T10), the full leak matrix (E1-T19, E1-T20).

## Acceptance criteria
- [ ] Given a principal for tenant A (tier 2, jurisdictions US), when `fa_app` selects from `chunks` after `set_config(..., true)`, then it sees tenant A and PUBLIC rows only, never tenant B rows, never rows with `tier_required = 3`, never rows with `jurisdiction = 'EU'` (`tests/db/test_rls_content.py`, parametrised over `chunks`, `documents`, `suitability_rules`).
- [ ] Given `fa_app`, when it runs INSERT, UPDATE or DELETE on `chunks`, `documents` or `suitability_rules`, then each fails with permission denied (no grant).
- [ ] Given `fa_worker` bound to tenant A, when it inserts a chunk with `tenant_id` = B, or with `tenant_id` = PUBLIC, then each raises a row-level-security violation; and when it updates `documents.title`, then it fails with permission denied (column grant).
- [ ] Given `fa_etl_public`, when it inserts a chunk into the PUBLIC tenant, then it succeeds; when it inserts into tenant A, then it raises a row-level-security violation.
- [ ] Given `fa_eval` with `app.tenant_id` set to tenant A, when it selects from `documents`, then it sees only `EVAL_TENANT_ID` and PUBLIC rows.
- [ ] Given no `app.tenant_id` set in the transaction, when `fa_app` selects from `chunks`, then it raises `unrecognized configuration parameter` (fail closed) and returns no rows.
