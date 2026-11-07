# FinAdvisor as-built map: backend app and agent (Explore, 2026-11-01)

Paths relative to /Users/keshav/Projects/FinAdvisor/backend. "inferred" = not read directly. Tests not run.

## 1. App and endpoints
- Entry `src/main.py:162` `app = create_app()`; create_app 78-91 mounts api_router at /api. Dockerfile: `uvicorn src.main:app --host 0.0.0.0 --port 8000` (Dockerfile:14). CLI `finadvisor = src.cli:main` starts compose, postgres, backend, frontend (src/cli.py:289).
- Lifespan (main.py:29-75) puts on app.state: Settings, async sessionmaker, VoyageEmbeddings, PII redactor, anthropic.AsyncAnthropic, Langfuse (only if both keys).
- Middleware: RequestContextMiddleware (observability/logging.py:43), http logging (main.py:126); exception handlers main.py:84-85.
- `GET /api/health` → {"status":"ok"}, no auth (api/health.py:11-13). `GET /api/me` → UserClaims (16-18).
- `POST /api/chat/stream` (api/chat.py:23-43): body ChatRequest{message, conversation_id?} (api/schemas.py:8-10); header X-User-Id; EventSourceResponse; conversation_id only logged (chat.py:34) — no memory.
- SSE events (chat.py:46-87): `message` {"type":"text","content":<PII-redacted>}; `tool` {tool,input,tool_use_id}; `tool_result` {content:<raw tool JSON, NOT redacted>}; `citation` (CitationEvent); `error` {message}; final `done` {}.
- Not token streaming: messages.create without stream; whole final text in one event (agent/orchestrator.py:72,150).
- Unused schemas ChatResponse, Citation(is_stale) (api/schemas.py:13-26). Kong audit target /api/audit/kong does not exist.

## 2. Auth
- No JWT. auth/jwt.py:9-13 reads X-User-Id, looks up hard-coded MOCK_USERS, 401 if unknown. jwt_secret (config.py:37) unused; python-jose dependency unused.
- UserClaims (auth/models.py:6-12): sub, name, tier, tier_level, jurisdictions (bare list[str]), licenses.
- Mock users (auth/mock_users.py:5-38): sarah_chen senior T3 US (Series-7, 66); alex_kim associate T1 EU (MiFID-II); james_wright private_wealth T4 UK (FCA); priya_sharma advisor T2 US+EU (Series-7, MiFID-II).
- No role checks beyond tier; AuthorizationError (403) never raised.
- Identity → DB: get_agent → get_rls_session → set_rls_context (dependencies.py:33-38,57); db/rls.py:9-17 `SET ROLE finadvisor_app`, `SET app.user_tier`, `SET app.user_jurisdictions` (f-string). Session-level SET, not SET LOCAL; reset_rls_context (rls.py:20) never called.

## 3. Orchestrator (src/agent/orchestrator.py)
- FinAdvisorAgent.run(query, user, max_iterations=5) async generator (36-157). Single-turn messages (60), no history.
- Each iteration: client.messages.create(model, max_tokens=4096, system, messages, tools) (72-78), non-streaming, no timeout/retry in code (SDK defaults).
- tool_use → yields tool_call, runs tools sequentially, yields tool_result, appends (92-138); else joins text → one text event (140-151); after 5 iterations error event (153-157).
- DEFAULT_MODEL claude-sonnet-4-20250514, MAX_TOKENS 4096 (18-19) — not in Settings.
- Gateway (main.py:45-51): default AsyncAnthropic(base_url=f"{KONG_URL}/v1", api_key=LITELLM_MASTER_KEY); if LLM_BASE_URL set → direct with ANTHROPIC_API_KEY.
- Tools: Anthropic native schemas from ToolRegistry.to_anthropic_schema() (tools/__init__.py:43); Pydantic model_validate (60); results model_dump_json (91).
- Tool errors → f'{{"error": "{exc!s}"}}' (orchestrator.py:117-123) — unescaped, invalid JSON on quotes, leaks exception text.
- Citations: NOT built in code. CitationEvent (agent/types.py:14) + SSE branch exist; orchestrator never yields citation. Only LLM [N] text per system prompt (agent/system_prompt.py:10-27). Stale warning is a prompt instruction only.
- Compliance escalation only LLM-triggered via tool (system_prompt.py:16-17).
- SYSTEM_PROMPT_VERSION 1.0.0 (system_prompt.py:3); tries Langfuse prompt `finadvisor-system` label production first (orchestrator.py:62; tracing.py:74-90).

## 4. Tools (registry agent/tools/__init__.py:21-93, if/elif dispatch 65-89)
- search_firm_kb (tools/search_kb.py): query, top_k=5 le=10 (no ge); embed_query → VectorStore.similarity_search; returns results[chunk_id, content, source_title, regulatory_ref, last_reviewed_at, similarity_score], total_found. SQL (retrieval/vector_store.py:22-31) ORDER BY embedding <=> vec LIMIT top_k — no WHERE; relies entirely on RLS.
- lookup_suitability_rule (tools/lookup_suitability.py): product_category, client_risk_profile free strings; SQL 60-70 on suitability_rules with jurisdiction/tier WHERE.
- lookup_product_factsheet (tools/lookup_factsheet.py): product_name; ILIKE %name% unescaped, no LIMIT (54-65); returns full raw_content (83).
- escalate_to_compliance (tools/escalate.py): reason, product_class, advisor_licenses (from LLM, not user.licenses); EscalationRecord id ESC-{sub}-{unix_ts} (collides within a second); only log.warning (64-71) — not persisted or notified.

