---
key: "E6-T5"
title: "Preflight job — what a plan structurally cannot check"
epic: "E6"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E5-T1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.4", "deep-dive/09-infra-terraform.md#9.6"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 34, "id": 5694993194, "url": "https://github.com/Keshav0375/sentinel-brain/issues/34"}
branch: "dev/infra-phase-6-dynamic-deployments"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/8"
updated: "2026-11-08"
---

## Summary
`terraform plan` proves auth works, state is readable, config is valid, and what would change.

## Description
Source: infra task 6.5 (`sentinel-brain/implementation/tasks/infra/phase-6-dynamic-deployments/task-5-preflight.md`).

It **cannot** prove an apply will succeed. Every item below is a failure this project actually
hit, and none of them are visible to a plan:

| Check | The failure it prevents |
|---|---|
| both tenants mint a token | phase 4: the azuread client 401'd after the azurerm plan fully succeeded |
| global name availability (ACR, storage, KV, PG, app) | `sentineltfstate` was taken by another tenant |
| soft-deleted vault holding the name | destroy → recreate fails on a vault nobody can see |
| AKS SKU exists in region **and** is permitted | `B2ats_v2` failed the system-pool RAM floor; `B2s` was not in the allowed list |
| regional vCPU quota ≥ requested | the 6-vCPU ceiling |
| resource providers registered | ten had to be registered by hand |
| Postgres running | `400 ServerStoppedError` broke a run three times |

Runs as a job before validate, on `environment: plan` so it needs only the read-only identity.
Output is a table of pass/fail with the remedy beside each failure — a preflight that says "no"
without saying "run this" has moved the problem rather than solved it.

## Acceptance criteria
- [x] All seven checks implemented and independently failable
- [x] Every failure prints the exact remediating command
- [x] Runs entirely under `gha-plan` — no write action required
- [x] Completes in under ~60s

## Outcome
_not yet implemented_
