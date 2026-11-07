# Publish diff: round 4 re-plan (finadvisor)

Not applied. `/researcher:publish` applies it after Keshav approves. Published issue numbers from the
ticket frontmatter; reasons from library/research/r4/changes-*.md.

## Counts

epic-new: 8, epic-update: 6, keep: 67, new: 212, update: 36

## Epics

| Epic | Action | Issue | Title | Tickets |
|---|---|---|---|---|
| E0 | update | 1 | Foundation | 15 |
| E1 | update | 16 | Identity and tenancy | 23 |
| E2 | update | 38 | Gateway and edge | 22 |
| E3 | update | 60 | Retrieval v2 | 18 |
| E4 | update | 92 | Agent and guardrails | 34 |
| E5 | update | 77 | Kafka platform | 15 |
| E6 | new | — | ETL and data engineering | 22 |
| E7 | new | — | Evaluation | 26 |
| E8 | new | — | Frontend | 17 |
| E9 | new | — | Observability and SLOs | 23 |
| E10 | new | — | Cloud deploy and operations | 28 |
| E11 | new | — | Real data onboarding and versioning | 28 |
| E12 | new | — | Data lifecycle and deletion | 28 |
| E13 | new | — | Regional cells and multiple logins | 16 |

## Tickets (published issues and new tickets)

