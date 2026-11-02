## 6. Interfaces and contracts

### 6.1 HTTP API v1 (served by `chat-api` behind Kong; same origin as the SPA)

All `/v1` routes except `GET /v1/tenants/{slug}` require `Authorization: Bearer <Identity Platform ID token>`. Errors are JSON `{"error": {"code", "message", "request_id", "retryable"}}` with a stable code and a fixed message, never exception text. `X-Request-Id` is set by Kong (`correlation-id`) and returned.

| Method and path | Auth / role | Request | Response |
|---|---|---|---|
| `GET /v1/tenants/{slug}` | none (public; Kong IP limit) | none | `{"display_name", "idp_tenant_id"}` only (served by `fa_tenant_lookup`); 404 `TENANT_NOT_FOUND` |
| `GET /v1/me` | any | none | `{advisor_id, tenant_id, display_name, role, tier, jurisdictions, licenses}` |
| `POST /v1/chat` | any | headers `Idempotency-Key` (required), body `{conversation_id?: uuid, message: string}` | `text/event-stream` (§6.2); 409 `IDEMPOTENCY_KEY_REUSED` if the key was used with a different body |
| `GET /v1/chat/{turn_id}/events` | owner of the turn | header `Last-Event-ID` | `text/event-stream` replay of `turn_events` with `seq > Last-Event-ID`, then tail until `done` |
| `GET /v1/conversations` | any | `?cursor` | list of own conversations |
| `GET /v1/conversations/{id}/messages` | owner | `?cursor` | messages with citations (redacted) |
| `DELETE /v1/conversations/{id}` | owner | none | 204 (soft delete) |
| `POST /v1/messages/{id}/feedback` | owner | `{score: -1 or 1, comment?: string}` | 204; writes `feedback` + outbox `eval.events.v1` |
| `GET /v1/escalations` | `compliance_officer`, or owner for own | none | list of `escalations` |
| `PATCH /v1/admin/advisors/{id}` | `tenant_admin` | `{role?, tier?, jurisdictions?, licenses?, status?}` | 200; direct `UPDATE advisors` (policy allows tenant admins only), bumps `entitlement_version`, outbox `AdvisorEntitlementChanged`; takes effect within the 60 s `principal` cache TTL |
| `POST /v1/admin/documents/{id}/acl-changes` | `tenant_admin` | `{tier_required?, jurisdiction?}` | 202 `{request_id}`; inserts `acl_change_requests` + outbox `AclChangeRequested` in one transaction; applied asynchronously by the `acl-applier` worker |
| `GET /v1/admin/acl-changes/{request_id}` | `tenant_admin` | none | `{status: pending or applied or failed, applied_at}` |
| `DELETE /v1/admin/documents/{id}` | `tenant_admin` | none | 202 `{request_id}`; an `acl_change_requests` row with `action = delete`; the applier deletes the document and chunks and purges `answer_cache` rows citing it |
| `GET /healthz` | none | none | liveness (process up) |
| `GET /readyz` | none | none | readiness: DB reachable and role flags / FORCE RLS / pgvector >= 0.8 asserted, Kafka reachable (degraded, not failing, for chat), model availability (configured models not retired or soon-retiring), firebase-admin verifier initialised |

Error codes: `UNAUTHENTICATED` (401), `FORBIDDEN` (403), `INPUT_TOO_LONG` (413), `INPUT_BLOCKED` (Model Armor or guard), `GUARD_UNAVAILABLE` (screen failed closed), `RATE_LIMITED` (429, `Retry-After`, from Kong or per-tenant budget), `TENANT_BUDGET_EXCEEDED`, `NO_FIRM_DOCUMENTATION` (a refusal event, not an HTTP error), `LLM_UNAVAILABLE`, `RETRIEVAL_UNAVAILABLE`, `TURN_INTERRUPTED`, `IDEMPOTENCY_KEY_REUSED`, `INTERNAL`. Numeric limits (input cap, budgets, rate limits) are config values (§6.6).

### 6.2 SSE event contract

