> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 8. Deployment target and scenario branches

Code: [Keshav0375/Sentinel-deployment](https://github.com/Keshav0375/Sentinel-deployment).

### 8.1 The app

`sentinel-watchtower`, a deliberately minimal FastAPI app on App Service F1 (always free). The
pipeline is the product; the app exists to be broken.

| Route | Returns |
|---|---|
| `GET /` | JSON with `message: "ok"` |
| `GET /health` | `{"status": "ok"}` |
| `GET /version` | the deployed version `pr-<N>-<sha>` |

A fixed startup log line is a contract. Every dependency is pinned `==` (gunicorn included) so the
only thing that changes what is installed is a scenario branch; dev tools live in
`requirements-dev.txt`, never deployed. `sentinel-watchtower` is the logical service name used as the
Datadog `service` tag, `deployments.service` and every monitor filter, deliberately decoupled from the
Azure resource name `app-<dep>-<env>-<uid>` ([ADR-030](../decision-logs.md#adr-030)).

### 8.2 Deploy pipeline

`ci_app_deployment.yml` runs on push to `main` only, and only for `app/**`, `requirements.txt`, the
workflow, `dd-report` and `.github/scripts/**` (a docs-only merge would report a false failure).
Stages: build (zip, refuses symlinks), deploy (`az webapp deploy --track-status` as `gha-app`),
verify (`/health`, `/version`), record (Entra DB token, `psql -v` values; `continue-on-error`),
summary. The `dd-report` composite action posts Datadog events and logs (US5 via `DD_SITE`),
fail-soft. One status vocabulary: `succeeded | failed | rolled_back`.

Merge gate: `main` requires a PR and the `sentinel-dev` environment allows only `main`, so only
merged code can mint a `gha-app` token. There is no required status check: deliberately broken
`deployfail/*` branches must stay mergeable.

### 8.3 The 30 scenario branches

The app is real ground truth: each branch is a self-contained change to `app/**` or
`requirements.txt` with a fixed label in `scenarios/branches.yaml` (fields `branch`, `case`, `fault`,
`expected_signal_type`, `expected_resolution`, `expected_failed_stage`, `also_expected`,
`expected_culprit`). A scenario runs by merging its branch through a PR; its merge is reverted before
the next one.

| Case | Branches | Pipeline | App | Signal | Expected |
|---|---|---|---|---|---|
| i clean | `pass/01..10` | green | healthy | none | no incident (true negative) |
| ii deploy fails | `deployfail/01..10` | red | previous version (build/Oryx failure) or broken/down (verify or startup failure; F1 has no slots) | `deploy_failure` | rollback |
| iii runtime | `runtime/01..10` | green | live and broken | `runtime_error` | rollback or escalate |

Determinism rules ([ADR-031](../decision-logs.md#adr-031)): F1 has a 60 CPU-min daily quota and
unloads after about 20 idle minutes; synthetics send only `GET /` and `GET /health`. So a runtime
fault must make one of those fail persistently; "after N minutes" faults anchor to the deploy
(package mtime), never to process uptime; Terraform-owned settings (start command, env, port) are
excluded. Dropped as untestable: load, payload, intermittent and uptime-relative faults, latency under
60 s, the random 60 s lifespan sleep.

Examples: `deployfail/03` pins `fastapi==0.0.0` (Oryx failure, previous version live);
`deployfail/07` is a syntax error (app fails to start, `also_expected: [runtime_error]`);
`runtime/01` returns 500 on `GET /`; `runtime/07` makes `/health` return 503 once more than 10 min
after the deploy; `runtime/08` returns `text/plain`; `runtime/09` returns `{"message":"error"}` with 200.
`expected_culprit` is `self` for cases ii-iii, bound at run time to the merge's `pr-<N>-<sha>`, so a
revert PR is scored against exactly the merge it should target.

### 8.4 Datadog monitors and the bridge

| Monitor | Type | Fires on | Case |
|---|---|---|---|
| `sentinel-deploy-failure` | event monitor | an event tagged `deploy_status:failed` | ii, `deploy_failure` |
| `sentinel-runtime-health` | two Synthetics API tests | `GET /` status 200, `content-type` contains `application/json`, `$.message == "ok"`; `GET /health` status 200; every 30 min, one retry after 60 s | iii, `runtime_error` |

The first live run used 5-minute synthetics; they cold-started gunicorn all day, pushed the app into
`QuotaExceeded` and made the next deploy fail with a Kudu 403: the monitor broke the thing it watched.
Monitors and the webhook are applied locally by the owner with `datadog/apply.sh` (the app key never
enters CI). The webhook posts to Event Grid; the bridge Function stamps `signal_type` and dispatches
`repository_dispatch` to `Sentinel` ([09](09-infra-terraform.md#92-modules)).
