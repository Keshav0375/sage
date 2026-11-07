---
key: "E8-T4"
title: "Map API error codes to UI states with 401 and 429 handling"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T3", "E13-T3", "E13-T4", "E13-T7"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.4", "deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/06-interfaces-and-contracts.md#6.11", "decision-logs.md#adr-031", "decision-logs.md#adr-032"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Every API error renders a fixed, code-keyed message; 401 and 429 never crash the app, 421 follows the cell hint once and 503 CELL_UNAVAILABLE shows a per-firm outage state.

## Description
Implements deep-dive/04-components-and-responsibilities.md §4.4 'error states keyed by error code', 6.1 error shape `{"error":{code,message,request_id,retryable}}` and 06 6.11. Add src/lib/errors.ts: parse the error body into ApiError; a table keyed by every 6.1 code (UNAUTHENTICATED, FORBIDDEN, INPUT_TOO_LONG, INPUT_BLOCKED, GUARD_UNAVAILABLE, RATE_LIMITED, TENANT_BUDGET_EXCEEDED, NO_FIRM_DOCUMENTATION, ANSWER_WITHHELD, LLM_UNAVAILABLE, RETRIEVAL_UNAVAILABLE, TURN_INTERRUPTED, TURN_EXPIRED, IDEMPOTENCY_KEY_REUSED, NOT_FOUND, TENANT_NOT_FOUND, ENTITLEMENT_CHANGED, WRONG_CELL, TENANT_MOVED, CELL_UNAVAILABLE, INTERNAL) to client-owned copy and a retry hint; unknown codes fall back to INTERNAL copy. Never display server `message` text verbatim as HTML; show request_id for support.
- 401: refresh the firm's token once, retry once, else return to that firm's sign-in.
- 429: read `Retry-After`, show a countdown and disable send until it elapses.
- 421 `WRONG_CELL` and `TENANT_MOVED` (06 6.11: body `{"error":{...},"cell_hint":{"cell_id","api_endpoint"}}`): show the cell hint copy, replace that firm's in-memory `apiBase` with `cell_hint.api_endpoint` (https only, otherwise show the INTERNAL state), and retry the request once, but only when the host of the hint equals the host `/resolve?slug=` returns now for that firm (E8-T2; if they differ the `/resolve` answer is used, and if `/resolve` fails the INTERNAL state shows); a second 421 on the retry shows the state and stops (no redirect loop). The token is not re-issued: the same firm token is sent to the hinted cell, which verifies it at project level.
- 503 `CELL_UNAVAILABLE`: show an outage state naming the firm only; there is no fallback to another cell, other firms in the switcher stay usable, and a Retry button re-sends once the person asks.
Add an error boundary. Out of scope: SSE-specific handling (E8-T5, E8-T6), the firm switcher UI (E8-T14).

## Acceptance criteria
- [ ] Given each code in the list above, when mapped, then a non-empty message exists (table-driven vitest over all codes) and an unknown code maps to the INTERNAL copy.
- [ ] Given a 429 with `Retry-After: 5`, when the chat send is attempted, then the send button is disabled and a countdown shows, re-enabling after 5 s (fake timers).
- [ ] Given a 401 whose retry after token refresh also returns 401, when it occurs, then the sign-in view shows and no uncaught exception is logged.
- [ ] Given a 421 `WRONG_CELL` with hint `https://eu.example` and `/resolve` also answering `https://eu.example`, when a request is made, then the firm's apiBase becomes `https://eu.example`, the request is retried once to that host and succeeds; given a second 421, then no third request is sent and the state shows (test `errors.test.ts::wrong_cell_follow_once`).
- [ ] Given a 421 hint whose host differs from the `/resolve` answer, when handled, then apiBase becomes the `/resolve` host, never the hint host (test `errors.test.ts::hint_must_match_resolve`).
- [ ] Given a 421 hint with an `http://` endpoint, when handled, then apiBase is unchanged and the INTERNAL state shows.
- [ ] Given a 503 `CELL_UNAVAILABLE` for firm A, when shown, then firm B's requests are not blocked and no request goes to another cell (test `errors.test.ts::cell_unavailable_isolated`).
- [ ] Given a render error in a child, when thrown, then the error boundary shows a fallback (unit test).
