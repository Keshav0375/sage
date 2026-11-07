---
key: "E0-T2"
title: "Build the backend image from poetry.lock with dev and runtime stages"
epic: "E0"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/01-context-and-goals.md#1", "deep-dive/04-components-and-responsibilities.md#4", "decision-logs.md#adr-021", "decision-logs.md#adr-019"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 3, "id": 6155566176, "url": "https://github.com/Keshav0375/FinAdvisor/issues/3"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
The backend image installs only what `backend/poetry.lock` pins, has a real `dev` stage, and the build fails when the lock is stale.

## Description
Why: G-28: `backend/Dockerfile:6-8` runs `pip install -e "."` from `>=` floors and ignores `poetry.lock`, so rebuilds change major versions. G-49: `docker-compose.override.yml` targets a `dev` stage that does not exist. ADR-021: lockfile installs only, images referenced by digest. ADR-019: one Python image (entrypoints are added in E0-T9).

Build `backend/Dockerfile` as a multi-stage build:
- `base`: `python:3.12-slim` referenced by `@sha256:` digest (resolve the current digest and add a comment with the tag).
- `builder`: installs a pinned Poetry version, runs `poetry check --lock` then `poetry install --no-root --only main --no-interaction` into a virtualenv at `/opt/venv` using `backend/poetry.lock`.
- `dev`: adds the `dev` dependency group, runs as non-root, keeps `CMD uvicorn src.main:app --reload --host 0.0.0.0 --port 8000` (the override file mounts `src/` and `tests/`).
- `runtime` (the last stage, so a plain `docker build` produces it): main group only, source copied, non-root user, `CMD uvicorn src.main:app --host 0.0.0.0 --port 8000`.
- Add `backend/.dockerignore` excluding `.venv`, `.env`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`.
- Pin the poetry-core build requirement in `backend/pyproject.toml` (`requires = ["poetry-core==<locked version>"]`) so builds do not float.
- Leave `docker-compose.yml` ports/services alone (E0-T11 rewrites it); only make sure `docker-compose.override.yml` `target: dev` now resolves.

Out of scope: the `api | worker | jobs` entrypoint dispatcher (E0-T9), compose rewrite (E0-T11), CI (E0-T13), Trivy image scan (E0-T14).

## Acceptance criteria
- [ ] Given a clean checkout, when `docker build --target runtime -t fa-backend:test backend` runs, then it succeeds, and `docker run --rm fa-backend:test python -c "import fastapi,anthropic,langfuse,importlib.metadata as m; print(m.version('fastapi'), m.version('anthropic'), m.version('langfuse'))"` prints exactly the three versions listed in `backend/poetry.lock`.
- [ ] Given `backend/pyproject.toml` has a new dependency added without re-locking, when the image is built, then the build fails at `poetry check --lock` (verified once by adding `rich` to pyproject and confirming a non-zero build exit).
- [ ] `docker build --target dev` succeeds and `docker run --rm <dev-image> pytest --version` exits 0, while `docker run --rm fa-backend:test pytest --version` exits non-zero (no dev tools in runtime).
- [ ] `docker run --rm fa-backend:test id -u` prints a non-zero uid.
- [ ] Every `FROM` line in `backend/Dockerfile` contains `@sha256:` (checked by `! grep -E '^FROM' backend/Dockerfile | grep -v '@sha256:'`).
