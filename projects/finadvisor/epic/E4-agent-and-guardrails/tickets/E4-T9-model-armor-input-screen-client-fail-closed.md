---
key: "E4-T9"
title: "Model Armor client behind a flag with in-process fallback"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T1", "E4-T8"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#adr-009", "decision-logs.md#adr-036", "decision-logs.md#adr-039"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 101, "id": 6155688365, "url": "https://github.com/Keshav0375/FinAdvisor/issues/101"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Screen redacted input via Model Armor when MODEL_ARMOR_ENABLED, else or on failure via Presidio plus heuristics, failing open with an audit flag for prompts.

## Description
Client in src/guardrails (round 4, ADR-036 amended 2026-11-07, ADR-009 amended, R4-D18 V3). Quote ADR-036: 'Model Armor sits behind a feature flag with a documented fallback ... Fallback: Presidio plus heuristic injection patterns. Ingest documents fail closed into quarantine; prompts fail open with an audit flag on the turn ... `GUARD_UNAVAILABLE` now means the in-process fallback itself failed.' This replaces the old '500 ms, fail closed' behaviour.

`screen(text, mode)` with mode `prompt` or `document`. When `MODEL_ARMOR_ENABLED` is true, call Model Armor sanitizeUserPrompt with MODEL_ARMOR_TEMPLATE on the redacted text, timeout MODEL_ARMOR_TIMEOUT_MS (from E4-T1). A match verdict -> INPUT_BLOCKED (no LLM call). Timeout, 5xx, auth error or `EXECUTION_SKIPPED` -> run the in-process fallback: heuristic injection patterns (instruction-override phrases, role markers, tool-call syntax; a hit -> INPUT_BLOCKED) over the already Presidio-redacted text; mode `prompt` then continues (fail OPEN) and returns `guard_degraded=true`, which the orchestrator writes as a flag on the turn (it travels in the chat.audit flags, E4-T21); mode `document` returns `fail_closed=True` so the caller quarantines (E11-T13 reuses this client with mode `document`). When the flag is false the fallback alone runs and `guard_degraded=true` is set with reason `armor_disabled`. If the fallback itself raises, `GUARD_UNAVAILABLE`. The screen runs concurrently (asyncio.gather) with the Voyage embed; if the screen blocks, the embed result is discarded and no retrieval SQL runs. The REST API only detects; the app acts. Out of scope: ingest scan stage (E6-T20), document screening wiring (E11-T13).

## Acceptance criteria
- [ ] Given MODEL_ARMOR_ENABLED=true and Model Armor stubbed to delay past MODEL_ARMOR_TIMEOUT_MS, when a prompt is screened, then the turn continues, `guard_degraded=true` with reason `armor_timeout`, and the heuristics ran (test test_prompt_fails_open_with_audit_flag).
- [ ] Given a blocked verdict, or a heuristic injection pattern while Model Armor is down, when screened, then INPUT_BLOCKED is raised and neither Anthropic nor DB retrieval is called.
- [ ] Given MODEL_ARMOR_ENABLED=false, when a prompt is screened, then the Model Armor stub records 0 calls, the fallback runs and `guard_degraded` reason is `armor_disabled`.
- [ ] Given mode `document` and a Model Armor 5xx or `EXECUTION_SKIPPED`, when screened, then `fail_closed=True` is returned (never pass-through).
- [ ] Given the fallback raising an exception, when a prompt is screened, then GUARD_UNAVAILABLE is returned; given the embed and screen stubs each sleeping 300 ms, when run together, then wall time is under 450 ms.
