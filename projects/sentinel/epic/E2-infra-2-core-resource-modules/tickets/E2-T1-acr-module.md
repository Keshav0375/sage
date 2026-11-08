---
key: "E2-T1"
title: "ACR module"
epic: "E2"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E1-T1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.2"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 7, "id": 5694988909, "url": "https://github.com/Keshav0375/sentinel-brain/issues/7"}
branch: "dev/infra-phase-2-core-modules"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/2"
updated: "2026-11-08"
---

## Summary
Standard-tier Container Registry that stores `sentinel-backend` + `ci-runner` images.

## Description
Source: infra task 2.1 (`sentinel-brain/implementation/tasks/infra/phase-2-core-modules/task-1-acr-module.md`).

**Files created:** `modules/acr/{main.tf,variables.tf,outputs.tf}`
- `main.tf` — `azurerm_container_registry "sentinel"` name `sentinelacr0375`, sku `Standard`, `admin_enabled = true`.
- `variables.tf` — `resource_group_name`, `location`.
- `outputs.tf` — `acr_login_server`, `acr_admin_username`, `acr_admin_password` (sensitive).

**Contract:** name `sentinelacr0375` (globally unique — adjust if taken, propagate to R-notes).

## Acceptance criteria
- [x] Module validates + fmt clean; outputs expose login server + admin creds (sensitive).
- [x] Root `main.tf` calls the module (wired fully in task 4.4).

## Outcome
`modules/acr/{main,variables,outputs}.tf`. Applied live: `sentinelacr0375.azurecr.io` ·
**Standard** · admin enabled · canadacentral. Plan `No changes`.
SKU went Basic→Standard mid-task: the Azure for Students grant covers "1 **Standard** tier
registry" and Basic is a different, non-covered meter — the cheaper SKU was the expensive
choice. Recorded in decisions.md with the original reasoning struck through.
Added `acr_id` output beyond §3.1's list (task 3.1 needs it for the AcrPull scope).
`registry_name` is a validated variable with root passthrough, so a name collision is a
tfvars change. **Accepted risk annotated in-module:** `admin_enabled` puts the registry
password in plaintext state; mitigation is `az acr credential renew`.
