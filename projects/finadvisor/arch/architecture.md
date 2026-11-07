# finadvisor: architecture

Binding. Top-down view of FinAdvisor v2 ("pooled multi-tenant modular monolith, event-driven ingest, demo-on-demand"). It restates what the deep-dive files and ADRs decide and adds nothing. Map: [architecture-diagram.md](architecture-diagram.md). Detail: [deep-dive/README.md](deep-dive/README.md). Decisions: [decision-logs.md](decision-logs.md) (ADR-001 to ADR-038). Status: [state.md](state.md). Build order: [../epic/plan.md](../epic/plan.md).

## 1. Goal and Keshav's decisions
A compliance-aware RAG assistant for wealth advisors across several tenant firms. Every claim is cited; tier (1-4) and jurisdiction (US/EU/UK) access is enforced in the database; PII is redacted before embedding, before LLM calls, in traces and on output. Python FastAPI backend, React + TypeScript frontend, a real cloud deployment that scales to zero between demos. Keshav's decisions: demo multi-tenant (2-3 synthetic firms, designed for 50), $100-200/month demo-on-demand, Kong in the design (binding), ETL/Kafka/evaluation/guardrails as learning goals, two regional cells designed but one deployed (K-R4-1), FCA Handbook API plus legislation.gov.uk for UK (K-R4-2), publisher documents private demo only (K-R4-3), 200-item golden set (K-R4-4).
Detail: [01](deep-dive/01-context-and-goals.md) §1.1-1.3. ADRs: ADR-001, ADR-002, ADR-011, ADR-031, ADR-037.

## 2. Quality targets (numbers)
- Latency: TTFT p50 < 2.0 s, p95 < 3.5 s; first stage p95 < 300 ms; rerank p95 < 700 ms; full answer p95 < 8 s. All are estimates to be measured.
- Availability: `demo` no SLA; `prod` 99.5% monthly on the chat path; entitlement revocation <= 60 s.
- Scale: demo 2-3 tenants, a few hundred advisors, ~10 QPS; designed for 50 tenants, 2,000 advisors, 100k-1M chunks.
- Quality gates: citation accuracy >= 0.95, faithfulness >= 0.90, cross-tenant/tier/jurisdiction leaks = 0, recall regression <= 2 points.
- Cost: idle $40-55, demo month $110-160, budget alert $180, always-on `prod` $300+ (out of budget).
- Erasure: live stores within 24 h, BigQuery and Kafka within 14 d, backups within 7 d, Langfuse provider-bound.
Detail: [02](deep-dive/02-quality-attributes.md) §2.1-2.10. ADRs: ADR-017, ADR-020, ADR-029, ADR-036, ADR-037.

## 3. System context
Advisors and tenant admins reach the platform only through the external ALB (`/*` SPA, `/v1/*` API). The platform verifies tokens with Identity Platform, calls Anthropic (Messages, Batch) and Voyage (embed, rerank), screens input and documents with Model Armor, sends scrubbed traces to Langfuse Cloud, uses Confluent Kafka, and reads public and publisher sources read-only. No real client data. Prompt, embedding and rerank inputs are processed US/global; data at rest stays in the home cell.
Detail: [03](deep-dive/03-system-context-and-boundaries.md). ADRs: ADR-010, ADR-012, ADR-026, ADR-038.

## 4. Components and how a request flows
Edge: external ALB, Cloud Armor, Kong `fa-gateway` (rate limits, header strip, SSE unbuffered), SPA bucket. App: Cloud Run `chat-api` with modules `auth`, `principal`, `retrieval`, `guardrails`, `agent`, `llm`, `events`, `admin`. Workers: `fa-worker` pool; jobs: Cloud Run jobs. One Python image, entrypoints `api | worker | jobs`, Direct VPC egress, no Cloud NAT.
Chat request: ALB, Cloud Armor, Kong, then `auth` (tenant-aware ID token), `principal` (home-cell check, 60 s entitlement cache), Presidio, `as_of` resolve, answer-cache lookup, Model Armor screen in parallel with query embed, hybrid SQL under RLS, rerank, confidence gate, streamed Claude answer with per-sentence PII, citation, numeric and as-of checks, outbox rows in the same transaction, SSE `done`. `chat-api` neither produces nor consumes Kafka.
Detail: [04](deep-dive/04-components-and-responsibilities.md), [04-1](deep-dive/04-1-key-flows.md). ADRs: ADR-005, ADR-007, ADR-011, ADR-019, ADR-024.

## 5. How a document flows (ingest)
Source connectors list, diff and fetch from each source (`etl`, `etl-public`), append `source_observations` and store bytes by sha256 in GCS bronze. An ingest scan and contract checks send failures to quarantine; passes go to the silver worker (Presidio, chunking, Pandera, Parquet), then the `indexer`, the only writer of `chunks`, which publishes one version per transaction under a per-document advisory lock via `reconcile_lineage`. Tenant stages are joined by Kafka topics; PUBLIC runs in-process. Events (ids and redacted metadata only) go Kafka to `bq-sink` to BigQuery; Dagster and dbt build bronze/silver/gold. FCA content never enters Kafka or BigQuery.
Detail: [04-2](deep-dive/04-2-source-lifecycle-and-cells.md) §4.15-4.17, [06](deep-dive/06-interfaces-and-contracts.md) §6.4, §6.7-6.8. ADRs: ADR-013, ADR-014, ADR-026, ADR-027, ADR-028, ADR-034.

