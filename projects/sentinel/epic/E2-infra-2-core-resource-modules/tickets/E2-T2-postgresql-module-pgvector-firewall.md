---
key: "E2-T2"
title: "PostgreSQL module (+ pgvector, firewall)"
epic: "E2"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E1-T1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.2"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 8, "id": 5694989061, "url": "https://github.com/Keshav0375/sentinel-brain/issues/8"}
branch: "dev/infra-phase-2-core-modules"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/2"
updated: "2026-11-08"
---

## Summary
Flexible Server B1MS + `sentinel` DB + pgvector + **Entra-only auth** + dev allow-all firewall.

## Description
Source: infra task 2.2 (`sentinel-brain/implementation/tasks/infra/phase-2-core-modules/task-2-postgresql-module.md`).

**Files created:** `modules/postgresql/{main.tf,variables.tf,outputs.tf}`

- `azurerm_postgresql_flexible_server "sentinel"` — name `sentinel-pg-0375`, version `16`,
  sku `B_Standard_B1ms`, storage `32768`, zone `"1"`,
  `authentication { active_directory_auth_enabled = true, password_auth_enabled = false }`
  (**no admin login/password**).
- **Two** `azurerm_postgresql_flexible_server_active_directory_administrator` resources, both
  with `tenant_id = data.azurerm_client_config.current.tenant_id` and `depends_on` the server:

  | Name | `object_id` | `principal_name` | `principal_type` |
  |------|-------------|------------------|------------------|
  | `human` | `var.postgres_entra_admin_object_id` | `var.postgres_entra_admin_principal_name` | `User` |
  | `backend_uami` | `var.backend_uami_principal_id` | `sentinel-backend-wi` | `ServicePrincipal` |

- `azurerm_postgresql_flexible_server_database "sentinel"` — charset UTF8, collation en_US.utf8.
- `azurerm_postgresql_flexible_server_configuration "pgvector"` — `azure.extensions = VECTOR`.
- `azurerm_postgresql_flexible_server_firewall_rule "allow_all_dev"` — 0.0.0.0–255.255.255.255,
  comment citing the §3.2 comparison table.
- **`data "azurerm_client_config" "current" {}` inside the module.** Data sources do **not**

## Acceptance criteria
- [x] Validates + fmt clean; `azure.extensions=VECTOR` present so the backend can
- [x] **Two** administrator resources, the second guarded by `count` on a null variable.
- [x] No `db_password`, no `administrator_login`, no `postgres_entra_admin_group_object_id`.
- [x] Firewall rule documented as dev-only (comment cites the §3.2 comparison table).
- [x] Outputs expose host/name/port and nothing else.
- [x] Consuming `postgres_entra_admin_*` clears 2 of the 3 `tflint`

## Outcome
`modules/postgresql/{main,variables,outputs}.tf`. Applied live: `sentinel-pg-0375` · PG 16 ·
B1MS · 32 GB · zone 1 · **AAD auth Enabled / password auth Disabled** · pgvector allow-listed
· allow-all dev firewall. **Entra-only auth proven, not inferred**: connected as
`<redacted>` with an access token as the password — PostgreSQL 16.14, `vector` 0.8.2
available, database `sentinel`.
Consuming `postgres_entra_admin_*` cleared the phase-1 tflint warnings by **use**, not
suppression — tflint went CLEAN for the first time in the project. Declared
`authentication.tenant_id` (now a pinned root var) to kill a perpetual diff Azure creates by
populating it server-side. The second Entra admin defers to 3.1 behind `enable_backend_admin`.
**Availability caveat annotated in-module:** the firewall argument covers who can *log in*,
