---
key: "E8-T8"
title: "Add conversation history list, load and delete"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T7"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/04-components-and-responsibilities.md#4.4"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 205, "id": 6263596265, "url": "https://github.com/Keshav0375/FinAdvisor/issues/205"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
An advisor can list, reopen and delete their own conversations.

## Description
Implements deep-dive/06-interfaces-and-contracts.md §6.1: `GET /v1/conversations?cursor`, `GET /v1/conversations/{id}/messages?cursor` (messages with citations, redacted), `DELETE /v1/conversations/{id}` (204). Sidebar list with cursor 'load more'; selecting loads messages (rendered with E8-T7 including citations and stale badges, and the stored retrieval_degraded notice if the response includes it; if the response shape lacks it, see questions); new chat button; delete with confirm, removes from list and clears view if active. Subsequent sends in an opened conversation pass its `conversation_id`. Empty and error states use E8-T4. Out of scope: search, rename, escalations list.

## Acceptance criteria
- [ ] Given a mocked first page with next cursor, when 'load more' is clicked, then the request carries `?cursor=<value>` and rows append (vitest).
- [ ] Given a conversation is selected, when messages load, then citations render under the assistant message.
- [ ] Given delete is confirmed and the API returns 204, when processed, then the row disappears; given it returns 403, then the row stays and the code-keyed error shows.
- [ ] Given an opened conversation, when a message is sent, then the POST body contains that conversation_id.
