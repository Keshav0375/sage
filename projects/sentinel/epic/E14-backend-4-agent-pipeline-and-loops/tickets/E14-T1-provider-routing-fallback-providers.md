---
key: "E14-T1"
title: "Provider routing + fallback (providers/)"
epic: "E14"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E13-T1"]
arch_refs: ["deep-dive/04-agent-pipeline.md#4.5"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 68, "id": 5694998580, "url": "https://github.com/Keshav0375/sentinel-brain/issues/68"}
branch: "dev/backend-phase-4-agents"
pr: "https://github.com/Keshav0375/Sentinel/pull/22"
updated: "2026-11-08"
---

## Summary
LLM provider routing: Anthropic default, OpenAI fallback, per-agent model assignment, and

## Description
Source: backend task 4.1 (`sentinel-brain/implementation/tasks/backend/phase-4-agents/task-1-provider-routing.md`).

automatic fallback on rate-limit/timeout/API error (§4.7).

**Files created:** `src/sentinel/providers/` — `__init__.py`, `router.py`, maybe `models.py`.
- Model map per agent/step (§4.7 table): orchestrator/analysis/resolution → `anthropic/claude-sonnet-4-6` (fb `openai/gpt-4o`); triage/reflexion/reverification/judge/pr-content → `anthropic/claude-haiku-4-5` (fb `openai/gpt-4o-mini`).
- `call_with_fallback(agent, input, primary, fallback)` per §4.7 snippet; switch default via `sentinel_primary_provider`.
- `SENTINEL_FAKE_LLM=1` → a deterministic stub provider for CI (no network).
- Uses OpenAI Agents SDK `Agent.with_model(...)` pattern.

## Acceptance criteria
- [x] Correct model string per agent role (conformance-checked against §4.7).
- [x] Fallback triggers on RateLimit/Timeout/APIError and logs the switch (structlog).
- [x] Fake mode returns canned outputs, no network.

## Outcome
Built the provider router (role map by `sentinel_primary_provider`, Anthropic/OpenAI only; judge on the non-primary provider with a guard; `call_with_fallback` returns `model_used`), `SENTINEL_FAKE_LLM` deterministic Model, R14 token bridge (generation spans to Langfuse, per-incident totals, 50K warning), and `set_trace_processors` with only our processors (`trace_include_sensitive_data=False`). `PUT /api/config` removed. Interim: agents keep Phase-1 shape until 4.2.
Commits (Sentinel): db70a9f, a0f4458, c37f70d, 75e113d. Per decision 2026-10-15 + amendment 52a5f7f.
