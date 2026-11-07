---
key: "E10-T7"
title: "Create DB roles, passwords and the dagster database in Cloud SQL"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T6", "E1-T3"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/08-security-and-privacy.md#8.4", "deep-dive/06-interfaces-and-contracts.md#6.6 DAGSTER_PG_*, DB_*", "ADR-020"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 255, "id": 6263682167, "url": "https://github.com/Keshav0375/FinAdvisor/issues/255"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Create every runtime login role with a Secret Manager password and the dagster database in Cloud SQL without secret values in Terraform state.

## Description
Boundary: E1-T3 bootstraps roles and the dagster database for local/CI only; E10 owns creating the roles, passwords and the dagster database in Cloud SQL. Overview 8.4: Secret Manager holds 'DB password per role'; 'Terraform never stores secret values in state in plaintext (G-27)'. 4.8 job table gives the roles: fa_owner, fa_app, fa_worker, fa_maint, fa_etl, fa_etl_public, fa_dbt, fa_eval, and fa_dagster (owns database `dagster`, no access to app schemas; config keys DAGSTER_PG_DB=dagster, DAGSTER_PG_USER=fa_dagster).

Build: (1) Terraform creates empty google_secret_manager_secret resources (no versions) `db-password-<role>` for each role, with secretAccessor granted per secret only to the SA that uses that role. (2) scripts/db_bootstrap.py (run as a Cloud Run job `db-bootstrap` in the VPC, using the Cloud SQL built-in admin user whose password is created/rotated by the script and stored in Secret Manager version, never in Terraform) generates a random password per role, writes a new secret version, then runs the E1-T3 role SQL (reuse the same SQL file, do not fork it) with those passwords and creates database dagster owned by fa_dagster. Idempotent: re-running does not rotate existing passwords unless --rotate is given.

Out of scope: grants on app tables (migrate job, E1), Kafka keys (E5-T13).

## Acceptance criteria
- [ ] `grep -r 'password' terraform.tfstate`-style check: after apply, `terraform show -json | jq` finds no google_secret_manager_secret_version and no random_password resource (test script fails if any is found)
- [ ] Integration test against a Postgres container: running db_bootstrap twice leaves password secret versions unchanged on the second run (mock Secret Manager client records one version per role) and creates all 9 roles plus database dagster owned by fa_dagster
- [ ] Against the real instance, `psql` as fa_dagster to database dagster succeeds and `\dn` on the app database as fa_dagster is denied (connect refused or no schema usage); output attached
- [ ] Each of the 9 secrets is readable only by its owning SA: `gcloud secrets get-iam-policy` for each shows exactly one secretAccessor member (test script)
