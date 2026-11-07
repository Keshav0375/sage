---
key: "E8-T6"
title: "Render the streamed turn with meta notice and refusal"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T5"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/04-components-and-responsibilities.md#4.4"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
The chat view shows deltas as they arrive, tool status, a degraded-retrieval notice, refusals and errors.

## Description
Implements deep-dive/06-interfaces-and-contracts.md §6.2 behaviour in the UI. Rewrite useChat (zustand store) on top of E8-T5: `turn` sets ids; `delta` appends to the in-progress assistant message; `tool` shows a status chip (tool name and status only); `meta` with retrieval_degraded=true shows a visible notice ('answer built with reduced ranking quality', reason optional), stored on the message; `refusal` NO_FIRM_DOCUMENTATION shows the refusal message and, if escalate_offer, an escalation hint (no endpoint call beyond arch); `error` shows the code-keyed state from E8-T4 with Retry when retryable; `done` finalises with message_id and finish_reason (max_tokens shows a 'truncated' note). Disable input while streaming; Stop button aborts. Remove client-side citation parsing of `[n]` (server emits citations; E8-T7). Out of scope: markdown (E8-T7), history (E8-T8).

## Acceptance criteria
- [ ] Given a scripted event sequence turn, delta x3, done, when processed, then the message text equals the concatenated deltas and finish state is set (vitest store test).
- [ ] Given `meta {retrieval_degraded:true}`, when received, then the degraded notice is in the DOM; given false, it is absent.
- [ ] Given `refusal {escalate_offer:true}`, when received, then the refusal view and escalation hint render and no assistant text is shown.
- [ ] Given `error {code:'LLM_UNAVAILABLE',retryable:true}`, when received, then the mapped message and a Retry button show; given retryable false, no Retry button.
- [ ] Given the Stop button, when clicked mid-stream, then the fetch is aborted and input is re-enabled.
