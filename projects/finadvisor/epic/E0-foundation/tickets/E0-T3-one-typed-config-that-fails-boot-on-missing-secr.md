---
key: "E0-T3"
title: "One typed config that fails boot on missing secrets"
epic: "E0"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.6", "deep-dive/01-context-and-goals.md#1", "decision-logs.md#adr-006", "decision-logs.md#adr-005"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 4, "id": 6155567512, "url": "https://github.com/Keshav0375/FinAdvisor/issues/4"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
A single pydantic-settings `Settings` holds the E0 keys from the config table, has no secret defaults, and the app refuses to start without its required keys.

## Description
Why: G-25: `backend/src/config.py` has code defaults for secrets (`localdev` DB password, `[dev key, redacted]`, `[dev secret, redacted]`) and a missing variable falls back silently. §6.6: "One typed `Settings` class (pydantic-settings). No secret has a default; a missing required key fails boot." ADR-006: "Model ids only from config."

Rewrite `backend/src/config.py` (one class, `Settings(BaseSettings)`, env names are the upper-case keys below, secrets as `SecretStr`):
- `ENV_PROFILE` (`dev` | `demo` | `prod`, default `dev`).
- `DB_HOST`, `DB_PORT` (see questions; int, default 5432), `DB_NAME`, `DB_USER`, `DB_PASSWORD` (secret), `DB_POOL_SIZE`, `DB_STATEMENT_TIMEOUT_MS`: no defaults except `DB_PORT`. Provide a `database_dsn` property (`postgresql+asyncpg://...`, URL-encoded password) replacing `database_url`.
- `ANTHROPIC_API_KEY` (secret, required), `ANTHROPIC_BASE_URL` (default `https://api.anthropic.com`).
- `LLM_MODEL_ANSWER` (default `claude-sonnet-5-5`), `LLM_MODEL_AUX` and `LLM_MODEL_JUDGE` (default `claude-haiku-5-5`), `LLM_MODEL_FALLBACK` (default `claude-sonnet-4-6`), `LLM_FALLBACK_ENABLED` (default `false`), `LLM_MAX_ITERATIONS` (default 3). A validator rejects `LLM_MODEL_JUDGE == LLM_MODEL_ANSWER` (§6.6: judge must differ from answer). The model-id values are not checked against the retirement table here (E0-T4 does that, and `/readyz` must still be able to boot and report it).
- `VOYAGE_API_KEY` (secret, required).
- `LANGFUSE_ENABLED` (default `false`), `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`; the three Langfuse values are required only when `LANGFUSE_ENABLED=true`.
- Keys still read by MVP code that E1 replaces: `PII_MODE` (default `regex`), `GCP_PROJECT_ID` (default empty), `JWT_SECRET` (secret, required, no default; E1 deletes it).
- Remove `openai_api_key`, `google_api_key`, `litellm_master_key`, `kong_url`, `llm_base_url`, `database_url`.
Only keys the E0 code consumes are added; later epics add theirs from §6.6.

Update every consumer: `backend/src/main.py` (build the engine from `database_dsn`, never log credentials), `backend/src/db/session.py` (`pool_size=DB_POOL_SIZE`, per-connection `statement_timeout` from `DB_STATEMENT_TIMEOUT_MS`), `backend/src/pii/__init__.py`, `backend/scripts/ingest.py`, `backend/scripts/generate_corpus.py`, `backend/tests` fixtures. Tests get their values from an autouse fixture / `pytest` env setup that sets dummy non-secret-looking values; the code itself holds none. Rewrite `.env.example` with placeholders only (`REPLACE_ME`), listing exactly these keys.

Out of scope: embeddings model keys (E3), Kafka and other keys (their epics), swapping the LLM call sites to the new model keys (E0-T6), role/RLS config (E1).

## Acceptance criteria
- [ ] Given each of `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `DB_PASSWORD`, `JWT_SECRET`, `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_POOL_SIZE`, `DB_STATEMENT_TIMEOUT_MS` removed in turn from an otherwise valid environment, when `Settings()` is built, then it raises `ValidationError` naming that key (parametrized unit test, `backend/tests/test_settings.py`).
- [ ] Given `ANTHROPIC_API_KEY` is unset, when `uvicorn src.main:app` is started in a subprocess, then the process exits non-zero within 15 s, stderr names `ANTHROPIC_API_KEY`, and no secret value from the environment appears in stderr (subprocess test).
- [ ] Given `LANGFUSE_ENABLED=true` with no Langfuse keys, `Settings()` raises; given `LANGFUSE_ENABLED=false` and no keys, it succeeds.
- [ ] Given `LLM_MODEL_JUDGE` equal to `LLM_MODEL_ANSWER`, `Settings()` raises `ValidationError`.
- [ ] `repr(Settings(...))` and `str(Settings(...))` contain none of the secret values, and `grep -rEn "localdev|[dev secret, redacted]|sk-litellm" backend/src backend/scripts .env.example` returns no match.
- [ ] `ruff check`, `ruff format --check`, `mypy src/` and the full existing `pytest` suite pass (97 passed before this ticket).
