# sentinel: decision logs (ADRs)

Newest first. Condensed from `sentinel-brain/architecture/decisions.md` (append-only, about 90
entries from 2026-06-30 to 2026-10-28). Each entry: status (date, decided-by), context, decision,
why, what it superseded, the rejected alternative, and what it makes harder later. A superseded ADR
stays, marked `Superseded by ADR-<n>`. "Owner" is Keshav; "orchestrator" is the `/implement-phase`
orchestrator ruling within the architecture.

## ADR-045: Automated eval runs in-cluster

**Status.** Accepted 2026-10-28 (owner, option b; orchestrator amendments).
**Context.** The eval needs the LLM keys, which live only in Key Vault and the pod.
**Decision.** `ci_eval.yml` runs `scripts/run_eval.py` as a Kubernetes Job in `sentinel-dev` under the
backend's workload identity. The namespace quota is one pod, so the eval pauses the backend and
restores it per keep-warm. Reports leave through Job logs; one `eval.scored` event per branch per run.
**Why.** No GHA identity may read the LLM keys.
**Supersedes.** The 2026-10-25 note that a human runs `run_eval.py` (still possible).
**Harder later.** The pending infra CI-identity ticket must grant `batch/jobs` and pod-log RBAC; incidents queue during an eval.

## ADR-044: Agent memory and storage hardening

**Status.** Accepted 2026-10-25 (owner chose all four options); amended 2026-10-28 after the safety review.
**Decision.** A: pre-destroy `pg_dump` to blob storage outside the estate, data-only restore on apply.
B: Postgres checkpoints, one bounded resume after a restart. C: Postgres tool/LLM cache (judge never).
D: Azure Managed Redis Balanced B0 (about $13/month), private, Entra auth, no keys, destroyed with the estate.
Amendments: the backup fails closed; `gha-deploy` is scoped to one database with a column-level UPDATE;
the restore skips checkpoints and closes stale `in_progress` rows as `escalated`; every cap and the
deadline carry across a resume.
**Why.** Memory was lost on every teardown and an in-flight incident stuck after a pod restart.
**Rejected.** Server-wide `pg_read_all_data` / `pg_write_all_data` (the platform server is shared).
**Harder later.** A first recurring cost beyond LLM calls; destroy can now be blocked by a backup error.

## ADR-043: Ops dashboard on an append-only git ledger

**Status.** Accepted 2026-10-25 (owner request; orchestrator design). Built as backend phase 10.
**Decision.** Events from every workflow go to an orphan branch `ops-ledger` (one JSON file per event,
deterministic id); a reconciler backfills from the GitHub API and Langfuse; a static React SPA on
GitHub Pages reads compacted snapshots. Observe-only, allow-listed data, summaries capped at 500 chars.
**Why.** Must survive estate teardown and scale-to-zero, be free, versioned and public-readable.
**Rejected.** The Azure Postgres (destroyed with the estate); an external DB (vendor, secret, API).
**Harder later.** Ledger growth; anything shown publicly must pass the allow-list.

## ADR-042: Phase 2 release, post-release branch model, monorepo

