---
key: "E8-T12"
title: "Add Playwright specs for resume, 429, 401 and XSS safety"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T11"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.4", "deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/08-security-and-privacy.md#8.2"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
E2E proves resume after disconnect, graceful 429 and 401, no unsanitized HTML and no token in localStorage.

## Description
Part of E8 Done-when. Specs: (1) mid-stream disconnect at seq N: the stub drops the connection; the UI reconnects with `Last-Event-ID: N`, final text equals the full answer with no duplicated text. (2) 429 with Retry-After on POST /v1/chat: the rate-limit message and countdown show, the page remains usable, send re-enables. (3) 401 on an API call: token refresh retried once, then the sign-in view shows, no page error (`page.on('pageerror')` count 0). (4) Injected payload: the answer text and a citation excerpt contain `<img src=x onerror=window.__xss=1>` and `<script>window.__xss=1</script>`; after render `window.__xss` is undefined and no such elements exist. (5) After sign-in and a chat, localStorage, sessionStorage and IndexedDB dumps do not contain the ID token string. Also covers TURN_INTERRUPTED: Retry resubmits with a new Idempotency-Key.

## Acceptance criteria
- [ ] Given a drop after seq 2 of 5 events, when the test completes, then the request log shows a GET with `Last-Event-ID: 2` and the answer contains each delta exactly once.
- [ ] Given a 429 `Retry-After: 2`, when sent, then the countdown is visible, `pageerror` count is 0 and send is enabled after about 2 s.
- [ ] Given 401 twice, when it occurs, then the sign-in view is visible and `pageerror` count is 0.
- [ ] Given the XSS payload, when rendered, then `window.__xss` is undefined and `page.locator('img[onerror], script:not([src])')` inside the message area has count 0.
- [ ] Given a completed signed-in chat, when browser storage is dumped, then the ID token string appears in none of localStorage, sessionStorage or IndexedDB.
