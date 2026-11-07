---
key: "E4-T18"
title: "Orchestrator pre-LLM stages: cache, screen+embed, retrieval, gate"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T9", "E4-T10", "E4-T17", "E4-T13", "E3-T9", "E3-T14"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.2", "decision-logs.md#ADR-007"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Retrieve-first pipeline up to the gate, with the meta event and refusal path.

## Description
src/agent orchestrator order (4.5, Flow 1): guard-in (cap, Presidio) -> condensation (if history) -> answer_cache lookup (E3-T13/T14 store, key from the normalized redacted question; hit re-fetches via fetch_chunks, re-runs the CitationVerifier, a miss on invisible chunk) -> on miss: Model Armor screen in parallel with Voyage embed -> RetrievalService search+rerank+gate (E3) in short transactions -> emit 'meta' {retrieval_degraded, reason?} once after rerank and store messages.retrieval_degraded. Gate failure emits 'refusal' {NO_FIRM_DOCUMENTATION, escalate_offer} then done(finish_reason gate) with no LLM call. Cache hit path emits delta/citation events from the verified cached answer and skips screen and embed. Failures map to one error event with a code (RETRIEVAL_UNAVAILABLE etc). Cache write after a verified, non-escalating turn is in the next ticket's persist step.

## Acceptance criteria
- [ ] Given the gate stub failing, when a turn runs, then events are turn, meta, refusal, done(gate) and the LLM stub is called 0 times.
- [ ] Given the reranker stub returning 429, when run, then meta.retrieval_degraded is true with reason rerank_429 and the stored messages.retrieval_degraded is true (equality test across both).
- [ ] Given a cache hit, when run, then Model Armor and Voyage stubs are called 0 times and chunks are fetched via fetch_chunks.
- [ ] Given a cache hit citing a chunk no longer visible to the principal, then it behaves as a miss.
- [ ] Given Model Armor timeout, the turn ends with error GUARD_UNAVAILABLE and no retrieval SQL.
