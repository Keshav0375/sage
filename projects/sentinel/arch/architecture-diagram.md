# sentinel: architecture diagram

> Part of [architecture](architecture.md) · deep-dive index: [deep-dive/README.md](deep-dive/README.md)

The full flow of Sentinel Phase 2 in one picture. Each component node ends with the number of the
deep-dive file that holds its detail; the table below maps node, file and ADRs.

```mermaid
flowchart TB
    HUMAN(["Human reviewer 10"])
    subgraph depRepo["Sentinel-deployment repo"]
        SCEN["30 scenario branches 08"]
        APPWF["ci_app_deployment.yml 08"]
        REVPR["Revert PR, the human gate 10"]
    end
    subgraph azure["Azure estate, resource tenant"]
        APP["App Service F1, sentinel-watchtower 08"]
        EG["Event Grid topic 09"]
        BRIDGE["Bridge Function stamps signal_type 09"]
        subgraph aks["AKS, one ARM64 node, stopped when idle"]
            BE["Backend FastAPI 06"]
            ORCH["Orchestrator and six agents 04"]
            JOB["Eval Job 12"]
        end
        PG[("Postgres B1MS, pgvector, Entra-only 05")]
        REDIS[("Managed Redis B0 05")]
        KV[("Key Vault per deployment 09-1")]
        ACR[("ACR 09")]
        BLOB[("Backup blob outside the estate 05")]
    end
    subgraph idt["Identity tenant"]
        APIAPP["API app registration, Incident.Write 09-1"]
    end
    subgraph senRepo["Sentinel repo"]
        INCWF["ci_incident_response.yml 07"]
        DEPLOYWF["ci_backend_deployment.yml 07"]
        EVALWF["ci_eval.yml 12"]
        INFRAWF["infra_* workflows 09"]
        LEDGER[("ops-ledger branch 11")]
        RECON["ops_reconcile.yml 11"]
    end
    DD["Datadog US5: events, logs, synthetics, monitors 08"]
    LF["Langfuse: traces, prompts, scores, dataset 11"]
    LLM["Anthropic default, OpenAI fallback 04"]
    TEAMS["Microsoft Teams 03"]
    PAGES["Ops dashboard on GitHub Pages 11"]

    HUMAN -->|merges scenario PR| SCEN
    SCEN --> APPWF
    APPWF -->|zip deploy as gha-app| APP
    APPWF -->|record deployments row| PG
    APPWF -->|deploy events and logs| DD
    DD -->|synthetics| APP
    DD -->|monitor webhook| EG
    EG --> BRIDGE
    BRIDGE -->|repository_dispatch| INCWF
    INCWF -->|backend-up, Entra bearer| BE
    BE --> ORCH
    ORCH -->|read-only tools| PG
    ORCH -->|fetch_logs| DD
    ORCH --> LLM
    ORCH --> LF
    BE --> REDIS
    BE -->|workload identity| KV
    APIAPP -.->|token audience| BE
    INCWF -->|opens with REVERT_PR_PAT| REVPR
    INCWF --> TEAMS
    REVPR -->|merge or close| HUMAN
    DEPLOYWF -->|image| ACR
    DEPLOYWF --> BE
    EVALWF --> JOB
    JOB --> LF
    JOB --> PG
    INFRAWF -->|terraform apply, destroy, pause| azure
    INFRAWF -->|pre-destroy pg_dump| BLOB
    INCWF -->|ops-event| LEDGER
    RECON --> LEDGER
    LEDGER --> PAGES
```

| Node | Deep-dive | ADRs |
|---|---|---|
| Scenario branches, deploy pipeline, App Service, Datadog monitors | [08](deep-dive/08-deployment-and-scenarios.md) | ADR-018, ADR-030, ADR-031 |
| Event Grid, bridge Function, ACR, infra workflows | [09](deep-dive/09-infra-terraform.md) | ADR-027, ADR-028, ADR-042 |
| Key Vault, API app registration, identities | [09-1](deep-dive/09-1-identity-plane.md) | ADR-014, ADR-016, ADR-021, ADR-022 |
| Backend FastAPI | [06](deep-dive/06-interfaces-and-contracts.md) | ADR-036 |
| Orchestrator and agents, LLMs | [04](deep-dive/04-agent-pipeline.md) | ADR-003, ADR-006, ADR-034, ADR-035 |
| Postgres, Redis, backup blob | [05](deep-dive/05-data-and-memory.md) | ADR-007, ADR-044 |
| Incident, deploy and scale workflows | [07](deep-dive/07-backend-hosting-and-ci.md) | ADR-013, ADR-026, ADR-039 |
| Eval Job and workflow | [12](deep-dive/12-evaluation.md) | ADR-037, ADR-045 |
| Langfuse, ops ledger, reconciler, dashboard | [11](deep-dive/11-observability-and-ops-dashboard.md) | ADR-009, ADR-043 |
| Revert PR, human reviewer | [10](deep-dive/10-security-and-hitl.md) | ADR-004, ADR-005, ADR-010 |
| Teams, external services | [03](deep-dive/03-system-context-and-boundaries.md) | ADR-001 |

Sequence diagrams of the critical flows: [deep-dive/04-1-key-flows.md](deep-dive/04-1-key-flows.md).
