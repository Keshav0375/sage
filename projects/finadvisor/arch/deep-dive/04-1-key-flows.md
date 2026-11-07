> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
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
    B->>E: POST /v1/chat, Bearer ID token (one firm), Idempotency-Key, optional as-of chip
    E->>K: WAF, DDoS and geo rules passed
    K->>K: strip identity headers, set X-RL-Key and X-Serverless-Authorization, rate-limit IP and session, size limit, correlation-id
    K->>C: proxy via VPC, no buffering
    C->>C: auth: tenant-aware ID token verify (firebase.tenant)
    C->>C: principal: home_cell from cells.json must equal this cell, else 421 with cell hint and no tenant read
    C->>D: principal: fa_tenant_lookup, load advisors row (60 s cache)
    C->>D: short tx: insert turn_events seq 0 (ON CONFLICT DO NOTHING), insert user message
    C->>C: guard-in: input cap, Presidio pseudonymize
    C->>D: as_of resolve: date parser, else UI chip, else current_date (UTC) from Postgres
    C->>D: answer_cache lookup (key incl. corpus, acl, entitlement versions, as_of, embed_model, source_epoch)
    par guard-in screen
        C->>M: screen redacted input (fail closed, timeout from measured latency)
    and embed
        C->>V: embed query (voyage-4, input_type query)
    end
    C->>D: short tx: set_config, hybrid SQL (FTS leg + dense leg, RRF k=60, valid_range @> as_of, active embed_model, RLS on both)
    D-->>C: candidates
    C->>V: rerank-2.5-lite (timeout)
    V-->>C: top 6, or timeout/429 then RRF order with retrieval_degraded
    C-->>B: SSE meta (retrieval_degraded, as_of)
    C->>C: confidence gate
    alt gate fails
        C-->>B: SSE refusal NO_FIRM_DOCUMENTATION + escalate offer (no LLM call)
    else gate passes
        C->>D: short tx: parent expansion, staleness and state (superseded, revoked, known_pending) against as_of
        C->>L: stream messages (system+tools cached, retrieval as JSON tool_result with boundary nonce)
        loop tool loop, max 3 iterations
            L-->>C: tokens or tool_use
            C-->>B: SSE tool (name + status only)
        end
        C->>C: per sentence: PII redaction, citation verifier, numeric grounding gate, as-of validity of cited chunks
        C->>C: licence footers from document_versions.attribution_text
        C-->>B: SSE delta and citation events, each with id
    end
    C->>D: short tx: persist assistant message, turn_events, outbox rows (chat.audit, chat.usage, sampled eval.sample)
    C-->>B: SSE done
