---
key: "E5-T5"
title: "Rewrite infra.md; supersede R5, R6, C1"
epic: "E5"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E5-T4"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.3", "deep-dive/09-1-identity-plane.md#9.9"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 28, "id": 5694992226, "url": "https://github.com/Keshav0375/sentinel-brain/issues/28"}
branch: "dev/infra-phase-5-dynamic-foundations"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/7"
updated: "2026-11-08"
---

## Summary
The architecture describes a single static estate. After phase 5 that is false in enough places

## Description
Source: infra task 5.5 (`sentinel-brain/implementation/tasks/infra/phase-5-dynamic-foundations/task-5-docs-and-supersessions.md`).

that leaving it would make it actively misleading — the failure mode this project has already
paid for ten times in phase 4's pre-build audit.

**Rewrite:** §2 (repo layout + two layers), §3 (platform vs deployment resources), §4 (three
identities, environment-scoped subjects), §8 (workspaces + remote state), §9 (config file
replaces most repo variables), §10 (bootstrap: state → identities → platform).

**Supersede in `decisions.md`, each with its original reasoning preserved and what changed:**

| | Was | Now |
|---|---|---|
| **R5** | Contributor + RBAC Admin scoped to `sentinel-rg`; deliberately narrow because PR-reachable | Subscription scope, split across three identities; the narrowness moves from *scope* to *reachability* |
| **R6** | No CI destroy — purge needs subscription scope CI should not hold | CI destroys, behind `environment: destroy`. Purge is required for the destroy→recreate cycle to work at all |
| **C1** | Resource groups bootstrap-created, read-only | Managed, except the state RG which can never manage itself |
| **§3.7** | One cluster per estate | One cluster, namespace per deployment — forced by the 6-vCPU ceiling |

**Rewrite `docs/BOOTSTRAP.md`** — the new order is state storage → identities → platform → first
deployment. Keep the Day-2 sections; both are still true and both were learned the hard way.

## Acceptance criteria
- [x] No section of `infra.md` describes the pre-phase-5 model without marking it superseded
- [x] R5, R6, C1 each carry a supersession entry naming what replaced them and why
- [x] `python scripts/arch.py infra --list` resolves; no dangling `§` references
- [x] No `0375` and no `ci_destroy_infra` anywhere outside a historical note

## Outcome
_not yet implemented_
