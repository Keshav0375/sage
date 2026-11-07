# Round-2 evidence digest (9 scouts, read 2026-11-01)

Requirements: requirements.md (same folder). Baseline: arch/MVP.md. Prices us-central1 list, monthly ≈ 730 h.

## Keshav's decisions (2026-11-01)
- Tenancy: demo multi-tenant — 2-3 synthetic firms, a few hundred advisors, ~10 QPS peak; isolation fully built; design documented to scale to 50 tenants / 2,000 advisors.
- Budget: ~$100-200/month, demo-on-demand. Dev runs everything locally in docker compose incl. Kafka. Cloud prod is real but scales to zero; costly parts start only for demos/load tests.
- Backend: keep Python FastAPI. Frontend: React + TypeScript.
- ETL data: synthetic per-tenant corpus + a real public source (SEC EDGAR fund filings or FINRA rule text).
- Compliance: as MVP (US/EU/UK synthetic), no real certification.

## Urgent facts
- claude-sonnet-4-20250514 RETIRED 2026-06-15 (replacement claude-sonnet-5-5); sonnet-4-5 retires 2026-11-30; active: claude-sonnet-5-5, claude-sonnet-4-6, claude-haiku-5-5, claude-haiku-4-5 (deprecation ~2026-10-15). https://platform.claude.com/docs/en/about-claude/model-deprecations
- Prices per MTok in/out: Sonnet 5.5 $2/$10 (cache read $0.10); Haiku 5.5 $0.10/$0.50; Haiku 4.5 $1/$5. Batch API −50%. Temperature/top_p/top_k removed in API 2026-10-21 (400). https://platform.claude.com/docs/en/about-claude/pricing
- Langfuse SDK v3+ removed trace()/span()/generation() (context managers / @observe); SDK v5 needs server v4; server v4 self-host needs ClickHouse+Redis+S3+Postgres, ≥4 vCPU/16 GiB; Langfuse Cloud Hobby free 50k units/mo, 30-day retention. https://langfuse.com/docs/observability/sdk/python/upgrade-path , https://langfuse.com/self-hosting , https://langfuse.com/pricing

## Multi-tenancy references
- AWS pool/bridge/silo for RAG; pool = shared index + tenant filter, cheapest, no per-tenant CMEK or perf isolation. https://aws.amazon.com/blogs/machine-learning/multi-tenant-rag-with-amazon-bedrock-knowledge-bases/ ; pgvector RLS variant https://aws.amazon.com/blogs/database/self-managed-multi-tenant-vector-search-with-amazon-aurora-postgresql/
- Azure: single retrieval API layer is the enforcement point; every retrieval (incl. agent tool calls) carries tenant + user filters; logs grounding for audit. https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/secure-multitenant-rag
- Google: multi-tenant agentic = project-per-tenant (silo) with shared hub (LB, Cloud Armor, Model Armor, IAP). https://docs.cloud.google.com/architecture/multi-tenant-agentic-ai-system ; RAG on Vertex+AlloyDB: GCS→Pub/Sub→Cloud Run parse/chunk/embed→pgvector; async eval subsystem → BigQuery. https://docs.cloud.google.com/architecture/rag-capable-gen-ai-app-using-vertex-ai
- Notion: Kafka consumers per page edit, workspace-ID sharding, per-span content hash → re-embed only changed text, permission change = metadata patch (−70% volume). https://www.notion.com/blog/two-years-of-vector-search-at-notion
- Uber: vector/search index as a replayable projection of a Kafka log (re-embed = replay). https://www.uber.com/us/en/blog/how-uber-indexes-streaming-data-with-pull-based-ingestion-in-opensearch/
- Finance: Morgan Stanley — answers only from firm content with source links, daily regression eval suite, advisor feedback. https://openai.com/index/morgan-stanley/ ; JPM Ask DAVID — accuracy <50% → ~80% (retrieval tuning) → ~90% (orchestration); per-sub-agent evals; OWASP-mapped guardrails. ; Bloomberg — RAG increases unsafe answers (5,000 harmful Qs, 11 LLMs) https://www.bloomberg.com/professional/insights/press-announcement/bloomberg-ai-researchers-mitigate-risks-of-unsafe-rag-llms-and-genai-in-finance/ ; EvidenT — deterministic evidence-to-source alignment, no citations to non-retrieved docs, +29% gold-source hit https://aclanthology.org/2026.emnlp-industry.69.pdf

