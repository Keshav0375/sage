---
key: "E10"
title: "Scenario branches"
phase: 2
phase_name: "Deployment"
repo: "Sentinel-deployment"
status: "done"
depends_on: ["E9"]
arch_refs: ["deep-dive/08-deployment-and-scenarios.md#8.3", "ADR-018", "ADR-031"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 46, "id": 5694995085, "url": "https://github.com/Keshav0375/sentinel-brain/issues/46"}
updated: "2026-11-08"
---

## Goal
Thirty pre-authored scenario branches (10 clean, 10 deploy-failure, 10 runtime-error) and the `scenarios/branches.yaml` ground-truth catalog that doubles as the eval set.

Source: deployment phase 3 · branch `dev/deploy-phase-3-scenario-branches` · PR https://github.com/Keshav0375/Sentinel-deployment/pull/4 · signed 2026-10-07.

## Scope
- E10-T1: 30 scenario branches + scenarios/branches.yaml catalog

## ADRs
[ADR-018](../../arch/decision-logs.md#adr-018), [ADR-031](../../arch/decision-logs.md#adr-031)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Verified on offline proof (gate GREEN, 248 tests). The catalog was redesigned for determinism before building. The live smoke (pass/01, deployfail/03, runtime/01) was deferred to the first backend work with the estate up and has not run yet.