```

Notes:
1. The cache lookup comes after Presidio (the key uses the normalized redacted question). On a hit the screen and embed are skipped; the cited chunks are re-fetched through `retrieval.fetch_chunks` under the caller's RLS, the citation verifier and the as-of validity check are re-run and staleness is recomputed. A chunk no longer visible turns the hit into a miss. Turns that call `escalate_to_compliance` are never written to the cache.
2. The database is never held open across the LLM call: each `D` step is its own transaction with `set_config(..., true)`.
3. Langfuse spans (masked) and OpenTelemetry spans are emitted asynchronously and never block the stream.
4. Failure at any step produces one SSE `error` event with a code (§6.2), never exception text.
5. The relay publishes the outbox rows later (`outbox-relay`, §4.7); chat does not wait for Kafka.
6. A sentence with a number and no `[n]`, or an ungrounded number, withholds the answer (§4.26); a missing licence footer blocks release; a cited chunk whose `valid_range` does not contain `as_of` blocks release (§4.18).

#### Flow 2: ingest

```mermaid
sequenceDiagram
    autonumber
    participant S as Cloud Scheduler
    participant J as Cloud Run job etl (Dagster, connectors)
    participant P as Source publisher
    participant G as GCS bronze, silver, quarantine
    participant K as Confluent Kafka
    participant W as fa-worker (silver, contextualizer, indexer)
    participant A as Anthropic Haiku Batch
    participant V as Voyage
    participant D as Cloud SQL
    participant T as dbt job (fa_dbt)
    participant Q as BigQuery
    S->>J: trigger source x run
    J->>P: connector: changes(cursor - 48 h overlap) and, on the listing cadence, full list()
    J->>D: one tx: append source_observations, advance source_registry cursor
    J->>D: listing diff: two-strike withdrawal, mass-delete breaker, source-class policy (retire or erase)
    J->>G: fetch, write bronze/tenant/sha256 (skip if exists)
    J->>D: document_versions row (ingesting), idempotent on (doc, version_key, content_sha256)
    J->>K: docs.bronze.v1 (key tenant_id, idempotent producer)
    K->>W: silver: Docling parse, ingest scan, contract checks
    alt scan or contract fails
        W->>G: bytes to quarantine/, version status quarantined, nothing in silver
    else passes
        W->>G: Presidio scrub, structure chunking, Pandera, silver Parquet (per version), rejects to ingest_rejects
        W->>K: docs.silver.v1
        K->>W: contextualizer: contextual headers (flag, default off) and rule extraction
        W->>A: Batch API (Haiku 5.5, redacted text)
        A-->>W: headers, suitability rules (structured)
        W->>D: insert suitability_rules (validated)
        W->>K: chunks.contextualized.v1
        K->>W: indexer: reconcile_lineage plan keyed by chunk identity
        W->>V: embed only chunk hashes without a vector for the active embed_model
        W->>D: one tx per document: advisory lock, tombstone and gate check, range merge, version active, corpus_version bump last, cache purge, processed_events
        W->>K: chunks.indexed.v1
    end
    T->>D: gold models (security_invoker views or incremental)
    K->>Q: bq-sink writes events (event_id dedupe)
```

Notes: every consumer commits offsets after the DB transaction that wrote `processed_events`; poison messages and envelope mismatches go to `dlq.v1`. A backfill, a re-embed or a replay after a parser fix is `reconcile_lineage` run again: Dagster re-publishes `docs.bronze.v1` for the partition (bronze is immutable), `parser_version` is part of the chunk identity so the replay re-parses (no "same bytes means no-op"), and unchanged chunk hashes keep their vectors. The PUBLIC corpus (eCFR, EUR-Lex, legislation.gov.uk, SEC RR datasets, FCA API) runs all stages in-process in the `etl-public` job as `fa_etl_public`, calls the same `reconcile_lineage`, bumps the PUBLIC `corpus_version` itself, and publishes only analytics events (`ingest.analytics.v1`); worker consumers reject PUBLIC, and FCA content never reaches Kafka or BigQuery (§4.20). Docling on 497K and inline-XBRL tables is a spike (§10).

#### Flow 3: ACL change (asynchronous, polling)

Document delete is not part of this flow: `DELETE /v1/admin/documents/{id}` writes a `deletion_requests` row directly and the `erasure-worker` runs the deletion flow (§4.19).

```mermaid
sequenceDiagram
    autonumber
    participant A as Tenant admin (browser)
    participant K as Kong fa-gateway
    participant C as chat-api (admin, events)
    participant D as Cloud SQL
    participant W as fa-worker (acl-applier)
    participant F as Confluent Kafka
    participant Q as BigQuery
    A->>K: POST /v1/admin/documents/{id}/acl-changes
    K->>C: proxy with ID token
    C->>C: auth, principal (role tenant_admin)
    C->>D: one tx: insert acl_change_requests (pending), insert outbox AclChangeRequested (analytics only)
    C-->>A: 202 Accepted (request id)
    W->>D: poll acl_change_requests, status pending, FOR UPDATE SKIP LOCKED
    W->>D: one tx: advisory lock (tenant, doc), UPDATE ACL columns of documents, document_versions and chunks (fa_worker, own-tenant WITH CHECK), request applied, bump tenants.acl_version, purge answer_cache rows citing the document
    W->>D: outbox AclChangeApplied
    D-->>F: outbox-relay publishes acl.changes.v1 (later, no effect on enforcement)
    F->>Q: bq-sink audit row
    A->>K: GET /v1/admin/acl-changes/{request_id}
