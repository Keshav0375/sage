## 6. Interfaces and contracts

### 6.1 HTTP API v1 (served by `chat-api` behind Kong; same origin as the SPA)

All `/v1` routes except `GET /v1/tenants/{slug}` require `Authorization: Bearer <Identity Platform ID token>`. Errors are JSON `{"error": {"code", "message", "request_id", "retryable"}}` with a stable code and a fixed message, never exception text. `X-Request-Id` is set by Kong (`correlation-id`) and returned.

| Method and path | Auth / role | Request | Response |
|---|---|---|---|
| `GET /v1/tenants/{slug}` | none (public; Kong IP limit) | none | `{"display_name", "idp_tenant_id"}` only (served by `fa_tenant_lookup`); 404 `TENANT_NOT_FOUND` |
| `GET /v1/me` | any | none | `{advisor_id, tenant_id, display_name, role, tier, jurisdictions, licenses}` |
| `POST /v1/chat` | any | headers `Idempotency-Key` (required), body `{conversation_id?: uuid, message: string, as_of?: date}` (`as_of` from the UI chip, §6.10) | `text/event-stream` (§6.2); 409 `IDEMPOTENCY_KEY_REUSED` if the key was used with a different body |
| `GET /v1/chat/{turn_id}/events` | owner of the turn | header `Last-Event-ID` | `text/event-stream` replay of `turn_events` with `seq > Last-Event-ID`, then tail until `done` |
| `GET /v1/conversations` | any | `?cursor` | list of own conversations |
| `GET /v1/conversations/{id}/messages` | owner | `?cursor` | messages with citations (redacted) |
| `DELETE /v1/conversations/{id}` | owner | none | 204 (soft delete) |
| `POST /v1/messages/{id}/feedback` | owner | `{score: -1 or 1, comment?: string}` | 204; writes `feedback` + outbox `eval.events.v1` |
| `GET /v1/escalations` | `compliance_officer`, or owner for own | none | list of `escalations` |
| `PATCH /v1/admin/advisors/{id}` | `tenant_admin` | `{role?, tier?, jurisdictions?, licenses?, status?}` | 200; direct `UPDATE advisors` (policy allows tenant admins only), bumps `entitlement_version`, outbox `AdvisorEntitlementChanged`; takes effect within the 60 s `principal` cache TTL |
| `POST /v1/admin/documents/{id}/acl-changes` | `tenant_admin` | `{tier_required?, jurisdiction?}` | 202 `{request_id}`; inserts `acl_change_requests` + outbox `AclChangeRequested` (analytics only) in one transaction; applied asynchronously by the `acl-applier` worker, which polls `acl_change_requests` in Postgres (R4-D7); carries ACL and reclassification changes only |
| `GET /v1/admin/acl-changes/{request_id}` | `tenant_admin` | none | `{status: pending or applied or failed, applied_at}` |
| `DELETE /v1/admin/documents/{id}`, `DELETE /v1/admin/advisors/{id}`, `GET /v1/admin/deletion-requests/{request_id}` | `tenant_admin` | none | 202 `{request_id}` or status and receipt; contract in §6.9 (a `deletion_requests` row is written directly, no `acl_change_requests`) |
| `GET /healthz` | none | none | liveness (process up) |
| `GET /readyz` | none | none | readiness: DB reachable and role flags / FORCE RLS / pgvector >= 0.8 asserted, Kafka reachable (degraded, not failing, for chat), model availability (configured models not retired or soon-retiring), firebase-admin verifier initialised |