`Content-Type: text/event-stream`. Each event has `id: <seq>` (integer, strictly increasing within a turn, persisted in `turn_events`), `event: <name>` and a JSON `data:`. The client reconnects with `Last-Event-ID` to `GET /v1/chat/{turn_id}/events`; because the server persists events, a dropped connection loses nothing. The turn id is returned in the first event and is derived from the `Idempotency-Key`, so a retried `POST /v1/chat` with the same key and body is a replay, not a second generation. A heartbeat comment line is sent every `SSE_HEARTBEAT_S` (value set in E4). Cloud Run request timeout is 3600 s; Kong `read_timeout` 3,600,000 ms.

| Event | Data | Notes |
|---|---|---|
| `turn` | `{turn_id, conversation_id, message_id}` | `seq 0`, first event |
| `meta` | `{retrieval_degraded: bool, reason?: "rerank_timeout" or "rerank_429"}` | emitted once after rerank; `true` means the rerank fell back to RRF order; also stored in `messages.retrieval_degraded` |
| `tool` | `{tool, status: "started" or "ok" or "error", tool_use_id}` | tool name and status only; never payloads, inputs or exception text (G-04) |
| `delta` | `{text}` | output after sentence-buffered PII redaction; the client appends |
| `citation` | `{index, chunk_id, source_title, regulatory_ref, last_reviewed_at, stale: bool, excerpt}` | emitted by the server only, after the citation verifier accepts `[n]`; `excerpt` is redacted (G-16) |
| `refusal` | `{code: "NO_FIRM_DOCUMENTATION", escalate_offer: bool}` | confidence gate failed; no LLM call was made |
| `error` | `{code, retryable}` | codes from §6.1; the stream ends after it |
| `done` | `{message_id, finish_reason}` | last event; `finish_reason` in (`end_turn`, `max_tokens`, `refusal`, `gate`) |

If the instance producing a turn dies, the replay endpoint appends `error {TURN_INTERRUPTED, retryable: true}` once the last persisted event is older than `TURN_LEASE_S` (value set in E4); the client resubmits with a new `Idempotency-Key`.

### 6.3 Tool contracts

Retrieval is not a model decision: the orchestrator runs retrieval first and injects the result as a JSON-encoded `tool_result` for a synthetic `search_firm_kb` call (so retrieved text is untrusted tool content, never in the system prompt). Tools never accept `tenant_id`, tier, jurisdiction or licenses; all come from `Principal`. Tool definitions are versioned with the prompt (changing them invalidates the prompt cache). Max 3 iterations; unknown tool names rejected; arguments validated by Pydantic models; outputs are `model_dump_json()`; errors are `{"error_code"}` without exception text.

| Tool | Input | Output | Notes |
|---|---|---|---|
| `search_firm_kb` (pre-fetched; the model may call it again for a follow-up) | `query: string`, `top_k?: int` (lower and upper bound enforced) | `{results:[{n, chunk_id, source_title, regulatory_ref, last_reviewed_at, stale, text}], total_found, today}` | goes through `RetrievalService.search` + rerank + gate. `stale` computed server-side from today's date; `today` placed after the cache breakpoint |
| `lookup_suitability_rule` | `product_category: string`, `client_risk_profile: enum(conservative, moderate, aggressive)` | `{rules:[{rule_name, product_category, client_risk_profile, jurisdiction, regulatory_ref, rule_text, last_reviewed_at, stale}], total_found}` | reads `suitability_rules`, populated by the ETL (G-07) |
| `lookup_product_factsheet` | `product_name: string` (wildcards escaped, `LIMIT` enforced) | `{results:[{title, jurisdiction, regulatory_ref, last_reviewed_at, product_category, risk_level, stale, chunks:[redacted text]}], total_found}` | redacted chunks only; no `raw_content` (G-03) |
| `escalate_to_compliance` | `reason: string`, `product_class: string` | `{escalation_id (uuid), status: "pending_review"}` | licenses taken server-side from `advisors.licenses`; row inserted in `escalations` and outbox event; client sees tool name + status only (G-18). A turn that calls this tool is never written to the answer cache |

### 6.4 Kafka topic catalogue

