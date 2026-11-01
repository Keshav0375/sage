# finadvisor: decisions (ADRs)

Newest first. Each entry: status (date, decided-by), context, options with costs, evidence (docs, papers, council), decision, dissent, what it makes harder later, trigger to revisit.

## ADR-024: VPC egress mode: Direct VPC egress private-ranges-only, no Cloud NAT

**Status.** Accepted 2026-11-01. decided-by: researcher (orchestrator rulings D15.2, D16.12). Resolves G-11 (wiring) and keeps G-26 closed.

**Context.** Kong must reach `chat-api` (ingress internal) through the VPC, while every service also calls public SaaS APIs (Anthropic, Voyage, Model Armor, Confluent, Langfuse). An all-traffic egress route needs Cloud NAT for the public calls.

**Options.**
1. Direct VPC egress, all-traffic routing, Private Google Access, plus Cloud NAT for public SaaS: simple routing, about +$32/month (D16.12).
2. Direct VPC egress `private-ranges-only`, Private Google Access on the subnet, and a Cloud DNS private zone mapping `run.app` to `private.googleapis.com` so the internal `run.app` URL of `chat-api` is reached through the VPC; public SaaS calls leave directly; no NAT (chosen).
3. Serverless VPC Access connector. Not chosen: Direct VPC egress is the documented newer path with a startup probe requirement.

**Evidence.** https://docs.cloud.google.com/run/docs/authenticating/service-to-service ; Direct VPC egress and Private Google Access notes in decision-r2.md D15.2 and D16.12; Cloud Run VPC docs https://cloud.google.com/run/docs/configuring/vpc-direct-vpc .

**Decision.** All Cloud Run services and jobs use Direct VPC egress in `private-ranges-only` mode with a startup probe; Private Google Access on the subnet; a Cloud DNS private zone maps `run.app` to `private.googleapis.com`. No Cloud NAT. The E2/E10 spike verifies Kong to `chat-api` over this path (overview §10 item 3).

**Dissent.** None recorded.

**What it makes harder later.** Egress to SaaS has no fixed source IP (no allow-listing by IP). The private-zone mapping is a DNS trick that must keep working across Cloud Run changes.

**Trigger to revisit.** The spike fails: switch to all-traffic egress + Cloud NAT (about +$32/month) and record an ADR.

## ADR-023: Gateway audit through Cloud Logging and BigQuery

**Status.** Accepted 2026-11-01. decided-by: researcher (orchestrator ruling D16.9). Resolves G-48.

**Context.** The MVP Kong `http-log` posts to `/api/audit/kong`, which does not exist (G-48). An HTTP log target on `chat-api` would need the IAM header that Kong's `http-log` cannot add, and would put gateway volume through the outbox.

**Options.**
1. Kong `http-log` to an internal FastAPI route `/internal/audit/gateway` and the outbox. Needs service IAM and adds an unauthenticated-looking internal route.
2. Kong `file-log` to stdout with a field whitelist, to Cloud Logging, then a log sink to BigQuery `gateway_audit` (chosen). Logging costs $0.50/GiB after 50 GiB per project (evidence-r2.md).
3. Gateway events on a Kafka topic. Not chosen: no Kafka producer in the gateway path.

**Evidence.** decision-r2.md D16.9; Cloud Logging pricing in evidence-r2.md.

**Decision.** Kong `file-log` to stdout with a whitelist (timestamp, route, method, status, latency, request id, client IP hash; no `Authorization`, no bodies, no query strings). A Cloud Logging sink exports to BigQuery `gateway_audit`. The `/internal/audit/gateway` route and the `gateway.audit.v1` topic do not exist; `chat-api` serves no `/internal/*` endpoints.

**Dissent.** None recorded.

**What it makes harder later.** Gateway audit rows carry no verified tenant (Kong cannot see it); correlation to a tenant goes through `X-Request-Id` and the application audit. The whitelist is a security control that must be reviewed when plugins change.

**Trigger to revisit.** Per-tenant gateway audit is required; log volume exceeds the free logging allowance.

## ADR-022: Asynchronous ACL changes through acl_change_requests and an acl-applier worker

**Status.** Accepted 2026-11-01. decided-by: researcher (orchestrator rulings D14.8, D14.9, D16.8). Resolves G-20, G-21 (no app write on content tables).

**Context.** The first draft let the `admin` module call `retrieval.update_acl` and gave `fa_app` UPDATE and DELETE grants on `documents` and `chunks`. That widens the write surface of the user-facing role on the tables the whole isolation design protects, and made `chat-api` the cache-invalidation point (a Kafka listener on every instance).

**Options.**
1. `fa_app` updates ACL columns directly (first draft). Synchronous, but `chat-api` can write content.
2. Synchronous call from `chat-api` to a worker service. Adds a service and a network hop.
3. Admin API writes an `acl_change_requests` row plus an outbox event in one transaction; a worker applies it as `fa_worker` (chosen).
4. A Kafka listener in every `chat-api` instance for cache invalidation. Rejected: chat must not depend on Kafka, and a background consumer needs CPU outside requests on Cloud Run.

