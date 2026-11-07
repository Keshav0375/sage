---
key: "E4-T4"
title: "Add E4 settings keys and the stable error-code mapping"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T21"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/06-interfaces-and-contracts.md#6.6"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 96, "id": 6155682537, "url": "https://github.com/Keshav0375/FinAdvisor/issues/96"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Typed Settings for E4 keys and a single error-code to HTTP/SSE mapping with fixed messages.

## Description
Add to the pydantic-settings Settings class (6.6), no secret default, missing required key fails boot: ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, LLM_MODEL_ANSWER, LLM_MODEL_AUX, LLM_MODEL_FALLBACK, LLM_FALLBACK_ENABLED(false), LLM_MAX_ITERATIONS(3), LLM_MAX_TOKENS, LLM_TIMEOUT_S, LLM_RETRIES, LLM_BREAKER_*, PROMPT_VERSION, INPUT_MAX_CHARS, MODEL_ARMOR_TEMPLATE, MODEL_ARMOR_TIMEOUT_MS(500), MODEL_ARMOR_FAIL_OPEN(false), PRESIDIO_SPACY_MODEL, TENANT_TOKEN_BUDGET, TENANT_MAX_CONCURRENCY, SSE_HEARTBEAT_S, SSE_REPLAY_TTL_S, TURN_LEASE_S, HISTORY_MAX_TURNS(6), HISTORY_MAX_TOKENS(3000), EVAL_SAMPLE_RATE. Values marked 'set in E4' come from the spikes and are documented in .env.example. Implement guardrails error mapping (6.1): UNAUTHENTICATED 401, FORBIDDEN 403, INPUT_TOO_LONG 413, INPUT_BLOCKED, GUARD_UNAVAILABLE, RATE_LIMITED 429 with Retry-After, TENANT_BUDGET_EXCEEDED, LLM_UNAVAILABLE, RETRIEVAL_UNAVAILABLE, TURN_INTERRUPTED, IDEMPOTENCY_KEY_REUSED 409, INTERNAL. HTTP error body is {"error":{"code","message","request_id","retryable"}} with a fixed message per code, never exception text. Replaces the MVP src/errors.py behaviour that leaks exceptions.

## Acceptance criteria
- [ ] Given a missing required key, when Settings loads, then boot raises (unit test per key group).
- [ ] Given each exception class raised in a handler, when mapped, then the response body has the stable code and the fixed message and contains no substring of the exception text (parametrized test over every code).
- [ ] X-Request-Id from Kong is echoed in error.request_id (test).
