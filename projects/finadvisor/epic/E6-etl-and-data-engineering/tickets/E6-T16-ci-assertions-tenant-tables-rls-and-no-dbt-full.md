---
key: "E6-T16"
title: "CI assertions: tenant tables RLS and no dbt full rebuild"
epic: "E6"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E6-T15", "E1-T17"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/04-components-and-responsibilities.md#4.8", "decision-logs.md#adr-014"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 149, "id": 6263504909, "url": "https://github.com/Keshav0375/FinAdvisor/issues/149"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add CI checks that every tenant-schema table has RLS and that dbt never full-rebuilds a tenant table.

## Description
Plan E6 done-when: 'dbt gold models pass the CI assertion that every tenant-schema table has RLS enabled, forced, with policies, and no dbt run does a full-table rebuild of a tenant table; only `fa_tenant_lookup` is `SECURITY DEFINER`.' Build a test script (pytest against compose Postgres after migrate + dbt run): (1) every table with a `tenant_id` column in the app schemas has `relrowsecurity` and `relforcerowsecurity` true and >=1 policy; (2) `pg_proc` has exactly one SECURITY DEFINER function, `fa_tenant_lookup` (extend, do not duplicate, E1-T17 if it exists); (3) a static check over dbt models that rejects `materialized='table'` for any model reading a tenant table, and a runtime check that no `DROP TABLE`/`CREATE TABLE AS` for tenant tables appears in the dbt run's executed SQL log. Gate in CI.

## Acceptance criteria
- [ ] Given a new table with tenant_id and no RLS, when the assertion runs, then it fails naming the table (negative test)
- [ ] Given a dbt model with `materialized='table'` over `chunks`, when the check runs, then it fails (negative test)
- [ ] Given the clean repo, when run, then the only SECURITY DEFINER function is `fa_tenant_lookup`
- [ ] The checks are wired into the CI workflow and block merge