## Data layer (pgvector, Postgres, Cloud SQL)
- pgvector OSS 0.8.7; Cloud SQL PG13+ ships 0.8.5 (iterative scans included). HNSW defaults m 16, ef_construction 64, ef_search 40; can build on empty table. Filtering is applied after ANN scan → short results; fix with hnsw.iterative_scan (strict/relaxed), max_scan_tuples 20,000, partial indexes (few values) or partitioning (many). halfvec ≤4,000 dims. https://github.com/pgvector/pgvector , https://docs.cloud.google.com/sql/docs/postgres/extensions
- Practitioner: 40 tenants/1.2M chunks: 52/400 queries returned 0 rows with default HNSW; relaxed iterative scan cut short results to 3 at p95 18→24 ms; small tenants best with exact scan. https://dev.to/ji_ai/pgvector-hnsw-filtering-returned-0-rows-for-52-of-my-400-queries-ghp ; AWS Aurora 0.8.0 iterative scan 0-10% → 100% expected rows https://aws.amazon.com/blogs/database/supercharging-vector-search-performance-and-relevance-with-pgvector-0-8-0-on-amazon-aurora-postgresql/ . Pattern: stay in Postgres at small tenant counts.
- Postgres: superuser/BYPASSRLS always bypass RLS; FORCE needed for owners; FK checks bypass RLS; session SET persists after COMMIT; use set_config(name, value, true) + SET LOCAL ROLE inside one transaction; app role non-owner, non-superuser. https://www.postgresql.org/docs/16/ddl-rowsecurity.html , https://www.postgresql.org/docs/16/sql-set.html
- Hybrid: tsvector + GIN on PG16 (ts_rank is not BM25); pg_textsearch (BM25) on Cloud SQL/AlloyDB needs PG17+; ParadeDB not on managed GCP. RRF is user-written SQL.
- Cost: Cloud SQL Enterprise 2 vCPU/8 GiB ≈ $101 (HA ≈ $202); db-g1-small ≈ $26 (no SLA); AlloyDB 2 vCPU/16 GiB ≈ $227+. Managed connection pooling = Enterprise Plus only (transaction mode forbids SET). Memorystore Valkey shared-core-nano 1.4 GB ≈ $23. Qdrant Cloud free 1 node 1 GB (no HA). 1M×1024 halfvec ≈ 2 GB.

## Advanced RAG (papers)
- Ranked by accuracy per latency: (1) hybrid BM25/FTS + dense with RRF, filters in both legs (Wang et al. 2407.01219: +2.3 nDCG@10 for +0.6 s prototype); rule IDs/tickers need lexical. (2) cross-encoder rerank top 20-50 → 5-8 (RankGPT 2304.09542: BM25 43.4 → 49-51 BEIR; Anthropic 2.9% → 1.9% failure); skip LLM listwise (11-32 s). (3) contextual retrieval at ingest + smaller chunks (256-512 tokens) with parent expansion (Anthropic: top-20 failure 5.7% → 2.9%, $1.02/M doc tokens one-time) https://www.anthropic.com/news/contextual-retrieval ; semantic chunking not worth it (2410.13070). (4) retrieval-confidence gate (CRAG 2401.15884, no web fallback) + claim-level citation verification (ALCE 2305.14627; up to 57% post-rationalized citations, 2412.18004). (5) fix filtered ANN, then tenant+tier+corpus-version-keyed answer cache.
- Not now: SPLADE, ColBERT, HyDE by default (+4.6 s), GraphRAG/RAPTOR, Self-RAG, semantic chunking.
- Reranker latency (hosted): Voyage rerank-2 ~0.68 s, Cohere v3 ~0.76 s per call on short facts (vectorize leaderboard).
- Voyage: input_type "query" for queries; voyage-4 series current (voyage-4 $0.06/M, 200M free tokens; voyage-4-lite $0.02); voyage-finance-2 finance-tuned; Tier-1 2000 RPM. https://docs.voyageai.com/docs/embeddings

## Kafka (cost table, our volume ~1-5k events/day)
- GCP Managed Kafka: min 3 vCPU, 3-zone, ≈ $189-248/mo; Schema Registry Preview. https://cloud.google.com/managed-service-for-apache-kafka/pricing
- Confluent Cloud Basic: first eCKU free then $0.14/eCKU-h, $0.05/GB in/out → ≈ $0-10/mo at our volume (estimate; confirm in console); 99.5% SLA; free Essentials Schema Registry (100 schemas); $400 trial. https://www.confluent.io/pricing/
- Aiven Free (250 KiB/s, 5 topics) $0; Developer $35. Redpanda Serverless GCP beta. Self-host KRaft on e2-medium ≈ $27 (single broker, no HA). Pub/Sub ≈ $0 but no Kafka API.
- Local: apache/kafka:4.4.0 KRaft single node (pin tag). Python: confluent-kafka 2.16.1 (AIOProducer, async Schema Registry, Avro/Protobuf/JSON Schema, idempotent + transactional). https://github.com/confluentinc/confluent-kafka-python
- No reference puts Kafka in front of pgvector at tens of tenants; Kafka is justified here for learning, replay, per-tenant ordering, not load. Debezium outbox EventRouter: https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html

## ETL
- Bronze (raw immutable, sha256 + URL + fetch time; GCS) → silver (Docling MIT local parse, PII scrub, structure chunking, Pandera validation, chunk/doc hashes, parser_version) → gold (dbt Core on Postgres; eval/usage events to BigQuery, 1 TiB/mo free queries, partition + cluster, max bytes billed).
- Orchestration: Dagster OSS self-hosted (free) assets/partitions/sensors with run_key dedupe; Dagster+ Solo $10/mo; avoid Cloud Composer (continuous billing). Kafka-triggered Dagster needs a custom sensor with offset cursor. https://dagster.io/docs/guides/automate/sensors
- SEC EDGAR: ≤10 req/s, declared User-Agent, nightly index ~10 pm ET. https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- BigQuery Storage Write API default stream at-least-once → idempotent sinks by event id. Document AI only as OCR fallback ($1.50/1k pages).

