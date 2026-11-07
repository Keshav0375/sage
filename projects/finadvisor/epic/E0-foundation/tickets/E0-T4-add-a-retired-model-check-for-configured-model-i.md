---
key: "E0-T4"
title: "Add a retired-model check for configured model ids"
epic: "E0"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E0-T3"]
arch_refs: ["decision-logs.md#adr-006", "deep-dive/06-interfaces-and-contracts.md#6.6", "deep-dive/01-context-and-goals.md#1"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 5, "id": 6155568723, "url": "https://github.com/Keshav0375/FinAdvisor/issues/5"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
A tested function and CLI report any configured model id that is retired, soon retiring or deprecated, so CI and readiness can fail on it.

## Description
Why: ADR-006: `claude-sonnet-4-20250514` retired 2026-06-15 (app and evals fail today); "Model ids only from config; CI and readiness fail on a retired or soon-retiring model." §7 failure modes: "Retired or soon-retiring model id: readiness check, CI check; `/readyz` fails; CI blocks."

Build `backend/src/model_lifecycle.py`:
- A static table of known lifecycle facts from ADR-006: `claude-sonnet-4-20250514` retired 2026-06-15; `claude-sonnet-4-5` retires 2026-11-30; `claude-haiku-4-5` deprecated about 2026-10-15 (retirement date not in the arch; see questions). Each row carries the source URL (https://platform.claude.com/docs/en/about-claude/model-deprecations).
- `check_models(settings, *, today: date) -> list[ModelProblem]` checks `LLM_MODEL_ANSWER`, `LLM_MODEL_AUX`, `LLM_MODEL_JUDGE` and `LLM_MODEL_FALLBACK` (the fallback is checked even while disabled). A problem is: retired (date <= today), soon retiring (within `SOON_RETIRING_DAYS`, one named module constant; value per questions, use 30 until answered) or deprecated. Each problem names the settings key and the model id and the reason code (`retired`, `retiring_soon`, `deprecated`). Ids absent from the table pass (denylist; see questions).
- CLI: `python -m src.model_lifecycle` builds `Settings()` from the environment, prints one line per problem, exits 1 on any problem and 0 otherwise. This is what CI (E0-T13) calls.

Out of scope: the `/readyz` endpoint (E0-T5), calling the Anthropic models API, the fallback eval gate.

## Acceptance criteria
- [ ] Given `LLM_MODEL_ANSWER=claude-sonnet-4-20250514`, `check_models(settings, today=date(2026,11,1))` returns a problem with key `LLM_MODEL_ANSWER` and reason `retired` (unit test).
- [ ] Given `LLM_MODEL_AUX=claude-sonnet-4-5`, `check_models` returns `retiring_soon` for `today=date(2026,11,1)` and returns no problem for `today=date(2026,9,1)` (unit test with the injected clock).
- [ ] Given the default models (`claude-sonnet-5-5`, `claude-haiku-5-5`, `claude-sonnet-4-6`), `check_models(..., today=date(2026,11,1))` returns an empty list.
- [ ] Given `LLM_MODEL_FALLBACK=claude-sonnet-4-20250514` with `LLM_FALLBACK_ENABLED=false`, the check still reports it.
- [ ] `LLM_MODEL_ANSWER=claude-sonnet-4-20250514 python -m src.model_lifecycle` exits 1 and prints the key name; the same command with default model ids exits 0 (subprocess test).
