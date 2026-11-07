> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 1. Context and goals

### 1.1 Goal

FinAdvisor v2 is a compliance-aware RAG assistant for wealth advisors, serving several tenant firms (customers) and many concurrent sessions from one deployment. Every claim is cited. Tier (1-4) and jurisdiction (US/EU/UK) access control is enforced in the database. PII is redacted before embedding, before LLM calls, in traces and logs, and on output. Sources older than 12 months are flagged stale. ETL / data engineering, evaluation, guardrails, security and Kafka are first-class parts of the system (Keshav's learning goals), not add-ons. Backend: Python FastAPI. Frontend: React + TypeScript. Both are deployed; the cloud deployment is real but scales to zero between demos.

### 1.2 Keshav's decisions (2026-11-01 and round 4, 2026-11-02)

| Topic | Decision | Source |
|---|---|---|
| Tenancy | Demo multi-tenant: 2-3 synthetic firms, a few hundred advisors, ~10 QPS peak. Isolation fully built. Design documented to scale to 50 tenants / 2,000 advisors | evidence-r2.md |
| Budget | ~$100-200/month, demo-on-demand. Dev runs everything locally in docker compose, including Kafka. Cloud prod is real but scales to zero; costly parts start only for demos and load tests | evidence-r2.md |
| Stack | Keep Python FastAPI. Frontend React + TypeScript | evidence-r2.md |
| ETL data | Synthetic per-tenant corpus plus one real public source (SEC EDGAR fund summary prospectuses, 497K HTML, first). Extended on 2026-11-02 by K-R4-2 and K-R4-3 below | evidence-r2.md, D13p |
| Compliance | As MVP: US/EU/UK synthetic corpus; no real certification | requirements.md |
| Gateway | Kong must be in the design for rate limiting and proxy plugins (D12, "include kong ... we need it"). Binding | decision-r2.md D12 |
| Learning goals | ETL (Dagster, dbt, BigQuery), Kafka, evaluation, guardrails, databases at scale | evidence-r2.md, D3 |
| K-R4-1 Regions (2026-11-02) | Two regional cells are designed and tested locally in docker compose; one region is deployed. Residency covers data at rest (Postgres, GCS, BigQuery, Kafka, Langfuse). Model calls are documented as US/global (Anthropic first-party `inference_geo` is `global` or `us` only). Claude on Vertex AI in an EU region stays a costed option in the ADR, not built | checkpoint-r4.md; ADR-031, ADR-038 |
| K-R4-2 UK source (2026-11-02) | Current FCA COBS from the FCA Handbook API (revocation and delete-on-request handled); UK version history from legislation.gov.uk (OGL). No crawling of the Handbook website. FINRA Rulebook dropped (terms forbid bulk copy and ML use) | checkpoint-r4.md; ADR-026 |
| K-R4-3 Publisher documents (2026-11-02) | Fund KIDs, SEC 497K and Form ADV brochures are private demo only: a small set (about 3 fund families, 10-20 brochures) fetched at runtime into private storage with attribution, never committed to the public repo and never published in eval sets | checkpoint-r4.md; ADR-026 |
| K-R4-4 Golden set (2026-11-02) | 200 items labelled by Keshav (about 40-55 h estimate). Release gates and ablations with gains of about 5 points or more; the set stays above 100 effective items after clustering by source document. The cluster unit is the provision or product (R4-D17) | checkpoint-r4.md; ADR-037 |

### 1.3 Non-goals

- No real regulatory certification. Real public documents (eCFR, EUR-Lex, legislation.gov.uk, the FCA Handbook API, SEC EDGAR) and private demo publisher documents (K-R4-3) are in scope. Real client data is still out of scope: Langfuse Cloud, Confluent Basic and BigQuery stay acceptable only without real client data. The trigger "real firm data" in ADR-013 and ADR-018 now reads: real public documents and private demo publisher documents are allowed; real client data is not (ADR-038).
- No cross-provider LLM fallback (changes regulated answers). No semantic answer cache (cross-user leak risk).
- No LLM-based guardrails on the hot path. No web fallback in the confidence gate.
- No SPLADE, ColBERT, HyDE by default, GraphRAG, RAPTOR, Self-RAG, semantic chunking. Contextual retrieval (LLM headers, ADR-016) is default OFF. Contextual retrieval and any other method enter the default pipeline only with an ablation gain of about 5 points or more that survives the Holm correction on the golden set; an inconclusive result means off (D-R4-3, ADR-037). Methods outside the four confirmatory arms are exploratory and cannot enter the default pipeline alone.
- A real second region and Claude on Vertex AI in an EU region are costed options in ADR-031 and ADR-038, not built. The second cell exists as design plus a two-cell docker compose suite. No EU-only processing claim is made: prompts, embedding and rerank inputs go to Anthropic and Voyage (US/global).
- No FINRA Rulebook, no crawling of the FCA Handbook website. No per-subject KMS keys, no PostgreSQL 18, no OpenLineage as a gate (ADR-027, ADR-029, ADR-034).
- No per-tenant Kafka topics. No Debezium in v2 scope (optional later learning epic).
- No project-per-tenant or database-per-tenant silo in v2 (seam kept: `tenants.shard_id`).
- No Konnect, no Kong Enterprise image, no Enterprise-only Kong plugins.
- No always-on prod in the budget: the `prod` profile is designed and costed (~$300+/month) but out of budget by design.
- Cloud Composer, Apigee ($365+/month), API Gateway streaming preview, GCP Managed Kafka (~$189-248/month) are rejected.

### 1.4 MVP critical gaps and where v2 fixes them

Gap IDs refer to `deep-dive/00-as-built-baseline.md` §13.

| Gap | MVP defect | v2 fix | Where | Epic |
|---|---|---|---|---|
| G-01 | Identity is an `X-User-Id` header over 4 hard-coded users | Identity Platform ID tokens verified tenant-aware (`firebase.tenant`; signature, aud, iss, exp); entitlements from `advisors` | §8.2, §4 `auth`/`principal`, ADR-010 | E1 |
| G-02 | `allUsers` run.invoker on backend and frontend | No `allUsers` on any service. `fa-gateway` has the Cloud Run invoker check disabled (the only such service; Google's recommended alternative to `allUsers`), ingress internal-and-cloud-load-balancing, Cloud Armor on the backend service. `chat-api` has ingress internal and `run.invoker` only for the Kong service account | §8.3, ADR-011, ADR-012 | E2, E10 |
| G-03 | `documents.raw_content` unredacted, returned to LLM and client | Column dropped in the E1 migration; raw bytes only in GCS bronze; factsheet tool returns redacted chunks | §5.2, §6.3, ADR-014 | E1, E3, E6 |
| G-04 | `tool` / `tool_result` SSE events carry raw tool JSON | Client receives tool name + status only; errors carry codes, not exception text | §6.2, §8.5, ADR-009 | E4 |
| G-05 | CI installs a non-existent `dev` extra; lint/test tools missing | Lockfile installs; ruff, mypy, pytest, eslint, tsc, vitest, trivy, gitleaks, pip-audit | §4.12, ADR-021 | E0 |
| G-06 | Eval gate cannot run (no keys, no DB URL, DB user rewritten, `sleep 5`) | Eval gate runs on the runner against real pgvector + Kafka service containers with keys from the CI secret store; healthcheck-gated | §4.14 (flow 4), ADR-017, ADR-021 | E0, E7 |
| G-07 | `suitability_rules` has no ingest path | Rules extracted with Haiku structured output, validated, loaded by the ETL | §5.2, §4.14 (flow 2), ADR-014 | E6 |
| G-08 | LiteLLM shuffles traffic across Claude, GPT-4o, Gemini under one name | LiteLLM removed; in-process `LLMClient`, same-provider fallback only | §4.5 `llm`, ADR-005 | E0, E4 |
| G-09 | LiteLLM `fallbacks` key matches nothing | Fallback implemented and tested in `LLMClient`; enabled only if it passes the eval gate | §4.5 `llm`, ADR-005 | E4 |
| G-10 | Backend `KONG_URL` points at itself in Cloud Run | Explicit config `ANTHROPIC_BASE_URL` (direct, or Kong egress route if the spike passes); readiness checks model availability | §6.6, ADR-005, ADR-011 | E2, E4 |
| G-11 | Kong upstream is Docker DNS; no service-to-service wiring | Kong `fa-gateway` Cloud Run service with ID token to chat-api (`X-Serverless-Authorization`); Terraform wires URLs, SAs, ingress | §4.3, §4.12, ADR-011 | E2, E10 |
| G-12 | `schema.sql` never applied; superuser + `SET ROLE` | Alembic baseline; migrations as `fa_owner` in a Cloud Run job before traffic; one non-superuser NOBYPASSRLS login role per process; startup and readiness assert role flags and FORCE RLS | §5.3, §5.4, ADR-002 | E0, E1, E10 |
| G-13 | No frontend Dockerfile; `/api/*` rewrite hard-coded to localhost | Vite SPA served from GCS behind the same ALB (`/*`), API on `/v1/*`; compose gets a frontend dev image | §4.4, ADR-012, ADR-019 | E0, E8, E10 |
