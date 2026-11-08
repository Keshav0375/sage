---
key: "E13-T5"
title: "get_deploy_details → PostgreSQL + GitHub API"
epic: "E13"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E11-T2", "E13-T1"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 64, "id": 5694997977, "url": "https://github.com/Keshav0375/sentinel-brain/issues/64"}
branch: "dev/backend-phase-3-tools"
pr: "https://github.com/Keshav0375/Sentinel/pull/21"
updated: "2026-11-08"
---

## Summary
Rewrite `get_deploy_details` / `list_recent_deploys` to query the `deployments` table +

## Description
Source: backend task 3.5 (`sentinel-brain/implementation/tasks/backend/phase-3-tools/task-5-deploy-checker.md`).

enrich with GitHub API (PR/commit) — this is the deploy↔incident correlation source.

**Files modified:** `src/sentinel/tools/deploy_checker.py`
- Input `DeployQuery{service, window_hours}` → Output list of `DeployRecord{pr_number, commit_sha, author, deploy_status, deployed_at, files_changed, ...}`.
- Postgres query "what deployed to this service in the last N hours?"; optional GitHub API enrichment via `github_api_token`.
- Read-only; structured errors; async.

## Acceptance criteria
- [x] Returns recent deploys for a service ordered by time; failed deploys included (they're the correlation targets).
- [x] GitHub enrichment optional + mockable; read-only; typed.

## Outcome
Built (commit 453e1d2, `refactor: get_deploy_details reads deployments from Postgres with optional GitHub PR enrichment`): get_deploy_details is the single LLM-visible name (list_recent_deploys retired). Read-only Postgres query (window/limit bounded, failed rows included, no incident_id backfill). Optional read-only GitHub PR enrichment: GET only, repo from services.metadata.repo, capped at 5, failure does not fail the tool, token never output. ToolDeps drops scenario and gains pool; main.py no longer loads scenarios in the pipeline; eval runner takes pool.
Files: tools/deploy_checker.py, models/tools.py, tools/registry.py, agents/deploy_correlator.py, prompts/deploy_correlator.txt, main.py, eval/runner.py, dashboard/index.html, tests.
Follow-up: DeployCorrelation output still uses the Phase-1 Deploy model (phase 4).
Tests/gate: 36 tests incl. pipeline's verbatim INSERT; gate VERDICT GREEN (7 ran, 1667 tests).