Error codes: `UNAUTHENTICATED` (401), `FORBIDDEN` (403), `INPUT_TOO_LONG` (413), `INPUT_BLOCKED` (Model Armor or guard), `GUARD_UNAVAILABLE` (screen failed closed), `WRONG_CELL` (421) and `TENANT_MOVED` (421) with a cell hint, `CELL_UNAVAILABLE` (503, §6.11), `ENTITLEMENT_CHANGED` (SSE error: an entitlement bump aborted an in-flight turn, ADR-033), `NOT_FOUND` (404), `RATE_LIMITED` (429, `Retry-After`, from Kong or per-tenant budget), `TENANT_BUDGET_EXCEEDED`, `NO_FIRM_DOCUMENTATION` and `ANSWER_WITHHELD` with a `reason` (refusal events, not HTTP errors), `LLM_UNAVAILABLE`, `RETRIEVAL_UNAVAILABLE`, `TURN_INTERRUPTED`, `IDEMPOTENCY_KEY_REUSED`, `INTERNAL`. Numeric limits (input cap, budgets, rate limits) are config values (§6.6).

### 6.2 SSE event contract

`Content-Type: text/event-stream`. Each event has `id: <seq>` (integer, strictly increasing within a turn, persisted in `turn_events`), `event: <name>` and a JSON `data:`. The client reconnects with `Last-Event-ID` to `GET /v1/chat/{turn_id}/events`; because the server persists events, a dropped connection loses nothing. The turn id is returned in the first event and is derived from the `Idempotency-Key`, so a retried `POST /v1/chat` with the same key and body is a replay, not a second generation. A heartbeat comment line is sent every `SSE_HEARTBEAT_S` (value set in E4). Cloud Run request timeout is 3600 s; Kong `read_timeout` 3,600,000 ms.

| Event | Data | Notes |
|---|---|---|
| `turn` | `{turn_id, conversation_id, message_id}` | `seq 0`, first event |
| `meta` | `{retrieval_degraded: bool, reason?: "rerank_timeout" or "rerank_429", as_of: date, as_of_source: "chip" or "parsed" or "today"}` | emitted once after rerank; `as_of` is the date applied to retrieval (§6.10); `true` means the rerank fell back to RRF order; also stored in `messages.retrieval_degraded` |
| `tool` | `{tool, status: "started" or "ok" or "error", tool_use_id}` | tool name and status only; never payloads, inputs or exception text (G-04) |
| `delta` | `{text}` | output after sentence-buffered PII redaction; the client appends |
| `citation` | `{index, chunk_id, source_title, regulatory_ref, jurisdiction, last_reviewed_at, stale: bool, excerpt}` | emitted by the server only, after the citation verifier accepts `[n]`; `excerpt` is redacted (G-16) |
| `refusal` | `{code: "NO_FIRM_DOCUMENTATION" or "ANSWER_WITHHELD", reason?: "numeric_ungrounded" or "footer_missing" or "as_of_violation" or "no_version_history", escalate_offer: bool}` | `NO_FIRM_DOCUMENTATION`: confidence gate failed, no LLM call was made. `ANSWER_WITHHELD`: a deterministic release check failed (ADR-036, ADR-027); a numeric refusal says "figure X not found in cited sources" and offers escalation. Reason names are fixed in E4 |
| `notice` | `{kind: "as_of" or "mixed_jurisdiction" or "known_pending" or "state", text}` | server-emitted, never model text: the `as_of` echo, the mixed-jurisdiction warning (US vs EU vs UK), the known-pending-amendment warning and the `superseded` / `revoked` state warning (ADR-036) |
| `footer` | `{licence_class, text}` | licence footer from `document_versions.attribution_text` for each cited licence class; a missing footer blocks release (ADR-036) |
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

Consumer rule: every pipeline consumer (`silver`, `contextualizer`, `indexer`, `eval-judge`) rejects a message whose `envelope.tenant_id` differs from the message key, or whose tenant is PUBLIC, to `dlq.v1` with a reason (D16.6). `bq-sink` accepts PUBLIC analytics events. FCA Handbook API content never enters Kafka or BigQuery (ADR-026), no erasure request travels on Kafka (ADR-029), and subject-bearing topics are delete-policy with retention 7 d and `segment.ms` 1 d, payloads limited to ids and `pseudonym_id` (ADR-029).

