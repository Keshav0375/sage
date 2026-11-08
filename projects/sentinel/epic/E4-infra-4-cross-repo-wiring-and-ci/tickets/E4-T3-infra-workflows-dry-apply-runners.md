---
key: "E4-T3"
title: "Infra workflows (dry / apply / runners)"
epic: "E4"
repo: "Sentinel-infra"
size: "M"
status: "done"
depends_on: ["E1-T3", "E4-T2"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.5"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 20, "id": 5694990997, "url": "https://github.com/Keshav0375/sentinel-brain/issues/20"}
branch: "dev/infra-phase-4-wiring-and-ci"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/4"
updated: "2026-11-08"
---

## Summary
**Three** GHA workflows in `.github/workflows/`.

## Description
Source: infra task 4.3 (`sentinel-brain/implementation/tasks/infra/phase-4-wiring-and-ci/task-3-infra-workflows.md`).

> ⚠ **Body rewritten 2026-08-24.** It previously described four workflows and a gate step —
> the R6 banner above said three while every other line said four. Two decisions settle it:
>
> - **decisions.md 2026-08-24 #1** — `quality_gate.py` lives in the `Sentinel` repo and these
>   workflows run in `Sentinel-infra`. Rather than check out a second repo, infra CI is
>   **terraform-only**. ⚠️ tflint / shellcheck / gitleaks therefore never run on a PR; the gate
>   is a local pre-commit discipline. Accepted knowingly — see the decision entry.
> - **decisions.md 2026-08-24 #3** — the dry run splits by credential need, because the
>   federated credentials cover only `main` and `pull_request`.

**Files created:**

- **`ci_infra_dry.yml`** — `[infra] terraform — validate and plan (dry run)`
  - `on:` `push: branches: ['**']`, `pull_request: branches: [main]`
  - `permissions:` `id-token: write`, `contents: read`, `pull-requests: write`
  - **`run-validate`** — *no Azure*: `fmt -check -recursive`, `init -backend=false`, `validate`.
    Runs on **every** push, `dev/*` included. `-backend=false` is what makes it credential-free.
  - **`run-plan`** — `needs: run-validate`, `if: pull_request || ref == refs/heads/main`.

## Acceptance criteria
- [x] **Three** workflows; `ci_destroy_infra.yml` does **not** exist.
- [x] `actionlint` clean on all three.
- [x] Every Azure job declares `id-token: write`.
- [x] `run-validate` runs `init -backend=false` and calls no Azure action — a `dev/*` push
- [x] `run-plan` is gated to `pull_request` + `push main` (the only federated subjects).
- [x] Every terraform step sets the four `ARM_*` env vars.
- [x] `identity_client_id` and `identity_use_oidc` are passed to plan and apply.
- [x] `ci_infra.yml` uses `environment: production`.
- [x] No `db_password` and no `quality_gate.py` reference in any workflow.

## Outcome
_not yet implemented_