**Status.** Accepted 2026-10-25 (owner).
**Decision.** `main` backed up as `main-backup`; `release-phase-2` merged into `main` with a merge
commit (PR #29) and frozen. New work branches from `main` (`dev/*` phases, `fix/*` repairs).
`Sentinel-infra` comes into `Sentinel` as `infra/` with full history (infra phase 7); `Sentinel-deployment`
stays separate because it is the monitored target and its revert PRs are the gate.
**Supersedes.** The Phase-2 release-train branch model for `Sentinel`; ADR-039's "release-phase-2 as default branch".
**Harder later.** The federated credentials must be re-bound to `Sentinel` by the owner before infra CI runs.

## ADR-041: Backend phase 9 contract (cleanup and end-to-end)

**Status.** Accepted 2026-10-25 (owner answers; amended after review).
**Decision.** `/api/scenarios` serves one vendored copy of `branches.yaml`; the pipeline writes one
Langfuse dataset item at the terminal state (best effort, background, 10 s timeout); the branch label
is forwarded from the PR head ref but never reaches an agent prompt; a narrow R14 exception lets
dataset items carry LLM-written summaries with raw tool output stripped; the SSE route is removed;
`run_eval.py` is kept; the live runbook lives in `sentinel-brain/reports/DEMO.md`.
**Supersedes.** Backend §13.1's deletion of `run_eval.py`; the 2026-10-19 "SSE behind the bearer" line.

## ADR-040: Dated pip-audit exception for filelock

**Status.** Accepted 2026-10-24, extended 2026-10-28 (owner).
**Decision.** Ignore 13 filelock CVEs fixed only in filelock 4.x, because litellm caps filelock `<4.0`.
Re-check by 2026-11-24 and drop the ignores as soon as litellm lifts the cap.
**Harder later.** A known-vulnerable transitive dependency ships until upstream moves.

## ADR-039: Backend CI/CD contract

**Status.** Accepted 2026-10-24 (owner answers; orchestrator rulings).
**Decision.** `release-phase-2` as the live branch until the release; `REVERT_PR_PAT` (fine-grained,
`Sentinel-deployment` only, Contents + PRs RW, 90 days) as an environment secret; a new
`GET /incidents/{id}/rollback-spec` endpoint passed unchanged to `/generate/pr-content`; every action
pinned by SHA; arm64 runners; `pr_details.sha` = the merge commit; `git revert -m 1`; the
`guard-main-source.yml` injection fixed; one pending run per concurrency group accepted.
**Supersedes.** Backend §9.1-§9.3 triggers, `secrets.GH_PAT`, the stale names.
**Harder later.** The CI identity (gha-backend) is a separate infra ticket that gates every live run.

## ADR-038: Container and K8s contract; LLM keys in Key Vault

**Status.** Accepted 2026-10-24 (owner answers; amended after review).
**Decision.** Names come from infra (namespace, ServiceAccount); manifests use validated placeholders;
ConfigMap only, no K8s Secret; grace 45 s; `backend-down` never stops the shared cluster; LLM keys are
Key Vault secrets read once at startup via workload identity; lock-based arm64 image, base by digest.
**Supersedes.** ADR-029's LLM federation deferral; hard-coded resource names in backend §7-§9.
**Harder later.** Key rotation needs a pod restart.

## ADR-037: Eval contract

**Status.** Accepted 2026-10-22 (owner answers; amended after review).
**Decision.** The runner is a read-only scorer of finished trajectories from dataset
`sentinel-scenario-runs`, joined to `branches.yaml`; four 0/1 checks plus judge dimensions, all 0-1;
`incidents.eval_score` JSONB; flags `judge_conflict` / `judge_failed` never aggregated.
**Supersedes.** The 0-5 score models; the `/eval/results` route name.

## ADR-036: API contract (backend phase 5)

**Status.** Accepted 2026-10-19 (owner answers; amended after review).
**Decision.** Entra bearer only; v2 issuer; `SENTINEL_API_AUDIENCE` is a required comma list (client-id
GUID first, because v2 tokens carry the GUID as `aud`); 401 vs 403; only `/health` and `/ready` open;
webhook dedupe on `correlation_id`; `/generate/pr-content` 404/409; `/ready` pings the DB, not the LLMs.
**Supersedes.** `/webhooks/alert`; the bare `api://sentinel-backend` audience.

## ADR-035: Judge model distinct from every agent model

**Status.** Accepted 2026-10-18 (orchestrator). Supersedes the judge rule of ADR-034.
**Context.** The 2026-10-15 rule (judge = the other provider's `gpt-4o`) self-grades: `gpt-4o` is also
the fallback for three roles, so any Anthropic failure had `gpt-4o` scoring `gpt-4o`.
**Decision.** The judge uses a model no role uses as primary or fallback (`gpt-4.1` / `claude-opus-4-1`);
a static check plus a runtime `judge_conflict` guard; no judge fallback.

## ADR-034: Python orchestrator with code-enforced caps; R14 bridge

**Status.** Accepted 2026-10-15 (orchestrator, within the architecture). Judge rule superseded by ADR-035.
**Decision.** The orchestrator is Python code, not an LLM with handoffs: tool-call counter 20 across all
runs, reflexion at most 2, reverification retry at most 1, rollback target cross-checked against
`deployments`. Six agents (comms deleted). Anthropic and OpenAI only. Terminal statuses
`rollback_proposed | escalated`. A custom openai-agents processor bridges generations to Langfuse
without I/O; the vendor's default trace exporter (which uploaded full spans to OpenAI) is removed.
**Why.** An SDK `max_turns` bound does not bound tool calls; caps in prompts are not caps.
**Supersedes.** `pending_approval`; the Groq/Azure/Gemini settings; runtime model repointing.

## ADR-033: Six read-only tools

**Status.** Accepted 2026-10-14 (owner answers; review requirements carried forward).
**Decision.** Exactly six tools (`get_service_metadata`, `search_past_incidents`, `fetch_logs`,
`get_deploy_details`, `prepare_rollback_spec`, `format_escalation`); `ToolFailure` results; `fetch_logs`
reads only what exists (Synthetics results and CI deploy logs; the app sends no runtime logs); compact
JSON; an untrusted-data preamble on every prompt; no secret required to boot.
**Supersedes.** The approval tool and endpoint, Slack and hotfix drafting, `list_recent_deploys`.

## ADR-032: Real service registry, Langfuse v3, Postgres-only memory

**Status.** Accepted 2026-10-10 and 2026-10-12 (orchestrator).
**Decision.** The `services` table holds the one real service `sentinel-watchtower` (fixtures stay in
tests); pin Langfuse v3 and rewrite the tracing contract to its API (W3C trace ids, OTel context,
mandatory prompt fallback); memory takes the asyncpg pool and raises `SentinelMemoryError` when absent;
runbooks live in `services.runbook`; IVFFlat probes set per query.
**Supersedes.** The 8 acme-corp fixtures; the v2 Langfuse API; the SQLite memory path.

## ADR-031: Scenario catalog redesigned for determinism; synthetics every 30 min

**Status.** Accepted 2026-10-07 (owner, deployment phase 3).
**Context.** About half the original faults could not produce their label on the stack as built, and
5-minute synthetics cold-started the F1 app into `QuotaExceeded`.
**Decision.** 30 deterministic, repo-only faults; verify-stage failures leave the broken version live;
`also_expected: [runtime_error]` for two-signal branches; `GET /` asserts content type and body;
synthetics every 30 min with one retry; deploy only on app paths.
**Rejected.** Pipeline auto-rollback (GHA would remediate on its own, breaking HITL).

## ADR-030: Target app identity, gha-app and the record stage

**Status.** Accepted 2026-10-04 and 2026-10-05 (owner; closes R7, R8, R10-R13).
**Decision.** Logical service name `sentinel-watchtower`, decoupled from the Azure resource name;
every app dependency pinned `==`; `expected_culprit` added to the catalog; a fourth CI identity
`gha-app` (Website Contributor on one App Service, a DB principal on `deployments`); SQL inline with
`psql -v` values; the record stage never changes `deploy_status`; no required status check on
`Sentinel-deployment` `main`; monitors applied locally.
**Rejected.** New federated credentials on `gha-deploy` (it can empty the subscription).

## ADR-029: LLM auth by workload identity federation (deferred)

**Status.** Accepted 2026-08-30 as deferred; Superseded by ADR-038.
**Decision.** Anthropic and OpenAI both support workload identity federation; the pod would federate
its projected token instead of shipping a key, with issuer registration in the apply path (the AKS
issuer URL changes on every rebuild). Deferred because no pod existed yet.
**Harder later.** Not zero secrets: one admin key per vendor at apply time; a leftover `*_API_KEY`
env var silently shadows federation.

## ADR-028: Dynamic multi-deployment platform

**Status.** Accepted 2026-08-24 (owner request). Supersedes ADR-023 (R5), ADR-024 (R6), C1 and one cluster per estate.
**Decision.** Deployments are created and destroyed from workflow inputs alone: a config file carries
size and detail (the form allows 10 inputs, the stack has about 40 knobs); one shared cluster with a
namespace per deployment (6 vCPU quota); two Terraform states (platform, deployment) joined by
read-only remote state; three identities split by PR reachability (`gha-plan`, `gha-deploy`, `gha-ops`);
destroy in CI behind its own environment with Key Vault purge; CAF naming with a derived uid; a preflight.
**Why.** Destroy-then-recreate must work; reachability, not scope, is what keeps a public repo's
credentials safe.
**Harder later.** Pause is a 7-day lease (Postgres auto-restarts); old estate destroyed rather than migrated.

## ADR-027: Infra CI is Terraform-only; identity pointers are variables

**Status.** Accepted 2026-08-24 (owner, four pre-build decisions).
**Decision.** The Python quality gate does not run in infra CI; validate jobs need no Azure and plan
runs only on the subjects that exist; `AZURE_*` identifiers are GitHub variables; the identity-tenant
pointers are distributed too.
**Accepted cost.** tflint, shellcheck and gitleaks never run on an infra PR; the gate is a local discipline there.

## ADR-026: AKS on ARM64 B2pls_v2, stop/start

**Status.** Accepted 2026-08-23 (orchestrator, preserving the owner's choice of a small node). Amends ADR-013.
**Context.** The free `B2ats_v2` fails the system-pool RAM floor; `B2s` is not allowed in the region;
every allowed small SKU is ARM64; a system pool cannot scale below one node.
**Decision.** `Standard_B2pls_v2` (2 vCPU, 4 GiB, about $0.03/h); scale-to-zero by `az aks stop/start`;
backend images built `linux/arm64`.

## ADR-025: Infra cost and lifecycle choices

**Status.** Accepted 2026-08-15, ACR reversed 2026-08-16 (owner).
**Decision.** ACR Standard (free under the student grant; Basic would have billed); region
`canadacentral` (R3); Key Vault 7-day soft delete with purge allowed; a systematic name suffix (later
replaced by the derived uid of ADR-028).
**Lesson.** On a subsidised subscription, cheaper SKU and free SKU are different questions.

## ADR-024: Full teardown is owner-run and local

**Status.** Accepted 2026-08-16. Superseded by ADR-028.
**Context.** A soft-deleted vault lives at subscription scope; CI's purge returned 403, silently
swallowed, and the next apply failed on the reserved name.
**Decision.** Remove `ci_destroy_infra.yml`; teardown is a documented local procedure as Owner.
**Rejected.** Subscription-scope Key Vault Contributor for CI.

## ADR-023: CI identity gets RBAC Administrator

**Status.** Accepted 2026-08-15. Superseded by ADR-028.
**Context.** Contributor cannot create role assignments; six were declared in Terraform. Phase 1
passed only because it applied locally as Owner.
**Decision.** RBAC Administrator on the resource group (its ABAC condition forbids granting Owner, UAA or itself).
**Rejected.** Moving role assignments into bootstrap scripts (the RBAC graph would drift out of code).

## ADR-022: Two-tenant identity split

**Status.** Accepted 2026-08-15 (owner: no institutional involvement). Resolves R4.
**Decision.** Every Azure resource stays in the school tenant; exactly two app registrations (the
backend API with `Incident.Write`, and the GitHub client app) live in a personal identity tenant, which
trusts GitHub OIDC through a federated credential.
**Why.** A managed identity can hold an app role but never define one; the school tenant denies app registration.
**Harder later.** Every auth bug starts with "which tenant?"; the CI managed identity cannot hold the app role.

## ADR-021: Identity plane rebuilt on managed identities

**Status.** Accepted 2026-08-15 (owner, option 3 of 4).
**Context.** Owner on the subscription but no directory rights: every Entra app, group and service
principal in the earlier design was unbuildable.
**Decision.** The CI identity is a user-assigned managed identity with federated credentials (child
resources, not directory objects); two direct Postgres Entra admins replace the admin group.
**Rejected.** A self-hosted runner with a system identity (24/7 cost; public-repo PR code execution).

## ADR-020: Control plane split into sentinel-brain; per-repo branch model

**Status.** Accepted 2026-07-26 (owner, rev-7 and rev-8).
**Decision.** Architecture, tracker, agents, skills and reports move out of `Sentinel` into
`sentinel-brain`; code repos carry code and CI only; Phase-1 docs are quarantined in an archive behind
a hook; tracker commits go straight to brain `main`; infra and deployment phases merge into their own
`main`, the backend keeps a release train; build agents move to Opus.
**Why.** Planning documents in a code repo were read as current and caused wrong builds.

## ADR-019: ci_destroy_infra workflow

**Status.** Accepted 2026-07-12. Superseded by ADR-024, then ADR-028.
**Decision.** A manual, typed-confirmation "everything, always" teardown workflow.

## ADR-018: 30 scenario branches replace the demo PRs

**Status.** Accepted 2026-07-12 (owner, rev-5).
**Decision.** Remove `ci_demo_prs.yml`; ship 30 pre-authored branches (10 per case) with a
`branches.yaml` catalog that is both the ground truth and the eval set.
**Why.** Template demo PRs proved nothing; a real deploy that really breaks is real signal.
**Supersedes.** The A/B/C demo-PR taxonomy of 2026-07-04 and template-based demo PRs.

## ADR-017: Dynamic secrets, Azure-native

**Status.** Accepted 2026-07-12 (owner, rev-5).
**Decision.** Postgres Entra-only (token as password, no `db-password`); LLM keys on a Key Vault
rotation policy with a rotator Function.
**Rejected.** HashiCorp Vault (a server to run and secure for a dev estate).

## ADR-016: Inbound auth with Entra bearer tokens

**Status.** Accepted 2026-07-12 (owner, rev-5). Refined by ADR-022 and ADR-036.
**Decision.** Replace the shared `X-Sentinel-Token` with Entra bearer tokens for an API app role
`Incident.Write`, validated against JWKS by a FastAPI dependency.
**Why.** A static shared secret is a standing leak risk.

## ADR-015: Workflow naming and the four backend workflows

**Status.** Accepted 2026-07-04 (owner).
**Decision.** `ci_` prefix, `[repo] scope — description` names; backend workflows: `ci_validation`
(fast PR gate, no ACR), `ci_backend_deployment` (post-merge deploy with promote/rollback),
`ci_incident_response`, `ci_backend_scale`.
**Supersedes.** `ci_backend` + `cd_backend`; `ci_backend_validation`.

## ADR-014: OIDC workload identity federation for CI

**Status.** Accepted 2026-07-04 (owner). Mechanism rebuilt by ADR-021 and ADR-028.
**Decision.** GitHub proves identity with its OIDC JWT; Azure trusts it through federated credentials;
no `AZURE_CLIENT_SECRET` anywhere.

## ADR-013: Scale-to-zero backend, dynamic URL, composite actions

**Status.** Accepted 2026-07-05 (owner). Amended by ADR-026.
**Decision.** The backend idles at zero and is brought up per run by shared composite actions;
the URL is resolved from the cluster each run and the LB Service deleted at teardown ($0 idle);
`SENTINEL_KEEP_WARM` for demos; one concurrency group; nightly safety-net scale-down.
**Why.** The node is the meter; always-on would consume the whole free grant.

## ADR-012: Backend on AKS, single replica

**Status.** Accepted 2026-07-04 (owner). Supersedes ADR-011. Amended by ADR-013.
**Context.** Each GHA job runs on a fresh VM, so a container started in one job is invisible to the next.
**Decision.** A single-replica Deployment on AKS reachable by every job.

## ADR-011: Ephemeral backend inside GitHub Actions

**Status.** Accepted 2026-07-02. Superseded by ADR-012 (unimplementable across jobs).

## ADR-010: HITL is fire-and-forget

**Status.** Accepted 2026-07-04 (owner). Amends ADR-005.
**Decision.** Sentinel's job ends when the revert PR exists and Teams is notified; no merge/close
tracking; the `revert_prs` table is dropped (4 tables to 3); GHA writes `pr_number`/`pr_url` on the incident.

## ADR-009: Langfuse, full integration

**Status.** Accepted 2026-07-01 (owner). API pinned by ADR-032; data rule by ADR-034.
**Decision.** Traces, prompt management with local fallback, judge scores, cost tracking, datasets.

## ADR-008: Correlation chain and the deployments table

**Status.** Accepted 2026-07-01 (owner).
**Decision.** A `deployments` table written by the deploy pipeline on every deploy (failed ones
included), and a `correlation_id` minted at the bridge and carried through every hop.

## ADR-007: PostgreSQL B1MS + pgvector

**Status.** Accepted 2026-07-01 (owner).
**Decision.** Replace SQLite with Azure Postgres (free 12 months) and pgvector; asyncpg; Alembic.

## ADR-006: Anthropic and OpenAI only, models by role

**Status.** Accepted 2026-07-02 (owner). Supersedes ADR-002 and the 2026-07-01 model selection.
**Decision.** Anthropic default, OpenAI fallback; Sonnet for reasoning roles, Haiku for classification
and constrained generation; switch with `SENTINEL_PRIMARY_PROVIDER`.
**Why.** For a portfolio system, decision quality matters more than token cost.

## ADR-005: The HITL gate is GitHub PR review

**Status.** Accepted 2026-07-01 (owner). Amended by ADR-010.
**Decision.** No `/approvals` endpoint; the revert PR on `Sentinel-deployment` is the approval surface.
**Why.** The destructive action is a merge; GitHub already has review, approve and merge.

## ADR-004: Backend reasons, GHA executes

**Status.** Accepted 2026-07-01 (owner).
**Decision.** The backend returns a decision and context; GHA creates the PR and sends notifications;
`draft_rollback_pr` is replaced by `prepare_rollback_spec`.

## ADR-003: Agentic loop patterns

**Status.** Accepted 2026-07-01 (owner).
**Decision.** Plan-execute, reflexion (confidence < 0.7, at most 2 loops) and reverification.
**Why.** A linear chain does not self-correct.

## ADR-002: Groq primary, Gemini backup

**Status.** Accepted 2026-06-30. Superseded by ADR-006.

## ADR-001: Three repos, pipeline as product

**Status.** Accepted 2026-06-30 (owner).
**Decision.** `Sentinel` (backend and orchestration), `Sentinel-deployment` (a deliberately trivial app
whose deploy pipeline generates all Datadog signal), `Sentinel-infra` (Terraform); App Service F1 as the
always-free target; Microsoft Teams for notifications; `Sentinel` is the backend (no separate repo).
**Amended.** ADR-042 brought the infra into `Sentinel/infra/`.