| Topic | Key | Schema / event types | Producer | Consumer group | Retention | Replay |
|---|---|---|---|---|---|---|
| `docs.bronze.v1` | `tenant_id` | `DocBronzeLanded` {document_id, bronze_uri, sha256, source, fetched_at, version_key, valid_from, source_class, licence_class (§6.8)} | `etl` job (Dagster bronze asset) | `cg.silver` | E5 | Dagster re-publishes for a partition; bronze is immutable |
| `docs.silver.v1` | `tenant_id` | `DocSilverReady` {document_id, silver_uri, chunk_count, parser_version, reject_count} | `fa-worker` role `silver` | `cg.contextualizer` | E5 | offset reset; idempotent via `processed_events` |
| `chunks.contextualized.v1` | `tenant_id` | `ChunksContextualized` {document_id, silver_uri, header_model, rules_extracted} | `fa-worker` role `contextualizer` | `cg.indexer` | E5 | offset reset |
| `chunks.indexed.v1` | `tenant_id` | `ChunksIndexed` {document_id, upserted, unchanged, deleted, embed_model, corpus_version} | `fa-worker` role `indexer` | `cg.bq-sink` | E5 | offset reset; re-embed = replay of `docs.bronze.v1` |
| `ingest.analytics.v1` | `tenant_id` (PUBLIC id) | `PublicIngestStage` {stage, document_id, counts} | `etl-public` job | `cg.bq-sink` | E5 | rerun the job |
| `acl.changes.v1` | `tenant_id` | `AclChangeRequested` {request_id, document_id, action, new ACL}, `AclChangeApplied` {request_id, acl_version}, `AdvisorEntitlementChanged` {advisor_id, entitlement_version} | `outbox-relay` (rows written by `admin` and by `acl-applier`) | `cg.bq-sink` (analytics and audit only; the `acl-applier` no longer consumes this topic, it polls `acl_change_requests`, R4-D7) | E5 | offset reset; applier is idempotent on `request_id` |
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
| `MODEL_ARMOR_TEMPLATE`, `MODEL_ARMOR_TIMEOUT_MS`, `MODEL_ARMOR_FAIL_OPEN` | required; timeout set from latency measured from the Cloud Run region (p99 plus margin), not 500 ms by default (ADR-036); `false` | `guardrails` |
| `TENANT_TOKEN_BUDGET`, `TENANT_MAX_CONCURRENCY` | 2,000,000 tokens per UTC day (counters in Postgres `tenant_usage`), 20 (ADR-025 R47) | `agent` |
| `SSE_HEARTBEAT_S`, `TURN_LEASE_S` | required; set in E4 | `agent` |
| `SSE_REPLAY_TTL_S` | 600; after it resume returns 410 `TURN_EXPIRED` (ADR-025 R49) | `agent` |
| `FACTSHEET_MAX_CHUNKS` | 8; E4 can change it (ADR-025 R43) | `retrieval` |
| `CONTEXTUAL_RETRIEVAL_ENABLED` | `false` (default OFF; confirmatory ablation arm 1, ADR-016 amended, ADR-037) | worker |
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
| `HOME_CELL`, `CELLS_JSON_URI`, `CELLS_REFRESH_S`, `CELLS_PUBLIC_KEY` | this cell's id; signed directory location (GCS) with a baked fallback; 60; verification key baked into the image (ADR-031; set in E13) | `principal`, SPA resolve |
| `BUDGET_ALERT_USD` | 180; total monthly alert guarding the $200 ceiling (R4-D16) | budget alert |
| `EVAL_BUDGET_USD` | required; caps eval runs; value set in E7 (ADR-037) | eval jobs |
| `CONNECTOR_OVERLAP_S`, `CONNECTOR_MASS_DELETE_ITEMS`, `CONNECTOR_MASS_DELETE_PCT`, `CONNECTOR_QUARANTINE_PAUSE_PCT` | 172800 (48 h), 5, 10, 5 (ADR-026, ADR-034) | connectors |
| `CONNECTOR_RATE_RPS_<SOURCE>` | per source: eCFR 1, EDGAR 2, CELLAR 1, legislation.gov.uk 1, FCA 1 (§6.7) | connectors |
| `SCAN_MODEL_ARMOR_QPM`, `SCAN_WINDOW_TOKENS`, `SCAN_MAX_BYTES` | 300 (of the shared 1,200 QPM), under 65,536 tokens, under 4 MB (ADR-036) | ingest scan |
| `QUOTE_CAP_WORDS` | 40 default for `publisher` licence class (role-policy output field, ADR-036) | `guardrails` |
| `RECONCILE_MIN_IDLE_MIN`, `ANN_SELFHIT_TICKET`, `ANN_SELFHIT_PAGE` | 30, 0.99, 0.95 (ADR-034) | `reconcile` |
| `ERASURE_BQ_MIN_AGE_MIN`, `ERASURE_BQ_BATCH_INTERVAL_MIN`, `BQ_MAX_TIME_TRAVEL_HOURS` | 30, 60 (one batched DML per hour), 48 (ADR-029) | `erasure-worker`, Terraform |
| `EMBED_BACKFILL_RATE_FRACTION` | 0.25 of the Voyage RPM (ADR-035) | `embed-backfill` |

