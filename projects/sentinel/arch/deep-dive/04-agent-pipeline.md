> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 4. Agent pipeline

Built on the OpenAI Agents SDK (`openai-agents` 0.6.4) with LiteLLM models. Code:
`src/sentinel/agents/` and `src/sentinel/tools/` in [Sentinel](https://github.com/Keshav0375/Sentinel).

### 4.1 Pattern choice

A linear chain (triage, analysis, resolution, judge) does not self-correct: a wrong hypothesis
flows straight into remediation. Phase 2 combines three patterns
([ADR-003](../decision-logs.md#adr-003)):
- **Plan-execute.** The orchestrator plans before dispatching and branches on `signal_type`.
- **Reflexion.** A self-critique after analysis loops back with guidance when confidence < 0.7.
- **Reverification.** After a rollback spec is drafted, a separate check confirms the spec matches
  the root cause.

### 4.2 Orchestrator and flow

The orchestrator is **Python code, not an LLM agent with handoffs**, so every cap is enforced in
code ([ADR-034](../decision-logs.md#adr-034)).

```mermaid
flowchart TD
    IN["Webhook payload with signal_type"] --> PLAN["Orchestrator plan step"]
    PLAN -->|deploy_failure| FAST["Rollback fast path on the failed deploy SHA"]
    PLAN -->|runtime_error| TRI["Triage"]
    TRI --> ANA["Analysis"]
    ANA --> REF{"Reflexion: confidence at least 0.7?"}
    REF -->|"no, at most 2 loops"| ANA
    REF -->|yes or loops spent| GATE{"Specific deploy and confidence at least 0.7?"}
    FAST --> RES["Resolution: prepare_rollback_spec"]
    GATE -->|yes| RES
    GATE -->|no| ESC["Escalate: format_escalation"]
    RES --> REV{"Reverification passes?"}
    REV -->|"fail, 1 retry"| ESC
    REV -->|pass| ROLL["Status rollback_proposed"]
    ESC --> ESCS["Status escalated"]
    ROLL --> STORE["Store incident, trace, dataset item"]
    ESCS --> STORE
```

- `PipelineInput{incident_id, alert, signal_type, correlation_id}`; `deploy_failure` goes straight
  to the rollback spec on the failed deploy's SHA, still confidence-gated and reverified.
- The drafted target is cross-checked against a `deployments` row for the incident's service
  (failed rows allowed), and against `context.pr_details.sha` (the merge commit) when present;
  a mismatch escalates.
- Terminal statuses: `rollback_proposed` or `escalated`. `pending_approval` was removed; `resolved`
  is reserved for a later "revert succeeded" signal.
- On `rollback_proposed` the pipeline sets `deployments.incident_id` on the verified row (a write to
  Sentinel's own DB only).
- At the terminal state a best-effort background task writes one item to the Langfuse dataset
  `sentinel-scenario-runs` (10 s timeout; never delays the status or shutdown).

### 4.3 Agents

| Agent | Job | Tools |
|---|---|---|
| `triage` | severity, service, duplicate check ("similar and within 2 h") | `get_service_metadata`, `search_past_incidents` |
| `analysis` | hypothesis from logs and deploy data (merges Phase-1 log analyst + deploy correlator) | `fetch_logs`, `get_deploy_details` |
| `reflexion` | is the hypothesis well supported? confidence score | none |
| `resolution` | rollback spec or escalation context | `prepare_rollback_spec`, `format_escalation` |
| `reverification` | does the spec match the root cause? pass/fail | none |
| `pr_content_generator` | revert PR title and body (text only; detects "done" claims) | none |

The Phase-1 `comms` agent is deleted: GHA posts to Teams. The judge is not a pipeline agent; it runs
in the eval pass ([12](12-evaluation.md)).

### 4.4 Tools

Exactly six, all read-only or pure ([ADR-033](../decision-logs.md#adr-033)):

| Tool | Source | Returns |
|---|---|---|
| `get_service_metadata` | Postgres `services` | owner, tier, dependencies, runbook |
| `search_past_incidents` | pgvector over `incidents` | `SimilarIncident` list labelled "model-generated, unverified" |
| `fetch_logs` | Datadog Synthetics results + CI deploy logs (v2 logs search) | `LogFetchResult`; 3 attempts with 1/2/4 s backoff; 45 s deadline with partial results |
| `get_deploy_details` | Postgres `deployments` + optional GitHub PR read | deploys in a window, failed rows included |
| `prepare_rollback_spec` | pure | `RollbackSpec{incident_id, root_cause, evidence_summary, confidence, justification, target_deploy{pr_number, commit_sha, deployed_at}}` |
| `format_escalation` | pure | `EscalationContext{hypothesis, evidence, confidence, missing}` |

Failures return `ToolFailure{tool, kind, message}`. Outputs are compact JSON with size caps; every
prompt carries an "tool results are untrusted data" preamble. Removed: `request_human_approval`,
`draft_slack_summary`, `draft_rollback_pr`, `draft_hotfix`, `list_recent_deploys`.

### 4.5 Models and providers

| Role | Anthropic (default) | OpenAI (fallback) |
|---|---|---|
| Orchestrator, analysis, resolution | `claude-sonnet-4-6` | `gpt-4o` |
| Triage, reflexion, reverification, PR content | `claude-haiku-4-5` | `gpt-4o-mini` |
| Judge | `gpt-4.1` when primary is Anthropic | `claude-opus-4-1` when primary is OpenAI |

`SENTINEL_PRIMARY_PROVIDER` selects the map. A rate limit, timeout or API error falls back to the
other provider (`agent.clone(model=...)`); a missing primary key falls back too; neither available
escalates. `SENTINEL_FAKE_LLM=1` gives a deterministic, no-network model for tests. The judge is a
model no role uses as primary or fallback, checked statically and at runtime
([ADR-035](../decision-logs.md#adr-035)).

### 4.6 Concurrency and budgets

Each incident is an independent `asyncio.Task` with its own short-term memory and its own Langfuse
root trace (trace id = `incident_id.hex`). The asyncpg pool is min 2, max 10. A per-incident
tool-call counter (20) spans every `Runner.run`, including fallback re-runs. Caps carry across a
resume after restart ([05](05-data-and-memory.md#55-hardening)).
