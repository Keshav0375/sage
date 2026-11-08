---
key: "E8-T2"
title: "App tests (health / version / root)"
epic: "E8"
repo: "Sentinel-deployment"
size: "S"
status: "done"
depends_on: ["E8-T1"]
arch_refs: ["deep-dive/08-deployment-and-scenarios.md#8.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 41, "id": 5694994266, "url": "https://github.com/Keshav0375/sentinel-brain/issues/41"}
branch: "dev/deploy-phase-1-app"
pr: "https://github.com/Keshav0375/Sentinel-deployment/pull/1"
updated: "2026-11-08"
---

## Summary
Endpoint tests using FastAPI `TestClient`.

## Description
Source: deployment task 1.2 (`sentinel-brain/implementation/tasks/deployment/phase-1-app/task-2-app-tests.md`).

**Files created:** `tests/__init__.py`, `tests/test_app.py`
- `test_root` — 200, body `{"message":"ok","service":"sentinel-watchtower"}`.
- `test_health` — 200, `status == "ok"`, `uptime_seconds` is an int ≥ 0.
- `test_version` — 200, `version` matches configured `app_version`, `service == "sentinel-watchtower"`.
- `test_startup_log` (optional) — capture the startup log line shape.
- Add `pytest` (+`httpx`) to a dev-requirements or `requirements-dev.txt`.

## Acceptance criteria
- [x] `pytest tests/ -x` green; covers all three endpoints + response shapes.
- [x] Tests import the app without hitting the network (TestClient).

## Outcome
Added tests/__init__.py, tests/test_app.py (4 tests: root, health, version via APP_VERSION, startup_log). Commit `04ad349` in Sentinel-deployment: test: add endpoint and startup-log tests for sentinel-watchtower. Env/.env isolation proven; mutation check confirmed failures on breakage.
Gate: VERDICT GREEN (n/a: yamllint, actionlint; ran ruff-lint, gitleaks, pytest).
Review fix `fb84894` in Sentinel-deployment: test: assert exact /health response shape (Refs #41).
Follow-up: StarletteDeprecationWarning (httpx -> httpx2 for TestClient) on pinned dev deps.
