---
key: "E4-T4"
title: "Root wiring + outputs + end-to-end apply"
epic: "E4"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E4-T1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.2", "deep-dive/09-1-identity-plane.md#9.9", "deep-dive/09-infra-terraform.md#9.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 21, "id": 5694991163, "url": "https://github.com/Keshav0375/sentinel-brain/issues/21"}
branch: "dev/infra-phase-4-wiring-and-ci"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/4"
updated: "2026-11-08"
---

## Summary
Wire every module in the root `main.tf`, resolve inter-module dependencies (ACR→AKS,

## Description
Source: infra task 4.4 (`sentinel-brain/implementation/tasks/infra/phase-4-wiring-and-ci/task-4-root-wiring-and-apply.md`).

Function→Event Grid, KV←SP), finalize `outputs.tf`, and drive a full clean `apply` from zero.

**Files modified:** `main.tf` (all module calls + `depends_on` ordering), `outputs.tf`
(acr_login_server, db_host, aks_cluster_name, app_url, key_vault_uri, function_app_id,
event grid endpoint), `README.md` (the §10 bootstrap runbook, ordered).

**Contract:** `terraform apply` from a clean state provisions the entire stack; `terraform
destroy` tears it down. Post-apply: §10 steps 6 (populate KV runtime secrets), 7 (push first
ci-runner), 10 (`alembic upgrade head` — backend task 1.3).

## Acceptance criteria
- [x] `terraform validate` + `plan` for the whole stack is clean and ordered (no cycle).
- [x] `terraform apply` from zero succeeds; all outputs populated.
- [x] README runbook reproduces the bootstrap in order.
- [x] This is the **phase-4 gate feature**: a working, reproducible Azure stack.

## Outcome
_not yet implemented_
