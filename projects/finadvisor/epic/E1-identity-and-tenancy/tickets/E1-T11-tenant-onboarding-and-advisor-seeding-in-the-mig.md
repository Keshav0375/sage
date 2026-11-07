---
key: "E1-T11"
title: "Tenant onboarding and advisor seeding in the migrate job"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T5", "E1-T9", "E1-T23"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.5", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.10", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.12", "decision-logs.md#adr-003", "decision-logs.md#adr-027", "decision-logs.md#adr-031"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 27, "id": 6155601752, "url": "https://github.com/Keshav0375/FinAdvisor/issues/27"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
`migrate --onboard-tenant` creates a tenant's chunks LIST partition with indexes, its tenants row and the IdP mapping, idempotently and without partition grants.

## Description
Implement the onboarding step in the `migrate` entrypoint (E0 created the entrypoint; Cloud Run job, role `fa_owner`): deep-dive/04-components-and-responsibilities.md §4.8 "`migrate` ... tenant onboarding (`--onboard-tenant <slug>`: LIST partition + indexes, `tenants` row, IdP mapping; the IdP tenant itself is provisioned by an onboarding script in E1 ...)". ADR-003: "Tenant onboarding creates its partition and indexes in the `migrate` job."

CLI: `migrate --onboard-tenant <slug> --display-name <name> --idp-tenant-id <id> [--tenant-id <uuid>] [--kind firm|public]`. In one transaction as `fa_owner`: insert the `tenants` row (`status='active'`, new uuid unless `--tenant-id`), call `create_chunks_partition` (E1-T5; partition plus the parent-declared indexes), commit. Rerunning with the same slug is a no-op that exits 0. If rows for that tenant already sit in the DEFAULT partition, exit non-zero with a clear message (do not move rows). The dedicated `eval` tenant is onboarded with `--tenant-id $EVAL_TENANT_ID`. The PUBLIC tenant already exists (E1-T4, E1-T5). Partitions get no grants. Print the new `tenants.id`.

Seed command (R18): `migrate --seed-advisors <file>` reads a JSON file of advisors (`tenant_slug, idp_uid, display_name, role, tier, jurisdictions, licenses`), resolves the tenant by slug, and inserts the `advisors` rows as `fa_owner` (upsert on `(tenant_id, idp_uid)`, idempotent). It is the only way the first advisors are created (demo setup uses it); there is no auto-provision on first login. Unknown tenant slug, invalid tier/role/jurisdiction, or malformed file exits non-zero and inserts nothing.

Out of scope: creating the IdP tenant (E1-T21), Terraform (E10), a tenant-creation HTTP endpoint ("Tenant onboarding (partition creation) is a job, not an endpoint").

Round 4 (ADR-027, ADR-031, ADR-029; deep-dive/04 section 4.8: onboarding creates the LIST partition, indexes, the per-leaf `EXCLUDE` constraint on `chunks`, the `tenants` row including `cell_id`, and the IdP mapping): (1) onboarding takes `--cell-id <cell>` (default: `HOME_CELL` from Settings) and optional `--residency-class none|eu_only|uk_only` and writes them to the `tenants` row. (2) The partition is created through `create_chunks_partition` (E1-T5), so it carries the `EXCLUDE` constraint; after creating it, `migrate` asserts that the new leaf has the constraint and the same indexes as `chunks_public` (like the other partition assertions of section 5.3) and exits non-zero otherwise. (3) `migrate --seed-advisors` also inserts one `pseudonym_map` row per seeded advisor (random `pseudonym_id`, E1-T23), idempotently with the advisor upsert.

## Acceptance criteria
- [ ] Given an empty database after migrations, when `migrate --onboard-tenant acme --display-name Acme --idp-tenant-id idp-acme` runs, then `tests/db/test_onboarding.py` passes: one `tenants` row with slug `acme` exists, `chunks` has a partition bound to its id, and `fa_tenant_lookup(p_idp_tenant_id => 'idp-acme')` returns that id.
- [ ] Given the same command is run a second time, then it exits 0 and `SELECT count(*) FROM tenants WHERE slug = 'acme'` is 1 and `chunks` still has exactly one partition for it.
- [ ] Given a chunk inserted for the onboarded tenant by `fa_owner`, then `tableoid::regclass` is the tenant's partition and `chunks_default` is empty (test).
- [ ] Given the new partition, then none of `fa_app, fa_worker, fa_etl, fa_etl_public, fa_dbt, fa_eval` has any privilege on it (`has_table_privilege`), and the same indexes as `chunks_public` exist on it (compared by definition).
- [ ] Given rows of the tenant already in `chunks_default`, when onboarding that tenant runs, then the command exits non-zero and creates no partition.
- [ ] Given a seed file with one valid advisor and one with an unknown `tenant_slug`, when `migrate --seed-advisors` runs, then it exits non-zero and the `advisors` table has no new rows; given only valid entries it inserts them, and a second run leaves the row count unchanged (`tests/db/test_seed_advisors.py`).
- [ ] Given the onboarded partition, then `pg_constraint` shows an exclusion constraint on it and the migrate step's own assertion passes; given a partition created without the constraint (test fixture), then the assertion makes `migrate` exit non-zero (`tests/db/test_onboarding.py::test_leaf_exclude_asserted`).
- [ ] Given `--cell-id eu --residency-class eu_only`, then the `tenants` row has those values; given `--residency-class us_only`, the command exits non-zero and inserts nothing.
- [ ] Given a seed file with two advisors, when `migrate --seed-advisors` runs twice, then `pseudonym_map` has exactly two rows with distinct `pseudonym_id` values and the second run changes none (`tests/db/test_seed_advisors.py::test_pseudonym_rows_seeded_once`).
