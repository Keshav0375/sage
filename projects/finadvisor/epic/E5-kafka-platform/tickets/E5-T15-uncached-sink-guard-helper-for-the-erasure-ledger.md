---
key: "E5-T15"
title: "Uncached sink-guard helper for the erasure ledger"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T5", "E5-T7"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/04-2-source-lifecycle-and-cells.md#4.17", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.11", "decision-logs.md#adr-028", "decision-logs.md#adr-029"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 141, "id": 6263492331, "url": "https://github.com/Keshav0375/FinAdvisor/issues/141"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Provide one helper that every sink calls before writing: an uncached point read of erasure_ledger that pauses the sink when it cannot read.

## Description
Implement `events/sink_guard.py` (R4-D20 E12 note; ADR-028). Quote 4.7: 'Write guard in every sink (`silver`, `contextualizer`, `indexer`, `bq-sink`): before writing, an UNCACHED point read of `erasure_ledger` on `(tenant_id, doc_key, sha256)` inside the sink's own transaction or write path; a hit drops the message with a counted reason. There is no 60 s cache on this read'. And ADR-028: 'pauses if it cannot read it'. The `erasure_ledger` table (key `(tenant_id, doc_key, sha256)`, `released_at`, RLS, `fa_worker` SELECT) is created by E12-T5; this ticket adds no table.

Interface: `SinkGuard(conn_factory, salt)` with `check(tenant_id, doc_key, sha256) -> GuardResult(blocked: bool)` and `check_subject(tenant_id, pseudonym_hash)`. `doc_key` is the plain document key; the helper applies the salted hash of 5.11 (salt LEDGER_SALT from Secret Manager, no default) and returns `blocked=True` when a row exists with `released_at IS NULL`; a row with `released_at` set (operator release) does not block. One SELECT per call, `SELECT 1 ... LIMIT 1`, run inside the caller's transaction or a short own transaction as `fa_worker` with `app.tenant_id` set; there is NO cache (no lru_cache, no TTL, no memoised result) and the module is checked for that. If the read raises or exceeds SINK_GUARD_TIMEOUT_MS (default 2000), the helper raises `LedgerUnreadable`; the E5-T7 consumer treats it as 'pause': the partition is paused, the offset is not committed, nothing goes to the DLQ, `sink_guard_paused_total` is incremented, and polling resumes with backoff. A blocked result increments `sink_guard_blocked_total{sink}` and the caller drops the message. Out of scope: wiring each sink (E5-T14, E6-T7, E6-T8, E6-T10, E6-T18), the ledger writes and release (E12).

## Acceptance criteria
- [ ] Given a ledger row for (tenant, doc_key, sha256) with released_at NULL, when `check` is called, then blocked is True; given the same row with released_at set, then blocked is False; given the same doc_key under another tenant, blocked is False (integration test on Postgres).
- [ ] Given a tombstone inserted between two consecutive `check` calls for the same key, when the second call runs immediately after the insert, then it returns blocked True (test_guard_is_uncached; no 60 s window).
- [ ] Given the DB connection raises or the query exceeds SINK_GUARD_TIMEOUT_MS, when `check` is called inside a consumer handler, then `LedgerUnreadable` is raised, the offset is not committed, the partition is paused and no DLQ record is written (test_guard_pauses_on_unreadable).
- [ ] Given the module source, when a grep test runs, then it contains no `lru_cache`, `cache`, TTL dict or module-level result store (test_no_cache_in_sink_guard).
- [ ] Given a call, when the SQL is captured, then it is a single indexed point read on the ledger primary key using the salted `doc_key` and never contains the plain doc_key (test).
