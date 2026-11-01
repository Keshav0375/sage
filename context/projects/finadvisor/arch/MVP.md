# FinAdvisor MVP: as-built baseline

## 0. Status

As-built baseline, mapped 2026-11-01 from commit d6c2bd3. Describes the code, not the docs.

All paths are relative to the FinAdvisor repo root (`/Users/keshav/Projects/FinAdvisor`). `DC` = `docker-compose.yml`, `OV` = `docker-compose.override.yml`. Evidence comes from four mapper reports and one verification report (skeptic re-read plus vendor docs), plus spot-checks made while writing this file (every `file:line` quoted here was re-read at d6c2bd3). Nothing was run end to end: no tests, no containers, no Terraform. Statements marked "inferred" were not confirmed by execution.

Things this run checked by execution, not only by reading:
- Regex PII patterns (`backend/src/pii/fallback.py:24-29`) run on sample strings: they over-match plain numbers (section 13, G-37).
- `langfuse==4.6.1` (the version in `poetry.lock`, also installed in the repo's local `.venv`) was installed into a scratch folder: the `Langfuse` client class has no `trace()`, `generation()` or `span()` method, which `backend/src/observability/tracing.py` calls (G-15).
- `backend/scripts/ingest.py:198` `.replace("/finadvisor", "/finadvisor_test")` run on the default `DATABASE_URL`: it also rewrites the user name (G-06).
- Kong `rate-limiting` parameter list read from https://developer.konghq.com/plugins/rate-limiting/reference/ : no `identifier` parameter (G-14).

### Doc vs code

Where README.md, architecture.md, mvp.md, TODO.md or docs/threat_model.md claim something the code does not do:

| Doc claim | Code reality | Evidence |
|---|---|---|
| Signed JWT verified on every request (mvp.md:83, mvp.md:92-103; README.md:40; architecture.md:205, :400) | Plain `X-User-Id` header looked up in a hard-coded dict; `jwt_secret` and `python-jose` unused | `backend/src/auth/jwt.py:9-13`, `backend/src/config.py:37` |
| Cloud SQL has no public IP (docs/threat_model.md:122) | `ipv4_enabled = true` on both instances | `terraform/cloud_sql.tf:20-22`, `:64-66` |
| Kong is the only public entry; LangFuse internal-only; Cloud Run services use internal URLs (docs/threat_model.md:120-122) | `allUsers` run.invoker on backend and frontend; Langfuse has no IAM binding listed | `terraform/iam.tf:35-49` |
| Client name and account number redacted before they hit the LLM (mvp.md:40) | The user message goes to Anthropic, Voyage and Langfuse unredacted; only the final LLM text is regex-redacted | `backend/src/agent/orchestrator.py:60`, `backend/src/api/chat.py:38-52` |
| Output redaction on every SSE text event (docs/threat_model.md:46) | Only the `message` text event is redacted; `tool`, `tool_result`, `error` are not | `backend/src/api/chat.py:46-82` |
| Redacted text uses `[REDACTED]` markers (docs/threat_model.md:39) / `[CLIENT_NAME_1]` tokens (mvp.md:40, architecture.md:854) | Regex mode writes `[SSN_REDACTED]`, `[PHONE_REDACTED]`, `[EMAIL_REDACTED]`, `[ACCOUNT_REDACTED]`; DLP mode writes `[INFO_TYPE]` | `backend/src/pii/fallback.py:38`, `backend/src/pii/redactor.py:82` |
| Escalation tool "creates audit records" (docs/threat_model.md:90, :161) | A `log.warning` line only; nothing persisted or sent | `backend/src/agent/tools/escalate.py:64-71` |
| Citation viewer with hover and source chunk excerpt (mvp.md:139) | Backend never emits `citation` events; frontend badges are inert grey without them; panel shows title, ref, date only (no chunk text), on click | `backend/src/agent/orchestrator.py:97-151`, `frontend/src/components/CitationInline.tsx:19-23`, `frontend/src/components/CitationPanel.tsx:20-50` |
| Kong token-budget plugin and PII-guard plugin (mvp.md:124-126; architecture.md:208, :812) | Kong config has only rate-limiting, request-size-limiting and http-log | `kong/kong.yml:12-29` |
| Circuit breaker "3x 5xx in 60s, skip 5 minutes" (mvp.md:122) | `allowed_fails: 3`, `cooldown_time: 300` in LiteLLM; TODO.md:507 words it differently | `litellm/config.yaml:29-30` |
| Dependencies pinned in pyproject.toml (docs/threat_model.md:131) | All backend dependencies are `>=` floors; Dockerfile ignores `poetry.lock` | `backend/pyproject.toml:9-21`, `backend/Dockerfile:6-8` |
| LangFuse stores the versioned system prompt (docs/threat_model.md:78) | Only when both Langfuse keys are set; otherwise the in-code prompt `1.0.0` is used. Compose passes no Langfuse keys | `backend/src/agent/orchestrator.py:62-63`, `backend/src/main.py:53-68`, `DC:23-31` |
| `frontend/Dockerfile` exists (docs listing); compose and Terraform build/deploy it | No `frontend/Dockerfile` in the repo | `DC:39`, `terraform/cloud_run.tf:141` |
| "Server Components by default" (CLAUDE.md:64) | The one page is `"use client"` | `frontend/src/app/page.tsx:1` |
| README default path "connects directly to Anthropic API (no gateway needed)" (README.md:111) | True for the `finadvisor` CLI (sets `LLM_BASE_URL`); false for the compose stack (goes via Kong then LiteLLM) | `backend/src/cli.py:234`, `backend/src/main.py:45-46` |
| Chunk count 200-300 planned (per map-frontend-docs) | 114 chunks actual per docs/demo_script.md:9; not recomputed here | `docs/demo_script.md:9` |
| TODO.md reports the project "100% complete" | Docker, CI on a PR, `terraform validate`, live eval and live Kong/LiteLLM/Langfuse checks were all deferred | `TODO.md:277, :508, :763, :818, :847, :877` |
| A CI deploy preview is described (per map-frontend-docs) | No deploy job exists in either workflow | `.github/workflows/ci.yml`, `.github/workflows/eval-gate.yml` |

## 1. Product and scope

**Goal.** A "Compliance-Aware Wealth Advisor RAG Assistant" for a fictional firm, Meridian Wealth Partners: an advisor asks a question, the agent searches a synthetic firm knowledge base and answers with `[N]` citations, filtered by the advisor's tier and jurisdiction (README.md:3-5, mvp.md:5-11, mvp.md:52). Status per the docs: a private interview/demonstration project (README.md:212, mvp.md:174-182). Never deployed.

**Not stated anywhere in the repo:** user count, QPS, latency target, SLO, LLM cost budget, deadline. Keshav's numbers for later research are in section 14.

**Personas (4 mock users, hard-coded).** `backend/src/auth/mock_users.py:5-38`, duplicated in `data/seed/mock_users.json` and `frontend/src/lib/users.ts:10-43`.

| User id | Name | Tier (level) | Jurisdictions | Licenses | Chunks visible per TODO.md:341-342 |
|---|---|---|---|---|---|
| `sarah_chen` | Sarah Chen | senior (3) | US | Series-7, Series-66 | 43 |
| `alex_kim` | Alex Kim | associate (1) | EU | MiFID-II | 10 |
| `james_wright` | James Wright | private_wealth (4) | UK | FCA | 26 |
| `priya_sharma` | Priya Sharma | advisor (2) | US, EU | Series-7, MiFID-II | 55 |

Chunk counts are the figures recorded when the E2E RLS test last ran (TODO.md:341-342, `Story-Reports/3.3-rls-e2e-verification.md:8-11`); not re-run here.

**Compliance rules as encoded.**
- Visibility rule (the only enforced one): a chunk is visible when `tier_required <= user tier_level` AND `jurisdiction` is in the user's jurisdiction list (`backend/db/schema.sql:64-71`). Tier 4 sees all tiers (docs/threat_model.md:22-27).
- Rules that exist only as system-prompt text, enforced by nothing but the LLM (`backend/src/agent/system_prompt.py:10-20`): every claim cites `[N]`; say "I don't have firm documentation" if unsupported; use `escalate_to_compliance` for products outside the advisor's licenses; never fabricate regulatory refs; warn when a source was last reviewed more than 12 months ago.
- The stale badge in the UI uses `monthsAgo > 12` computed as days/30 (`frontend/src/components/StaleBadge.tsx:9-12`).
- License scope is never checked in code: `escalate_to_compliance` takes `advisor_licenses` from the LLM, not from `user.licenses` (`backend/src/agent/tools/escalate.py:16, 57`).
- Regimes named in the corpus and docs: FINRA, SEC, MSRB, MiFID II, FCA COBS (docs/threat_model.md:168). The regulation text is synthetic (CLAUDE.md:174).

**What is mock or synthetic.**
- Identity: 4 hard-coded users, no IdP (`backend/src/auth/jwt.py:9-13`).
- Corpus: 50 LLM-generated documents (`backend/scripts/generate_corpus.py`, model `claude-sonnet-4-20250514` at `:667` per map-data, not re-read), 20 product factsheets, 10 suitability rules, 10 compliance memos, 10 jurisdiction disclosures; 8 contain fake PII by design. Counts recomputed from `data/corpus/*/*.json`: US 22 docs, EU 15, UK 11, APAC 2; `last_reviewed_at` ranges 2023-06-15 to 2025-03-15; total 187,840 characters. About 114 chunks (docs/demo_script.md:9).
- Golden Q&A: 50 items in `data/eval/golden_qa.json` (suitability 15, jurisdiction 10, refusal 10, citation 10, stale 5, per map-data).
- Compliance escalation: log line only. Kong audit sink: route missing.

## 2. System context

```mermaid
flowchart LR
    advisor["Advisor browser"]
    subgraph sys["FinAdvisor"]
        next["Next.js frontend"]
        api["FastAPI backend"]
        pg[("Postgres + pgvector")]
        kong["Kong gateway"]
        litellm["LiteLLM proxy"]
        lf["Langfuse v2"]
        lfdb[("Langfuse Postgres")]
        redis[("Redis (unused)")]
    end
    anth["Anthropic API"]
    oai["OpenAI API"]
    gem["Gemini API"]
    voy["Voyage AI embeddings"]
    advisor -->|"HTTP, X-User-Id header"| next
    next -->|"rewrite /api/* to localhost:8000, SSE"| api
    api -->|"asyncpg, SET ROLE + RLS"| pg
    api -->|"Anthropic SDK, /v1/messages"| kong
    kong -->|"HTTP reverse proxy"| litellm
    litellm -->|"shuffle across 3"| anth
    litellm -->|"shuffle across 3"| oai
    litellm -->|"shuffle across 3"| gem
    api -.->|"LLM_BASE_URL bypass"| anth
    api -->|"HTTPS embed (sync SDK in thread)"| voy
    api -.->|"Langfuse SDK, only if keys set"| lf
    lf --> lfdb
```

Evidence: frontend rewrite `frontend/next.config.mjs:3-9`; DB `backend/src/dependencies.py:33-38`; LLM client `backend/src/main.py:45-51`; Kong route `kong/kong.yml:3-10`; LiteLLM models `litellm/config.yaml:1-21`; Voyage `backend/src/retrieval/embeddings.py:38-47`; Langfuse `backend/src/main.py:53-68`; Redis `DC:97-102` (no consumer anywhere in the configs read).

## 3. Containers and components

```mermaid
flowchart TB
    subgraph frontend["frontend (Next.js 14.2.35)"]
        ui["ChatWindow, useChat, api.ts"]
    end
    subgraph backend["backend (FastAPI, one process)"]
        api["api: /api/health, /api/me, /api/chat/stream"]
        auth["auth: X-User-Id lookup"]
        agent["agent: FinAdvisorAgent ReAct loop"]
        tools["tools: ToolRegistry, 4 tools"]
        retrieval["retrieval: VoyageEmbeddings, VectorStore"]
        pii["pii: RegexRedactor / PIIRedactor"]
        observability["observability: structlog, Langfuse tracing"]
        dbm["db: session pool, set_rls_context"]
    end
    subgraph gateway["gateway"]
        kong["Kong 3.9 DB-less"]
        litellm["LiteLLM main-latest"]
    end
    subgraph data["data"]
        pg[("Postgres 16 + pgvector")]
        redis[("Redis 7 unused")]
    end
    subgraph obs["observability"]
        lf["Langfuse 2"]
        lfdb[("Langfuse Postgres 16")]
    end
    ui -->|"POST /api/chat/stream, SSE"| api
    api --> auth
    api --> agent
    api --> pii
    auth --> dbm
    dbm -->|"asyncpg"| pg
    agent --> tools
    agent -->|"HTTP /v1/messages"| kong
    kong -->|"HTTP"| litellm
    tools --> retrieval
    tools --> dbm
    retrieval -->|"HTTPS Voyage"| ext["Voyage AI"]
    agent --> observability
    observability -.->|"HTTP, keys required"| lf
    lf --> lfdb
```

### 3.1 frontend
- Responsibility: single-page chat UI; user switcher; tool-call cards; markdown with `[N]` badges; sources panel; stale badge.
- Key files: `frontend/src/app/page.tsx:5-7`, `src/hooks/useChat.ts`, `src/lib/api.ts`, `src/lib/users.ts`, `src/components/*` (11 components), `frontend/next.config.mjs`.
- Behaviour: Next.js 14.2.35 App Router, one route, `"use client"` (`page.tsx:1`), no API routes, no middleware, no server components. Sends `POST /api/chat/stream` with header `X-User-Id` and body `{message, conversation_id?}` (`api.ts:12-22`); `conversation_id` is never passed (`useChat.ts:68`). `/api/*` is rewritten to `http://localhost:8000` at build time (`next.config.mjs:3-9`); `NEXT_PUBLIC_API_URL` set in compose and Terraform is not read by any source file (grep for `process.env` in `frontend/src` finds nothing). SSE is parsed by hand (`api.ts:35-53`): lines split on `\n`, the event name is cleared after one `data:` line, so multi-line `data:` is not supported. `eventsource-parser` is a dependency but unused. Handled events: `message` (only `type: "text"`), `tool`, `tool_result` (matched to the last running tool, not by id, `useChat.ts:108-113`), `citation`, `error`, `done`; `JSON.parse` is unguarded (`useChat.ts:70, 79, 120, 145`). Non-2xx gives a generic error (`api.ts:24-26`); no abort, timeout, 401 or 429 handling. Chat state is local `useState`; zustand holds only the selected user, persisted in `localStorage` key `finadvisor_user` (`hooks/useUser.ts:11, 22`); switching user does not clear the chat. Citation badges use `/\[(\d+)\]/g` (`lib/parseCitations.ts:13`) only inside `p` and `li` text nodes (`MarkdownContent.tsx:52-79`); without `citation` events the badges render grey and non-clickable (`CitationInline.tsx:19-23`). No tests, no test runner.

### 3.2 backend/api
- Responsibility: HTTP surface and SSE encoding.
- Key files: `backend/src/main.py`, `src/api/{chat,health,router,schemas}.py`, `src/errors.py`.
- Behaviour: `create_app()` mounts the router under `/api` (`main.py:78-91`); app object created at import (`main.py:162`). Lifespan builds on `app.state`: Settings, session factory, VoyageEmbeddings, redactor, `anthropic.AsyncAnthropic`, optional Langfuse (`main.py:29-75`). Middleware: `RequestContextMiddleware` (`observability/logging.py:43-52`) and an HTTP logging middleware (`main.py:126-159`). `FinAdvisorError` handler maps `AuthorizationError`->403, `RetrievalError`->502, `ToolExecutionError`->500 (`main.py:22-26`), but nothing in `src/` raises these (`errors.py:7-16`). Unhandled errors return a generic 500 JSON (`main.py:111-123`). The SSE generator has no try/except (`chat.py:37-41`), so an exception after the 200 header is sent drops the stream with no `error` event (skeptic claim 14). `ChatRequest.message` has no length limit (`api/schemas.py:8-10`). `ChatResponse` and `Citation` schemas are defined but unused (`schemas.py:13-26`).

### 3.3 backend/auth
- Responsibility: identity for every request.
- Key files: `src/auth/jwt.py:9-13`, `mock_users.py:5-38`, `models.py:6-12`.
- Behaviour: `get_current_user` reads `X-User-Id`; unknown or missing returns 401; otherwise `UserClaims(**MOCK_USERS[id])`. No token, no signature, no expiry. `jwt_secret` (`config.py:37`) and the `python-jose` dependency are unused. No role checks beyond tier; `AuthorizationError` never raised. `UserClaims.jurisdictions` is a bare `list[str]` (`models.py:11`).

### 3.4 backend/agent
- Responsibility: ReAct loop over Anthropic tool use.
- Key files: `src/agent/orchestrator.py`, `system_prompt.py`, `types.py`.
- Behaviour: `FinAdvisorAgent.run(query, user, max_iterations=5)` is an async generator (`orchestrator.py:36-157`). Single-turn: `messages = [{"role": "user", "content": query}]`, no history (`:60`). Per iteration it calls `client.messages.create(model, max_tokens=4096, system, messages, tools)` non-streaming, no explicit timeout or retry (`:72-78`). If `stop_reason == "tool_use"` it yields a `tool_call` event per `tool_use` block, runs tools one after another, yields `tool_result`, appends assistant and user turns (`:92-138`); text blocks that accompany tool use are dropped. Otherwise it joins text blocks and yields one `text` event (`:140-151`). After 5 iterations it yields an `error` event ("Max reasoning iterations reached...", `:153-157`). Tool exceptions become `f'{{"error": "{exc!s}"}}'` (`:117-123`): unescaped, so invalid JSON when the message contains quotes, and it echoes exception text to the LLM and to the client via `tool_result`. Model `claude-sonnet-4-20250514` and `MAX_TOKENS=4096` are constants, not Settings (`:18-19`). System prompt: tries Langfuse prompt `finadvisor-system` label `production` first (`:62`, `tracing.py:74-90`), else the in-code prompt `SYSTEM_PROMPT_VERSION = "1.0.0"` (`system_prompt.py:3`). The prompt does not tell the model the advisor's tier, jurisdictions or today's date. Citations are not built in code: `CitationEvent` exists (`types.py:14-18`) and the SSE encoder has a branch for it (`chat.py:72-76`), but the orchestrator never yields one. Langfuse calls (`start_trace` etc.) are not wrapped in try/except (`orchestrator.py:43-51, 66-80`; `tracing.py:15-30`).

### 3.5 backend/tools
- Responsibility: four tools exposed to the LLM; registry validates input with Pydantic and dispatches by name.
- Key files: `src/agent/tools/__init__.py:21-93`, `search_kb.py`, `lookup_suitability.py`, `lookup_factsheet.py`, `escalate.py`.
- Behaviour: details in section 6.3. Dispatch is an if/elif chain (`__init__.py:65-89`); results are `model_dump_json()` strings (`:91`). The registry is rebuilt per request with the request's DB session (`dependencies.py:63`).

### 3.6 backend/retrieval
- Responsibility: query/document embeddings and vector search.
- Key files: `src/retrieval/embeddings.py`, `vector_store.py`.
- Behaviour: `VoyageEmbeddings` uses the synchronous `voyageai.Client` inside `asyncio.to_thread` (`embeddings.py:21, 42-47`), model `voyage-3`, 1024 dims, batch 128, 3 retries with exponential backoff base 1 s on any exception, a semaphore of 3 and a 0.333 s sleep held inside the semaphore (`:11-16, 23-24, 38-71`); no request timeout. `embed_query` calls the same path with `input_type="document"` (`:34-47`). `VectorStore.similarity_search` runs `ORDER BY embedding <=> :vec LIMIT :top_k` with no WHERE clause and no score threshold; score = `1 - distance` (`vector_store.py:22-31`). Everything about who may see a chunk is left to RLS.

### 3.7 backend/pii
- Responsibility: redact PII on ingest and on LLM output text.
- Key files: `src/pii/__init__.py:8-11`, `fallback.py`, `redactor.py`.
- Behaviour: `create_redactor` returns the DLP redactor only if `PII_MODE == "dlp"` AND `GCP_PROJECT_ID` is set; anything else, including Terraform's `"gcp_dlp"` (`terraform/cloud_run.tf:94-97`), silently yields the regex redactor. Regex patterns: SSN, PHONE, EMAIL, ACCOUNT (`fallback.py:24-29`). DLP: 8 info types, `min_likelihood: LIKELY`, replace with info type, synchronous call, no retry (`redactor.py:26-62`). The FastAPI dependency types the redactor as `RegexRedactor` (`dependencies.py:45`). Redaction is applied to: documents at ingest (before chunking, `ingest.py:120-125`) and the `text` SSE event (`chat.py:47-52`). Not applied to: the user's message, tool inputs and outputs, `tool_result` events, `documents.raw_content`, Langfuse payloads, logs.

### 3.8 backend/observability
- Responsibility: logs and traces.
- Key files: `src/observability/logging.py`, `tracing.py`.
- Behaviour: see section 11.

### 3.9 backend/db
- Responsibility: engine, session, RLS context, ORM models.
- Key files: `src/db/session.py`, `rls.py`, `models.py`; `backend/db/schema.sql`.
- Behaviour: async engine, asyncpg, `pool_size=5`, `max_overflow=10`, `expire_on_commit=False`, no `pool_pre_ping`, recycle or statement timeout (`session.py:9-15`). One `AsyncSession` per request (`dependencies.py:27-30`). `set_rls_context` runs `SET ROLE finadvisor_app`, then `SET app.user_tier = '<int>'` and `SET app.user_jurisdictions = '<csv>'` via f-strings (`rls.py:9-17`); plain `SET`, not `SET LOCAL`; `reset_rls_context` only runs `RESET ROLE`, does not reset the two settings, and is never called (`rls.py:20-21`). No commit anywhere in `src/`; each request ends by rollback when the session closes, which also reverts the `SET` statements (verification.md, claim 2). SQLAlchemy ORM classes exist but only serve test `create_all`; runtime and ingest use raw `text()` SQL (`models.py`, per map-data).

### 3.10 gateway (Kong, LiteLLM)
- Kong `kong:3.9`, DB-less, config copied into the image (`kong/Dockerfile:1-10`). One service `llm-service` -> `http://litellm:4000`, route path `/v1`, `strip_path: false` (`kong/kong.yml:3-10`). Plugins: `rate-limiting` 60/min and 500/h, `policy: local`, `identifier: header`, `header_name: X-User-Id`; `request-size-limiting` `allowed_payload_size: 1`; `http-log` POST to `http://backend:8000/api/audit/kong` (`kong.yml:12-29`). No auth plugin, no CORS. See G-14 and G-48.
- LiteLLM `ghcr.io/berriai/litellm:main-latest` (`litellm/Dockerfile:1`); config in section 6.5.
- The backend does not send `X-User-Id` to Kong: the Anthropic client is created with only `api_key` and `base_url` (`main.py:47-50`).

### 3.11 data and observability stores
- Postgres `pgvector/pgvector:pg16` (`DC:3`), schema applied only on first init of the volume via initdb mount (`DC:10-12`) or by the CLI (`backend/src/cli.py:178-200`).
- Langfuse `langfuse/langfuse:2` with its own `postgres:16` (`DC:67-95`).
- Redis `redis:7-alpine` (`DC:97-102`): no consumer in any config read; `terraform/` has no Redis.

## 4. Key flows

### 4.a Chat request, end to end

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser (useChat)
    participant N as Next.js rewrite
    participant A as FastAPI /api/chat/stream
    participant D as Postgres (finadvisor_app role)
    participant L as Anthropic SDK -> Kong -> LiteLLM
    participant V as Voyage AI
    B->>N: POST /api/chat/stream, X-User-Id, {message}
    N->>A: proxy to localhost:8000
    A->>A: get_current_user: header lookup in MOCK_USERS (401 if unknown)
    A->>D: autobegin; SET ROLE finadvisor_app; SET app.user_tier; SET app.user_jurisdictions
    A->>A: build ToolRegistry(session) + FinAdvisorAgent
    A-->>B: 200 text/event-stream opened
    loop iteration 0..4 (max_iterations=5)
        A->>L: messages.create(model, max_tokens 4096, system, messages, 4 tools), non-streaming
        L-->>A: full response
        alt stop_reason == tool_use
            A-->>B: event: tool {tool, input, tool_use_id}
            A->>V: embed_query (search_firm_kb only)
            A->>D: SELECT ... (RLS applies to chunks)
            A-->>B: event: tool_result {content} (raw JSON, not redacted)
        else final answer
            A->>A: RegexRedactor.redact(text)
            A-->>B: event: message {"type":"text","content":redacted}
        end
    end
    A-->>B: event: error {message} (only if 5 iterations used up)
    A-->>B: event: done {}
    A->>D: session closes -> rollback (reverts SET ROLE and app.* settings)
```

Evidence by step: header auth `backend/src/auth/jwt.py:9-13`; RLS context `backend/src/dependencies.py:33-38, 57-68` and `backend/src/db/rls.py:9-17`; loop `backend/src/agent/orchestrator.py:65-157`; encoder `backend/src/api/chat.py:46-87`; `done` event `chat.py:41`.

**SSE event contract as built** (`backend/src/api/chat.py:46-87`, `backend/src/agent/types.py:21-25`):

| SSE event name | Data payload | Redacted? | Emitted by real agent? |
|---|---|---|---|
| `message` | `{"type":"text","content":<final answer>}` | Yes, regex or DLP (`chat.py:47-52`) | Yes, once per request, whole answer |
| `tool` | `{"tool","input","tool_use_id"}` | No (`chat.py:54-64`) | Yes, one per tool_use block |
| `tool_result` | `{"content":<raw tool JSON string>}` | No (`chat.py:66-70`); includes chunk text, full `raw_content` of factsheets, exception text | Yes, one per tool call |
| `citation` | `CitationEvent` JSON `{index, source_title, regulatory_ref, last_reviewed_at}` | No redaction code path | No: the orchestrator never yields it (`orchestrator.py:97-151`); only tests with a mocked agent produce it (`backend/tests/test_integration.py:17-47`) |
| `error` | `{"message":<fixed string>}` | No (`chat.py:78-82`) | Only the max-iterations message (`orchestrator.py:153-157`); exceptions produce no event |
| `done` | `{}` | n/a | Yes, after the generator finishes (`chat.py:41`) |
| fallback branch | `event: message`, `{"type":<type>,"content":...}` for any other type | No | Not reachable with current `StreamEvent` types (`chat.py:84-87`) |

Because the final text is a single event, the "split PII across events" concern in the maps does not occur today; it would if token streaming were added.

### 4.b Ingest

```mermaid
sequenceDiagram
    autonumber
    participant S as scripts/ingest.py
    participant C as data/corpus/*/NN_slug.json
    participant R as RegexRedactor or PIIRedactor
    participant V as Voyage (voyage-3)
    participant D as Postgres (as finadvisor)
    S->>C: rglob *.json (50 files)
    loop each document
        S->>R: redact(content)
        R-->>S: redacted text
        S->>S: chunk 2048 chars, overlap 200 (recursive split)
        S->>S: new uuid4 for document and each chunk
    end
    S->>S: cost estimate = words*1.3 /1e6 * 0.06
    S->>V: embed_texts(all chunks), batch 128, input_type=document
    V-->>S: 1024-d vectors
    S->>D: BEGIN; INSERT documents (raw_content UNREDACTED); INSERT chunks; COMMIT
    Note over S,D: plain INSERT, no unique key: re-run duplicates everything. suitability_rules never written.
```

Evidence: corpus load `backend/scripts/ingest.py:89-96`; redaction before chunking `:120-125`; chunker `:23-86` (overlap text is prepended after splitting, so a chunk can exceed 2048, `:78-84`); `raw_content` stored unredacted `:141`; uuid4 `:127, 149`; Voyage `:177-191`; single transaction `:203-228`; `--target test` `:196-198`; `_source_file` loaded `:94` but not stored. Only `documents` and `chunks` are written; chunks carry jurisdiction, tier, regulatory_ref, last_reviewed_at, source_title but not doc_type, product_category or risk_level (`:146-160`). The CLI avoids re-ingest by skipping when `chunks` already has rows (`backend/src/cli.py:206-211`); direct `ingest.py` runs do not.

### 4.c Eval gate in CI

```mermaid
sequenceDiagram
    autonumber
    participant GH as GitHub Actions (PR to main)
    participant J1 as job lint-and-test
    participant J2 as job eval-gate
    participant PG as pgvector service (test/test)
    participant API as uvicorn backend
    participant E as scripts/run_eval.py
    participant J as Anthropic judge
    GH->>J1: pip install -e ".[dev]" (dev extra does not exist)
    J1->>J1: ruff check, ruff format --check, mypy src/, pytest -x
    GH->>J2: needs lint-and-test
    J2->>PG: psql -f db/schema.sql
    J2->>J2: python scripts/ingest.py --target test (no VOYAGE_API_KEY, no DATABASE_URL in step env)
    J2->>API: uvicorn in background, sleep 5
    J2->>E: run_eval.py --api-base http://localhost:8000
    loop 50 golden questions
        E->>API: POST /api/chat/stream as mock user
        API-->>E: SSE events
        E->>J: judge prompt (faithfulness, citation_accuracy)
    end
    E-->>J2: eval_results.json
    J2->>J2: fail if avg_citation_accuracy < 0.95 or avg_faithfulness < 0.90
    J2->>GH: upload eval-results artifact
```

Evidence: `.github/workflows/eval-gate.yml:7-121`; judge model `backend/scripts/run_eval.py:23`; scoring thresholds also inside the script `run_eval.py:376-381`; the script talks to the backend directly with `X-User-Id` (`run_eval.py:49-55`) and calls Anthropic for judging with `ANTHROPIC_API_KEY` (`:194`). As written this job cannot reach the threshold step (G-05, G-06). It has never run on a PR (TODO.md:847).

## 5. Data model

Source: `backend/db/schema.sql` (raw SQL, no migrations, no version table). Extensions `vector`, `pgcrypto` (`:6-7`).

```mermaid
erDiagram
    documents ||--o{ chunks : "document_id FK ON DELETE CASCADE"
    documents {
        uuid id PK
        text title
        text doc_type "CHECK 4 values"
        text jurisdiction "CHECK US EU UK APAC"
        int tier_required "CHECK 1..4 default 1"
        text regulatory_ref
        date last_reviewed_at
        text product_category
        text risk_level "CHECK conservative moderate aggressive"
        text raw_content "UNREDACTED"
        timestamptz created_at
    }
    chunks {
        uuid id PK
        uuid document_id FK
        int chunk_index
        text content "redacted"
        vector_1024 embedding "NOT NULL"
        text jurisdiction "no CHECK"
        int tier_required "no CHECK"
        text regulatory_ref
        date last_reviewed_at
        text source_title
        timestamptz created_at
    }
    suitability_rules {
        uuid id PK
        text rule_name
        text product_category
        text client_risk_profile "CHECK 3 values"
        int min_tier_required "default 1"
        text jurisdiction
        text regulatory_ref
        text rule_text
        date last_reviewed_at
        timestamptz created_at
    }
```

- `documents` `schema.sql:12-29`; `chunks` `:34-46`; `suitability_rules` `:95-108` (no FK to anything; nothing populates it).
- Indexes: `idx_chunks_embedding` IVFFlat `vector_cosine_ops` `lists = 10` (`:51-52`) created in the same script as the empty table, so no training data at build time; no HNSW; no `ivfflat.probes` setting anywhere in the repo. Btree on `chunks(document_id)`, `chunks(jurisdiction)`, `chunks(tier_required)` (`:54-56`). Nothing else on `documents` or `suitability_rules` (no index on `doc_type`, `title`).
- RLS: `ALTER TABLE chunks ENABLE ROW LEVEL SECURITY; ... FORCE ROW LEVEL SECURITY` (`:61-62`). Policy text, verbatim (`:64-71`):
  ```sql
  CREATE POLICY chunk_visibility ON chunks
      FOR SELECT
      USING (
          tier_required <= current_setting('app.user_tier')::int
          AND jurisdiction = ANY(
              string_to_array(current_setting('app.user_jurisdictions'), ',')
          )
      );
  ```
  `current_setting` has no `missing_ok`, so an unset variable raises an error: fails closed (verification.md, PostgreSQL 16 docs).
- Roles (`:76-90, 110-111`): `finadvisor_service` (ALL on chunks, documents, suitability_rules; unused by the app) and `finadvisor_app` (SELECT only on the same three tables). Both created with plain `CREATE ROLE` (NOLOGIN by default). The application connects as `finadvisor` (`config.py:19`), which in the Postgres container is the bootstrap superuser, then `SET ROLE finadvisor_app` (`rls.py:11`). A superuser bypasses RLS even with FORCE; `SET ROLE` to a non-superuser drops that (verification.md).
- **No RLS**: `documents` (holds `raw_content`, tier and jurisdiction columns) and `suitability_rules`. `finadvisor_app` has plain SELECT on both. The SQL tools filter in the WHERE clause (`lookup_factsheet.py:56-65`, `lookup_suitability.py:61-70`); the database does not enforce it.
- Isolation tests (need live Postgres): `backend/tests/test_rls.py`, `test_rls_context.py`, `test_rls_e2e.py` (top_k=200 and zero-leakage assertions for 4 users, per map-data). The test fixture copies the policy text rather than reading `schema.sql`, and `create_all` would create tables without RLS or the IVFFlat index (`conftest.py:50`, per map-data).
- Data volume: 50 documents, ~114 chunks, 187,840 source characters (section 1).

## 6. Interfaces

### 6.1 HTTP endpoints (`backend/src/api/*.py`, mounted at `/api`, `main.py:89`)

| Method and path | Auth | Request | Response | Evidence |
|---|---|---|---|---|
| `GET /api/health` | none | none | `{"status":"ok"}` (static; no dependency checks) | `api/health.py:11-13` |
| `GET /api/me` | `X-User-Id` | none | `UserClaims` dump | `api/health.py:16-18` |
| `POST /api/chat/stream` | `X-User-Id` | `ChatRequest{message: str, conversation_id: str or null}` | `text/event-stream` (section 4.a) | `api/chat.py:23-43`, `api/schemas.py:8-10` |

Error statuses: 401 `{"detail":"Unknown user"}` from auth; 422 from Pydantic; 500 generic from the exception handlers. `conversation_id` is only logged (`chat.py:34`). The path `/api/audit/kong`, which Kong posts to, does not exist (`api/router.py:8-10`).

### 6.2 SSE event contract

See the table in section 4.a.

### 6.3 Tool contracts (4 tools)

All tools: input validated by `model_cls.model_validate` (`tools/__init__.py:60`); schema sent to Anthropic is `Model.model_json_schema()`; output is `model_dump_json()`. Unknown tool name raises `ValueError` (`:56-57`).

| Tool | Input | Output | Query / side effect | Evidence |
|---|---|---|---|---|
| `search_firm_kb` | `query: str`; `top_k: int = 5`, `le=10`, no lower bound | `{results:[{chunk_id, content, source_title, regulatory_ref, last_reviewed_at, similarity_score}], total_found}` | `embed_query` then `SELECT ... FROM chunks ORDER BY embedding <=> :vec LIMIT :top_k`, no WHERE; RLS only | `tools/search_kb.py:12-59`, `retrieval/vector_store.py:22-31` |
| `lookup_suitability_rule` | `product_category: str`, `client_risk_profile: str` (free strings; description lists the allowed values) | `{rules:[{rule_name, product_category, client_risk_profile, jurisdiction, regulatory_ref, rule_text, last_reviewed_at}], total_found}` | `SELECT ... FROM suitability_rules WHERE product_category=:c AND client_risk_profile=:r AND jurisdiction = ANY(:j) AND min_tier_required <= :tier ORDER BY jurisdiction, rule_name`. Table is empty after ingest, so it returns `total_found: 0` on a real DB (skeptic claim 4) | `tools/lookup_suitability.py:13-94` |
| `lookup_product_factsheet` | `product_name: str` | `{results:[{title, jurisdiction, tier_required, regulatory_ref, last_reviewed_at, product_category, risk_level, content}], total_found}` | `SELECT ... raw_content FROM documents WHERE doc_type='product_factsheet' AND title ILIKE '%name%' AND jurisdiction = ANY(:j) AND tier_required <= :tier ORDER BY title`; wildcard characters in the input are not escaped, no LIMIT; returns full unredacted `raw_content` as `content` | `tools/lookup_factsheet.py:13-89` |
| `escalate_to_compliance` | `reason: str`, `product_class: str`, `advisor_licenses: list[str]` (LLM-supplied) | `EscalationRecord{escalation_id "ESC-{sub}-{unix_seconds}", advisor_id, advisor_name, reason, product_class, advisor_licenses, advisor_jurisdictions, advisor_tier, timestamp, status "pending_review"}` | `log.warning("compliance_escalation", ...)` only; not persisted, not sent; id collides within the same second | `tools/escalate.py:13-73` |

The 10 suitability-rule documents are not lost: they are ingested into `documents`/`chunks` with `doc_type = 'suitability_rule'` and are reachable through `search_firm_kb`; only the structured table is empty.

### 6.4 LLM path

- Default (compose, Terraform): `anthropic.AsyncAnthropic(api_key=LITELLM_MASTER_KEY, base_url=f"{KONG_URL}/v1")` (`main.py:45-50`), i.e. Anthropic Messages API against `{KONG_URL}/v1/messages` -> Kong route `/v1` (`strip_path: false`) -> LiteLLM `http://litellm:4000`.
- Bypass: if `LLM_BASE_URL` is non-empty the client uses that base URL with `ANTHROPIC_API_KEY` (`main.py:45-46`); the `finadvisor` CLI sets it to `https://api.anthropic.com` (`cli.py:234`), so the README's default path skips Kong, LiteLLM and fallback entirely.
- Model name sent: `claude-sonnet-4-20250514` for every request (`orchestrator.py:18`); the eval judge uses the same string (`run_eval.py:23`).
- LiteLLM accepts the Anthropic Messages format on `/v1/messages` per its docs (verification.md); Kong passthrough of the `x-api-key` header was not tested.

### 6.5 LiteLLM routing: as configured vs what the docs say it does

As configured (`litellm/config.yaml`):

| Item | Value | Line |
|---|---|---|
| Deployments (all `model_name: "claude-sonnet-4-20250514"`) | `claude-primary` (anthropic `claude-sonnet-4-20250514`), `gpt4o-fallback` (`openai/gpt-4o`), `gemini-fallback` (`gemini/gemini-2.5-flash`) | `:1-21` |
| `routing_strategy` | `simple-shuffle` | `:24` |
| `num_retries` / `retry_after` | 2 / 5 | `:25-26` |
| `fallbacks` | `- claude-primary: [gpt4o-fallback, gemini-fallback]` | `:27-28` |
| `allowed_fails` / `cooldown_time` | 3 / 300 | `:29-30` |
| `drop_params` | true | `:33` |
| timeout, budget, cache, DB | none | whole file |

What the docs say it does (https://docs.litellm.ai, unversioned pages read 2026-11-01, recorded in verification.md; this is inference from the quotes, not a run):
- Deployments sharing a `model_name` are one load-balanced group. `simple-shuffle` without `rpm`/`tpm`/`weight` picks at random, so while Claude is healthy about one third of requests would go to Claude, one third to GPT-4o and one third to Gemini Flash, all returned under the Claude model name.
- `fallbacks` entries are keyed by `model_name` group. `claude-primary` is a `model_info.id`, so the entry most likely matches nothing; and the fallback targets are in the same group anyway.
- The documented patterns for "primary then fallback" are `order` in `litellm_params` within one group, or separate `model_name`s chained with `fallbacks`.
- `cooldown_time: 300` benches a deployment for 5 minutes after more than `allowed_fails` failures per minute; with one Claude deployment that removes the primary for 5 minutes.
- No timeout is set; library defaults apply. Redis is required for shared cooldown and rate limits across more than one instance; Postgres for virtual keys and spend.
- `drop_params: true` may silently drop Anthropic-specific parameters when a request lands on another provider (unverified).
- The only tests are mocked at `messages.create` (`backend/tests/test_fallback_chain.py:1-30`) and a manual live script (`backend/scripts/test_fallback_live.py`), never run (TODO.md:546).

## 7. Configuration

### 7.1 Settings fields (`backend/src/config.py:6-37`, env file `.env`, `extra="ignore"`)

| Field (env) | Default | Used by |
|---|---|---|
| `anthropic_api_key` (`ANTHROPIC_API_KEY`) | `""` | LLM client key only when `LLM_BASE_URL` is set (`main.py:46`) |
| `openai_api_key` | `""` | Not read by backend code (grep finds only `config.py`); LiteLLM gets it from the compose env |
| `google_api_key` | `""` | Not read by backend code |
| `litellm_master_key` | `"sk-litellm-local"` (dev secret) | LLM client key via Kong (`main.py:46`) |
| `voyage_api_key` | `""` | `VoyageEmbeddings` (`main.py:39`), ingest |
| `database_url` | `postgresql+asyncpg://finadvisor:localdev@localhost:5432/finadvisor` (dev secret) | engine (`session.py:10`), ingest |
| `pii_mode` | `"regex"` | `"dlp"` plus `gcp_project_id` selects DLP (`pii/__init__.py:9`) |
| `gcp_project_id` | `""` | DLP parent path |
| `kong_url` | `http://localhost:8001` | `{kong_url}/v1` base URL (`main.py:45`) |
| `llm_base_url` | `""` | when set, bypasses Kong |
| `langfuse_host` | `http://localhost:3030` | Langfuse client host |
| `langfuse_public_key` / `langfuse_secret_key` | `""` | Langfuse initialised only if both non-empty (`main.py:53`) |
| `jwt_secret` | `"local-dev-secret"` (dev secret) | Unused |

A missing production variable falls back silently to a dev value (`config.py:13, 19, 37`).

### 7.2 Hard-coded knobs

| Knob | Value | Where |
|---|---|---|
| ReAct `max_iterations` | 5 | `agent/orchestrator.py:41` |
| `MAX_TOKENS` | 4096 | `orchestrator.py:19` |
| `DEFAULT_MODEL` | `claude-sonnet-4-20250514` | `orchestrator.py:18` |
| Langfuse prompt name / label | `finadvisor-system` / `production` | `orchestrator.py:62`, `observability/tracing.py:77-78` |
| `SYSTEM_PROMPT_VERSION` | `1.0.0` | `agent/system_prompt.py:3` |
| DB pool | `pool_size=5`, `max_overflow=10` | `db/session.py:12-13` |
| RLS role name | `finadvisor_app` | `db/rls.py:11` |
| Embedding model / dims / batch | `voyage-3` / 1024 / 128 | `retrieval/embeddings.py:11-13` |
| Embedding retries / base delay / "RPS" | 3 / 1.0 s / 3 (semaphore size and 1/3 s sleep) | `embeddings.py:14-16, 23-24` |
| `input_type` | `"document"` for all calls | `embeddings.py:46` |
| `top_k` default / max | 5 / `le=10` | `tools/search_kb.py:14` |
| Chunk size / overlap | 2048 chars / 200 | `scripts/ingest.py:23-24` |
| Embedding price used in estimate | $0.06 per 1M tokens | `ingest.py:181` |
| `--target test` DB swap | `/finadvisor` -> `/finadvisor_test` | `ingest.py:197-198` |
| DLP info types / min likelihood | 8 types / `LIKELY` | `pii/redactor.py:26-35, 45` |
| Regex PII patterns | SSN, PHONE, EMAIL, ACCOUNT | `pii/fallback.py:24-29` |
| Mock users | 4 | `auth/mock_users.py:5-38` |
| Stale threshold | 12 months (days/30) | `frontend/src/components/StaleBadge.tsx:9-12`; prompt `system_prompt.py:19` |
| Eval thresholds | citation >= 0.95, faithfulness >= 0.90 | `scripts/run_eval.py:376-381`, `.github/workflows/eval-gate.yml:107-112` |
| Judge model | `claude-sonnet-4-20250514` | `run_eval.py:23` |
| Kong limits | 60/min, 500/h, payload 1 | `kong/kong.yml:15-16, 23` |
| LiteLLM retries / cooldown | 2 / 5 s / 3 fails / 300 s | `litellm/config.yaml:25-30` |
| Cloud Run scaling (max) | backend 10, frontend 5, litellm 3, kong 3, langfuse 2 | `terraform/cloud_run.tf:10, 137, 169, 236, 279` |
| Cloud Run min | backend 1 in prod else 0; others 0 | `cloud_run.tf:9, 136, 168, 235, 278` |
| Cloud Run resources | backend 1 CPU / 512Mi, frontend 1 / 256Mi, litellm 1 / 512Mi, kong 1 / 256Mi, langfuse 1 / 512Mi | `variables.tf:60-81`, `cloud_run.tf:181-182, 248-249, 297-298` |
| Cloud SQL tiers | `db-f1-micro` (app and Langfuse) | `terraform/variables.tf:48-58` |
| Region / environment default | `us-central1` / `dev` | `variables.tf:6-16` |
| Frontend backend URL | `http://localhost:8000` | `frontend/next.config.mjs:7` |

### 7.3 Dev-secret defaults in the repo
`LITELLM_MASTER_KEY=sk-litellm-local` and `JWT_SECRET=local-dev-secret` in `.env.example` and `config.py:13, 37`; Postgres `finadvisor/localdev` in `DC:5-7` and `config.py:19`; Langfuse DB `langfuse/langfuse` (`DC:84-86`); `NEXTAUTH_SECRET` default `langfuse-dev-secret` (`DC:73`); the standalone Langfuse compose file sets `admin@finadvisor.local` / `admin123` and keys `pk-lf-finadvisor-dev` / `sk-lf-finadvisor-dev` (`langfuse/docker-compose.langfuse.yml:11-17`, README.md:163). `.env` is gitignored and untracked (`git ls-files .env` returns nothing).

## 8. Runtime and deployment

### 8a. Local docker compose (`DC`)

| Service | Image / build | Host port | Healthcheck | Notes |
|---|---|---|---|---|
| postgres | `pgvector/pgvector:pg16` (`DC:3`) | 5432 | `pg_isready` (`DC:13-17`) | volume `pgdata`; schema mounted as initdb script (`DC:12`), runs first init only; creds `finadvisor/localdev` |
| backend | `build ./backend` (`DC:20`) | 8000 | none | `KONG_URL=http://kong:8000`, `LANGFUSE_HOST=http://langfuse:3000`, `PII_MODE=regex`; no Langfuse keys passed, so tracing off (`DC:23-31`); depends_on postgres healthy, kong started (`DC:32-36`) |
| frontend | `build ./frontend` (`DC:39`) | 3000 | none | **No `frontend/Dockerfile`**: cannot build |
| litellm | `build ./litellm` -> `ghcr.io/berriai/litellm:main-latest` | 4000 | none | provider keys from env |
| kong | `build ./kong` -> `kong:3.9` | 8001 -> container 8000 (`DC:60`) | none | `depends_on: litellm` without health condition |
| langfuse | `langfuse/langfuse:2` | 3030 -> 3000 | none | `SALT` not set in compose; standalone file sets it (`langfuse/docker-compose.langfuse.yml:10`, per map-infra) |
| langfuse-db | `postgres:16` | 5433 -> 5432 | `pg_isready` | creds `langfuse/langfuse` |
| redis | `redis:7-alpine` | 6379 | none | unused |

- Fixed host ports: 5432, 8000, 3000, 4000, 8001, 3030, 5433, 6379.
- Override file (`OV`): backend `target: dev` (`OV:3-5`) but `backend/Dockerfile` is single-stage with no `dev` target; mounts `src` and `tests`, runs `uvicorn --reload`; frontend runs `npm run dev`.
- Backend image: `python:3.12-slim`, `pip install -e "."` from `pyproject.toml` only (ignores `poetry.lock`), runs as root, single `uvicorn` process, no `HEALTHCHECK`, no `.dockerignore` (`backend/Dockerfile:1-14`).
- What does not build or work as shipped: frontend image; `docker compose` with the override file (missing `dev` target); `langfuse` compose service lacks its `SALT`. Kong may reject its own config (G-14).
- Usual dev path is not compose: `finadvisor` CLI (`backend/src/cli.py:289-345`) starts only Postgres in Docker, applies schema, ingests if `chunks` is empty, runs uvicorn on the host with `LLM_BASE_URL=https://api.anthropic.com` (`cli.py:231-250`), and `npm run dev` for the frontend.

### 8b. GCP Terraform as written

**Never deployed. `terraform validate` was never run** (Terraform CLI not installed on the author's machine, TODO.md:877; nothing in the repo contradicts it). Everything below is read from the `.tf` files.

```mermaid
flowchart TB
    internet["Internet (allUsers)"]
    subgraph gcp["GCP project, us-central1"]
        subgraph run["Cloud Run v2 services"]
            fe["frontend (no Dockerfile)"]
            be["backend KONG_URL=localhost:8000"]
            kg["kong (no ingress rule)"]
            ll["litellm"]
            lfs["langfuse:2"]
        end
        sql[("Cloud SQL POSTGRES_16 finadvisor, public IPv4")]
        lsql[("Cloud SQL langfuse, public IPv4, no backups")]
        sm["Secret Manager (9 secrets, only db-url populated)"]
        ar["Artifact Registry finadvisor"]
        gcs["GCS corpus + eval-results buckets"]
        dlp["Cloud DLP (roles/dlp.user)"]
    end
    state[("GCS finadvisor-tfstate (unmanaged)")]
    internet -->|"roles/run.invoker allUsers"| fe
    internet -->|"roles/run.invoker allUsers"| be
    be -->|"/cloudsql unix socket"| sql
    lfs -->|"/cloudsql unix socket"| lsql
    be -.->|"env KONG_URL, points at itself"| kg
    kg -.->|"upstream litellm:4000 Docker DNS"| ll
    be --> sm
    ll --> sm
    be --> dlp
```

- Backend: min 1 instance in prod else 0, max 10, 1 CPU 512Mi, Cloud SQL volume mount, 7 secret env vars plus `KONG_URL`, `LANGFUSE_HOST`, `PII_MODE`, `GCP_PROJECT_ID` (`cloud_run.tf:1-126`). Frontend, litellm, kong, langfuse services: `cloud_run.tf:128-330`. No concurrency, timeout, VPC connector or egress settings anywhere.
- Cloud SQL app instance: `POSTGRES_16`, `db-f1-micro`, `REGIONAL` + backups + PITR + `deletion_protection` only when `environment == "prod"`, flag `cloudsql.enable_pgvector` (`cloud_sql.tf:1-26`); Langfuse instance has no backups, no HA, no deletion protection (`:56-70`); both `ipv4_enabled = true`, no private networking.
- IAM: service accounts for backend and frontend only; backend gets project-wide `secretmanager.secretAccessor`, `cloudsql.client`, `dlp.user`, `storage.objectViewer` (`iam.tf:11-33`); `allUsers` invoker on backend and frontend (`:35-49`).
- Secrets: nine Secret Manager secret shells; only `db-url` receives a value from Terraform (`cloud_sql.tf:44-54`). Env refs use `version = "latest"`.
- State: GCS bucket `finadvisor-tfstate`, prefix `terraform/state`, the bucket is not created by this code, one prefix for all environments (`main.tf:11-14`). Provider `google ~> 5.0`, `required_version >= 1.5`; `random_password` is used with no `random` provider declared (implicit).
- Image tags default to `latest` (`variables.tf:24-46`). Not present: Redis, VPC, load balancer, Cloud Armor, monitoring, alerting, uptime checks.

Why it would not work as written:
1. Backend `KONG_URL = http://localhost:8000` (`cloud_run.tf:44-47`) is the backend's own container; there is no sidecar. Every LLM call fails.
2. Kong's upstream `http://litellm:4000` (`kong.yml:5`) is a Docker-compose DNS name; Cloud Run services are addressed by their `*.run.app` URLs and need IAM or public access between services, none of which is configured.
3. Cloud SQL: `schema.sql` is never applied (no Terraform resource or pipeline step); the user `finadvisor` (`cloud_sql.tf:33-37`) is `cloudsqlsuperuser`, not a true superuser, and nothing grants it `finadvisor_app`. `SET ROLE finadvisor_app` (`rls.py:11`) most likely fails on first chat request (inferred, verification.md).
4. `PII_MODE = "gcp_dlp"` (`cloud_run.tf:94-97`) does not equal `"dlp"` (`pii/__init__.py:9`): regex redaction is used silently.
5. Backend gets no `LITELLM_MASTER_KEY`, so it sends the default `sk-litellm-local` while LiteLLM runs with the secret (`cloud_run.tf:34-112`, `config.py:13`).
6. Frontend: no Dockerfile to build, and `/api/*` is rewritten to `http://localhost:8000` at build time (`next.config.mjs:7`), so `NEXT_PUBLIC_API_URL` set to the backend URI (`cloud_run.tf:154-157`) has no effect.
7. Both Cloud SQL instances have public IPv4; the backend and frontend are open to `allUsers`; with header-only auth anyone on the internet can choose to be the Tier-4 UK user.
8. Langfuse: `NEXTAUTH_SECRET = "changeme-in-production"` and the DB password as a plaintext env value (`cloud_run.tf:302-317`), `NEXTAUTH_URL` is a placeholder `https://langfuse.finadvisor.example.com`, no `SALT`; backend gets Langfuse keys from empty secrets (and see G-15 for the SDK problem).
9. `cloudsql.enable_pgvector` as a database flag name was not checked against Cloud SQL docs (open item).

## 9. CI/CD

Two workflows in `.github/workflows/`.

| Workflow | Trigger | Jobs | What runs |
|---|---|---|---|
| `ci.yml` | PR to main, push to main | `backend` (Python 3.12), `frontend` (Node 20, npm cache) | backend: `pip install -e ".[dev]"`, `ruff check .`, `ruff format --check .`, `mypy src/`, `pytest tests/ -v --tb=short` (`ci.yml:9-37`). frontend: `npm ci`, `npm run lint`, `npx tsc --noEmit`, `npm run build` (`:39-65`) |
| `eval-gate.yml` | PR to main | `lint-and-test` (same steps as backend job, `pytest -x`), `eval-gate` (needs the first; pgvector service `test/test`) | schema load, ingest `--target test`, uvicorn + `sleep 5`, `run_eval.py`, threshold check, artifact upload (`eval-gate.yml:7-121`) |

What actually happens as written:
- **Broken install.** `pip install -e ".[dev]"` (`ci.yml:25`, `eval-gate.yml:23, 64`): `backend/pyproject.toml` is Poetry with a `[tool.poetry.group.dev.dependencies]` group and no `dev` extra (`pyproject.toml:23-28`), so `ruff`, `mypy` and `pytest` are not installed and the Lint step fails (skeptic claim 10; the "pip warns about a missing extra rather than erroring" behaviour is expected, not run).
- **No Postgres in `ci.yml`.** The DB test files skip themselves when `localhost:5432` is unreachable (`backend/tests/conftest.py:22-41`), so the RLS tests do not run in the PR CI (skeptic claim 13). The eval-gate job has Postgres but runs after `lint-and-test`, which runs `pytest tests/` without a service container.
- **Eval job cannot complete as written** (G-06): the ingest step has no `VOYAGE_API_KEY` (the script exits at `ingest.py:258-260`) and no `DATABASE_URL`; the default URL goes through the `--target test` replace that also rewrites the user name; the backend step passes no `KONG_URL` or `LLM_BASE_URL`, so the LLM client points at `localhost:8001` where nothing listens; `sleep 5` instead of a health wait.
- The "DEPLOY BLOCKED" text refers to a deploy that does not exist.
- Never run on a real PR (TODO.md:847).

Missing: image build and push, deploy, `terraform fmt/validate/plan/apply`, dependency, container or secret scanning, CodeQL, Dependabot, coverage gate (targets in CLAUDE.md: >70% backend, >60% frontend), frontend tests, compose integration job, pre-commit.

## 10. Testing

Backend: 18 `test_*.py` files, 122 `def test_` occurrences (counted with grep; maps said ~123), `asyncio_mode = "auto"` (`backend/pyproject.toml:56-58`). Frontend: no tests and no test runner (`frontend/package.json:5-10`).

| Type | Files | Needs | Mocked |
|---|---|---|---|
| Unit | `test_agent` (8), `test_chat_stream` (7), `test_tool_registry` (8), `test_escalate` (6), `test_pii` (10), `test_logging` (11), `test_tracing` (12, Langfuse as `MagicMock`), `test_auth` (5), `test_eval_runner` (14), parts of `test_search_kb` (4) | nothing | Anthropic client, DB sessions, Langfuse, FastAPI dependencies |
| API-level with mocked agent | `test_integration` (9) | nothing | `FinAdvisorAgent` replaced by `MagicMock` (`test_integration.py:17-110`); this is the only place the `citation` SSE event is exercised |
| DB-dependent (`@requires_db`) | `test_rls` (3), `test_rls_context` (2), `test_rls_e2e` (5), `test_lookup_factsheet` (6), `test_lookup_suitability` (5), DB parts of `test_search_kb` | Postgres at `localhost:5432` | none |
| External-key | `test_embeddings` (2, skipped without `VOYAGE_API_KEY`, `test_embeddings.py:9-11`) | Voyage key | none |
| Fallback | `test_fallback_chain` (5) | nothing | `messages.create` only; does not exercise LiteLLM |
| Manual live | `backend/scripts/test_fallback_live.py` | compose stack | none; never run |

Facts about the DB tests: `TEST_DATABASE_URL` is hard-coded to the dev database `finadvisor:localdev@localhost:5432/finadvisor` (`conftest.py:17`); fixtures seed documents with the `__TEST_SEED__` prefix and re-apply RLS DDL inline (duplicated policy text); `can_connect_to_db()` runs at import time (`conftest.py:22-41`); `conftest` imports `src.main`, which builds the app at import.

Coverage gaps: no real producer of citation events; no timeout or latency tests; no concurrent pool-reuse RLS test; no live Kong, LiteLLM or Langfuse tests; no oversized or malicious input tests; no readiness tests; DLP only mocked; no test that Langfuse works with the installed SDK (G-15); no frontend tests; no retrieval-quality metrics (recall@k, MRR). Eval: 50 golden questions judged by an LLM (faithfulness, citation accuracy) with gates 0.95/0.90; never run.

## 11. Observability

- **Logging.** structlog JSON to stdout (`PrintLoggerFactory`), `contextvars` for `request_id` (from `X-Request-Id` or uuid4) and `user_id` (from the unauthenticated `X-User-Id` header), `cache_logger_on_first_use=True` (`observability/logging.py:11-52`). Raw search queries are logged (`tools/search_kb.py:47`), factsheet product names and user ids (`lookup_factsheet.py:48-52`), escalation reasons (`escalate.py:64-71`). The DB URL is logged with credentials stripped (`main.py:37`). `LOG_LEVEL` in the override file is not read by `configure_logging` (`logging.py:26-32`; `make_filtering_bound_logger(0)`).
- **Langfuse.** Off in compose (no keys passed, `DC:23-31`); initialised only if both keys are set (`main.py:53-68`). When on: one trace `finadvisor_query` per request, one generation per iteration with full `messages` as input and the whole `response.model_dump()` as output, one span per tool with unredacted input and output (`orchestrator.py:43-51, 66-80, 106-125`). `get_prompt` is a synchronous network call per request (`orchestrator.py:62`, `tracing.py:84`), wrapped in try/except (`tracing.py:83-90`). The trace calls themselves are not isolated, and use the Langfuse v2 method names that the locked SDK (4.6.1) does not have (G-15). No flush call on request end.
- **Health.** `GET /api/health` returns a static body; no readiness (DB, LLM, Voyage, Langfuse) and no metrics endpoint (`api/health.py:11-13`). Compose has no backend, litellm, kong or frontend healthcheck.
- **Not present:** metrics, dashboards, alerts, uptime checks, log shipping, request-level latency histograms. Token usage is logged per iteration (`orchestrator.py:82-90`).

## 12. Security posture as built

Claims from `docs/threat_model.md` (line numbers in that file) against the code.

| Claim | As built | Evidence |
|---|---|---|
| RLS enforces access at the database level (tm:11-12) | True for `chunks` on the normal path: `SET ROLE finadvisor_app` first, FORCE RLS, fails closed if settings unset. Not true for `documents` and `suitability_rules` (app-level WHERE) | `db/rls.py:11`, `schema.sql:61-71`, `lookup_factsheet.py:56-65` |
| The superuser `finadvisor` is never used for application queries (tm:14) | The app connects as `finadvisor` (superuser in the compose Postgres) and drops privilege per request with `SET ROLE`; any code path that skips `get_rls_session` bypasses RLS | `config.py:19`, `rls.py:10-11`, `dependencies.py:33-38` |
| Session variables set before every query (tm:13) | `SET` (not `SET LOCAL`), session-scoped on a pooled connection; reverted only because each request ends in rollback (no commit exists in `src/`); `reset_rls_context` never called and does not reset `app.*` | `rls.py:11-21`, verification.md claim 2 |
| Residual risk mitigated by `get_rls_session` DI (tm:18) | All three endpoints that touch the DB use it via `get_agent`; the dependency pattern is the only guard | `dependencies.py:57-68` |
| PII redaction before embedding (tm:36-39) | Yes at ingest (regex default); but `documents.raw_content` stores the original text and `lookup_product_factsheet` returns it to the LLM and the client | `ingest.py:120-141`, `lookup_factsheet.py:58, 83` |
| Output redaction on every SSE text event (tm:46) | Only the final `message` event; tool events and errors not redacted; user input never redacted | `chat.py:47-82` |
| Regex covers SSN, phone, email, account (tm:37) | Yes, but US-centric; over-matches numbers (`12500000` and `2019 2024` become `[ACCOUNT_REDACTED]`), does not cover names or addresses (run on samples 2026-11-01) | `pii/fallback.py:24-29` |
| GCP DLP used in production (tm:37, 50) | Selected only when `PII_MODE == "dlp"`; Terraform sets `gcp_dlp`, so regex is used | `pii/__init__.py:9`, `cloud_run.tf:94-97` |
| `X-User-Id` maps to predefined profiles; unknown ids 401 (tm:59-61) | True, and trivially spoofable; no authentication | `auth/jwt.py:9-13` |
| System prompt versioned in LangFuse (tm:78) | Only if keys set; otherwise code constant | `orchestrator.py:62-63` |
| User input always in the user role (tm:79) | True | `orchestrator.py:60` |
| Tool inputs validated via Pydantic (tm:80) | True for shape; no length or content limits; `product_name` used in ILIKE without escaping | `tools/__init__.py:60`, `lookup_factsheet.py:54` |
| `max_iterations` 5 prevents infinite loops (tm:81) | True | `orchestrator.py:41, 65, 153-157` |
| No prompt-injection guardrail beyond the above | None in code | `system_prompt.py`, whole `src/` |
| Tool outputs structured; RLS prevents unauthorized data (tm:86-89) | RLS holds for chunks; `tool_result` events carry full raw tool output to the browser | `chat.py:66-70` |
| Escalation tool creates audit records (tm:90) | Log line only | `escalate.py:64-71` |
| LiteLLM Claude -> GPT-4o -> Gemini with circuit breaker (tm:97-98) | Shuffle across all three; fallback entry likely matches nothing | `litellm/config.yaml:23-30` |
| Kong enforces per-user rate limits (tm:99) | Config uses a non-existent `identifier` field; backend does not forward `X-User-Id`; `policy: local` | `kong.yml:13-19`, `main.py:47-50` |
| All model calls traced in LangFuse (tm:100) | Off by default; unusable with locked SDK | `DC:23-31`, G-15 |
| Secrets never in code; `.env` gitignored; Secret Manager in prod (tm:109-113) | `.env` ignored; dev secrets in code defaults, compose and Terraform (`changeme-in-production`) | `config.py:13,19,37`, `cloud_run.tf:314-317` |
| structlog avoids logging sensitive fields (tm:113) | Raw queries, escalation reasons and unauthenticated user ids are logged | `search_kb.py:47`, `escalate.py:64-71` |
| Cloud Run services use internal URLs; Kong only public entry; LangFuse internal; Cloud SQL no public IP (tm:120-122) | `allUsers` on backend and frontend; public IPv4 on both Cloud SQL instances | `iam.tf:35-49`, `cloud_sql.tf:20-22, 64-66` |
| Dependencies pinned; images built from repo Dockerfiles (tm:131) | `>=` floors; `litellm:main-latest`, `langfuse/langfuse:2`, `latest` tags; root user; no scanning | `pyproject.toml:9-21`, `litellm/Dockerfile:1`, `variables.tf:24-46` |
| CI blocks deploy if citation < 95% or faithfulness < 90% (tm:144) | Gate exists in YAML and script; the job cannot run as written and no deploy exists | `eval-gate.yml`, G-05, G-06 |
| UI shows STALE badge older than 12 months; prompt flags stale sources (tm:153-154) | Badge exists but needs citation events that never arrive; prompt flag is advisory; every corpus document is now over 12 months old | `StaleBadge.tsx:9-12`, `system_prompt.py:19-20` |
| Every query traced with user, tools, sources, response (tm:161) | Only when Langfuse is on and working; user id comes from an unauthenticated header | G-15, `logging.py:46` |
| Data residency via region variable (tm:175) | `region` variable exists (default `us-central1`); Voyage, Anthropic, OpenAI and Gemini calls leave any region by design | `variables.tf:6-10` |

## 13. Gap register

Severity scale: critical = breaks the product's stated purpose or exposes restricted data on the described path; high = likely failure or exposure under normal use; medium = real defect or gap with limited blast radius at the current size; low = hygiene. "Source" names the report the gap came from: `map-backend`, `map-data`, `map-infra`, `map-fe-docs` (map-frontend-docs), `skeptic` (verification.md claim number), `docs <URL>` (vendor docs recorded in verification.md), or `this run` (found while writing this file). Evidence is `file:line` relative to the FinAdvisor repo root.

| ID | Area | Gap | Severity | Evidence file:line | Source |
|---|---|---|---|---|---|
| G-01 | Auth | Identity is the `X-User-Id` header looked up in 4 hard-coded users; no token, signature or expiry; `jwt_secret`/`python-jose` unused | critical | `backend/src/auth/jwt.py:9-13`, `backend/src/auth/mock_users.py:5-38`, `backend/src/config.py:37` | map-backend, skeptic 1 |
| G-02 | Cloud / exposure | `allUsers` `run.invoker` on backend and frontend; with G-01 anyone can read Tier-4 UK content | critical | `terraform/iam.tf:35-49` | map-infra, skeptic 12 |
| G-03 | PII | `documents.raw_content` is stored unredacted and `lookup_product_factsheet` returns it as `content` to the LLM and client (PII leak, not a tier leak) | critical | `backend/scripts/ingest.py:141`, `backend/src/agent/tools/lookup_factsheet.py:58, 83`, `backend/db/schema.sql:27` | map-data, skeptic 6 |
| G-04 | PII / SSE | `tool` and `tool_result` SSE events are not redacted; they carry raw tool JSON (chunk text, factsheets, exception text) | critical | `backend/src/api/chat.py:54-70` | map-backend, skeptic 7 |
| G-05 | CI | `pip install -e ".[dev]"` but no `dev` extra exists (Poetry group), so ruff, mypy, pytest are not installed; CI fails at Lint | critical | `.github/workflows/ci.yml:25`, `.github/workflows/eval-gate.yml:23, 64`, `backend/pyproject.toml:23-28` | map-infra, skeptic 10 |
| G-06 | CI / eval | Eval gate cannot run as written: ingest step has no `VOYAGE_API_KEY` (exit at `ingest.py:258-260`) and no `DATABASE_URL`; `--target test` replace also rewrites the DB user (`finadvisor_test:localdev`); backend step has no `KONG_URL`/`LLM_BASE_URL` (defaults to `localhost:8001`); `sleep 5` | critical | `.github/workflows/eval-gate.yml:67-85`, `backend/scripts/ingest.py:196-198, 258-260`, `backend/src/config.py:26` | this run (ran the replace), map-infra |
| G-07 | Data / tools | `suitability_rules` has no ingest path (only a test inserts); `lookup_suitability_rule` returns empty on a real DB | critical | `backend/scripts/ingest.py:130-228`, `backend/tests/test_lookup_suitability.py:67`, `backend/src/agent/tools/lookup_suitability.py:60-70` | map-data, skeptic 4 |
| G-08 | LLM gateway | Three deployments share one `model_name` with `simple-shuffle`: traffic is spread across Claude, GPT-4o and Gemini Flash while Claude is healthy; silent model substitution under the Claude name | critical | `litellm/config.yaml:1-21, 24` | map-infra, docs https://docs.litellm.ai/docs/routing |
| G-09 | LLM gateway | `fallbacks: - claude-primary: [...]` uses a `model_info.id`, but fallbacks are keyed by `model_name`; entry most likely matches nothing, so no real fallback exists | critical | `litellm/config.yaml:27-28` | map-infra, docs https://docs.litellm.ai/docs/proxy/reliability |
| G-10 | Cloud wiring | Backend `KONG_URL=http://localhost:8000` points at itself; every LLM call fails in Cloud Run | critical | `terraform/cloud_run.tf:44-47` | map-infra, skeptic 12 |
| G-11 | Cloud wiring | Kong upstream `http://litellm:4000` is Docker DNS; no service-to-service URL, IAM or ingress between Kong, LiteLLM and backend | critical | `kong/kong.yml:5`, `terraform/cloud_run.tf:162-269` | map-infra, skeptic |
| G-12 | Cloud wiring | `schema.sql` never applied to Cloud SQL; user `finadvisor` is `cloudsqlsuperuser` with no grant of `finadvisor_app`; `SET ROLE finadvisor_app` likely fails on first request (inferred) | critical | `terraform/cloud_sql.tf:33-37`, `backend/src/db/rls.py:11` | skeptic (new hidden risk) |
| G-13 | Cloud wiring / frontend | No `frontend/Dockerfile` (compose and Terraform both reference it); `/api/*` rewrite is hard-coded to `localhost:8000` at build time, so the frontend cannot reach Cloud Run backend | critical | `docker-compose.yml:39`, `terraform/cloud_run.tf:141, 154-157`, `frontend/next.config.mjs:7` | map-infra, map-fe-docs, skeptic 9 |
| G-14 | Gateway | Kong `rate-limiting` is configured with `identifier: header`; the open-source plugin has no `identifier` parameter (`limit_by` default `consumer`), so Kong may reject the declarative config or not limit by user; also backend never forwards `X-User-Id` to Kong; `policy: local` per instance. Not run | high | `kong/kong.yml:13-19`, `backend/src/main.py:47-50` | this run (https://developer.konghq.com/plugins/rate-limiting/reference/), map-infra |
| G-15 | Observability | Tracing uses Langfuse v2 methods `trace()/generation()/span()`; `poetry.lock` pins `langfuse 4.6.1` and `pyproject` allows `>=2.0.0`, and the 4.6.1 `Langfuse` class has none of them; with both keys set `start_trace` raises `AttributeError` outside any try/except, so chat fails. Tests pass because Langfuse is a `MagicMock` | high | `backend/src/observability/tracing.py:24, 41, 55`, `backend/src/agent/orchestrator.py:43-51`, `backend/pyproject.toml:16`, `poetry.lock` (langfuse 4.6.1), `backend/tests/test_tracing.py:19-23` | this run (installed 4.6.1, inspected client) |
| G-16 | Citations | Server never produces `citation` events or maps `[N]` to chunks; UI badges stay inert and sources panel empty; the "every claim cited" rule rests on the LLM alone | high | `backend/src/agent/types.py:14-18`, `backend/src/agent/orchestrator.py:97-151`, `frontend/src/components/CitationInline.tsx:19-23` | map-backend, map-fe-docs, skeptic 7 |
| G-17 | PII | User message is sent to Anthropic, Voyage and Langfuse unredacted (docs claim it is redacted); only final LLM text is redacted | high | `backend/src/agent/orchestrator.py:60`, `backend/src/api/chat.py:38-52`, `backend/src/agent/tools/search_kb.py:49`, `mvp.md:40` | this run, map-backend |
| G-18 | Compliance | `escalate_to_compliance` only logs; not persisted or notified; `advisor_licenses` come from the LLM, not `user.licenses`; id `ESC-{sub}-{unix_s}` collides within a second | high | `backend/src/agent/tools/escalate.py:16, 49, 57, 64-71` | map-backend |
| G-19 | RLS | Session-level `SET` on pooled connections; safe only because each request rolls back (no commit exists); adding a commit leaks one user's tier into the next request on that connection; `reset_rls_context` never called and only resets the role | high | `backend/src/db/rls.py:11-21`, `backend/src/dependencies.py:27-38` | map-backend, map-data, skeptic claim 2 (partly) |
| G-20 | RLS | RLS only on `chunks`; `documents` and `suitability_rules` rely on app WHERE clauses while `finadvisor_app` has SELECT on them | high | `backend/db/schema.sql:61-71, 87-90, 110-111`, `backend/src/agent/tools/lookup_factsheet.py:56-65` | map-data, skeptic 3 |
| G-21 | RLS | App connects as a superuser and relies on `SET ROLE`; any path that skips `get_rls_session` bypasses RLS; the cloud user is `cloudsqlsuperuser` | high | `backend/src/config.py:19`, `backend/src/db/rls.py:10-11` | map-data, docs https://www.postgresql.org/docs/16/ddl-rowsecurity.html |
| G-22 | Streaming | No try/except in the SSE generator or around `messages.create`; a failure after the 200 header drops the connection with no `error` event | high | `backend/src/api/chat.py:37-41`, `backend/src/agent/orchestrator.py:72-78` | map-backend, skeptic 14 |
| G-23 | PII / config | Terraform `PII_MODE=gcp_dlp` never equals `"dlp"`; regex redaction is used silently in the cloud | high | `terraform/cloud_run.tf:94-97`, `backend/src/pii/__init__.py:9` | this run |
| G-24 | Cloud config | Backend Cloud Run env has no `LITELLM_MASTER_KEY`; it sends the default `sk-litellm-local` | high | `terraform/cloud_run.tf:34-112`, `backend/src/config.py:13` | this run |
| G-25 | Config | Dev secrets are code defaults (`localdev` DB password, `sk-litellm-local`, `local-dev-secret`); a missing production variable falls back silently | high | `backend/src/config.py:13, 19, 37` | map-backend, map-infra |
| G-26 | Cloud data | Both Cloud SQL instances have public IPv4, no private networking (threat model says none) | high | `terraform/cloud_sql.tf:20-22, 64-66`, `docs/threat_model.md:122` | map-infra, skeptic 12 |
| G-27 | Cloud secrets | `NEXTAUTH_SECRET = "changeme-in-production"` and Langfuse DB password as plaintext env value in Terraform (and so in state) | high | `terraform/cloud_run.tf:302-317` | map-infra |
| G-28 | Build | Backend image installs with `pip install -e "."` from unpinned `>=` floors and ignores `poetry.lock`; rebuilds can change major versions (anthropic, langfuse, fastapi) | high | `backend/Dockerfile:6-8`, `backend/pyproject.toml:9-21` | map-backend, map-infra |
| G-29 | Cloud data | Backups, HA and deletion protection only when `environment == "prod"`; Langfuse DB never; `db-f1-micro` | high | `terraform/cloud_sql.tf:8, 15-18, 25, 56-70`, `terraform/variables.tf:48-58` | map-infra, skeptic 12 |
| G-30 | Capacity | Each chat request holds a pooled DB connection (open transaction) for the whole LLM loop; pool is 5 + 10 per process, no `pool_pre_ping`, recycle or statement timeout | medium | `backend/src/db/session.py:9-15`, `backend/src/dependencies.py:27-38` | map-data, this run |
| G-31 | Latency / reliability | No explicit timeout or retry setting on the Anthropic call (SDK defaults), no overall turn deadline; Voyage call has no timeout; retry catches every exception | medium | `backend/src/agent/orchestrator.py:72-78`, `backend/src/retrieval/embeddings.py:42-47, 55` | map-backend, map-data |
| G-32 | Latency / UX | LLM calls are non-streaming; the full answer arrives as one `message` event after up to 5 sequential calls | medium | `backend/src/agent/orchestrator.py:72, 150` | map-backend |
| G-33 | Retrieval | Queries are embedded with `input_type="document"`; Voyage docs say use `"query"` | medium | `backend/src/retrieval/embeddings.py:46` | map-data, skeptic 8, docs https://docs.voyageai.com/docs/embeddings |
| G-34 | Retrieval | IVFFlat `lists=10` built on an empty table (no training data), no `ivfflat.probes`; ANN results are filtered after the index scan, so RLS can return fewer than `top_k`; pgvector docs favour HNSW or iterative scans (needs pgvector >= 0.8.0; deployed version unknown) | medium | `backend/db/schema.sql:51-52`, `backend/src/retrieval/vector_store.py:22-31` | map-data, docs https://github.com/pgvector/pgvector |
| G-35 | Retrieval | Vector search has no application-level filter (tier, jurisdiction); no score threshold, rerank or hybrid search | medium | `backend/src/retrieval/vector_store.py:22-31` | map-backend, map-data |
| G-36 | Dependency | Voyage is a single provider with no fallback; `voyage-3` is an older generation (docs list voyage-4 series, voyage-finance-2); sync SDK via threads | medium | `backend/src/retrieval/embeddings.py:11, 21, 42` | map-data, docs https://docs.voyageai.com/docs/embeddings |
| G-37 | PII | Regex patterns US-centric, no names or addresses; `ACCOUNT` and `PHONE` over-match plain numbers (`12500000`, `2019 2024`, ISINs) and swallow trailing whitespace | medium | `backend/src/pii/fallback.py:24-29` | map-backend, map-data, this run |
| G-38 | PII | DLP call is synchronous inside the async request path with no retry; redactor injected with type `RegexRedactor` | medium | `backend/src/pii/redactor.py:55`, `backend/src/dependencies.py:45` | map-backend |
| G-39 | Ingest | Ingest is not idempotent (uuid4 per run, plain INSERT, no unique source key); no migrations or schema version; schema only on first volume init | medium | `backend/scripts/ingest.py:127, 149, 203-228`, `backend/db/schema.sql`, `docker-compose.yml:12` | map-data, skeptic 5 |
| G-40 | Observability / PII | Langfuse receives full messages and tool outputs unredacted; `get_prompt` is a synchronous network call per request; trace calls not isolated from the request path | medium | `backend/src/agent/orchestrator.py:62, 66-80, 125`, `backend/src/observability/tracing.py:15-30` | map-backend |
| G-41 | Logging | Logs carry raw queries, escalation reasons and an unauthenticated user id | medium | `backend/src/agent/tools/search_kb.py:47`, `backend/src/agent/tools/escalate.py:64-71`, `backend/src/observability/logging.py:46`, `backend/src/main.py:131` | map-backend |
| G-42 | Errors | Tool errors built by string interpolation (invalid JSON when the message has quotes) and leak exception text to the LLM and client | medium | `backend/src/agent/orchestrator.py:117-123` | map-backend |
| G-43 | RLS | `SET` values by f-string; `jurisdictions` is an unvalidated `list[str]` (safe only because values come from `MOCK_USERS`); tier is int-cast | medium | `backend/src/db/rls.py:14-17`, `backend/src/auth/models.py:11` | map-data, skeptic claim 2 |
| G-44 | Operations | Health endpoint is static; no readiness (DB, LLM, Voyage, Langfuse), no metrics, no alerting, uptime checks or monitoring in Terraform | medium | `backend/src/api/health.py:11-13`, `terraform/` | map-backend, map-infra |
| G-45 | Input limits | `ChatRequest.message` unbounded; `top_k` has no lower bound; factsheet `ILIKE` input unescaped, no `LIMIT`, returns whole documents | medium | `backend/src/api/schemas.py:8-10`, `backend/src/agent/tools/search_kb.py:14`, `backend/src/agent/tools/lookup_factsheet.py:54-65` | map-backend |
| G-46 | Cloud runtime | No concurrency, timeout, VPC connector or ingress settings on Cloud Run; no load balancer, Cloud Armor or CORS; Kong rate limit is per instance (`policy: local`, up to 3 instances) | medium | `terraform/cloud_run.tf:1-330`, `kong/kong.yml:17` | map-infra |
| G-47 | Terraform | State bucket not managed, one state prefix for all environments; `terraform validate` never run; image tags default to `latest`; LiteLLM base image `main-latest`; no deploy or image-build pipeline | medium | `terraform/main.tf:11-14`, `terraform/variables.tf:24-46`, `litellm/Dockerfile:1`, `TODO.md:877` | map-infra |
| G-48 | Gateway | Kong `http-log` posts to `/api/audit/kong`, which does not exist in the backend | medium | `kong/kong.yml:25-29`, `backend/src/api/router.py:8-10` | map-infra, skeptic 11 |
| G-49 | Local runtime | Override file targets a `dev` build stage that does not exist; no healthchecks on backend, litellm, kong, frontend; `kong` waits only for `litellm` start; Langfuse service lacks `SALT`; fixed host ports; duplicate standalone Langfuse compose with conflicting ports and published admin password | medium | `docker-compose.override.yml:3-5`, `docker-compose.yml:32-36, 64-79`, `langfuse/docker-compose.langfuse.yml:10-17` | map-infra, skeptic 9 |
| G-50 | Cloud IAM | Backend service account has project-wide secretAccessor, cloudsql.client, dlp.user, storage.objectViewer; no service accounts for litellm, kong, langfuse | medium | `terraform/iam.tf:1-33` | map-infra |
| G-51 | Container | Backend image: single stage, root user, no `HEALTHCHECK`, no `.dockerignore`, single uvicorn process; no image scanning | medium | `backend/Dockerfile:1-14` | map-backend, map-infra |
| G-52 | Staleness | `last_reviewed_at` in the corpus ranges 2023-06-15 to 2025-03-15, so every document is now over 12 months old; the model is not told today's date; the stale warning is a prompt instruction only | medium | `data/corpus/*/*.json` (`last_reviewed_at`), `backend/src/agent/system_prompt.py:19-20`, `frontend/src/components/StaleBadge.tsx:9-12` | this run |
| G-53 | Product | No conversation memory: every request is single-turn; `conversation_id` is accepted and only logged | medium | `backend/src/agent/orchestrator.py:60`, `backend/src/api/chat.py:34`, `frontend/src/hooks/useChat.ts:68` | map-backend, map-fe-docs |
| G-54 | Evaluation | Eval gate scores only LLM-judged faithfulness and citation accuracy; no retrieval metrics (recall@k, MRR); judge is the same model family; never run on a PR | medium | `backend/scripts/run_eval.py:23, 376-381`, `TODO.md:847` | map-data, map-fe-docs |
| G-55 | Security | No prompt-injection guardrail; compliance flags and license checks exist only as prompt text | medium | `backend/src/agent/system_prompt.py:10-20`, `docs/threat_model.md:77-81` | map-fe-docs |
| G-56 | Testing | DB tests target the dev DB and are skipped without Postgres (so skipped in PR CI); RLS policy text duplicated in fixtures; no concurrent pool-reuse RLS test; no live gateway tests; DLP only mocked; no frontend tests | medium | `backend/tests/conftest.py:17, 22-41, 72-125`, `.github/workflows/ci.yml` | map-backend, map-data, skeptic 13 |
| G-57 | Frontend | Unguarded `JSON.parse`; `tool_result` matched to the last running tool, not by id; no abort, timeout, 401 or 429 handling; user switch does not clear chat; full profile in `localStorage`; unused `eventsource-parser`; hand-rolled SSE parser (no multi-line `data`) | low | `frontend/src/hooks/useChat.ts:70, 79, 108-113, 120, 145`, `frontend/src/lib/api.ts:24-26, 40-50`, `frontend/src/hooks/useUser.ts:11, 22` | map-fe-docs |
| G-58 | Hard-coded knobs | Model, max tokens, iterations, embedding model and dimension, chunk size, pool sizes and embedding price are constants | low | `backend/src/agent/orchestrator.py:18-19, 41`, `backend/src/retrieval/embeddings.py:11-16`, `backend/scripts/ingest.py:23-24, 181` | map-backend, map-data |
| G-59 | Dead config | Redis container unused; `jwt_secret`, `python-jose`, `ChatResponse`/`Citation` schemas, `NEXT_PUBLIC_API_URL`, `openai_api_key`/`google_api_key` settings unused | low | `docker-compose.yml:97-102`, `backend/src/config.py:11-12, 37`, `backend/src/api/schemas.py:13-26` | map-backend, map-infra |
| G-60 | Docs | README, architecture.md, mvp.md and threat_model.md contradict the code on auth, LLM path, Kong plugins, citations, PII tokens and counts (section 0) | low | section 0 table | map-fe-docs |
| G-61 | Runtime hygiene | App object built at import (`create_app()`); structlog `cache_logger_on_first_use`; `LOG_LEVEL` env in the override is not read | low | `backend/src/main.py:162`, `backend/src/observability/logging.py:26-32` | map-backend |
| G-62 | Ingest | Overlap text is prepended after splitting, so chunks can exceed 2048 characters; chunks omit `doc_type`, `product_category`, `risk_level` | low | `backend/scripts/ingest.py:78-84, 146-160` | map-data |

Count at d6c2bd3: 62 gaps: 13 critical (G-01 to G-13), 16 high (G-14 to G-29), 27 medium (G-30 to G-56), 6 low (G-57 to G-62). Recount if rows change.

## 14. Inputs for future research

### 14.1 Keshav's numbers (2026-11-01, from the orchestrator run brief; verification.md)
- About 50 advisors, fewer than 5 QPS.
- Budget under $100 per month for cloud plus LLM.
- Compliance scope: as the MVP, a US/EU/UK synthetic corpus (FINRA, SEC, MiFID II, FCA COBS as encoded); no real regulatory certification.
- Latency, availability and RPO/RTO targets: not given (open).

### 14.2 Vendor facts to start from (read 2026-11-01; recorded in verification.md unless noted)

| Topic | Fact | URL |
|---|---|---|
| pgvector (README 0.8.7) | IVFFlat should be created after the table has data; `lists` about rows/1000, `probes` default 1, start at sqrt(lists). HNSW has better speed-recall and can be built on an empty table. At 114 rows a sequential scan is exact | https://github.com/pgvector/pgvector |
| pgvector filtering | Filtering is applied after the index scan (10% selectivity with `ef_search` 40 gives about 4 rows); iterative index scans (`hnsw.iterative_scan`, `ivfflat.max_probes`, pgvector >= 0.8.0), higher `ef_search`, partial indexes or partitioning mitigate. Deployed pgvector version unknown: `SELECT extversion FROM pg_extension WHERE extname='vector'` | https://github.com/pgvector/pgvector |
| PostgreSQL 16 RLS | Superusers and `BYPASSRLS` roles always bypass RLS (FORCE does not change that); `SET ROLE` to a non-superuser drops superuser privileges; session `SET` persists past COMMIT and reverts on ROLLBACK; recommended pattern is one transaction per request with `set_config(name, value, true)` (bind parameters) and `SET LOCAL ROLE`, connecting as a non-superuser, non-owner role; `current_setting` without `missing_ok` raises (fail closed) | https://www.postgresql.org/docs/16/ddl-rowsecurity.html , https://www.postgresql.org/docs/16/sql-set.html |
| Voyage | Specify `input_type` (`query` for queries); `voyage-3` is the older generation (current voyage-4 series; `voyage-finance-2` for finance), 1024 dims; Tier-1 rate limit 2000 RPM (the code throttles itself far below that); list max 1,000 inputs; backoff with jitter recommended; `voyage-3` price $0.06 per 1M tokens | https://docs.voyageai.com/docs/embeddings , https://docs.voyageai.com/docs/rate-limits , https://docs.voyageai.com/docs/pricing |
| LiteLLM routing | Same-`model_name` deployments are load-balanced; `simple-shuffle` without weights is random; fallbacks are keyed by `model_name`; documented primary-then-fallback patterns are `order` or chained `model_name`s; no timeout set means library defaults; `cooldown_time` default 5 s (config uses 300); pin a SemVer tag, not `main-latest`; Redis needed for more than one instance, Postgres for keys and spend | https://docs.litellm.ai/docs/routing , https://docs.litellm.ai/docs/proxy/reliability |
| LiteLLM + Anthropic SDK | Proxy `/v1/messages` follows the Anthropic Messages spec, key as `x-api-key`; Kong passthrough and SSE untested | https://docs.litellm.ai |
| Kong rate-limiting (fetched this run) | OSS parameters: `limit_by` (default `consumer`; values consumer, consumer-group, credential, header, ip, path, principal, service), `header_name`, `policy`, `minute/hour/...`; no `identifier` parameter | https://developer.konghq.com/plugins/rate-limiting/reference/ |

Note on URLs: verification.md recorded the sites and sections read (pgvector README, PostgreSQL 16.15 docs, Voyage docs, docs.litellm.ai) but not every page address; the page paths above for PostgreSQL, Voyage and LiteLLM are the standard documentation pages for those topics and should be re-opened when a research round cites them.

### 14.3 Unconfirmed in this run
- Whether `pip install -e ".[dev]"` errors or only warns (expected: warns, then tools are missing).
- Whether Kong 3.9 refuses `identifier` at start-up or ignores it (not run).
- Whether the `SET ROLE` failure on Cloud SQL (G-12) occurs (no Cloud SQL instance; inferred).
- Whether `cloudsql.enable_pgvector` is a valid database flag name (not checked against Cloud SQL docs).
- Whether FastAPI at the locked version (0.136.1) keeps the dependency-yielded DB session open for the full SSE stream; the flow assumes it does, and the mocked tests do not exercise it.
- Deployed pgvector version (the compose image tag `pg16` floats).
- Whether Langfuse SDK 4.x can talk to a Langfuse server `:2` (moot while G-15 stands).
- Test counts per type are from grep, tests were not run; `test_integration.py` DB requirement was not found (it uses a mocked agent).
