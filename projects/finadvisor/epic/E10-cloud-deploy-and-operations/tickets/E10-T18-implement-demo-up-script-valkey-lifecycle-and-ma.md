---
key: "E10-T18"
title: "Implement demo-up script, Valkey lifecycle and make demo-up"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T1", "E10-T2", "E10-T16", "E10-T17"]
arch_refs: ["deep-dive/04-1-key-flows.md#4.14 Flow 5", "deep-dive/04-components-and-responsibilities.md#4.6", "deep-dive/06-interfaces-and-contracts.md#6.6 VALKEY_INSTANCE_NAME", "ADR-020", "ADR-024"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Start the demo in the exact reverse order, create Valkey, redeploy Kong with its endpoint and print the measured start time.

## Description
Flow 5 and ADR-020 (up is exactly the reverse, D16.13): (1) Cloud SQL activation policy ALWAYS and wait RUNNABLE (record elapsed seconds; wait timeout from docs/adr/cloud-sql-start-time.md of E10-T1), (2) create the Memorystore Valkey instance (shared-core-nano, fixed name from `VALKEY_INSTANCE_NAME`, in the E2 VPC, outside Terraform state; 4.6), (3) deploy a new fa-gateway (Kong) revision with the Valkey endpoint in an environment variable and raise chat-api and fa-gateway min instances (fa-gateway max 2 per 7.2), (4) worker pool manual instance count up (command from E10-T2), (5) resume Scheduler triggers, (6) run `maintenance` then `demo-prewarm` jobs (inside the VPC) and wait for success, (7) print the URL and the measured Cloud SQL start time. Remaining outbox rows from a forced down are delivered by the relay automatically after step 4; log the count at start.

Build scripts/demo/demo_up.py reusing scripts/demo/common.py (E10-T16) and `make demo-up`. Which env var name Kong reads for the Valkey endpoint comes from the E2 Kong config (check kong/ and the E2 fa-gateway module; if not defined, add to questions). Idempotent and rerunnable; the Valkey step succeeds if the instance already exists and is READY.

Out of scope: demo-prewarm job code (E10-T17), demo-ttl (E10-T19).

## Acceptance criteria
- [ ] Unit test with fake clients: the call order is exactly sql=ALWAYS, valkey create, gateway revision with the Valkey endpoint env, min instances up, worker up, scheduler resume, run maintenance, run demo-prewarm; a reversed order fails the test
- [ ] Unit test: the script exits non-zero and skips the later steps if Cloud SQL is not RUNNABLE within the timeout
- [ ] On the real project after `make demo-down` then `make demo-up`: `/readyz` through the ALB returns 200 and the script's last output line contains `cloud_sql_start_seconds=<number>`; output attached
- [ ] The Kong revision created by demo-up has the Valkey host in its env (`gcloud run services describe fa-gateway` shows it) and a request burst over RATE_LIMIT_CHAT_PER_MIN gets 429 (counter stored in Valkey)
- [ ] `terraform plan -detailed-exitcode` returns 0 after demo-up
