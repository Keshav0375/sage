# sentinel: architecture

Binding (as ported). Top-down view of Sentinel MVP (built as Phase 2): an autonomous DevOps incident-response agent
across three code repos, where Datadog detects a failure, a multi-agent pipeline diagnoses it, and the
result is a revert PR or an escalation that a human reviews. It restates what the deep-dive files and
ADRs decide and adds nothing. Map: [architecture-diagram.md](architecture-diagram.md). Detail:
[deep-dive/README.md](deep-dive/README.md). Decisions: [decision-logs.md](decision-logs.md)
(ADR-001 to ADR-045). Status: [state.md](state.md). Beyond the MVP: [path-to-production.md](path-to-production.md). Build order: [../epic/plan.md](../epic/plan.md).
Source of truth: the `sentinel-brain` control plane (`architecture/`, `implementation/`, `reports/`).

## 1. Goal and Keshav's decisions
Automate the mechanical first half of incident response (notice, correlate to a deploy, read the logs,
decide rollback vs escalate, write it up) and stop before acting. Credibility comes from real ground
truth (a real app with 30 labelled failure branches), a human gate by construction, no stored cloud
secrets, self-correcting agents with caps in code, and near-zero idle cost. The POC (a local SQLite,
synthetic-data proof of concept) was replaced wholesale by the MVP.
Detail: [00](deep-dive/00-poc-and-the-pivot-to-mvp.md), [01](deep-dive/01-context-and-goals.md). ADRs: ADR-001, ADR-018, ADR-022.

## 2. Quality targets
Infra about $0 at idle, LLM about $5-12/month (+ Redis B0 about $13 while up); cold start 3-7 min +
1-3 min for the LB IP; pipeline timeout 600 s; 20 tool calls per incident, reflexion at most 2,
reverification retry at most 1, confidence gate 0.7; worst-case shutdown 37 s under a 45 s grace;
eval checks 0/1 and judge dimensions 0-1, `judge_conflict` runs never counted.
Detail: [02](deep-dive/02-quality-attributes.md), [13](deep-dive/13-cost.md). ADRs: ADR-013, ADR-026, ADR-034.

## 3. System context
`Sentinel` (backend, CI/CD, dashboard, and `infra/` since the monorepo move), `Sentinel-deployment`
(target app + scenario branches, kept separate because it is the monitored target and its revert PRs
are the gate), `Sentinel-infra` (Terraform for infra phases 1-6, now a read-only backup), and the
`sentinel-brain` control plane (architecture, tracker, agents; no app code). External: Anthropic,
OpenAI, Datadog US5, Langfuse Cloud, Microsoft Teams, GitHub.
Detail: [03](deep-dive/03-system-context-and-boundaries.md). ADRs: ADR-001, ADR-020, ADR-042.

## 4. How an incident flows
A human merges a scenario PR; `ci_app_deployment.yml` deploys and records a `deployments` row; Datadog
fires `deploy_failure` (deploy red) or `runtime_error` (synthetics fail); Event Grid and the bridge
Function stamp `signal_type` and `correlation_id` and send `repository_dispatch`;
`ci_incident_response.yml` brings the backend up, fetches context in parallel and posts the webhook with
an Entra bearer; the orchestrator returns `rollback_proposed` (with a rollback spec) or `escalated`; GHA
opens the revert PR with a scoped PAT, notifies Teams, records the PR on the incident and scales down.
Detail: [03](deep-dive/03-system-context-and-boundaries.md) §3.2, [04-1](deep-dive/04-1-key-flows.md). ADRs: ADR-004, ADR-010.

## 5. Agent pipeline
A Python orchestrator (not an LLM with handoffs) branching on `signal_type`: `deploy_failure` takes a
rollback fast path; `runtime_error` runs triage, analysis, reflexion (loop while confidence < 0.7, at
most 2), a decision gate, resolution, reverification. Six LLM agents, six read-only or pure tools.
Anthropic Sonnet/Haiku by role with OpenAI fallback; the judge is a model no role uses.
Detail: [04](deep-dive/04-agent-pipeline.md). ADRs: ADR-003, ADR-006, ADR-033, ADR-034, ADR-035.

