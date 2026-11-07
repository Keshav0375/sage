---
key: "E4-T19"
title: "Orchestrator LLM loop: streaming with tools, verifier and redaction"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T7", "E4-T10", "E4-T11", "E4-T12", "E4-T18"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.3", "decision-logs.md#ADR-007", "decision-logs.md#ADR-009"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
One streaming LLM call with tools, max 3 iterations, wired to verifier and output redaction.

## Description
After the gate passes (parent expansion and staleness via E3), inject retrieval as a JSON-encoded tool_result for a synthetic search_firm_kb tool_use, then stream via LLMClient with tools (4 tools, E4-T10 dispatcher), prompt cache (E4-T7) and the versioned system prompt (update MVP src/agent/system_prompt.py: no secrets or tenant data, 'today' and tenant/user text after the cache breakpoint, instruct citing with [n]). Emit 'tool' events (name/status/tool_use_id) on tool_use start and result; text goes through sentence-buffered redaction to 'delta'; when the answer completes (or per sentence), the CitationVerifier runs and citation events are emitted; verifier rejection handled per questions. Max LLM_MAX_ITERATIONS. finish_reason in (end_turn, max_tokens, refusal, gate). LLM failures after breaker/fallback -> error LLM_UNAVAILABLE.

## Acceptance criteria
- [ ] Given the LLM stub citing [n] not in retrieved ids, when the turn runs, then no citation event for that n is emitted and the verifier outcome is recorded (end-to-end verifier test).
- [ ] Given a tool raising an exception with sensitive text, then no emitted event or tool_result contains that text.
- [ ] Given the LLM stub requesting tools forever, then the loop stops at 3 iterations and done is emitted.
- [ ] Given the retrieved text contains 'ignore previous instructions', it appears only inside a tool_result block in the captured Anthropic request, never in system (test).
- [ ] Delta events contain no PII injected in the stubbed answer.
