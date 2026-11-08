---
key: "E10-T20"
title: "Add security and connection budget invariant checks"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T8", "E10-T9", "E10-T10", "E10-T14"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.3", "deep-dive/08-security-and-privacy.md#8.4", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.2", "deep-dive/06-interfaces-and-contracts.md#6.6", "ADR-012", "ADR-020"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 242, "id": 6263659740, "url": "https://github.com/Keshav0375/FinAdvisor/issues/242"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add a scripted check for no allUsers, invoker exception only on fa-gateway, no public Cloud SQL IP, no secret in state and pool sizes <= 300.

## Description
Epic done-when: 'No allUsers binding on any service; the invoker check is disabled only on fa-gateway; Cloud SQL has no public IP; no secret value in Terraform state; the sum of pool sizes over max instances is <= 300.' Sources: 6.6 DB_POOL_SIZE ('pool per instance x max instances over all services must stay <= 300 of Cloud SQL max_connections 400'), 7.2 connection budget (`max_connections` 400, headroom for migrations, dbt and Dagster; fa-gateway max 2), 8.3, 8.4 (G-27), ADR-012.

Build scripts/check_invariants.py with two modes: `--plan plan.json` (static, from `terraform show -json`) and `--live` (gcloud). Checks: (1) no allUsers/allAuthenticatedUsers in any run service, job, worker pool or bucket policy; (2) invoker check disabled (`invokerIamDisabled`) on fa-gateway only, enabled on every other service; (3) Cloud SQL ipv4_enabled false and no PRIMARY/PUBLIC address; (4) state/plan values: no sensitive attribute from google_secret_manager_secret_version or any value matching a configured secret-name list; (5) budget: sum over services/pools of DB_POOL_SIZE x max_instance_count (chat-api, worker pool count, jobs max parallelism x pool) <= 300, printing the table and failing above. Run in CI (terraform-plan workflow) and by `make check-invariants`.

Out of scope: runtime load.

## Acceptance criteria
- [ ] Unit tests with fixture plan JSON: one with allUsers on chat-api fails (exit 1); one with invokerIamDisabled on chat-api fails; one with ipv4_enabled true fails; clean fixture passes
- [ ] Unit test: DB_POOL_SIZE=10, chat-api max 20, worker 2 x 10 = 220 passes; chat-api max 40 (total 420) fails with the table printed
- [ ] Unit test: a fixture plan containing a google_secret_manager_secret_version with secret_data fails
- [ ] `make check-invariants --live` on the real project exits 0 with the printed budget total <= 300; output attached
- [ ] The terraform-plan workflow runs the check on PRs and fails when a fixture violation is introduced on a test branch
