---
key: "E12-T9"
title: "Postgres erasure step: ordered DELETE, counts, VACUUM, cache purge"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T8"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.14", "decision-logs.md#adr-29", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#3"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Delete a document's rows in the arch's child-first order in one transaction, record counts, then VACUUM the partitions.

## Description
StoreStep `postgres` for scope `document` and `source`: in the per-document transaction of E12-T8 delete in this order (4.19): `answer_cache` rows whose `source_document_ids` contain the document, `chunks` (every embedding generation: delete by `doc_id`, 4.27), `suitability_rules`, `ingest_rejects`, `document_versions`, `documents`; record `rows_affected` per table in `erasure_steps`. After commit run `VACUUM (ANALYZE)` on the affected tenant partitions of the touched tables (outside the transaction), then a probe `SELECT count(*)` for each table, stored as `probe_result`. Set `window_closes_at` to now + 24 h of system running (the live-store window). No temporal-FK cascade exists, so children are explicit. Tenant B's rows with the same content hash are untouched (tenant-scoped). Out of scope: other stores, advisor scope.

## Acceptance criteria
- [ ] Given a document with 3 versions and 40 chunks, when the step runs, then the probe counts are 0 for every table and `rows_affected` per table equals the pre-run counts.
- [ ] Given the same document content in firm A and firm B, when A's is erased, then B's rows and cached answers are unchanged and B still answers (#4; counts per tenant).
- [ ] Given a cached answer citing the document, when the step runs, then that `answer_cache` row is gone and the same question misses (#3 variant).
- [ ] Given two embedding generations present, when the step runs, then zero chunk rows remain in either (#20 DB part).
- [ ] VACUUM runs after commit (`pg_stat_user_tables.last_vacuum` advances in an integration test) and never inside the delete transaction.
