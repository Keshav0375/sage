---
key: "E9-T1"
title: "dd-report composite action"
epic: "E9"
repo: "Sentinel-deployment"
size: "S"
status: "done"
depends_on: []
arch_refs: ["deep-dive/08-deployment-and-scenarios.md#8.2"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 43, "id": 5694994590, "url": "https://github.com/Keshav0375/sentinel-brain/issues/43"}
branch: "dev/deploy-phase-2-deploy-pipeline"
pr: "https://github.com/Keshav0375/Sentinel-deployment/pull/2"
updated: "2026-11-08"
---

## Summary
Local composite action so every pipeline stage calls one Datadog reporter instead of

## Description
Source: deployment task 2.1 (`sentinel-brain/implementation/tasks/deployment/phase-2-deploy-pipeline/task-1-dd-report-action.md`).

copy-pasted curl blocks.

**Files created:** `.github/actions/dd-report/action.yml`
- Inputs: `title`, `text`, `tags` (comma list), `alert-type` (`info|error`), optional `log-payload`, `dd-api-key`, `dd-site` (**required**, no default: the org is on US5 `us5.datadoghq.com`, and a wrong default fails as a silent 403).
- Steps: `send_dd_event` → POST `https://api.${DD_SITE}/api/v1/events`; if `log-payload` set, `send_dd_log` → POST `https://http-intake.logs.${DD_SITE}/api/v2/logs` (§3.2 helper bodies).
- Mask the API key; fail soft (report failures shouldn't break the deploy record).

## Acceptance criteria
- [x] `action.yml` validates under actionlint; inputs match §3.2; key masked.
- [x] Event + log paths both implemented; `dd-site` configurable.

## Outcome
Built `dd-report` composite action. Commit `05d35ce` (Sentinel-deployment, feat: add dd-report composite action for Datadog events and logs).
Files: `.github/actions/dd-report/action.yml`, `.github/actions/dd-report/dd-report.sh`, `.yamllint.yaml`, `tests/test_dd_report.py`.
Key goes to curl via a 0600 header file (never in argv/output); JSON built with jq; `dd-site` required (US5), URLs built from it; `event-id` prefers id_str; fails soft with warnings. First commit d144d9b failed gitleaks on a fake key literal; amended to 05d35ce.
