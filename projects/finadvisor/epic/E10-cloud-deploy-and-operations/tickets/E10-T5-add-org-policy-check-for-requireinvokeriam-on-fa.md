---
key: "E10-T5"
title: "Add org policy check for requireInvokerIam on fa-gateway"
epic: "E10"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E10-T4"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.3", "ADR-012"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Verify the org policy allows the invoker-check exception on fa-gateway only, and fail loudly if not.

## Description
8.3: `fa-gateway`: 'invoker check disabled (the only service where it is) ... E10 checks the org policy constraints/run.managed.requireInvokerIam.' ADR-012: 'the invoker-check exception on fa-gateway depends on the org policy allowing it (checked in E10)'.

Build scripts/check_org_policy.sh: runs `gcloud org-policies describe run.managed.requireInvokerIam --project=$PROJECT --effective` (and the folder/org if the project has none), parses the effective policy, and exits non-zero with a message that says which scope enforces it if enforcement is TRUE for the project. Add it as a pre-apply step in the Terraform apply workflow (E10-T15) and as a precondition `check` block or documented make target `make check-org-policy`.
If the project is not in an organization (no policy possible) the script reports 'no org policy; invoker check can be disabled' and exits 0.

Out of scope: changing the org policy; if enforced, record it in questions of the PR and stop.

## Acceptance criteria
- [ ] With a stubbed gcloud returning enforce: true, `scripts/check_org_policy.sh` exits 1 and prints the scope (unit test in tests/scripts or bats)
- [ ] With a stubbed gcloud returning enforce: false or a not-found for a project without an organization, it exits 0 (unit test)
- [ ] `make check-org-policy` against the real project exits 0, output attached to the PR
