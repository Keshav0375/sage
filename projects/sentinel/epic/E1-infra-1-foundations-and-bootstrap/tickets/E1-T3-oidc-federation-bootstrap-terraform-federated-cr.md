---
key: "E1-T3"
title: "OIDC federation (bootstrap + Terraform federated creds)"
epic: "E1"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E1-T1", "E1-T2"]
arch_refs: ["deep-dive/09-1-identity-plane.md#9.9", "deep-dive/09-1-identity-plane.md#9.13"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 5, "id": 5694988580, "url": "https://github.com/Keshav0375/sentinel-brain/issues/5"}
branch: "dev/infra-phase-1-foundations"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/1"
updated: "2026-11-08"
---

## Summary
Passwordless GitHub→Azure auth. **One UAMI** with federated credentials for all three repos,

## Description
Source: infra task 1.3 (`sentinel-brain/implementation/tasks/infra/phase-1-foundations/task-3-oidc-federation.md`).

no stored client secret. Bootstrap the identity + the two `Sentinel-infra` credentials by
hand, import all five objects into Terraform, then TF manages the rest.

**Files created:**
- `oidc.tf` — `azurerm_user_assigned_identity "sentinel_gha"`; `azurerm_role_assignment`
  **Contributor** on the RG (via `data.azurerm_resource_group.sentinel`, C1);
  `azurerm_role_assignment` **Storage Blob Data Contributor** on `sentineltfstate0375` (C2 —
  the state account is outside the Contributor scope, and without this every CI
  `terraform init` fails); and one `azurerm_federated_identity_credential` per repo+trigger
  (§4.2): `Sentinel-infra` main+pr, `Sentinel` main+pr, `Sentinel-deployment` main.
- `scripts/bootstrap-oidc.sh` — one-time `az identity create` + both role assignments +
  the two `Sentinel-infra` federated credentials (§4.3), then prints all five
  `terraform import` commands. Must:
  - set **`MSYS_NO_PATHCONV=1`** so `--scope /subscriptions/...` survives Git Bash;
  - on **`az role assignment create`**, use `--assignee-object-id` +
    `--assignee-principal-type ServicePrincipal`, never bare `--assignee` — the latter
    does a Microsoft Graph lookup that fails without directory write rights. (Scoped to

## Acceptance criteria
- [x] `oidc.tf` validates; subjects use `Keshav0375` + correct repo names/refs.
- [x] **No `azuread_*` resource anywhere.**
- [x] Bootstrap script is idempotent and creates identity + both role assignments + the two
- [x] All five imports succeed, and `terraform plan` afterwards shows **no destroy and no
- [x] After apply, `terraform plan` reports **"No changes."**

## Outcome
`oidc.tf` + `scripts/bootstrap-oidc.sh`, **executed end to end against the live
subscription**. rev-9 is no longer a hypothesis — a managed identity does substitute for an
app registration.
**Live state:** UAMI `sentinel-gha` (`clientId <redacted-id>`,
`canadacentral`) · Contributor on `sentinel-rg` · Storage Blob Data Contributor on
`sentineltfstate0375` · **all 5 federated credentials**, subjects verified with exact casing.
**Acceptance met:** 5 objects imported → `Plan: 3 to add, 2 to change, 0 to destroy` (no
destroy, no replace) → apply → **`No changes. Your infrastructure matches the
configuration.`** Gate `RESULT: PASS`.
### Four things reality taught us — all now encoded