## 6. Data and storage
One Cloud SQL PostgreSQL 16 with pgvector 0.8.5: pool tenancy with RLS, one non-superuser NOBYPASSRLS role per process, `chunks` LIST-partitioned by tenant, hybrid retrieval (FTS + dense, RRF) and a bitemporal model on PG16 ranges (`valid_range`, `system_range`). Exact-match answer cache keyed on corpus, ACL and entitlement versions, `as_of`, `embed_model`, `source_epoch`. GCS holds bronze/silver/quarantine; BigQuery holds analytics; embedding generations are blue/green.
Detail: [05](deep-dive/05-data-model-and-storage.md), [05-1](deep-dive/05-1-rls-indexes-versioning-and-deletion.md). ADRs: ADR-002, ADR-003, ADR-004, ADR-015, ADR-027, ADR-028, ADR-035.

## 7. Tenancy and security
Identity Platform with one tenant per firm and tenant discovery; identity comes only from a verified token, entitlements from the DB. The tenant boundary is RLS, tested by a leak matrix on every PR. No `allUsers`; Cloud Run ingress internal; `fa-gateway` is the only service with the invoker check off. OWASP LLM Top 10 (2025) mapped control by control; secrets in Secret Manager; SSE carries tool name and status only.
Detail: [08](deep-dive/08-security-and-privacy.md), [06](deep-dive/06-interfaces-and-contracts.md) §6.1-6.2. ADRs: ADR-002, ADR-004, ADR-009, ADR-010, ADR-011, ADR-012, ADR-032.

## 8. Regional cells
A cell is the whole data plane of one region; nothing is replicated between cells. The control plane is the signed static `cells.json` (refreshed every 60 s), the global ALB and Identity Platform. A wrong-cell request gets 421 with a cell hint. Only the `us` cell is deployed; `eu` is designed and tested in `docker-compose.cells.yml`. Tenant move: freeze, copy, verify, cutover, drain, erase. Residency wording: at rest only; model calls are US/global.
Detail: [04-2](deep-dive/04-2-source-lifecycle-and-cells.md) §4.24, [07](deep-dive/07-scaling-failure-modes-and-recovery.md) §7.6, [06](deep-dive/06-interfaces-and-contracts.md) §6.11. ADRs: ADR-031, ADR-032, ADR-033, ADR-038.

## 9. Data lifecycle and deletion
Physical delete on every live store, no Kafka on the delete path, no per-subject KMS keys. Requests go to the Postgres queue `deletion_requests`; the `erasure-worker` writes a tombstone to `erasure_ledger` first, deletes in order (Postgres, GCS, BigQuery, Langfuse; Kafka waits out retention), re-sweeps at the end of each window and issues a two-phase signed receipt. Restore replays the ledger before traffic. Source withdrawal has two classes: retire and erase (`purge_source('fca_api')`). A canary drill runs at each demo start. Document ACL changes use `acl_change_requests` and the `acl-applier`.
Detail: [04-2](deep-dive/04-2-source-lifecycle-and-cells.md) §4.19-4.23, [05-1](deep-dive/05-1-rls-indexes-versioning-and-deletion.md) §5.11-5.14. ADRs: ADR-022, ADR-026, ADR-029, ADR-030.

## 10. Guardrails
No LLM guardrails on the hot path. Ingest scan and quarantine for fetched documents; Model Armor input screen (fail closed); Presidio PII; per-sentence citation verifier, numeric grounding gate and as-of validity check; licence footers from `document_versions.attribution_text`; role policy. Any guard adding more than 150 ms p95 moves to async or is dropped.
Detail: [04-2](deep-dive/04-2-source-lifecycle-and-cells.md) §4.25-4.26, [08](deep-dive/08-security-and-privacy.md) §8.1, §8.6, §8.8. ADRs: ADR-009, ADR-036.

## 11. RAG and evaluation
Retrieve-first orchestration; hybrid retrieval with RRF k=60, Voyage rerank, confidence gate that refuses without an LLM call; parent expansion; staleness and state flags (`superseded`, `revoked`, `known_pending`). Contextual retrieval is default OFF behind a flag. Evaluation: 200-item golden set, four confirmatory ablation arms with Holm correction, guardrail sets, deploy gate on the quality targets of part 2.
Detail: [02](deep-dive/02-quality-attributes.md) §2.4, §2.10, [04-1](deep-dive/04-1-key-flows.md), [05-1](deep-dive/05-1-rls-indexes-versioning-and-deletion.md) §5.6. ADRs: ADR-007, ADR-008, ADR-016, ADR-017, ADR-037.

## 12. Observability
Langfuse Cloud (masked spans, judge scores) plus OpenTelemetry to Cloud Trace; log-based and OTel metrics in Cloud Monitoring; health endpoints; SLOs and alerts with a $180 budget alert; reconciliation alerts; deletion receipts and the canary; weekly guardrail measurement. Gateway audit through Cloud Logging and BigQuery.
Detail: [09](deep-dive/09-observability.md). ADRs: ADR-018, ADR-023, ADR-030, ADR-034.

## 13. Delivery phases
Phase 0 foundation (E0); 1 platform core (E1, then E2, E3, E5); 2 product (E4, E6); 3 real data and lifecycle (E11, E13 core, E12); 4 quality and UI (E7, E8); 5 operate (E9, E10). 203 tickets across E0-E10 are all `todo`; round-4 changes are updates plus new epics E11-E13. Nothing is built; the implementation gate stays closed until Keshav opens it. Open spikes: [10](deep-dive/10-open-questions.md). Stack with versions: [11](deep-dive/11-tech-stack.md). Baseline: [00](deep-dive/00-as-built-baseline.md).
Detail: [../epic/plan.md](../epic/plan.md). ADRs: ADR-001, ADR-025.
