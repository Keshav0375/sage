---
key: "E8-T1"
title: "FastAPI app (3 routes + startup log + config)"
epic: "E8"
repo: "Sentinel-deployment"
size: "S"
status: "done"
depends_on: []
arch_refs: ["deep-dive/08-deployment-and-scenarios.md#8.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 40, "id": 5694994102, "url": "https://github.com/Keshav0375/sentinel-brain/issues/40"}
branch: "dev/deploy-phase-1-app"
pr: "https://github.com/Keshav0375/Sentinel-deployment/pull/1"
updated: "2026-11-08"
---

## Summary
Intentionally minimal app — the deploy pipeline is the product; this is the target.

## Description
Source: deployment task 1.1 (`sentinel-brain/implementation/tasks/deployment/phase-1-app/task-1-fastapi-app.md`).

**Files created:**
- `app/__init__.py`
- `app/main.py` — FastAPI app; `GET /` → `{"message":"ok","service": settings.dd_service}`; `GET /health` → `{"status":"ok","uptime_seconds":N}`; `GET /version` → `{"version": settings.app_version, "service": settings.dd_service}` (`dd_service` defaults to `sentinel-watchtower`, R10); startup lifespan emits ONE structured JSON log line `app.startup` with dd.service/env/version (§2.2).
- `app/config.py` — `AppConfig(BaseSettings)` per §2.4: `app_version`, `dd_service`, `dd_env`, `port`.
- `requirements.txt` — exact `==` pins per §2.3: `fastapi`, `uvicorn`, `pydantic-settings`, `gunicorn` (the §2.5 start command needs it).
- `requirements-dev.txt` — `-r requirements.txt` + pinned `pytest`, `httpx`, `ruff` (never deployed; Oryx installs only `requirements.txt`).
- `.env.example` — from [implementation/env-examples/deployment.env.example] app section.
- `.gitignore` (extend), `README.md` (run locally: `uvicorn app.main:app --reload`).

## Acceptance criteria
- [x] `uvicorn app.main:app` boots; all three routes return the documented shapes.
- [x] Startup emits exactly one `app.startup` structured line with dd tags + app_version from env.
- [x] `/version` reflects `APP_VERSION` env (so demo PRs that change version are observable).

## Outcome
Built sentinel-watchtower FastAPI app (3 routes, one `app.startup` log line, AppConfig). Commit `bad8fbd` in Sentinel-deployment: feat: add sentinel-watchtower FastAPI app with startup log and config. Files: app/__init__.py, app/config.py, app/main.py, requirements.txt, requirements-dev.txt, .env.example, .gitignore, README.md.
Gate: VERDICT GREEN (n/a: yamllint, actionlint, pytest; ran ruff-lint, gitleaks). 7 pins co-install on 3.12.15, pip check clean; uvicorn and gunicorn (§2.5) both boot.
Gate rule change (user, 2026-10-04): missing-path skips report n/a (brain 80ce6fe).
