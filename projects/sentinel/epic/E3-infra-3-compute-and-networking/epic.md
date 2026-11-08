---
key: "E3"
title: "Compute and networking modules"
phase: 1
phase_name: "Infra"
repo: "Sentinel-infra"
status: "done"
depends_on: ["E2"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.2", "deep-dive/09-1-identity-plane.md#9.8", "ADR-022", "ADR-026"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 10, "id": 5694989387, "url": "https://github.com/Keshav0375/sentinel-brain/issues/10"}
updated: "2026-11-08"
---

## Goal
AKS with workload identity, Event Grid two-signal routing, the Function bridge that stamps `signal_type`, the App Service F1 target, the identity-tenant app registrations and Key Vault rotation.

Source: infra phase 3 · branch `dev/infra-phase-3-compute-modules` · PR https://github.com/Keshav0375/Sentinel-infra/pull/3 · signed 2026-08-24.

## Scope
- E3-T1: AKS module (+ AcrPull, scale-to-zero lifecycle)
- E3-T2: Event Grid module
- E3-T3: Azure Function bridge module (+ Python source)
- E3-T4: App Service module (F1 target)
- E3-T5: Identity plane: backend Entra app (two-tenant)
- E3-T6: Key Vault rotation: policy + rotator Function

## ADRs
[ADR-022](../../arch/decision-logs.md#adr-022), [ADR-026](../../arch/decision-logs.md#adr-026)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
AKS live on one ARM64 `B2pls_v2` node, stopped when idle; bridge and rotator Functions registered; 14 handler unit tests run by the gate. Azure taught four constraints live: Y1 and F1 plans cannot share a resource group, the free AKS SKU fails the system-pool RAM floor, new Entra tenants reject bare `api://name` URIs, and a guest invitation must be redeemed before CLI tokens work.
