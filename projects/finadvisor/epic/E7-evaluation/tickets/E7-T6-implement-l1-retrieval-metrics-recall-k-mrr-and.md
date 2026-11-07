---
key: "E7-T6"
title: "Implement L1 retrieval metrics: recall@k, MRR and nDCG"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E3-T16", "E7-T5"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "ADR-008", "ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Compute retrieval quality metrics for a retrieval configuration over the golden set.

## Description
In `backend/src/evals/l1.py` (or the repo's existing eval package location) compute recall@k (k in 5, 10, 15), MRR and nDCG@10 per case and aggregate, calling the production `RetrievalService.search` path under the `fa_eval` role and the `eval` tenant so RLS applies exactly as in chat. Accept a config object {mode: dense|fts|hybrid|hybrid_rerank, rerank_candidates, contextual_headers: bool}, which sets the corresponding settings for the run only (RRF_K 60, HNSW settings from config). Record p50/p95 latency of the first stage and of rerank per config. Only answerable cases with expected chunk ids are scored. Output JSON per config. Quote ADR-008: "RRF k = 60 in one SQL statement with RLS on both legs" and ADR-017 L1. Out of scope: choosing the winning config (E7-T7).

## Acceptance criteria
- [ ] Unit test with a fake retriever and hand-built ranked lists asserts recall@5, MRR and nDCG@10 equal hand-computed values to 4 decimals.
- [ ] Integration test (real pgvector in CI) runs mode=dense and mode=hybrid on 5 seeded cases and returns metrics with latency fields non-null.
- [ ] Test asserts the L1 run opens its connection as fa_eval and that a query using a foreign tenant id returns zero results.
