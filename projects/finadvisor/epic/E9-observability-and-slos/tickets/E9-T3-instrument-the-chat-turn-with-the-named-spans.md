---
key: "E9-T3"
title: "Instrument the chat turn with the named spans"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T2", "E4-T19"]
arch_refs: ["deep-dive/09-observability.md#9.1", "ADR-018"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
The chat turn emits chat.turn and its child spans with the 9.1 names and only non-sensitive attributes.

## Description
Implements the span-name list of deep-dive/09-observability.md §9.1: chat.turn, auth.verify, principal.load, guard.input, guard.model_armor, embed.query, retrieval.hybrid_sql, retrieval.rerank, retrieval.gate, llm.stream, guard.output, persist.turn.
Add backend/src/observability/spans.py: constants for the names above and a helper span(name, **attrs) that rejects (raises in tests, drops in prod) attributes outside an allowlist (tenant_id, turn_id, model, token counts, chunk_count, degraded, gate_result, cache_hit, error_code). Wrap the existing call sites in auth, principal, guardrails, retrieval, llm, agent and persistence code in the matching span. chat.turn is the parent; llm.stream carries model, input/output/cache-read token counts; retrieval.gate carries gate_result. Spans must not carry query text, prompts, chunk text or SQL parameters.
Out of scope: changing the behaviour of those stages; Langfuse generations (E0-T8); worker spans (E9-T4).

## Acceptance criteria
- [ ] Given one stubbed POST /v1/chat that is answered, When spans are collected with an in-memory exporter, Then all twelve span names exist, share one trace_id, and every one except chat.turn has a parent in the trace (pytest test_turn_spans.py).
- [ ] Given a refusal turn (gate refuses), When collected, Then retrieval.gate has gate_result='refused' and no llm.stream span exists.
- [ ] Given span('x', query='abc'), When run under pytest, Then it raises ValueError; with ENV_PROFILE=prod it drops the attribute and the exported span lacks it.
- [ ] Given the turn, When exported, Then llm.stream has integer attributes for input, output and cache-read tokens.
