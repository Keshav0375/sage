---
key: "E4"
title: "Cross-repo wiring and CI"
phase: 1
phase_name: "Infra"
repo: "Sentinel-infra"
status: "done"
depends_on: ["E3"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.5", "deep-dive/09-1-identity-plane.md#9.13", "ADR-027"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 17, "id": 5694990536, "url": "https://github.com/Keshav0375/sentinel-brain/issues/17"}
updated: "2026-11-08"
---

## Goal
Infra CI (validate, plan, apply, runner image) and the cross-repo distribution of identity pointers and outputs.

Source: infra phase 4 · branch `dev/infra-phase-4-wiring-and-ci` · PR https://github.com/Keshav0375/Sentinel-infra/pull/4, https://github.com/Keshav0375/Sentinel-infra/pull/5, https://github.com/Keshav0375/Sentinel-infra/pull/6 · signed 2026-08-24.

## Scope
- E4-T1: Cross-repo secret + variable distribution (github provider)
- E4-T2: CI runner image (Dockerfile + build-push)
- E4-T3: Infra workflows (dry / apply / runners)
- E4-T4: Root wiring + outputs + end-to-end apply

## ADRs
[ADR-027](../../arch/decision-logs.md#adr-027)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
The identity plane was proven live on the first CI run: Terraform refreshed the whole estate under the CI managed identity, exercising the OIDC round trip, the RBAC grant and the state blob, none of which phases 1-3 had tested. Follow-ups landed as PR #5 (review fixes, `environment:production` credential, DB start guard) and PR #6 (workflow renames, sha image tags). Closed B16.
