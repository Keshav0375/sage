---
key: "E6-T10"
title: "indexer: atomic per-document publish and lock order"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T8", "E6-T21", "E6-T20", "E3-T4", "E1-T8", "E5-T15", "E11-T5", "E11-T11"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/04-2-source-lifecycle-and-cells.md#4.17", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.10", "deep-dive/04-1-key-flows.md#4.14", "decision-logs.md#adr-028", "decision-logs.md#adr-027"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 143, "id": 6263494403, "url": "https://github.com/Keshav0375/FinAdvisor/issues/143"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Publish one document version atomically under the advisory lock, check the ledger and the gates, and bump corpus_version last.

## Description
Implement the transactional half of the `indexer` role (04 §4.17, ADR-028 amended 2026-11-07, R4-D5). Quote 4.17: 'The indexer is the only writer of `chunks`. It embeds first, outside any transaction (E6-T21), then runs ONE transaction per document: (1) `pg_advisory_xact_lock(hash(tenant_id, doc_id))`; (2) check there is no ledger tombstone for `(tenant_id, doc_key, sha256)` (uncached point read) and that the version has `contract_passed AND scan_passed`; (3) apply the diff; (4) set the version `active`; (5) delete `answer_cache` rows whose `source_document_ids` contain the document; (6) write `processed_events`; (7) bump the tenant's `corpus_version` row last.' 'Lock order for publish and erasure alike: one document per transaction, advisory lock first, tenant `corpus_version` row last, retry with jitter. `pg_advisory_xact_lock` only (safe under pooling).'

Consume `chunks.contextualized.v1` and take the prepared publish plan from E6-T21. Step (2) uses the E5-T15 helper inside the transaction: a hit drops the message with `tombstoned` and writes nothing; an unreadable ledger rolls back and pauses; a version without `contract_passed AND scan_passed` (columns of `document_versions`, E11-T5; set by E11-T11 and E6-T20) writes nothing and is counted `gate_not_passed`. Step (3) for a single version: insert missing rows (E6-T21 supplies vectors), extend `valid_range` where the same chunk hash continues (no embed), close superseded rows (`valid_range` upper and `system_range` upper set, never overwritten), delete extras; multi-version ordering (late, out-of-order, withdrawn) is `reconcile_lineage` in E11-T9, which replaces this diff function. Retry on lock timeout or deadlock with jitter (INDEXER_RETRY_MAX). Emit `chunks.indexed.v1` after commit. Runs as `fa_worker`. A chunk in the table means its version passed every gate. Out of scope: embedding (E6-T21), reconcile_lineage (E11-T9), cache-key logic (E3).

## Acceptance criteria
- [ ] Given a statement log of one publish, when inspected, then the order is advisory lock, ledger read and gate check, chunk writes, version `active`, answer_cache delete, processed_events insert, `UPDATE tenants SET corpus_version` LAST, all in one transaction, and corpus_version rises by exactly 1 per document (test_publish_statement_order).
- [ ] Given a ledger tombstone for the document, or a version with scan_passed=false or contract_passed=false, when published, then zero chunk rows are written, the version is not `active` and corpus_version is unchanged (test_publish_blocked_by_gates).
- [ ] Given a failure injected after the chunk insert and before the corpus_version bump, when the transaction ends, then no chunk row, cache purge or processed_events row persists (atomicity test).
- [ ] Given an erasure transaction and an indexer transaction for the same document started concurrently, when both finish, then either rows exist and the erasure deleted them or the indexer wrote nothing, never rows left behind, and no deadlock occurs over 50 repeated runs (test_indexer_vs_erasure_race).
- [ ] Given `fa_worker` in tenant A context, when it writes a chunk with tenant B id, then RLS denies it; given the same event delivered twice, then the second is a no-op by processed_events.
