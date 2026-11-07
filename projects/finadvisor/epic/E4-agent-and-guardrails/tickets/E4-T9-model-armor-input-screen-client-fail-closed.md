---
key: "E4-T9"
title: "Model Armor input screen client, fail closed"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T1", "E4-T8"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#ADR-009"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 101, "id": 6155688365, "url": "https://github.com/Keshav0375/FinAdvisor/issues/101"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Screen redacted input via Model Armor with a 500 ms timeout that fails closed.

## Description
Client in src/guardrails calling Model Armor sanitizeUserPrompt with MODEL_ARMOR_TEMPLATE on the redacted text; timeout MODEL_ARMOR_TIMEOUT_MS (500). Verdict match -> INPUT_BLOCKED (not an LLM call, SSE error or HTTP per 6.1). Timeout, 5xx or auth error -> GUARD_UNAVAILABLE and the turn stops, unless MODEL_ARMOR_FAIL_OPEN is true (default false; boot warns in prod profile if true). The screen runs concurrently (asyncio.gather) with the Voyage embed; if the screen blocks or fails, the embed result is discarded and no retrieval SQL runs. The REST API only detects; the app acts (ADR-009). Use verdict/latency findings from E4-T1.

## Acceptance criteria
- [ ] Given Model Armor stubbed to delay 600 ms, when screened, then GUARD_UNAVAILABLE is returned at about 500 ms and no retrieval call is made (test with timing assertion <700 ms).
- [ ] Given a blocked verdict, when screened, then INPUT_BLOCKED is raised and neither Anthropic nor DB retrieval is called.
- [ ] Given the embed and screen stubs each sleeping 300 ms, when run together, then total wall time is under 450 ms (concurrency test).
- [ ] Given MODEL_ARMOR_FAIL_OPEN=false and a 5xx, the result is GUARD_UNAVAILABLE (never pass-through).
