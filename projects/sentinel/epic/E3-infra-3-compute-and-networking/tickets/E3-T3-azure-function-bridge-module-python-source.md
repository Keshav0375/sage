---
key: "E3-T3"
title: "Azure Function bridge module (+ Python source)"
epic: "E3"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E2-T3", "E3-T2"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.2"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 13, "id": 5694989879, "url": "https://github.com/Keshav0375/sentinel-brain/issues/13"}
branch: "dev/infra-phase-3-compute-modules"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/3"
updated: "2026-11-08"
---

## Summary
Consumption Function that bridges Event Grid → GitHub `repository_dispatch` on the sentinel

## Description
Source: infra task 3.3 (`sentinel-brain/implementation/tasks/infra/phase-3-compute-modules/task-3-functions-bridge-module.md`).

repo, generating `correlation_id` and passing Datadog context through.

**Files created:**
- `modules/functions/{main.tf,variables.tf,outputs.tf}` — `azurerm_service_plan` Y1 Linux, `azurerm_storage_account` for the function, `azurerm_linux_function_app "bridge"` python 3.12, app_settings: `GITHUB_TOKEN=@Microsoft.KeyVault(...github-pat)`, `GITHUB_REPO=Keshav0375/Sentinel` (⚠ R1/R2 — not keshxvDev), `GITHUB_EVENT_TYPE=incident-alert`.
- `modules/functions/src/bridge/{__init__.py,function.json}` — Event Grid trigger; POST to `api.github.com/repos/${GITHUB_REPO}/dispatches` with `event_type` + `client_payload` (inject `correlation_id = uuid4()`, pass `dd_event_id`, `alert_id`, `tags`).
- `outputs.tf` — `function_app_id`, `function_app_name`.

## Acceptance criteria
- [x] Validates; `GITHUB_REPO` uses real owner/repo; token via Key Vault reference (not literal).
- [x] Bridge posts a well-formed `repository_dispatch` with `event_type=incident-alert` and `client_payload` carrying correlation_id + dd fields.
- [x] `function.json` binds the Event Grid trigger.

## Outcome
_not yet implemented_
