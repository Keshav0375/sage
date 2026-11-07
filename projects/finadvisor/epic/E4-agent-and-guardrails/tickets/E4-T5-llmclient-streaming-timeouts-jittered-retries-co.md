---
key: "E4-T5"
title: "LLMClient: streaming, timeouts, jittered retries, config-only models"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T4"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#ADR-005", "decision-logs.md#ADR-006"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 97, "id": 6155683649, "url": "https://github.com/Keshav0375/FinAdvisor/issues/97"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
In-process LLMClient over the Anthropic SDK with streaming, timeouts and retries.

## Description
Implement src/llm (ADR-005). stream(messages, tools, system, model=None) yields normalized events (text delta, tool_use, usage, stop_reason). Explicit connect/read timeouts from LLM_TIMEOUT_S; retries LLM_RETRIES with exponential backoff and full jitter on 429/5xx/overloaded/connection errors only (never on 4xx other than 429); max_tokens=LLM_MAX_TOKENS always set; model ids only from Settings; base URL from ANTHROPIC_BASE_URL. The request builder must never send temperature, top_p or top_k (removed 2026-10-21, 400). Replaces LiteLLM use in the MVP (litellm/ dir out of scope to delete unless E1 owns it). Out of scope: breaker, fallback, caching.

## Acceptance criteria
- [ ] Given a stubbed 529 twice then 200, when streaming, then exactly 3 attempts are made with sleeps drawn from the jitter range (seeded test).
- [ ] Given a 400 response, when streaming, then no retry occurs and LLM_UNAVAILABLE-mappable error is raised.
- [ ] Given any request, when captured at the HTTP layer, then the body has no temperature, top_p or top_k keys and has max_tokens (test).
- [ ] Given no hardcoded model string in src/llm, a grep-based test fails if a literal 'claude-' id appears outside config/tests.
