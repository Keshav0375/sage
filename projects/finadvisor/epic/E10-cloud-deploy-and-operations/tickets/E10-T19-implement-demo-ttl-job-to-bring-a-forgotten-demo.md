---
key: "E10-T19"
title: "Implement demo-ttl job to bring a forgotten demo down"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T10", "E10-T16", "E10-T18", "E1-T12"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/04-components-and-responsibilities.md#4.14 Flow 6", "deep-dive/06-interfaces-and-contracts.md#6.6 DEMO_TTL_HOURS", "ADR-020"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Add the hourly demo-ttl job that runs demo-down when the demo has been up longer than DEMO_TTL_HOURS.

## Description
4.8: `demo-ttl`, role `fa_maint`: 'Hourly safety net: reads the outbox count and runs demo-down if the demo has been up longer than DEMO_TTL_HOURS (Cloud Run admin SA rights)'. ADR-020: 'An hourly demo-ttl job auto-downs the demo as a safety net.' The job must run the same logic as scripts/demo/demo_down.py (E10-T16), so package the demo scripts into the image under the jobs entrypoint rather than duplicating them.

Build jobs subcommand `demo-ttl`: determine 'up since' from the Cloud SQL activation transition (the time of the last operation START/patch ALWAYS from the Cloud SQL operations API) and from a label `demo_up_at` that demo-up sets on the Cloud SQL instance (add the label write to demo_up.py as part of this ticket's PR); if Cloud SQL is stopped do nothing (exit 0, log 'already down'); if now - up_since > DEMO_TTL_HOURS, read the outbox count (query as fa_maint, count of rows with published_at is null) and call the demo-down routine with the 10-minute drain; log the outbox count read. Value of DEMO_TTL_HOURS is set by this ticket via the Terraform variable default (4; see questions).

Out of scope: changing the drain order.

## Acceptance criteria
- [ ] Unit test with fake clients: up for 5 h and DEMO_TTL_HOURS=4 -> demo-down routine called once; up for 1 h -> not called; stopped instance -> not called and exit 0
- [ ] Integration test against a Postgres container: the outbox count query runs as fa_maint and returns the number of unpublished rows seeded (3)
- [ ] On the real project, after demo-up and temporarily setting DEMO_TTL_HOURS=0, `gcloud scheduler jobs run demo-ttl` results in Cloud SQL activation policy NEVER within 15 minutes (drain included); output attached
- [ ] The job fails the check if its SA has roles/owner or roles/editor (E10-T10 IAM test still passes)
