---
key: "E10-T18"
title: "Implement demo-up script, Valkey lifecycle and make demo-up"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T1", "E10-T2", "E10-T16", "E10-T17", "E10-T25", "E12-T7"]
arch_refs: ["deep-dive/04-1-key-flows.md#4.14", "deep-dive/04-components-and-responsibilities.md#4.6", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.14", "deep-dive/06-interfaces-and-contracts.md#6.6", "decision-logs.md#adr-020", "decision-logs.md#adr-024", "decision-logs.md#adr-029", "decision-logs.md#adr-039"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 239, "id": 6263651640, "url": "https://github.com/Keshav0375/FinAdvisor/issues/239"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Start the demo with the erasure job first, then the reverse of the down order, create Valkey, redeploy Kong with its endpoint and print the measured start time.

## Description
Flow 5 and ADR-020 (up is exactly the reverse of down, D16.13), with the round-4 rule of ADR-029 and 5.14: "in demo-on-demand the erasure job runs first at every start", and ADR-039 (a firm tenant's `erasure-worker` pulls FCA purges, so a stopped tenant catches up at its next run). Order:
1. Cloud SQL activation policy ALWAYS and wait RUNNABLE (record elapsed seconds; wait timeout from docs/adr/cloud-sql-start-time.md of E10-T1).
2. Run the erasure job (the Cloud Run job of E10-T25 that runs one pass of the `erasure-worker` code, E12-T7, for every tenant) and wait for it to exit. A non-zero exit stops `demo-up` here: no traffic path, Valkey, gateway revision, worker or Scheduler trigger has been touched yet. A store that is down is NOT an error exit (E12-T7: that step stays `pending`), so the script logs the count of requests still pending and continues.
3. Create the Memorystore Valkey instance (shared-core-nano, fixed name from `VALKEY_INSTANCE_NAME`, in the E2 VPC, outside Terraform state; 4.6).
4. Deploy a new fa-gateway (Kong) revision with the Valkey endpoint in an environment variable and raise chat-api and fa-gateway min instances (fa-gateway max 2 per 7.2).
5. Worker pool manual instance count up (command from E10-T2).
6. Resume Scheduler triggers.
7. Run `maintenance` then `demo-prewarm` jobs (inside the VPC) and wait for success.
8. Print the URL and the measured Cloud SQL start time.
Remaining outbox rows from a forced down are delivered by the relay automatically after step 5; log the count at start. The canary drill and the retirement preflight are added between steps 7 and 8 by E10-T27.

Build scripts/demo/demo_up.py reusing scripts/demo/common.py (E10-T16) and `make demo-up`. Which env var name Kong reads for the Valkey endpoint comes from the E2 Kong config (check kong/ and the E2 fa-gateway module; if not defined, add to questions). Idempotent and rerunnable; the Valkey step succeeds if the instance already exists and is READY; rerunning step 2 is safe because the erasure job is idempotent per request.

Out of scope: demo-prewarm job code (E10-T17), demo-ttl (E10-T19), the erasure job code (E12-T7), the canary (E10-T27).

## Acceptance criteria
- [ ] Unit test with fake clients: the call order is exactly sql=ALWAYS, erasure job run and wait, valkey create, gateway revision with the Valkey endpoint env, min instances up, worker up, scheduler resume, run maintenance, run demo-prewarm; a reversed or reordered call fails the test (the erasure job after valkey create fails it)
- [ ] Unit test: when the erasure job fake exits non-zero, the script exits non-zero and records no call to valkey create, gateway, worker or scheduler (test `test_demo_up.py::test_erasure_failure_stops_before_traffic`)
- [ ] Unit test: when the erasure job exits zero but reports 2 pending requests (a store down), the script logs `erasure pending: 2` and continues
- [ ] Unit test: the script exits non-zero and skips the later steps if Cloud SQL is not RUNNABLE within the timeout
- [ ] On the real project after `make demo-down` then `make demo-up`: `/readyz` through the ALB returns 200 and the script's last output line contains `cloud_sql_start_seconds=<number>`; the execution list shows an erasure job execution that finished before the first fa-gateway revision of the run was created; output attached
- [ ] The Kong revision created by demo-up has the Valkey host in its env (`gcloud run services describe fa-gateway` shows it) and a request burst over RATE_LIMIT_CHAT_PER_MIN gets 429 (counter stored in Valkey)
- [ ] `terraform plan -detailed-exitcode` returns 0 after demo-up