Cluster: Confluent Cloud Basic (us-central1); local `apache/kafka:4.4.0`. Client `confluent-kafka` 2.16.1, idempotent producers, at-least-once consumers with idempotent sinks (`processed_events`). `chat-api` has no Kafka credentials: its events leave through the `outbox` table and the `outbox-relay`. Keys are `tenant_id` (per-tenant ordering). Value schemas: JSON Schema in Schema Registry (Essentials, 100 schemas free; subject `<topic>-value`, registry default compatibility), generated from Pydantic envelope models. Common envelope: `{event_id, event_type, schema_version, tenant_id, occurred_at, trace_context, payload}`; the Kafka header carries `traceparent`. Payloads are minimised: ids, hashes, redacted text only; never raw documents or prompts (D13j). Confluent Basic has no RBAC: one service account and API key per service (`fa-worker`, `etl`, `etl-public`, `eval`), Kafka ACLs per service account, limits 50 API keys, 1,000 ACLs and 1,500 partitions (D15.8). Partition counts and retention are set in E5 within those limits (the brief gives no values); the single DLQ is `dlq.v1`.

Consumer rule: every pipeline consumer (`silver`, `contextualizer`, `indexer`, `acl-applier`, `eval-judge`) rejects a message whose `envelope.tenant_id` differs from the message key, or whose tenant is PUBLIC, to `dlq.v1` with a reason (D16.6). `bq-sink` accepts PUBLIC analytics events.

| Topic | Key | Schema / event types | Producer | Consumer group | Retention | Replay |
|---|---|---|---|---|---|---|
| `docs.bronze.v1` | `tenant_id` | `DocBronzeLanded` {document_id, bronze_uri, sha256, source, fetched_at} | `etl` job (Dagster bronze asset) | `cg.silver` | E5 | Dagster re-publishes for a partition; bronze is immutable |
| `docs.silver.v1` | `tenant_id` | `DocSilverReady` {document_id, silver_uri, chunk_count, parser_version, reject_count} | `fa-worker` role `silver` | `cg.contextualizer` | E5 | offset reset; idempotent via `processed_events` |
| `chunks.contextualized.v1` | `tenant_id` | `ChunksContextualized` {document_id, silver_uri, header_model, rules_extracted} | `fa-worker` role `contextualizer` | `cg.indexer` | E5 | offset reset |
| `chunks.indexed.v1` | `tenant_id` | `ChunksIndexed` {document_id, upserted, unchanged, deleted, embed_model, corpus_version} | `fa-worker` role `indexer` | `cg.bq-sink` | E5 | offset reset; re-embed = replay of `docs.bronze.v1` |
| `ingest.analytics.v1` | `tenant_id` (PUBLIC id) | `PublicIngestStage` {stage, document_id, counts} | `etl-public` job | `cg.bq-sink` | E5 | rerun the job |
| `acl.changes.v1` | `tenant_id` | `AclChangeRequested` {request_id, document_id, action, new ACL}, `AclChangeApplied` {request_id, acl_version}, `AdvisorEntitlementChanged` {advisor_id, entitlement_version} | `outbox-relay` (rows written by `admin` and by `acl-applier`) | `cg.acl-applier` (`AclChangeRequested` only), `cg.bq-sink` | E5 | offset reset; applier is idempotent on `request_id` |
| `chat.audit.v1` | `tenant_id` | `TurnCompleted`, `TurnRefused`, `EscalationCreated` {ids, hashes, redacted text, retrieved chunk ids, model, gate result, retrieval_degraded} | `outbox-relay` (from `agent`) | `cg.bq-sink` | E5 | outbox rows remain in Postgres until published |
| `chat.usage.v1` | `tenant_id` | `TurnUsage` {tokens, cache read, latency, cost estimate} | `outbox-relay` | `cg.bq-sink` | E5 | offset reset |
| `eval.sample.v1` | `tenant_id` | `TurnSampled` {message_id, redacted question, redacted answer, cited excerpts (redacted)} written for a `EVAL_SAMPLE_RATE` fraction of turns | `outbox-relay` (from `agent`) | `cg.eval-judge` | E5 | offset reset; judge dedupes on `message_id` + metric |
| `eval.events.v1` | `tenant_id` | `FeedbackRecorded`, `JudgeScored`, `EvalRunCompleted` | `outbox-relay` (feedback, judge scores), `eval` job (direct idempotent producer) | `cg.bq-sink` | E5 | offset reset |
| `dlq.v1` | original key | original envelope + `{source_topic, consumer, error_code, reason, attempts}` (payload redacted) | any consumer after retries or envelope check | operator tooling | E5 | operator re-publishes after the fix |

