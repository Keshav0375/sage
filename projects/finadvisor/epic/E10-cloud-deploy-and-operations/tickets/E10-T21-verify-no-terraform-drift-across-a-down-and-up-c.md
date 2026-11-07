---
key: "E10-T21"
title: "Verify no Terraform drift across a down and up cycle"
epic: "E10"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E10-T16", "E10-T18", "E10-T12"]
arch_refs: ["deep-dive/04-1-key-flows.md#4.14 Flow 5 and Flow 6", "deep-dive/04-components-and-responsibilities.md#4.12", "ADR-020"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Run demo-down then demo-up and assert terraform plan is clean at every stage.

## Description
Epic done-when: '`terraform plan` is clean (no drift) after a down / up cycle thanks to `ignore_changes`.' 4.14: Terraform uses lifecycle.ignore_changes on activation_policy, min_instance_count and manual_instance_count. Add scripts/demo/drift_check.sh and a make target `make demo-cycle-test`: apply, `terraform plan -detailed-exitcode`, demo-down, plan, demo-up, plan, each must return exit code 0; also confirm the end state of demo-down (SQL NEVER, worker 0, min 0, Valkey absent) and demo-up (`/readyz` 200).

If a plan shows drift on an attribute (for example the Scheduler paused state, a Cloud Run revision template field, or the Kong environment variable set by demo-up), fix it by adding a narrowly scoped ignore_changes in the owning Terraform file and list it in the PR; record each added attribute in questions if it is not one of the three the arch names. The Kong Valkey env var set by demo-up is the most likely candidate (E2 owns the module; make the minimal change there).

## Acceptance criteria
- [ ] `make demo-cycle-test` exits 0; the log shows three `terraform plan -detailed-exitcode` results all equal to 0 (after apply, after demo-down, after demo-up)
- [ ] The test asserts the post-down state: Cloud SQL activation policy NEVER, worker pool count 0, chat-api and fa-gateway min 0, `gcloud redis`/memorystore instance absent; it fails if any is wrong (negative run with a stubbed non-zero worker count fails)
- [ ] The test asserts the post-up state: `/readyz` through the ALB returns 200; and the job logs the measured start time
