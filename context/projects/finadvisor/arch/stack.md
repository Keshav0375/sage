# finadvisor: tech stack

## Target (v2)

Decided 2026-11-01 (ADR-002 to ADR-024 in `decisions.md`; rulings D14-D16 applied; architecture in `overview.md`). "Pin at implementation" means the brief gives no version: the implementing epic pins it in the lockfile or image digest and updates this table; no version here is guessed. Everything installs from lockfiles; images are referenced by digest.

| Layer | Technology | Version / tag (pinned) | Why (ADR) | Official docs |
|---|---|---|---|---|
| Language (backend) | Python | 3.12 (as built); pin image by digest at implementation | ADR-019 | https://docs.python.org/3.12/ |
| Backend framework | FastAPI | 0.162 | ADR-019 | https://fastapi.tiangolo.com/ |
| SSE | `fastapi.sse` (`EventSourceResponse`, native in FastAPI 0.162) | with FastAPI 0.162 (alternative sse-starlette 3.6) | ADR-007 | https://fastapi.tiangolo.com/ |
| ASGI server | uvicorn, one process per container | pin at implementation | ADR-019 | https://www.uvicorn.org/ |
| Settings / schemas | pydantic, pydantic-settings (Pydantic generates the Schema Registry JSON Schemas) | pin at implementation | ADR-013, ADR-021 | https://docs.pydantic.dev/latest/ |
| ORM / DB access | SQLAlchemy (asyncio) | 2.1 | ADR-002 | https://docs.sqlalchemy.org/ |
| DB driver | asyncpg | 0.32 | ADR-002 | https://magicstack.github.io/asyncpg/current/ |
| Migrations | Alembic (run as the `migrate` Cloud Run job) | 1.20 | ADR-002, ADR-021 | https://alembic.sqlalchemy.org/ |
| Database | PostgreSQL 16 on Cloud SQL Enterprise (2 vCPU / 8 GiB, zonal, HA flag) | PG16; local and CI image `pgvector/pgvector:0.8.5-pg16` (matches Cloud SQL) | ADR-002, ADR-020 | https://www.postgresql.org/docs/16/ , https://docs.cloud.google.com/sql/docs/postgres |
| Vector search | pgvector (halfvec(1024), HNSW m 16 / ef_construction 64, iterative scan) | 0.8.5 on Cloud SQL | ADR-008 | https://github.com/pgvector/pgvector |
| Tenancy / isolation | PostgreSQL RLS (ENABLE + FORCE, LIST partitions by tenant) | PG16 | ADR-002, ADR-003 | https://www.postgresql.org/docs/16/ddl-rowsecurity.html |
| Full-text search | tsvector + GIN, `websearch_to_tsquery` | PG16 built-in | ADR-008 | https://www.postgresql.org/docs/16/textsearch.html |
| Edge | External Application Load Balancer + Cloud Armor | managed | ADR-012 | https://cloud.google.com/load-balancing/docs , https://cloud.google.com/armor/docs |
| API gateway | Kong Gateway OSS, DB-less, `_format_version: "3.0"` | `kong:3.9.4` | ADR-011 | https://developer.konghq.com/gateway/ |
| Gateway state | Valkey (Memorystore shared-core-nano in cloud; container locally) | pin at implementation | ADR-011 | https://cloud.google.com/memorystore/docs/valkey , https://valkey.io/docs/ |
| Gateway audit | Kong `file-log` (stdout, field whitelist) to Cloud Logging, then a log sink to BigQuery `gateway_audit` | managed | ADR-023 | https://cloud.google.com/logging/docs/export/configure_export_v2 |
| VPC egress | Direct VPC egress `private-ranges-only`, Private Google Access, Cloud DNS private zone mapping `run.app` to `private.googleapis.com`; no Cloud NAT | managed | ADR-024 | https://cloud.google.com/run/docs/configuring/vpc-direct-vpc |
| Streaming (cloud) | Confluent Cloud Basic + Schema Registry Essentials (JSON Schema), us-central1; one service account + API key per service, Kafka ACLs (no RBAC), limits 50 keys / 1,000 ACLs / 1,500 partitions | managed | ADR-013 | https://docs.confluent.io/cloud/current/overview.html |
| Streaming (local) | Apache Kafka KRaft single node; Confluent cp-schema-registry | `apache/kafka:4.4.0`; cp-schema-registry pin at implementation | ADR-013 | https://kafka.apache.org/documentation/ , https://docs.confluent.io/platform/current/schema-registry/ |
| Kafka client | confluent-kafka (Python) | 2.16.1 | ADR-013 | https://github.com/confluentinc/confluent-kafka-python |
| LLM (answer) | Anthropic `claude-sonnet-5-5` | model id from config; Anthropic SDK pin at implementation | ADR-006 | https://platform.claude.com/docs/en/about-claude/models |
| LLM (judge, headers, extraction, condensation) | Anthropic `claude-haiku-5-5` (Batch API for offline work) | model id from config | ADR-006, ADR-016 | https://platform.claude.com/docs/en/about-claude/pricing |
| LLM (fallback) | Anthropic `claude-sonnet-4-6` (same provider only; enabled only after passing the eval gate) | model id from config | ADR-005 | https://platform.claude.com/docs/en/about-claude/model-deprecations |
| LLM client | In-process `LLMClient` over the Anthropic SDK (no LiteLLM) | pin at implementation | ADR-005 | https://docs.anthropic.com/en/api/client-sdks |
| Embeddings | Voyage `voyage-4` (1024 dims, `input_type` query / document) | model id from config; voyageai SDK pin at implementation | ADR-008 | https://docs.voyageai.com/docs/embeddings |
| Reranker | Voyage `rerank-2.5-lite` (or `rerank-2.5`; ablation decides) | model id from config | ADR-008 | https://docs.voyageai.com/docs/reranker |
| PII | Microsoft Presidio (in-process pseudonymization) with spaCy `en_core_web_sm` | presidio-analyzer 2.2.x; spaCy model pin at implementation | ADR-009 | https://data-privacy-stack.github.io/presidio/ |
| Prompt-injection screen | Google Cloud Model Armor (REST) | managed | ADR-009 | https://docs.cloud.google.com/model-armor/overview |
| Auth | Google Identity Platform, multi-tenancy (one IdP tenant per firm), ID tokens (tenant claim `firebase.tenant`) | managed | ADR-010 | https://docs.cloud.google.com/identity-platform/docs/multi-tenancy |
| Auth library | firebase-admin (Python), tenant-aware verification (`tenant_mgt.auth_for_tenant(tenant_id).verify_id_token`) | pin at implementation | ADR-010 | https://docs.cloud.google.com/identity-platform/docs/multi-tenancy-managing-tenants |
| Document parsing | Docling | pin at implementation | ADR-014 | https://docling-project.github.io/docling/ |
| Data validation | Pandera | pin at implementation | ADR-014 | https://pandera.readthedocs.io/ |
| Orchestration | Dagster OSS, daemon-less (`dagster asset materialize` in Cloud Run jobs), run / event storage with `dagster-postgres` (database `dagster`, role `fa_dagster`); `dagster dev` locally | pin at implementation | ADR-014 | https://docs.dagster.io/ |
| Transformation | dbt Core with `dbt-postgres` (gold models) and `dbt-bigquery` (BigQuery marts) | pin at implementation | ADR-014 | https://docs.getdbt.com/ |
| Warehouse | BigQuery (day-partitioned, clustered by `tenant_id`, per-tenant authorized views primary + row access policies, `maximum_bytes_billed`) | managed | ADR-014 | https://cloud.google.com/bigquery/docs |
| Object storage | GCS (bronze by sha256, silver, SPA bucket) | managed | ADR-014 | https://cloud.google.com/storage/docs |
| Evaluation | Ragas (collections API), promptfoo (red team), Langfuse datasets / `run_experiment` | pin at implementation | ADR-017 | https://docs.ragas.io/ , https://www.promptfoo.dev/docs/ , https://langfuse.com/docs |
| LLM observability | Langfuse Cloud Hobby; Python SDK 5.x (`@observe` with `capture_input` / `capture_output` off on sensitive spans, `mask_otel_spans`) behind a wrapper | 5.x (5.1.0 current) | ADR-018 | https://langfuse.com/docs |
| Telemetry | OpenTelemetry (SDK + exporters) to Cloud Trace, Cloud Logging, Cloud Monitoring | pin at implementation | ADR-018 | https://opentelemetry.io/docs/ , https://cloud.google.com/trace/docs |
| Logging | Structured JSON logs, redacted (library pin at implementation; as built: structlog) | pin at implementation | ADR-018 | https://www.structlog.org/ |
| Frontend | Vite + React 19 + TypeScript SPA on GCS + CDN behind the ALB | React 19 (19.3.1 current in evidence); Vite and TypeScript pin at implementation | ADR-019 | https://vite.dev/ , https://react.dev/ |
| Frontend tests | vitest, Playwright, eslint, tsc | pin at implementation | ADR-021 | https://vitest.dev/ , https://playwright.dev/ |
| Compute | Cloud Run services (`fa-gateway`, `chat-api`), worker pool (`fa-worker`), jobs (migrate, etl, etl-public, dbt, eval, redteam, demo-ttl) | managed | ADR-019 | https://cloud.google.com/run/docs |
| Scheduling | Cloud Scheduler | managed | ADR-020 | https://cloud.google.com/scheduler/docs |
| Secrets, images | Secret Manager, Artifact Registry | managed | ADR-019, ADR-021 | https://cloud.google.com/secret-manager/docs , https://cloud.google.com/artifact-registry/docs |
| IaC | Terraform, google provider; Confluent provider | provider versions pin at implementation | ADR-020, ADR-021 | https://registry.terraform.io/providers/hashicorp/google/latest/docs , https://registry.terraform.io/providers/confluentinc/confluent/latest/docs |
| CI/CD | GitHub Actions with Workload Identity Federation; ruff, mypy, pytest, import-linter, trivy, gitleaks, pip-audit, `kong config parse`, deck | action and tool versions pin at implementation | ADR-021 | https://docs.github.com/en/actions , https://docs.astral.sh/ruff/ |
| Local orchestration | Docker Compose (Postgres+pgvector, Kafka, Schema Registry, Kong, Valkey, api, worker, frontend dev image) | env-driven host ports | ADR-019 | https://docs.docker.com/compose/ |

