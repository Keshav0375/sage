# finadvisor: architecture diagram

> Part of [architecture](architecture.md) · deep-dive index: [deep-dive/README.md](deep-dive/README.md)

The full flow of FinAdvisor v2 in one picture. Each component node ends with the deep-dive file (number) that holds its detail; the table below the diagram maps node, file and ADRs. Sources of this picture: the diagrams in `deep-dive/03`, `04`, `04-2` and `07` (one deployed cell shown; the second cell is designed and tested locally, see 07).

```mermaid
flowchart TB
    ADV["Advisor and tenant admin<br/>(browser SPA)<br/>01"]
    subgraph edge["Edge"]
        ALB["External ALB<br/>04"]
        ARMOR["Cloud Armor<br/>04"]
        SPA["SPA bucket (GCS)<br/>04"]
        KONG["Kong fa-gateway<br/>04"]
        VALKEY["Valkey rate-limit counters<br/>04"]
    end
    CELLS["cells.json (signed)<br/>04-2"]
    IDP["Identity Platform<br/>08"]
    subgraph chat["chat-api (Cloud Run)"]
        API["auth, principal, admin<br/>04"]
        AGENT["agent, guardrails, llm<br/>04-1"]
        RETR["retrieval (as_of, hybrid SQL, rerank)<br/>05-1"]
    end
    MARM["Model Armor (flag, fallback)<br/>08"]
    subgraph store["Cloud SQL Postgres 16 + pgvector (RLS)"]
        SQL[("chunks, documents,<br/>versions, answer_cache<br/>05")]
        OUTBOX[("outbox rows<br/>04")]
        DELQ[("deletion_requests,<br/>source_purges (PUBLIC)<br/>05-1")]
        ACLQ[("acl_change_requests<br/>05-1")]
        LEDGER[("erasure_ledger<br/>05-1")]
    end
    subgraph ingest["Ingest path (etl, etl-public)"]
        SRC["Source publishers<br/>03"]
        CONN["Source connectors<br/>04-2"]
        BRONZE[("GCS bronze<br/>04-2")]
        SCAN["Ingest scan and quarantine<br/>04-2"]
        SILVER["Silver worker<br/>04-2"]
        IDX["Indexer (atomic publish)<br/>04-2"]
    end
    subgraph events["Events and analytics"]
        RELAY["outbox-relay (fa-worker)<br/>04"]
        KAFKA["Confluent Kafka + Schema Registry<br/>06"]
        BQSINK["bq-sink<br/>04"]
        BQ[("BigQuery<br/>04")]
    end
    subgraph lifecycle["Lifecycle workers (fa-worker)"]
        EW["erasure-worker<br/>04-2"]
        ACLA["acl-applier<br/>04-2"]
    end
    LF["Langfuse Cloud<br/>09"]
    subgraph egress["LLM egress boundary (US/global)"]
        ANT["Anthropic<br/>08"]
        VOY["Voyage (embed, rerank)<br/>08"]
    end

    ADV -->|"HTTPS"| ALB
    ALB --> ARMOR
    ARMOR -->|"/* static"| SPA
    ARMOR -->|"/v1/* API and SSE"| KONG
    KONG -->|"rate-limit counters"| VALKEY
    KONG -->|"VPC, X-Serverless-Authorization"| API
    API -->|"verify ID token (firebase.tenant)"| IDP
    API -->|"home_cell check, 421 on mismatch"| CELLS
    API --> AGENT
    AGENT -->|"screen input"| MARM
    AGENT --> RETR
    RETR -->|"SQL as fa_app under RLS"| SQL
    RETR -->|"embed query, rerank"| VOY
    AGENT -->|"Messages API stream"| ANT
    AGENT -->|"outbox rows in same tx"| OUTBOX
    AGENT -.->|"masked spans"| LF
    API -->|"admin writes"| ACLQ
    API -->|"erasure requests"| DELQ

    SRC --> CONN
    CONN -->|"bytes by sha256"| BRONZE
    BRONZE --> SCAN
    SCAN -->|"pass"| SILVER
    SILVER --> IDX
    IDX -->|"one tx per document, doc lock"| SQL
    IDX -->|"embed"| VOY
    IDX -->|"tombstone check"| LEDGER

    OUTBOX --> RELAY
    RELAY -->|"produce, idempotent"| KAFKA
    CONN -.->|"events, ids only"| KAFKA
    KAFKA --> BQSINK
    BQSINK --> BQ

    DELQ -->|"poll, SKIP LOCKED"| EW
    EW -->|"pull source_purges, enqueue own requests"| DELQ
    EW -->|"tombstone first"| LEDGER
    EW -->|"physical delete"| SQL
    EW -->|"delete objects"| BRONZE
    EW -->|"batched DML"| BQ
    EW -->|"delete by trace id"| LF
    ACLQ -->|"poll"| ACLA
    ACLA -->|"acl_version bump"| SQL
```

