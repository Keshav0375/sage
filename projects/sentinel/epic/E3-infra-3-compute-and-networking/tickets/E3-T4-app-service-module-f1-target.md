---
key: "E3-T4"
title: "App Service module (F1 target)"
epic: "E3"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E1-T1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.2"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 14, "id": 5694990050, "url": "https://github.com/Keshav0375/sentinel-brain/issues/14"}
branch: "dev/infra-phase-3-compute-modules"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/3"
updated: "2026-11-08"
---

## Summary
Free F1 Linux web app that hosts the dummy-api-0375 (deployment repo's zip-deploy target).

## Description
Source: infra task 3.4 (`sentinel-brain/implementation/tasks/infra/phase-3-compute-modules/task-4-app-service-module.md`).

**Files created:** `modules/app-service/{main.tf,variables.tf,outputs.tf}`
- `azurerm_service_plan "deployment"` — name `sentinel-deploy-plan`, Linux, sku `F1`.
- `azurerm_linux_web_app "dummy_api"` — name `dummy-api-0375`, python 3.12, app_settings: `APP_VERSION=initial`, `DD_SERVICE=dummy-api-0375`, `DD_ENV=dev`, `SCM_DO_BUILD_DURING_DEPLOYMENT=true`; startup command (gunicorn+uvicorn worker, §2.5) via `site_config.app_command_line`.
- `variables.tf` — `resource_group_name`, `location`.
- `outputs.tf` — `app_url` (`https://dummy-api-0375.azurewebsites.net`), `app_name`.

## Acceptance criteria
- [x] Validates; F1 plan + web app; startup command set for gunicorn/uvicorn; DD_* app settings present.
- [x] Output `app_url` matches what deployment's `DEPLOYED_APP_URL` will use.

## Outcome
_not yet implemented_
