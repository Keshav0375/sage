---
key: "E3-T6"
title: "Key Vault rotation: policy + rotator Function"
epic: "E3"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E2-T3", "E3-T3"]
arch_refs: ["deep-dive/09-1-identity-plane.md#9.13"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 16, "id": 5694990389, "url": "https://github.com/Keshav0375/sentinel-brain/issues/16"}
branch: "dev/infra-phase-3-compute-modules"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/3"
updated: "2026-11-08"
---

## Summary
Rotate the LLM API keys on a schedule with a Function triggered by Key Vault near-expiry events.

## Description
Source: infra task 3.6 (`sentinel-brain/implementation/tasks/infra/phase-3-compute-modules/task-6-keyvault-rotation.md`).

**Files created / changed:**
- `modules/keyvault/` — set an expiry on `anthropic-api-key` / `openai-api-key` (seed ~90d);
  document that the rotator owns subsequent versions.
- `modules/functions/`:
  - `azurerm_linux_function_app "rotator"` (system-assigned MI) sharing the bridge's `Y1` plan;
    MI granted `Key Vault Secrets Officer` (in `task-3-keyvault-module`).
  - `azurerm_eventgrid_system_topic "kv"` (source = the vault) + system-topic event subscription
    for `Microsoft.KeyVault.SecretNearExpiry` → the rotator Function.
  - `src/rotate/` (Python): read secret name from the event → call the provider key-management
    API to mint a fresh key (Anthropic Admin API where org-admin available; else post a Teams
    "manual rotation required" alert) → `set_secret` a new version with a fresh 90-day expiry.

**Contract:**

## Acceptance criteria
- [x] `terraform validate`/`tflint` pass; system topic + subscription + Function plan cleanly.
- [x] Setting a short expiry on a test secret fires `SecretNearExpiry` → Function runs → new version appears.
- [x] Rotator degrades gracefully (Teams alert) when no provider key API is available.

## Outcome
_not yet implemented_
