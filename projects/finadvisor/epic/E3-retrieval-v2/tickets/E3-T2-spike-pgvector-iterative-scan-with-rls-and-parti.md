---
key: "E3-T2"
title: "Spike: pgvector iterative scan with RLS and partitions"
epic: "E3"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T21"]
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.5", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.6", "decision-logs.md#adr-008", "decision-logs.md#adr-003"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 62, "id": 6155643890, "url": "https://github.com/Keshav0375/FinAdvisor/issues/62"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Prove that HNSW with iterative scan returns the requested row count under RLS on LIST partitions, and measure first-stage SQL latency on 10k chunks.

## Description
Build the reusable synthetic corpus generator `backend/scripts/synth_corpus.py` and the spike script `backend/scripts/spike_pgvector.py`, and record the result as an ADR `docs/adr/ADR-E3-02-pgvector-iterative-scan-rls.md` (confirms D13b / ADR-003: LIST partitions by `tenant_id`).

Arch being tested (deep-dive/05-1-rls-indexes-versioning-and-deletion.md §5.5): "`chunks`: `PARTITION BY LIST (tenant_id)` ... HNSW on `embedding halfvec_cosine_ops` with `m = 16`, `ef_construction = 64`, partial `WHERE kind = 'child'` ... Query-time settings, per transaction (`SET LOCAL`): `hnsw.iterative_scan = relaxed_order`, `hnsw.max_scan_tuples = 20000`, `hnsw.ef_search` ~80-100 ... Filtering is applied after the ANN scan in pgvector, so iterative scan is mandatory". ADR-008 evidence: "practitioner 52/400 queries returned 0 rows with default HNSW".

Synthetic corpus (deterministic, seed in the file): 10,000 child chunks plus their parents across 3 firm tenants and the PUBLIC tenant (partitions created through the E1 onboarding path), with `tier_required` 1..4 and `jurisdiction` in US/EU/UK distributed so that a restrictive caller (tier 1, jurisdiction US only) can see only about 5-10% of rows. Embeddings are seeded clustered 1024-dim vectors (no Voyage calls for corpus generation); the DB uses the E1 schema and roles, and queries run as `fa_app` with `set_config(..., true)` settings set exactly as the `principal` module does.

Experiments, all as `fa_app` through RLS: (1) default HNSW (no iterative scan) vs `relaxed_order` with `max_scan_tuples` 20000 and `ef_search` 40, 80, 100: fraction of 400 queries returning fewer than `LIMIT` rows, for LIMIT 15 and 30; (2) the hybrid statement of deep-dive/05-1-rls-indexes-versioning-and-deletion.md §5.6 (copy it verbatim) p50/p95/p99 SQL latency over 400 queries per caller profile; (3) `EXPLAIN (ANALYZE)` on a dense query showing partitions removed ("Subplans Removed") under the RLS `current_setting` policy; (4) the same with a `strict_order` comparison for the record.

The ADR states: the chosen `HNSW_EF_SEARCH`, whether `HNSW_MAX_SCAN_TUPLES` 20000 suffices for the restrictive profile, the per-leg `LIMIT` ($2 in §5.6) to use, the measured SQL p95, and a verdict on D13b (LIST partitions keep pruning at this scale).

Out of scope: the app's `RetrievalService` (E3-T5), index DDL in migrations (E3-T4), embeddings from Voyage.

## Acceptance criteria
- [ ] Given the 10k-chunk corpus and a tier-1 US-only caller when 400 queries run with default HNSW settings then the script reports the count with fewer than 15 rows, and with `relaxed_order` + `max_scan_tuples` 20000 + `ef_search` 80 reports 0 queries with fewer than 15 rows (asserted in `backend/tests/test_spike_pgvector.py::test_iterative_scan_fills_limit`, marked `integration`).
- [ ] `EXPLAIN (ANALYZE)` output stored in the ADR shows 'Subplans Removed' > 0 for the dense leg under RLS, and the test `test_partition_pruning_under_rls` asserts the plan text contains it.
- [ ] The ADR contains a table of hybrid-statement SQL latency p50/p95/p99 in ms per caller profile, a chosen `HNSW_EF_SEARCH` (80-100 range or a justified other value), the per-leg LIMIT, and an explicit confirm/reject of D13b.
- [ ] Running `python backend/scripts/synth_corpus.py --chunks 10000 --seed 1` twice produces identical `chunk_hash` sets (test `test_synth_corpus_deterministic`).
