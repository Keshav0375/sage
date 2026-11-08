---
key: "E7-T2"
title: "Root infra workflows, OIDC-ready gate and identity scripts"
epic: "E7"
repo: "Sentinel"
size: "M"
status: "done"
depends_on: ["E7-T1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.7"]
issue: null
branch: "dev/infra-phase-7-monorepo"
pr: "https://github.com/Keshav0375/Sentinel/pull/32"
updated: "2026-11-08"
---

## Summary
Move the infra workflows to the root as `infra_validate_plan`, `infra_deploy`, `infra_pause` and `infra_runners` (working-directory `infra`, `infra/**` filters, own concurrency groups, SHA pins).

## Description
Source: infra task 7.2 (built in https://github.com/Keshav0375/Sentinel/pull/32).

Move the infra workflows to the root as `infra_validate_plan`, `infra_deploy`, `infra_pause` and `infra_runners` (working-directory `infra`, `infra/**` filters, own concurrency groups, SHA pins); add the `INFRA_OIDC_READY` gate; backend workflows ignore `infra/**`; `bootstrap-identities.sh` defaults `INFRA_REPO=Sentinel` and updates FIC subjects in place; `set-gh-secrets.sh` targets `Sentinel`; 18 workflow tests.

## Acceptance criteria
- [x] Cloud jobs skip cleanly while `INFRA_OIDC_READY` is unset
- [x] Backend workflows do not trigger on `infra/**` changes
- [x] Infra gate VERDICT GREEN

## Outcome
Merged in https://github.com/Keshav0375/Sentinel/pull/32 on 2026-10-25.