**Evidence.** Notion: a permission change is a metadata patch, with no re-embedding (https://www.notion.com/blog/two-years-of-vector-search-at-notion ); RLS write split D13a; decision-r2.md D14.8-D14.9, D16.8.

**Decision.** `chat-api` never writes content tables. `POST /v1/admin/documents/{id}/acl-changes` (and `DELETE /v1/admin/documents/{id}`) inserts an `acl_change_requests` row and an `AclChangeRequested` outbox row in one transaction and returns 202. The `acl-applier` worker role consumes `acl.changes.v1` and, as `fa_worker` (UPDATE grants on the ACL columns of `documents` and `chunks` only, own-tenant WITH CHECK), applies the change, marks the request `applied`, bumps `tenants.acl_version` and purges `answer_cache` rows that cite the document. Advisor entitlement changes remain a direct `UPDATE advisors` by a `tenant_admin`. `chat-api` does not consume Kafka; the 60 s `principal` cache TTL is the revocation bound for entitlements. For documents, `acl_version` in the answer-cache key makes older cached answers unreachable once the applier commits, and a cache hit that raced the bump is re-verified against freshly fetched chunks under the caller's RLS.

**Dissent.** None recorded.

**What it makes harder later.** The old ACL applies until the applier commits (relay plus consumer lag, tracked as `acl_apply_lag_s`); admin UX is two-step (202, then status); failed requests need operator handling.

**Trigger to revisit.** The lag is unacceptable (add a synchronous path or push invalidation, with a new ADR); a second ACL source appears.

## ADR-021: CI/CD with GitHub Actions, WIF and a gated deploy

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-05, G-06, G-28, G-47, G-51.

**Context.** The MVP CI cannot install its tools (`dev` extra missing), the eval gate cannot run, images build from unpinned floors, Terraform has no pipeline and image tags default to `latest`. One developer needs a pipeline that is cheap, keyless and blocks regressions.

**Options.**
1. Keep the MVP workflows and patch. Cost: unpinned builds, no deploy path.
2. GitHub Actions + Workload Identity Federation + Artifact Registry + Cloud Run tagged revisions (chosen). Cost: free runner minutes within plan; no stored cloud keys.
3. Cloud Build / GitLab. Rejected: second system, no gain.

**Evidence.** `gcloud run deploy --tag pr-N --no-traffic` preview pattern and WIF (evidence-r2.md, Compute / CI section); Cloud Run docs https://cloud.google.com/run/docs ; MVP.md §9 and G-05, G-06.

**Decision.** GitHub Actions with WIF. Lockfile installs only. Python: ruff, mypy, pytest, import-linter; frontend: eslint, tsc, vitest; security: trivy, gitleaks, pip-audit; `kong config parse`; `terraform fmt`, `validate`, `plan` on PR. L0 and the ~60-question eval subset run on the runner with real pgvector and Kafka service containers (ADR-017). Images pushed to Artifact Registry and referenced by digest. Deploy order: `migrate` Cloud Run job before traffic, then a tagged no-traffic revision, smoke test, then traffic shift. Provider keys for evals come from the CI secret store. CI service containers and compose pin `pgvector/pgvector:0.8.5-pg16` to match Cloud SQL (D16.20).

**Dissent.** None recorded.

**What it makes harder later.** The eval gate costs LLM money on every PR touching the path filter; the PR subset is kept to ~60 questions for that reason. Service containers pin the CI Postgres / Kafka versions, which must track the Cloud SQL and Confluent versions.

**Trigger to revisit.** CI cost or duration grows past the budget; more than one developer needs preview environments.

## ADR-020: Demo-on-demand operations and Cloud SQL sizing

**Status.** Accepted 2026-11-01. decided-by: researcher, on Keshav's input (budget $100-200/month, demo-on-demand; cloud prod is real but scales to zero).

**Context.** Keshav's budget cannot carry an always-on stack. An always-on `prod` profile is ~$300+/month.

**Options.**
1. Cloud SQL `db-g1-small` ~$26/month (no SLA). Cheap but small for pgvector HNSW.
2. Cloud SQL Enterprise 2 vCPU / 8 GiB ~$101 while running (HA ~$202), stopped by default (chosen).
3. AlloyDB 2 vCPU / 16 GiB ~$227+. Rejected on cost.
4. Always-on everything. Rejected: ~$300+.

**Evidence.** Cloud SQL pricing and AlloyDB figures in evidence-r2.md (Data layer); Memorystore Valkey shared-core-nano ~$23/month; budget recomputation D13r; Cloud Run billing (min instances bill while idle).

**Decision.** Terraform owns everything; `make demo-up` and `make demo-down` flip the Cloud SQL activation policy, `fa-gateway` / `chat-api` min instances, the worker pool count, and Cloud Scheduler pause state; Valkey is created on up and deleted on down. Down order (D13h): stop Scheduler triggers (the hourly `demo-ttl` job stays active), drain outbox and consumers to idle (10-minute timeout, then force; leftover outbox rows go out on the next up), scale the worker pool to 0, API and Kong min 0, delete Valkey, stop Cloud SQL. Up is exactly the reverse (D16.13): start Cloud SQL, create Valkey (fixed Memorystore name, outside Terraform state), deploy a new Kong revision with the Valkey endpoint and raise API / Kong min instances, scale the worker pool up, resume Scheduler triggers, then run `maintenance` and the `demo-prewarm` job inside the VPC. An hourly `demo-ttl` job (role `fa_maint`, Cloud Run admin rights) auto-downs the demo as a safety net. Terraform uses `lifecycle.ignore_changes` on `activation_policy`, `min_instance_count`, `manual_instance_count`. HA is a Terraform flag for load tests. Availability: the 99.5% SLO applies to the `prod` profile only; demo mode has no SLA (D13g). Budget: idle ~$40-55; demo month (~40 h, ~2,000 chats) ~$110-160.

**Dissent.** Simplicity proposal: `g1-small` always on.

**What it makes harder later.** Cold start: Cloud SQL start time is undocumented (spike, overview §10). Idle cost is fixed by the ALB ($18.25) and Cloud Armor (~$6-10, unverified). The idle estimate assumes a stopped instance bills storage only; unverified. Worker pool scale-to-0 and its Terraform support are unverified. Demo-down must drain the outbox first or audit events are delayed to the next up.

**Trigger to revisit.** Measured start time too slow for demos; a real customer needs availability (switch to `prod` profile); budget changes.

## ADR-019: Compute mapping: one image, three entrypoints, Cloud Run, Vite SPA

**Status.** Accepted 2026-11-01. decided-by: researcher (Keshav's inputs: keep FastAPI, React + TypeScript). Resolves G-13, G-49, G-51.

**Context.** One developer, learning goals, scale-to-zero, SSE streaming, continuous Kafka consumers, batch ETL.

**Options.**
1. GKE. Rejected: operating burden, no scale to zero at the budget.
2. Cloud Run services only (consumers as services). Services autoscale and bill on requests; consumers need continuous pull.
3. Cloud Run services + worker pools + jobs (chosen). Worker pools: no autoscaling, ~37% cheaper CPU.
4. Frontend as Next.js 16 standalone on Cloud Run vs Vite SPA on GCS + CDN. The SPA removes the BFF buffering hop and Next multi-instance issues.

**Evidence.** Cloud Run request timeout <= 60 min (SSE needs reconnect + `Last-Event-ID`), worker pools for continuous consumers, jobs <= 168 h; estimates: API min=1 ~$20-30, worker pool 0.5-1 vCPU ~$18-33, ETL jobs ~$1-2 (evidence-r2.md). FastAPI 0.162 native `fastapi.sse`; SQLAlchemy 2.1, asyncpg 0.32, alembic 1.20.

**Decision.** One Python image with entrypoints `api | worker | jobs`. Cloud Run service `chat-api` (SSE, explicit concurrency, timeout 3600, `Last-Event-ID` resume, `Idempotency-Key`), Cloud Run service `fa-gateway` (ADR-011), Cloud Run worker pool `fa-worker`, Cloud Run jobs (migrate, maintenance, etl, etl-public, dbt, eval, redteam, demo-prewarm, demo-ttl). Worker roles: outbox-relay, silver, contextualizer, indexer, acl-applier, eval-judge, bq-sink. All services use Direct VPC egress `private-ranges-only` (ADR-024). Vite + React 19 + TypeScript SPA on GCS behind the ALB. Local dev = docker compose with the same image. One Uvicorn process per container.

**Dissent.** None recorded.

**What it makes harder later.** A modular monolith needs import-linter discipline; worker pool autoscaling is manual (count flipped by `demo-up`); worker pool scale to 0 and Terraform support are to be verified.

**Trigger to revisit.** Retrieval needs separate scaling (ADR-004); a consumer needs autoscaling; SSR/SEO needs for the frontend.

## ADR-018: Observability and Langfuse Cloud

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-15, G-40, G-41, G-44.

**Context.** MVP tracing uses Langfuse v2 methods that do not exist in the locked SDK, so chat fails with keys set; logs carry raw queries; health is static.

**Options.**
1. Self-host Langfuse v4: needs ClickHouse + Redis + S3 + Postgres, >= 4 vCPU / 16 GiB. Rejected on cost.
2. Langfuse Cloud Hobby: free 50k units/month, 30-day retention (chosen), synthetic data only.
3. Drop LLM tracing. Rejected: eval datasets and judges use it.
4. Cloud Trace (free to 2.5M spans), Logging ($0.50/GiB after 50 GiB per project).

**Evidence.** https://langfuse.com/docs/observability/sdk/python/upgrade-path , https://langfuse.com/self-hosting , https://langfuse.com/pricing ; GCP ops pricing in evidence-r2.md.

**Decision.** Langfuse Cloud Hobby with Python SDK 5.x (5.1.0 current) behind one wrapper: `@observe` with `capture_input` / `capture_output` off on sensitive spans and `mask_otel_spans` for export masking (the legacy `mask=` does not cover OTel spans; D15.6); scrubbed input only, tagged by tenant (D13l). OpenTelemetry (Kong to API to workers, `traceparent` in Kafka headers) to Cloud Trace; SQL parameter capture off; no request bodies in logs or spans (D13o). Structured redacted logs; log-based metrics (TTFT, gate refusals, guard blocks, consumer lag); `/healthz` and `/readyz`; one availability SLO with burn-rate alert (prod only) plus latency SLOs; budget alerts.

**Dissent.** None recorded.

**What it makes harder later.** Traces live at a third party: acceptable only for synthetic data. SDK 5.x needs server v4 (self-hosting would too); Cloud compatibility is confirmed when the wrapper is built in E0. Hobby retention is 30 days.

**Trigger to revisit.** "Real firm data": self-host Langfuse v4 in the project or drop third-party tracing; Hobby unit cap reached.

## ADR-017: Evaluation strategy and deploy gate

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-06, G-54, G-56.

**Context.** The MVP eval scores only LLM-judged faithfulness and citation accuracy, with the same model family as judge, and never ran on a PR. JPM and Morgan Stanley run regression suites with per-component evals.

**Options.**
1. LLM-judge only (MVP). Rejected: no retrieval metrics, self-judging.
2. Layered evals L0-L4 with deterministic checks first (chosen).
3. Full 300-question suite on every PR. Rejected on cost and time.

**Evidence.** Ragas collections, Langfuse datasets, ARES https://arxiv.org/abs/2311.09476 (CI bounds), MT-Bench swap order https://arxiv.org/abs/2306.05685 , JPM Ask DAVID and Morgan Stanley https://openai.com/index/morgan-stanley/ , EvidenT https://aclanthology.org/2026.emnlp-industry.69.pdf , Bloomberg RAG risk (evidence-r2.md).

**Decision.** L0 deterministic on every PR with real pgvector + Kafka service containers: RLS leak matrix (reads, writes, FK probes, pooled-connection reuse), fail-closed, citation verifier, PII, model-retirement check. L1 retrieval recall@k / MRR / nDCG with dense / FTS / hybrid / rerank ablation. L2 Ragas collections (faithfulness, context precision / recall, noise sensitivity) with a Haiku 5.5 judge (judge differs from the answer model) calibrated on ~30 human labels (Cohen's kappa) and CI lower bounds reported. L3 cross-tenant / tier / jurisdiction refusal and promptfoo red team. L4 online sampled judge and thumbs: the `eval-judge` worker consumes `eval.sample.v1` (a 5-10% sample), judges with Haiku 5.5 and writes scores to Langfuse and `eval_scores`; Langfuse-side evaluators are not used (D14.14). The `eval` and `redteam` jobs run as `fa_eval`, pinned to a dedicated `eval` tenant (D16.18). Golden set 50 growing to ~300, tenant-parameterised. Gate: citation >= 0.95, faithfulness >= 0.90, leaks = 0, recall regression <= 2 pts. PR runs a ~60-question path-filtered subset; the full set runs weekly and before demos, and once against the fallback model.

**Dissent.** None recorded.

**What it makes harder later.** Human labels take time; the golden set must be curated per tenant; judge calibration drifts with model changes; gate thresholds need re-tuning when the corpus grows.

**Trigger to revisit.** Judge kappa below acceptable; gate flakiness; model change.

## ADR-016: Contextual retrieval at ingest, behind a flag

**Status.** Accepted 2026-11-01. decided-by: researcher.

**Context.** Chunks lose context when split; Anthropic reports top-20 retrieval failure 5.7% to 2.9% with contextual headers, at a one-time ~$1.02 per million document tokens.

**Options.**
1. Defer (simplicity). Cost: lower recall.
2. On, Haiku 5.5 via Batch API (-50%), behind a flag (chosen; cost proposal and scale proposal).
3. Semantic chunking. Rejected (arXiv 2410.13070: not worth it).

**Evidence.** https://www.anthropic.com/news/contextual-retrieval ; Haiku 5.5 $0.10 / $0.50 per MTok, Batch -50% (https://platform.claude.com/docs/en/about-claude/pricing ).

**Decision.** Generate headers with `claude-haiku-5-5` through the Batch API in the `contextualizer` role, enabled by `CONTEXTUAL_RETRIEVAL_ENABLED`. Input is redacted text; output must pass the PII scrub and tier rules. The L1 ablation decides whether it stays. The header is stored in `chunks.context_header` and is part of the embedded and FTS text.

**Dissent.** Simplicity proposal: defer.

**What it makes harder later.** Ingest becomes asynchronous on Batch API latency; changing the header prompt changes `chunk_hash` inputs and forces re-embedding.

**Trigger to revisit.** The ablation shows no gain; Batch cost or latency.

## ADR-015: Exact-match answer cache

**Status.** Accepted 2026-11-01. decided-by: researcher.

**Context.** Repeated questions cost an LLM call; in a regulated multi-tenant product a wrong cache hit is a leak or a stale answer.

**Options.**
1. Defer (simplicity).
2. Semantic cache. Rejected: cross-user leak risk.
3. Exact-match cache in a Postgres UNLOGGED table (chosen).

**Evidence.** Pattern ranking in evidence-r2.md (fix filtered ANN, then tenant + tier + corpus-version-keyed answer cache); D9, D13i.

**Decision.** Table `answer_cache` (UNLOGGED), own RLS + FORCE. Key = hash(tenant, tier, jurisdiction set, corpus_version (own and PUBLIC), acl_version, user entitlement version, prompt_version, model, normalized redacted question). Single-turn only, TTL 24 h. On a hit, re-run the citation verifier against freshly fetched chunks under the caller's RLS and recompute staleness; any failure is a miss. Turns that called a side-effect tool (`escalate_to_compliance`) are never cached. Purged by the `acl-applier` on ACL change and document delete, and by the `maintenance` job when expired (D16.8, D16.18).

**Dissent.** Simplicity proposal: defer.

**What it makes harder later.** Every new version input must be added to the key; UNLOGGED data is lost on a crash (acceptable for a cache); cache hit rate stays low because questions rarely repeat exactly.

**Trigger to revisit.** Measured hit ratio too low to justify the table; a safe semantic cache design emerges.

## ADR-014: ETL stack: Dagster, dbt, BigQuery, bronze/silver/gold

**Status.** Accepted 2026-11-01. decided-by: researcher, on Keshav's explicit goal to learn ETL / data engineering and his data input (synthetic per-tenant corpus + a real public source). Resolves G-03, G-07, G-39, G-62.

**Context.** MVP ingest is a script with random ids, no idempotency, a raw-content column and no suitability-rule path.

**Options.**
1. SQL views and a script (simplicity). Cheapest; no learning value.
2. Dagster OSS + dbt Core + BigQuery (chosen). All three are free at this size.
3. Cloud Composer. Rejected: continuous billing. Dagster+ Solo $10/month: not needed.
4. Document AI for parsing: only as an OCR fallback ($1.50/1k pages).

**Evidence.** Bronze / silver / gold, Dagster sensors https://dagster.io/docs/guides/automate/sensors , SEC access rules https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data , Notion per-span content hash https://www.notion.com/blog/two-years-of-vector-search-at-notion , Uber replayable index https://www.uber.com/us/en/blog/how-uber-indexes-streaming-data-with-pull-based-ingestion-in-opensearch/ , BigQuery free 1 TiB queries (evidence-r2.md).

**Decision.** Bronze: GCS by sha256, raw immutable, with URL and fetch time. Silver (Parquet in GCS `silver/`, partitioned tenant / dt): Docling parse (HTML supported; first public source = fund summary prospectuses 497K; inline-XBRL tables tested in a spike), Presidio scrub, structure-aware chunking with Voyage `count_tokens`, Pandera validation, rejects table, `parser_version`. Contextual headers (ADR-016), suitability-rule extraction (Haiku structured output, validated; fixes G-07), embed-indexer upserts. Gold: dbt Core on Postgres as `fa_dbt`: views with `security_invoker = true`, or incremental models with a tenant predicate, never full-table rebuilds; the `gold` schema is owned by `fa_dbt` and exempt from the not-owner assertion; CI asserts RLS enabled, forced and policies present for every tenant-schema table (D13n, D16.14). Dagster OSS assets (partitioned tenant x date, `run_key` dedupe) run daemon-less as Cloud Run jobs from Cloud Scheduler (`dagster asset materialize`), with run and event storage in Postgres (`dagster-postgres`, database `dagster` on the same Cloud SQL instance, role `fa_dagster`, no access to app schemas) so run history survives (D15.4); `dagster dev` locally; no cloud daemon until > 10 tenants or a sensor is needed. Silver, contextualize and embed-indexer run as worker consumers (`fa_worker`); PUBLIC ingest runs all stages in-process in the `etl-public` job (`fa_etl_public`); the embed-indexer bumps `corpus_version` after the `chunks` upsert (D14.5, D16.6, D16.7). BigQuery marts for audit / usage / eval analytics: redacted text only, partitioned by day, clustered by `tenant_id`, `maximum_bytes_billed` on every query; per-tenant authorized views are the primary isolation and row access policies the second layer (they do not prune partitions and can bill more rows; D15.5); marts built by `dbt-bigquery`; fed by a Kafka sink worker with event-id dedupe. Idempotent ingest: unique `(tenant_id, chunk_hash, embed_model)`, re-embed only changed chunks, ACL change = metadata UPDATE, `documents.raw_content` dropped.

**Dissent.** Simplicity proposal: SQL views suffice for the product; a second platform to run and learn.

**What it makes harder later.** Three tools to keep current; dbt runs need a dedicated per-tenant connection to set `app.tenant_id`; EDGAR limits (<= 10 req/s, declared User-Agent) shape the fetcher. Two execution paths (worker consumers for tenants, in-process job for PUBLIC) must stay behaviourally identical.

**Trigger to revisit.** > 10 tenants or a sensor need (Dagster daemon); Docling fails on 497K / XBRL (spike result); BigQuery cost.

## ADR-013: Kafka on Confluent Cloud Basic, Schema Registry, transactional outbox

**Status.** Accepted 2026-11-01. decided-by: researcher, on Keshav's goal that Kafka is a first-class learning part and that dev runs Kafka locally.

**Context.** Event volume is ~1-5k events/day; no reference puts Kafka in front of pgvector at tens of tenants; Kafka is justified for learning, replay and per-tenant ordering, not load.

**Options.**
1. GCP Managed Kafka: min 3 vCPU, 3 zones, ~$189-248/month. Rejected.
2. Confluent Cloud Basic: first eCKU free then $0.14/eCKU-h, $0.05/GB; ~$0-10/month (UNVERIFIED estimate; confirm in console); 99.5% SLA; Essentials Schema Registry free (100 schemas); $400 trial (chosen).
3. Aiven Free (250 KiB/s, 5 topics) $0 / Developer $35. 4. Self-hosted KRaft on e2-medium ~$27, single broker. 5. Pub/Sub ~$0 but no Kafka API.
6. Outbox vs fire-and-forget (D4): fire-and-forget loses audit when Kafka is down.

**Evidence.** https://cloud.google.com/managed-service-for-apache-kafka/pricing , https://www.confluent.io/pricing/ , https://github.com/confluentinc/confluent-kafka-python , Debezium outbox https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html .

**Decision.** Confluent Cloud Basic in us-central1 (create the cluster first: the Schema Registry region is fixed by the first cluster, D13q); `apache/kafka:4.4.0` KRaft and cp-schema-registry locally; `confluent-kafka` 2.16.1. Versioned topics `*.v1` keyed by `tenant_id`; JSON Schema in Schema Registry generated from Pydantic (D5). Idempotent producers; at-least-once consumers with idempotent sinks (`processed_events`); DLQ topic `dlq.v1`. Transactional outbox table with a relay loop in the worker, no Debezium (D4); chat never depends on Kafka. Payloads minimised (ids, hashes, redacted text only), separate API keys per service, DLQ payloads redacted (D13j). Per-tenant topics rejected (topic and partition count). `chat-api` has no Kafka credentials and no consumer: its events leave through the outbox and the relay, and the 60 s entitlement TTL is the revocation bound (D14.9, ADR-022). Confluent Basic has no RBAC: one service account and API key per service, Kafka ACLs per service account, limits of 50 API keys, 1,000 ACLs and 1,500 partitions (D15.8). Pipeline consumers reject events whose envelope tenant differs from the key or is PUBLIC (D16.6). Added topics: `eval.sample.v1` (judge input), `ingest.analytics.v1` (PUBLIC ingest analytics); no gateway audit topic (ADR-023).

**Dissent.** All three proposals: Schema Registry is an extra component and Pydantic envelopes alone would work. Kept for the Kafka learning goal at small cost.

**What it makes harder later.** Confluent Basic has no in-cluster RBAC, so tenant isolation of events rests on payload minimisation; the relay is custom code to operate; Basic has 99.5% SLA only.

**Trigger to revisit.** "Real firm data": Confluent Standard RBAC; > 100 schemas; Debezium outbox connector as an optional learning epic.

## ADR-012: Edge: external ALB + Cloud Armor, same origin

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-02, G-13, G-46.

**Context.** The MVP exposes backend and frontend with `allUsers` invoker and no load balancer, WAF or CORS.

**Options.**
1. Firebase Hosting + public API with JWT (cost proposal): cheaper, but a public API.
2. External ALB + Cloud Armor, same origin (chosen): `/*` to a GCS backend bucket (SPA, CDN), `/v1/*` to the gateway.

**Evidence.** Network guidance in evidence-r2.md (ALB + Cloud Armor ~$0.75/1M requests + policy fee; Cloud Run ingress internal-and-cloud-load-balancing); ALB $18.25/month; Cloud Armor ~$6-10/month UNVERIFIED.

**Decision.** External ALB with Cloud Armor (DDoS, WAF, geo rules) in front of everything; SPA on the GCS backend bucket; `/v1/*` goes to Kong (`fa-gateway`, ADR-011). Persistent (~$18-25/month) because certificate provisioning is slow, so `demo-down` never removes it. `fa-gateway` has the Cloud Run invoker check disabled (the only service where it is; Google recommends this over `allUsers`, https://docs.cloud.google.com/run/docs/authenticating/public ), ingress internal-and-cloud-load-balancing, Cloud Armor on the backend service; no `allUsers` anywhere (D15.1, D16.1). IAP was rejected: it replaces the caller identity and conflicts with end-user ID tokens. E10 checks the org policy `constraints/run.managed.requireInvokerIam`.

**Dissent.** Cost proposal: Firebase Hosting.

**What it makes harder later.** Fixed idle cost; the invoker-check exception on `fa-gateway` depends on the org policy allowing it (checked in E10).

**Trigger to revisit.** Cloud Armor cost verification fails the idle budget; budget change.

## ADR-011: Kong as the edge API gateway (Keshav's decision)

**Status.** Accepted 2026-11-01. decided-by: Keshav ("include kong for rate limiting and proxy plugins as well we need it"). Binding. Resolves G-02, G-10, G-11, G-14, G-46, G-48.

**Context.** The three proposals dropped Kong (Cloud Armor + FastAPI limits suffice). Keshav requires it. Kong docs check, 2026-11-01: Kong OSS ends at 3.9.x (latest 3.9.4, 2026-10-12); 3.10+ has no free mode. OSS has `rate-limiting` (`limit_by`: consumer, credential, ip, service, header, path; policies local / redis in DB-less), `request-size-limiting`, `cors`, `correlation-id`, `ip-restriction`, `bot-detection`, `request/response-transformer`, `pre-function`, `prometheus`, `opentelemetry`, `http-log`, `proxy-cache`, `ai-proxy`, `ai-prompt-guard`. Enterprise-only: `openid-connect` (JWKS), `rate-limiting-advanced`, `ai-rate-limiting-advanced`, `ai-proxy-advanced`, `ai-semantic-cache`, `ai-sanitizer`. OSS `jwt` uses static per-consumer keys (no JWKS), so it cannot verify rotating Google ID tokens. OSS `ai-proxy` 3.9 has no native Anthropic Messages format (`llm_format anthropic` is 3.10+).

**Options.**
1. No gateway: Cloud Armor + FastAPI (all three proposals). Cheapest, fewest hops.
2. Kong OSS 3.9.4 DB-less on Cloud Run (chosen). Cost: a hop, a Cloud Run service (min 0, max 2), Valkey ~$0.03/h while up.
3. Kong 3.10+ / Konnect / Enterprise. Rejected: paid.
4. Apigee ($365+/month) and API Gateway (streaming preview). Rejected.

**Evidence.** https://developer.konghq.com/plugins/rate-limiting/reference/ ; Kong docs check recorded in decision-r2.md D12; MVP.md G-14 (the MVP `identifier` parameter does not exist).

**Decision.** External ALB + Cloud Armor, then Kong (`fa-gateway`, Cloud Run, ingress internal-and-cloud-load-balancing, invoker check disabled on this service only (no `allUsers`; D15.1, D16.1), admin API off, status listener), then `chat-api` (ingress internal, `run.invoker` only for the Kong service account). Kong `pre-function` fetches a Google ID token from the metadata server (audience = chat-api URL, cached until near expiry) into `X-Serverless-Authorization`, leaving the user's `Authorization` intact; verified in a spike (fallback = ingress-internal + app JWT, recorded as an ADR). Token verification stays in FastAPI; Kong does not trust or set identity headers and a `request-transformer` strips client `X-User-Id`, `X-Tenant-Id`, `X-Serverless-Authorization`. Rate limits (OSS only): per client IP and per session key (`limit_by: header` on `X-RL-Key = sha256(Authorization)`, set by the `pre-function`, so raw tokens never reach Valkey keys; D16.10), stricter on `POST /v1/chat`, request-size limit, 429 with `Retry-After`; policy `redis` against Valkey (local container; Memorystore shared-core-nano created by `demo-up` and deleted by `demo-down` with a fixed instance name, outside Terraform state; `demo-up` passes the endpoint to Kong by deploying a new revision), `sync_rate: 0` on the chat route. Per-tenant token budgets and concurrency stay in FastAPI. Also `cors` (SPA allow-list), `correlation-id`, `opentelemetry`, `prometheus`, `file-log` to stdout with a field whitelist into Cloud Logging and a log sink to BigQuery (fixes G-48, ADR-023; no `/internal/*` routes), `bot-detection`. SSE route: `response_buffering: false`, `request_buffering: false`, `read_timeout` 3,600,000 ms; verified in a spike. LLM egress ("proxy plugins"): spike `ai-proxy` `route_type: preserve` (or a plain proxy) to `api.anthropic.com` with streaming and tool use; if it passes, `LLMClient` calls Anthropic through an internal Kong route that adds the API key, a global LLM rate limit and `log_statistics`, protected by `key-auth` (consumer `chat-api`, key from Secret Manager) and `ip-restriction` to the VPC range (D16.11); if not, `LLMClient` calls Anthropic directly (ADR). Native Messages format only. Local: `kong:3.9.4` + Valkey in compose; `kong.yml` validated with `kong config parse`. Kong reaches `chat-api` through Direct VPC egress `private-ranges-only` with a private `run.app` zone (ADR-024). Not used: Konnect, Enterprise image, `openid-connect`, `ai-*` Enterprise plugins, `http-log`.

**Dissent.** Cost, simplicity and scale proposals: Kong OSS duplicates Cloud Armor and FastAPI limits, cannot see the verified tenant, and adds a hop and a service. Kept because Keshav requires it.

**What it makes harder later.** An extra hop and failure surface for SSE (buffering risk until the spike passes); the OSS line ends at 3.9.x so there is no upgrade path inside OSS; per-tenant limiting cannot live in Kong; three spikes (SSE, IAM header, egress) can each change the design; the egress route would put the Anthropic key in Kong.

**Trigger to revisit.** Any spike fails (record a conditional ADR); 3.9.x stops receiving fixes; Keshav drops the requirement.

## ADR-010: Authentication with Identity Platform multi-tenancy and tenant discovery

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-01.

**Context.** MVP identity is a header over 4 hard-coded users. Needs one sign-in configuration per firm and a path to SSO.

**Options.**
1. Single Identity Platform pool (simplicity, cost). No per-firm configuration.
2. Identity Platform multi-tenancy, one IdP tenant per firm (chosen; D6). Billing must be enabled for > 2 tenants; email/password free to 50k MAU; SAML/OIDC $0.015/MAU after 50.
3. Auth0 Free (25k MAU, 5 orgs), Clerk free 50k MRU. Rejected: another vendor.
4. Verify in Kong: OSS `jwt` has static keys; `openid-connect` is Enterprise. Rejected.

**Evidence.** https://docs.cloud.google.com/identity-platform/docs/multi-tenancy ; PostgreSQL docs on SECURITY DEFINER risk via D13m review.

**Decision.** FastAPI verifies ID tokens tenant-aware with firebase-admin: the `firebase.tenant` claim names the IdP tenant and `tenant_mgt.auth_for_tenant(tenant_id).verify_id_token` checks signature, `aud`, `iss`, `exp` and raises `TenantIdMismatchError` (D15.3; https://docs.cloud.google.com/identity-platform/docs/multi-tenancy-managing-tenants ). The token identifies only `sub` and the IdP tenant; entitlements (tier, jurisdictions, licenses, role) come from `advisors` (60 s cache, invalidated on `acl.changes.v1`). Tenant discovery: the SPA resolves the firm from `/t/<slug>` through the public `GET /v1/tenants/{slug}`, which returns only `{display_name, idp_tenant_id}` from a `SECURITY DEFINER` function `fa_tenant_lookup`, reviewed in CI and the only such function allowed (D13m); it is owned by the NOLOGIN role `fa_lookup` (not `fa_owner`), which has a SELECT policy on `tenants` only, with `EXECUTE` revoked from PUBLIC and granted to `fa_app` (D16.2). It serves both slug discovery and the `idp_tenant_id` to `tenants.id` mapping (D14.4). The IdP tenant id maps to `tenants.id` before settings are set.

**Dissent.** Cost and simplicity proposals: a single pool.

**What it makes harder later.** Billing must stay enabled; the public discovery endpoint allows slug enumeration (bounded by the Kong IP limit); one `SECURITY DEFINER` exception must be kept reviewed.

**Trigger to revisit.** SSO requirement; > 50 tenants; enterprise customer needs a different IdP.

## ADR-009: Guardrails (OWASP LLM Top 10 2025)

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-04, G-17, G-23, G-37, G-38, G-41, G-42, G-45, G-55.

**Context.** The MVP sends the user message unredacted to Anthropic, Voyage and Langfuse, emits raw tool JSON to the client, and has no injection screen. Measured: classifier-style rails 20-250 ms and 0-4% false positives; LLM-based rails 0.5-1.5 s and up to 16% (arXiv 2605.06669); stacking guards compounds false positives.

**Options.**
1. LLM-based rails (NeMo). Rejected: latency, false positives.
2. Cloud DLP API ($3/GiB after 1 GiB free) for PII. Rejected: network call; Presidio is in-process.
3. Deterministic guards plus Model Armor (chosen). Model Armor free to 2M tokens/month then $0.10/1M; REST API detects, the app acts.

**Evidence.** https://genai.owasp.org/llm-top-10/ ; https://docs.cloud.google.com/model-armor/overview ; https://data-privacy-stack.github.io/presidio/ ; Anthropic guidance (untrusted content only in `tool_result`); EvidenT https://aclanthology.org/2026.emnlp-industry.69.pdf ; ALCE https://arxiv.org/abs/2305.14627 .

**Decision.** Cloud Armor edge limits; input cap; Presidio in-process pseudonymization (presidio-analyzer 2.2.x, spaCy `en_core_web_sm`, latency benchmarked in E4) before embed / LLM / traces / logs; Model Armor input screen in parallel with embed (500 ms timeout, fail closed); untrusted content only in a JSON-encoded `tool_result`; least-privilege tools (tenant, tier, jurisdiction never tool arguments); `escalate_to_compliance` uses server-side licenses and persists; the client receives tool name + status only; errors carry codes, not exception text; sentence-buffered output PII redaction; deterministic citation verifier (every `[n]` in retrieved chunk ids, quote overlap) with server-emitted citation events carrying redacted excerpts; React renders sanitized markdown only; no LLM-based rails on the hot path.

**Dissent.** None recorded.

**What it makes harder later.** Presidio has no recall guarantee; fail-closed Model Armor makes chat depend on it (500 ms timeout); sentence buffering adds a small latency to first visible tokens; the citation verifier can reject good answers and must be tuned by the evals.

**Trigger to revisit.** Measured Presidio recall or Model Armor latency / false positives outside tolerance.

## ADR-008: Hybrid retrieval, rerank, confidence gate and chunking

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-33, G-34, G-35, G-36, G-52, G-62.

**Context.** MVP retrieval is dense-only IVFFlat on an empty table, `input_type="document"` for queries, filters applied after the ANN scan (short results), no rerank, no gate.

**Options.**
1. Dense only (MVP).
2. Hybrid dense + FTS with RRF in one SQL statement (Wang et al. arXiv 2407.01219: +2.3 nDCG@10 for +0.6 s prototype).
3. Add a cross-encoder rerank of the top candidates (RankGPT arXiv 2304.09542; Anthropic failure 2.9% to 1.9%). LLM listwise rerank costs 11-32 s: rejected. HyDE +4.6 s: rejected. SPLADE, ColBERT, GraphRAG, RAPTOR, Self-RAG, semantic chunking: not now.
4. Gate: CRAG-style confidence gate (arXiv 2401.15884), no web fallback.
5. pg_textsearch (BM25) needs PG17+ (not on Cloud SQL PG16); `ts_rank` is not BM25.

**Evidence.** pgvector README (HNSW defaults m 16, ef_construction 64, ef_search 40; iterative scan; halfvec <= 4,000 dims) https://github.com/pgvector/pgvector ; practitioner 52/400 queries returned 0 rows with default HNSW https://dev.to/ji_ai/pgvector-hnsw-filtering-returned-0-rows-for-52-of-my-400-queries-ghp ; AWS Aurora iterative scan https://aws.amazon.com/blogs/database/supercharging-vector-search-performance-and-relevance-with-pgvector-0-8-0-on-amazon-aurora-postgresql/ ; Voyage https://docs.voyageai.com/docs/embeddings ; Cloud SQL extensions https://docs.cloud.google.com/sql/docs/postgres/extensions ; rerank price $0.05/M and Tier-1 2M TPM (D13e).

**Decision.** Voyage `voyage-4` with `input_type` query / document; `halfvec(1024)`; HNSW (m 16, ef_construction 64) with `SET LOCAL hnsw.iterative_scan = relaxed_order`, `hnsw.max_scan_tuples = 20000`, `ef_search` ~80-100; `tsvector` + GIN FTS leg (`websearch_to_tsquery`) for rule ids and tickers; RRF `k = 60` in one SQL statement with RLS on both legs; Voyage `rerank-2.5-lite` (or `rerank-2.5`) with timeout; a rerank timeout or 429 falls back to RRF order and marks the turn degraded (SSE `meta {retrieval_degraded: true}` and `messages.retrieval_degraded`), increments `rerank_fallback_total{reason}`, and alerts when > 5% of turns in 15 min are degraded (visible, so not silent; D14.2); kept or dropped by the eval ablation on recall and latency; `RERANK_CANDIDATES` default 15 (range 10-30), set by the L1 ablation (D14.1); CRAG-style gate yields "no firm documentation" + escalate offer without an LLM call; parent expansion; staleness computed server-side from today's date. Chunking: structure-aware 256-512-token children, ~1k-token parents, title then section heading prefix. Latency targets (estimates): TTFT p50 < 2.0 s, p95 < 3.5 s; first stage p95 < 300 ms; rerank p95 < 700 ms; full answer p95 < 8 s.

**Dissent.** None recorded. The skeptic replaced rerank-2 with rerank-2.5-lite and relaxed the earlier latency targets (D13e).

**What it makes harder later.** FTS is not BM25; rerank is single-vendor (Voyage) and rate limited (about 5 QPS on Tier 1); the gate threshold must be tuned by evals; ANN with RLS needs iterative scan tests.

**Trigger to revisit.** BM25 available on managed Postgres (PG17+); recall regression; ANN p95 > 100 ms; rerank latency or TPM unmet.

## ADR-007: Retrieve-first orchestration and conversation state

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-22, G-32, G-53.

**Context.** MVP is a ReAct loop of up to 5 non-streaming LLM calls with the DB connection held open; no conversation memory.

**Options.**
1. ReAct loop with the model deciding when to retrieve (MVP). Slow, non-streaming, injection surface.
2. Retrieve-first in code, then one streaming call with tools, max 3 iterations (chosen).
3. Multi-agent / sub-agent orchestration (JPM Ask DAVID). Not now.

**Evidence.** Anthropic guidance: untrusted content only in `tool_result`, JSON-encoded; Azure single retrieval layer https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/secure-multitenant-rag ; JPM figures (<50% to ~80% with retrieval tuning, ~90% with orchestration; evidence-r2.md).

**Decision.** Retrieval runs in code before the first LLM call and is injected as a JSON-encoded `tool_result`; one streaming call with tools (`lookup_product_factsheet`, `lookup_suitability_rule`, `escalate_to_compliance`, follow-up `search_firm_kb`), max 3 iterations, `max_tokens` bounded. Short DB transactions, never held across the LLM loop. Conversation state in Postgres: `conversations` and `messages` (monthly range partitions), last 6 turns <= 3k tokens, follow-up condensation with Haiku only when history exists (D11). Persist events in `turn_events` for resume.

**Dissent.** None recorded.

**What it makes harder later.** The model cannot skip retrieval, so every question pays embed + SQL (+ rerank); the gate handles irrelevant questions; the synthetic prefetch tool call is a convention the prompt must follow.

**Trigger to revisit.** The follow-up search tool hurts precision in evals; multi-step tasks need sub-agents.

## ADR-006: Models and prompt caching

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves the urgent retirement of `claude-sonnet-4-20250514` (G-58).

**Context.** `claude-sonnet-4-20250514` retired 2026-06-15 (app and evals fail today); `claude-sonnet-4-5` retires 2026-11-30; `claude-haiku-4-5` deprecation ~2026-10-15. `temperature`, `top_p`, `top_k` removed in the API on 2026-10-21 (400).

**Options.**
1. Sonnet 5.5 $2 / $10 per MTok (cache read $0.10; cache minimum 512 tokens) (chosen for answers).
2. Sonnet 4.6 $3 / $15 (1,024-token cache minimum): fallback only.
3. Haiku 5.5 $0.10 / $0.50 for aux work (chosen); Haiku 4.5 $1 / $5 rejected. Batch API -50%.

**Evidence.** https://platform.claude.com/docs/en/about-claude/model-deprecations , https://platform.claude.com/docs/en/about-claude/pricing .

**Decision.** Answer `claude-sonnet-5-5`; judge, contextual headers, rule extraction, condensation and citation spot-checks `claude-haiku-5-5` (judge differs from the answer model); Batch API for offline / bulk. No `temperature` / `top_p` / `top_k`. Model ids only from config; CI and readiness fail on a retired or soon-retiring model. Prompt caching on system prompt + tools (cache order tools, system, messages); tenant / user / date text after the breakpoint; tool definitions are versioned with the prompt because changing them invalidates the cache.

**Dissent.** None recorded.

**What it makes harder later.** Model churn is continuous: the retirement check is a standing maintenance cost; changing prompt or tools invalidates caches and answer-cache keys.

**Trigger to revisit.** Any deprecation notice; price change; a model passes the eval gate at lower cost.

## ADR-005: Drop LiteLLM; in-process LLMClient with same-provider fallback

**Status.** Accepted 2026-11-01. decided-by: researcher (Kong egress interaction: ADR-011). Resolves G-08, G-09, G-10, G-24, G-31.

**Context.** The MVP LiteLLM config shuffles across Claude, GPT-4o and Gemini under one model name (G-08), its fallback key matches nothing (G-09), and recent LiteLLM releases had OOM regressions.

**Options.**
1. Keep LiteLLM pinned v1.106.6: >= 4 Gi per pod, canary + soak, Redis for > 1 replica, budgets need its DB.
2. Kong `ai-proxy` as the LLM layer: OSS 3.9 has no native Anthropic Messages format.
3. Thin in-process `LLMClient` over the Anthropic SDK (chosen).
4. Cross-provider fallback. Rejected: changes regulated answers.

**Evidence.** https://docs.litellm.ai/docs/routing , https://docs.litellm.ai/blog/retry-breadcrumb-oom-incident ; Kong ai-proxy limits (D12).

**Decision.** `LLMClient` with streaming, explicit timeouts, retries with jitter, circuit breaker, same-provider fallback only (`claude-sonnet-5-5` to `claude-sonnet-4-6`). The fallback costs 50% more ($3 / $15), has a 1,024-token cache minimum and its own cache; it is budgeted and enabled only if it passes the eval gate (D13f). Model ids only from config. Base URL from config: direct, or Kong egress route if the spike passes (ADR-011), protected by `key-auth` (consumer `chat-api`) and `ip-restriction` (D16.11).

**Dissent.** None recorded.

**What it makes harder later.** Adding another provider means writing it; no central spend dashboard (usage goes through `chat.usage.v1` and Langfuse); the breaker and fallback logic is ours to test.

**Trigger to revisit.** A second model provider is required (only after equivalence evals); the Kong egress spike changes the path.

## ADR-004: Single retrieval enforcement point

**Status.** Accepted 2026-11-01. decided-by: researcher. Resolves G-20, G-21, G-35.

**Context.** In the MVP, tools query content tables directly with app-level WHERE clauses, and only `chunks` has RLS. Azure guidance: a single retrieval API layer is the enforcement point; every retrieval, including agent tool calls, carries tenant and user filters.

**Options.**
1. Separate retrieval service (scale proposal): stronger isolation, +network hop, +service.
2. In-process module with a second pool and DB role `fa_retrieval` (original D1): double connections, two snapshots, a nominal boundary.
3. In-process `RetrievalService(principal)` module; one DB login role per process; import-linter + test; RLS as the backstop (chosen, D13c).

**Evidence.** https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/secure-multitenant-rag .

**Decision.** `RetrievalService(principal)` is the only code that touches content tables; tools never take tenant, tier or jurisdiction arguments; entitlements come from `advisors` (60 s cache; the TTL is the revocation bound, no Kafka invalidation, D14.9). `fa_app` has SELECT only on content tables; ACL changes and deletes are applied by the `acl-applier` worker (ADR-022). Roles per process are listed in overview §5.3.

**Dissent.** Scale proposal: a network boundary is stronger isolation than a module boundary.

**What it makes harder later.** The boundary is enforced by tooling, not topology; a developer error inside `retrieval` is the risk the RLS backstop and L0 tests cover.

**Trigger to revisit.** Retrieval needs separate scaling, or a second consumer of retrieval appears: extract it to its own Cloud Run service with its own role.

## ADR-003: LIST partitions of chunks by tenant

**Status.** Accepted 2026-11-01. decided-by: researcher (skeptic correction D13b replaced the original HASH decision).

**Context.** Pgvector applies filters after the ANN scan. Partitioning gives each tenant its own HNSW and GIN index and prunes at plan time.

**Options.**
1. Partition at a trigger (simplicity, cost proposals). Cheap now; retrofit needs a replay.
2. HASH(tenant_id) x 8 partitions (original D2). Four tenant keys in 8 hash buckets collide with probability ~59%.
3. LIST partitions: one per tenant, one for PUBLIC, plus DEFAULT (chosen).

**Evidence.** Practitioner: 40 tenants / 1.2M chunks, default HNSW returned 0 rows for 52/400 queries; small tenants best with exact scan (https://dev.to/ji_ai/pgvector-hnsw-filtering-returned-0-rows-for-52-of-my-400-queries-ghp ); pgvector README on partitioning https://github.com/pgvector/pgvector ; runtime pruning with the RLS `current_setting` policy confirmed by test on the 8-partition setup ("Subplans Removed: 6 of 8", pgvector 0.8.7 / PG16.15).

**Decision.** `chunks` is `PARTITION BY LIST (tenant_id)`, with HNSW and GIN per partition declared on the parent. Tenant onboarding creates its partition and indexes in the `migrate` job. Partitions get no grants; runtime roles reach them only through the partitioned parent (D16.3). PUBLIC can be sub-partitioned by source later.

**Dissent.** Simplicity proposal: partitioning adds indexes and planner complexity for 3 tenants.

**What it makes harder later.** Onboarding is a migration step, not a row insert; rows in the DEFAULT partition mean a missed onboarding; planner and migration cost at ~50 partitions is unmeasured (E1 measures it); the pruning test must be repeated on LIST partitions.

**Trigger to revisit.** One tenant > 250k chunks, total > 2M chunks, or ANN p95 > 100 ms: grow partitions or silo a tenant through `tenants.shard_id`. PUBLIC > 250k chunks: sub-partition by source.

## ADR-002: Pool tenancy in one Postgres with RLS (read/write split, role per process)

**Status.** Accepted 2026-11-01. decided-by: researcher; scope input by Keshav (demo multi-tenant: 2-3 synthetic firms, designed for 50 tenants / 2,000 advisors). Resolves G-12, G-19, G-20, G-21, G-43.

**Context.** The MVP applies RLS to `chunks` only, connects as a superuser and uses session-level `SET` on pooled connections. v2 must isolate several firms in one deployment at demo cost.

**Options.**
1. Silo, project-per-tenant (Google multi-tenant agentic reference): strongest isolation; cost per tenant exceeds the budget.
2. Bridge: schema or database per tenant.
3. Pool: shared tables with `tenant_id` and RLS (chosen). Cheapest; no per-tenant CMEK or performance isolation (AWS pool / bridge / silo).

**Evidence.** https://aws.amazon.com/blogs/machine-learning/multi-tenant-rag-with-amazon-bedrock-knowledge-bases/ , https://aws.amazon.com/blogs/database/self-managed-multi-tenant-vector-search-with-amazon-aurora-postgresql/ , https://docs.cloud.google.com/architecture/multi-tenant-agentic-ai-system , https://www.postgresql.org/docs/16/ddl-rowsecurity.html , https://www.postgresql.org/docs/16/sql-set.html , Notion workspace-ID sharding https://www.notion.com/blog/two-years-of-vector-search-at-notion .

**Decision.** `tenant_id NOT NULL` on every table; `ENABLE` + `FORCE` RLS on all tenant tables; the app connects as a non-owner, non-superuser, NOBYPASSRLS login role (no `SET ROLE`); per-transaction `set_config('app.*', $n, true)` with bind parameters; `current_setting` without `missing_ok` (fail closed); short transactions never held across the LLM loop; composite FKs `(tenant_id, ...)` because FK checks bypass RLS; migrations as a separate owner role in a Cloud Run job; startup and readiness assert role flags, FORCE RLS on every table and pgvector >= 0.8. A reserved PUBLIC tenant holds the public corpus. Write split (D13a): SELECT = own tenant OR PUBLIC; INSERT / UPDATE / DELETE = own tenant only; only `fa_etl_public` writes PUBLIC. One DB login role per process (D13c): `fa_app` (chat-api, SELECT only on content tables), `fa_worker`, `fa_etl`, `fa_etl_public`, `fa_dbt`, `fa_owner`, plus `fa_maint` (maintenance, `demo-ttl`), `fa_eval` (eval and redteam, pinned to the `eval` tenant), `fa_lookup` (NOLOGIN, owns the one `SECURITY DEFINER` function) and `fa_dagster` (separate database). `tenants` is under FORCE RLS with policies for `fa_app` (own and PUBLIC rows), `fa_lookup` (SELECT) and `fa_owner` (onboarding) (D16.2). `advisors`: SELECT own row or, for `tenant_admin`, the tenant; UPDATE only for `tenant_admin`, so no self-escalation (D16.4). Tenant and monthly partitions carry no grants (D16.3). Two explicit exemptions to the not-owner assertion: `fa_dbt` on schema `gold`, `fa_maint` on `messages` (partition DDL needs ownership of the parent). Entitlements are cached <= 60 s per process and the TTL is the revocation bound; `chat-api` does not consume Kafka (D14.9, ADR-022). The L0 leak matrix tests reads and writes, FK probes, direct partition access, advisor self-escalation and pooled-connection reuse.

**Dissent.** None among the three proposals (all agreed); the skeptic found the write-through-PUBLIC hole, fixed by D13a.

**What it makes harder later.** One RLS or code bug can expose all tenants, so the leak matrix is a permanent gate; six roles multiply pools and secrets; no per-tenant CMEK or performance isolation (noisy neighbours); `SECURITY DEFINER` is banned except `fa_tenant_lookup`.

**Trigger to revisit.** A tenant requires CMEK or performance isolation, "real firm data", or > 50 tenants: silo through `tenants.shard_id`.

## ADR-001: As-built MVP is the baseline

Date: 2026-11-01. Status: accepted (decided by the orchestrator with Keshav).

**Context.** FinAdvisor is an interview-grade MVP, never deployed: Docker, CI on a real PR, `terraform validate`, the live eval and live Kong/LiteLLM/Langfuse checks were all deferred (`TODO.md:763, 818, 847, 877`; commit d6c2bd3). Its docs (README, architecture.md, mvp.md, threat model) disagree with the code in many places. Later research and architecture work needs one trusted statement of what actually exists.

**Options.**
1. Map the code as it is, and use that as the reference. Cost: one mapping and verification round, no design work yet.
2. Start from the docs' intended architecture. Rejected: the docs describe a JWT auth, Kong token budget and PII plugins, citation events and a working cloud deploy that the code does not have.
3. Design the target architecture now. Rejected for this run: no research has been done on scale, cost or compliance fit; the numbers Keshav gave (about 50 advisors, under 5 QPS, under $100 per month, US/EU/UK synthetic corpus) have not yet been checked against vendor facts.

**Evidence.** `arch/MVP.md` was built from four independent code maps, a skeptic re-read of the highest-risk claims, vendor-doc checks (pgvector, PostgreSQL 16 RLS, Voyage, LiteLLM) and spot-checks of every quoted `file:line` at d6c2bd3. It records 62 gaps: 13 critical, 16 high, 27 medium, 6 low (MVP.md §13).

**Decision.** `arch/MVP.md` records the code as of commit d6c2bd3 and is the reference for later research. `arch/stack.md` lists the stack as built. `arch/overview.md` keeps its template headings and records only goals and quality inputs; the target architecture is not yet decided and will be decided in later ADRs, each citing the gap IDs (G-nn) it resolves.

**What it makes harder later.** MVP.md goes stale as soon as the code changes: re-map before each research round and bump the commit hash in MVP.md §0. It also records defects as findings, not as decisions; nothing in it commits the project to fix, keep or replace any component.
