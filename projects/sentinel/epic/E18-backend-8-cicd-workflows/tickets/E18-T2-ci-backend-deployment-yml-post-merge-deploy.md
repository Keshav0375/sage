---
key: "E18-T2"
title: "ci_backend_deployment.yml (post-merge deploy)"
epic: "E18"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E17-T3", "E17-T2"]
arch_refs: ["deep-dive/07-backend-hosting-and-ci.md#7.4", "deep-dive/07-backend-hosting-and-ci.md#7.2", "deep-dive/07-backend-hosting-and-ci.md#7.3"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 88, "id": 5695001540, "url": "https://github.com/Keshav0375/sentinel-brain/issues/88"}
branch: "dev/backend-phase-8-cicd"
pr: "https://github.com/Keshav0375/Sentinel/pull/27"
updated: "2026-11-08"
---

## Summary
Post-merge: build+push (immutable sha tag), scale up AKS, sync secrets, deploy, validate,

## Description
Source: backend task 8.2 (`sentinel-brain/implementation/tasks/backend/phase-8-cicd/task-2-ci-backend-deployment.md`).

run all tests + smoke against the LIVE deployment, promote or `rollout undo`, scale to zero.
In the `sentinel-backend` concurrency group.

**Files created:** `.github/workflows/ci_backend_deployment.yml` — name `[sentinel] backend — deployment`; `push: main` (paths src/tests/pyproject/Dockerfile/azure/.github/actions); `concurrency: sentinel-backend`.
- Jobs (§9.2): `run-quality` → `build-and-push` (sha tag, no latest) → `deploy-to-aks` (secret sync §8.2, `backend-up` → `backend-url`, `kubectl set image`, rollout, validate `/health`+`/ready`) → `run-tests` (unit + integration + smoke POST canned incident to `{backend-url}/webhooks/incident`) → `promote-or-rollback` (`if: always()`: green → tag `stable` + ACR cleanup keep-3; red → `rollout undo` + notify-teams; always → `backend-down` unless KEEP_WARM).

## Acceptance criteria
- [x] Validates; immutable sha tag only (no `latest` in hot path); rollback on any post-deploy failure; scale-to-zero teardown.
- [x] Smoke test asserts incident stored + resolution/escalation + judge score present.

## Outcome
Built `ci_backend_deployment.yml`: build, deploy, live smoke, promote or rollback, scale down. sha tags only; `stable` via imagetools; ACR cleanup keeps 3 + stable + running; undo + Teams on red; keep-warm teardown. Smoke checks only that the eval_score key exists (live pipeline doesn't score, per 6.1). Commit 5c187a3. Files: workflow, tests/test_infra/test_workflow_deployment.py (30 tests). Gate: VERDICT GREEN on e0e8335 (full run, 7 ran, 0 skipped); boot OK (/health, /ready 200; protected routes 401). Not verified live (B1 + infra CI-identity ticket).
Review fixes 0402b8e, 7b82bfe (2026-10-24): Smoke test uses the GUID-first audience list; backend-up requires the audience GUID first (7b82bfe); summary falls back on a blank outcome; shared .github/actions/resolve-stable-tag. All actions pinned by SHA (tests/test_infra/test_workflow_hardening.py). Gate: VERDICT GREEN on 7b82bfe (full run, 7 ran, 0 skipped); boot OK (/health, /ready 200; protected routes incl. rollback-spec 401). Decisions: 29edfa7, 8b72023, 61178fa, e1cdbf0. Status stays done-pending-review.
