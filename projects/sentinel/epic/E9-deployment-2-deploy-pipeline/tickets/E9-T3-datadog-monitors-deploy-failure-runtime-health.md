---
key: "E9-T3"
title: "Datadog monitors (deploy-failure + runtime-health)"
epic: "E9"
repo: "Sentinel-deployment"
size: "S"
status: "done"
depends_on: ["E9-T2", "E3-T2", "E3-T3"]
arch_refs: ["deep-dive/08-deployment-and-scenarios.md#8.4", "deep-dive/08-deployment-and-scenarios.md#8.3"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 45, "id": 5694994927, "url": "https://github.com/Keshav0375/sentinel-brain/issues/45"}
branch: "dev/deploy-phase-2-deploy-pipeline"
pr: "https://github.com/Keshav0375/Sentinel-deployment/pull/2"
updated: "2026-11-08"
---

## Summary
The two monitors that turn Datadog signal into a `repository_dispatch`. Defined as code

## Description
Source: deployment task 2.3 (`sentinel-brain/implementation/tasks/deployment/phase-2-deploy-pipeline/task-3-datadog-monitors.md`).

(Datadog Terraform provider OR versioned monitor JSON + apply script — pick one; document).

**Artifacts:**
- `sentinel-deploy-failure` — event monitor on `deploy_status:failed` (Condition C).
- `sentinel-runtime-health` — metric/HTTP monitor: App Service 5xx rate over threshold OR failed synthetic pings to `/` and `/health` (Condition B).
- Both notify the same webhook channel → Event Grid topic (infra 3.2 endpoint+key) → Function → dispatch.
- Monitor hygiene (§6.3): renotify OFF, recovery period, 5-min eval window on runtime monitor.
- **Files:** `datadog/monitors/*.json` (or `*.tf`) + `datadog/README.md` (webhook setup, tag→evidence-class mapping).

## Acceptance criteria
- [x] Both monitors defined as code with the exact trigger conditions (C = deploy_status:failed event; B = 5xx/failed pings).
- [x] Webhook wired to the Event Grid topic; tags let agents distinguish B vs C.
- [x] Hygiene settings applied so demos fire predictably.

## Outcome
Built commit `d5fa824` (feat: add Datadog deploy-failure and runtime-health triggers with apply script). Files: datadog/webhook.json, datadog/monitors/deploy-failure.json, datadog/synthetics/runtime-health-root.json, datadog/synthetics/runtime-health-health.json, datadog/apply.sh, datadog/README.md, tests/test_datadog.py.
Flat webhook body to CustomEventSchema topic (infra PR #17). Synthetics: 2 API tests, aws:ca-central-1, every 5 min, min_failure_duration 300, timeout 60s.
NOT live: estate destroyed, DD_APP_KEY not yet in Sentinel-infra/.env. Unverified: aws:ca-central-1 on US5, JSON-escaping of $EVENT_TITLE, end-to-end chain.
