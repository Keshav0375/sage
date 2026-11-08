---
key: "E8-T9"
title: "Add thumbs feedback on assistant messages"
epic: "E8"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E8-T6"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/04-components-and-responsibilities.md#4.4"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 206, "id": 6263597236, "url": "https://github.com/Keshav0375/FinAdvisor/issues/206"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
An advisor can rate an answer up or down with an optional comment.

## Description
Implements deep-dive/06-interfaces-and-contracts.md §6.1 `POST /v1/messages/{id}/feedback` body `{score: -1 | 1, comment?: string}` -> 204. Thumbs up/down on each completed assistant message (message_id from `done` or history); thumbs down opens an optional comment field. State: pending, saved, failed (retry); selection persists in view after reload of history only if the messages API returns it (otherwise questions). Disabled while streaming and for refusal/error messages. Out of scope: eval pipeline (backend).

## Acceptance criteria
- [ ] Given thumbs-up on message m1, when clicked, then POST /v1/messages/m1/feedback is sent with body `{score:1}` (vitest fake fetch).
- [ ] Given thumbs-down with comment 'wrong', when submitted, then the body is `{score:-1, comment:'wrong'}`.
- [ ] Given a 500/INTERNAL response, when received, then the button shows failed with Retry and no exception escapes.
- [ ] Given a message still streaming, when rendered, then feedback buttons are disabled.
