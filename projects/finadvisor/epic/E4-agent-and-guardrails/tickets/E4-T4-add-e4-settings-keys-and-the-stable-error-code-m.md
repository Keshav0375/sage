---
key: "E4-T4"
title: "E4 settings keys and the stable error-code mapping"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T21"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/06-interfaces-and-contracts.md#6.6", "decision-logs.md#adr-036", "decision-logs.md#adr-033"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 96, "id": 6155682537, "url": "https://github.com/Keshav0375/FinAdvisor/issues/96"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Typed Settings for E4 keys (Model Armor behind a flag) and one error-code to HTTP/SSE mapping with fixed messages.

## Description
Add to the pydantic-settings Settings class (6.6), no secret default, missing required key fails boot: ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, LLM_MODEL_ANSWER, LLM_MODEL_AUX, LLM_MODEL_FALLBACK, LLM_FALLBACK_ENABLED(false), LLM_MAX_ITERATIONS(3), LLM_MAX_TOKENS, LLM_TIMEOUT_S, LLM_RETRIES, LLM_BREAKER_*, PROMPT_VERSION, INPUT_MAX_CHARS, PRESIDIO_SPACY_MODEL, TENANT_TOKEN_BUDGET, TENANT_MAX_CONCURRENCY, SSE_HEARTBEAT_S, SSE_REPLAY_TTL_S, TURN_LEASE_S, HISTORY_MAX_TURNS(6), HISTORY_MAX_TOKENS(3000), EVAL_SAMPLE_RATE, CONTEXTUAL_RETRIEVAL_ENABLED (default false, ADR-016 amended). Model Armor (round 4, ADR-036 amended, R4-D18 V3): MODEL_ARMOR_ENABLED (default from the E4-T1 ADR, false until it says otherwise), MODEL_ARMOR_TEMPLATE, MODEL_ARMOR_TIMEOUT_MS (no 500 default: the value comes from E4-T1 and is documented in .env.example). The earlier MODEL_ARMOR_FAIL_OPEN key is REMOVED (prompts now fail open with an audit flag by rule, not by setting). Values marked 'set in E4' come from the spikes.

Error mapping (6.1): UNAUTHENTICATED 401, FORBIDDEN 403, INPUT_TOO_LONG 413, INPUT_BLOCKED, GUARD_UNAVAILABLE (now only when the in-process fallback guard itself failed; a Model Armor outage alone never raises it), RATE_LIMITED 429 with Retry-After, TENANT_BUDGET_EXCEEDED, LLM_UNAVAILABLE, RETRIEVAL_UNAVAILABLE, TURN_INTERRUPTED, IDEMPOTENCY_KEY_REUSED 409, ENTITLEMENT_CHANGED (ADR-033), INTERNAL; and the refusal reasons of 6.2 as constants (`ANSWER_WITHHELD` with `numeric_ungrounded`, `footer_missing`, `as_of_violation`, `no_version_history`). HTTP error body is {"error":{"code","message","request_id","retryable"}} with a fixed message per code, never exception text. `WRONG_CELL` and `TENANT_MOVED` belong to E13. Replaces the MVP src/errors.py behaviour that leaks exceptions.

## Acceptance criteria
- [ ] Given a missing required key, when Settings loads, then boot raises (unit test per key group).
- [ ] Given Settings, when its fields are listed, then `MODEL_ARMOR_ENABLED`, `MODEL_ARMOR_TIMEOUT_MS` and `CONTEXTUAL_RETRIEVAL_ENABLED` exist, `MODEL_ARMOR_FAIL_OPEN` does not, `CONTEXTUAL_RETRIEVAL_ENABLED` defaults false, and the timeout has no literal 500 default (unit test test_settings_model_armor_keys).
- [ ] Given each exception class raised in a handler, when mapped, then the response body has the stable code and the fixed message and contains no substring of the exception text (parametrized over every code, including ENTITLEMENT_CHANGED).
- [ ] X-Request-Id from Kong is echoed in error.request_id (test).
