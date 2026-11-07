---
key: "E10-T22"
title: "Add prod profile (HA flag, min instances) and plan test"
epic: "E10"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E10-T6", "E10-T8", "E10-T9", "E10-T16"]
arch_refs: ["deep-dive/07-scaling-failure-modes-and-recovery.md#7.2", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.3", "deep-dive/06-interfaces-and-contracts.md#6.6 ENV_PROFILE", "ADR-020"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 244, "id": 6263661903, "url": "https://github.com/Keshav0375/FinAdvisor/issues/244"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Make the prod profile switch Cloud SQL to HA and set min instances >= 1 through env_profile.

## Description
7.2: 'Always-on availability required: Switch to the prod profile: HA Cloud SQL flag, min instances >= 1 (~300+ USD/month)'; 6.6 ENV_PROFILE selects 'HA flag, min instances'; ADR-020: 'HA is a Terraform flag for load tests'; the 99.5% SLO applies to the prod profile only. 7.3: backups, PITR and RPO/RTO 'are set in E10 when the prod profile is built' but the arch gives no values (see questions; implement only the toggle for backup_configuration.enabled and point_in_time_recovery_enabled as variables defaulting to enabled in prod, no RPO/RTO claims).

Build: env_profile = prod sets Cloud SQL availability_type REGIONAL (already wired in E10-T6), chat-api and fa-gateway min_instance_count >= 1 (variable default 1) and worker pool count >= 1; demo_down.py and demo_up.py refuse to run when ENV_PROFILE=prod unless `--force-prod` is passed (prod must not be stopped by accident); demo-ttl is not created in prod (count = 0). Provide an example terraform/envs/prod.tfvars and docs/runbook-profiles.md with the cost note (~300+ USD).

Out of scope: running prod; the load test (E10-T23).

## Acceptance criteria
- [ ] Terraform test: env_profile=prod plan shows REGIONAL availability, min_instance_count >= 1 for chat-api and fa-gateway, and no demo-ttl job/scheduler; env_profile=demo shows ZONAL, min 0, demo-ttl present
- [ ] Unit test: `demo_down.py` with ENV_PROFILE=prod exits non-zero with a message and makes no client calls; with --force-prod it proceeds
- [ ] In prod profile the `ignore_changes` does not hide min_instance_count drift of 0 (documented decision; checked: test asserts the plan for prod uses a separate resource or variable path or the runbook states how prod min instances are managed)
