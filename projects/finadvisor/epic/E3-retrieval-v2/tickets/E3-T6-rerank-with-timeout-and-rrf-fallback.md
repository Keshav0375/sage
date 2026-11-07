---
key: "E3-T6"
title: "Rerank with timeout and RRF fallback"
epic: "E3"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E3-T1", "E3-T5"]
arch_refs: ["decision-logs.md#adr-008", "decision-logs.md#adr-037", "decision-logs.md#adr-039", "deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/06-interfaces-and-contracts.md#6.6"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 66, "id": 6155648528, "url": "https://github.com/Keshav0375/FinAdvisor/issues/66"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add RetrievalService.rerank using Voyage rerank-3-lite that falls back to RRF order and flags the turn degraded on timeout or 429.

## Description
Add `RetrievalService.rerank(query_text, candidates) -> RerankResult` in `backend/src/retrieval/rerank.py`, wired into the service. Inputs: the candidate chunk texts (the child chunk `content` fetched under RLS for the top `RERANK_CANDIDATES` ids; fetch via `fetch_chunks`, E3-T8, or a private helper if T8 is not merged). Output: `RerankResult(items: list[(chunk_id, score)] , degraded: bool, reason: "rerank_timeout" | "rerank_429" | None)`.

Arch (ADR-008): "Voyage `rerank-3-lite` (or `rerank-3`) with timeout; a rerank timeout or 429 falls back to RRF order and marks the turn degraded (SSE `meta {retrieval_degraded: true}` and `messages.retrieval_degraded`), increments `rerank_fallback_total{reason}`, and alerts when > 5% of turns in 15 min are degraded". SSE contract §6.2: `meta {retrieval_degraded: bool, reason?: "rerank_timeout" or "rerank_429"}`. Config §6.6: `RERANK_MODEL`, `RERANK_ENABLED`, `RERANK_TIMEOUT_MS` (value from the E3-T1 ADR), `RERANK_CANDIDATES` (default 15; clamp to range 10-30 at settings validation: a value outside fails boot), `RERANK_TOP_N` (6).

Behaviour: if `RERANK_ENABLED` is false, return the RRF order truncated to `RERANK_TOP_N` with `degraded=False` (a disabled rerank is configuration, not degradation). On timeout (client timeout = `RERANK_TIMEOUT_MS`) or HTTP 429 (exception shapes recorded in the E3-T1 ADR): return the RRF order truncated to `RERANK_TOP_N`, `degraded=True`, and increment `rerank_fallback_total{reason}` (OpenTelemetry counter; `rerank_429_total` additionally on 429). Record `rerank_ms` (histogram) for every call and a span `retrieval.rerank`. Counters carry no tenant text or query content. The module only produces the flag; persisting `messages.retrieval_degraded` and emitting the SSE `meta` event is the orchestrator's job (E4).

Out of scope: the alert policy (E8 observability), other Voyage errors (see questions), the gate (E3-T7).

Round 4 (R4-D18 V1, ADR-037, ADR-008): `RERANK_MODEL` defaults to `rerank-3-lite`; the model id is read from Settings only, so ablation arm 3 (`rerank-3` against `rerank-3-lite`) is switched by configuration with no code change. The timeout value comes from the E3-T1 ADR measured on the default model.

## Acceptance criteria
- [ ] Given a stubbed Voyage rerank that sleeps longer than `RERANK_TIMEOUT_MS` when `rerank` runs then the result has the RRF order, `degraded=True`, `reason='rerank_timeout'`, and the counter `rerank_fallback_total{reason='rerank_timeout'}` increased by 1 (test `backend/tests/test_rerank.py::test_timeout_falls_back`).
- [ ] Given the stub raises the 429 error type recorded in the E3-T1 ADR when `rerank` runs then `degraded=True`, `reason='rerank_429'`, `rerank_fallback_total{reason='rerank_429'}` and `rerank_429_total` each increased by 1 (test `test_429_falls_back`).
- [ ] Given the stub returns scores for 15 candidates when `rerank` runs then the result is ordered by descending rerank score and has `RERANK_TOP_N` (6) items and `degraded=False` (test `test_reorders_and_truncates`).
- [ ] Given `RERANK_CANDIDATES=40` or `5` when Settings loads then boot fails with a validation error naming the 10-30 range (test `test_candidates_range_validated`).
- [ ] Given `RERANK_ENABLED=false` when `rerank` runs then Voyage is not called and `degraded=False` (test `test_disabled_is_not_degraded`).
- [ ] Given `RERANK_MODEL` unset, then Settings returns `rerank-3-lite`; given `RERANK_MODEL=rerank-3`, then the stubbed Voyage client receives `model='rerank-3'` with no other change; `grep -rn "rerank-3" backend/src` matches only the Settings default (`backend/tests/test_rerank.py::test_model_is_config_only`).