## Node map

| Node | Deep-dive file | ADRs |
|---|---|---|
| Advisor and tenant admin | `deep-dive/01-context-and-goals.md`, `deep-dive/03-system-context-and-boundaries.md` | ADR-010, ADR-032 |
| External ALB, Cloud Armor | `deep-dive/04-components-and-responsibilities.md` (4.1, 4.2) | ADR-012 |
| SPA bucket | `deep-dive/04-components-and-responsibilities.md` (4.4) | ADR-019 |
| Kong fa-gateway, Valkey | `deep-dive/04-components-and-responsibilities.md` (4.3, 4.6), `deep-dive/06-interfaces-and-contracts.md` (6.5) | ADR-011, ADR-023 |
| cells.json | `deep-dive/04-2-source-lifecycle-and-cells.md` (4.24), `deep-dive/07-scaling-failure-modes-and-recovery.md` (7.6) | ADR-031, ADR-033 |
| Identity Platform | `deep-dive/08-security-and-privacy.md` (8.2) | ADR-010, ADR-032 |
| auth, principal, admin | `deep-dive/04-components-and-responsibilities.md` (4.5) | ADR-002, ADR-004, ADR-010 |
| agent, guardrails, llm | `deep-dive/04-1-key-flows.md` (flow 1), `deep-dive/04-2-source-lifecycle-and-cells.md` (4.25, 4.26) | ADR-005, ADR-006, ADR-007, ADR-009, ADR-036 |
| retrieval | `deep-dive/05-1-rls-indexes-versioning-and-deletion.md` (5.6, 5.7) | ADR-004, ADR-008, ADR-015, ADR-027 |
| Model Armor | `deep-dive/08-security-and-privacy.md` (8.6) | ADR-009, ADR-036, ADR-039 |
| Cloud SQL, chunks, answer_cache | `deep-dive/05-data-model-and-storage.md` | ADR-002, ADR-003, ADR-027, ADR-035 |
| outbox rows, outbox-relay | `deep-dive/04-components-and-responsibilities.md` (4.7) | ADR-013 |
| deletion_requests, source_purges, acl_change_requests, erasure_ledger | `deep-dive/05-1-rls-indexes-versioning-and-deletion.md` (5.11) | ADR-022, ADR-029, ADR-030 |
| Source publishers, Source connectors | `deep-dive/03-system-context-and-boundaries.md`, `deep-dive/04-2-source-lifecycle-and-cells.md` (4.15) | ADR-026 |
| GCS bronze, Ingest scan and quarantine | `deep-dive/04-2-source-lifecycle-and-cells.md` (4.15, 4.25) | ADR-014, ADR-034, ADR-036 |
| Silver worker, Indexer | `deep-dive/04-2-source-lifecycle-and-cells.md` (4.16, 4.17) | ADR-014, ADR-027, ADR-028, ADR-035 |
| Confluent Kafka + Schema Registry | `deep-dive/06-interfaces-and-contracts.md` (6.4) | ADR-013, ADR-034 |
| bq-sink, BigQuery | `deep-dive/04-components-and-responsibilities.md` (4.11) | ADR-014, ADR-023 |
| erasure-worker | `deep-dive/04-2-source-lifecycle-and-cells.md` (4.19, 4.20) | ADR-029, ADR-030 |
| acl-applier | `deep-dive/04-2-source-lifecycle-and-cells.md` (4.21) | ADR-022 |
| Langfuse Cloud | `deep-dive/09-observability.md` | ADR-018 |
| Anthropic, Voyage | `deep-dive/08-security-and-privacy.md` (8.7) | ADR-005, ADR-006, ADR-038 |
