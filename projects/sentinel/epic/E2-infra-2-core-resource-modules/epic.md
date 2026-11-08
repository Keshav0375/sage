---
key: "E2"
title: "Core resource modules"
phase: 1
phase_name: "Infra"
repo: "Sentinel-infra"
status: "done"
depends_on: ["E1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.2", "deep-dive/13-cost.md#13.1", "ADR-017", "ADR-025"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 6, "id": 5694988745, "url": "https://github.com/Keshav0375/sentinel-brain/issues/6"}
updated: "2026-11-08"
---

## Goal
ACR, PostgreSQL (Entra-only, pgvector) and Key Vault (RBAC) as modules, all on the free grants.

Source: infra phase 2 · branch `dev/infra-phase-2-core-modules` · PR https://github.com/Keshav0375/Sentinel-infra/pull/2 · signed 2026-08-23.

## Scope
- E2-T1: ACR module
- E2-T2: PostgreSQL module (+ pgvector, firewall)
- E2-T3: Key Vault module (+ RBAC roles, secrets)

## ADRs
[ADR-017](../../arch/decision-logs.md#adr-017), [ADR-025](../../arch/decision-logs.md#adr-025)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
All three applied and verified live: an Entra token used as the Postgres password (no password exists on the server), a Key Vault secret written, read, deleted and purged through RBAC. tflint clean for the first time. Cost $0 after reading the Azure for Students entitlement (ACR Standard is free, Basic would have billed).
