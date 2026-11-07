---
key: "E3-T5"
title: "RetrievalService.search: hybrid dense + FTS with RRF"
epic: "E3"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E3-T2", "E3-T3", "E3-T4"]
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.5", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.6", "deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#adr-004", "decision-logs.md#adr-008"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 65, "id": 6155647336, "url": "https://github.com/Keshav0375/FinAdvisor/issues/65"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Implement RetrievalService(principal).search as one SQL statement with RLS on both legs and iterative HNSW scan.

## Description
Create `RetrievalService(principal)` in `backend/src/retrieval/service.py` and its `search(query_text, query_vec, limit)` method. This is the first method of the only module allowed to touch content tables (ADR-004: "`RetrievalService(principal)` is the only code that touches content tables; tools never take tenant, tier or jurisdiction arguments"). It opens a short tenant-scoped transaction through the `principal` module's context manager (E1; `set_config(..., true)` settings), never holds it across an LLM call, and returns a list of `Candidate(chunk_id, parent_id, rrf_score)` ordered by RRF.

Quoted arch (deep-dive/05-1-rls-indexes-versioning-and-deletion.md §5.6): "One statement, RLS applied to both legs, RRF with `k = 60` (`RRF_K`)" followed by the statement with CTEs `dense` (`embedding <=> $1::halfvec`, `kind = 'child' AND embedding IS NOT NULL`, `LIMIT $2`), `fts` (`websearch_to_tsquery('simple', $3)`, `tsv @@ q`, `ORDER BY ts_rank(tsv, q) DESC LIMIT $2`) and the `sum(1.0 / (60 + r))` fusion with `LIMIT $4`. "The RLS policy supplies the tenant / PUBLIC / tier / jurisdiction filter to both legs; partition pruning limits the scan to the caller's tenant and PUBLIC partitions." Per transaction: `SET LOCAL hnsw.iterative_scan = relaxed_order`, `hnsw.max_scan_tuples = HNSW_MAX_SCAN_TUPLES` (20000), `hnsw.ef_search = HNSW_EF_SEARCH`. Because `SET LOCAL` takes no bind parameters, set them with `set_config('hnsw.ef_search', $n, true)`.

Rules: use the SQL from §5.6 with `$1` the embedding as a `halfvec`, `$3` the (already PII-redacted) query text, `$4` the final limit (callers pass `RERANK_CANDIDATES`), `RRF_K` from `Settings` (do not hard-code 60 in the SQL string; bind it), `$2` the per-leg limit from the constant fixed by the E3-T2 ADR. No tier / jurisdiction / tenant WHERE clauses in the application SQL: RLS does it. No `raw_content`. Query text and vectors never appear in logs or exception messages. Statement runs under `DB_STATEMENT_TIMEOUT_MS`.

Out of scope: embedding (E3-T3 is called by the pipeline in E3-T9), rerank (E3-T6), gate, parent expansion, answer cache.

## Acceptance criteria
- [ ] Given the 10k-chunk synthetic corpus from E3-T2 and a tier-1 US-only principal when `search(..., limit=15)` runs for 100 queries then every call returns exactly 15 rows (test `backend/tests/test_retrieval_search.py::test_no_short_results_under_restrictive_rls`, marked `integration`).
- [ ] Given tenant A and tenant B each have chunks when a tenant-A principal searches with a vector that is nearest to a tenant-B chunk then no tenant-B chunk id is returned from either leg (test `test_no_cross_tenant_rows_both_legs`); a PUBLIC chunk is returned when it matches.
- [ ] Given a chunk whose content contains the token `FINRA-2111` and whose embedding is far from the query vector when the query text is `FINRA-2111` then that chunk is in the top 5 (FTS leg works; test `test_fts_leg_finds_rule_id`).
- [ ] Given the principal's tier is below a chunk's `tier_required` when the chunk is the exact vector and text match then it is absent from the result (test `test_acl_filtered_by_rls`).
- [ ] `EXPLAIN` of the statement shows a single statement with both CTEs and the `hnsw` index used for the dense leg on a tenant partition, and the SQL text contains no literal `60` (test `test_single_statement_and_rrf_k_bound`).
