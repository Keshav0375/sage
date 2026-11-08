> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 0. The POC (proof of concept) and the pivot to the MVP

The POC is dead. The MVP replaced it layer by layer; nothing in the POC is a design input any more.
This file describes the POC only from what the MVP architecture and decision log say about it
(the POC design documents are quarantined and were not used for this port).

### 0.1 What the POC was

Built in May 2026 in the `Sentinel` repo (PRs #1 to #8, branch `ai/tasks`): a local, single-process
multi-agent incident responder on the OpenAI Agents SDK.

| Layer | POC |
|---|---|
| Data | SQLite (`data/sentinel.db`, `infra/db.py`, `aiosqlite`) seeded from JSON |
| Signal | 10 synthetic scenarios (`data/scenarios/*.json`) with hard-coded logs, deploys and alerts, produced by `src/sentinel/generator/` (alert, log and deploy generators) |
| Services | 8 fictional "acme-corp" services in `service_map.json`, `dependency_graph.json`, `runbooks.json` |
| Agents | a linear chain: triage, log analyst, deploy correlator, remediation, comms, judge |
| Tools | included `request_human_approval`, `draft_slack_summary`, `draft_rollback_pr`, `draft_hotfix`, `list_recent_deploys`; 15 tool calls per incident |
| HITL | an approval tool plus an `approve_hitl` endpoint (`/approvals`) inside the backend |
| Execution | the backend drafted and owned the actions itself |
| Hosting | local (`scripts/demo.py`, `scripts/run_scenario.py`), a FastAPI dashboard with a live SSE view |
| Auth | none (later a shared static `X-Sentinel-Token`) |
| LLMs | Groq primary (Llama), Gemini backup |
| Eval | `scripts/run_eval.py` over the synthetic scenario set |

### 0.2 Why it was replaced

The planning round of June-July 2026 (PRs #9 to #14, titled "Planning of transition from phase 2 <- MVP" at the time; today's POC and MVP)
found that the POC demonstrated agent plumbing but nothing a reviewer could trust:

- **Fake ground truth.** Every log, deploy and alert was authored next to its expected answer, so a
  correct diagnosis proved little. There was no real system to break and no real signal.
- **The agent acted on its own approval.** An approval tool inside the same process that drafts the
  action is not a human gate.
- **No identity or secret story.** Local only, no auth, static keys.
- **Linear chain, no self-correction.** A wrong analysis flowed straight into remediation.
- **Model choice.** Free-tier models were chosen for cost; decision quality matters more for a
  portfolio system ([ADR-006](../decision-logs.md#adr-006)).
- **Self-grading.** The default judge model was the triage model.

### 0.3 What the MVP changed

| Concern | POC | MVP | ADR |
|---|---|---|---|
| Store | SQLite | Azure PostgreSQL B1MS + pgvector, Alembic | [ADR-007](../decision-logs.md#adr-007) |
| Signal | synthetic JSON | 30 real scenario branches deployed to App Service and watched by Datadog | [ADR-018](../decision-logs.md#adr-018) |
| Human gate | approval tool | the revert PR on `Sentinel-deployment` is the gate | [ADR-005](../decision-logs.md#adr-005), [ADR-010](../decision-logs.md#adr-010) |
| Who acts | backend executes | backend reasons, GitHub Actions executes | [ADR-004](../decision-logs.md#adr-004) |
| Hosting | local | AKS single replica, stopped between runs | [ADR-012](../decision-logs.md#adr-012), [ADR-026](../decision-logs.md#adr-026) |
| Auth | none | Entra bearer on the API, OIDC for CI, workload identity for the pod | [ADR-014](../decision-logs.md#adr-014), [ADR-016](../decision-logs.md#adr-016) |
| Agents | linear chain | Python orchestrator with plan-execute, reflexion, reverification | [ADR-003](../decision-logs.md#adr-003), [ADR-034](../decision-logs.md#adr-034) |
| Models | Groq / Gemini | Anthropic default, OpenAI fallback, judge distinct from every agent model | [ADR-006](../decision-logs.md#adr-006), [ADR-035](../decision-logs.md#adr-035) |
| Observability | in-process | Langfuse traces, prompts and scores; Datadog signal; ops dashboard | [ADR-009](../decision-logs.md#adr-009), [ADR-043](../decision-logs.md#adr-043) |
| Infra | none | Terraform, two layers, two tenants, four CI identities | [ADR-028](../decision-logs.md#adr-028) |

### 0.4 Migration and cleanup

The MVP build kept the POC running until the replacements were proven, then deleted it
(backend phase 9, [E19](../../epic/E19-backend-9-cleanup-and-e2e/epic.md)):

1. Add the new dependencies; create the asyncpg pool next to the old SQLite module.
2. Alembic and the initial schema; rewrite memory, then the tools one by one, then the orchestrator.
3. Add Langfuse; only then delete `data/`, `generator/`, `infra/db.py`, the demo scripts, the
   SSE route, the POC models and `aiosqlite`.
4. Dockerfile without `data/`; K8s manifests; composite actions; the four CI workflows.

`scripts/run_eval.py` survived: phase 6 rewrote it as the Langfuse-backed eval CLI. `/api/scenarios`
was re-pointed at the real catalog (a vendored copy of `Sentinel-deployment/scenarios/branches.yaml`).

Code: [Keshav0375/Sentinel](https://github.com/Keshav0375/Sentinel) · the pre-release `main` is
kept as `main-backup`.
