---
key: "E13-T1"
title: "config.py extensions"
epic: "E13"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E11-T1"]
arch_refs: ["deep-dive/04-agent-pipeline.md#4.5", "deep-dive/00-poc-and-the-pivot-to-mvp.md#0.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 60, "id": 5694997368, "url": "https://github.com/Keshav0375/sentinel-brain/issues/60"}
branch: "dev/backend-phase-3-tools"
pr: "https://github.com/Keshav0375/Sentinel/pull/21"
updated: "2026-11-08"
---

## Summary
Extend `Settings` (pydantic-settings) with all MVP config keys.

## Description
Source: backend task 3.1 (`sentinel-brain/implementation/tasks/backend/phase-3-tools/task-1-config-extensions.md`).

**Files modified:** `src/sentinel/config.py`
- LLM: `sentinel_primary_provider`, `anthropic_api_key`, `openai_api_key`.
- DB: `database_url`, `db_pool_min`, `db_pool_max`.
- LangFuse: `langfuse_public_key`, `langfuse_secret_key`, `langfuse_base_url` (env `LANGFUSE_BASE_URL`; decision 2026-10-12).
- Datadog: `dd_api_key`, `dd_app_key`, `dd_site`.
- GitHub: `github_api_token`.
- API auth: `sentinel_api_token`.
- Runtime: `log_level`, `max_tool_calls` (default 20), `embedding_model`, `fake_llm` (bool).
- All typed, env-driven, `SENTINEL_`-prefixed where applicable; secrets as `SecretStr`.

## Acceptance criteria
- [x] Settings load from env/.env; `max_tool_calls` defaults to 20; secrets are `SecretStr`.
- [x] `.env.example` (repo root) matches the fields (already reconstructed).
- [x] Missing required secret raises a clear validation error (not a silent None) in non-fake mode.

## Outcome
Commit `0800159` — feat: config extensions — optional SecretStr credentials, Datadog/GitHub/LangFuse settings.
Files: .env.example, config.py, providers/resolver.py, providers/__init__.py, main.py, eval/runner.py, tests (test_config, test_resolver, test_main, test_runner, conftest).
Per decision 2026-10-14 (phase 3 tools contract): sentinel_* names kept; max_tool_calls 20; dd/github/langfuse creds are SecretStr|None; dd_site us5; no sentinel_api_token; no secret required at boot (provider keys checked in resolve_model, missing key escalates the incident); added sentinel_fake_llm (unused yet). Fixed python-dotenv inline-comment bug in .env.example. App boots with no credentials (subprocess test).
Gate: VERDICT GREEN, 7 ran (orchestrator, env -i + TEST_DATABASE_URL only). 20 tests. Tree clean, attribution none.
