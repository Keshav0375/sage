# r1: MVP planning revisions and reconciliations

Research note for sentinel. Source: `sentinel-brain/implementation/history.md` (change log, closed
blockers, resolved R-items), `implementation/STATE.md`, `architecture/decisions.md`. Summarised; ids
redacted.

## Planning revisions

| Rev | Date | What changed |
|---|---|---|
| (rounds) | 2026-06-29 to 07-12 | MVP architecture written in the `Sentinel` repo on `planning/phase-2-e2e` (PRs #9-#13): three repos, agent loops, Postgres, Langfuse, AKS, the PR as the human gate |
| rev-5 | 2026-07-12 | Security and ground-truth overhaul: Entra-only Postgres, Key Vault rotation, backend Entra app and AKS workload identity, `ci_destroy_infra`, 30 scenario branches replace demo PRs, inbound Entra bearer. Several existing task bodies superseded and flagged |
| rev-6 | 2026-07-26 | Build-loop repair: phases branch from `release-phase-2` with a `dev/` prefix; the branch-convention and source-guard checks accept it (previously every phase PR would have failed two checks) |
| rev-7 | 2026-07-26 | Control plane split into `sentinel-brain`; code repos carry code and CI only; POC docs quarantined in an archive behind a hook and a permission deny rule; tracker commits straight to brain `main`; `reports/` added |
| rev-8 | 2026-07-26 | Per-repo branch model (infra and deployment merge into their own `main`; backend keeps a release train); `planning/phase-2-e2e` retired (PR #14); build agents moved to Opus |
| rev-9 | 2026-08-15 | Identity plane rebuilt on managed identities after discovering the subscription sits in a university tenant with no directory rights; region `canadacentral`; conflicts C1-C9 resolved before any code |
| phases 5-6 | 2026-08-24 | Static estate replaced by a dynamic multi-deployment platform (14 new tasks) |
| post-release | 2026-10-25 | Monorepo, ops dashboard, memory hardening, in-cluster eval as owner tickets |

## Architecture conflicts resolved before code (C-items)

Surfaced by `architecture-warden` (distill) against infra phase 1; all would have produced broken or
unverifiable infra. Highlights: the resource group became a data source (C1); the state account
needed a blob data role and the backend needed `use_azuread_auth` + `use_oidc`, without which every CI
`terraform init` fails (C2); all five bootstrap objects imported, not one (C3); `GITHUB_PAT` renamed
`GH_PAT` because GitHub reserves the prefix (C6); `AZURE_*` are variables, not secrets (C7); versions
pinned (C9); the gate's `actionlint` failed every repo without workflows (C13, fixed in `Sentinel`
PRs #15/#16).

## Reconciliations (R-items, decisions the owner owed)

| R | Item | Resolution |
|---|---|---|
| R1, R2 | Placeholder GitHub owner and repo casing | `Keshav0375`, exact casing (OIDC subjects are case-sensitive) |
| R3 | Region | `canadacentral` (proximity, residency, less burstable-SKU contention); `var.location` has no default |
| R4 | The API app registration needs a directory write the school tenant denies | two-tenant split ([ADR-022](../../../arch/decision-logs.md#adr-022)) |
| R5 | CI identity could not create role assignments | RBAC Administrator, later replaced by three identities |
| R6 | CI cannot purge a soft-deleted vault | teardown local and Owner-run, later CI destroy behind its own environment |
| R7 | No OIDC identity for `Sentinel-deployment` | fourth identity `gha-app` |
| R8 | Cross-repo secret distribution | `push-deploy-config.sh` under the operator's `gh` auth |
| R9 | Stale names in `deployment.md` | rewritten to `vars.*` from infra outputs |
| R10 | What is the service identity? | `sentinel-watchtower` |
| R11 | App URL and name not root outputs | new outputs |
| R12 | Pipeline Postgres access | `gha-app` DB principal; the backend migration grants on `deployments` |
| R13 | Cross-repo composite actions missing | SQL inlined in the deploy workflow |
| R14 | LLM token and cost capture | custom add-only Langfuse generation bridge, no I/O |

## Blockers

Closed: B1 subscription, B2 state, B3 CI identity, B6 Datadog, B7 Langfuse, B8 Teams, B9 PAT
(superseded), B10 Postgres admins, B11 personal tenant, B12 AKS workload identity, B13-B14 branch
setup, B15 gate defect, B16 identity-tenant CI (its earlier "granted" record was a false positive:
the service principal had no directory role at all). Open: B4 Anthropic key, B5 OpenAI key.
