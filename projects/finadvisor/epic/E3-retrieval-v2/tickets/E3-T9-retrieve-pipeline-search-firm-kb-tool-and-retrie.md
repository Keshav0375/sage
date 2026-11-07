---
key: "E3-T9"
title: "retrieve pipeline (as_of), search_firm_kb tool and metrics"
epic: "E3"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E3-T3", "E3-T6", "E3-T7", "E3-T8"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.3", "deep-dive/09-observability.md#9", "decision-logs.md#adr-008", "decision-logs.md#adr-004", "decision-logs.md#adr-027"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 69, "id": 6155652140, "url": "https://github.com/Keshav0375/FinAdvisor/issues/69"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Wire embed, hybrid search, rerank, gate and parent expansion into one retrieve call, rebuild search_firm_kb on it, and emit the retrieval metrics.

## Description
Add `RetrievalService.retrieve(query_text, as_of, top_k=None) -> RetrievalResult` in `backend/src/retrieval/service.py` and rebuild `backend/src/agent/tools/search_kb.py` on it.

Pipeline order (§4.14 flow and §4.5): embed (`embed_query`, E3-T3) -> `search` (E3-T5, `limit=RERANK_CANDIDATES`) -> `rerank` (E3-T6) -> `gate` (E3-T7) -> `expand_parents` (E3-T8). `RetrievalResult` carries: ordered results, `gate: GateResult`, `degraded: bool`, `degraded_reason`, `total_found`, `today`. Gate failure returns the result with no expanded text (the orchestrator issues the refusal; E4).

Tool contract (§6.3): `search_firm_kb`, input `query: string`, `top_k?: int` (lower and upper bound enforced; arch gives no numbers: use named constants 1 and 10 until decided, see questions), output `{results:[{n, chunk_id, source_title, regulatory_ref, last_reviewed_at, stale, text}], total_found, today}` via `model_dump_json()`; "arguments validated by Pydantic models; errors are `{"error_code"}` without exception text"; the tool accepts no tenant, tier or jurisdiction argument and unknown extra arguments are rejected (Pydantic `extra='forbid'`).

Metrics and spans (deep-dive/09-observability.md §9): histograms `retrieval_first_stage_ms` (embed + SQL) and `rerank_ms`; counters `rerank_fallback_total{reason}`, `rerank_429_total`, `gate_refusals_total`; gauge/ratio `retrieval_degraded_ratio` derived from degraded vs total retrievals; spans `embed.query`, `retrieval.hybrid_sql`, `retrieval.rerank`, `retrieval.gate`. No query text, tenant text or chunk text in attributes (chunk ids and scores only, for the Langfuse retrieval span).

Out of scope: the orchestrator calling retrieve first and emitting SSE `meta` / `refusal` (E4), the alert rule (E8).

Round 4 (ADR-027): `retrieve` takes `as_of` from its caller (the orchestrator gets it from the resolver, E4-T18) and passes it to `search` and `expand_parents`; `RetrievalResult` carries the `as_of` used so the answer can echo it. The `search_firm_kb` tool still takes no `as_of` argument from the model: the orchestrator binds it.

## Acceptance criteria
- [ ] Given stubs for Voyage embed and rerank and the synthetic corpus when `retrieve('What is the suitability rule for structured notes?')` runs then results are <= `RERANK_TOP_N`, each has `stale` as a bool, and `today` equals the injected clock date (test `backend/tests/test_retrieve_pipeline.py::test_pipeline_shape`, `integration`).
- [ ] Given the gate fails when `retrieve` runs then the returned results list is empty, `gate.passed=False` and the expand_parents method was not called (test `test_gate_failure_skips_expansion`).
- [ ] Given the tool is called with `{'query':'x','tenant_id':'t1'}` or `top_k=0` or `top_k=1000` then it returns `{"error_code": ...}` with no exception text (test `backend/tests/test_search_kb.py::test_tool_rejects_extra_and_bad_top_k`).
- [ ] After one successful and one rerank-timeout retrieve the metrics reader shows `retrieval_first_stage_ms` count 2, `rerank_ms` count 2, `rerank_fallback_total{reason='rerank_timeout'}` = 1 (test `test_retrieval_metrics_emitted`).
- [ ] The span exporter test shows spans named `embed.query`, `retrieval.hybrid_sql`, `retrieval.rerank`, `retrieval.gate` with no attribute value equal to the query string (test `test_spans_have_no_query_text`).
- [ ] Given `retrieve(q, as_of=2020-06-01)` on the versioned fixture, then every returned chunk's `valid_range` contains that date and `RetrievalResult.as_of` equals it (`test_retrieve_pipeline.py::test_as_of_propagates`); given the tool called with an `as_of` argument, then it is rejected by `extra='forbid'`.
