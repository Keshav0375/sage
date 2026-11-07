---
key: "E1-T3"
title: "Bootstrap DB roles and the separate dagster database"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.3", "decision-logs.md#adr-002"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 19, "id": 6155591054, "url": "https://github.com/Keshav0375/FinAdvisor/issues/19"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
All ten database roles exist with the exact attributes the arch requires, created by an idempotent bootstrap script that compose and CI run.

## Description
Implement deep-dive/05-data-model-and-storage.md §5.3: "One login role per process ... All are NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOBYPASSRLS. Runtime roles own nothing, with two explicit exemptions."

Create `backend/db/bootstrap/roles.sql` (idempotent: `DO` blocks / `\gexec`), run by the compose Postgres init and by the CI Postgres service step (E0 compose and CI files updated). Roles: `fa_owner` (login; used by `migrate` only), `fa_lookup` (NOLOGIN), `fa_app`, `fa_worker`, `fa_etl`, `fa_etl_public`, `fa_dbt`, `fa_maint`, `fa_eval`, `fa_dagster` (login). Passwords come from env vars (`DB_PASSWORD_<ROLE>`), none hard-coded. Database `dagster` is created and owned by `fa_dagster`; `fa_dagster` has no CONNECT on the app database (`REVOKE CONNECT ON DATABASE <app> FROM PUBLIC`, then grant CONNECT to the app roles only). `fa_owner` is the owner of the app database and (via later migrations) of all objects except schema `gold` and table `messages`. Create schema `gold` owned by `fa_dbt`.

Compose services get `DB_USER` set to their process role (`fa_app` for the api, `fa_worker` for the worker); `Settings` keys used: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

Out of scope: Cloud SQL role creation and secrets (E10 Terraform), grants and policies on tables (E1-T8 to E1-T10).

## Acceptance criteria
- [ ] Given the bootstrap has run, when `tests/db/test_roles.py` queries `pg_roles`, then for each of the 10 roles `rolsuper`, `rolcreatedb`, `rolcreaterole` and `rolbypassrls` are all false, and `fa_lookup.rolcanlogin` is false while the other nine can log in.
- [ ] Given the script is run twice on the same database, then the second run exits 0 and `pg_roles` is unchanged (test).
- [ ] Given a connection as `fa_dagster`, when it tries to connect to the app database, then it fails with permission denied; and `pg_database` shows `dagster` owned by `fa_dagster` (test).
- [ ] Given a connection as `fa_app`, when it runs `CREATE TABLE x(a int)` in schema public, then it fails with permission denied (runtime roles own nothing and cannot create objects).
