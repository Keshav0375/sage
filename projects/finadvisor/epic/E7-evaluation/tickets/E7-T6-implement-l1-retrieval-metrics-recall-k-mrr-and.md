---
key: "E7-T6"
title: "Implement L1 retrieval metrics: recall@k, MRR and nDCG"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E3-T16", "E7-T5"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/02-quality-attributes.md#2.10", "decision-logs.md#adr-008", "decision-logs.md#adr-017", "decision-logs.md#adr-037"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Compute the tier-1 deterministic metrics (evidence-span recall@10, MRR, gold-version-in-top-5, numeric-in-span, footer present) per case and per cluster for a retrieval configuration.

## Description
In `backend/src/evals/l1.py` (or the repo's existing eval package location) compute, per case and aggregated per cluster, calling the production `RetrievalService.search` path under the `fa_eval` role and the `eval` tenant so RLS applies exactly as in chat:
- evidence-span recall@10 (and @5, @15 for the ablation tables): a hit when a retrieved chunk overlaps a `expected_evidence` quote span of the case (E7-T2) in the same `doc_key` and `version_key`;
- MRR and nDCG@10 over the same span relevance;
- gold-version-in-top-5: the gold `version_key` (an as-of or superseded question) appears among the top 5 chunks' versions;
- numeric-in-span: every figure a case marks as required appears inside a retrieved evidence span (locale-aware compare, as the numeric gate of 8.6 does);
- footer present: for answered cases the SSE stream carried a `footer` event for each cited licence class (06 6.2).
ASR (injection attack success rate) is computed by E7-T26 and reported next to these.

Accept a config object {mode: dense|fts|hybrid|hybrid_rerank, rerank_model: rerank-3-lite|rerank-3, rerank_candidates, contextual: llm|section_path_prefix, embed: plain|voyage_context_4, table_handling: chunks|structured_lookup}, which sets the corresponding settings for the run only (RRF_K 60, HNSW settings from config). Output per-cluster aggregates (never only the pooled mean) so E7-T23 can do cluster-level tests. Record p50/p95 latency of the first stage and of rerank per config. Tier-1 metrics come first: the judge-based L2 metrics (E7-T8) gate only if rho^2 >= 0.4 (ADR-037).

Quote ADR-008: "RRF k = 60 in one SQL statement with RLS on both legs" and ADR-037. Out of scope: choosing the winning config (E7-T7), statistics (E7-T23).

## Acceptance criteria
- [ ] Unit test with a fake retriever and hand-built ranked lists asserts evidence-span recall@10, MRR and nDCG@10 equal hand-computed values to 4 decimals (test `test_l1_metrics.py::test_hand_computed`).
- [ ] Unit test: a case whose gold version is in rank 6 only gives gold-version-in-top-5 = 0, and in rank 5 gives 1 (`test_l1_metrics.py::test_gold_version_boundary`).
- [ ] Unit test: output groups results by `cluster_id` and the per-cluster means match hand values for 2 clusters of 3 cases (`test_l1_metrics.py::test_cluster_aggregation`).
- [ ] Integration test (real pgvector in CI) runs mode=dense and mode=hybrid on 5 seeded cases and returns metrics with latency fields non-null.
- [ ] Test asserts the L1 run opens its connection as fa_eval and that a query using a foreign tenant id returns zero results.
