## 1. Context and goals

### 1.1 Goal

FinAdvisor v2 is a compliance-aware RAG assistant for wealth advisors, serving several tenant firms (customers) and many concurrent sessions from one deployment. Every claim is cited. Tier (1-4) and jurisdiction (US/EU/UK) access control is enforced in the database. PII is redacted before embedding, before LLM calls, in traces and logs, and on output. Sources older than 12 months are flagged stale. ETL / data engineering, evaluation, guardrails, security and Kafka are first-class parts of the system (Keshav's learning goals), not add-ons. Backend: Python FastAPI. Frontend: React + TypeScript. Both are deployed; the cloud deployment is real but scales to zero between demos.

### 1.2 Keshav's decisions (2026-11-01)

| Topic | Decision | Source |
|---|---|---|
| Tenancy | Demo multi-tenant: 2-3 synthetic firms, a few hundred advisors, ~10 QPS peak. Isolation fully built. Design documented to scale to 50 tenants / 2,000 advisors | evidence-r2.md |
| Budget | ~$100-200/month, demo-on-demand. Dev runs everything locally in docker compose, including Kafka. Cloud prod is real but scales to zero; costly parts start only for demos and load tests | evidence-r2.md |
| Stack | Keep Python FastAPI. Frontend React + TypeScript | evidence-r2.md |
| ETL data | Synthetic per-tenant corpus plus one real public source (SEC EDGAR fund summary prospectuses, 497K HTML, first) | evidence-r2.md, D13p |
| Compliance | As MVP: US/EU/UK synthetic corpus; no real certification | requirements.md |
| Gateway | Kong must be in the design for rate limiting and proxy plugins (D12, "include kong ... we need it"). Binding | decision-r2.md D12 |
| Learning goals | ETL (Dagster, dbt, BigQuery), Kafka, evaluation, guardrails, databases at scale | evidence-r2.md, D3 |

### 1.3 Non-goals

- No real regulatory certification; synthetic data only (Langfuse Cloud, Confluent Basic and BigQuery are acceptable only for synthetic data; trigger "real firm data" is in ADR-013 and ADR-018).
- No cross-provider LLM fallback (changes regulated answers). No semantic answer cache (cross-user leak risk).
- No LLM-based guardrails on the hot path. No web fallback in the confidence gate.
- No SPLADE, ColBERT, HyDE by default, GraphRAG, RAPTOR, Self-RAG, semantic chunking.
- No per-tenant Kafka topics. No Debezium in v2 scope (optional later learning epic).
- No project-per-tenant or database-per-tenant silo in v2 (seam kept: `tenants.shard_id`).
- No Konnect, no Kong Enterprise image, no Enterprise-only Kong plugins.
- No always-on prod in the budget: the `prod` profile is designed and costed (~$300+/month) but out of budget by design.
- Cloud Composer, Apigee ($365+/month), API Gateway streaming preview, GCP Managed Kafka (~$189-248/month) are rejected.

### 1.4 MVP critical gaps and where v2 fixes them

Gap IDs refer to `MVP.md` §13.

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
