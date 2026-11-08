---
key: "E18-T4"
title: "ci_backend_scale.yml (scale toggle + nightly)"
epic: "E18"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E17-T3"]
arch_refs: ["deep-dive/07-backend-hosting-and-ci.md#7.3"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 90, "id": 5695001834, "url": "https://github.com/Keshav0375/sentinel-brain/issues/90"}
branch: "dev/backend-phase-8-cicd"
pr: "https://github.com/Keshav0375/Sentinel/pull/27"
updated: "2026-11-08"
---

## Summary
Manual up/down toggle + nightly auto-down safety net for scale-to-zero (§8.5 rule 4).

## Description
Source: backend task 8.4 (`sentinel-brain/implementation/tasks/backend/phase-8-cicd/task-4-ci-backend-scale.md`).

**Files created:** `.github/workflows/ci_backend_scale.yml` — name `[sentinel] backend — scale`; `workflow_dispatch` (input `direction: up|down`) + nightly cron `0 2 * * *` (down).
- `up` → `backend-up` (outputs URL for the session); `down` → `backend-down`.
- Nightly always scales to zero (forgotten KEEP_WARM costs at most one night).

## Acceptance criteria
- [x] Validates; dispatch up/down works; nightly cron scales to zero; uses the shared actions.

## Outcome
Built `ci_backend_scale` workflow: manual up/down toggle plus nightly scale-to-zero cron; cron always scales down, never stops the cluster. Commit e0e8335. Files: workflow, tests/test_infra/test_workflow_scale.py (21 tests). Gate: VERDICT GREEN on e0e8335 (full run, 7 ran, 0 skipped); boot OK (/health, /ready 200; protected routes 401). Not verified live (B1 + infra CI-identity ticket).
Review fixes 0402b8e, 7b82bfe (2026-10-24): Uses the shared .github/actions/resolve-stable-tag for the stable lookup. All actions pinned by SHA (tests/test_infra/test_workflow_hardening.py). Gate: VERDICT GREEN on 7b82bfe (full run, 7 ran, 0 skipped); boot OK (/health, /ready 200; protected routes incl. rollback-spec 401). Decisions: 29edfa7, 8b72023, 61178fa, e1cdbf0. Status stays done-pending-review.
