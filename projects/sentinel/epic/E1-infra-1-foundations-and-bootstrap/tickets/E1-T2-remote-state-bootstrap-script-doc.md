---
key: "E1-T2"
title: "Remote state bootstrap (script + doc)"
epic: "E1"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E1-T1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 4, "id": 5694988411, "url": "https://github.com/Keshav0375/sentinel-brain/issues/4"}
branch: "dev/infra-phase-1-foundations"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/1"
updated: "2026-11-08"
---

## Summary
Terraform's `azurerm` backend needs a state RG + storage account + container that exist

## Description
Source: infra task 1.2 (`sentinel-brain/implementation/tasks/infra/phase-1-foundations/task-2-remote-state-bootstrap.md`).

*before* the first `init`. This is a one-time manual bootstrap — scripted + documented,
not applied by Terraform (chicken-and-egg).

**Files created:**
- `scripts/bootstrap-state.sh` — idempotent, guards on existence, `MSYS_NO_PATHCONV=1`:
  - `az group create --name sentinel-state-rg --location canadacentral`
  - `az storage account create --name sentineltfstate0375 -g sentinel-state-rg --sku Standard_LRS --encryption-services blob`
  - `az storage container create --name tfstate --account-name sentineltfstate0375 --auth-mode login`
  - **grant the operator `Storage Blob Data Contributor` on the account** — see the
    control-plane/data-plane note below.
- `docs/BOOTSTRAP.md` (or README section) — the ordered one-time setup (§10 steps 1–2),
  the blob-lease locking note (§8.2), and how `backend.tf` maps to these names.

**Contract:** names must match `backend.tf` from task 1: `sentinel-state-rg`,
`sentineltfstate0375`, `tfstate`, key `sentinel.terraform.tfstate`, region `canadacentral`.

> **⚠ Control plane ≠ data plane.** `backend.tf` sets `use_azuread_auth = true` (C2), so
> `terraform init` reaches the state blob with an **Entra token**, not a storage access key.
> Being **Owner** on the subscription does *not* grant blob data access — Owner is a

## Acceptance criteria
- [x] `bootstrap-state.sh` runs clean and is re-runnable (idempotent).
- [x] `terraform init` (real, with backend) succeeds against the created container.
- [x] The operator holds `Storage Blob Data Contributor` on the account.
- [x] BOOTSTRAP.md lists exact commands in order, region `canadacentral`.

## Outcome
`scripts/bootstrap-state.sh` + `docs/BOOTSTRAP.md`, both **executed against the live
subscription** — this task is verified for real, not just written.
**Created:** `sentinel-state-rg` · `sentineltfstate0375` (Standard_LRS, blob encryption,
TLS 1.2 min) · `tfstate` container · `Storage Blob Data Contributor` → `<redacted-id>` (User).
**Proof:**
- First run created everything cleanly.
- **Second run skipped all four steps** — idempotency is real, not asserted.
- **`terraform init` → "Successfully configured the backend \"azurerm\"!"** This one line is
  the actual acceptance test: it proves the storage account, container, `use_azuread_auth`
  path and the data-plane role assignment all work together. It is the first live
