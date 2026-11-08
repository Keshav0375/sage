---
key: "E4-T19"
title: "Orchestrator LLM loop: streaming, tools, release checks, nonce"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T7", "E4-T10", "E4-T11", "E4-T12", "E4-T18"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.3", "decision-logs.md#adr-007", "decision-logs.md#adr-009", "decision-logs.md#adr-036"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 125, "id": 6263468053, "url": "https://github.com/Keshav0375/FinAdvisor/issues/125"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
One streaming LLM call with tools, max 3 iterations, with a per-request nonce, sentence-level release checks and original-text lookups by id.

## Description
After the gate passes (parent expansion and staleness via E3), inject retrieval as a JSON-encoded tool_result for a synthetic search_firm_kb tool_use, then stream via LLMClient with tools (E4-T10 dispatcher), prompt cache (E4-T7) and the versioned system prompt (no secrets or tenant data; 'today', as_of and tenant/user text after the cache breakpoint; cite with [n]). Emit 'tool' events (name/status/tool_use_id); text goes through sentence-buffered redaction (E4-T12); finish_reason in (end_turn, max_tokens, refusal, gate); LLM failures after breaker/fallback -> error LLM_UNAVAILABLE; max LLM_MAX_ITERATIONS.

Round 4 (ADR-036, ADR-009 amended, 04 §4.5 'sentences are released only after the numeric gate and the citation verifier pass'): (1) Prompt guard: untrusted chunk text reaches the model only inside the JSON-encoded tool_result with a per-request random boundary nonce (>= 128 bits, from `secrets`, new per request, never in system, never logged); JSON-encode spotlighting is the default; datamarking exists only behind the exploratory flag `A_INJ_2_DATAMARKING` (default false) on the model-visible copy. (2) Release pipeline: each sentence passes an ordered list of `ReleaseCheck` callables before its delta is emitted; this ticket registers the CitationVerifier (E4-T11) and defines the protocol `ReleaseCheck(sentence, context) -> Pass | Withhold(reason)`; E4-T28, E4-T29 and E4-T31 register further checks. A `Withhold` stops emission, emits `refusal {ANSWER_WITHHELD, reason, escalate_offer}`, finish_reason `refusal`. (3) The verifier compares against the original chunk text fetched by id (E4-T11), not the tool_result copy. Out of scope: the numeric gate, footers, entitlement re-read, policy (separate tickets).

## Acceptance criteria
- [ ] Given the LLM stub citing [n] not in retrieved ids, when the turn runs, then no citation event for that n is emitted and the verifier outcome is recorded (end-to-end test).
- [ ] Given two requests, when the captured Anthropic requests are compared, then each tool_result carries a different random nonce, the nonce never appears in `system`, and the retrieved text 'ignore previous instructions' appears only inside a tool_result block (test_nonce_per_request_and_no_system_leak).
- [ ] Given a `ReleaseCheck` stub that returns Withhold('numeric_ungrounded') on sentence 2, when the turn runs, then sentence 1's delta is emitted, no delta for sentence 2 is emitted, and the events end with refusal {ANSWER_WITHHELD, numeric_ungrounded} then done(refusal).
- [ ] Given a tool raising an exception with sensitive text, then no emitted event or tool_result contains that text; given the LLM stub requesting tools forever, the loop stops at 3 iterations and done is emitted.
- [ ] Given the flag A_INJ_2_DATAMARKING unset, when a request is built, then no datamarking transform is applied to the tool_result (test).
