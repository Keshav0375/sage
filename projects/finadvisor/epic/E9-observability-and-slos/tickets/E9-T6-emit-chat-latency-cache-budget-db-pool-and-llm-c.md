---
key: "E9-T6"
title: "Emit chat latency, cache, budget, DB pool and LLM cost metrics"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T5", "E4-T18", "E4-T19"]
arch_refs: ["deep-dive/09-observability.md#9.2"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 226, "id": 6263629830, "url": "https://github.com/Keshav0375/FinAdvisor/issues/226"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The chat path emits the 9.2 metrics no other epic owns: TTFT, total latency, cache ratio, tenant budget rejections and connection use.

## Description
Implements the 9.2 rows for chat_ttft_ms, chat_total_ms, answer_cache_hit_ratio, tenant_budget_rejections_total{tenant} and db_connections_in_use. Retrieval metrics are emitted by E3-T9, guard and LLM metrics (guard_blocks_total, llm_fallback_total, llm_breaker_state, gate_refusals_total) by E4, acl_apply_lag_s by E5; do not touch those.
Using metrics.record (E9-T5): in the chat orchestrator record chat_ttft_ms at the first delta event and chat_total_ms at done (also on errors, with the elapsed time); record answer_cache_hit_ratio as a rolling ratio gauge over the last N turns (window config constant, default 100); record tenant_budget_rejections_total when TENANT_BUDGET_EXCEEDED is returned; sample db_connections_in_use from the asyncpg pool every 15 s in a background task (pool size is DB_POOL_SIZE; budget is 300 connections overall, 9.2).
If E4 already emits any of these names, keep one emitter and delete the duplicate (check with grep before coding).
Also emit llm_cost_usd_total{provider,model} (R73): cost = input/output/cache-read/cache-write token counts from each Anthropic call (and Voyage embed/rerank usage) multiplied by a price table in config (new Settings key LLM_PRICE_TABLE_JSON, a mapping provider/model to USD per million tokens by token kind; a missing model logs a warning and records 0 with a label-free counter llm_cost_unpriced). Recorded in the llm client after each call; no payloads.

## Acceptance criteria
- [ ] Given a stubbed turn with the first delta after 1.2 s and done after 3.0 s using a fake clock, When it completes, Then chat_ttft_ms=1200 and chat_total_ms=3000 are recorded exactly once each (pytest test_chat_metrics.py).
- [ ] Given 3 cache hits and 1 miss, When answer_cache_hit_ratio is read, Then it is 0.75.
- [ ] Given a tenant over its budget, When POST /v1/chat is called, Then the response error code is TENANT_BUDGET_EXCEEDED and tenant_budget_rejections_total{tenant} increments by 1.
- [ ] Given a pool with 4 connections acquired, When the sampler runs, Then db_connections_in_use=4. A grep test asserts each of these five names is recorded in exactly one module.
- [ ] Given a stubbed call with 1000 input and 500 output tokens on a model priced at $3 and $15 per million, When completed, Then llm_cost_usd_total{provider='anthropic',model=<m>} increases by 0.0105 (pytest test_llm_cost.py).
- [ ] Given a model absent from LLM_PRICE_TABLE_JSON, When called, Then no exception is raised and llm_cost_unpriced increments by 1.