Gateway audit is not on Kafka: Kong `file-log` goes to Cloud Logging and a log sink to BigQuery (ADR-023).

### 6.5 Kong routes and plugins (OSS 3.9.4, DB-less; D12, D16)

Paths use prefixes or `~` regexes, never globs. Plugins in use: `rate-limiting` (`limit_by: ip`, and `limit_by: header` with `header_name: X-RL-Key`, `policy: redis` against Valkey, `sync_rate: 0` on the chat route, 429 with `Retry-After`), `request-size-limiting`, `cors`, `correlation-id`, `bot-detection`, `request-transformer`, `pre-function`, `prometheus`, `opentelemetry`, `file-log`, and for the egress route `key-auth`, `ip-restriction` and (spike) `ai-proxy` (`route_type: preserve`) with `log_statistics`. The `pre-function` sets `X-Serverless-Authorization` and `X-RL-Key = sha256(Authorization)` (so raw tokens never become Valkey keys) and runs before `rate-limiting` in the access phase; verified in the E2 spike. Not used: `jwt` (static per-consumer keys, no JWKS), `http-log`, Enterprise `openid-connect`, `rate-limiting-advanced`, `ai-*` Enterprise plugins. Numeric limits are config (§6.6) and set in E2.

`file-log` writes to stdout with a field whitelist: timestamp, route, method, status, latency, request id, client IP hash; no `Authorization`, no bodies, no query strings.

| Route | Paths / methods | Upstream | Plugins |
|---|---|---|---|
| `chat` | `POST ~/v1/chat$` | `chat-api` | `request-transformer` (remove client `X-User-Id`, `X-Tenant-Id`, `X-Serverless-Authorization`, `X-RL-Key`), `pre-function` (ID token from the metadata server to `X-Serverless-Authorization`, `X-RL-Key`), `rate-limiting` by IP, `rate-limiting` by `X-RL-Key` (stricter, per session), `request-size-limiting`, `cors`, `correlation-id`, `bot-detection`, `opentelemetry`, `prometheus`, `file-log`; `response_buffering: false`, `request_buffering: false`; service `read_timeout` 3,600,000 ms |
| `chat-resume` | `GET ~/v1/chat/[^/]+/events$` | `chat-api` | as `chat` |
| `api` | prefix `/v1/` (lower priority than the routes above) | `chat-api` | as `chat` with the general (not strict) limits |
| `tenant-discovery` | `GET ~/v1/tenants/[^/]+$` | `chat-api` | `rate-limiting` by IP only (no bearer), `cors`, `correlation-id`, `request-size-limiting`, `file-log` |
| `llm-egress` (conditional on spike) | prefix `/egress/anthropic`, callable by `chat-api` only | `https://api.anthropic.com` | `key-auth` (consumer `chat-api`, key from Secret Manager), `ip-restriction` (VPC range), `ai-proxy` `preserve` or plain proxy, `request-transformer` adds the API key from env, global LLM `rate-limiting`, `log_statistics`. Native Messages format only (no OpenAI-format translation) |

No `/internal/*` route exists: `chat-api` serves no internal endpoints and Kong returns 404 for anything not listed. The `demo-prewarm` job reaches `/readyz` inside the VPC, not through Kong. Kong status listener serves liveness; admin API off. `kong.yml` is validated in CI by `kong config parse`.

### 6.6 Configuration keys

One typed `Settings` class (pydantic-settings). No secret has a default; a missing required key fails boot. Secrets come from Secret Manager (cloud) or `.env` (local). "Set in Ex" means the brief gives no value; the epic fixes it by measurement.

