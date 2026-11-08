---
key: "E1"
title: "Foundations and bootstrap"
phase: 1
phase_name: "Infra"
repo: "Sentinel-infra"
status: "done"
depends_on: []
arch_refs: ["deep-dive/09-infra-terraform.md#9.1", "deep-dive/09-1-identity-plane.md#9.9", "ADR-014", "ADR-021", "ADR-022", "ADR-023", "ADR-025"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 2, "id": 5694988095, "url": "https://github.com/Keshav0375/sentinel-brain/issues/2"}
updated: "2026-11-08"
---

## Goal
A Terraform root that plans against the real subscription, remote state in Azure Storage, and GitHub OIDC federation so no CI job ever holds an Azure secret.

Source: infra phase 1 · branch `dev/infra-phase-1-foundations` · PR https://github.com/Keshav0375/Sentinel-infra/pull/1 · signed 2026-08-15.

## Scope
- E1-T1: Repo skeleton + provider/backend/vars config
- E1-T2: Remote state bootstrap (script + doc)
- E1-T3: OIDC federation (bootstrap + Terraform federated creds)

## ADRs
[ADR-014](../../arch/decision-logs.md#adr-014), [ADR-021](../../arch/decision-logs.md#adr-021), [ADR-022](../../arch/decision-logs.md#adr-022), [ADR-023](../../arch/decision-logs.md#adr-023), [ADR-025](../../arch/decision-logs.md#adr-025)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
`terraform plan` showed No changes; both bootstrap scripts proved idempotent; five federated credentials verified in Azure. Resolved R3 (region `canadacentral`), R4, R5 and conflicts C1-C9, C12, C13 before code. Found that the phase passed only because it applied locally as Owner: CI had never authenticated (fixed in E4).
