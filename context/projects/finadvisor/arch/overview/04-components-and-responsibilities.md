## 4. Components and responsibilities

```mermaid
flowchart TB
    subgraph edge["edge"]
        ALB["External ALB"]
        ARMOR["Cloud Armor"]
        KONG["Kong fa-gateway"]
        SPA["SPA (GCS backend bucket)"]
        VALKEY["Valkey (Memorystore)"]
    end
    subgraph app["app: Cloud Run service chat-api"]
        AUTH["auth"]
        PRINC["principal"]
        RETR["retrieval"]
        GUARD["guardrails"]
        AGENT["agent"]
        LLM["llm"]
        EVENTS["events"]
        ADMIN["admin"]
    end
    subgraph workers["workers"]
        WORKER["fa-worker pool"]
    end
    subgraph jobs["jobs"]
        JOBS["Cloud Run jobs"]
    end
    subgraph data["data"]
        SQL[("Cloud SQL")]
        GCS[("GCS bronze")]
        BQ[("BigQuery")]
    end
    subgraph streaming["streaming"]
        KAFKA["Confluent Kafka"]
        SR["Schema Registry"]
    end
    subgraph saas["SaaS"]
        IDP["Identity Platform"]
        ANT["Anthropic"]
        VOY["Voyage"]
        MARM["Model Armor"]
        LF["Langfuse"]
    end
    ALB --> ARMOR
    ARMOR -->|"/* HTTPS"| SPA
    ARMOR -->|"/v1/* HTTPS"| KONG
    KONG -->|"rate-limit counters (redis)"| VALKEY
    KONG -->|"HTTPS via VPC, X-Serverless-Authorization, SSE unbuffered"| AUTH
    AUTH -->|"tenant-aware ID token verify"| IDP
    AUTH --> PRINC
    PRINC --> AGENT
    PRINC --> ADMIN
    AGENT --> GUARD
    AGENT --> RETR
    AGENT --> LLM
    AGENT --> EVENTS
    GUARD -->|"REST screen"| MARM
    RETR -->|"embed, rerank"| VOY
    RETR -->|"SQL as fa_app, SELECT only (PSC)"| SQL
    PRINC -->|"SQL as fa_app"| SQL
    ADMIN -->|"advisors, acl_change_requests, outbox in one tx"| SQL
    EVENTS -->|"outbox rows in same tx"| SQL
    LLM -->|"Messages API stream (direct or via Kong egress)"| ANT
    AGENT -.->|"masked spans"| LF
    WORKER -->|"SQL as fa_worker"| SQL
    WORKER -->|"produce/consume, idempotent"| KAFKA
    WORKER --> SR
    WORKER -->|"BQ sink"| BQ
    WORKER -->|"embed"| VOY
    WORKER -->|"Haiku batch, eval judge"| ANT
    WORKER -->|"read bronze, write silver"| GCS
    WORKER -->|"judge scores"| LF
    JOBS -->|"SQL as fa_owner/fa_etl/fa_etl_public/fa_dbt/fa_maint/fa_eval"| SQL
    JOBS -->|"write by sha256"| GCS
    JOBS -->|"produce"| KAFKA
    JOBS --> BQ
    JOBS -->|"embed"| VOY
    JOBS -->|"Haiku, eval"| ANT
```

Notes on the diagram: `chat-api` neither produces nor consumes Kafka; its events leave through the outbox rows that the `fa-worker` relay publishes. `chat-api` calls Kong's internal egress route to reach Anthropic only if the egress spike passes (§10); otherwise `llm` calls Anthropic directly. The SPA hosts no code that talks to anything but `/v1/*` on its own origin. Platform services (Cloud Scheduler, Secret Manager, Artifact Registry, VPC / PSC / Private Google Access, Cloud Trace / Logging / Monitoring, GitHub Actions + WIF) are in the deployment diagram (§4.12); Terraform is described there in a note.

Runtime shape (ADR-019): one Python image, entrypoints `api | worker | jobs`. `chat-api` is a Cloud Run service (SSE, explicit concurrency, request timeout 3600 s). `fa-worker` is a Cloud Run worker pool. Jobs are Cloud Run jobs. Local dev is docker compose with the same image. All Cloud Run services and jobs use Direct VPC egress in `private-ranges-only` mode with no Cloud NAT (ADR-024).

