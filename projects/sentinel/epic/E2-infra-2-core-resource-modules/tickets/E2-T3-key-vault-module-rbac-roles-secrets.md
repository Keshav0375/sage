---
key: "E2-T3"
title: "Key Vault module (+ RBAC roles, secrets)"
epic: "E2"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E2-T2", "E1-T3"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.2"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 9, "id": 5694989213, "url": "https://github.com/Keshav0375/sentinel-brain/issues/9"}
branch: "dev/infra-phase-2-core-modules"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/2"
updated: "2026-11-08"
---

## Summary
Central secret store, RBAC-authorized. Terraform writes, GHA SP + backend UAMI read, rotator writes.

## Description
Source: infra task 2.3 (`sentinel-brain/implementation/tasks/infra/phase-2-core-modules/task-3-keyvault-module.md`).

**Files created:** `modules/keyvault/{main.tf,variables.tf,outputs.tf}`
- `azurerm_key_vault "sentinel"` — name `sentinel-kv-0375`, sku `standard`,
  **`rbac_authorization_enabled = true`** (NOT `enable_rbac_authorization` — deprecated in
  azurerm v4, removed in v5; verified against the pinned 4.81.0), tenant from a
  **module-local** `data "azurerm_client_config" "current"` (data sources do not inherit
  across module boundaries), plus `soft_delete_retention_days = 7` and
  `purge_protection_enabled = false` (owner decision 2026-08-15 — Azure's 90-day +
  purge-protection default would leave the vault name reserved after any `ci_destroy_infra`
  teardown, making the rebuild impossible under the same name).
- `azurerm_role_assignment "terraform_kv_admin"` — `Key Vault Secrets Officer` to `data.azurerm_client_config.current.object_id`.
- `azurerm_role_assignment "gha_kv_reader"` — `Key Vault Secrets User` to the GHA SP object id (task 1.3 output).
- `azurerm_role_assignment "backend_kv_reader"` — `Key Vault Secrets User` to the backend UAMI (task 3.1).
- `azurerm_role_assignment "rotator_kv_officer"` — `Key Vault Secrets Officer` to the rotator Function MI (task 3.6).
- Secret placeholders loaded post-apply via `az keyvault secret set` (§10). LLM keys seeded with a ~90d expiry (rotation, task 3.6).
- `variables.tf` — `resource_group_name`, `location`, `gha_principal_id`, `backend_uami_principal_id` (**no** `db_password`).
- `outputs.tf` — `key_vault_id`, `key_vault_name`, `key_vault_uri`.

## Acceptance criteria
- [x] Validates; RBAC (not access policies); **four** role assignments — Secrets Officer for the
- [x] **No `db-password` and no `sentinel-api-token`** anywhere in the module (Entra-only DB auth,
- [x] LLM keys (`anthropic-api-key`, `openai-api-key`) carry a ~90d expiry for task 3.6 rotation.
- [x] Outputs expose vault id/name/uri.

## Outcome
`modules/keyvault/{main,variables,outputs}.tf` + root wiring. Applied live:
`sentinel-kv-0375` · standard · **RBAC** (`rbac_authorization_enabled`, not the deprecated
spelling) · 7-day soft delete · purge protection off. **Zero secret resources in state** —
verified, not asserted. Live write→read→delete→**purge** test through the RBAC path passed;
the purge is the same mechanism the teardown depends on.
**Review changed this task materially:**
- `terraform_kv_admin` → `kv_admin` bound to an explicit `kv_admin_object_id` instead of
  `client_config.current.object_id`, which resolves to the **CI identity** when CI applies —
  the first CI apply would have destroyed the human's Officer rights. Renamed via a `moved`
  block so no window exists with no Officer on the vault.
