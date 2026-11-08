---
key: "E7"
title: "Monorepo: Sentinel-infra into Sentinel/infra"
phase: 4
phase_name: "Post-release"
repo: "Sentinel"
status: "done"
depends_on: ["E6", "E19"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.7", "ADR-042"]
issue: null
updated: "2026-11-08"
---

## Goal
Bring the Terraform repo into the `Sentinel` monorepo as `infra/` with full history, so one repo holds the backend, the infra and the dashboard.

Source: infra phase 7 · branch `dev/infra-phase-7-monorepo` · PR https://github.com/Keshav0375/Sentinel/pull/32 · signed 2026-10-25.

## Scope
- E7-T1: Subtree import of Sentinel-infra into infra/
- E7-T2: Root infra workflows, OIDC-ready gate and identity scripts

## ADRs
[ADR-042](../../arch/decision-logs.md#adr-042)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
`git subtree add` imported 38 commits; infra workflows moved to the root as `infra_*.yml` with `working-directory: infra`, path filters, SHA pins and an `INFRA_OIDC_READY` gate so cloud jobs skip until the federated credentials are re-bound; 18 workflow tests. Gates: backend GREEN, infra GREEN (13 ran). Owner steps remain (re-run bootstrap, re-push secrets, set the gate variable), then `Sentinel-infra` is archived.
