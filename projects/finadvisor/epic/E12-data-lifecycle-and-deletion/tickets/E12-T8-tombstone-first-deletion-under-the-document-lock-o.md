---
key: "E12-T8"
title: "Tombstone-first deletion under the document lock; operator release"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T7", "E6-T10", "E5-T15"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.17", "deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "decision-logs.md#adr-28", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.11"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 312, "id": 6263810603, "url": "https://github.com/Keshav0375/FinAdvisor/issues/312"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Write the tombstone before any delete under the per-document advisory lock and add the operator release action.

## Description
Uses the `erasure_ledger` table created in E12-T5 (key `(tenant_id, doc_key, sha256)`, salted hash, append-only), E11 `documents`, and E5-T15 (uncached ledger read). Implement `erase_document(tenant_id, doc_id)`: ONE document per transaction, `pg_advisory_xact_lock(hash(tenant_id, doc_id))` first, insert the ledger row (salted hash of `doc_key` using the Secret Manager salt, `request_id`, `scope_type`, `requested_at`) before any delete, bump the tenant `corpus_version` row LAST, retry with jitter on lock or serialization failure (same order as the indexer, 4.17). A multi-document request is a series of single-document transactions. Implement the operator command `fa-ops erasure release --tenant T --doc-key K [--sha256 H]` that sets `released_at` and `released_by` on the ledger row, run with a dedicated role that has UPDATE on those two columns only (5.13); no DELETE for anyone. The E5 sink-guard helper already does the uncached read; this ticket adds a test that a released key passes them. Legal hold: a document or record with `retention_class` set is not deleted, and the step records `retained: legal basis X` for the receipt (4.19 and ADR-029 legal hold). Out of scope: store steps, the E5-T15 helper.

## Acceptance criteria
- [ ] Given an indexer holding the lock for a document and an erasure arriving, when both run (N=200 interleavings with a seeded scheduler), then the end state has zero chunk rows and either outcome of ADR-028 holds (indexer first then erasure deletes, or erasure first and indexer writes nothing) (#1; race harness).
- [ ] Given two concurrent multi-document erasures over overlapping documents plus an ingest storm, when they run, then no transaction is lost to a deadlock and every lock is taken in order advisory then `corpus_version` last (#29; log of lock acquisition order asserted).
- [ ] Given a tombstone for `(A, k, h)`, when a sink guard for tenant B and the same key runs, then it passes (tenant-scoped, #4 variant); for tenant A it refuses until `release` is run, after which a re-ingest passes (#30).
- [ ] Given the release role, when it tries UPDATE of any ledger column other than `released_at` and `released_by`, or any DELETE, then permission is denied.
- [ ] Given a record with `retention_class` set, when the erasure runs, then it is not deleted and the step result carries `retained: legal basis <class>`.