## 5. Configuration (config.py:6-37, env_file .env)
| Env | Default | Used |
|---|---|---|
| ANTHROPIC_API_KEY | "" | only with LLM_BASE_URL |
| OPENAI_API_KEY, GOOGLE_API_KEY | "" | not in backend |
| LITELLM_MASTER_KEY | [dev key, redacted] | LLM key via Kong |
| VOYAGE_API_KEY | "" | yes |
| DATABASE_URL | postgresql+asyncpg://finadvisor:localdev@localhost:5432/finadvisor | yes |
| PII_MODE | regex | dlp+GCP_PROJECT_ID → DLP (pii/__init__.py:9) |
| GCP_PROJECT_ID | "" | DLP |
| KONG_URL | http://localhost:8001 | yes |
| LLM_BASE_URL | "" | bypass Kong |
| LANGFUSE_HOST/PUBLIC/SECRET | localhost:3030/""/"" | yes |
| JWT_SECRET | [dev secret, redacted] | unused |
- Hard-coded: max_iterations 5, MAX_TOKENS 4096, DEFAULT_MODEL (orchestrator.py:18-41); pool_size 5, max_overflow 10 (db/session.py:12-13); voyage-3, 1024, batch 128, MAX_RETRIES 3, BASE_DELAY 1.0, RATE_LIMIT_RPS 3 (retrieval/embeddings.py:11-16); model log line main.py:40; Langfuse prompt name/label (tracing.py:77-78); DLP info types, min_likelihood (pii/redactor.py:26-45); mock users; role finadvisor_app (db/rls.py:11).
- Dev secret defaults in code → silent fallback if env missing (config.py:13,37).

## 6. Errors, logging, tracing, health
- errors.py: FinAdvisorError → AuthorizationError 403, RetrievalError 502, ToolExecutionError 500, EvalThresholdError — never raised in src. Generic Exception handler 500 (main.py:111-123).
- Exceptions inside the SSE generator are not caught (chat.py:37-41) → client gets no error event (inferred).
- structlog JSON stdout, contextvars request_id/user_id (observability/logging.py:11-52); request_id from X-Request-Id or uuid4. user_id from unauthenticated header (main.py:131). Raw query logged (search_kb.py:47), escalation reason logged (escalate.py:64-71). DB URL creds stripped in log (main.py:37).
- Langfuse v2 API: trace finadvisor_query (orchestrator.py:43-51), generation per iteration (66-80), span per tool (106-125). Not wrapped in try/except (inferred: Langfuse failure breaks agent). get_prompt is a sync network call per request (orchestrator.py:62). Full messages and tool outputs sent to Langfuse unredacted.
- Health: static /api/health only; no readiness (DB/LLM/Voyage/Langfuse), no metrics.

## 7. Tests (17 files, ~123 test functions, asyncio_mode auto)
- CI: ruff check, ruff format --check, mypy src/, pytest tests/ -v.
- conftest: TEST_DATABASE_URL hard-coded to dev DB finadvisor:localdev (line 16); requires_db skip if no Postgres; seeded_session inserts 11 docs/chunks with [0.1]*1024 and re-applies RLS inline; test_client httpx ASGITransport.
- Unit (mocked): test_agent, test_chat_stream, test_tool_registry, test_escalate, test_pii, test_logging, test_tracing, test_auth, test_eval_runner, parts of test_search_kb; test_embeddings skipped without Voyage key. test_fallback_chain mocks messages.create only (no real fallback).
- DB-dependent: test_rls, test_rls_context, test_rls_e2e, test_lookup_factsheet, test_lookup_suitability, integration parts of test_search_kb; test_integration (requires_db unconfirmed).
- Gaps: no citation event tests; no timeout/latency tests; no concurrent RLS pool-reuse test; no live Kong/LiteLLM/Langfuse tests; no oversized/malicious input tests; no readiness tests; DLP only mocked.

## 8. Production gaps
- Spoofable X-User-Id auth, hard-coded users (auth/jwt.py:10-12).
- RLS session-scoped SET on pooled connections, no SET LOCAL/reset (db/rls.py:11-17).
- RLS only on chunks; documents/suitability_rules app-filtered.
- Vector search has no app-level filter (vector_store.py:23-30).
- Voyage sync SDK via to_thread, input_type document for queries, ~3 RPS per process, no timeout (embeddings.py:23-48).
- Anthropic call no explicit timeout/retry; no overall turn deadline.
- No model output streaming.
- Mid-stream exceptions uncaught.
- Tool error JSON by string interpolation.
- Citations/staleness/compliance flags not implemented in code.
- Escalation not persisted, trusts LLM licenses.
- ChatRequest.message no length limit; conversation_id unused.
- tool and tool_result SSE events unredacted; regex PII US-centric and loose; DLP sync call in async path; DLP redactor typed as RegexRedactor (dependencies.py:45).
- Langfuse not isolated; sync get_prompt per request; unredacted data to Langfuse.
- Logs carry raw queries and unauthenticated user id.
- No readiness/DB checks.
- Dockerfile root, `pip install -e .` ignores poetry.lock (unpinned >=), single uvicorn process, no HEALTHCHECK.
- Global app singleton at import; structlog cache_logger_on_first_use.
- Voyage has no fallback (SPOF); Kong rate-limit local + spoofable header.
- factsheet ILIKE no cap, returns whole documents; top_k no ge=1.
