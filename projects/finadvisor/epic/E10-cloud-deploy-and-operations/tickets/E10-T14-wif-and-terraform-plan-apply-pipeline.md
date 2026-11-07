---
key: "E10-T14"
title: "WIF and Terraform plan/apply pipeline"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T4", "E10-T5", "E0-T14"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.12", "deep-dive/08-security-and-privacy.md#8.3", "ADR-021"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Create Workload Identity Federation for GitHub and the Terraform plan-on-PR and gated apply workflows.

## Description
ADR-021 and 8.3: keyless CI to GCP via Workload Identity Federation, no JSON keys; 4.12: Terraform 'applied from GitHub Actions through WIF (plan on PR)'. E0-T13/E0-T14 already build PR CI (lint, tests, terraform fmt/validate); do not redo them.

Build: terraform/wif.tf (google_iam_workload_identity_pool + GitHub OIDC provider with attribute_condition restricting to the repository and, for the apply/deploy SA, to ref refs/heads/main or an environment), two SAs: `tf-plan` (read-only roles, usable on PRs) and `deployer` (roles needed for apply, Artifact Registry writer, run.admin on services/jobs/pools, scoped as tightly as practical). Workflows: .github/workflows/terraform-plan.yml (on PR touching terraform/, uses google-github-actions/auth with WIF, runs `terraform plan`, posts it) and terraform-apply.yml (workflow_dispatch / main with a GitHub environment requiring approval, runs check-org-policy from E10-T5 first, then apply). Pin action versions by SHA or exact version. The bootstrap of the WIF resources themselves is a one-time local apply documented in docs/runbook-bootstrap.md.

Out of scope: the service deploy workflow (E10-T16).

## Acceptance criteria
- [ ] `.github/workflows/terraform-plan.yml` run on a PR that touches terraform/ authenticates via WIF and prints a plan; gitleaks and a grep for `credentials_json` / `GOOGLE_CREDENTIALS` in .github/ finds none (CI step fails otherwise)
- [ ] A run triggered from a fork or from a non-main ref requesting the deployer SA is rejected by the attribute condition (negative test: `gcloud iam workload-identity-pools` condition test or a documented failed run)
- [ ] The apply workflow does not proceed when `make check-org-policy` exits non-zero (workflow-level test with stubbed script)
- [ ] `terraform plan` on the merged tree has exit code 0 after apply (no drift)
