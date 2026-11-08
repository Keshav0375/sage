---
key: "E3-T2"
title: "Event Grid module"
epic: "E3"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E1-T1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.2"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 12, "id": 5694989721, "url": "https://github.com/Keshav0375/sentinel-brain/issues/12"}
branch: "dev/infra-phase-3-compute-modules"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/3"
updated: "2026-11-08"
---

## Summary
Event Grid topic that routes Datadog webhooks to the bridge Function.

## Description
Source: infra task 3.2 (`sentinel-brain/implementation/tasks/infra/phase-3-compute-modules/task-2-event-grid-module.md`).

**Files created:** `modules/event-grid/{main.tf,variables.tf,outputs.tf}`
- `azurerm_eventgrid_topic "sentinel"` — name `sentinel-events`.
- `azurerm_eventgrid_event_subscription "to_function"` — `azure_function_endpoint { function_id = "${var.function_app_id}/functions/bridge" }`.
- `variables.tf` — `resource_group_name`, `location`, `function_app_id`.
- `outputs.tf` — `topic_id`, `topic_endpoint`, `topic_key` (sensitive — Datadog webhook uses it).

**Note:** the subscription depends on the Function existing (task 3.3) → wire ordering in root `main.tf` (task 4.4).

## Acceptance criteria
- [x] Validates; topic + subscription defined; outputs expose endpoint + key for the Datadog monitor webhook.
- [x] Subscription targets the `bridge` function.

## Outcome
_not yet implemented_
