---
key: "E0-T13"
title: "Rewrite CI: lockfile installs, service containers, all checks"
epic: "E0"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T2", "E0-T4", "E0-T6", "E0-T9", "E0-T10", "E0-T12"]
arch_refs: ["deep-dive/01-context-and-goals.md#1", "deep-dive/04-components-and-responsibilities.md#4", "decision-logs.md#adr-021", "deep-dive/11-tech-stack.md#cicd"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 14, "id": 6155584971, "url": "https://github.com/Keshav0375/FinAdvisor/issues/14"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
A pull request runs ruff, mypy, unit and integration tests, the model-id check, eslint, tsc and vitest from lockfiles, and any failure blocks the PR.

## Description
Why: G-05: `.github/workflows/ci.yml` runs `pip install -e ".[dev]"` but no `dev` extra exists, so ruff, mypy and pytest are not installed and CI fails at Lint; `eval-gate.yml` has the same install and cannot run (G-06, owned by E7). ADR-021: "Lockfile installs only. Python: ruff, mypy, pytest, import-linter; frontend: eslint, tsc, vitest". plan.md E0: "CI with lockfile installs, Postgres and Kafka service containers (`pgvector/pgvector:0.8.5-pg16`)". The security scans are E0-T14. Unit-testing import-linter contracts is a later epic (no contracts exist yet).

Replace `.github/workflows/ci.yml`. Triggers `pull_request` to `main` and `push` to `main`; `permissions: contents: read`; concurrency cancels superseded runs; every `uses:` action pinned to a full commit SHA with the tag in a comment. Jobs:
- `backend-static`: Python 3.12, `pip install poetry==<pinned>`, `poetry check --lock`, `poetry install --with dev --no-interaction` from `backend/poetry.lock`; `ruff check .`, `ruff format --check .`, `mypy src/`; `python -m src.model_lifecycle` (E0-T4, with default env so the check runs on the configured ids); `bash scripts/check_no_litellm.sh` (E0-T6).
- `backend-unit`: same install; `pytest -m "not integration"`.
- `backend-integration`: service containers `pgvector/pgvector:0.8.5-pg16` and `apache/kafka:4.4.0` (KRaft, health options so the job waits for healthy), `postgresql-client-16` installed for `pg_dump`, `REQUIRE_SERVICES=1`, runs `python -m src.entrypoint jobs migrate` then `pytest -m integration`. Test-only DB credentials come from workflow env generated for the job (not repository defaults in code).
- `frontend`: Node 20, `npm ci`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.
- Delete `.github/workflows/eval-gate.yml` (it cannot run; E7 re-creates the gate on the service containers defined here; see questions).
- Document in `docs/ci.md` the job list and the negative-control procedure below.

Out of scope: trivy, gitleaks, pip-audit (E0-T14), terraform and `kong config parse` jobs (E2, E10), deploy and WIF (E10), eval gate (E7). Making the jobs required checks is a GitHub branch-protection setting, not a file in the repo (see questions).

## Acceptance criteria
- [ ] Given a clean clone of the PR branch, the `CI` workflow completes green on GitHub with all four jobs passing and installs coming only from `backend/poetry.lock` and `frontend/package-lock.json` (`poetry check --lock` and `npm ci` steps present).
- [ ] Negative controls, each on a throwaway branch with the run link recorded in `docs/ci.md`: an unused import turns `backend-static` red (ruff); a wrong return type turns it red (mypy); a failing unit test turns `backend-unit` red; a failing integration test turns `backend-integration` red; an eslint error, a TypeScript error and a failing vitest test each turn `frontend` red.
- [ ] Given `LLM_MODEL_ANSWER=claude-sonnet-4-20250514` in the job env, `backend-static` fails at the model-id step (negative control), and passes with the default.
- [ ] In `backend-integration` the pytest summary reports 0 skipped (the job greps the summary line and fails if `skipped` appears).
- [ ] `grep -rn "\.\[dev\]" .github` returns no match and `.github/workflows/eval-gate.yml` does not exist.
- [ ] `actionlint` run on `.github/workflows/ci.yml` reports no errors, and every `uses:` line carries a 40-hex SHA.
