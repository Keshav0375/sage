---
key: "E12-T7"
title: "erasure-worker role: poll, claim and request state machine"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T5", "E5-T9"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "decision-logs.md#adr-29", "deep-dive/06-interfaces-and-contracts.md#6.9", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#7"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Poll deletion_requests with FOR UPDATE SKIP LOCKED and drive each request through its status lifecycle.

## Description
Add the `erasure-worker` role to the E5-T9 `WORKER_ROLES` dispatch (role `fa_worker`, per tenant, never PUBLIC firm cross-writes). Loop: in a transaction with `app.tenant_id` set, claim one `pending` row (`SELECT ... FOR UPDATE SKIP LOCKED`), set `running`, `claimed_at`, `attempts + 1`, then call a `StoreStep` interface (one implementation per store, added by later tickets: `postgres`, `gcs`, `bigquery`, `kafka`, `langfuse`, `cache`) and write one `erasure_steps` row per store. Status moves `pending -> running -> executed` when every store step is done or waiting on a window, `windows_open` while windows run, `closed` after phase 2, `failed` after `ERASURE_MAX_ATTEMPTS` (default 5, add to deep-dive/06 6.6 only if the arch lacks it: ask) with backoff. A step that cannot run (a store is down) stays `pending` and the worker continues with other stores and requests; it must not fail the whole request. Emit `erasure_oldest_pending_age_s` as an OTel gauge via the E9 metrics module. No Kafka client on this code path (R4-D6). Out of scope: the store implementations, receipts, the ledger.

## Acceptance criteria
- [ ] Given two worker instances and 50 pending rows, when both run, then every row is claimed exactly once (SKIP LOCKED integration test counting `claimed_at` writes).
- [ ] Given a store step that raises, when the worker runs, then the other stores' steps still complete, the failed one is `pending` with `attempts` incremented, and the request is not `failed` before the cap.
- [ ] Given a request executed with every step done, then its status is `executed` or `windows_open` and never `closed` without phase 2.
- [ ] Given a row pending for 5 h, then `erasure_oldest_pending_age_s` reads at least 18000 (in-memory metric reader).
- [ ] The module imports no Kafka package (import-lint test), proving no Kafka on the delete path.
