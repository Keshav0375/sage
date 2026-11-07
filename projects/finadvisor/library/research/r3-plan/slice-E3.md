# Slice E3

## Epic section (from arch/plan.md)

### E3 Retrieval v2

- **Goal.** Filtered, hybrid, reranked retrieval that is fast, fail-closed and measured.
- **Scope.**
  - `voyage-4` embeddings with `input_type` query / document, `halfvec(1024)`, HNSW (m 16, ef_construction 64) + iterative scan, `max_scan_tuples` 20000, `ef_search` ~80-100.
  - FTS leg (`tsvector` + GIN, `websearch_to_tsquery`), RRF k=60 in one SQL statement with RLS on both legs.
  - `rerank-2.5-lite` with timeout; `RERANK_CANDIDATES` default 15 (range 10-30); a timeout or 429 falls back to RRF order and yields `retrieval_degraded` plus counters; CRAG-style confidence gate; parent expansion; server-side staleness.
  - The factsheet and suitability tools reimplemented on `RetrievalService` (no `raw_content`, escaped input, `LIMIT`).
  - Answer cache (UNLOGGED, own RLS, versioned key, verifier re-run on hit, side-effect turns excluded, purge by the applier and `maintenance`); `RetrievalService(principal)` as the only content-table accessor (import-linter + test); retrieval metrics.
- **Arch sections.** overview.md#5.5 to #5.7, overview.md#4.5 (`retrieval`), overview.md#6.3; ADR-004, ADR-008, ADR-015.
- **Dependencies.** E1.
- **Spikes first.** Rerank latency and TPM / tier (target rerank p95 < 700 ms; ~5 QPS on Tier 1); pgvector iterative scan with RLS and LIST partitions (result confirms D13b).
- **Done when.**
  - On a 10k-chunk synthetic corpus, retrieval first stage (embed + SQL) p95 < 300 ms and rerank p95 < 700 ms are measured against overview §2.1 (fail if above, or the ablation drops rerank and the ADR says why).
  - Queries return the requested number of rows under RLS (no short results) in a test using a restrictive tier / jurisdiction.
  - Import-linter fails when a non-`retrieval` module imports a content-table accessor; `fa_app` has no INSERT / UPDATE / DELETE on content tables (test).
  - Answer-cache tests: key changes with `acl_version`, `corpus_version`, entitlement version; a hit that fails the verifier is a miss; a turn that called `escalate_to_compliance` is never cached.
  - Rerank timeout and 429 increment `rerank_fallback_total{reason}` and set `retrieval_degraded`.
  - Fixes G-33, G-34, G-35, G-36 (single provider accepted), G-52.

## Arch files to read (paths; read only the named subsections)

- context/projects/finadvisor/arch/overview/04-components-and-responsibilities.md  (sections: 4.5)
- context/projects/finadvisor/arch/overview/05-data-model-and-storage.md  (sections: 5.5)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md  (sections: 6.3)
- context/projects/finadvisor/arch/stack.md (versions)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md §6.6 (config keys), only the keys this epic uses

## ADRs (context/projects/finadvisor/arch/decisions.md; line of heading)

- line 435: ADR-004: Single retrieval enforcement point
- line 348: ADR-008: Hybrid retrieval, rerank, confidence gate and chunking
- line 198: ADR-015: Exact-match answer cache
