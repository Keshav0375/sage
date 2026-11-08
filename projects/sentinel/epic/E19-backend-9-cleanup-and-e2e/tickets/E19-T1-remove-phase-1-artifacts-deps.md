---
key: "E19-T1"
title: "Remove POC artifacts + deps"
epic: "E19"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: []
arch_refs: ["deep-dive/00-poc-and-the-pivot-to-mvp.md#0.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 92, "id": 5695002100, "url": "https://github.com/Keshav0375/sentinel-brain/issues/92"}
branch: "dev/backend-phase-9-cleanup"
pr: "https://github.com/Keshav0375/Sentinel/pull/28"
updated: "2026-11-08"
---

## Summary
Delete the POC synthetic-data machinery now that the MVP is proven (§13.5 step 8 is

## Description
Source: backend task 9.1 (`sentinel-brain/implementation/tasks/backend/phase-9-cleanup/task-1-remove-phase1-artifacts.md`).

intentionally late).

**Files deleted (§13.1):** `data/` (all), `src/sentinel/generator/` (all 4), `src/sentinel/infra/db.py`, `scripts/run_scenario.py`, `scripts/run_eval.py`, `scripts/demo.py`, `docker-compose.yml`.
**Deps removed (§13.4):** `aiosqlite`; `numpy` (keep only if transitively required by sentence-transformers).
**Files modified:** `pyproject.toml` (drop deps), `Dockerfile` (already no `data/` from 7.1), any lingering imports.

## Acceptance criteria
- [x] All listed paths removed; app boots; full suite green; no dangling imports.
- [x] `aiosqlite` gone; `numpy` gone or transitive-only; lockfile regenerated.

## Outcome
Commit `8a55663` on `dev/backend-phase-9-cleanup`: "refactor: remove POC synthetic data, generator, SQLite and scripts; serve the scenario catalog".
- Deleted: `data/`, `src/sentinel/generator/`, `infra/db.py`, `api/events.py` (SSE `/events/{id}`, dashboard-only), `scripts/run_scenario.py`, `scripts/demo.py`, `docker-compose.yml`, POC tests.
- Kept: `scripts/run_eval.py` (decision 2026-10-25), alembic 001/002.
- `aiosqlite` removed (lock: aiosqlite + content-hash only); numpy transitive only. pyproject no longer includes `data/`; CLI serve-only; `config.sentinel_db_path` removed.
- Catalog: vendored `src/sentinel/catalog/branches.yaml` (git mv from eval fixture) + loader; `/api/scenarios` serves it read-only behind bearer. Dashboard is a read-only catalog (no Fire button, no live view).
- Decisions: 3c492de, 9320bb1.
- Review fix `3f7cdd3` ("fix: phase 9 review — branch kept out of prompts, dataset write off the critical path, POC models removed"): POC models deleted; stale text fixed; numpy and pytest-timeout dev-only.
- Decisions: 3c492de, 9320bb1, b0fa4a4, 8e763a0, 934fe7d.
- Follow-up: EventBus and DashboardEventEmitter have no subscriber; kept per decision 2026-10-15 (emitter as trace processor); removal needs a decision.
