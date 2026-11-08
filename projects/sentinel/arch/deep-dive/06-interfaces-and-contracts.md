> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 6. Interfaces and contracts

### 6.1 HTTP API (FastAPI, `src/sentinel/api/`)

| Route | Auth | Purpose |
|---|---|---|
| `POST /webhooks/incident` | bearer + `Incident.Write` | start a pipeline; 202 `{incident_id, correlation_id, status}`; duplicate `correlation_id` returns the original id with `status: "duplicate"` |
| `GET /incidents` | bearer | list (limit <= 200), `incidents` columns without the embedding |
| `GET /incidents/{id}` | bearer | one incident (in-flight served from short-term memory) |
| `GET /incidents/{id}/trajectory` | bearer | status-only timeline |
| `GET /incidents/{id}/deploy` | bearer | the `deployments` row linked to the incident |
| `GET /incidents/{id}/rollback-spec` | bearer + `Incident.Write` | the drafted `RollbackSpec`; 404 when none (escalated) |
| `POST /generate/pr-content` | bearer + `Incident.Write` | revert PR title and body, text only; 404 unknown incident, 409 target not in `deployments`, 502 on SDK errors |
| `GET /api/scenarios` | bearer | the 30-branch catalog (vendored `branches.yaml`), read-only |
| `GET /api/eval-report` | bearer | the latest eval report |
| `GET /health` | open | exactly `{"status": "ok"}` |
| `GET /ready` | open | 200 `{"status": "ready"}` when wired and the DB pool pings, else 503 |

Removed: `/webhooks/alert`, `/approvals`, the SSE route `GET /events/{incident_id}`, and the
unauthenticated `PUT /api/config` that could repoint models at runtime.

### 6.2 Webhook payload and dispatch mapping

`IncidentPayload` requires `signal_type`, `correlation_id`, `title`; everything else is optional
(`severity` defaults to `"unknown"`; `tags` may be an object or a Datadog comma string). `context`
is pre-fetched by GHA: `service_metadata`, `pr_details{number, sha, author, files_changed, branch}`,
`recent_logs`. `pr_details.sha` is the **merge commit** sha; `pr_details.branch` is eval metadata
only, validated against the catalog and excluded from every agent prompt (it is the ground-truth label).

Bridge `client_payload.{signal_type, correlation_id, event}` maps to `IncidentPayload`
(`title` from `event.title`, `tags` from `event.tags`). The Datadog webhook posts a flat JSON body
(`title`, `tags`, `alert_transition`, `link`, `alert_id`, `date`) to Event Grid.

### 6.3 Rollback spec and PR content

`prepare_rollback_spec` returns the `RollbackSpec` ([04](04-agent-pipeline.md#44-tools)); the
workflow passes it unchanged to `POST /generate/pr-content`, whose body is the same shape plus
`justification`. GHA's `TARGET_SHA` is `target_deploy.commit_sha`; merge commits are reverted with
`git revert -m 1`; the branch pushed is `revert-<sha>`.

### 6.4 Composite actions (`Sentinel/.github/actions/`)

Seven actions, used cross-repo pinned by commit SHA, never `@main`. Callers run `azure/login` (OIDC)
first; inputs reach `run:` only through `env:`; SQL values travel only as `psql -v` variables.

| Action | Does |
|---|---|
| `backend-up` | `az aks start` only if stopped; render and validate the bundled manifests; apply; wait for rollout; resolve the LB IP; output `backend-url` |
| `backend-down` | skipped when `SENTINEL_KEEP_WARM == 'true'`; delete the Service (releases the IP); scale to 0; never stops the shared cluster |
| `get-kv-secrets` | read named secrets from the KV URI (never exports the LLM keys) |
| `get-db-token` | output `pg-token` (`oss-rdbms` audience) |
| `get-backend-token` | output `bearer` for the first (GUID) entry of `SENTINEL_API_AUDIENCE` in the identity tenant |
| `notify-teams` | post a card |
| `psql-exec` | run SQL with a token, values as `psql -v` vars |

Plus `resolve-stable-tag` (map `stable` to its `sha-<7>` tag via the ACR digest) and `ops-event`
(append to the ops ledger, [11](11-observability-and-ops-dashboard.md#113-ops-dashboard)).

### 6.5 Configuration

Pod config is one ConfigMap `sentinel-config` with non-secret values only: `SENTINEL_API_TENANT_ID`
(identity tenant), `SENTINEL_API_AUDIENCE` (comma list, client-id GUID first; required, no default;
unset means every protected route returns 401 and the log says `auth_not_configured`),
`DD_SITE=us5.datadoghq.com`, `KEY_VAULT_URL`, `PGHOST`/`PGDATABASE`/`PGUSER`,
`SENTINEL_PRIMARY_PROVIDER`. Secrets come from Key Vault at startup via workload identity
(Datadog, Langfuse, `anthropic-api-key`, `openai-api-key`); restart to rotate. Locally,
`DATABASE_URL` wins over the Entra `PG*` path. No secret is required to boot; a missing key makes
its feature return a structured failure at use.
