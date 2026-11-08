---
key: "E16-T2"
title: "eval/runner.py → LangFuse datasets"
epic: "E16"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E16-T1"]
arch_refs: ["deep-dive/11-observability-and-ops-dashboard.md#11.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 81, "id": 5695000526, "url": "https://github.com/Keshav0375/sentinel-brain/issues/81"}
branch: "dev/backend-phase-6-eval"
pr: "https://github.com/Keshav0375/Sentinel/pull/24"
updated: "2026-11-08"
---

## Summary
Rewrite the eval runner to work against LangFuse datasets (was iterating `data/` scenarios,

## Description
Source: backend task 6.2 (`sentinel-brain/implementation/tasks/backend/phase-6-eval/task-2-eval-runner-datasets.md`).

which are deleted in Phase 9) — run new prompt versions against historical trajectories.

**Files modified:** `src/sentinel/eval/runner.py`
- Pull a LangFuse dataset of past trajectories; re-run the pipeline (or judge) against each; aggregate scores; optional `GET /eval/results` data source (§1.1 route).
- No dependency on `data/scenarios/`.

## Acceptance criteria
- [x] Runner iterates a dataset (fixture offline) and produces aggregate scores; no `data/` reference.
- [x] Feeds the eval results endpoint.

## Outcome
Built commit 063c3d8 on dev/backend-phase-6-eval: "refactor: eval runner scores finished scenario runs from a LangFuse dataset against branches.yaml (#81)". Dataset `sentinel-scenario-runs` (item schema in runner docstring); scores go to a dataset-run trace; runner is read-only (dec 2026-10-22). Files: eval/runner.py, eval/report.py, models/eval_result.py, scripts/run_eval.py, README.md, pyproject.toml/poetry.lock (pyyaml>=6.0.0), tests/test_eval/fixtures/branches.yaml (vendored), tests.
Review fix batch cf56e67 (decisions brain 1ffd083, a85666d): runner persists incidents.eval_score via new eval/score_store.py (best effort; `--no-store` skips); push_item moved off the event loop; pyyaml spec style. Gate on cf56e67: VERDICT GREEN, full run, 7 ran, 0 skipped; boot OK (/health, /ready 200, protected routes 401).