## 6. Data and memory
Azure Postgres B1MS (Entra-only) with pgvector: `incidents` (episodic), `services` (semantic),
`deployments` (deploy to incident to PR correlation), plus `incident_checkpoints` and `cache_entries`.
A `correlation_id` chain links alert, deploy, incident, trace and revert PR. Hardening: fail-closed
pre-destroy backup and data-only restore, one bounded resume after restart, a tool/LLM cache, Azure
Managed Redis B0 for hot state.
Detail: [05](deep-dive/05-data-and-memory.md). ADRs: ADR-007, ADR-008, ADR-044.

## 7. Interfaces
Bearer-protected FastAPI (`/webhooks/incident`, `/incidents*`, `/incidents/{id}/rollback-spec`,
`/generate/pr-content`, `/api/scenarios`, `/api/eval-report`), open probes, the dispatch mapping, and
seven SHA-pinned composite actions shared across repos.
Detail: [06](deep-dive/06-interfaces-and-contracts.md). ADRs: ADR-036, ADR-039.

## 8. Backend hosting and CI/CD
One replica on AKS (one ARM64 node, cluster stopped when idle), ConfigMap only, workload identity, no
static URL; four backend workflows (PR gate, deploy, incident, scale), plus eval, dashboard and infra
workflows; one `sentinel-backend` concurrency group; keep-warm for demos and a nightly scale-down.
Detail: [07](deep-dive/07-backend-hosting-and-ci.md). ADRs: ADR-012, ADR-013, ADR-026, ADR-038, ADR-039.

## 9. Deployment target and ground truth
`sentinel-watchtower` on App Service F1; push-only deploy pipeline with an Entra-token record stage;
30 deterministic scenario branches (10 clean, 10 deploy-failure, 10 runtime) labelled in
`scenarios/branches.yaml`, which is also the eval set; two Datadog monitors.
Detail: [08](deep-dive/08-deployment-and-scenarios.md). ADRs: ADR-018, ADR-030, ADR-031.

## 10. Infra and identity
Terraform with per-resource modules, a platform layer (shared ACR, one AKS, shared Postgres) and a
per-deployment layer in separate states joined by read-only remote state; CAF naming with a derived uid;
preflight; apply, destroy and pause from workflow inputs. Two tenants (resources vs the API app
registrations), four CI managed identities split by PR reachability, audience-scoped tokens everywhere.
Detail: [09](deep-dive/09-infra-terraform.md), [09-1](deep-dive/09-1-identity-plane.md). ADRs: ADR-014, ADR-017, ADR-021, ADR-022, ADR-028.

## 11. Security and HITL
No backend tool modifies external state; the revert PR is the only gate and no workflow can merge it;
caps in code; R14 keeps raw tool and log data out of every external store; least-privilege identities
and DB grants; SHA-pinned supply chain.
Detail: [10](deep-dive/10-security-and-hitl.md). ADRs: ADR-004, ADR-005, ADR-010, ADR-016, ADR-034.

## 12. Observability, dashboard and eval
Langfuse traces, prompt management, scores and the `sentinel-scenario-runs` dataset; Datadog as the
signal; a public observe-only ops dashboard on GitHub Pages backed by an append-only git ledger;
a read-only eval runner, run in-cluster under the backend's workload identity.
Detail: [11](deep-dive/11-observability-and-ops-dashboard.md), [12](deep-dive/12-evaluation.md). ADRs: ADR-009, ADR-037, ADR-043, ADR-045.

## 13. Delivery
21 build phases (infra 1-7, deployment 1-3, backend 1-11), 83 tasks, all merged by 2026-10-30; the MVP
release merged `release-phase-2` into `main` on 2026-10-25 (PR #29). Built by the `/implement-phase`
agent DAG under per-phase human sign-off. Nothing has run live end to end yet.
Detail: [../epic/plan.md](../epic/plan.md), [15](deep-dive/15-open-questions.md). Stack: [14](deep-dive/14-tech-stack.md).

## 14. Path to production
The MVP is not production. Multi-tenancy, HA, TLS and private networking, a GitHub App, dashboard SSO,
CODEOWNERS and change windows, SLOs, spend caps, retention, DR drills and eval gates are listed, and
not built, in [path-to-production.md](path-to-production.md).