### 6.7 Connector contract (ADR-026, R4-D1, R4-D2)

One interface for every source. Names of the four methods are fixed by the decision; the field lists below are the contract the connectors and the E11 tickets implement. Connectors run against recorded fixtures (VCR) in PR; live source smoke runs weekly (§7.4).

```python
class Connector(Protocol):
    source_id: str
    source_class: Literal["law", "qa", "fca_api", "publisher"]   # on_withdraw: retire, retire, erase, erase
    def list(self) -> list[ListingItem]: ...                      # full listing: the truth for deletes
    def changes(self, cursor: dict) -> list[Observation]: ...     # feed or poll: only an accelerator
    def fetch(self, item: ListingItem) -> bytes: ...
    def classify(self, item: ListingItem) -> Classification: ...
```

| Type | Fields |
|---|---|
| `ListingItem` | `external_id`, `version_key` (the SOURCE's version key, never arrival time), `source_ts`, `locator` |
| `Observation` | `source_id`, `external_id`, `version_key`, `content_sha256`, `source_ts`, `observed_at` (DB clock), `state` in (`present`, `revoked`, `withdrawn`, `pending`) |
| `Classification` | `jurisdiction`, `tier`, `licence_class`, `language`, `authoritative` (bool), `attribution_text`, `valid_from`, `valid_from_basis` in (`source`, `observed`) |

`licence_class` values (gate what may be quoted, §8.8): `us_gov`, `eu_consolidated_ccby`, `esma_transformed`, `ogl`, `ogl_fca`, `publisher`.

Rules every connector obeys (ADR-026):
- Idempotent on `(source_id, external_id, version_key, content_sha256)`. Same bytes again is a no-op. Same `version_key` with new bytes is a `silent_edit` event, a new `document_versions` row with a new system-time range, and an alert.
- Every incremental read starts at `cursor - 48 h`; the cursor and overlap live in `source_state(source_id, cursor jsonb, overlap_s, last_listing_at)`, updated in the same transaction as the observations it covers.
- Withdrawal needs two consecutive listings that omit the item. A listing that drops more than 5 items or more than 10% of a source, or returns 0 items, applies nothing, freezes the connector and pages.
- Source class decides withdrawal: `law` and `qa` are RETIRED (`valid_to` set, text kept for as-of); `fca_api` and `publisher` are ERASED (§6.9). `pending` (legislation.gov.uk "known change, not yet applied") is stored as `status = 'known_pending'` on the provision; retrieval is unaffected and the compliance check adds a warning.
- The connector suspends on HTTP 401 or 403 (FCA revocation) and an operator runs `purge_source('fca_api')` (§6.9).
- A response that is 200 with an HTML error page fails the contract (§6.8) and is quarantined, never indexed.

| Source | Incremental | Delete or revoke signal | Backstop listing | Cadence |
|---|---|---|---|---|
| eCFR | `titles.json` `up_to_date_as_of` advances, then diff `versions/title-17.json?part=275` | `removed: true` = retire; `substantive: false` = metadata only | full versions list each run | daily |
| EDGAR 497K | per-CIK submissions (new accession), daily index | none per filing | Saturday full index vs last week's set; a missing accession is a `withdrawn` candidate | daily and weekly |
| SEC RR datasets | quarterly zip (82 MB) | none | quarterly | quarterly |
| EUR-Lex CELLAR | SPARQL `cdm:lastModificationDate` poll for the acts | in-force flag, end-of-validity date, repeals | list all consolidated CELEX per act | daily |
| legislation.gov.uk | `/update` publication log filtered to the three eur items | title "(revoked)", status | `hasVersion` list per item | daily |
| ESMA / JC Q&A (optional) | news page diff and PDF hash | "Deleted" in the changes overview, curated `withdrawals.yaml` in the repo, human reviewed | weekly hash | weekly |
| FCA Handbook API | weekly poll of listed modules by hash or last-modified | 401 or 403, or a revocation notice, triggers `purge_source` | module list | weekly, plus a manual monthly email check |
| Publisher documents | none (manual fetch) | operator `erase` | none | on demand |

Evidence for sources, limits and licence texts: ADR-026 (eCFR https://www.ecfr.gov/api/versioner/v1 ; EUR-Lex https://eur-lex.europa.eu/content/legal-notice/legal-notice.html ; FCA https://handbook.fca.org.uk/footer-widget/terms-and-conditions ; SEC https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).

### 6.8 `source_observations` and bronze contract (ADR-026, ADR-034)

`source_observations` is append-only. Columns: `source_id`, `external_id`, `version_key`, `content_sha256`, `source_ts`, `observed_at`, `state`. Unique on `(source_id, external_id, version_key, content_sha256)`. Table DDL is in §5.9 (`source_registry` holds `source_class`, `on_withdraw`, cursor and the `frozen` flag).

Bronze (GCS):
- Immutable and content-addressed by `content_sha256`; every object carries `sha256` in its object metadata (the source-to-bronze reconcile compares it with the observation). Exact object layout is set in E11.
- Publisher documents (`private_demo`) go to the private bucket of the firm tenant only, never to the public repo or a public eval set (K-R4-3). Public sources go to the PUBLIC tenant.
- Quarantined bytes live under `quarantine/`, never in silver. Silver is per document: `silver/tenant_id=/doc_id=/version=`.
- `DocBronzeLanded` (§6.4) carries `version_key`, `valid_from`, `source_class` and `licence_class` in addition to its current fields (E11 fixes the schema).

Contracts and blocking rules. A failure sets the version to `quarantined` and nothing is indexed; the indexer's atomic gate (ADR-028) is the control and Dagster checks are advisory.

| Layer | Contract |
|---|---|
| Events | Pydantic models to JSON Schema in Schema Registry, BACKWARD compatibility, CI check (ADR-013) |
| Silver | Pandera 0.35.0 with `PANDERA_VALIDATION_DEPTH=SCHEMA_AND_DATA` set explicitly (a LazyFrame validates schema only by default; polars >= 1.20.0); a planted bad row must fail in CI |
| Gold | dbt `contract: enforced` on gold tables (tables only, not views or snapshots) |
| Blocking rules | `licence_class` and `attribution_text` non-null; jurisdiction and tier non-null; eCFR part has the expected section ids; every CELEX arrives with all three languages or none; every 497K has a recognisable fee table or is `parse_incomplete`; chunk token bounds; no empty `provision_path`; ingest scan passed (§8.1) |
| Batch circuit | more than 5% of a batch quarantined pauses the connector |
| Quarantine | version `status = quarantined`; operator `release` or `reject` is recorded; compliance officers see a summary, never raw quarantined text (§8.8) |

Chunk identity includes `valid_from` and `parser_version`, so a replay after a parser fix re-parses (same bytes is not a no-op) and A-B-A text is representable (ADR-027).

### 6.9 Deletion API, receipts and the kill switch (ADR-029, ADR-030, ADR-028)

Deletes go through a Postgres queue (`deletion_requests`, polled by `erasure-worker` with `FOR UPDATE SKIP LOCKED`); Kafka is not on the delete path. `acl_change_requests` carries ACL and reclassification changes only (R4-D17).

| Method and path | Auth / role | Request | Response |
|---|---|---|---|
| `DELETE /v1/admin/documents/{id}` | `tenant_admin` | none | 202 `{request_id}`; writes a `deletion_requests` row directly (scope `document`, `subject_ref` = the document's `doc_key`, reason `erasure` or `takedown`; INSERT is granted to `fa_app` for `tenant_admin` only, §5.13); it does not go through `acl_change_requests`. 404 `NOT_FOUND` for an id outside the caller's tenant |
| `DELETE /v1/admin/advisors/{id}` (subject erasure; the decision names the endpoint but not its path, so this path is set by this section and ratified in E12) | `tenant_admin` | none | 202 `{request_id}`; one `deletion_requests` row (scope `advisor`, `subject_ref` = the advisor's `pseudonym_id`); the `pseudonym_id` mapping is deleted at once, so surviving analytics rows are unlinked while physical deletion runs inside the store windows |
| `GET /v1/admin/deletion-requests/{request_id}` (status and receipt read; path set by this section, ratified in E12) | `tenant_admin` | none | `{status, phase, steps[], receipt_uri?}`; `status` is the `deletion_requests.status` column of §5.11: `pending`, `running`, `executed`, `windows_open`, `closed`, `failed`; `phase` 1 or 2 from `erasure_receipts`; `steps` from `erasure_steps`; `receipt_uri` = the receipt's GCS URI |

Lifecycle: `executed` = receipt phase 1 (hours); `windows_open` = waiting for store windows; `closed` = receipt phase 2 `windows_closed` (9 to 14 days). Ledger key is `(tenant_id, doc_key, sha256)`; an operator `release` action (`released_at`) allows a legitimate re-ingest. Every sink guards writes with an uncached point read of the ledger (ADR-028). Lock order for publish and erasure: per-document advisory lock first, tenant `corpus_version` row last, one document per transaction.

Kill switch (not an HTTP endpoint): `purge_source('fca_api')` is an operator command. It runs as the PUBLIC owner role, bumps `source_epoch` (cache invalidation) and fans out one `deletion_requests` row per firm tenant (scope `source`, `parent_request_id` set; §4.20), each executed under that tenant's own role, for messages and cached answers that quote FCA text. There is no cross-tenant role (ADR-002 D13a stands). Drilled quarterly.

Receipt (JSON, stored in GCS, hash recorded in the ledger). Stored as `erasure_receipts.receipt` (§5.11); the per-store field set derives from `erasure_steps` (`status`, `executed_at`, `rows_affected`, `probe_result`, `window_closes_at`); names of the envelope fields are set in E12.

```json
{
  "request_id": "uuid",
  "tenant_id": "uuid",
  "scope_type": "document | advisor | source | tenant",
  "subject_ref_hash": "salted sha256, never the id",
  "requested_at": "2026-11-02T10:00:00Z",
  "phase": 1,
  "steps": [
    {"store": "postgres", "status": "done", "executed_at": "...", "rows_affected": 214,
     "probe_result": "count=0", "window": "live, 24 h", "window_kind": "observed"},
    {"store": "bigquery", "status": "done", "rows_affected": 31,
     "probe_result": "count=0 now; time-travel probe pending", "window": "48 h time travel + 7 d fail-safe",
     "window_kind": "documented", "window_closes_at": "..."},
    {"store": "langfuse", "status": "pending", "window": "provider best effort", "window_kind": "provider"}
  ],
  "retained": [{"what": "escalations", "legal_basis": "retention_class X"}],
  "windows_closed_at": null,
  "ledger_hash": "sha256",
  "signature": {"alg": "HMAC (KMS key)", "key_id": "..."}
}
```

Rules: phase 1 lists executed steps and carries no signature claim of "erased everywhere"; phase 2 (`windows_closed`) is issued by `erasure-verify` only after each store's window timer and probe, then signed with an HMAC using a KMS key. Observable stores get a probe result; the BigQuery fail-safe, Cloud SQL PITR logs and provider retention are marked `documented` or `provider`, not measured. If Langfuse does not honour a delete, the step retries, an alert fires at 24 h and the receipt stays phase 1. Records under legal hold appear in `retained` with the legal basis. A receipt is issued once per request (idempotent after a Kafka or BigQuery outage).

### 6.10 `as_of` parameter and echo (ADR-027)

- Request: `POST /v1/chat` accepts an optional `as_of` (ISO date) set by the UI chip. Resolution order (§4.18): an explicit date or year found in the question by the deterministic parser; else the chip; else the Postgres `current_date` in UTC. The model never sets `as_of` and no tool accepts it. Ambiguous numeric formats such as `03/04/2024` need a locale rule, decided in E11 (§10).
- Response: `meta` carries `as_of` and `as_of_source` (`chip`, `parsed`, `today`); the server emits a `notice {kind: "as_of"}` event so the answer states the parsed date (not model text). The same date is stored on the message and goes into the answer cache key (§5.7).
- Enforcement: every retrieval SQL carries `valid_range @> :as_of` (CI checks it); after generation every cited chunk must satisfy it or the release is blocked. Ranges are half-open.
- UK sources refuse a date before the first observation: `refusal {code: "ANSWER_WITHHELD", reason: "no_version_history"}`.

### 6.11 Cells directory, wrong-cell response and `cells.json` (ADR-031, ADR-033)

`cells.json` is signed and stored in GCS with a baked fallback in the image; each cell refreshes it every 60 s (`CELLS_REFRESH_S`). There is no control-plane database. The named fields per tenant (slug, `tenant_id`, `idp_tenant_id`, `home_cell`, `residency_class`, endpoints; §4.24) are fixed by ADR-031; the remaining fields below are set in E13.

```json
{
  "schema_version": 1,
  "version": 42,
  "issued_at": "2026-11-02T10:00:00Z",
  "cells": [
    {"cell_id": "us", "region": "us-central1", "api_endpoint": "https://us.api.example", "deployed": true},
    {"cell_id": "eu", "region": "europe-west3", "api_endpoint": "https://eu.api.example", "deployed": false}
  ],
  "tenants": [
    {"slug": "alpha", "tenant_id": "uuid", "idp_tenant_id": "...", "home_cell": "us", "residency_class": "none", "state": "active"},
    {"slug": "beta", "tenant_id": "uuid", "idp_tenant_id": "...", "home_cell": "eu", "residency_class": "eu_only", "state": "active"}
  ],
  "signature": {"alg": "set in E13", "key_id": "...", "value": "base64"}
}
```

- `residency_class` in (`none`, `eu_only`, `uk_only`). `state` in (`active`, `moved`). A higher `version` replaces a lower one atomically; a cell never applies an older version.
- Unreadable or badly signed file: the last good copy, then the baked fallback.
- `GET /resolve?slug=` (public, rate limited by IP, served from the same signed file by a Kong route or edge function; set in E13) returns `{cell_id, api_endpoint}`. The SPA then talks to the per-cell hostname.
- Wrong cell: `principal` (§4.5) checks `home_cell == this cell` and returns before any database read (the tenant's `tenants.cell_id` equals the directory entry, §5.12): HTTP 421 with `{"error": {"code": "WRONG_CELL", "message", "request_id", "retryable": false}, "cell_hint": {"cell_id", "api_endpoint"}}`. A tenant whose `state` is `moved` gets 421 `TENANT_MOVED` with the new cell hint. Code names are proposed here and fixed in E13.
- Cell down: the router or ALB answers 503 `CELL_UNAVAILABLE` for that cell's tenants only; there is no cross-cell failover and no fallback to another cell.
- Provider outage in any cell returns `LLM_UNAVAILABLE`, not a cell failure (ADR-038).
- Token and URL: the server verifies the ID token at project level, reads `firebase.tenant` and requires it to equal the tenant in the URL and the `cells.json` entry (ADR-032); a mismatch is 403 or 421.
