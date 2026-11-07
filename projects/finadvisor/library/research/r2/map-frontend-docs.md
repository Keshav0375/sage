# FinAdvisor as-built map: frontend and repo docs (Explore, 2026-11-01)

Paths relative to /Users/keshav/Projects/FinAdvisor. No graphify output folder exists.

## A. Frontend (Next.js 14.2.35 App Router)
- One route: src/app/page.tsx:5-7 "use client" ChatWindow; layout.tsx:32-33 Header + main. No API routes, middleware or server components.
- Components: ChatWindow, MessageBubble, StreamingText, MarkdownContent, ToolCallCard, SourcesPanel, CitationInline, CitationPanel, StaleBadge, Header, UserSwitcher. Hooks useChat, useUser. Lib api.ts, users.ts, parseCitations.ts.
- Deps next, react, react-markdown, zustand, eventsource-parser (unused; SSE parser hand-rolled src/lib/api.ts:28-53).
- Backend call: fetch("/api/chat/stream", POST) (api.ts:12), body {message, conversation_id?}; next.config.mjs:4-8 rewrites /api/* → http://localhost:8000 (baked at build; cannot reach Cloud Run).
- SSE parse splits on "\n", event name resets after one data line (no multi-line data) (api.ts:40-50); non-OK → generic error (24-26).
- useChat handles message(type text only), tool, tool_result (matched by last index, not tool_use_id; :103-118), citation, error, done; JSON.parse unguarded (:70,79,120,145).
- Auth: header X-User-Id only (api.ts:16); mock users hard-coded in src/lib/users.ts:10-43; UserSwitcher select, localStorage `finadvisor_user` (useUser.ts:11,22); switching user does not clear chat.
- Citations: [N] regex (parseCitations.ts:13) only inside p/li (MarkdownContent.tsx:56,74); click-only panel with title, ref, reviewed date, no chunk text (CitationPanel.tsx:20-50); StaleBadge > 12×30 days (StaleBadge.tsx:9-12); SourcesPanel lists all.
- State: chat in local useState (useChat.ts:37-39), module-level counter; zustand only for user. conversationId never sent (useChat.ts:68).
- No process.env usage; NEXT_PUBLIC_API_URL in compose unused.
- No tests, no test runner; CI only lint + build (ci.yml:39-65). Target >60% coverage (CLAUDE.md:103).
- No frontend/Dockerfile.
- Gaps: spoofable header auth; client holds full profile in localStorage; hard-coded backend URL; no retry/abort/timeout/401/429 handling; unguarded JSON.parse; no conversation continuity; tool_result mismatch; dropped event shapes; no tests.

## B. Docs as stated intent
- Goal: Compliance-Aware Wealth Advisor RAG Assistant for fictional firm "Meridian Wealth Partners" (README.md:3-5, mvp.md:52). Problem: SharePoint keyword search; generic chatbots leak PII, hallucinate citations, same results for all (mvp.md:5-11).
- Status: "Private -- Interview project for demonstration purposes" (README.md:212, mvp.md:174-182).
- Personas (README.md:74-79): Sarah Chen senior T3 US; Alex Kim associate T1 EU; James Wright private_wealth T4 UK; Priya Sharma advisor T2 US+EU. Tier rule: see tier ≤ own level (docs/threat_model.md:22-27).
- Regimes: FINRA, SEC, MSRB, MiFID II, FCA COBS (threat_model.md:168). Regulation only from synthetic corpus (CLAUDE.md:174).
- Rules (CLAUDE.md:151-163): RLS is the authorization layer; PII redacted before embedding and on output; every claim cited [N]; eval gate is the deploy gate; no secrets in code; flag cost before bulk API calls. Stale > 12 months badge.
- Numbers: 50 docs (20/10/10/10); 114 chunks actual vs 200-300 planned; voyage-3 1024; corpus embed ~$0.003-0.01; 50 golden Q&A; gate citation ≥95%, faithfulness ≥90%; Kong 60/min, 500/h, 1 MB; circuit breaker 3 fails/300s (TODO.md:507) vs "3x 5xx in 60s" (mvp.md:122); max_iterations 5; 9 milestones ~24 h; ~123 test functions (README says 120+, TODO 94); coverage targets >70% backend, >60% frontend.
- NOT stated: user count, QPS, latency targets, SLOs, LLM cost budget, deadlines (only a 5-7 min demo).
- Non-goals implied: mock auth, real IdP is a "production consideration" (threat_model.md:54-69); refuses tax advice and client PII/account data; Redis optional.
- Deferred verifications (TODO.md says 100% done): Docker runs, CI on a real PR, terraform validate/apply, live eval, live Kong/LiteLLM/Langfuse, GPT-4o fallback (no OpenAI key). README default path bypasses the gateway (README.md:111). Nothing deployed to GCP.
- Threat model vs code: RLS implemented and tested; PII regex only in chat path, split-chunk gap; auth mock (RS256/OIDC listed as future); no prompt-injection guardrail; escalation "audit record" is a log line; Kong token-budget and PII-guard plugins (mvp.md:124-126) absent; jwt_secret default and Langfuse [dev default login, redacted] published (README.md:163); network claims internal-only but Terraform allUsers on backend/frontend; litellm main-latest; no image scanning; eval gate never run on a PR; Kong audit sink route missing.
- Doc contradictions: auth (README JWT vs mvp signed JWT vs architecture/threat model X-User-Id; code = header); LLM path (README direct vs Kong→LiteLLM; code default Kong); chunk count 200-300 vs 114; Kong plugins token budget/PII guard vs rate limits only; citation UI hover+excerpt vs click-only no excerpt; PII token format [CLIENT_NAME_1] vs [REDACTED]; demo product names differ; ARCHITECTURE.md vs architecture.md filename; "Server Components by default" vs "use client"; frontend Dockerfile listed but absent; CLAUDE.local.md says Windows/PowerShell; CI deploy preview described but absent; circuit-breaker rule differs; test counts differ.
- Phase deliveries (TODO.md:920-962, 39 Story-Reports): P0 scaffolding, compose, lint, CI; P1 schema, RLS, ORM, RLS tests; P2 corpus, PII, Voyage, ingest (50 docs → 114 chunks); P3 mock users + header auth, E2E RLS zero leakage (43/10/26/55 chunks per user); P4 four tools, registry, ReAct orchestrator, prompt v1.0.0; P5 LiteLLM, Kong, mocked fallback tests (live deferred); P6 app factory, SSE, PII output, structlog, 9 integration tests; P7 UI, citations, stale badge; P8 Langfuse (deferred), golden set, eval runner (live deferred); P9 eval gate (not run on a PR), Terraform 9 files (not validated), docs.
