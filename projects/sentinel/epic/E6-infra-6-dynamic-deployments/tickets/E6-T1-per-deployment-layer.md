---
key: "E6-T1"
title: "Per-deployment layer"
epic: "E6"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E5-T4"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.4", "deep-dive/09-infra-terraform.md#9.6"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 30, "id": 5694992530, "url": "https://github.com/Keshav0375/sentinel-brain/issues/30"}
branch: "dev/infra-phase-6-dynamic-deployments"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/8"
updated: "2026-11-08"
---

## Summary
Everything a single deployment owns, in its own resource group and workspace.

## Description
Source: infra task 6.1 (`sentinel-brain/implementation/tasks/infra/phase-6-dynamic-deployments/task-1-deployment-layer.md`).

Modules are the phase-2/3 ones, re-parameterised on the naming module instead of hardcoded
names. The Y1/F1 webspace conflict is structural and survives: Consumption and Dedicated Linux
plans cannot share a resource group, so each deployment needs its own functions RG
(`rg-<d>-<env>-func-cc`) — the same constraint that produced `sentinel-func-rg`, now derived
rather than special-cased.

## Acceptance criteria
- [x] Two deployments coexist with no name collision and no shared resource
- [x] Destroying one leaves the other and the platform untouched
- [x] Key Vault is created empty — Terraform never writes a runtime secret
- [x] Every name comes from `module.naming`; no literal resource name in any module

## Outcome
_not yet implemented_
