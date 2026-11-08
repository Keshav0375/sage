---
key: "E6-T4"
title: "Component toggles + dependency preconditions"
epic: "E6"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E6-T1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.4", "deep-dive/09-infra-terraform.md#9.6"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 33, "id": 5694993044, "url": "https://github.com/Keshav0375/sentinel-brain/issues/33"}
branch: "dev/infra-phase-6-dynamic-deployments"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/8"
updated: "2026-11-08"
---

## Summary
`components: [keyvault, database, functions, app_service, event_grid, namespace]` drives `count`

## Description
Source: infra task 6.4 (`sentinel-brain/implementation/tasks/infra/phase-6-dynamic-deployments/task-4-toggles-and-preconditions.md`).

on each module.

**Checkbox independence is a lie, and this task exists to say so out loud.** The components have
hard dependencies:

| Component | Requires |
|---|---|
| `functions` | `keyvault` (KV references for its secrets), `event_grid` |
| `event_grid` | `functions` (the subscription needs the function app id) |
| `namespace` | platform AKS |
| backend identity | `namespace` + `database` + `keyvault` |

Unchecking `keyvault` while `functions` is on does not produce a smaller stack — it produces a
provider error hundreds of lines into a plan, naming a resource attribute rather than the
mistake. So every dependency gets a `precondition` that fails in seconds with the actual
sentence: `"components: functions requires keyvault"`.

Note `functions` and `event_grid` are mutually dependent — they are a single unit and the
validation should say so rather than pretending either can stand alone.

## Acceptance criteria
- [x] Every dependency in the table is enforced by a precondition with a human-readable message
- [x] An invalid combination fails within ~5 seconds of `plan`, before any provider call
- [x] A minimal deployment (`[keyvault, database]`) applies successfully
- [x] Removing a component from a live deployment destroys only that component

## Outcome
_not yet implemented_
