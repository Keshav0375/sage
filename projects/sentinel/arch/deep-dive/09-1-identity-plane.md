> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 9.1 Identity plane (OIDC, Entra, workload identity)

No stored cloud client secret, no shared API token, no DB password. Every trust edge is a
short-lived Entra token stamped for one audience.

### 9.8 Two tenants

The subscription is Azure for Students inside a university tenant where the owner is subscription
Owner but has no directory write rights, and app registration is denied by tenant policy. A managed
identity can hold an app role but never define one, so the API audience needs a tenant the owner
controls ([ADR-021](../decision-logs.md#adr-021), [ADR-022](../decision-logs.md#adr-022)).

| Tenant | Holds |
|---|---|
| Resource (school) tenant | every Azure resource; the CI managed identities; the backend and rotator managed identities |
| Identity (personal) tenant, $0 | exactly two app registrations: the backend API (`Incident.Write` app role, v2 tokens) and the GitHub client app `sentinel-gha-client` |

The client app carries a federated credential trusting GitHub OIDC, the same trust source as the
managed identities, so "no stored credential" survives. Locally, the owner's account is a redeemed
B2B guest with Application Administrator in the identity tenant; CI uses `sentinel-tf-identity`.
New Entra tenants reject bare `api://name` URIs, so the identifier URI includes the tenant id; v2
tokens always carry `aud` = the API app's client-id GUID.

### 9.9 CI identities

User-assigned managed identities in `rg-sentinel-bootstrap` (stable client ids across every
destroy and recreate), each with federated credentials on exact subjects
([ADR-028](../decision-logs.md#adr-028)):

| Identity | Rights | Subjects | Reachable from a PR |
|---|---|---|---|
| `gha-plan` | Reader + state blob read | `pull_request`, `environment:plan` | yes, changes nothing |
| `gha-deploy` | Contributor + RBAC Administrator + KV purge + AKS RBAC Cluster Admin | `environment:production`, `environment:destroy` | no, by construction |
| `gha-ops` | custom role: read + `*/start/action` + `*/stop/action` | `environment:ops` | no |
| `gha-app` | Website Contributor on one App Service; a DB principal with INSERT/SELECT on `deployments` | `repo:Keshav0375/Sentinel-deployment:environment:sentinel-dev` | no (main-only environment) |

A job that declares `environment: X` gets the subject `...:environment:X`, which GitHub never mints
for a `pull_request` event, so `gha-deploy` cannot be reached from a PR with no rule to misconfigure.
RBAC Administrator carries an ABAC condition that forbids assigning Owner, User Access Administrator
or itself, so a leaked token cannot self-promote. Pending: a `gha-backend` identity for the backend
workflows (see [15](15-open-questions.md)).

### 9.10 Token model

| GHA talks to | Audience | How |
|---|---|---|
| Azure control plane | `https://management.azure.com` | `azure/login` (OIDC) |
| Terraform state | `https://storage.azure.com` | backend `use_azuread_auth` |
| Backend API | the API app (identity tenant) | second `azure/login` as `sentinel-gha-client` with `allow-no-subscriptions`, then `get-backend-token` |
| PostgreSQL | `https://ossrdbms-aad.database.windows.net` | `az account get-access-token --resource-type oss-rdbms` |

Identity pointers (`AZURE_CLIENT_ID`, tenant, subscription) are GitHub **variables**, not secrets:
under OIDC they are public identifiers, and masking them hides the subject in `AADSTS700213` errors.

### 9.11 Workload identity (backend pod)

AKS publishes an OIDC issuer; the pod's projected ServiceAccount token federates to the namespace's
UAMI, which mints tokens for Key Vault and Postgres (`DefaultAzureCredential`, refreshed per new DB
connection). No K8s Secret holds app credentials; `automountServiceAccountToken: false`. The AKS
issuer URL is per cluster, so any third-party federation must be registered in the apply path.

### 9.12 Inbound API auth

FastAPI dependency `require_incident_write`: RS256 via `PyJWKClient` on the identity tenant's v2 JWKS;
only the v2 issuer is accepted; `aud` must be in `SENTINEL_API_AUDIENCE` (comma list, client-id GUID
first); bad, expired, wrong-aud or wrong-iss token returns 401; a missing `Incident.Write` role
returns 403. Only `/health` and `/ready` are open. `SENTINEL_DEV_OPEN_DASHBOARD=1` opens dashboard
routes for local use only.

### 9.13 Secrets and distribution

- Key Vault (per deployment): Datadog API and app keys, Langfuse public and secret keys and base URL,
  the Teams webhook, the bridge's GitHub dispatch PAT, and `anthropic-api-key` / `openai-api-key`
  (read once at startup by the pod; GHA never reads the LLM keys). Seeded with a 90-day expiry; the
  rotator re-stamps expiry on every version it writes. Terraform manages rotation infrastructure only,
  never secret values.
- Postgres: Entra-only; roles bound by object id.
- Distribution: Terraform's GitHub provider was removed (phase 5); `set-gh-secrets.sh` and
  `push-deploy-config.sh` push secrets and variables under the operator's own `gh` auth. Values are
  deterministic (derived uid), so they are pushed once.
- Human-held: `REVERT_PR_PAT` (fine-grained, `Sentinel-deployment` only, Contents + PRs RW, 90 days,
  a `sentinel-dev` environment secret) and the backend's read-only PR PAT.
- LLM workload identity federation (Anthropic and OpenAI both support it) was designed in 2026-08 and
  deferred; the shipped design keeps the two LLM keys in Key Vault ([ADR-038](../decision-logs.md#adr-038)).