## As built (MVP, d6c2bd3)

As built at commit d6c2bd3 (mapped 2026-11-01). Versions are what the repo pins; "floating" means a lower bound or a moving tag, so the resolved version changes with each build. Where `poetry.lock` resolves a version it is shown as "lock x.y.z" but the backend Dockerfile ignores the lock (`backend/Dockerfile:6-8`), so the lock is not what a container build installs. The target stack is in the section above; the Why column here points to the as-built description.

| Layer | Technology | Version | Why (ADR) | Official docs |
|---|---|---|---|---|
| Language (backend) | Python | `>=3.12,<3.14` (`backend/pyproject.toml:8`); Docker `python:3.12-slim` (`backend/Dockerfile:1`); CI 3.12 | as built, see MVP.md §3, §8 | https://docs.python.org/3.12/ |
| Backend framework | FastAPI | floating `>=0.115.0` (lock 0.136.1) | as built, see MVP.md §3.2 | https://fastapi.tiangolo.com/ |
| ASGI server | uvicorn[standard] | floating `>=0.30.0` (lock 0.47.0); one process, no workers flag | as built, see MVP.md §8a | https://www.uvicorn.org/ |
| SSE | sse-starlette | floating `>=2.0.0` (lock 3.4.4) | as built, see MVP.md §4.a, §6.2 | https://github.com/sysid/sse-starlette |
| Settings | pydantic-settings | floating `>=2.0.0` (lock 2.14.1) | as built, see MVP.md §7 | https://docs.pydantic.dev/latest/concepts/pydantic_settings/ |
| ORM / DB access | SQLAlchemy (asyncio) | floating `>=2.0.0` (lock 2.0.49); runtime uses raw `text()` SQL | as built, see MVP.md §3.9 | https://docs.sqlalchemy.org/en/20/ |
| DB driver | asyncpg | floating `>=0.29.0` (lock 0.31.0) | as built, see MVP.md §3.9 | https://magicstack.github.io/asyncpg/current/ |
| Logging | structlog | floating `>=24.0.0` (lock 25.5.0) | as built, see MVP.md §11 | https://www.structlog.org/ |
| LLM SDK | anthropic (Python SDK) | floating `>=0.40.0` (lock 0.102.0); model string `claude-sonnet-4-20250514` hard-coded | as built, see MVP.md §3.4, §6.4 | https://docs.anthropic.com/en/api/client-sdks |
| Embeddings SDK | voyageai | floating `>=0.3.0` (lock 0.3.7); model `voyage-3`, 1024 dims | as built, see MVP.md §3.6 | https://docs.voyageai.com/docs/embeddings |
| Tracing SDK | langfuse (Python SDK) | floating `>=2.0.0` (lock 4.6.1); code written for the v2 API | as built, see MVP.md §11 and G-15 | https://langfuse.com/docs |
| PII (cloud mode) | google-cloud-dlp | floating `>=3.0.0` (lock 3.36.0) | as built, see MVP.md §3.7 | https://cloud.google.com/sensitive-data-protection/docs |
| Vector client | pgvector (Python) | floating `>=0.3.0` (lock 0.4.2); ORM `Vector(1024)` type only | as built, see MVP.md §5 | https://github.com/pgvector/pgvector-python |
| Auth lib (unused) | python-jose[cryptography] | floating `>=3.3.0` (lock 3.5.0); not imported | as built, see MVP.md §3.3 | https://python-jose.readthedocs.io/ |
| Backend dev tools | pytest, pytest-asyncio, ruff, mypy, httpx | floating `>=8.0.0`, `>=0.24.0`, `>=0.7.0`, `>=1.11.0`, `>=0.27.0` (Poetry dev group; no `dev` extra) | as built, see MVP.md §9, §10 | https://docs.pytest.org/ , https://docs.astral.sh/ruff/ , https://mypy.readthedocs.io/ |
| Packaging | Poetry (poetry-core); root `pyproject.toml` plus `backend/pyproject.toml` | build backend `poetry-core` unpinned | as built, see MVP.md §8a, G-28 | https://python-poetry.org/docs/ |
| Frontend framework | Next.js (App Router) | pinned `14.2.35` (`frontend/package.json:13`) | as built, see MVP.md §3.1 | https://nextjs.org/docs |
| UI library | React / react-dom | floating `^18` | as built, see MVP.md §3.1 | https://react.dev/ |
| Client state | zustand | floating `^5.0.13` | as built, see MVP.md §3.1 | https://zustand.docs.pmnd.rs/ |
| Markdown | react-markdown | floating `^10.1.0` | as built, see MVP.md §3.1 | https://github.com/remarkjs/react-markdown |
| SSE parser (unused) | eventsource-parser | floating `^3.0.8`; parser is hand-rolled in `src/lib/api.ts` | as built, see MVP.md §3.1 | https://github.com/rexxars/eventsource-parser |
| Styling / tooling | Tailwind `^3.4.1`, TypeScript `^5`, ESLint `^8`, Prettier `^3.8.3` | floating | as built, see MVP.md §9 | https://tailwindcss.com/docs |
| Frontend runtime | Node.js | 20 (CI only, `ci.yml:48-51`); `@types/node ^20`; no Dockerfile | as built, see MVP.md §8a | https://nodejs.org/docs/latest-v20.x/api/ |
| Database | PostgreSQL + pgvector | image `pgvector/pgvector:pg16` (`docker-compose.yml:3`, floating minor); Cloud SQL `POSTGRES_16` | as built, see MVP.md §5 | https://github.com/pgvector/pgvector , https://www.postgresql.org/docs/16/ |
| Row-level security | PostgreSQL RLS (`chunks` only) | PostgreSQL 16 | as built, see MVP.md §5 | https://www.postgresql.org/docs/16/ddl-rowsecurity.html |
| API gateway | Kong Gateway (DB-less) | `kong:3.9` (`kong/Dockerfile:1`, floating patch) | as built, see MVP.md §3.10 | https://developer.konghq.com/gateway/ |
| LLM proxy | LiteLLM | `ghcr.io/berriai/litellm:main-latest` (floating) | as built, see MVP.md §6.5 | https://docs.litellm.ai/ |
| LLM providers | Anthropic, OpenAI (`gpt-4o`), Google (`gemini-2.5-flash`) | via LiteLLM config (`litellm/config.yaml:1-21`) | as built, see MVP.md §6.5 | https://docs.anthropic.com/ , https://platform.openai.com/docs , https://ai.google.dev/gemini-api/docs |
| Observability backend | Langfuse server | `langfuse/langfuse:2` (floating minor); own `postgres:16` | as built, see MVP.md §11 | https://langfuse.com/self-hosting |
| Cache (unused) | Redis | `redis:7-alpine` (`docker-compose.yml:98`); no consumer | as built, see MVP.md §3.11 | https://redis.io/docs/latest/ |
| Cloud IaC | Terraform with provider google | `required_version >= 1.5`, `hashicorp/google ~> 5.0` (`terraform/main.tf:2-9`); `random` provider implicit | as built, see MVP.md §8b | https://registry.terraform.io/providers/hashicorp/google/latest/docs |
| Cloud runtime (as written, not deployed) | Cloud Run v2, Cloud SQL, Secret Manager, Artifact Registry, GCS, Cloud DLP | region `us-central1`; image tags default `latest` | as built, see MVP.md §8b | https://cloud.google.com/run/docs |
| CI | GitHub Actions | `actions/checkout@v4`, `setup-python@v5`, `setup-node@v4`, `upload-artifact@v4` | as built, see MVP.md §9 | https://docs.github.com/en/actions |
| Local orchestration | Docker Compose | compose file without a `version:` key | as built, see MVP.md §8a | https://docs.docker.com/compose/ |
