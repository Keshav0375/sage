---
key: "E4-T1"
title: "Cross-repo secret + variable distribution (github provider)"
epic: "E4"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E2-T1", "E1-T3", "E3-T5"]
arch_refs: ["deep-dive/09-1-identity-plane.md#9.13"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 18, "id": 5694990702, "url": "https://github.com/Keshav0375/sentinel-brain/issues/18"}
branch: "dev/infra-phase-4-wiring-and-ci"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/4"
updated: "2026-11-08"
---

## Summary
After apply, push identity/ACR values to the `Sentinel` and `Sentinel-deployment` repos so that

## Description
Source: infra task 4.1 (`sentinel-brain/implementation/tasks/infra/phase-4-wiring-and-ci/task-1-cross-repo-secrets.md`).

no value is ever hand-set in the GitHub UI.

> ⚠ **Corrected 2026-08-24 (decisions.md).** Three things in the original spec were wrong: the
> client id was sourced from `azuread_application.sentinel_gha`, **which rev-9 deleted**; the
> identity pointers were pushed as *secrets*, which under OIDC masks public identifiers and
> makes `AADSTS700213` unreadable; and the identity-tenant caller that §4.5 needs was pushed
> nowhere. Nine resources became **twelve**, split across two resource types.

**Files created:** `github-repo-config.tf`

**Secrets (`github_actions_secret`) — real credentials only, 3:**

| Repo | Name | Value |
|------|------|-------|
| `Sentinel` | `ACR_USERNAME` | `module.acr.acr_admin_username` |
| `Sentinel` | `ACR_PASSWORD` | `module.acr.acr_admin_password` (sensitive) |
| `Sentinel` | `ACR_LOGIN_SERVER` | `module.acr.acr_login_server` — secret for symmetry with §6.4's `container:` block, which reads it beside the credential pair |

**Variables (`github_actions_variable`) — public identifiers, 9:**

## Acceptance criteria
- [x] Validates; **3 secrets + 9 variables**; exact repo casing.
- [x] Client id comes from the **UAMI**, not a non-existent `azuread_application.sentinel_gha`.
- [x] `ACR_PASSWORD` is sensitive and no secret value appears in plan output.
- [x] No `DB_PASSWORD` / `AZURE_CLIENT_SECRET` resource exists.

## Outcome
_not yet implemented_
