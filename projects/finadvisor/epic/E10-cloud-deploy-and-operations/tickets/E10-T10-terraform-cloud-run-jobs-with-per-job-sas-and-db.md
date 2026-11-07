---
key: "E10-T10"
title: "Terraform Cloud Run jobs with per-job SAs and DB roles"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T4", "E10-T7", "E10-T6"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/06-interfaces-and-contracts.md#6.6", "ADR-019", "ADR-020"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Define the nine Cloud Run jobs on the single image with per-job SA, DB role and VPC egress.

## Description
Implements 4.8 job table and ADR-019. One image, `jobs` entrypoint. Jobs and DB roles: migrate=fa_owner, maintenance=fa_maint, etl=fa_etl (plus fa_dagster for Dagster storage via DAGSTER_PG_*), etl-public=fa_etl_public, dbt=fa_dbt, eval=fa_eval, redteam=fa_eval, demo-prewarm=none (no DB), demo-ttl=fa_maint. Each job: its own SA (E10-T4), Direct VPC egress private-ranges-only, startup probe where applicable, only the secrets it needs (DB password of its role; Kafka keys for etl, etl-public, eval, per config 6.6 one key per service fa-worker, etl, etl-public, eval). EVAL_TENANT_ID and PUBLIC_TENANT_ID passed to migrate and eval jobs. demo-ttl SA needs Cloud Run admin rights (4.8) limited to this project's services, worker pool and Cloud SQL instance patch, and Cloud Scheduler pause/resume, and Memorystore delete for the demo instance; nothing else. The job code (maintenance E1-T12; others in their epics) is not written here, only the job definitions with args placeholders from those epics.

Build terraform/jobs.tf with a for_each over a local map of job name -> {sa, db_role, args, secrets}. Jobs reference the image digest. Set DEMO_TTL_HOURS (decide value 4 as default variable, see questions) and OUTBOX_DRAIN_TIMEOUT_MIN=10 as env on demo-ttl.

Out of scope: Scheduler triggers (E10-T12).

## Acceptance criteria
- [ ] `terraform plan` lists exactly 9 google_cloud_run_v2_job resources named migrate, maintenance, etl, etl-public, dbt, eval, redteam, demo-prewarm, demo-ttl (terraform test counts and names)
- [ ] A test script parses the plan JSON and asserts each job's DB_USER matches the table in 4.8 (for example etl-public -> fa_etl_public) and that demo-prewarm has no DB_* variables
- [ ] `gcloud run jobs execute migrate --wait` (after the E1 migration exists) exits 0 under the fa_owner role against the real instance; output attached
- [ ] demo-ttl SA role list is printed by `gcloud projects get-iam-policy --filter` and contains no roles/owner or roles/editor (test script)
