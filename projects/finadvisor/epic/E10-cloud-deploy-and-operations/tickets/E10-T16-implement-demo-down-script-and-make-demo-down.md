---
key: "E10-T16"
title: "Implement demo-down script and make demo-down"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T6", "E10-T8", "E10-T9", "E10-T12", "E1-T12", "E5-T13"]
arch_refs: ["deep-dive/04-1-key-flows.md#4.14 Flow 6", "deep-dive/06-interfaces-and-contracts.md#6.6 OUTBOX_DRAIN_TIMEOUT_MIN, VALKEY_INSTANCE_NAME", "ADR-020"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Stop the demo in the exact documented order with a 10-minute outbox drain and forced remainder log.

## Description
Flow 6 and ADR-020 down order: (1) pause Scheduler triggers except hourly demo-ttl, (2) drain: wait for outbox empty and consumer lag 0 with `OUTBOX_DRAIN_TIMEOUT_MIN` = 10 then force (remaining outbox rows are logged and delivered on the next demo-up), (3) worker pool to 0, (4) fa-gateway and chat-api min instances 0, (5) delete the Valkey instance named `VALKEY_INSTANCE_NAME` (outside Terraform state), (6) Cloud SQL activation policy NEVER. The ALB, Cloud Armor, Confluent cluster and storage stay.

Build scripts/demo/demo_down.py (typed Python, shared helpers in scripts/demo/common.py with a thin wrapper around gcloud/Google client libraries and a dry-run mode) and `make demo-down`. The outbox count is read from Postgres via a read-only query run in the VPC by the demo-ttl/ `fa_maint` job path or by a small `demo-down` execution mode of the demo-ttl job image (the script must not need direct DB access from the laptop since Cloud SQL is private); consumer lag is read from Confluent API/consumer-group lag (use the credentials of the E5-T13 admin key held in Secret Manager). Each step is logged with timestamp and is idempotent (rerun after a partial failure continues). Exit non-zero if any step fails; steps never run out of order. After the timeout, log the number of remaining outbox rows and proceed.

Out of scope: demo-up (E10-T18); demo-ttl job (E10-T19).

## Acceptance criteria
- [ ] Unit test with fake clients: the recorded call order is exactly pause-scheduler, drain, worker=0, min=0, delete-valkey, sql=NEVER; an out-of-order call fails the test
- [ ] Unit test: with an outbox that never empties and a fake clock, the script waits 10 minutes (OUTBOX_DRAIN_TIMEOUT_MIN), logs 'forced remainder: N outbox rows', then continues with the remaining steps
- [ ] Unit test: if the Valkey instance is already absent, the step succeeds (idempotent) and the script continues
- [ ] On the real project `make demo-down` ends with `gcloud sql instances describe` activation policy NEVER, worker pool count 0, API and Kong min 0, Memorystore instance not found, and Scheduler jobs paused except demo-ttl; output attached
- [ ] `terraform plan -detailed-exitcode` returns 0 after demo-down
