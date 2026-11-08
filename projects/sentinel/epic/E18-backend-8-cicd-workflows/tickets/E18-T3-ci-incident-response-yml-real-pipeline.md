---
key: "E18-T3"
title: "ci_incident_response.yml (real pipeline)"
epic: "E18"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E17-T3", "E15-T1", "E15-T3"]
arch_refs: ["deep-dive/07-backend-hosting-and-ci.md#7.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 89, "id": 5695001680, "url": "https://github.com/Keshav0375/sentinel-brain/issues/89"}
branch: "dev/backend-phase-8-cicd"
pr: "https://github.com/Keshav0375/Sentinel/pull/27"
updated: "2026-11-08"
---

## Summary
The real incident pipeline — the payoff workflow. `repository_dispatch: incident-alert`,

## Description
Source: backend task 8.3 (`sentinel-brain/implementation/tasks/backend/phase-8-cicd/task-3-ci-incident-response.md`).

scale-to-zero, serialized. Backend reasons, GHA executes (§9.3).

**Files created:** `.github/workflows/ci_incident_response.yml` — name `[sentinel] incident — response pipeline`; `repository_dispatch [incident-alert]`; `permissions: id-token/contents`; `concurrency: sentinel-backend`.
- Jobs (§9.3 DAG): `ensure-backend-up` (backend-up → `backend-url`; failure → Teams "NOT processed" + fail loudly) → parallel `fetch-service-info`/`fetch-pr-details`/`fetch-datadog-logs` (each OIDC + own KV secret; outputs non-secret, truncated) → `run-agent-pipeline` (POST `/webhooks/incident` + poll 10-min cap → timeout degrades to escalation) → branch: rollback (`generate-pr-content` → `create-rollback-pr` on Keshav0375/Sentinel-deployment + psql UPDATE incidents pr_number/pr_url → `notify-rollback`) OR `notify-escalation` → `teardown-backend` (`if: always()`, skip on KEEP_WARM) → `summary` (Datadog event + Teams).
- Respect §13.6: each job = fresh VM; no secrets across job outputs.

## Acceptance criteria
- [x] Validates; DAG matches §9.3; rollback + escalation branches correct; teardown always; timeout → escalation (never silent hang).
- [x] `create-rollback-pr` targets `Keshav0375/Sentinel-deployment` (R1); records pr_number/pr_url via psql-exec.

## Outcome
Built incident response workflow and `GET /incidents/{id}/rollback-spec` (serves persisted trajectory.pipeline_result spec; no migration). `scripts/incident_dispatch.py` (stdlib). REVERT_PR_PAT only in create-rollback-pr; `git revert -m 1`; no merge/approve/auto-merge. Commit 4e5db70. Files: src/sentinel/api/incidents.py, scripts/incident_dispatch.py, workflow, tests (~82: 10 API, 49 script, 24 workflow). Gate: VERDICT GREEN on e0e8335 (full run, 7 ran, 0 skipped); boot OK (/health, /ready 200; protected routes 401). Not verified live (B1 + infra CI-identity ticket).
Review fixes 0402b8e, 7b82bfe (2026-10-24): record-rollback-pr is a separate job gated on the PR URL; summary always reports the PR; persist-credentials false, env-only push auth with --force-with-lease to revert-<sha>, open PR reused on re-run; curl --max-time/--connect-timeout; poll fails fast on 4xx (60 s 404 grace), retries 5xx; summary Teams step runs if !cancelled(); severity and dd_event_id mapped, Teams deduped; shared resolve-stable-tag. All actions pinned by SHA (tests/test_infra/test_workflow_hardening.py). Gate: VERDICT GREEN on 7b82bfe (full run, 7 ran, 0 skipped); boot OK (/health, /ready 200; protected routes incl. rollback-spec 401). Decisions: 29edfa7, 8b72023, 61178fa, e1cdbf0. Status stays done-pending-review.
