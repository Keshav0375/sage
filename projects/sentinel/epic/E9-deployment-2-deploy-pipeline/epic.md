---
key: "E9"
title: "Deploy pipeline"
phase: 2
phase_name: "Deployment"
repo: "Sentinel-deployment"
status: "done"
depends_on: ["E8"]
arch_refs: ["deep-dive/08-deployment-and-scenarios.md#8.2", "deep-dive/08-deployment-and-scenarios.md#8.4", "ADR-030", "ADR-031"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 42, "id": 5694994424, "url": "https://github.com/Keshav0375/sentinel-brain/issues/42"}
updated: "2026-11-08"
---

## Goal
`ci_app_deployment.yml` (build, deploy, verify, record with an Entra DB token, summary), the `dd-report` action and the two Datadog triggers.

Source: deployment phase 2 · branch `dev/deploy-phase-2-deploy-pipeline` · PR https://github.com/Keshav0375/Sentinel-deployment/pull/2, https://github.com/Keshav0375/Sentinel-deployment/pull/3 · signed 2026-10-07.

## Scope
- E9-T1: dd-report composite action
- E9-T2: ci_app_deployment.yml (Build→Deploy→Verify→Record→Summary)
- E9-T3: Datadog monitors (deploy-failure + runtime-health)

## ADRs
[ADR-030](../../arch/decision-logs.md#adr-030), [ADR-031](../../arch/decision-logs.md#adr-031)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Live run green: the version deployed under the `gha-app` OIDC identity, Postgres Entra login worked, Datadog accepted events and logs, Event Grid reported DeliverySuccess. The record stage failed only on the missing `deployments` table, which backend task 1.3 later created. Estate destroyed after the test.
