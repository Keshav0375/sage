# Slice E4

## Epic section (from arch/plan.md)

### E4 Agent and guardrails

- **Goal.** A streamed, cited, guarded answer with resumable delivery and no data leaks to the client.
- **Scope.**
  - `LLMClient`: timeouts, retries with jitter, circuit breaker, same-provider fallback gated by evals, prompt caching, config-only model ids.
  - Retrieve-first orchestrator; Haiku follow-up condensation; Presidio (`en_core_web_sm`); Model Armor (500 ms, fail closed); JSON `tool_result`; citation verifier + server citation events; sentence-buffered output redaction.
  - SSE v2 contract with ids, `meta` event, resume (`turn_events`), `Idempotency-Key`; escalations persisted; `conversations` / `messages` (with `retrieval_degraded`); outbox rows written in the persist transaction (`chat.audit`, `chat.usage`, sampled `eval.sample`).
  - Admin endpoints: advisor updates (direct), document ACL-change and delete requests (`acl_change_requests` + outbox, 202) with the status endpoint; per-tenant token budget and concurrency; error codes.
- **Arch sections.** overview.md#4.5 (`guardrails`, `agent`, `llm`, `events`, `admin`), overview.md#6.1 to #6.3, overview.md#8.1; ADR-005, ADR-006, ADR-007, ADR-009, ADR-022.
- **Dependencies.** E3.
- **Spikes first.** Model Armor latency; Presidio latency and recall on the synthetic corpus (no official figure); Sonnet 5.5 prompt-cache hit behaviour with the versioned tools.
- **Done when.**
  - Client-visible events contain no tool payloads or exception text (test over all event types); every emitted `[n]` is in the retrieved chunk ids (verifier test).
  - A dropped connection resumes from `Last-Event-ID` and replays missing events; the same `Idempotency-Key` does not generate twice; a different body returns 409; `meta.retrieval_degraded` matches `messages.retrieval_degraded`.
  - Model Armor timeout (500 ms) fails closed; PII injected in a question never reaches Voyage, Anthropic, logs or Langfuse (test).
  - With the primary model forced to fail, the fallback is used only when `LLM_FALLBACK_ENABLED` is true; no temperature / top_p / top_k is sent.
  - An admin ACL-change request returns 202 and writes exactly one `acl_change_requests` row and one outbox row; `chat-api` holds no write grant on content tables.
  - TTFT p50 < 2.0 s and p95 < 3.5 s measured on the 10k-chunk synthetic corpus with a real LLM against overview §2.1 (fail if above).
  - Fixes G-04, G-16, G-17, G-18, G-22, G-23, G-31, G-32, G-38, G-42, G-45, G-53, G-55.

## Arch files to read (paths; read only the named subsections)

- context/projects/finadvisor/arch/overview/04-components-and-responsibilities.md  (sections: 4.5)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md  (sections: 6.1)
- context/projects/finadvisor/arch/overview/08-security-and-privacy.md  (sections: 8.1)
- context/projects/finadvisor/arch/stack.md (versions)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md §6.6 (config keys), only the keys this epic uses

## ADRs (context/projects/finadvisor/arch/decisions.md; line of heading)

- line 413: ADR-005: Drop LiteLLM; in-process LLMClient with same-provider fallback
- line 392: ADR-006: Models and prompt caching
- line 371: ADR-007: Retrieve-first orchestration and conversation state
- line 327: ADR-009: Guardrails (OWASP LLM Top 10 2025)
- line 47: ADR-022: Asynchronous ACL changes through acl_change_requests and an acl-applier worker
