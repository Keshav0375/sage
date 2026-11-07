---
key: "E10-T4"
title: "Terraform v2 root: state, profiles, registry, service SAs"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T7", "E2-T4", "E2-T5", "E2-T8", "E2-T18", "E2-T19"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.12", "deep-dive/08-security-and-privacy.md#8.3", "ADR-019", "ADR-021"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Create the Terraform v2 root module with per-env state, demo/prod profile variables, Artifact Registry and one least-privilege service account per service and job.

## Description
Implements deep-dive/04-components-and-responsibilities.md §4.12 ('Terraform ... owns every resource in this view ... with state per env prefix') and 8.3 ('Service identity: one service account per service ... least privilege; no project-wide secretAccessor (G-50)'). E0-T7 has already removed the MVP LiteLLM/Kong resources; E2 owns terraform/edge/ (VPC, Private Google Access, private run.app zone, fa-gateway, ALB, Cloud Armor, log sink). Reuse those modules; do not recreate them.

Build under terraform/: backend config with a GCS state bucket and prefix per env (demo, prod); variables.tf with `env_profile` in {demo, prod} that selects the Cloud SQL HA flag and min instances (consumed by later tickets); Artifact Registry repo (images referenced by digest only; a variable `image_digest` with no default and a validation that rejects values not matching ^sha256:[a-f0-9]{64}$ so tags and `latest` are refused); service accounts: gateway (E2 may already create it, reuse), chat-api, worker, and one per job (migrate, maintenance, etl, etl-public, dbt, eval, redteam, demo-prewarm, demo-ttl); required API enablement. IAM bindings are per resource (for example secretAccessor on individual secrets in E10-T7/T9), never project-level secretAccessor.

Out of scope: the resources that use the SAs (later tickets).

## Acceptance criteria
- [ ] `terraform init` with the demo and prod backend prefixes and `terraform validate` pass in CI (named job terraform-validate)
- [ ] `terraform plan -var image_digest=latest` fails with the validation error; with a valid sha256 digest it passes
- [ ] A script check (`scripts/check_iam.sh` or a terraform test) fails if any google_project_iam_* resource or member grants roles/secretmanager.secretAccessor at project level; it passes on the tree
- [ ] `terraform plan` lists one service account for each of chat-api, worker and the 9 jobs and no `google_project_iam_member` for secretAccessor
