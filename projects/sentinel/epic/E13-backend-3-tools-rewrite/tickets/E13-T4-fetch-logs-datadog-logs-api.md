---
key: "E13-T4"
title: "fetch_logs → Datadog Logs API"
epic: "E13"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E13-T1"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 63, "id": 5694997838, "url": "https://github.com/Keshav0375/sentinel-brain/issues/63"}
branch: "dev/backend-phase-3-tools"
pr: "https://github.com/Keshav0375/Sentinel/pull/21"
updated: "2026-11-08"
---

## Summary
Rewrite `fetch_logs` to call the Datadog Logs API via httpx (was synthetic).

## Description
Source: backend task 3.4 (`sentinel-brain/implementation/tasks/backend/phase-3-tools/task-4-log-fetcher.md`).

**Files modified:** `src/sentinel/tools/log_fetcher.py`
- Input `LogQuery{service, window_minutes, level?}` → Output `LogAnalysis{entries, count, ...}`.
- httpx async call to Datadog Logs API using `dd_api_key`/`dd_app_key`/`dd_site` from config; retry w/ backoff (CLAUDE.md: 3 attempts 1/2/4s); read-only; structured `ToolError` on failure.
- Respect `SENTINEL_FAKE_LLM`/test mode by allowing an injected client for deterministic tests.

## Acceptance criteria
- [x] Real Datadog query shape correct (endpoint, auth headers, time window); returns typed entries.
- [x] Retries/backoff on transient errors; structured error return (never raw raise).

## Outcome
Built `fetch_logs` per decision 2026-10-14: evidence = Datadog Synthetics results (tests tagged `service:<svc>`; failure code/message, snippets) + CI deploy logs (v2 logs search `service:<svc> (@deploy.status:* OR "deploy.completed")`). URLs built from `dd_site`; 3 attempts w/ backoff on transient errors only, 429 honours Retry-After (cap 10s); missing key -> ToolFailure(unavailable). New `LogFetchResult` has `sources`; `LogAnalysis` untouched; output truncated. Scope: `ToolDeps` gained settings; `build_log_analyst_agent` dropped scenario.
Commit `5423739` refactor: fetch_logs reads Datadog Synthetics results and CI deploy logs.
Files: tools/log_fetcher.py, models/tools.py, tools/registry.py, agents/log_analyst.py, agents/prompts/log_analyst.txt, main.py, eval/runner.py, tests (conftest, test_log_fetcher, test_registry, test_log_analyst).
Live check skipped: no scoped DD keys yet; Sentinel/.env has DD_SITE=datadoghq.com, must become us5.datadoghq.com.
