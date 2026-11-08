---
key: "E6-T7"
title: "Rebuild Sentinel Infra — Deploy (apply / destroy)"
epic: "E6"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E6-T6"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.4", "deep-dive/09-infra-terraform.md#9.6"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 36, "id": 5694993488, "url": "https://github.com/Keshav0375/sentinel-brain/issues/36"}
branch: "dev/infra-phase-6-dynamic-deployments"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/8"
updated: "2026-11-08"
---

## Summary
Rewrite `ci_infra.yml`. One workflow, both directions.

## Description
Source: infra task 6.7 (`sentinel-brain/implementation/tasks/infra/phase-6-dynamic-deployments/task-7-deploy-workflow.md`).

`environment: production` for apply, **`environment: destroy` for destroy** — distinct subjects,
so a required reviewer can be attached to destruction alone.

**Destroy safeguards, and why each exists:**
- typed confirmation matching the deployment name — the difference between an irreversible action and a mis-click
- `workflow_dispatch` only; no push path can ever destroy
- **purge the Key Vault after destroy.** Without it the name is reserved 7 days and the next create fails on a vault nobody can see. This is the whole reason `gha-deploy` holds purge rights, and the destroy→recreate cycle is the phase's headline test.
- refuse to destroy the `platform` workspace from this workflow — the shared layer is not a deployment

**Acceptance test for the phase:** destroy `demo1`, recreate `demo1`, and get an identical
estate. That single cycle exercises naming determinism, purge, workspace handling and namespace
teardown at once.

## Acceptance criteria
- [x] `deployment: demo1` + `apply` produces a complete deployment with no other input
- [x] destroy without a matching `confirm` refuses before authenticating
- [x] destroy purges the vault; an immediate recreate succeeds
- [x] `platform` cannot be destroyed here
- [x] `actionlint` clean

## Outcome
_not yet implemented_
