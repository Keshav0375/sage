---
key: "E12-T4"
title: "infra/tracing.py → LangFuse (observe + prompts + scoring)"
epic: "E12"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E11-T1", "E13-T1"]
arch_refs: ["deep-dive/11-observability-and-ops-dashboard.md#11.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 58, "id": 5694996972, "url": "https://github.com/Keshav0375/sentinel-brain/issues/58"}
branch: "dev/backend-phase-2-memory-and-tracing"
pr: "https://github.com/Keshav0375/Sentinel/pull/20"
updated: "2026-11-08"
---

## Summary
Replace custom trace capture with LangFuse: `@observe` decorators, LangFuse-first prompt

## Description
Source: backend task 2.4 (`sentinel-brain/implementation/tasks/backend/phase-2-memory-and-tracing/task-4-langfuse-tracing.md`).

loading with local fallback, and score piping (§6.2–6.4).

**Files modified:** `src/sentinel/infra/tracing.py`
_(v3 API, amended 2026-10-12 — langfuse 3.x; see decisions.md 2026-10-12)_
- Client via `from langfuse import get_client` → `get_client()`, from env `LANGFUSE_PUBLIC_KEY` /
  `LANGFUSE_SECRET_KEY` / `LANGFUSE_BASE_URL` (not the deprecated `LANGFUSE_HOST`). No `langfuse.decorators`.
- `from langfuse import observe` wrappers for pipeline / agent / tool (`as_type="agent"` / `"tool"`);
  trace attributes via `propagate_attributes(metadata, tags)` (§6.2). Trace id = `incident_id.hex`
  passed as `langfuse_trace_id=` to the root observed call; `RunContext` carries the id string (§4.5).
- `async def load_prompt(agent_name)` — `get_prompt(name, cache_ttl_seconds=300)` inside try/except,
  fallback to `agents/prompts/{name}.txt` (§6.3). Keyless client raises in `get_prompt` — the except is required.
- `push_score(trace_id, name, value)` → `create_score(trace_id=…, name=…, value=…, data_type="NUMERIC")` (§6.4).
- `shutdown()` on app exit, `flush()` at the end of CLI/eval runs.
- Degrade gracefully when LangFuse keys are absent/unreachable (disabled client, file prompts, no crash).
- Do not touch the openai-agents `TracingProcessor` wiring; LLM-generation capture is an open decision (§6.2 gap).

## Acceptance criteria
- [x] Prompt loader returns LangFuse prompt when available, file otherwise (test both).
- [x] Trace/score helpers callable and typed; no hard failure when keys absent.

## Outcome
Built v3 LangFuse tracing in `infra/tracing.py`: `trace_incident` context manager (root "incident-pipeline", trace id = UUID.hex, propagate_attributes), `incident_trace_id`, `load_prompt` (LangFuse-first, package-relative file fallback), `push_score` (create_score NUMERIC), shutdown in lifespan, flush in CLI/scripts. Safe with no keys or unreachable Langfuse. R14 (token/cost) out of scope.
Commit `49e3534` refactor: LangFuse v3 tracing — observe, prompt loading, scores.
Files: src/sentinel/infra/tracing.py, main.py, cli.py, scripts/run_eval.py, scripts/run_scenario.py, tests/conftest.py, tests/test_infra/test_tracing.py, .env.example.
Live trace check SKIPPED: user's .env uses LANGFUSE_HOST; needs rename to LANGFUSE_BASE_URL.