| Key | Value / default | Used by |
|---|---|---|
| `ENV_PROFILE` | `dev` / `demo` / `prod` | all; selects HA flag, min instances |
| `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | required (secret); user is the process role (`fa_app`, `fa_worker`, ...) | all |
| `DB_PORT` | 5432 (ADR-025 R7) | all |
| `DB_POOL_SIZE`, `DB_STATEMENT_TIMEOUT_MS` | required; pool per instance x max instances over all services must stay <= 300 of Cloud SQL `max_connections` 400 (D15.7) | chat-api, worker |
| `PUBLIC_TENANT_ID` | required uuid | migrate, principal |
| `IDP_PROJECT_ID` | required; firebase-admin tenant-aware verification uses it (`aud`, `iss`) | `auth` |
| `ENTITLEMENT_CACHE_TTL_S` | 60 | `principal` |
| `ANTHROPIC_API_KEY` | required (secret); held by Kong when the egress route is used | `llm`, worker |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` or the Kong egress URL | `llm` |
| `LLM_MODEL_ANSWER` | `claude-sonnet-5-5` | `llm` |
| `LLM_MODEL_AUX` / `LLM_MODEL_JUDGE` | `claude-haiku-5-5` (judge must differ from answer) | guardrails spot-check, condensation, ETL, evals |
| `LLM_MODEL_FALLBACK`, `LLM_FALLBACK_ENABLED` | `claude-sonnet-4-6`, `false` until the gate passes against it | `llm` |
| `LLM_MAX_ITERATIONS` | 3 | `agent` |
| `MODEL_RETIRE_WARN_DAYS` | 30; a model in the config allowlist fails readiness when retired or retiring within this many days; unknown ids fail; a deprecated model with no retirement date passes with a warning (ADR-025 R6) | `llm`, `/readyz` |
| `LLM_MAX_TOKENS`, `LLM_TIMEOUT_S`, `LLM_RETRIES`, `LLM_BREAKER_*` | required; set in E4 | `llm` |
| `LLM_PRICE_TABLE_JSON` | required; input and output USD per million tokens per provider / model; feeds `llm_cost_usd_total` (ADR-025 R73) | `llm`, metrics |
| `LLM_MONTHLY_BUDGET_USD` | 75; the LLM share of the $100-200 demo budget (ADR-025 R73) | budget alert |
| `PROMPT_VERSION` | required; versions system prompt and tools | `agent`, cache key |
| `VOYAGE_API_KEY` | required (secret) | `retrieval`, worker |
| `EMBED_MODEL`, `EMBED_DIM` | `voyage-4`, 1024 | `retrieval`, indexer |
| `RERANK_MODEL`, `RERANK_ENABLED` | `rerank-2.5-lite`, decided by the ablation | `retrieval` |
| `RERANK_TIMEOUT_MS`, `RERANK_CANDIDATES`, `RERANK_TOP_N` | timeout: set in E3; candidates: default 15, range 10-30, the L1 ablation sets it (D14.1); top-n 6 | `retrieval` |
| `RRF_K` | 60 | `retrieval` |
| `EMBED_MAX_RETRIES` | 2, with jitter; then the turn fails with `RETRIEVAL_UNAVAILABLE` (ADR-025 R36) | `retrieval` |
| `HNSW_EF_SEARCH`, `HNSW_MAX_SCAN_TUPLES` | ~80-100, 20000 | `retrieval` |
| `GATE_MIN_SCORE` | required; set in E3 by eval | `retrieval` |
| `GATE_MIN_RESULTS` | 2; degraded gate passes if RRF returns at least this many candidates and marks the answer `retrieval_degraded` (ADR-025 R37) | `retrieval` |
| `SEARCH_TOP_K_MAX`, `RETRIEVAL_LEG_LIMIT` | 10, 40 (ADR-025 R40) | `retrieval` |
| `STALE_AFTER_MONTHS` | 12; one key for retrieval, gold models and UI (ADR-025 R39) | `retrieval`, dbt, SPA |
| `CITATION_MIN_OVERLAP` | 0.5; tuned by E7 (ADR-025 R46) | `guardrails` (citation verifier) |
| `ANSWER_CACHE_ENABLED`, `ANSWER_CACHE_TTL_S` | true, 86400 | `retrieval` |
| `HISTORY_MAX_TURNS`, `HISTORY_MAX_TOKENS` | 6, 3000 | `agent` |
| `INPUT_MAX_CHARS` | 4000; Kong request-size limit 64 KB (ADR-025 R27) | `guardrails`, Kong size limit |
| `MODEL_ARMOR_TEMPLATE`, `MODEL_ARMOR_TIMEOUT_MS`, `MODEL_ARMOR_FAIL_OPEN` | required, 500, `false` | `guardrails` |
| `TENANT_TOKEN_BUDGET`, `TENANT_MAX_CONCURRENCY` | 2,000,000 tokens per UTC day (counters in Postgres `tenant_usage`), 20 (ADR-025 R47) | `agent` |
| `SSE_HEARTBEAT_S`, `TURN_LEASE_S` | required; set in E4 | `agent` |
| `SSE_REPLAY_TTL_S` | 600; after it resume returns 410 `TURN_EXPIRED` (ADR-025 R49) | `agent` |
| `FACTSHEET_MAX_CHUNKS` | 8; E4 can change it (ADR-025 R43) | `retrieval` |
| `CONTEXTUAL_RETRIEVAL_ENABLED` | true; the L1 ablation decides | worker |
| `KAFKA_BOOTSTRAP`, `KAFKA_API_KEY`, `KAFKA_API_SECRET` | required; one service account and key per service (`fa-worker`, `etl`, `etl-public`, `eval`); none for `chat-api` | outbox-relay, worker, jobs |
| `SCHEMA_REGISTRY_URL`, `SCHEMA_REGISTRY_API_KEY`, `SCHEMA_REGISTRY_API_SECRET` | required | producers, consumers |
| `KAFKA_CONSUMER_MAX_ATTEMPTS`, `KAFKA_RETRY_BACKOFF_MS` | 5, 500 (ADR-025 R53) | worker |
| `OUTBOX_RELAY_BATCH`, `OUTBOX_RELAY_POLL_MS` | 100, 500 (ADR-025 R53) | `outbox-relay` |
| `WORKER_ROLES` | comma list of `outbox-relay`, `silver`, `contextualizer`, `indexer`, `acl-applier`, `eval-judge`, `bq-sink` | worker |
| `GCS_DATA_BUCKET`, `BQ_DATASET`, `BQ_MAX_BYTES_BILLED` | required | jobs, worker |
| `LANGFUSE_ENABLED`, `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | secrets required when enabled | wrapper |
| `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_DB_CAPTURE_PARAMS` | required, `false` | all |
| `CORS_ALLOWED_ORIGINS` | the SPA origin | Kong |
| `RATE_LIMIT_IP_PER_MIN`, `RATE_LIMIT_TOKEN_PER_MIN`, `RATE_LIMIT_CHAT_PER_MIN` | 300 (all routes), 120 (api routes), 20 per session (chat routes); Valkey down fails open, chat-api budgets still apply (ADR-025 R26) | Kong |
| `AUDIT_IP_SALT` | secret (Secret Manager); salt for the client IP HMAC-SHA256 in the gateway audit (ADR-025 R28) | Kong |
| `DEMO_TTL_HOURS` | 4 (ADR-025 R81) | `demo-ttl` job |
| `OUTBOX_DRAIN_TIMEOUT_MIN` | 10 (then force; remaining outbox rows are delivered on the next `demo-up`) | `demo-down` |
| `VALKEY_INSTANCE_NAME` | fixed Memorystore name; endpoint passed to Kong as an env var by `demo-up` | demo script, Kong |
| `EVAL_SAMPLE_RATE` | 0.05-0.10 (5-10% of completed turns); value set in E7 | `agent`, `eval-judge` |
| `EVAL_TENANT_ID` | required uuid of the dedicated `eval` tenant (bound into `fa_eval` policies) | migrate, eval jobs |
| `MESSAGES_PARTITIONS_AHEAD`, `MESSAGES_RETENTION_MONTHS` | 3, 6 (ADR-025 R20) | `maintenance` |
| `PRESIDIO_SPACY_MODEL` | `en_core_web_sm` | `guardrails`, `silver` |
| `KONG_EGRESS_KEY` | secret (Secret Manager) for the `key-auth` consumer `chat-api` on the egress route; only if the spike adopts it | `llm`, Kong |
| `DAGSTER_PG_DB`, `DAGSTER_PG_USER`, `DAGSTER_PG_PASSWORD` | `dagster`, `fa_dagster`, secret | `etl`, `etl-public` |
