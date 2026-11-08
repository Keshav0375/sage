---
key: "E9-T2"
title: "ci_app_deployment.yml (Build→Deploy→Verify→Record→Summary)"
epic: "E9"
repo: "Sentinel-deployment"
size: "S"
status: "done"
depends_on: ["E8-T1", "E9-T1"]
arch_refs: ["deep-dive/08-deployment-and-scenarios.md#8.2"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 44, "id": 5694994763, "url": "https://github.com/Keshav0375/sentinel-brain/issues/44"}
branch: "dev/deploy-phase-2-deploy-pipeline"
pr: "https://github.com/Keshav0375/Sentinel-deployment/pull/2"
updated: "2026-11-08"
---

## Summary
The core pipeline. Fires on push to main; every stage reports to Datadog; the record stage

## Description
Source: deployment task 2.2 (`sentinel-brain/implementation/tasks/deployment/phase-2-deploy-pipeline/task-2-ci-app-deployment.md`).

writes the `deployments` row that backend correlation depends on.

**Files created:** `.github/workflows/ci_app_deployment.yml` — name `[deployment] deploy — build and ship`; `push: [main]`; env DD_SITE/DD_SERVICE/DD_ENV.
- **Stage 1** metadata: PR_NUMBER, SHORT_SHA, PR_TITLE, `APP_VERSION=pr-<n>-<sha>`.
- **Stage 2** build zip (app/ + requirements.txt); on failure → `dd-report` `stage:build deploy_status:failed`.
- Job declares `environment: sentinel-dev`; `permissions: id-token: write, contents: read`; `concurrency: deploy-sentinel-dev` (no cancel).
- **Stage 3** deploy: `azure/login@v2` (OIDC as `gha-app`), `az webapp config appsettings set APP_VERSION`, `az webapp deploy --type zip`, against `vars.AZURE_RG` / `vars.APP_NAME`; on failure → dd-report `stage:deploy`.
- **Stage 4** verify: sleep 30, retry `/health` ×3, `/version` == APP_VERSION; on failure → dd-report `stage:verify`.
- **Stage 5** record (`if: always()`, `continue-on-error: true`, `id: record`): **inline** (R13) — `az account get-access-token --resource-type oss-rdbms` → `psql` as `vars.PG_USER` on `vars.PG_HOST`/`vars.PG_DATABASE`, INSERT into `deployments` (service, pr_number, commit_sha, author, deploy_status, gha_run_id, files_changed jsonb, metadata{failed_stage,version}) with **every value a `psql -v` variable** (never string-built SQL). `incident_id` NULL. Record failure → dd-report `stage:record`, never changes `deploy_status`.
- **Stage 6** summary (`if: always()`): dd-report final event + structured `deploy.completed` log (§3.1 payload).
- Config (§3.4, environment `sentinel-dev`): secrets AZURE_CLIENT_ID/TENANT_ID/SUBSCRIPTION_ID, DD_API_KEY; vars AZURE_RG, APP_NAME, DEPLOYED_APP_URL, PG_HOST, PG_DATABASE, PG_USER, DD_SITE.

## Acceptance criteria
- [x] Workflow validates; Build→Deploy→Verify→Record→Summary present; failure paths report per §3.1.
- [x] Record stage runs `if: always()` (failed deploys recorded) and writes all `deployments` columns.
- [x] Uses OIDC as `gha-app` (no client secret); inline SQL with `psql -v` variables only.
- [x] **No** required status check on `main` (decision 2026-10-05 — post-merge workflow can't gate a PR; scenario branches must merge).
- [x] `STATUS` is `succeeded` | `failed` — the same value for the Datadog tag and `deployments.deploy_status`.

## Outcome
Built `ci_app_deployment.yml` (build, deploy, verify, record, summary) in Sentinel-deployment, commit `cc3dba6`.
Files: `.github/workflows/ci_app_deployment.yml`, `.github/scripts/{deploy-metadata,deploy-status,set-env}.sh`, `tests/test_deploy_scripts.py`.
Each report step is gated on its own stage outcome; login runs `if: always()` so failed builds are recorded. STATUS is `succeeded|failed`; record failures report `stage:record` without `deploy_status:failed`. appsettings set uses `--output none`.
Not run live (estate destroyed). Deployments-row check deferred to backend 1.3 (R12). Limitation: if checkout fails, the local dd-report action is unavailable and nothing is reported.
**Gate:** VERDICT GREEN, 5 ran (ruff-lint, yamllint, actionlint, gitleaks, pytest), none n/a; tree clean, attribution none. 34 tests (PR#/title parsing, files JSON, STATUS folding, payload, GITHUB_ENV injection).