### 4.1 External ALB
- Purpose: single public entry point, same origin for SPA and API. URL map: `/*` to the GCS backend bucket (SPA, CDN); `/v1/*` to the `fa-gateway` serverless NEG. Managed certificate.
- Persistent (~$18-25/month with Cloud Armor) because certificate provisioning is slow; never torn down by `demo-down` (D7).
- `fa-gateway` has the Cloud Run invoker check disabled (the only service where it is), ingress internal-and-cloud-load-balancing, so `run.app` is unreachable from the internet and the ALB is the only path in; no `allUsers` binding anywhere (D15.1, D16.1; https://docs.cloud.google.com/run/docs/authenticating/public ). IAP was rejected: it replaces the caller identity and conflicts with end-user ID tokens. E10 checks the org policy `constraints/run.managed.requireInvokerIam` and that no service has an `allUsers` binding.
- Fixes G-02, G-13. Decision: ADR-012.

### 4.2 Cloud Armor
- Policy attached to the ALB backend services: DDoS / WAF preconfigured rules, geo rules, coarse per-IP throttle. Kong keeps the fine-grained limits; Cloud Armor keeps DDoS / WAF / geo (D12).
- Cost ~$0.75/1M requests + policy fee: exact cost UNVERIFIED (§10).

### 4.3 Kong (Cloud Run service `fa-gateway`)
- Image `kong:3.9.4`, DB-less, `_format_version: "3.0"`, admin API off, status listener for health. Ingress internal-and-cloud-load-balancing, invoker check disabled (§4.1). min instances 0 (demo), max 2. Binding per D12 (Keshav); ADR-011.
- Network: Direct VPC egress `private-ranges-only`, Private Google Access on the subnet, and a Cloud DNS private zone mapping `run.app` to `private.googleapis.com`, so Kong reaches `chat-api` (ingress internal) through the VPC (D16.12, ADR-024). Valkey endpoint comes from a Kong environment variable; `demo-up` deploys a new Kong revision with it.
- Responsibilities: rate limits (per client IP and per session key, `redis` policy on Valkey), request-size limit, CORS (SPA origin allow-list), `correlation-id` (`X-Request-Id`), OpenTelemetry (`traceparent`), Prometheus, `file-log` audit, bot-detection, `request-transformer` stripping client `X-User-Id`, `X-Tenant-Id`, `X-Serverless-Authorization`, `X-RL-Key`, and a `pre-function` that (a) sets `X-Serverless-Authorization: Bearer <Google ID token>` (from the metadata server, audience = chat-api URL, cached until near expiry), leaving the user's `Authorization` intact (Cloud Run IAM checks only that header when both are present; https://docs.cloud.google.com/run/docs/authenticating/service-to-service ), and (b) sets `X-RL-Key = sha256(Authorization)` so raw tokens never reach Valkey keys.
- Audit (D16.9, ADR-023): `file-log` to stdout with a field whitelist (no `Authorization`, no bodies, no query strings) to Cloud Logging, then a log sink to BigQuery `gateway_audit`. There is no `/internal/audit/gateway` route. Fixes G-48.
- Does not verify tokens, does not set identity headers, cannot key on the verified tenant (OSS limitation); per-tenant budgets and concurrency live in `chat-api`.
- SSE chat routes: `response_buffering: false`, `request_buffering: false`, service `read_timeout` 3,600,000 ms.
- Local: `kong:3.9.4` + Valkey in compose; `kong.yml` in git, validated in CI with `kong config parse`, smoke-tested with deck/curl.
- Full route and plugin table: §6.5. Spikes: SSE pass-through, `X-Serverless-Authorization` passthrough smoke test, private-DNS `run.app` egress, ai-proxy `preserve` egress, `X-RL-Key` behaviour (§10).

### 4.4 SPA (GCS backend bucket)
- Vite + React 19 + TypeScript single-page app, static files in a GCS bucket behind the ALB with CDN. Same origin as the API, so no CORS in the normal path and no BFF buffering hop.
- Behaviour: tenant discovery from `/t/<slug>`, Identity Platform sign-in for that IdP tenant, fetch-based SSE client with `Last-Event-ID` resume and `Idempotency-Key`, citations with excerpts, stale badges, conversation history, feedback, error states keyed by error code. Renders sanitized markdown only. Tests: vitest + Playwright. Epic E8.
- Replaces Next.js 14 (G-13, G-57).

### 4.5 chat-api modules (Cloud Run service `chat-api`)
Single deployable, modular monolith. Import-linter contracts enforce the boundaries below, plus a test. DB login role `fa_app`: SELECT only on content tables, no write on content tables anywhere in `chat-api`. Ingress internal; `run.invoker` granted only to the Kong service account (IAM checks the `X-Serverless-Authorization` header). Request timeout 3600 s, explicit concurrency (number set in E10 from the load test), one Uvicorn process per container. `chat-api` has no Kafka credentials: it neither produces nor consumes.

**`auth`**: verifies the `Authorization: Bearer <Identity Platform ID token>` with firebase-admin tenant-aware verification: the `firebase.tenant` claim names the IdP tenant, and `tenant_mgt.auth_for_tenant(tenant_id).verify_id_token(...)` checks signature, `aud`, `iss`, `exp` and raises `TenantIdMismatchError` on a tenant mismatch (D15.3; https://docs.cloud.google.com/identity-platform/docs/multi-tenancy-managing-tenants ). Output: `(sub, idp_tenant_id)`. Never reads identity from headers. The claim name is verified in the first E1 ticket. Fixes G-01.

**`principal`**: maps `idp_tenant_id` to `tenants.id` (via `fa_tenant_lookup`, §5.4), loads `advisors` (tier, jurisdictions, licenses, role, `entitlement_version`) into a `Principal` object, cached <= 60 s per process; the TTL is the revocation bound (no Kafka invalidation). Owns the only function that sets the per-transaction settings `app.tenant_id`, `app.idp_uid`, `app.user_id`, `app.role`, `app.tier`, `app.jurisdictions` via `set_config(name, $n, true)` with bind parameters (the principal-load transaction sets `app.tenant_id` and `app.idp_uid` plus neutral values for the rest). Provides the tenant-scoped transaction context manager used by every module; transactions are short and never held across the LLM loop.

**`retrieval`**: `RetrievalService(principal)` is the single enforcement point (ADR-004). Only module allowed to touch content tables (`documents`, `chunks`, `suitability_rules`), read-only. Methods: `search(query_text, query_vec)` (hybrid SQL + RRF), `rerank`, `gate`, `expand_parents`, `factsheet`, `suitability`, `fetch_chunks(ids)` (used by the citation verifier and the cache-hit path). Tools never pass tenant, tier or jurisdiction. Embeds via Voyage `voyage-4` (`input_type=query`), reranks via `rerank-2.5-lite`; a rerank timeout or 429 falls back to RRF order and marks the turn degraded (§6.2 `meta`). Also owns the `answer_cache` read/write (not a content table); turns that called a side-effect tool are never cached.

**`guardrails`**: input cap; Presidio (`presidio-analyzer` 2.2.x, spaCy `en_core_web_sm`) in-process pseudonymization before embed / LLM / traces / logs; Model Armor input screen (parallel with embed, timeout 500 ms, fail closed); sentence-buffered output PII redaction; deterministic citation verifier (every `[n]` is in the retrieved chunk ids; quote overlap); error-code mapping. No LLM-based rails on the hot path (ADR-009). Presidio latency is benchmarked in E4 (no official figure).

**`agent`**: the retrieve-first orchestrator (ADR-007). Order: guard-in, answer-cache lookup, embed + screen, retrieval, gate, then one streaming `llm` call with tools (`lookup_product_factsheet`, `lookup_suitability_rule`, `escalate_to_compliance`, `search_firm_kb` follow-up), max 3 iterations. Conversation state: last 6 turns <= 3k tokens, follow-up condensation with Haiku only when history exists. Emits SSE events with sequence ids and persists them to `turn_events`; sets `messages.retrieval_degraded`. Persists escalations (G-18). On a sampled fraction of completed turns (`EVAL_SAMPLE_RATE`) writes an `eval.sample.v1` outbox row.

**`llm`**: `LLMClient` over the Anthropic SDK: streaming, explicit timeouts, retries with jitter, circuit breaker, same-provider fallback (`claude-sonnet-5-5` to `claude-sonnet-4-6`) enabled only if the eval gate passed against the fallback; model ids only from config; no `temperature`/`top_p`/`top_k`; prompt caching on system prompt + tools (tool definitions versioned with the prompt); `max_tokens` bound; CI and readiness fail on a retired or soon-retiring model. Base URL from config (`ANTHROPIC_BASE_URL`): direct, or Kong egress route (`key-auth` consumer `chat-api`). ADR-005, ADR-006.

**`events`**: transactional outbox writer: rows inserted in the same transaction as the business write (turn persist, escalation, admin change). It has no Kafka client and no listener: chat never depends on Kafka. ADR-013.

**`admin`**: tenant-admin endpoints (`/v1/admin/*`). Advisor entitlement changes are a direct `UPDATE advisors` (allowed to `tenant_admin` only by policy, bumping `entitlement_version`) plus an outbox event for analytics. Document ACL changes and deletes never write content tables: `admin` inserts an `acl_change_requests` row and an `acl.changes.v1` outbox row in one transaction and returns 202; the `acl-applier` worker applies it (ADR-022). Role check `tenant_admin` through `principal`. Tenant onboarding (partition creation) is a job, not an endpoint (§4.8).

### 4.6 Valkey (Memorystore, shared-core-nano)
- Backing store for Kong `rate-limiting` counters (`policy: redis`, `sync_rate: 0` on the chat route). Local: valkey container in compose. In the cloud it is a fixed-name Memorystore instance created by `demo-up` and deleted by `demo-down` by the demo script, outside Terraform state (documented once here and in §2.6); `demo-up` passes its endpoint to Kong as an environment variable by deploying a new Kong revision. ~$23/month, ~$0.03/h only while up. Not used for anything else (no session or answer cache).

### 4.7 fa-worker (Cloud Run worker pool)
- Entrypoint `worker`; one image, roles selected by `WORKER_ROLES`: `outbox-relay`, `silver`, `contextualizer`, `indexer`, `acl-applier`, `eval-judge`, `bq-sink`. DB login role `fa_worker`. Confluent: one service account and API key per service, Kafka ACLs per service account (ADR-013). Instance count 0 when the demo is down.
- Envelope check on every consumed message: if `envelope.tenant_id` differs from the message key, or the tenant is PUBLIC, the message goes to `dlq.v1` with a reason (PUBLIC is ingested in-process by `etl-public`, never through worker consumers). `bq-sink` is exempt for PUBLIC analytics events.
- `outbox-relay`: per tenant, reads unpublished `outbox` rows in order, produces with an idempotent producer, marks `published_at`. At-least-once. No Debezium.
- `silver`: consumes `docs.bronze.v1`: Docling parse, Presidio scrub, structure-aware chunking (256-512-token children, ~1k-token parents, token counts from Voyage `count_tokens`), Pandera validation, rejects to `ingest_rejects`, writes silver Parquet to the data bucket under `silver/tenant_id=<id>/dt=<date>/`, emits `docs.silver.v1`.
- `contextualizer`: consumes `docs.silver.v1`: Haiku 5.5 Batch API contextual headers (behind flag `CONTEXTUAL_RETRIEVAL_ENABLED`), suitability-rule extraction (Haiku structured output, validated) into `suitability_rules`, emits `chunks.contextualized.v1`.
- `indexer`: consumes `chunks.contextualized.v1`: Voyage `voyage-4` document embeddings only for chunks whose `(tenant_id, chunk_hash, embed_model)` is new, upserts `chunks`, deletes superseded chunks, then bumps the tenant's `corpus_version` (UPDATE on its own tenant row by policy), emits `chunks.indexed.v1`.
- `acl-applier`: consumes `AclChangeRequested` events on `acl.changes.v1`: applies the ACL-column UPDATE (or delete) on `documents` and `chunks` for the request (own-tenant WITH CHECK, ACL columns only), marks the `acl_change_requests` row `applied`, bumps `tenants.acl_version`, purges `answer_cache` rows that cite the document, emits `AclChangeApplied` (ADR-022).
- `eval-judge`: consumes `eval.sample.v1` (a `EVAL_SAMPLE_RATE` sample, 5-10%), scores the redacted question / answer / cited excerpts with `claude-haiku-5-5` (judge differs from the answer model), writes scores to Langfuse and `eval_scores`, emits `JudgeScored` on `eval.events.v1`. Langfuse-side evaluators are not used.
- `bq-sink`: consumes audit, usage, eval, ingest and ACL topics; writes BigQuery with event-id dedupe.
- Every consumer: `processed_events` dedupe in the sink transaction, retries, then DLQ `dlq.v1`. Each message handled in a transaction with `app.tenant_id` set from the event key.
- The PUBLIC corpus is never written by `fa_worker` (§5.4).

### 4.8 Cloud Run jobs
All from the one image (`jobs` entrypoint). Triggered by Cloud Scheduler, by `demo-up`, or manually.

| Job | DB role | Purpose |
|---|---|---|
| `migrate` | `fa_owner` | Alembic upgrade before traffic; tenant onboarding (`--onboard-tenant <slug>`: LIST partition + indexes, `tenants` row, IdP mapping; the IdP tenant itself is provisioned by an onboarding script in E1 and Terraform in E10); asserts role flags, FORCE RLS and that partitions carry no runtime grants |
| `maintenance` | `fa_maint` | Purges expired `answer_cache` and `turn_events` rows; creates `messages` partitions 3 months ahead and drops those past retention; hourly while the demo is up and run by `demo-up` (D16.8) |
| `etl` | `fa_etl` | Dagster run of tenant bronze assets (fetch, GCS by sha256, register `documents`, publish `docs.bronze.v1`), backfills and replays. Daemon-less: `dagster asset materialize` in a Cloud Run job; run and event storage in Postgres (`dagster-postgres`, database `dagster` on the same Cloud SQL instance, owned by role `fa_dagster`, no access to app schemas); `dagster dev` locally |
| `etl-public` | `fa_etl_public` | Public-ingest (EDGAR 497K): runs every stage in-process and publishes only analytics topics (`ingest.analytics.v1`); the only writer of PUBLIC rows |
| `dbt` | `fa_dbt` | dbt Core gold models on Postgres (`dbt-postgres`: views with `security_invoker = true`, or incremental models with a tenant predicate, never full rebuilds) and BigQuery marts (`dbt-bigquery`); per tenant run on a dedicated connection |
| `eval` | `fa_eval` | Full or subset eval run (L1-L3) against the dedicated `eval` tenant; results to Langfuse and `eval.events.v1` |
| `redteam` | `fa_eval` | promptfoo red team against the API |
| `demo-prewarm` | none | Runs inside the VPC after `demo-up`: calls `/readyz` and warms pools and caches (not run from the operator laptop) |
| `demo-ttl` | `fa_maint` | Hourly safety net: reads the outbox count and runs `demo-down` if the demo has been up longer than `DEMO_TTL_HOURS` (Cloud Run admin SA rights) |

### 4.9 Cloud SQL (PostgreSQL 16, pgvector 0.8.5)
- Enterprise, 2 vCPU / 8 GiB, zonal, private IP only (PSC), activation policy flipped by `demo-up` / `demo-down`; HA is a Terraform flag for `prod` and load tests (ADR-020). Databases: the app database and `dagster`. Schema, roles, RLS and indexes: §5.
- Single store for relational data, vectors (halfvec + HNSW), full text (tsvector + GIN), conversation state, outbox, answer cache.
- `max_connections` is 400 on this tier; the pool budget (`DB_POOL_SIZE` x max instances over all services) must stay <= 300, leaving headroom for migrations, dbt and Dagster (D15.7). Managed connection pooling is Enterprise Plus only (transaction mode forbids `SET`).

### 4.10 GCS bronze
- Bucket (data) with prefix `bronze/{tenant_id}/{sha256}`: raw immutable bytes plus source URL and fetch time; the only place raw documents live (G-03). `silver/tenant_id=<id>/dt=<date>/` holds redacted chunk Parquet. The SPA bucket is separate.

### 4.11 BigQuery
- Analytics marts for audit, usage, eval and gateway events: tables partitioned by day, clustered by `tenant_id`; redacted text only; `maximum_bytes_billed` set on every query. Per-tenant authorized views are the primary isolation; row access policies per tenant are the second layer (they do not prune partitions and can bill more rows) (D15.5). Marts are built by `dbt-bigquery`. Fed by the `bq-sink` with event-id dedupe (Storage Write API default stream is at-least-once) and, for `gateway_audit`, by a Cloud Logging log sink. 1 TiB/month of queries free (evidence-r2.md). ADR-014, ADR-023.

### 4.12 Platform services and the deployment view

```mermaid
flowchart TB
    subgraph gha["CI/CD"]
        GH["GitHub Actions"]
        WIF["Workload Identity Federation"]
    end
    USER["Browser"]
    IDP["Identity Platform"]
    subgraph gcp["GCP project us-central1"]
        LB["External ALB"]
        CA["Cloud Armor"]
        AR["Artifact Registry"]
        subgraph net["VPC: Direct VPC egress private-ranges-only, Private Google Access, run.app private DNS zone"]
            GW["Cloud Run fa-gateway"]
            API["Cloud Run chat-api"]
            WP["Cloud Run worker pool fa-worker"]
            CJ["Cloud Run jobs"]
            DB[("Cloud SQL PG16 via PSC")]
            VK["Memorystore Valkey"]
        end
        SCH["Cloud Scheduler"]
        SM["Secret Manager"]
        OBS["Cloud Trace, Logging, Monitoring"]
        LS["Log sink to BigQuery"]
        BKT["GCS buckets: spa, data"]
    end
    CONF["Confluent Cloud (via Terraform provider)"]
    USER -->|"HTTPS"| LB
    LB --> CA
    CA -->|"/v1/*"| GW
    CA -->|"/*"| BKT
    USER -->|"sign-in"| IDP
    GH --> WIF
    WIF -->|"keyless"| AR
    AR -->|"image by digest"| GW
    AR --> API
    AR --> WP
    AR --> CJ
    GW -->|"ID token via VPC"| API
    API --> DB
    WP --> DB
    CJ --> DB
    GW --> VK
    SCH -->|"triggers"| CJ
    SM -.->|"secrets at start"| API
    API --> OBS
    GW --> OBS
    OBS --> LS
    WP --> CONF
    CJ --> BKT
```

Terraform (google provider, plus Confluent provider) owns every resource in this view and the Confluent cluster, with state per env prefix, applied from GitHub Actions through WIF (plan on PR). The one exception is the Valkey instance lifecycle (§4.6). `lifecycle.ignore_changes` covers `activation_policy`, `min_instance_count`, `manual_instance_count`.

- **Cloud Scheduler**: triggers `etl`, `etl-public`, `dbt`, `maintenance`, `eval`, `redteam` and `demo-ttl`. `demo-down` pauses all except `demo-ttl`.
- **Secret Manager**: all secrets (DB passwords per role, Kafka and Schema Registry keys per service, Anthropic, Voyage, Langfuse keys, the Kong `key-auth` key for the egress route). No secret defaults in code: missing config fails boot.
- **Artifact Registry**: images by digest; deploy references digests, never tags.
- **VPC / PSC / egress** (ADR-024): Cloud SQL private only (PSC); all services and jobs use Direct VPC egress in `private-ranges-only` mode (public SaaS APIs are reached directly; no Cloud NAT), Private Google Access on the subnet, and a Cloud DNS private zone mapping `run.app` to `private.googleapis.com`. Startup probe on Cloud Run. Per-service service accounts, least privilege (G-50). Fallback if the private-DNS spike fails: all-traffic egress + Cloud NAT (about +$32/month) with an ADR.
- **Cloud Trace / Logging / Monitoring**: §9. A log sink exports Kong's `file-log` audit to BigQuery.
- **GitHub Actions + WIF**: keyless deploy and CI (ADR-021).
- **Local (docker compose)**: Postgres (`pgvector/pgvector:0.8.5-pg16`, matching Cloud SQL), `apache/kafka:4.4.0` KRaft, Schema Registry (cp-schema-registry), `kong:3.9.4`, Valkey, api, worker, frontend dev image, `dagster dev`; env-driven host ports; healthchecks (G-49).

### 4.13 SaaS dependencies
- **Identity Platform** (multi-tenancy, one IdP tenant per firm; billing enabled for > 2 tenants; email/password free to 50k MAU). Verified by `auth` with firebase-admin; ADR-010.
- **Anthropic**: answer `claude-sonnet-5-5`; judge, headers, rule extraction, condensation, citation spot-checks `claude-haiku-5-5`; fallback `claude-sonnet-4-6`; Batch API for offline work. ADR-006.
- **Voyage**: `voyage-4` embeddings (halfvec(1024), `input_type` query / document), `rerank-2.5-lite`. Single provider, no fallback. Rerank timeout or 429 degrades to RRF order, flagged and counted.
- **Model Armor**: REST screen of the redacted input (detects, the app acts). Free to 2M tokens/month.
- **Langfuse Cloud Hobby** (Python SDK 5.x): free 50k units/month, 30-day retention; metadata, hashes, redacted text only, tagged by tenant; `capture_input` / `capture_output` off on sensitive spans and `mask_otel_spans` for export masking; synthetic data only. ADR-018.
- **Confluent Cloud Basic + Schema Registry (Essentials)**: cluster and registry in us-central1 (registry region is fixed by the first cluster). Kafka ACLs per service account (no RBAC), max 50 API keys, 1,000 ACLs, 1,500 partitions: one service account + key per service. Local: `apache/kafka:4.4.0` + cp-schema-registry.

### 4.14 Key flows

#### Flow 1: chat request

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser SPA
    participant E as ALB + Cloud Armor
    participant K as Kong fa-gateway
    participant C as chat-api
    participant D as Cloud SQL
    participant M as Model Armor
    participant V as Voyage
    participant L as Anthropic
    B->>E: POST /v1/chat, Bearer ID token, Idempotency-Key
    E->>K: WAF, DDoS and geo rules passed
    K->>K: strip identity headers, set X-RL-Key and X-Serverless-Authorization, rate-limit IP and session, size limit, correlation-id
    K->>C: proxy via VPC, no buffering
    C->>C: auth: tenant-aware ID token verify (firebase.tenant)
    C->>D: principal: fa_tenant_lookup, load advisors row (60 s cache)
    C->>D: short tx: insert turn_events seq 0 (ON CONFLICT DO NOTHING), insert user message
    C->>C: guard-in: input cap, Presidio pseudonymize
    C->>D: answer_cache lookup (key incl. corpus, acl, entitlement versions)
    par guard-in screen
        C->>M: screen redacted input (500 ms, fail closed)
    and embed
        C->>V: embed query (voyage-4, input_type query)
    end
    C->>D: short tx: set_config, hybrid SQL (FTS leg + dense leg, RRF k=60, RLS on both)
    D-->>C: candidates
    C->>V: rerank-2.5-lite (timeout)
    V-->>C: top 6, or timeout/429 then RRF order with retrieval_degraded
    C-->>B: SSE meta (retrieval_degraded)
    C->>C: confidence gate
    alt gate fails
        C-->>B: SSE refusal NO_FIRM_DOCUMENTATION + escalate offer (no LLM call)
    else gate passes
        C->>D: short tx: parent expansion, staleness from today's date
        C->>L: stream messages (system+tools cached, retrieval as JSON tool_result)
        loop tool loop, max 3 iterations
            L-->>C: tokens or tool_use
            C-->>B: SSE tool (name + status only)
        end
        C->>C: output guard: sentence-buffered PII redaction, citation verifier
        C-->>B: SSE delta and citation events, each with id
    end
    C->>D: short tx: persist assistant message, turn_events, outbox rows (chat.audit, chat.usage, sampled eval.sample)
    C-->>B: SSE done
```

Notes:
1. The cache lookup comes after Presidio (the key uses the normalized redacted question). On a hit the screen and embed are skipped; the cited chunks are re-fetched through `retrieval.fetch_chunks` under the caller's RLS, the citation verifier is re-run and staleness is recomputed. A chunk no longer visible turns the hit into a miss. Turns that call `escalate_to_compliance` are never written to the cache.
2. The database is never held open across the LLM call: each `D` step is its own transaction with `set_config(..., true)`.
3. Langfuse spans (masked) and OpenTelemetry spans are emitted asynchronously and never block the stream.
4. Failure at any step produces one SSE `error` event with a code (§6.2), never exception text.
5. The relay publishes the outbox rows later (`outbox-relay`, §4.7); chat does not wait for Kafka.

#### Flow 2: ingest

```mermaid
sequenceDiagram
    autonumber
    participant S as Cloud Scheduler
    participant J as Cloud Run job etl (Dagster)
    participant G as GCS bronze and silver
    participant K as Confluent Kafka
    participant W as fa-worker (silver, contextualizer, indexer)
    participant A as Anthropic Haiku Batch
    participant V as Voyage
    participant D as Cloud SQL
    participant T as dbt job (fa_dbt)
    participant Q as BigQuery
    S->>J: trigger tenant x date partition
    J->>G: fetch source, write bronze/tenant/sha256 (skip if exists)
    J->>K: docs.bronze.v1 (key tenant_id, idempotent producer)
    K->>W: silver: Docling parse, Presidio scrub, structure chunking, Pandera
    W->>G: write silver Parquet, rejects to ingest_rejects
    W->>K: docs.silver.v1
    K->>W: contextualizer: contextual headers and rule extraction
    W->>A: Batch API (Haiku 5.5, redacted text)
    A-->>W: headers, suitability rules (structured)
    W->>D: insert suitability_rules (validated)
    W->>K: chunks.contextualized.v1
    K->>W: indexer: chunk_hash check
    W->>V: embed only new (tenant_id, chunk_hash, embed_model)
    W->>D: upsert chunks, delete superseded (processed_events in same tx)
    W->>D: bump tenants.corpus_version
    W->>K: chunks.indexed.v1
    T->>D: gold models (security_invoker views or incremental)
    K->>Q: bq-sink writes events (event_id dedupe)
```

Notes: every consumer commits offsets after the DB transaction that wrote `processed_events`; poison messages and envelope mismatches go to `dlq.v1`. A backfill or re-embed is a replay: Dagster re-publishes `docs.bronze.v1` for the partition (bronze is immutable), and unchanged chunk hashes cost nothing. The PUBLIC corpus (EDGAR 497K) runs all stages in-process in the `etl-public` job as `fa_etl_public`, bumps the PUBLIC `corpus_version` itself, and publishes only analytics events (`ingest.analytics.v1`); worker consumers reject PUBLIC. Docling on 497K and inline-XBRL tables is a spike (§10).

#### Flow 3: ACL change (asynchronous)

```mermaid
sequenceDiagram
    autonumber
    participant A as Tenant admin (browser)
    participant K as Kong fa-gateway
    participant C as chat-api (admin, events)
    participant D as Cloud SQL
    participant W as fa-worker (outbox-relay, acl-applier)
    participant F as Confluent Kafka
    participant Q as BigQuery
    A->>K: POST /v1/admin/documents/{id}/acl-changes
    K->>C: proxy with ID token
    C->>C: auth, principal (role tenant_admin)
    C->>D: one tx: insert acl_change_requests (pending), insert outbox AclChangeRequested
    C-->>A: 202 Accepted (request id)
    W->>D: relay reads unpublished outbox rows
    W->>F: acl.changes.v1 (key tenant_id)
    F->>W: acl-applier consumes AclChangeRequested
    W->>D: one tx: UPDATE ACL columns of documents and chunks (fa_worker, own-tenant WITH CHECK), request applied, bump tenants.acl_version, purge answer_cache rows citing the document
    W->>F: AclChangeApplied (via outbox)
    F->>Q: bq-sink audit row
    A->>K: GET /v1/admin/acl-changes/{request_id}
```

Notes: no re-embedding (Notion pattern, evidence-r2.md); the change is a metadata UPDATE. Until the applier runs, the old ACL still applies (the lag is relay + consumer time). When the applier commits, the bump of `acl_version` makes every earlier cached answer unreachable, and a cache hit that raced the bump is re-verified against freshly fetched chunks under the caller's RLS (D13i), so a cached answer cannot cite a chunk the caller can no longer see. Document delete follows the same path with `action = delete`. Advisor entitlement changes are a direct `UPDATE advisors` by a `tenant_admin` (no worker); `chat-api` does not consume Kafka, so the 60 s `principal` cache TTL is the revocation bound.

#### Flow 4: eval gate in CI

```mermaid
sequenceDiagram
    autonumber
    participant P as Pull request
    participant R as GitHub Actions runner
    participant S as Service containers (pgvector 0.8.5-pg16, Kafka)
    participant V as Voyage
    participant L as Anthropic
    participant F as Langfuse
    P->>R: push (path-filtered)
    R->>S: start containers, wait for healthchecks
    R->>R: lockfile install, ruff, mypy, pytest, eslint, tsc, vitest
    R->>S: alembic upgrade (as fa_owner), create roles (incl. fa_eval), onboard eval tenants
    R->>R: L0 deterministic: RLS leak matrix (reads, writes, FK probes, partition grants, pooled reuse, advisor self-escalation), fail-closed, citation verifier, PII, model-retirement check
    R->>V: ingest fixture corpus (embed)
    R->>L: run ~60-question subset (answer model, then Haiku judge)
    R->>F: dataset run_experiment, scores
    R->>R: gate: citation >= 0.95, faithfulness >= 0.90, leaks = 0, recall regression <= 2 pts
    R-->>P: required status check pass / fail
```

Notes: the PR runs the ~60-question path-filtered subset; the full set (50 growing to ~300) runs weekly and before demos, and also once against the fallback model (fallback is enabled only if it passes). L1 retrieval metrics (recall@k, MRR, nDCG, dense / FTS / hybrid / rerank ablation) and L2 Ragas metrics run in the same job; L3 cross-tenant refusal and the promptfoo red team run in the `redteam` job. Fixes G-05, G-06.

#### Flow 5: demo-up

The exact reverse of the demo-down order (D16.13).

```mermaid
sequenceDiagram
    autonumber
    participant O as Operator (make demo-up)
    participant SQ as Cloud SQL
    participant VK as Memorystore Valkey
    participant GW as fa-gateway and chat-api
    participant WP as fa-worker pool
    participant SC as Cloud Scheduler
    participant PW as maintenance and demo-prewarm jobs
    O->>SQ: activation policy ALWAYS
    SQ-->>O: RUNNABLE (start time not documented, measured in E10)
    O->>VK: create fixed-name instance
    O->>GW: new Kong revision with Valkey endpoint env, min instances up
    O->>WP: manual instance count up
    O->>SC: resume triggers
    O->>PW: run maintenance, then demo-prewarm inside the VPC (/readyz, pools)
    PW-->>O: ready, print URL
```

#### Flow 6: demo-down

```mermaid
sequenceDiagram
    autonumber
    participant O as Operator or demo-ttl job
    participant SC as Cloud Scheduler
    participant OB as Outbox and Kafka consumers
    participant WP as fa-worker pool
    participant GW as fa-gateway and chat-api
    participant VK as Memorystore Valkey
    participant SQ as Cloud SQL
    O->>SC: pause triggers (except hourly demo-ttl)
    O->>OB: drain: wait for outbox empty and consumer lag 0 (10 min timeout, then force)
    O->>WP: scale to 0
    O->>GW: min instances 0
    O->>VK: delete instance
    O->>SQ: activation policy NEVER (stop)
```

After a forced down, remaining outbox rows are logged and delivered on the next `demo-up`. Terraform uses `lifecycle.ignore_changes` on `activation_policy`, `min_instance_count` and `manual_instance_count`, so `apply` never fights the script. The ALB, Cloud Armor, Confluent cluster and storage stay (idle cost, §2.5).