```

Notes: no re-embedding (Notion pattern, evidence-r2.md); the change is a metadata UPDATE. Until the applier runs, the old ACL still applies (the lag is the poll interval). Enforcement no longer depends on Kafka, so a tightening during a Kafka outage still lands (R4-D7; test: stop Kafka, tighten the ACL, the answer is refused within 60 s). When the applier commits, the bump of `acl_version` makes every earlier cached answer unreachable, and a cache hit that raced the bump is re-verified against freshly fetched chunks under the caller's RLS (D13i), so a cached answer cannot cite a chunk the caller can no longer see. The applier takes the same per-document advisory lock as the indexer and the erasure-worker (§4.17), so a reclassification cannot race an ingest. Advisor entitlement changes are a direct `UPDATE advisors` by a `tenant_admin` (no worker); `chat-api` does not consume Kafka, so the 60 s `principal` cache TTL is the revocation bound.

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
    R->>R: L0 deterministic: RLS leak matrix (reads, writes, FK probes, partition grants, pooled reuse, advisor self-escalation), per-leaf EXCLUDE check, as-of boundaries, race harness, contracts, fail-closed, citation verifier, numeric gate, PII, model-retirement check
    R->>V: ingest fixture corpus (embed)
    R->>L: run ~60-question subset (answer model, then Haiku judge)
    R->>F: dataset run_experiment, scores
    R->>R: gate: citation >= 0.95, faithfulness >= 0.90, leaks = 0, recall regression <= 2 pts
    R-->>P: required status check pass / fail
```

Notes: the PR runs the ~60-question path-filtered subset; the 200-item golden set (public slice committed, private slice only where its bucket is mounted; ADR-037) runs weekly and before demos, and also once against the fallback model (fallback is enabled only if it passes). L1 retrieval metrics (recall@k, MRR, nDCG, dense / FTS / hybrid / rerank ablation) and L2 Ragas metrics run in the same job; L3 cross-tenant refusal and the promptfoo red team run in the `redteam` job. Fixes G-05, G-06.

#### Flow 5: demo-up

The exact reverse of the demo-down order (D16.13), then the lifecycle checks that must run before the demo is announced ready.

```mermaid
sequenceDiagram
    autonumber
    participant O as Operator (make demo-up)
    participant SQ as Cloud SQL
    participant VK as Memorystore Valkey
    participant GW as fa-gateway and chat-api
    participant WP as fa-worker pool
    participant SC as Cloud Scheduler
    participant PW as maintenance, erasure, reconcile, canary, prewarm jobs
    O->>SQ: activation policy ALWAYS
    SQ-->>O: RUNNABLE (start time not documented, measured in E10)
    O->>VK: create fixed-name instance
    O->>GW: new Kong revision with Valkey endpoint env, min instances up
    O->>WP: manual instance count up
    O->>PW: erasure job first: drain deletion_requests, re-sweeps due, receipts phase 2 due
    O->>PW: restore check: if the instance was restored, erasure-replay before traffic
    O->>SC: resume triggers
    O->>PW: run maintenance, reconcile, then the canary drill (erasure-canary)
    O->>PW: demo-prewarm inside the VPC (/readyz, pools)
    PW-->>O: ready, print URL
```

In demo-on-demand the system is stopped between demos, so nothing runs while it is down: the erasure job runs first at every start, and the 24 h live-store promise is counted in time the system is running (R4-D9). The canary drill replaces a weekly cron (§4.23).

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
