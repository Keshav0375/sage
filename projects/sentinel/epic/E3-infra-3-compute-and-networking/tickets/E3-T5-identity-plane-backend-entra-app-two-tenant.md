---
key: "E3-T5"
title: "Identity plane: backend Entra app (two-tenant)"
epic: "E3"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E1-T3"]
arch_refs: ["deep-dive/09-1-identity-plane.md#9.12", "deep-dive/09-1-identity-plane.md#9.10", "deep-dive/09-1-identity-plane.md#9.13"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 15, "id": 5694990207, "url": "https://github.com/Keshav0375/sentinel-brain/issues/15"}
branch: "dev/infra-phase-3-compute-modules"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/3"
updated: "2026-11-08"
---

## Summary
Give the backend a real API identity so callers present **audience-scoped Entra tokens**

## Description
Source: infra task 3.5 (`sentinel-brain/implementation/tasks/infra/phase-3-compute-modules/task-5-backend-entra-app.md`).

instead of a shared secret — the change that deleted `sentinel-api-token` in rev-5.

**Files created:** `identity.tf` (new — keep it separate from `oidc.tf`, which is
school-tenant only; the file boundary makes the tenant boundary obvious in review).

**Resources — all with `provider = azuread.identity`:**

| Resource | Name | Purpose |
|---|---|---|
| `azuread_application` | `sentinel-backend-api` | `identifier_uris = ["api://sentinel-backend"]`, `app_role` **Incident.Write** (stable GUID `<redacted-id>`) |
| `azuread_service_principal` | ↑ | the resource half of the role assignment |
| `azuread_application` | `sentinel-gha-client` | the caller |
| `azuread_service_principal` | ↑ | the principal half |
| `azuread_application_federated_identity_credential` | `sentinel-main` | `repo:Keshav0375/Sentinel:ref:refs/heads/main` |
| `azuread_app_role_assignment` | `gha_incident_write` | grants the caller the role |

**Also:** aliased provider block, `identity_tenant_id` root variable, `azuread ~> 3.0` added
to `versions.tf` (deliberately absent in phases 1–2), `AZURE_IDENTITY_TENANT_ID` GitHub
variable.

> ### ⛔ The trap — read before writing a line

## Acceptance criteria
- [x] Every resource in `identity.tf` carries `provider = azuread.identity`. No directory
- [x] `az account get-access-token --resource api://sentinel-backend` (as `sentinel-gha-client`
- [x] The `aud` claim is `api://sentinel-backend` and `iss` is the **identity** tenant.
- [x] `terraform plan` is clean after the bootstrap import.
- [x] No client secret exists on either app registration.

## Outcome
_not yet implemented_
