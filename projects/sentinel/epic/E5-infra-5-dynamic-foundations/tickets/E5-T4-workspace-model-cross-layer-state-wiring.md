---
key: "E5-T4"
title: "Workspace model + cross-layer state wiring"
epic: "E5"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E5-T3"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.3", "deep-dive/09-1-identity-plane.md#9.9"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 27, "id": 5694992079, "url": "https://github.com/Keshav0375/sentinel-brain/issues/27"}
branch: "dev/infra-phase-5-dynamic-foundations"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/7"
updated: "2026-11-08"
---

## Summary
How the two layers find each other without sharing a state file.

## Description
Source: infra task 5.4 (`sentinel-brain/implementation/tasks/infra/phase-5-dynamic-foundations/task-4-workspaces-and-remote-state.md`).

**Workspaces.** `platform` for the shared layer; `<deployment>-<env>` for each deployment. The
azurerm backend maps a workspace to `env:/<workspace>/<key>` automatically, so one storage
account holds all of them with no `-backend-config` juggling per run.

**Deployments read the platform, never write it:**

A read-only data source is the right coupling: a deployment *needs* the cluster's OIDC issuer
and the ACR login server, and must be unable to change either. The alternative — passing them
as variables — means the same values typed in two places and drifting.

**Root layout.** One root, `var.layer` selecting `platform` or `deployment`, with modules
`count`-gated on it. Considered and rejected: two separate root directories. Two roots means two
provider blocks, two lock files and two `init` paths to keep in step, for one boolean's worth of
separation.

## Acceptance criteria
- [x] `platform` and a scratch `t1-dev` workspace coexist; each plan sees only its own resources
- [x] A deployment plan resolves the platform's OIDC issuer through the remote-state data source
- [x] `terraform destroy` in a deployment workspace proposes **zero** platform resources — assert this explicitly, it is the whole point
- [x] Selecting a non-existent workspace creates it rather than failing

## Outcome
_not yet implemented_