## Security and guardrails
- Auth: Identity Platform multi-tenancy (tenant silos, OIDC/SAML; Tier-1 free to 50k MAU; SAML/OIDC $0.015/MAU after 50; billing needed for >2 tenants); custom claims via Admin SDK (tenant_id/tier/jurisdiction), validate JWT server-side. Alternatives Auth0 Free (25k MAU, 5 orgs), Clerk free 50k MRU. https://docs.cloud.google.com/identity-platform/docs/multi-tenancy
- Network: external ALB + Cloud Armor (≈ $0.75/1M req + policy fee) → Cloud Run ingress internal-and-cloud-load-balancing, no allUsers; per-service SA + run.invoker + ID tokens; Cloud SQL via PSC; WIF for GitHub Actions; Direct VPC egress needs startup probe.
- Guardrails: Model Armor (prompt injection, jailbreak, SDP) free to 2M tokens/mo then $0.10/1M; REST API only detects (app acts); GKE example timeout 500 ms, failOpen false. https://docs.cloud.google.com/model-armor/overview . Anthropic: untrusted content only in tool_result, JSON-encoded; Haiku pre-screen; refusal stop_reason. Presidio in-process (community project; reversible pseudonymization; no recall guarantee) https://data-privacy-stack.github.io/presidio/ ; DLP API $3/GiB after 1 GiB free.
- Measured guardrail costs: classifier-style 20-250 ms, 0-4% FPR; LLM-based rails (NeMo) 0.5-1.5 s, up to 16% FPR (2605.06669); stacking guards compounds false positives. Indirect injection via tool output is architectural → least privilege, tenant from verified token never from model args. OWASP LLM Top 10 2025: LLM01 injection, 02 sensitive disclosure, 03 supply chain, 04 poisoning, 05 improper output, 06 excessive agency, 07 prompt leakage, 08 vector/embedding weaknesses, 09 misinformation, 10 unbounded consumption. https://genai.owasp.org/llm-top-10/

## Evals and LLM ops
- Offline: golden set → Langfuse dataset + run_experiment in CI; Ragas (collections API: faithfulness, context precision/recall, noise sensitivity; tool-call accuracy) + deterministic checks; judge ≠ answer model (Haiku), calibrate vs ~30 human labels (Cohen's κ), report CI (ARES 2311.09476); swap order (MT-Bench 2306.05685). Grow golden set to hundreds incl. cross-tenant refusal and adversarial cases. Run nightly + per PR.
- Online: Langfuse observation-level judges on 5-10% sample ($0.01-0.10 each), user feedback scores. Red team: promptfoo redteam nightly (injection, PII, jailbreak, finance categories).
- LiteLLM: pin v1.106.6 (no -stable naming); recent releases had OOM/memory regressions (v1.100.0, v1.105-106) → canary + soak; ≥4 Gi per pod; `order` for priority; set request_timeout / num_retries; Redis only with >1 replica; budgets need its DB. Cross-provider fallback changes answers in a regulated product. https://docs.litellm.ai/docs/routing , https://docs.litellm.ai/blog/retry-breadcrumb-oom-incident
- GCP ops: Logging $0.50/GiB after 50 GiB/project; Trace free to 2.5M spans; SLOs via custom service on Cloud Run metrics, burn-rate alerts.

## Compute, frontend, deploy
- Cloud Run: request timeout ≤60 min (SSE needs reconnect + Last-Event-ID); services for HTTP; worker pools for continuous Kafka consumers (no autoscaling, ~37% cheaper CPU); jobs for ETL (≤168 h). Request-based billing, min instances bill while idle. Estimates: prod API min=1 ≈ $20-30; consumer worker pool 0.5-1 vCPU ≈ $18-33; ETL jobs ≈ $1-2; dev ≈ $0-20.
- FastAPI 0.162 with native fastapi.sse.EventSourceResponse (or sse-starlette 3.6); one Uvicorn process per container; SQLAlchemy 2.1, asyncpg 0.32, alembic 1.20 (migrations as a Cloud Run job before traffic).
- Frontend: Vite React+TS SPA on GCS+CDN calling the API directly (bearer + CORS) removes the BFF buffering hop and the Next multi-instance issues; or Next.js 16 standalone on Cloud Run. Next.js 16.4.3 / React 19.3.1 current.
- Gateways: Apigee $365+/mo (no); API Gateway streaming preview (no); drop Kong; keep LiteLLM internal; do auth/rate limits in FastAPI + Cloud Armor.
- CI/CD: GitHub Actions + WIF → Artifact Registry → `gcloud run deploy --tag pr-N --no-traffic` previews; Terraform state per env prefix.
