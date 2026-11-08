> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 7. Backend hosting and CI/CD

### 7.1 Image

Multi-stage Dockerfile: the builder installs main dependencies from `poetry.lock` (torch from the CPU
wheel index); the runtime is `python:3.12-slim` pinned by `@sha256` digest with the venv, `src/`,
`alembic/` and `alembic.ini`. Built for `linux/arm64` (the only small AKS SKUs allowed in the region
are ARM64) on native `ubuntu-24.04-arm` runners. Non-root; the embedding model is baked in, pinned
by `revision=` and run offline; uvicorn with `--timeout-graceful-shutdown`. Tags are immutable
`sha-<7>`; `stable` is promoted after a green live test; nothing pulls `latest`.

### 7.2 Kubernetes manifests (`azure/k8s/`)

- Namespace `sentinel-dev` and ServiceAccount `sentinel-backend` (with the workload-identity client-id
  annotation) are owned by infra Terraform; the backend ships no ServiceAccount manifest.
- Deployment: `replicas: 1`, `serviceAccountName: sentinel-backend`, label
  `azure.workload.identity/use: "true"`, `automountServiceAccountToken: false`,
  `readOnlyRootFilesystem: true` with emptyDir for `/app/reports` and `/tmp`,
  `terminationGracePeriodSeconds: 45`.
- Service type LoadBalancer (public IP, dev); NetworkPolicy allows TCP 8000 to the backend under Cilium.
- ConfigMap only; no K8s Secret. Manifests carry `${VAR}` placeholders filled by `backend-up` from
  Terraform outputs; every value is validated (no quotes or newlines, per-field patterns); the
  action applies the manifests bundled with its pinned SHA, never the caller's workspace.
- No `imagePullSecrets`: the kubelet identity holds AcrPull.
- The eval Job manifest lives in `azure/k8s/jobs/`, outside `backend-up`'s glob.

### 7.3 Scale-to-zero lifecycle

A system node pool cannot scale below one node (found live 2026-08-23), so the original
"node pool 0 to 1" design was impossible. The shared cluster is started when stopped
(`backend-up`) and the backend is torn down per run (`backend-down`: delete the Service, scale to 0);
stopping the cluster is a separate manual or pause operation. There is no static backend URL: it is
resolved from the cluster each run and passed as a job output. Safety rails: one concurrency group
`sentinel-backend` (no cancel-in-progress), teardown `if: always()`, `SENTINEL_KEEP_WARM` for demos,
nightly scale-down at 02:00 UTC.

### 7.4 Workflows

| Workflow | Repo | Trigger | Does |
|---|---|---|---|
| `ci_validation.yml` | Sentinel | `pull_request` | read-only PR gate: build, migrate, run, probe, pytest, pinned and checksum-verified actionlint; no environment, no `id-token`, no secrets |
| `ci_backend_deployment.yml` | Sentinel | push to `main` | build and push, deploy to AKS, live smoke (GUID-first audience), promote `stable` or `rollout undo`, scale down |
| `ci_incident_response.yml` | Sentinel | `repository_dispatch` | the real pipeline ([04-1](04-1-key-flows.md#47-runtime-error-full-incident-response)) |
| `ci_backend_scale.yml` | Sentinel | manual up/down + nightly | scale toggle and safety net |
| `ci_eval.yml` | Sentinel | manual | eval as a K8s Job ([12](12-evaluation.md#123-in-cluster-eval)) |
| `ops_reconcile.yml`, `ops_pages.yml`, `ci_web.yml` | Sentinel | schedule, `workflow_run`, main | dashboard ledger, Pages, web e2e + Lighthouse |
| `infra_validate_plan`, `infra_deploy`, `infra_pause`, `infra_runners` | Sentinel (`infra/`) | push/PR, dispatch | Terraform ([09](09-infra-terraform.md#95-infra-ci)) |
| `ci_app_deployment.yml` | Sentinel-deployment | push to `main` on app paths | build, deploy, verify, record, Datadog |
| `guard-main-source.yml` | Sentinel | PR into `main` | allow only `dev/*` and `fix/*` heads |

Rules: workflow names `[repo] scope — description`, files `ci_`-prefixed; every third-party action
pinned by commit SHA; every job that runs `azure/login` declares `environment: sentinel-dev`;
checkouts using `REVERT_PR_PAT` set `persist-credentials: false`; path filters include
`poetry.lock`, `alembic/**`, `scripts/**`, `.github/**`; ACR cleanup keeps the 3 newest `sha-` tags
plus the ones behind `stable` and the running Deployment. Until the CI identity exists, the deploy,
incident and scale workflows skip cleanly (PR #30); infra cloud jobs wait for `INFRA_OIDC_READY`.

### 7.5 Branch model

- During the MVP build, backend phases branched from `release-phase-2` and merged back into it; infra and
  deployment phases merged straight into their own `main`.
- 2026-10-25: `main` backed up as `main-backup`; `release-phase-2` merged into `main` with a merge
  commit (PR #29); `release-phase-2` frozen as the MVP record.
- After the release: work branches from `main` and PRs into `main`: `dev/<cat>-phase-<M>-*` for
  phase work, `fix/*` for out-of-phase repairs. `main` is protected (PR required).
