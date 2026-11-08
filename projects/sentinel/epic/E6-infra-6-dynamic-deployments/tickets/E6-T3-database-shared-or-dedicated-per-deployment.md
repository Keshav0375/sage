---
key: "E6-T3"
title: "Database — shared or dedicated per deployment"
epic: "E6"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E6-T1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.4", "deep-dive/09-infra-terraform.md#9.6"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 32, "id": 5694992864, "url": "https://github.com/Keshav0375/sentinel-brain/issues/32"}
branch: "dev/infra-phase-6-dynamic-deployments"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/8"
updated: "2026-11-08"
---

## Summary
`database.mode` per deployment, defaulting to `shared`.

## Description
Source: infra task 6.3 (`sentinel-brain/implementation/tasks/infra/phase-6-dynamic-deployments/task-3-database-modes.md`).

**`shared`** — a database plus an Entra role on the platform server. Cheap: one server's compute
serves every deployment. Accepted cost: shared compute, so a runaway query in one deployment can
slow another.

**`dedicated`** — its own flexible server in the deployment's resource group. Full isolation of
compute, storage, admins and backups. Costs a VM against the same grant, ~8 minutes to create,
and adds one more server that must be **started before any plan can run** — the
`ServerStoppedError` problem multiplied per deployment, which the CI start-guard must therefore
iterate over rather than hardcode one server name.

Both paths must produce the **same connection contract** so the backend cannot tell them apart:
one output shape, `db_host` / `db_name`, Entra-only auth, no password in either case.

## Acceptance criteria
- [x] Both modes apply and produce identical output *shapes*
- [x] Switching mode on an existing deployment is either clean or fails loudly — never silent data loss
- [x] `shared` grants only that deployment's database, verified by a cross-deployment connection attempt that is refused
- [x] The CI start-guard discovers servers dynamically; no hardcoded server name anywhere

## Outcome
_not yet implemented_
