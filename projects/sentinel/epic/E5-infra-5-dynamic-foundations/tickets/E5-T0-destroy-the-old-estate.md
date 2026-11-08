---
key: "E5-T0"
title: "Destroy the old estate"
epic: "E5"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: []
arch_refs: ["deep-dive/09-infra-terraform.md#9.3", "deep-dive/09-1-identity-plane.md#9.9"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 23, "id": 5694991455, "url": "https://github.com/Keshav0375/sentinel-brain/issues/23"}
branch: "dev/infra-phase-5-dynamic-foundations"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/7"
updated: "2026-11-08"
---

## Summary
The phase-1-to-4 estate is built on a naming scheme and a resource-group model that phases 5-6

## Description
Source: infra task 5.0 (`sentinel-brain/implementation/tasks/infra/phase-5-dynamic-foundations/task-0-destroy-old-estate.md`).

replace. It is **deleted, not migrated** (owner decision): nothing is deployed into it, so this
is the cheapest this will ever be, and leaving it beside the new model would mean maintaining
two schemes forever.

**Order matters — state goes last, because it describes everything above it.**

Then re-bootstrap state storage under the new scheme (`st<org>tfstate<uid>`), because
`sentineltfstate0375` carries the same ad-hoc `0375` suffix this phase removes.

**Survives deliberately:** `sentinel-tf-identity` in the identity tenant and its three federated
credentials. They are repo-scoped, not deployment-scoped, so they stay valid — and re-creating
them means another interactive cross-tenant login.

**Deleted as a consequence:** `azuread_application.sentinel_backend` and `sentinel_gha_client`
are Terraform-managed, so `destroy` removes them. Phase 6 recreates them per deployment.

## Acceptance criteria
- [x] `az group list --query "[?starts_with(name,'sentinel')]"` → empty
- [x] `az keyvault list-deleted --query "[?name=='sentinel-kv-0375']"` → empty (purged, not just deleted)
- [x] New state account exists, `terraform init` reports "Successfully configured the backend"
- [x] `sentinel-tf-identity` still present with 3 federated credentials

## Outcome
_not yet implemented_
