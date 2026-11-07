---
key: "E4-T25"
title: "Leak tests: PII never reaches Voyage, Anthropic, logs, Langfuse"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T19", "E4-T21"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.1", "decision-logs.md#ADR-009"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 131, "id": 6263473652, "url": "https://github.com/Keshav0375/FinAdvisor/issues/131"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
End-to-end test that injected PII is absent from every outbound call, log line and trace.

## Description
Integration test: run the full orchestrator with stubs capturing (a) Voyage embed and rerank request bodies, (b) Anthropic requests incl. aux condensation, (c) Model Armor request, (d) captured log records and OTel/Langfuse span attributes, (e) outbox payloads and turn_events. Inject PII (email, phone, name, account number) in the question and in history. Assert none of the raw values appear anywhere; also assert client SSE events contain no tool payloads or exception text across all event types. Ensure Langfuse masking is wired if LANGFUSE_ENABLED (mask before export).

## Acceptance criteria
- [ ] Given PII in the question, when a turn runs, then a scan of all captured outbound bodies, logs, spans and outbox rows finds zero occurrences of the raw values (test fails if one leaks).
- [ ] Given a poisoned tool exception text, the full SSE capture contains no part of it.
- [ ] Given LANGFUSE_ENABLED=true with a capture exporter, span attributes contain redacted text only.
