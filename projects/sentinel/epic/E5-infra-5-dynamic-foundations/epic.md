---
key: "E5"
title: "Dynamic foundations"
phase: 1
phase_name: "Infra"
repo: "Sentinel-infra"
status: "done"
depends_on: ["E4"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.3", "deep-dive/09-1-identity-plane.md#9.9", "ADR-028"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 22, "id": 5694991309, "url": "https://github.com/Keshav0375/sentinel-brain/issues/22"}
updated: "2026-11-08"
---

## Goal
Replace the single static estate with a two-layer platform: CAF naming with a derived uid, a deployment config file, three CI identities and Terraform workspaces joined by read-only remote state.

Source: infra phase 5 · branch `dev/infra-phase-5-dynamic-foundations` · PR https://github.com/Keshav0375/Sentinel-infra/pull/7 · signed 2026-08-25.

## Scope
- E5-T0: Destroy the old estate
- E5-T1: Deployment config schema + naming module
- E5-T2: Three CI identities + GitHub environments
- E5-T3: Platform layer — shared ACR, AKS, Postgres
- E5-T4: Workspace model + cross-layer state wiring
- E5-T5: Rewrite infra.md; supersede R5, R6, C1

## ADRs
[ADR-028](../../arch/decision-logs.md#adr-028)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
The old estate (45 resources) was destroyed and rebuilt as platform + deployment layers. Proven live: a deployment workspace plans zero Azure resources yet reads platform outputs; `gha-plan` holds read rights plus two blob reads only. Superseded R5, R6, C1 and one-cluster-per-estate.
