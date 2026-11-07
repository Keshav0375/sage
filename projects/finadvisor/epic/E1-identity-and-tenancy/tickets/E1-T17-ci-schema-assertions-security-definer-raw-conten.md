---
key: "E1-T17"
title: "CI schema assertions: SECURITY DEFINER, raw_content, tenant_id"
epic: "E1"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T8", "E1-T9", "E1-T10"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/05-data-model-and-storage.md#5.4", "decision-logs.md#adr-002", "decision-logs.md#adr-010"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 33, "id": 6155609705, "url": "https://github.com/Keshav0375/FinAdvisor/issues/33"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
A pytest suite run in CI fails on any extra SECURITY DEFINER function, any raw_content column, or any table missing tenant_id and FORCE RLS.

## Description
Add `tests/db/test_schema_invariants.py`, run by the existing CI Postgres job (E0) after `alembic upgrade head`. Invariants from the arch: "`fa_tenant_lookup` ... is the only `SECURITY DEFINER` function allowed in the database (D13m, D13n); CI fails on any other"; "No `raw_content` column (G-03)"; "Every table carries `tenant_id uuid NOT NULL`"; "All tenant tables: `ENABLE` and `FORCE ROW LEVEL SECURITY`"; "All composite foreign keys start with `tenant_id`".

Checks over `pg_catalog` for the app schemas (excluding `gold` views and `alembic_version`): (1) the set of functions with `prosecdef` equals `{fa_tenant_lookup}`; (2) no column named `raw_content` in any table; (3) every table has a `tenant_id` column (or `id` for `tenants`) of type uuid NOT NULL; (4) `relrowsecurity` and `relforcerowsecurity` true for every table including partitioned parents; (5) every foreign key's first column is `tenant_id`, except the FK from `advisors.tenant_id` and similar single-column FKs to `tenants(id)`; (6) no runtime role holds privileges on any partition of `chunks` or `messages`. The suite must also run against a deliberately broken fixture (a temp table without FORCE, a second SECURITY DEFINER function) in a negative test proving it fails.

Out of scope: the runtime startup check (E1-T18).

## Acceptance criteria
- [ ] Given the migrated schema, when the suite runs, then all six invariants pass.
- [ ] Given a temporary `SECURITY DEFINER` function `evil()` created in the test database, then invariant (1) fails (negative test asserts the failure).
- [ ] Given a temporary table with `tenant_id` but without FORCE RLS, then invariant (4) fails; given a temporary column `raw_content` on `documents`, then invariant (2) fails (negative tests).
- [ ] Given the CI workflow, then this suite runs in the same job as the other DB tests and a failure fails the PR (workflow file contains the job step; a CI run with the negative fixture enabled via env var turns red).
