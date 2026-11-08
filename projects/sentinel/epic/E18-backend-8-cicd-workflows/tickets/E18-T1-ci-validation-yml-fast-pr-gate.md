---
key: "E18-T1"
title: "ci_validation.yml (fast PR gate)"
epic: "E18"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E17-T1"]
arch_refs: ["deep-dive/07-backend-hosting-and-ci.md#7.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 87, "id": 5695001402, "url": "https://github.com/Keshav0375/sentinel-brain/issues/87"}
branch: "dev/backend-phase-8-cicd"
pr: "https://github.com/Keshav0375/Sentinel/pull/27"
updated: "2026-11-08"
---

## Summary
Fast PR gate — quality + single-job build/run/test (no ACR, no AKS, stubbed LLM). **Single

## Description
Source: backend task 8.1 (`sentinel-brain/implementation/tasks/backend/phase-8-cicd/task-1-ci-validation.md`).

runner rule** (§9.1/§13.6): build image, run container, pgvector service, tests all in ONE
job.

**Files created:** `.github/workflows/ci_validation.yml` — name `[sentinel] PR — validation`; `pull_request` to main (paths src/tests/pyproject/Dockerfile/azure).
- `run-quality`: ruff check + `ruff format --check` + `pyright src/`.
- `build-and-test` (needs run-quality; service pgvector/pgvector:pg16): docker build (local, no push) → `docker run` with local DB + `SENTINEL_FAKE_LLM=1` → poll `/health`+`/ready` → `pytest test_tools+test_models` (unit) → `pytest test_agents+test_api` (integration) → teardown (`if: always()`).
- Can use the ACR ci-runner image as `container:` once available (infra 4.2) — optional.

## Acceptance criteria
- [x] Validates under actionlint; single-job build/run/test; no ACR/AKS/external calls; FAKE_LLM deterministic; ~3–5 min.

## Outcome
Built `ci_validation.yml` PR gate (PRs into main and release-phase-2; read-only, no cloud, arm64 runner; one job: build, migrate, run, probe, pytest; always-teardown). `guard-main-source.yml` head_ref injection fixed via env (one documented shellcheck SC2254 disable). Commit 69efed0. Files: .github/workflows/ci_validation.yml, guard-main-source.yml, tests/test_infra/test_ci_validation_workflow.py (16 tests). Gate: VERDICT GREEN on e0e8335 (full run, 7 ran, 0 skipped); boot OK (/health, /ready 200; protected routes 401). Not verified live (B1 + infra CI-identity ticket).
Review fixes 0402b8e, 7b82bfe (2026-10-24): PR gate now runs tests/test_scripts + tests/test_infra with a pinned, checksum-verified actionlint; timeout-minutes set; ci.yml pinned too. All actions pinned by SHA (tests/test_infra/test_workflow_hardening.py). Gate: VERDICT GREEN on 7b82bfe (full run, 7 ran, 0 skipped); boot OK (/health, /ready 200; protected routes incl. rollback-spec 401). Decisions: 29edfa7, 8b72023, 61178fa, e1cdbf0. Status stays done-pending-review.
