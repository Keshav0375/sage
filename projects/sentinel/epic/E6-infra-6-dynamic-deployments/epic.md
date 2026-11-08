---
key: "E6"
title: "Dynamic deployments and workflows"
phase: 1
phase_name: "Infra"
repo: "Sentinel-infra"
status: "done"
depends_on: ["E5"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.4", "deep-dive/09-infra-terraform.md#9.6", "ADR-028"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 29, "id": 5694992389, "url": "https://github.com/Keshav0375/sentinel-brain/issues/29"}
updated: "2026-11-08"
---

## Goal
Per-deployment layer (resource group, Key Vault, Functions, App Service, Event Grid, K8s namespace with its own workload identity), component toggles, preflight, and the Validate & Plan, Deploy (apply/destroy) and Pause/Resume workflows.

Source: infra phase 6 · branch `dev/infra-phase-6-dynamic-deployments` · PR https://github.com/Keshav0375/Sentinel-infra/pull/8, https://github.com/Keshav0375/Sentinel-infra/pull/9, https://github.com/Keshav0375/Sentinel-infra/pull/10, https://github.com/Keshav0375/Sentinel-infra/pull/11, https://github.com/Keshav0375/Sentinel-infra/pull/12, https://github.com/Keshav0375/Sentinel-infra/pull/13, https://github.com/Keshav0375/Sentinel-infra/pull/14, https://github.com/Keshav0375/Sentinel-infra/pull/15 · signed 2026-09-13.

## Scope
- E6-T1: Per-deployment layer
- E6-T2: Kubernetes namespace + per-namespace workload identity
- E6-T3: Database — shared or dedicated per deployment
- E6-T4: Component toggles + dependency preconditions
- E6-T5: Preflight job — what a plan structurally cannot check
- E6-T6: Rebuild Sentinel Infra — Validate & Plan
- E6-T7: Rebuild Sentinel Infra — Deploy (apply / destroy)
- E6-T8: New workflow — Sentinel — Pause / Resume

## ADRs
[ADR-028](../../arch/decision-logs.md#adr-028)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Full lifecycle proven live from an empty subscription: apply platform (11 resources), apply deployment (31 resources incl. the namespace, quota, LimitRange, NetworkPolicy, ServiceAccount, federated credential), destroy deployment, destroy all with verify 11/11. Five defects found by reading run history and fixed the same day (PRs #11-#15), including a destroy deadlock where the Entra admin was dropped concurrently with the database it owns. Signed with task 6.8 (Pause/Resume) recorded as shipped but never executed.
