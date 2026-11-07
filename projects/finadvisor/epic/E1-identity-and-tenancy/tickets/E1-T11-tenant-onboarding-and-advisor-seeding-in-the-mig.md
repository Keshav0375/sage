---
key: "E1-T11"
title: "Tenant onboarding and advisor seeding in the migrate job"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T5", "E1-T9"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.5", "decision-logs.md#adr-003"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 27, "id": 6155601752, "url": "https://github.com/Keshav0375/FinAdvisor/issues/27"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
`migrate --onboard-tenant` creates a tenant's chunks LIST partition with indexes, its tenants row and the IdP mapping, idempotently and without partition grants.

## Description
Implement the onboarding step in the `migrate` entrypoint (E0 created the entrypoint; Cloud Run job, role `fa_owner`): deep-dive/04-components-and-responsibilities.md §4.8 "`migrate` ... tenant onboarding (`--onboard-tenant <slug>`: LIST partition + indexes, `tenants` row, IdP mapping; the IdP tenant itself is provisioned by an onboarding script in E1 ...)". ADR-003: "Tenant onboarding creates its partition and indexes in the `migrate` job."

CLI: `migrate --onboard-tenant <slug> --display-name <name> --idp-tenant-id <id> [--tenant-id <uuid>] [--kind firm|public]`. In one transaction as `fa_owner`: insert the `tenants` row (`status='active'`, new uuid unless `--tenant-id`), call `create_chunks_partition` (E1-T5; partition plus the parent-declared indexes), commit. Rerunning with the same slug is a no-op that exits 0. If rows for that tenant already sit in the DEFAULT partition, exit non-zero with a clear message (do not move rows). The dedicated `eval` tenant is onboarded with `--tenant-id $EVAL_TENANT_ID`. The PUBLIC tenant already exists (E1-T4, E1-T5). Partitions get no grants. Print the new `tenants.id`.

Seed command (R18): `migrate --seed-advisors <file>` reads a JSON file of advisors (`tenant_slug, idp_uid, display_name, role, tier, jurisdictions, licenses`), resolves the tenant by slug, and inserts the `advisors` rows as `fa_owner` (upsert on `(tenant_id, idp_uid)`, idempotent). It is the only way the first advisors are created (demo setup uses it); there is no auto-provision on first login. Unknown tenant slug, invalid tier/role/jurisdiction, or malformed file exits non-zero and inserts nothing.

Out of scope: creating the IdP tenant (E1-T21), Terraform (E10), a tenant-creation HTTP endpoint ("Tenant onboarding (partition creation) is a job, not an endpoint").

## Acceptance criteria
- [ ] Given an empty database after migrations, when `migrate --onboard-tenant acme --display-name Acme --idp-tenant-id idp-acme` runs, then `tests/db/test_onboarding.py` passes: one `tenants` row with slug `acme` exists, `chunks` has a partition bound to its id, and `fa_tenant_lookup(p_idp_tenant_id => 'idp-acme')` returns that id.
- [ ] Given the same command is run a second time, then it exits 0 and `SELECT count(*) FROM tenants WHERE slug = 'acme'` is 1 and `chunks` still has exactly one partition for it.
- [ ] Given a chunk inserted for the onboarded tenant by `fa_owner`, then `tableoid::regclass` is the tenant's partition and `chunks_default` is empty (test).
- [ ] Given the new partition, then none of `fa_app, fa_worker, fa_etl, fa_etl_public, fa_dbt, fa_eval` has any privilege on it (`has_table_privilege`), and the same indexes as `chunks_public` exist on it (compared by definition).
- [ ] Given rows of the tenant already in `chunks_default`, when onboarding that tenant runs, then the command exits non-zero and creates no partition.
- [ ] Given a seed file with one valid advisor and one with an unknown `tenant_slug`, when `migrate --seed-advisors` runs, then it exits non-zero and the `advisors` table has no new rows; given only valid entries it inserts them, and a second run leaves the row count unchanged (`tests/db/test_seed_advisors.py`).
