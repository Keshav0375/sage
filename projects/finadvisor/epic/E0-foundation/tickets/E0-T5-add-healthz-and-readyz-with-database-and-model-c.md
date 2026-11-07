---
key: "E0-T5"
title: "Add /healthz and /readyz with database and model checks"
epic: "E0"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E0-T3", "E0-T4"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6", "deep-dive/09-observability.md#9", "decision-logs.md#adr-006", "decision-logs.md#adr-018"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 6, "id": 6155570023, "url": "https://github.com/Keshav0375/FinAdvisor/issues/6"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
The API exposes a liveness probe and a readiness probe that fails when the database is unreachable or a configured model is retired.

## Description
Why: §6.1 and observability: `/healthz` (liveness) and `/readyz` (readiness, including "model availability (configured models not retired or soon-retiring)"). plan.md E0 done-when: "`claude-sonnet-4-20250514` in config makes CI and `/readyz` fail (test)". Docker healthchecks in E0-T11 use `/healthz`.

Build (root paths, not under `/api`; the existing `/api/health` stays until E4 replaces the router):
- `GET /healthz`: 200 `{"status": "ok"}`; touches no dependency.
- `GET /readyz`: runs `SELECT 1` on the app's DB engine with a 2 s timeout and `check_models(settings, today=date.today())` from E0-T4. 200 `{"status":"ready","checks":{"db":"ok","models":"ok"}}` when both pass; otherwise 503 `{"status":"not_ready","checks":{"db":"ok|fail","models":"ok|fail"}}`. Responses carry check names and codes only: no exception text, connection strings, key values (the arch rule that errors carry codes, not exception text). Log the failing key/model at warning level.
- The app must still start with a retired model id configured (so readiness can report it).

Out of scope (later epics add them to `/readyz`): DB role flags and FORCE RLS assertions (E1), pgvector >= 0.8 assertion, Kafka reachability (E5), firebase-admin verifier initialised (E1).

## Acceptance criteria
- [ ] Given the app with a stub DB that answers `SELECT 1` and default models, `GET /readyz` returns 200 and `checks.models == "ok"` (unit test).
- [ ] Given `LLM_MODEL_ANSWER=claude-sonnet-4-20250514`, `GET /readyz` returns 503 with `checks.models == "fail"`, while `GET /healthz` still returns 200 (unit test).
- [ ] Given a DB that raises on `SELECT 1`, `GET /readyz` returns 503 with `checks.db == "fail"`, and the response body contains neither the DB host nor the exception message (unit test asserting on `response.text`).
- [ ] Integration test (`requires_db`): against the real pgvector Postgres, `/readyz` returns 200; with `DB_PORT` pointed at a closed port it returns 503 within 5 s.
- [ ] mypy strict and ruff pass on the new routes.
