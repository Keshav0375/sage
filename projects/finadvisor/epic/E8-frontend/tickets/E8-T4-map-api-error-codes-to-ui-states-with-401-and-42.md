---
key: "E8-T4"
title: "Map API error codes to UI states with 401 and 429 handling"
epic: "E8"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E8-T3"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.4", "deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Every API error renders a fixed, code-keyed message and 401 and 429 never crash the app.

## Description
Implements deep-dive/04-components-and-responsibilities.md §4.4 'error states keyed by error code' and 6.1 error shape `{"error":{code,message,request_id,retryable}}`. Add src/lib/errors.ts: parse the error body into ApiError; a table keyed by every 6.1 code (UNAUTHENTICATED, FORBIDDEN, INPUT_TOO_LONG, INPUT_BLOCKED, GUARD_UNAVAILABLE, RATE_LIMITED, TENANT_BUDGET_EXCEEDED, NO_FIRM_DOCUMENTATION, LLM_UNAVAILABLE, RETRIEVAL_UNAVAILABLE, TURN_INTERRUPTED, IDEMPOTENCY_KEY_REUSED, INTERNAL) to client-owned copy and a retry hint; unknown codes fall back to INTERNAL copy. Never display server `message` text verbatim as HTML; show request_id for support. 401: refresh token once, retry once, else return to sign-in. 429: read `Retry-After`, show a countdown and disable send until it elapses. Add an error boundary. Out of scope: SSE-specific handling (E8-T5/T6).

## Acceptance criteria
- [ ] Given each code in the 6.1 list, when mapped, then a non-empty message exists (table-driven vitest over all codes) and an unknown code maps to the INTERNAL copy.
- [ ] Given a 429 with `Retry-After: 5`, when the chat send is attempted, then the send button is disabled and a countdown shows, re-enabling after 5 s (fake timers).
- [ ] Given a 401 whose retry after token refresh also returns 401, when it occurs, then the sign-in view shows and no uncaught exception is logged.
- [ ] Given a render error in a child, when thrown, then the error boundary shows a fallback (unit test).
