> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 3. System context and boundaries

### 3.1 Repos and the control plane

| Repo | Role | Runs on |
|---|---|---|
| [Keshav0375/Sentinel](https://github.com/Keshav0375/Sentinel) | The backend: agents, tools, memory, API, eval, the backend CI/CD, the ops dashboard (`dashboard-web/`) and, since infra phase 7, the Terraform (`infra/`) | AKS, one replica, cluster stopped between runs |
| [Keshav0375/Sentinel-deployment](https://github.com/Keshav0375/Sentinel-deployment) | The target app `sentinel-watchtower`, its deploy pipeline, the Datadog monitors and the 30 scenario branches (ground truth and eval set) | Azure App Service F1 |
| [Keshav0375/Sentinel-infra](https://github.com/Keshav0375/Sentinel-infra) | The Terraform repo for infra phases 1-6; read-only backup since the monorepo move, archived after the first infra plan run from `Sentinel` | GitHub Actions + Terraform |
| `sentinel-brain` (control plane) | Architecture, decision log, tracker, task specs and reports, the Claude Code agents and skills, the board mirror. No application code | Local + the GitHub project board |

`Sentinel-deployment` stays a separate repo on purpose: it is the monitored target, and its scenario
branches and revert PRs are the human gate; merging it into the monorepo would break that model.

### 3.2 End-to-end flow

1. A human merges a scenario branch PR on `Sentinel-deployment`. `ci_app_deployment.yml` builds,
   deploys to App Service, verifies, and records a `deployments` row (success or failure) in
   Postgres with an Entra token.
2. Datadog fires one of two monitors: `sentinel-deploy-failure` (event tagged `deploy_status:failed`,
   case ii) or `sentinel-runtime-health` (synthetics on `GET /` and `GET /health`, case iii).
   A clean deploy (case i) fires neither.
3. The Datadog webhook posts to an Event Grid topic; the bridge Function classifies the payload,
   stamps `signal_type` (`deploy_failure` or `runtime_error`) and a `correlation_id`, and sends
   `repository_dispatch` to `Sentinel`.
4. `ci_incident_response.yml` brings the backend up, fetches service metadata, PR details and
   Datadog logs in parallel, and posts the enriched payload to `POST /webhooks/incident` with an
   Entra bearer token.
5. The orchestrator branches on `signal_type`, runs the agents, and ends `rollback_proposed` (with a
   rollback spec) or `escalated`.
6. GHA reads the rollback spec, asks the backend to draft the PR text, opens the revert PR on
   `Sentinel-deployment` with a scoped PAT, notifies Teams, records the PR on the incident row,
   and scales the backend back down. A human merges or closes the revert PR.

Sequence diagrams: [04-1](04-1-key-flows.md).

### 3.3 Trust boundaries

| Edge | Mechanism | Never |
|---|---|---|
| GitHub Actions to Azure | OIDC federated credentials on user-assigned managed identities, subject per environment | a stored Azure client secret |
| Caller to backend API | Entra v2 bearer token, app role `Incident.Write`, validated against the identity tenant's JWKS | a shared API token |
| Backend pod to Azure | AKS workload identity: Entra tokens for Key Vault and Postgres | a K8s Secret with app credentials |
| Pipeline to Postgres | Entra token as the password; Postgres is Entra-only | a DB password |
| Backend to the world | read-only tools; the backend never writes to GitHub, Datadog or Azure | a merge, deploy or revert |
| GHA to `Sentinel-deployment` | `REVERT_PR_PAT`, fine-grained, that repo only, Contents + PRs RW, 90 days; `main` requires a PR | auto-merge or approval |
| Dashboard | static public site; allow-listed, summary-only data | raw logs, tool output or secrets |

Detail: [09-1](09-1-identity-plane.md), [10](10-security-and-hitl.md).

### 3.4 External services

| Service | Used for | Auth |
|---|---|---|
| Anthropic / OpenAI | agent LLM calls (Anthropic default, OpenAI fallback) and the judge | keys in Key Vault, read once at startup by the pod |
| Datadog (US5) | deploy events and logs, synthetics, the two monitors, the webhook | API key (pipeline), scoped app key `logs_read_data` + `synthetics_read` (backend) |
| Langfuse Cloud | traces, prompt management, scores, the eval dataset | public/secret keys in Key Vault |
| Microsoft Teams | notifications (GHA only; the backend never notifies) | webhook URL in Key Vault |
| GitHub | `repository_dispatch`, PR read for `get_deploy_details`, revert PR creation (GHA), Pages | bridge PAT (dispatch), read-only PAT (backend), `REVERT_PR_PAT` (GHA) |
