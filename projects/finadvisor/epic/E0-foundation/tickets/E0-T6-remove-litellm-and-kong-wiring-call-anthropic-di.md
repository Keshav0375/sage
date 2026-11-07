---
key: "E0-T6"
title: "Remove LiteLLM and Kong wiring; call Anthropic directly"
epic: "E0"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T3"]
arch_refs: ["deep-dive/01-context-and-goals.md#1", "decision-logs.md#adr-005", "decision-logs.md#adr-006", "deep-dive/06-interfaces-and-contracts.md#6.6"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 7, "id": 6155571397, "url": "https://github.com/Keshav0375/FinAdvisor/issues/7"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
No LiteLLM service, config, dependency or doc remains; the backend calls Anthropic at `ANTHROPIC_BASE_URL` with model ids from Settings.

## Description
Why: ADR-005: drop LiteLLM; its config shuffles Claude, GPT-4o and Gemini under one name (G-08) and its fallback key matches nothing (G-09). plan.md E0: "Remove LiteLLM and the Kong/LiteLLM wiring". The in-process `LLMClient` with same-provider fallback is E4; this ticket only removes the old path and makes the existing code call Anthropic directly. Kong returns in E2 with a new `kong.yml`; the MVP Kong config only fronts LiteLLM and posts to a non-existent audit route, so it goes.

Do:
- Delete `litellm/`, `kong/` (Dockerfile and kong.yml), `backend/tests/test_fallback_chain.py`, `backend/scripts/test_fallback_live.py`.
- `backend/src/main.py`: `anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY, base_url=settings.ANTHROPIC_BASE_URL)`; remove the `kong_url` / `litellm_master_key` branch. Do not pass `temperature`, `top_p` or `top_k` anywhere (ADR-006: removed from the API, 400).
- Model ids from config at every call site: `backend/src/agent/orchestrator.py` (drop `DEFAULT_MODEL`; `model` becomes a required constructor argument, `backend/src/dependencies.py` passes `settings.LLM_MODEL_ANSWER`), `backend/scripts/run_eval.py` (`JUDGE_MODEL` from `LLM_MODEL_JUDGE`), `backend/scripts/generate_corpus.py` (`LLM_MODEL_AUX`). Update tests that referenced the old string (`tests/test_tracing.py` line 43 is replaced by E0-T8).
- `docker-compose.yml`: delete the `litellm` and `kong` services and the backend env `KONG_URL`, `LITELLM_MASTER_KEY`, the `depends_on: kong`. Pass `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` instead. (E0-T11 rewrites the file fully.)
- Update `README.md` (architecture diagram, stack table, directory list, "Fallback Chain" paragraph) and `CLAUDE.md` (routing and stack lines) to say: Anthropic direct, Kong arrives in E2. Update `.env.example` already done in E0-T3, confirm no leftovers.
- Add `scripts/check_no_litellm.sh`: fails if `git grep -il litellm` matches any tracked file outside the allowlist `Story-Reports/`, `TODO.md`, `mvp.md`, `architecture.md`, `docs/threat_model.md`, `scripts/check_no_litellm.sh` itself (historical MVP records; see questions), and fails if `backend/poetry.lock` or `backend/pyproject.toml` contains `litellm`.

Out of scope: Terraform (E0-T7), the LLMClient, fallback, circuit breaker (E4), the Kong egress route (E2).

## Acceptance criteria
- [ ] Given the repo after this change, `bash scripts/check_no_litellm.sh` exits 0; after temporarily adding the word `LiteLLM` to `backend/src/main.py` it exits 1 (verified in the PR description).
- [ ] `git ls-files litellm kong` prints nothing, and `docker compose config --services` lists no `litellm` or `kong` service.
- [ ] `grep -rEn "claude-sonnet-4-20250514|DEFAULT_MODEL|JUDGE_MODEL = " backend/src backend/scripts` returns no hard-coded model id, and a unit test asserts `FinAdvisorAgent` sends `model == settings.LLM_MODEL_ANSWER` to the (mocked) Anthropic client.
- [ ] A unit test asserts the client built in `src.main.lifespan` has `base_url` equal to `ANTHROPIC_BASE_URL` and the API key from `ANTHROPIC_API_KEY`.
- [ ] `ruff check`, `mypy src/` and `pytest` pass (the two deleted fallback test files are the only removed tests).
