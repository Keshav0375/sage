---
key: "E8-T6"
title: "Render the streamed turn with meta notice and refusal"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T5"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/04-components-and-responsibilities.md#4.4", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "decision-logs.md#adr-033", "decision-logs.md#adr-036"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 203, "id": 6263594048, "url": "https://github.com/Keshav0375/FinAdvisor/issues/203"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The chat view shows deltas as they arrive, tool status, the degraded-retrieval notice, server notices, refusals with their reason, and an entitlement-aborted turn.

## Description
Implements deep-dive/06-interfaces-and-contracts.md §6.2 behaviour in the UI. Rewrite useChat (zustand store) on top of E8-T5:
- `turn` sets ids; `delta` appends to the in-progress assistant message; `tool` shows a status chip (tool name and status only).
- `meta` with retrieval_degraded=true shows a visible notice ('answer built with reduced ranking quality', reason optional), stored on the message; the `as_of` and `as_of_source` fields are stored on the message for the chip of E8-T13.
- `notice {kind: "as_of" | "mixed_jurisdiction" | "known_pending" | "state", text}`: render the server `text` as plain text in a notice area above the answer, one per event, with a style per kind (never model text, never HTML).
- `refusal`: `NO_FIRM_DOCUMENTATION` shows the refusal message; `ANSWER_WITHHELD` shows copy keyed by `reason` (`numeric_ungrounded`: 'a figure could not be found in the cited sources', `footer_missing`, `as_of_violation`, `no_version_history`: 'no version history for this source'); with `escalate_offer` an escalation hint (no endpoint call beyond arch). No assistant text is shown for a refusal.
- `error` shows the code-keyed state from E8-T4 with Retry when retryable; `ENTITLEMENT_CHANGED` marks the message `refused`, keeps the text already streamed with a banner 'your access changed during this answer; no further sources are shown', and renders no citations that arrive after the abort (ADR-033: text already streamed cannot be recalled). `TURN_EXPIRED` shows its mapped state.
- `done` finalises with message_id and finish_reason (`max_tokens` shows a 'truncated' note; `refusal` and `gate` show no answer text).
Disable input while streaming; Stop button aborts. Remove client-side citation parsing of `[n]` (server emits citations; E8-T7). Out of scope: markdown (E8-T7), footers (E8-T15), history (E8-T8).

## Acceptance criteria
- [ ] Given a scripted event sequence turn, delta x3, done, when processed, then the message text equals the concatenated deltas and finish state is set (vitest store test).
- [ ] Given `meta {retrieval_degraded:true}`, when received, then the degraded notice is in the DOM; given false, it is absent.
- [ ] Given `notice {kind:'mixed_jurisdiction', text:'<b>US vs EU</b>'}`, when received, then the text shows literally with no <b> element and the kind style class is applied.
- [ ] Given `refusal {code:'ANSWER_WITHHELD', reason:'numeric_ungrounded', escalate_offer:true}`, when received, then the numeric copy and escalation hint render and no assistant text is shown; given `reason:'no_version_history'` the matching copy shows.
- [ ] Given `error {code:'ENTITLEMENT_CHANGED'}` after 3 deltas and then a late `citation`, when processed, then the streamed text stays, the access banner shows, the message state is `refused` and the late citation is not rendered (test `useChat.test.ts::entitlement_changed_abort`).
- [ ] Given `error {code:'LLM_UNAVAILABLE',retryable:true}`, when received, then the mapped message and a Retry button show; given retryable false, no Retry button.
- [ ] Given the Stop button, when clicked mid-stream, then the fetch is aborted and input is re-enabled.
