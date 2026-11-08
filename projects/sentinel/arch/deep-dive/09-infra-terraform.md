> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 9. Infra (Terraform)

Code: [Sentinel/infra](https://github.com/Keshav0375/Sentinel/tree/main/infra) (since infra phase 7;
before that [Sentinel-infra](https://github.com/Keshav0375/Sentinel-infra)). Terraform >= 1.9,
`azurerm ~> 4.0`, `azuread ~> 3.0` (aliased to the identity tenant). Region `canadacentral`.

### 9.1 State and bootstrap

- Remote state in Azure Storage in an out-of-band resource group `rg-sentinel-bootstrap`; backend
  `use_azuread_auth` + `use_oidc`; blob lease locking. State can never delete itself.
- One-time bootstrap scripts, idempotent: `bootstrap-state.sh` (state account and container) and
  `bootstrap-identities.sh` (the four CI managed identities and their federated credentials; it
  deletes stale credentials such as the retired `plan-pull-request` subject).
- `docs/BOOTSTRAP.md` is the ordered runbook. After an apply, `grant-db-access.sh` (human Entra
  admin) creates the in-database roles Terraform cannot (`pgaadauth_create_principal_with_oid`, bound
  by object id), and `seed-vault.sh` seeds secrets with `--expires +90d`.

### 9.2 Modules

| Module | Resource | Notes |
|---|---|---|
| `naming` | CAF prefixes + `uid = substr(sha1("<subscription>-<deployment>-<env>"), 0, 4)` | deterministic, never typed; `deployment` capped at 8 characters (Key Vault's 24-character limit) |
| `acr` | Container Registry Standard | free under the 12-month grant (Basic would have billed) |
| `postgresql` | Flexible Server B1MS, PG 16, pgvector | Entra-only (`password_auth_enabled = false`); two direct Entra admins (human user, backend UAMI); firewall open in dev; `shared` or `dedicated` mode |
| `keyvault` | Key Vault, RBAC authorization | 7-day soft delete, purge protection off; Officer (Terraform) / User (readers) split; holds no generated state |
| `event-grid` | custom topic + subscription | Datadog webhook in; batch defaults declared to avoid perpetual diffs |
| `functions` | Y1 Function apps: bridge and rotator | bridge stamps `signal_type` and dispatches; rotator writes a new secret version on `SecretNearExpiry`; system-assigned identity with KV read |
| `app-service` | F1 Linux plan + web app | `always_on = false`, 32-bit worker; `DD_SERVICE=sentinel-watchtower` |
| `aks` | Free-tier AKS, 1x `Standard_B2pls_v2` (ARM64) | OIDC issuer + workload identity; Cilium network policy; Terraform ignores node-count drift |
| `managed-redis` | Azure Managed Redis Balanced B0 | private endpoint, Entra auth, no access keys (phase 11) |

### 9.3 Layers and workspaces

Two Terraform states per estate, as a safety property ([ADR-028](../decision-logs.md#adr-028)):

- **Platform** (`platform.tf`, workspace per region): the shared ACR, **one** AKS cluster and the
  shared Postgres server. The regional quota is 6 vCPU and a node is 2, so one cluster per
  deployment would stop at three.
- **Deployment** (`deployment.tf`, workspace per `<deployment>-<env>`): reads the platform through a
  read-only `terraform_remote_state` (it needs the OIDC issuer and ACR login server and must be unable
  to change them). Destroying a deployment cannot touch the cluster.
- `var.layer` gates modules by `count`. `azure/config/deployment-config.yaml` carries size and detail
  (`defaults:` plus per-deployment exceptions), because `workflow_dispatch` takes at most 10 inputs
  and the stack has about 40 knobs; the form carries only shape and intent.

### 9.4 Per-deployment layer and toggles

Components: `keyvault`, `database` (`shared` = a database and an Entra role on the platform server;
`dedicated` = its own server, about 8 min to create), `functions`, `event_grid`, `app_service`,
`namespace`, `redis`. Preconditions enforce the dependency graph in seconds (`functions` and
`event_grid` are a pair; `functions` needs `keyvault`; `redis` needs `namespace`).

The `namespace` component creates the K8s namespace `<deployment>-<env>` with a mandatory
ResourceQuota (one backend pod), LimitRange, NetworkPolicy, the ServiceAccount `sentinel-backend`,
and a per-namespace UAMI with a federated credential on
`system:serviceaccount:<namespace>:sentinel-backend`. Entra matches that subject exactly with no
wildcard, so a pod in one namespace cannot mint a token for another deployment's Key Vault.

Root outputs include `app_name`, `app_url`, `deployment_resource_group`, `database_name`,
`database_host`, the ACR login server, KV URI and the backend UAMI client id.

### 9.5 Infra CI

- **Validate & Plan:** `fmt -check`, `init -backend=false`, `validate` on every push (no Azure);
  `plan` only on `pull_request` and `push main` (the subjects that exist) under `gha-plan`.
- **Deploy:** `apply` or `destroy` from `workflow_dispatch` inputs alone, behind
  `environment: production` / `environment: destroy` (required reviewer on destruction, a typed
  confirmation matching the deployment name). Destroy purges the soft-deleted vault so
  destroy-then-recreate works.
- **Pause/Resume** (`gha-ops`): `az aks stop/start`, Postgres stop/start. Compute charges stop; disks,
  storage, the LB and ACR continue; Postgres auto-restarts after 7 days. Shipped but never executed.
- **Runners:** the CI runner image (`ci-images/`, python:3.12-slim + Azure CLI + ruff/pyright/pytest)
  built and pushed to ACR; the first push is manual (ACR bootstrap circularity).
- Owner decision: the Python quality gate does not run in infra CI; `tflint`, `shellcheck` and
  `gitleaks` run locally through the gate, not on infra PRs ([ADR-027](../decision-logs.md#adr-027)).

### 9.6 Preflight, verify and destroy

A plan cannot prove an apply will succeed, so `preflight.sh` checks what a plan cannot see: both
tenants minting tokens, global name availability, soft-deleted vaults holding a name, AKS SKU
availability and permission, regional vCPU and F1 quota, provider registration, and Postgres being
awake (a stopped Postgres makes plan fail; a stopped AKS does not). `verify-estate.sh` proves a
destroy-all left only `rg-sentinel-bootstrap` (and `NetworkWatcherRG`). Before destroy, the memory
backup runs and fails closed ([05](05-data-and-memory.md#55-hardening)).

Lessons from the live lifecycle (infra phase 6): identical run names, a false-alarm verify, unseen F1
quota, a PR plan that tried to create its workspace, an unguarded apply against a missing platform,
and a destroy deadlock (Postgres `2BP01`) when the Entra admin was dropped concurrently with the
database it owns. All fixed and proven in production the same day.

### 9.7 Monorepo

Infra phase 7 (PR #32, 2026-10-25) imported `Sentinel-infra` into `Sentinel/infra/` with
`git subtree add` (38 commits kept). Workflows moved to the root as `infra_*.yml` with
`working-directory: infra`, `infra/**` path filters and their own concurrency groups; backend
workflows ignore `infra/**`. The environments `plan`, `production`, `destroy`, `ops` and the infra
variables were recreated on `Sentinel`; federated subjects become
`repo:Keshav0375/Sentinel:environment:<env>` once the owner re-runs `bootstrap-identities.sh` and
sets `INFRA_OIDC_READY=true`.
