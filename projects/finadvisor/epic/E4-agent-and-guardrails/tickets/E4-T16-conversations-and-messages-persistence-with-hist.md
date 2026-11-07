---
key: "E4-T16"
title: "Conversations and messages persistence with history window"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T4", "E4-T8", "E1-T21"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#ADR-007", "deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 108, "id": 6155696659, "url": "https://github.com/Keshav0375/FinAdvisor/issues/108"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Persist conversations/messages and load the last 6 turns within 3k tokens.

## Description
Repository in src/agent (using E1 tables conversations and messages, monthly range partitions, columns incl. retrieval_degraded and citations (redacted)). Functions: create/get conversation (owner = principal), insert user message (redacted text only) and assistant message, load history = last HISTORY_MAX_TURNS turns trimmed to HISTORY_MAX_TOKENS (token count method documented), soft delete via DELETE /v1/conversations/{id} (204), GET /v1/conversations and /messages with cursor. All in short, tenant-scoped transactions. Stored text is the redacted text.

## Acceptance criteria
- [ ] Given 10 prior turns, when history loads, then at most 6 turns are returned and total tokens <= 3000 (test with a long-turn fixture).
- [ ] Given another advisor's conversation id, when GET messages, then 404/403 (RLS test).
- [ ] Given DELETE then GET, the conversation is excluded and returns 204 once.
- [ ] Given a user message containing PII, the stored content equals the redacted text (test).
