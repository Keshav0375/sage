---
key: "E1-T1"
title: "Repo skeleton + provider/backend/vars config"
epic: "E1"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: []
arch_refs: ["deep-dive/09-infra-terraform.md#9.2", "deep-dive/09-1-identity-plane.md#9.9", "deep-dive/09-infra-terraform.md#9.1", "deep-dive/09-1-identity-plane.md#9.13"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 3, "id": 5694988236, "url": "https://github.com/Keshav0375/sentinel-brain/issues/3"}
branch: "dev/infra-phase-1-foundations"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/1"
updated: "2026-11-08"
---

## Summary
Lay down the root Terraform layout that every module wires into. No resources yet beyond

## Description
Source: infra task 1.1 (`sentinel-brain/implementation/tasks/infra/phase-1-foundations/task-1-repo-skeleton-and-providers.md`).

the provider/backend plumbing.

**Files created:**
- `main.tf` — provider blocks (`azurerm` with `features {}` **and `subscription_id`**,
  `github` with `owner = var.github_owner`), `data "azurerm_client_config" "current"`, and
  `data "azurerm_resource_group" "sentinel"` — a **data source, not a resource** (C1: the RG
  is created by the bootstrap and deleted by `ci_destroy_infra`; Terraform reads it, never
  owns it). Module call stubs commented for phases 2–3.
- `versions.tf` — `required_version >= 1.9` and pinned `required_providers` (C9):
  `azurerm ~> 4.0`, `integrations/github ~> 6.0`. **No `azuread`** — rev-9 removed every
  directory object from phases 1–2.
- `variables.tf` — see the contract below.
- `outputs.tf` — empty scaffold with header comment (populated in task 4.4).
- `backend.tf` — `backend "azurerm"` per §8.1, **including `use_azuread_auth = true` and
  `use_oidc = true`** (C2 — without these CI cannot reach the state blob at all).
- `terraform.tfvars.example` — every non-secret var with placeholder values; real
  `terraform.tfvars` gitignored.

## Acceptance criteria
- [x] `terraform fmt -check -recursive` clean.
- [x] `terraform init -backend=false && terraform validate` passes (offline validate; real
- [x] `terraform.tfvars` and `.env` are gitignored; the Python template's entries survive.
- [x] Provider `github.owner` resolves to `Keshav0375`.
- [x] `azurerm_resource_group` appears **only** as a `data` block.
- [x] `backend.tf` carries `use_azuread_auth` + `use_oidc`.
- [x] Providers pinned; **no `azuread` provider declared**.
- [x] No `db_password`, no `postgres_entra_admin_group_object_id`; `location` has no default.

## Outcome
Six files on `dev/infra-phase-1-foundations`: `versions.tf`, `main.tf`, `backend.tf`,
`variables.tf`, `outputs.tf`, `terraform.tfvars.example`, plus a Terraform section appended
to the existing Python `.gitignore` (template preserved — `.env` was already at line 151).
**Gate:** `RESULT: PASS` — `tf-fmt` ✅ · `tf-init -backend=false` ✅ · `tf-validate` ✅ ·
`gitleaks` ✅. Skipped: `tfsec` + `yamllint` (not installed), `actionlint` (no
`.github/workflows/` until task 4.3 — this is the C13/B15 fix working as intended).
**⚠️ `tflint` reports 5 `terraform_unused_declarations` warnings** — `location`,
`postgres_entra_admin_object_id`, `postgres_entra_admin_principal_name`,
`data.azurerm_client_config.current`, `data.azurerm_resource_group.sentinel`. All five are
correct-but-premature: each is consumed by a module that lands in phase 2. tflint is an
