---
key: "E10-T17"
title: "Implement demo-prewarm Cloud Run job"
epic: "E10"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E10-T10", "E4-T27"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/04-components-and-responsibilities.md#4.14 Flow 5", "ADR-019"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Add the in-VPC demo-prewarm job code that calls /readyz and warms pools, since it cannot run from the laptop.

## Description
4.8: `demo-prewarm`, DB role none: 'Runs inside the VPC after demo-up: calls /readyz and warms pools and caches (not run from the operator laptop)'. Job entrypoint `jobs` in the one image. Look at the existing jobs entrypoint dispatcher from E1 to add the subcommand `demo-prewarm`.

Build backend/src/.../jobs/demo_prewarm.py: reads the internal chat-api URL, gets an ID token from the metadata server (audience = chat-api URL), polls /readyz up to a configured timeout (default 120 s, interval 5 s), then issues a small number of warm requests to bring connection pools up (use the readiness endpoint repeatedly with the concurrency equal to a fraction of DB_POOL_SIZE; no LLM calls, no data writes). Exit 0 only when /readyz returns 200; exit non-zero with the last response body otherwise. No DB credentials.

Out of scope: demo-up (E10-T18).

## Acceptance criteria
- [ ] Unit test with a fake HTTP server: returns 503 twice then 200 -> job exits 0 after 3 polls; always 503 -> exits non-zero after the timeout (fake clock)
- [ ] Unit test: the job never reads DB_* variables and never calls an endpoint other than /readyz (assert on recorded requests)
- [ ] `gcloud run jobs execute demo-prewarm --wait` after demo-up exits 0 and its logs show the poll count; output attached