| Ticket | Action | Issue | Title | Reason |
|---|---|---|---|---|
| E0-T1 | keep | 2 | Spike: confirm Langfuse Cloud accepts SDK 5.x with masking |  |
| E0-T10 | keep | 11 | Add vitest and a frontend dev image |  |
| E0-T11 | keep | 12 | Rewrite docker compose with healthchecks and env-driven host ports |  |
| E0-T12 | keep | 13 | Split unit and integration tests and add a dependency start script |  |
| E0-T13 | update | 14 | Rewrite CI: lockfile installs, service containers, all checks | CI asserts Postgres major 16 equals Cloud SQL and the PR gate stays under 12 min (ADR-027, ADR-017) |
| E0-T14 | keep | 15 | Add trivy, gitleaks and pip-audit jobs that fail the PR |  |
| E0-T15 | new | — | Add test helpers: VCR replay, race harness, Kafka-off | Test helpers: VCR-style HTTP replay, race harness, Kafka-off fixture (ADR-017, ADR-026, ADR-028) |
| E0-T2 | keep | 3 | Build the backend image from poetry.lock with dev and runtime stages |  |
| E0-T3 | keep | 4 | One typed config that fails boot on missing secrets |  |
| E0-T4 | keep | 5 | Add a retired-model check for configured model ids |  |
| E0-T5 | keep | 6 | Add /healthz and /readyz with database and model checks |  |
| E0-T6 | keep | 7 | Remove LiteLLM and Kong wiring; call Anthropic directly |  |
| E0-T7 | keep | 8 | Remove LiteLLM and Kong resources from Terraform |  |
| E0-T8 | keep | 9 | Replace Langfuse v2 tracing with an SDK 5.x wrapper |  |
| E0-T9 | keep | 10 | Alembic baseline from schema.sql and the migrate entrypoint |  |
| E1-T1 | keep | 17 | Spike: verify Identity Platform tenant claim and billing |  |
| E1-T10 | keep | 26 | RLS and grants for activity, pipeline and usage tables |  |
| E1-T11 | update | 27 | Tenant onboarding and advisor seeding in the migrate job | Onboarding takes cell_id and residency_class, asserts the per-leaf EXCLUDE, seeds pseudonym_map (ADR-027, ADR-031, ADR-029) |
| E1-T12 | keep | 28 | Maintenance job: messages partitions and expired-row purge |  |
| E1-T13 | update | 29 | auth module: tenant-aware ID token verification | Gated by the same-email spike (E1-T22); one token per firm, no identity merge (ADR-032, R4-D18 V5) |
| E1-T14 | keep | 30 | principal: entitlement cache and tenant-scoped transactions |  |
| E1-T15 | keep | 31 | Wire identity into the API: 401 and cross-tenant isolation |  |
| E1-T16 | keep | 32 | Tenant discovery endpoint GET /v1/tenants/{slug} |  |
| E1-T17 | update | 33 | CI schema assertions: SECURITY DEFINER, raw_content, tenant_id | New invariant: every chunks leaf has the EXCLUDE constraint and btree_gist exists (ADR-027) |
| E1-T18 | keep | 34 | Startup and readiness role and RLS assertions |  |
| E1-T19 | update | 35 | L0 leak matrix part 1: cross-tenant reads, writes, FK probes | Leak matrix: fa_etl_public writes no firm table, new tables enter by pg_class (ADR-039 M6, ADR-002 D13a) |
| E1-T2 | keep | 18 | Spike: LIST-partition pruning and planner cost at 52 partitions |  |
| E1-T20 | keep | 36 | L0 leak matrix part 2: partitions, pooling, pruning, CI gate |  |
| E1-T21 | update | 37 | IdP tenant provisioning script | One IdP tenant per firm, gated by E1-T22 (ADR-032) |
| E1-T22 | new | — | Spike: same email in two Identity Platform tenants | Spike: same email in two Identity Platform tenants, gates the IdP tickets (ADR-032, R4-D18 V5) |
| E1-T23 | new | — | Migration: pseudonym_map, pseudonym_id columns and RLS | pseudonym_map plus pseudonym_id on conversations and messages, RLS; deleting the mapping unlinks (ADR-029, ADR-038, R4-D6) |
| E1-T3 | keep | 19 | Bootstrap DB roles and the separate dagster database |  |
| E1-T4 | update | 20 | Migration: tenants and advisors tables | `tenants` gains cell_id, residency_class, source_epoch; same idp_uid allowed in two tenants (ADR-031, ADR-032) |
| E1-T5 | update | 21 | Migration: content tables with LIST-partitioned chunks | btree_gist, 8-column chunk identity, range columns, per-leaf EXCLUDE; 3-column key becomes plain index (ADR-027, ADR-035, R4-D19 M1) |
| E1-T6 | keep | 22 | Migration: conversation, message and cache tables |  |
| E1-T7 | keep | 23 | Migration: ACL, eval, outbox, dedupe and tenant_usage tables |  |
| E1-T8 | keep | 24 | RLS v2 policies and grants for content tables |  |
| E1-T9 | keep | 25 | RLS for tenants and advisors, and fa_tenant_lookup |  |
| E2-T1 | keep | 39 | Spike: X-RL-Key keying and Valkey keys on Kong 3.9.4 |  |
| E2-T10 | keep | 48 | Spike: Cloud Armor cost from the billing catalog |  |
| E2-T11 | keep | 49 | Compose: Kong 3.9.4, Valkey and the stub |  |
| E2-T12 | update | 50 | kong.yml routes (incl. /resolve), header stripping, CORS, size limit | Adds the public `GET /resolve` Kong route (ADR-031, R4-D20) |
| E2-T13 | keep | 51 | pre-function: Google ID token and X-RL-Key |  |
| E2-T14 | update | 52 | Rate limits per IP and per session on Valkey | Per-IP rate limit on `/resolve` (ADR-031) |
| E2-T15 | keep | 53 | Observability plugins and file-log audit whitelist |  |
| E2-T16 | keep | 54 | CI: kong config parse, deck validation, forbidden-plugin guard |  |
| E2-T17 | keep | 55 | Gateway smoke tests (curl/deck) in compose and CI |  |
| E2-T18 | keep | 56 | Terraform: Cloud Armor policy on the ALB backend service |  |
| E2-T19 | keep | 57 | Cloud Logging sink to BigQuery gateway_audit |  |
| E2-T2 | keep | 40 | Spike: ai-proxy preserve egress to api.anthropic.com |  |
| E2-T20 | keep | 58 | llm-egress route (conditional on the egress spike) |  |
| E2-T21 | keep | 59 | Cloud acceptance: full gateway through the ALB |  |
| E2-T22 | new | — | Spike: ALB host rules for per-cell hostnames | Spike: ALB host rules for per-cell hostnames, with cost (ADR-031) |
| E2-T3 | keep | 41 | Stub chat-api service for gateway tests |  |
| E2-T4 | keep | 42 | Terraform: gateway network (PGA, run.app private zone) |  |
| E2-T5 | keep | 43 | fa-gateway Cloud Run service with Kong 3.9.4 image |  |
| E2-T6 | keep | 44 | Spike: private-DNS run.app egress without Cloud NAT |  |
| E2-T7 | keep | 45 | Spike: X-Serverless-Authorization passthrough |  |
| E2-T8 | update | 46 | Terraform: external ALB, URL map, serverless NEG | Per-cell hostnames and ALB host rules in the URL map (ADR-031) |
| E2-T9 | keep | 47 | Spike: SSE pass-through ALB to Kong to chat-api |  |
| E3-T1 | update | 61 | Spike: Voyage rerank latency, TPM and tier | Default reranker rerank-3-lite, rerank-3 comparison, rerank-2.5 removed (ADR-039 V1, ADR-037) |
| E3-T10 | keep | 70 | Reimplement lookup_product_factsheet on RetrievalService |  |
| E3-T11 | keep | 71 | Reimplement lookup_suitability_rule on RetrievalService |  |
| E3-T12 | keep | 72 | Enforce RetrievalService as sole content-table accessor |  |
| E3-T13 | update | 73 | Answer cache: table, versioned key and store | Cache key adds as_of, embed_model, PUBLIC source_epoch (ADR-015 amended, ADR-027, ADR-035) |
| E3-T14 | update | 74 | Answer cache lookup: verifier re-run and eligibility | Hit also requires every cited chunk valid at as_of; miss after a new version (ADR-015 amended, ADR-027) |
| E3-T15 | update | 75 | Answer cache purge by document and by expiry | Purge on publish, supersede, retire, withdraw, erase; document delete is the erasure-worker's (ADR-015 amended, ADR-039 M7) |
| E3-T16 | update | 76 | Retrieval benchmark and rerank ablation on 10k chunks | First-stage gate p95 <= 600 ms, rerank-3-lite default (ADR-039 M3, V1) |
| E3-T17 | new | — | CI check: SQL on chunks and document_versions has as_of predicate | CI check: SQL on chunks and document_versions in retrieval carries the as_of predicate (ADR-027) |
| E3-T18 | new | — | As-of boundary-day test (#9) for retrieve | As-of boundary-day test #9: day edges, clock +/-2 h, DST days (ADR-027) |
| E3-T2 | update | 62 | Spike: pgvector iterative scan with RLS and partitions | Spike adds 30% superseded rows, strict vs relaxed order, HNSW build time, first-stage p95 <= 600 ms (ADR-027, ADR-039 M3) |
| E3-T3 | keep | 63 | Voyage embeddings: voyage-4 with query/document input_type |  |
| E3-T4 | update | 64 | Migration: halfvec, FTS and HNSW indexes on chunks | (tenant_id, chunk_hash, embed_model) is a non-unique reuse index (ADR-035, R4-D19 M1) |
| E3-T5 | update | 65 | RetrievalService.search: hybrid dense + FTS with RRF and as_of | `search` takes as_of, inlines embed_model literal from allow-list, merges adjacent ranges (ADR-027, ADR-035) |
| E3-T6 | update | 66 | Rerank with timeout and RRF fallback | RERANK_MODEL default rerank-3-lite, config-only so ablation arm 3 needs no code (ADR-037, ADR-039) |
| E3-T7 | keep | 67 | CRAG-style confidence gate |  |
| E3-T8 | update | 68 | Parent expansion, fetch_chunks and server-side staleness | expand_parents and fetch_chunks take as_of and carry the predicate (ADR-027) |
| E3-T9 | update | 69 | retrieve pipeline (as_of), search_firm_kb tool and metrics | `retrieve` takes and returns as_of (ADR-027) |
| E4-T1 | update | 93 | Spike: Model Armor latency from Cloud Run region, fallback rates | Timeout from measured Cloud Run latency, 150 ms rule, flag default (ADR-036/009 amended, R4-D18 V3) |
| E4-T10 | keep | 102 | Tool dispatcher: JSON tool_result, validation, max iterations |  |
| E4-T11 | update | 103 | CitationVerifier with original-text compare and as-of check | as_of valid_range post-generation check, original-text compare (ADR-027, ADR-036) |
| E4-T12 | keep | 104 | Sentence-buffered output PII redaction |  |
| E4-T13 | keep | 105 | turn_events store and SSE v2 event encoding |  |
| E4-T14 | keep | 106 | POST /v1/chat with Idempotency-Key and replay |  |
| E4-T15 | keep | 107 | GET /v1/chat/{turn_id}/events resume and TURN_INTERRUPTED |  |
| E4-T16 | keep | 108 | Conversations and messages persistence with history window |  |
| E4-T17 | keep | 109 | Follow-up condensation with Haiku |  |
| E4-T18 | new | — | Orchestrator pre-LLM stages: as_of, cache, screen+embed, gate | as_of resolver, echo, locale date rule, meta as_of (ADR-027, R4-D4, R4-D20) |
| E4-T19 | new | — | Orchestrator LLM loop: streaming, tools, release checks, nonce | Per-request nonce, ReleaseCheck pipeline, original-text compare (ADR-036, ADR-009 amended) |
| E4-T2 | update | 94 | Spike: Presidio latency and recall on synthetic corpus | Measure DE/FR recall, English-only claim (ADR-036 decision 7) |
| E4-T20 | new | — | escalate_to_compliance persistence and GET /v1/escalations |  |
| E4-T21 | new | — | Outbox writer and turn-persist transaction (no text events) | chat.audit and eval.sample carry no text, pseudonym_id (ADR-013 amended, R4-D19 M5) |
| E4-T22 | new | — | Per-tenant token budget and concurrency limits |  |
| E4-T23 | new | — | Admin: PATCH /v1/admin/advisors/{id} |  |
| E4-T24 | new | — | Admin: ACL change requests with status endpoint | Drop document delete via acl_change_requests; deletes go to deletion_requests, E12-T11 (ADR-022 amended, ADR-029) |
| E4-T25 | new | — | Leak tests: PII never reaches Voyage, Anthropic, logs, Langfuse |  |
| E4-T26 | new | — | Integration tests: resume, idempotency, fallback, guard flag | Model Armor timeout now fails open via fallback with audit flag (ADR-036 amended) |
| E4-T27 | new | — | TTFT benchmark to first complete sentence, 10k-chunk corpus | TTFT measured to first complete sentence (ADR-036, ADR-039 M3) |
| E4-T28 | new | — | Numeric grounding gate per sentence, locale-aware | Numeric grounding gate, locale-aware, Hypothesis tests (ADR-036) |
| E4-T29 | new | — | Compliance checks: licence footer, jurisdiction label, staleness | Licence footer, jurisdiction label, staleness by state (ADR-036 decision 5) |
| E4-T3 | keep | 95 | Spike: Sonnet 5.5 prompt-cache hit behaviour with versioned tools |  |
| E4-T30 | new | — | Role policy table policy.py with default deny and CI matrix | Role policy as data, default deny, generated matrix (ADR-036 decision 6) |
| E4-T31 | new | — | Entitlement re-read before each step and before done | Entitlement re-read, ENTITLEMENT_CHANGED, message refused (ADR-033, #2) |
| E4-T32 | new | — | llm_egress_ack enforcement on the LLM prompt path | llm_egress_ack enforced on the Anthropic/Voyage query path (ADR-038, ADR-039 V4) |
| E4-T33 | new | — | Deterministic calc tool with grounded inputs | calc tool required by the numeric gate and policy table (ADR-036) |
| E4-T34 | new | — | Structured fund-facts lookup tool over fund_rr_facts and KID fee rows | Flagged `lookup_fund_facts` tool over `fund_rr_facts` and KID fee rows, for arm 4 (R4-D20 Q14, ADR-037) |
| E4-T4 | update | 96 | E4 settings keys and the stable error-code mapping | Model Armor flag keys, FAIL_OPEN removed, ENTITLEMENT_CHANGED, contextual flag off (ADR-036, ADR-016) |
| E4-T5 | keep | 97 | LLMClient: streaming, timeouts, jittered retries, config-only models |  |
| E4-T6 | update | 98 | LLMClient: breaker, fallback gating, model-retirement guard | Model-retirement guard #10, no temperature/top_p/top_k (ADR-039, 07 §7.4) |
| E4-T7 | keep | 99 | LLMClient: prompt caching, versioned tools, model retirement check |  |
| E4-T8 | keep | 100 | Guard-in: input cap and Presidio pseudonymization |  |
| E4-T9 | update | 101 | Model Armor client behind a flag with in-process fallback | Model Armor behind MODEL_ARMOR_ENABLED, fallback, fail-open prompts (ADR-036 amended, R4-D18 V3) |
| E5-T1 | keep | 78 | Spike: confirm Confluent Basic idle cost |  |
| E5-T10 | keep | 87 | outbox-relay worker role |  |
| E5-T11 | update | 88 | acl-applier worker role (polls acl_change_requests) | Polling worker on acl_change_requests, no Kafka, lock order (ADR-022 amended, ADR-028, R4-D7) |
| E5-T12 | update | 89 | Integration tests: chat and ACL survive a Kafka outage | Add the stop-Kafka, tighten-ACL, refused-within-60-s test (ADR-022 amended) |
| E5-T13 | update | 90 | Terraform: Confluent cluster, accounts, keys, ACLs, topics | Delete-policy topic settings, no applier ACL (ADR-013 amended, ADR-022 amended, ADR-029) |
| E5-T14 | update | 91 | bq-sink worker role | Sink guard dependency, no text/FCA in BigQuery, acl.changes analytics only (ADR-028, ADR-013 amended) |
| E5-T15 | new | — | Uncached sink-guard helper for the erasure ledger | New: uncached ledger point-read helper for every sink (ADR-028, R4-D20) |
| E5-T2 | update | 79 | Spike: partition counts and retention per topic | Delete-policy topics: retention 7 d, segment.ms 1 d, editability spike (ADR-013 amended, ADR-029) |
| E5-T3 | keep | 80 | Local compose: Kafka KRaft and Schema Registry |  |
| E5-T4 | update | 81 | Envelope and event payload models with JSON Schema | chat.audit and eval.sample payloads carry no text; pseudonym_id on subject events (ADR-013 amended, R4-D19 M5) |
| E5-T5 | update | 82 | Register schemas in Schema Registry and gate breaking changes | BACKWARD contracts for docs.* and chunks.* checked in CI (ADR-013 amended, ADR-034) |
| E5-T6 | update | 83 | Idempotent producer with traceparent and PUBLIC/FCA guard | Producer rejects fca_api source; FCA content never on Kafka (ADR-013 amended, ADR-026) |
| E5-T7 | keep | 84 | Consumer framework: dedupe, tenant transaction, envelope check |  |
| E5-T8 | keep | 85 | Consumer retries and redacted DLQ publishing |  |
| E5-T9 | keep | 86 | Worker entrypoint with WORKER_ROLES dispatch |  |
| E6-T1 | new | — | Spike: Docling on EDGAR 497K HTML and inline XBRL |  |
| E6-T10 | new | — | indexer: atomic per-document publish and lock order | Atomic per-document publish, lock order, gates (ADR-028 amended, R4-D5, 4.17) |
| E6-T11 | new | — | Replay, parser-bump and ACL-change tests with zero embed calls | Replay after parser bump, polling applier ACL test (ADR-027, ADR-022 amended) |
| E6-T12 | new | — | Dagster partitions and the etl job entrypoint |  |
| E6-T13 | new | — | etl-public: in-process EDGAR 497K pipeline as fa_etl_public | In-process path uses scan stage, atomic publish, ledger guard; no FCA on Kafka (ADR-028, ADR-026) |
| E6-T14 | new | — | Raw-text scan test across documents, chunks, events, BigQuery | Scan includes FCA marker and no answer text in Kafka/BigQuery (test #15, ADR-013 amended) |
| E6-T15 | new | — | dbt project and Postgres gold models as fa_dbt | dbt contract enforced on gold tables (ADR-014 amended, ADR-034) |
| E6-T16 | new | — | CI assertions: tenant tables RLS and no dbt full rebuild |  |
| E6-T17 | new | — | BigQuery dataset: partitioned tables, views, 48 h time travel | Project default max time travel 48 h plus per-dataset check (ADR-029 amended, R4-D18 V2) |
| E6-T18 | new | — | dbt-bigquery marts and the ingest_events feed | Ledger-guarded ingest mapping, no FCA/text, dbt sets no dataset options (ADR-029 amended, ADR-028) |
| E6-T19 | new | — | BigQuery isolation, byte-cap and time-travel acceptance test | Assert 48 h time travel on every dataset incl. dbt-created (ADR-029 amended) |
| E6-T2 | new | — | Scaffold the ETL package and daemon-less Dagster |  |
| E6-T20 | new | — | Ingest scan stage and quarantine in the silver worker | Ingest scan stage: sanitiser, pattern list, quarantine (ADR-036, ADR-034, 4.25) |
| E6-T21 | new | — | indexer embed stage: chunk identity and vector reuse | Chunk identity 8-column key, reuse index, generations keyed on identity (R4-D19 M1, ADR-035) |
| E6-T22 | new | — | voyage-context-4 contextualized chunk embeddings as an eval-only generation | `voyage-context-4` eval-only embedding generation on the E12 generations, for arm 2 (R4-D20 Q14, ADR-037, ADR-035) |
| E6-T3 | new | — | Synthetic per-tenant corpus generator |  |
| E6-T4 | new | — | Bronze asset: GCS by sha256, register documents, publish |  |
| E6-T5 | new | — | Silver transform: Docling parse, Presidio scrub, chunking | Chunk identity fields valid_from and parser_version, B0 structural prefix (ADR-027, ADR-016 amended) |
| E6-T6 | new | — | Pandera validation, ingest_rejects and versioned silver Parquet | Versioned silver path, Pandera SCHEMA_AND_DATA (ADR-014 amended, ADR-034) |
| E6-T7 | new | — | silver worker role: consume bronze, emit silver, guard writes | Sink guard before and after Parquet write, versioned path (ADR-028, 4.7) |
| E6-T8 | new | — | contextualizer: Haiku headers (default off), guarded sink | Contextual headers default OFF, B0 prefix kept, sink guard (ADR-016 amended, ADR-028) |
| E6-T9 | new | — | Suitability-rule extraction, validation and lookup |  |
| E7-T1 | new | — | Spike: calibrate the Haiku judge against ~30 human labels | Judge acceptance is judge-human rho^2 >= 0.4, not kappa; separate from the pilot (ADR-037 amended, ADR-017) |
| E7-T10 | new | — | Add the gate evaluator with thresholds and recall baseline | Release gates: refusal >= 0.90, numeric false rejects <= 3%, zero ungrounded numbers, paired recall lower bound >= -2 pp, ASR <= 3/300 (ADR-017, ADR-037) |
| E7-T11 | new | — | Wire the path-filtered PR eval job in CI |  |
| E7-T12 | new | — | Prove the gate with four deliberate-regression test PRs |  |
| E7-T13 | new | — | Add the weekly full eval run with CI lower bounds | Weekly run on the 200-item set plus guardrail sets and edge case #21 ASR line (ADR-037, 07 7.4 #21) |
| E7-T14 | new | — | Full eval on the fallback model gates LLM_FALLBACK_ENABLED |  |
| E7-T15 | new | — | Add the promptfoo red-team job |  |
| E7-T16 | new | — | Emit eval.sample.v1 outbox rows and thumbs feedback events | `eval.sample.v1` carries ids, hashes, flags only, no text (ADR-039 M5) |
| E7-T17 | new | — | Implement the eval-judge worker role | Judge reads redacted text from Postgres `messages` by `message_id`, skips erased messages (ADR-039 M5, 9.6) |
| E7-T18 | new | — | Verify eval-judge end to end with RLS on eval_scores |  |
| E7-T19 | new | — | Keshav labels the 30-item pilot with the labelling CLI | Keshav labels the 30-item pilot (about 6-8 h) with the labelling CLI (K-R4-4, ADR-037, R4-D15) |
| E7-T2 | new | — | Define the golden-set schema and loader with clusters and splits | Schema gets cluster_id and unit, slice, tranche, split public/private/synthetic, evidence spans; private skipped without the bucket (ADR-037, R4-D17, K-R4-3) |
| E7-T20 | new | — | Keshav labels items 31 to 60 to complete tranche 1 | Keshav labels items 31-60 (about 6-8 h) to complete tranche 1 = PR subset (K-R4-4, ADR-037) |
| E7-T21 | new | — | Keshav labels tranche 2 (140 items) and the intra-rater check | Keshav labels tranche 2, 140 items (about 28-39 h of the 40-55 h) and the 15% intra-rater check (K-R4-4, ADR-037, 2.10) |
| E7-T22 | new | — | Add the golden_stats cluster-rule and split check | L0 `golden_stats` check: at least 40 clusters, at most 5 per cluster (ADR-037, R4-D17) |
| E7-T23 | new | — | Cluster-level statistics: permutation, exact McNemar and Holm | Cluster aggregation, sign-flip permutation, exact McNemar, Holm over a fixed family, small slices exact or exploratory (ADR-037) |
| E7-T24 | new | — | Freeze the pre-registration of the four confirmatory arms | Frozen pre-registration naming exactly the four arms before the first run (ADR-037, R4-D17) |
| E7-T25 | new | — | PII guardrail eval: openpii-1.5m and Gretel finance sets | PII sets openpii-1.5m and Gretel finance, DE/FR recall, gauges (ADR-037, ADR-036, 9.9) |
| E7-T26 | new | — | Injection guardrail eval: gandalf, deepset smoke and LLMail-Inject | Injection sets gandalf, deepset (smoke only), LLMail-Inject wrapped chunks, ASR line (ADR-037, ADR-036, 7.4 #21) |
| E7-T27 | new | — | Compute and record the detectable effect from the pilot | Detectable effect computed from the pilot and recorded before any arm runs (ADR-037, R4-D15) |
| E7-T3 | new | — | Add adversarial, refusal and leak-probe cases to the golden set | Probe set kept as synthetic (outside the 200); templates for the refusal and injection slices of the 200 (ADR-037, ADR-017 L3) |
| E7-T5 | new | — | Build the eval job entrypoint, Langfuse datasets and run record | PR subset = tranche 1 (60 items); required `EVAL_BUDGET_USD` aborts a run; skipped private count (ADR-037) |
| E7-T6 | new | — | Implement L1 retrieval metrics: recall@k, MRR and nDCG | Tier-1 deterministic metrics (evidence-span recall@10, MRR, gold-version-in-top-5, numeric-in-span, footer present) per cluster; arm config (ADR-037, ADR-039 V1) |
| E7-T7 | new | — | Spike: run the four confirmatory ablation arms with Holm | Depends on E6-T22 and E4-T34 for arms 2 and 4; rerank/contextual spike becomes the four confirmatory arms with Holm via the Batches API; rerank-3 vs rerank-3-lite (ADR-037, R4-D17, ADR-039 V1) |
| E7-T8 | new | — | Implement L2 Ragas runner with CI lower bounds | Cluster-level intervals; judge metrics gate only when rho^2 >= 0.4, else exploratory (ADR-037) |
| E7-T9 | new | — | Implement L3 refusal, tier, jurisdiction and cross-tenant runner |  |
| E8-T1 | new | — | Replace Next.js 14 with a Vite React 19 TS scaffold |  |
| E8-T10 | new | — | Set up Playwright and an auditable test harness for the SPA |  |
| E8-T11 | new | — | Add Playwright specs for sign-in, streamed cited answer and feedback |  |
| E8-T12 | new | — | Add Playwright specs for resume, 429, 401 and XSS safety |  |
| E8-T13 | new | — | Add the as-of chip and the echoed parsed date | As-of chip sends ISO `as_of`; echoes the date the server applied (ADR-027, 6.10) |
| E8-T14 | new | — | Add the firm switcher with one session per firm | Firm switcher, one session per firm, nothing persisted (ADR-032, #17) |
| E8-T15 | new | — | Render licence footers and label private_demo sources | (updated) per-citation `source_class` label and stored footers in history (R4-D20 Q2) |
| E8-T16 | new | — | Add Playwright specs for firm switching, 421, as-of and footers | Playwright for #17 browser part, 421/503, as-of echo, footers, ENTITLEMENT_CHANGED (ADR-032, ADR-036, 7.4 #17) |
| E8-T17 | new | — | Add the quarantine summary view for the compliance role | Quarantine summary view for the compliance role, depends on E11-T28 (R4-D20 Q1, ADR-036) |
| E8-T2 | new | — | Add tenant discovery at /t/<slug> | Resolve slug to cell, then tenant from the per-cell host (ADR-031, 6.11) |
| E8-T3 | new | — | Add Identity Platform tenant sign-in with in-memory token | One auth instance per firm, in-memory, no persisted tenantId (ADR-032) |
| E8-T4 | new | — | Map API error codes to UI states with 401 and 429 handling | (updated again) cell hint is followed only when its host equals the `/resolve` answer (R4-D20 Q15) |
| E8-T5 | new | — | Build fetch-based SSE client with resume and idempotency |  |
| E8-T6 | new | — | Render the streamed turn with meta notice and refusal | Renders `notice` kinds, ANSWER_WITHHELD reasons, ENTITLEMENT_CHANGED abort (6.2, ADR-033, ADR-036) |
| E8-T7 | new | — | Render sanitized markdown, citations with excerpts and stale badges | Jurisdiction chip on citations from the new `jurisdiction` field (6.2, ADR-027) |
| E8-T8 | new | — | Add conversation history list, load and delete |  |
| E8-T9 | new | — | Add thumbs feedback on assistant messages |  |
| E9-T1 | new | — | Structured JSON logging with redaction processor |  |
| E9-T10 | new | — | End-to-end trace test across Kong, API, DB and LLM |  |
| E9-T11 | new | — | Terraform: log-based metrics and notification channel |  |
| E9-T12 | new | — | Terraform: four Cloud Monitoring dashboards | First-stage line 600 ms not 300; guardrail panels on the chat dashboard (ADR-039 M3, 9.9) |
| E9-T13 | new | — | Terraform: availability and latency SLOs with burn-rate alerts | Retrieval first-stage SLO <= 600 ms, TTFT unchanged (ADR-039 M3) |
| E9-T14 | new | — | Terraform: chat and retrieval alert policies |  |
| E9-T15 | new | — | Terraform: event pipeline and partition alert policies |  |
| E9-T16 | new | — | Terraform: monthly budget alerts on GCP billing and LLM cost | Budget alert at $180 against the $200 ceiling plus the $75 LLM share (R4-D16, 9.5, 2.5) |
| E9-T17 | new | — | Alert drill runbook and script |  |
| E9-T18 | new | — | Terraform: data-lifecycle dashboard for erasure, receipts and canary | Data-lifecycle dashboard: erasure windows per store, deletion receipts, canary, reconcile, ingest (ADR-030, ADR-034, 9.8) |
| E9-T19 | new | — | Terraform: reconciliation alert policies | Reconciliation alert policies per pair, ticket vs page, silent when the system is stopped (ADR-034, 9.7) |
| E9-T2 | new | — | OpenTelemetry bootstrap for chat-api and workers |  |
| E9-T20 | new | — | Terraform: erasure, canary and E12 job alert policies | Erasure age > 4 h, Langfuse 24 h, FAILED-canary (E12-T21) and E12 job-failure alerts (ADR-029, ADR-030, 9.8) |
| E9-T21 | new | — | Terraform: connector frozen, quarantine and silent-edit alerts | Connector frozen, > 5% quarantined and silent-edit alerts (ADR-026, ADR-036, E11-T7 hand-off) |
| E9-T22 | new | — | Emit guardrail hit, skip, latency and numeric-gate metrics | Guardrail hit, skip, latency and numeric-gate metrics on the live path; precision/recall gauges come from E7-T25/T26 (ADR-036, ADR-037, 9.9) |
| E9-T23 | new | — | Extend the alert drill to the round-4 alerts | Drill for every new round-4 alert (E9 Done-when, ADR-029, ADR-034) |
| E9-T3 | new | — | Instrument the chat turn with the named spans |  |
| E9-T4 | new | — | Link consumer spans to producer spans over Kafka headers |  |
| E9-T5 | new | — | Shared metrics module and 9.2 metric registry | Registry equals the whole 9.2 table incl. round-4 rows, with a dashboard attribute (ADR-034, ADR-036) |
| E9-T6 | new | — | Emit chat latency, cache, budget, DB pool and LLM cost metrics |  |
| E9-T7 | new | — | Emit event-pipeline and partition health metrics |  |
| E9-T8 | new | — | Complete /readyz with the 9.4 checks |  |
| E9-T9 | new | — | Leak test for logs, spans and metrics |  |
| E10-T1 | new | — | Spike: measure Cloud SQL start time and stopped billing |  |
| E10-T10 | new | — | Terraform Cloud Run jobs with per-job SAs and DB roles |  |
| E10-T11 | new | — | Terraform SPA bucket and ALB backend bucket wiring |  |
| E10-T12 | new | — | Terraform Cloud Scheduler triggers and paused-state drift | (updated again) ten triggers incl. daily `ledger-export`; erasure-verify hourly at minute 30 (R4-D20 Q5, Q8) |
| E10-T13 | new | — | Terraform Identity Platform tenant provisioning |  |
| E10-T14 | new | — | WIF and Terraform plan/apply pipeline |  |
| E10-T15 | new | — | Add deploy workflow: migrate, tagged revision, smoke test, shift |  |
| E10-T16 | new | — | Implement demo-down script and make demo-down |  |
| E10-T17 | new | — | Implement demo-prewarm Cloud Run job |  |
| E10-T18 | new | — | Implement demo-up script, Valkey lifecycle and make demo-up | Erasure job runs first after Cloud SQL is up and before any traffic path (ADR-029, ADR-039, 5.14) |
| E10-T19 | new | — | Implement demo-ttl job to bring a forgotten demo down |  |
| E10-T2 | new | — | Spike: worker pool scale to 0 and Terraform support |  |
| E10-T20 | new | — | Add security and connection budget invariant checks |  |
| E10-T21 | new | — | Verify no Terraform drift across a down and up cycle |  |
| E10-T22 | new | — | Add prod profile (HA flag, min instances) and plan test |  |
| E10-T23 | new | — | Load test with stub LLM at 10 QPS against synthetic corpus |  |
| E10-T24 | new | — | Confirm demo month cost from the billing export |  |
| E10-T25 | new | — | Terraform the E12 jobs, the receipt KMS key and the ledger export bucket | (updated) `KAFKA_VERIFY_API_KEY` read-only key; ledger-export scheduled, erasure-replay manual (R4-D20 Q5, Q6) |
| E10-T26 | new | — | Terraform retention settings and the retention check | Retention settings in Terraform and checked: BigQuery 48 h default, GCS soft delete 0, topics, logs 7 d (ADR-029, ADR-039 V2) |
| E10-T27 | new | — | Add the canary drill and model preflight stages to demo-up | demo-up canary drill then 1-token model preflight (ADR-030, 9.8, R4 E10 line) |
| E10-T28 | new | — | Add the cloud restore drill with erasure-replay before traffic | Cloud restore drill: PITR clone, erasure-replay before traffic (ADR-029, ADR-030, 7.4 #14) |
| E10-T3 | new | — | Spike: confirm ALB, Cloud Armor and Confluent idle cost |  |
| E10-T4 | new | — | Terraform v2 root: state, profiles, registry, service SAs |  |
| E10-T5 | new | — | Add org policy check for requireInvokerIam on fa-gateway |  |
| E10-T6 | new | — | Terraform Cloud SQL (PG16, PSC, no public IP, profile HA flag) | Cloud SQL backups 7 d and PITR log retention 7 d, validated (ADR-029, ADR-039 V5) |
| E10-T7 | new | — | Create DB roles, passwords and the dagster database in Cloud SQL |  |
| E10-T8 | new | — | Terraform chat-api Cloud Run service on the VPC |  |
| E10-T9 | new | — | Terraform fa-worker Cloud Run worker pool |  |
| E11-T1 | new | — | Spike: FCA Handbook API format and rate limit |  |
| E11-T10 | new | — | Source class policy: retire law, erase publisher and FCA |  |
| E11-T11 | new | — | Boundary contracts and blocking rules |  |
| E11-T12 | new | — | Quarantine batch circuit, operator release and reject |  |
| E11-T13 | new | — | Model Armor document screening in the scan stage |  |
| E11-T14 | new | — | Private ingest refused without llm_egress_ack |  |
| E11-T15 | new | — | ecfr connector: 17 CFR 275 versions |  |
| E11-T16 | new | — | sec connector: 497K per-CIK submissions |  |
| E11-T17 | new | — | sec connector: RR quarterly datasets into fund_rr_facts |  |
| E11-T18 | new | — | eurlex connector: CELLAR PRIIPs and MiFID in EN, DE, FR |  |
| E11-T19 | new | — | legislation_gov_uk connector: point-in-time XML |  |
| E11-T2 | new | — | Spike: CELLAR rate behaviour and formats |  |
| E11-T20 | new | — | fca_api connector: current text only |  |
| E11-T21 | new | — | publisher connector: manual KIDs, 497K and ADV |  |
| E11-T22 | new | — | FCA kill switch and purge_source('fca_api') |  |
| E11-T23 | new | — | Cache invalidation on publish of a new PUBLIC version |  |
| E11-T24 | new | — | As-of from versions: known_at and no-history refusal |  |
| E11-T25 | new | — | Poison corpus test: nothing malformed is indexed |  |
| E11-T26 | new | — | First corpus, per-source fixtures and weekly live smoke |  |
| E11-T27 | new | — | Optional ESMA / JC Q&A connector with disclaimer |  |
| E11-T28 | new | — | GET /v1/admin/quarantine/summary for the compliance role | `GET /v1/admin/quarantine/summary`: counts by source and reason code, compliance role, no text (R4-D20 Q1, ADR-036) |
| E11-T3 | new | — | Spike: eCFR terms page and API limits |  |
| E11-T4 | new | — | Migration: source_registry and source_observations |  |
| E11-T5 | new | — | Migration: bitemporal document_versions with EXCLUDE |  |
| E11-T6 | new | — | Connector interface, types and fixture harness |  |
| E11-T7 | new | — | Change capture: idempotent observations, silent edit, ordering |  |
| E11-T8 | new | — | Listing diff: two-strike withdrawal and mass-delete breaker |  |
| E11-T9 | new | — | reconcile_lineage: idempotent version and chunk reconcile |  |
| E12-T1 | new | — | Spike: Cloud SQL backup expiry while the instance is stopped |  |
| E12-T10 | new | — | Advisor-scope erasure and subject unlink via pseudonym_map |  |
| E12-T11 | new | — | Admin API: advisor erasure, status read, document delete queue |  |
| E12-T12 | new | — | GCS erasure step: bronze, silver and quarantine objects |  |
| E12-T13 | new | — | BigQuery erasure step: batched DML and settings check |  |
| E12-T14 | new | — | Kafka erasure step: wait out retention and topic-scan probe |  |
| E12-T15 | new | — | Langfuse erasure step: batch delete, retry and 24 h alert |  |
| E12-T16 | new | — | Receipt phase 1: erasure_steps to signed JSON receipt |  |
| E12-T17 | new | — | erasure-verify: end-of-window re-sweeps and phase-2 receipt |  |
| E12-T18 | new | — | Document the deletion promise wording |  |
| E12-T19 | new | — | purge_source pull model: tenant erasure-worker polls source_purges |  |
| E12-T2 | new | — | Spike: BigQuery time-travel probe and observable windows |  |
| E12-T20 | new | — | erasure-replay and the daily ledger export |  |
| E12-T21 | new | — | Canary drill at demo start |  |
| E12-T22 | new | — | reconcile job: framework, manifests, source-bronze-silver-chunks |  |
| E12-T23 | new | — | reconcile: ANN canary, BigQuery, tombstones, BQ settings |  |
| E12-T24 | new | — | Replay twice after a parser bump: zero resurrection |  |
| E12-T25 | new | — | embed_generations schema, active_embed_model and model allow-list |  |
| E12-T26 | new | — | embed-backfill job with dual write while building |  |
| E12-T27 | new | — | Generation validation and per-tenant flip, eval tenant first |  |
| E12-T28 | new | — | Retire the blue generation after 7 days as an erasure-class operation |  |
| E12-T3 | new | — | Spike: Langfuse trace delete behaviour against a stub |  |
| E12-T4 | new | — | Spike: Voyage batch throughput under the 25% RPM cap |  |
| E12-T5 | new | — | Migration: deletion queue, steps, receipts and ledger tables |  |
| E12-T6 | new | — | Migration: source_purges and reconciliation tables |  |
| E12-T7 | new | — | erasure-worker role: poll, claim and request state machine |  |
| E12-T8 | new | — | Tombstone-first deletion under the document lock; operator release |  |
| E12-T9 | new | — | Postgres erasure step: ordered DELETE, counts, VACUUM, cache purge |  |
| E13-T1 | new | — | cells.json schema, signing and verification |  |
| E13-T10 | new | — | PUBLIC manifest comparison and drift alert |  |
| E13-T11 | new | — | Multiple logins: two firms, one token each, alias fallback |  |
| E13-T12 | new | — | Privacy notice: residency wording and global-data list |  |
| E13-T13 | new | — | move-tenant job: state machine, freeze and rollback |  |
| E13-T14 | new | — | move-tenant: ordered Postgres copy and hash verify |  |
| E13-T15 | new | — | move-tenant: GCS and BigQuery copy, kill-target test |  |
| E13-T16 | new | — | move-tenant: cutover, moved 421, grace and source erase |  |
| E13-T2 | new | — | CellDirectory loader: GCS read, 60 s refresh, baked fallback |  |
| E13-T3 | new | — | GET /resolve?slug= from the signed directory |  |
| E13-T4 | new | — | principal: WRONG_CELL and TENANT_MOVED 421, zero DB reads |  |
| E13-T5 | new | — | Token tenant must equal URL tenant and cell map entry |  |
| E13-T6 | new | — | Two-cell docker compose suite with a cells.json router |  |
| E13-T7 | new | — | Cell down: 503 CELL_UNAVAILABLE; provider outage is not a cell failure |  |
| E13-T8 | new | — | Compose separation and per-cell data isolation tests |  |
| E13-T9 | new | — | Per-cell etl-public ingest and PUBLIC manifest |  |
