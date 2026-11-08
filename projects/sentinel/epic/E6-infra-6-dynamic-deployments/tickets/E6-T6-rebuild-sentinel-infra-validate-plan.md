---
key: "E6-T6"
title: "Rebuild Sentinel Infra — Validate & Plan"
epic: "E6"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E6-T5"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.4", "deep-dive/09-infra-terraform.md#9.6"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 35, "id": 5694993335, "url": "https://github.com/Keshav0375/sentinel-brain/issues/35"}
branch: "dev/infra-phase-6-dynamic-deployments"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/8"
updated: "2026-11-08"
---

## Summary
Rewrite `ci_infra_dry.yml`. `workflow_dispatch` caps at **10 inputs**, which is the constraint

## Description
Source: infra task 6.6 (`sentinel-brain/implementation/tasks/infra/phase-6-dynamic-deployments/task-6-validate-plan-workflow.md`).

that shaped the whole config design: the form carries *shape and intent*, the YAML carries *size
and detail*.

**Jobs:** `preflight` → `run-validate` → `run-plan`.

`environment: plan` on every job, deliberately. A dispatch from a feature branch presents
`:ref:refs/heads/<branch>`, which has no credential; declaring the environment rewrites the
subject to `:environment:plan` and makes config-from-any-branch work. Same mechanism that broke
the first apply, used on purpose.

Keep from phase 4, all of it learned live: values reach Terraform through `env:` not `${{ }}`
splicing; `ARM_*` on every terraform step; the Postgres start-guard; `run-validate` runs
`-backend=false` so it needs no credential at all and works before anything is bootstrapped.

## Acceptance criteria
- [x] ≤10 inputs; `deployment` alone is sufficient for a run
- [x] Dispatch from a non-main branch reads that branch's config and authenticates
- [x] `run-validate` still requires no Azure credential
- [x] Plan posted as a PR comment, truncated at 60000 chars
- [x] `actionlint` clean

## Outcome
_not yet implemented_
