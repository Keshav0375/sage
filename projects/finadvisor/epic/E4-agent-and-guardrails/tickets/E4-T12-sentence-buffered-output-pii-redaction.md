---
key: "E4-T12"
title: "Sentence-buffered output PII redaction"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T8"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#ADR-009"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 104, "id": 6155691998, "url": "https://github.com/Keshav0375/FinAdvisor/issues/104"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Buffer streamed text to sentence boundaries and redact PII before emitting delta events.

## Description
In src/guardrails: wrap the LLM text stream; accumulate until a sentence boundary (or max buffer length to bound latency, config), run Presidio on the sentence (and restore pseudonym placeholders only if arch allows; default: leave redacted), then emit. Flush remaining buffer at end of stream. Must handle [n] markers split across chunks without breaking them. Quote ADR-009: 'sentence-buffered output PII redaction ... adds a small latency to first visible tokens'. Record the added first-delta latency in the PR.

## Acceptance criteria
- [ ] Given a stream chunked mid-sentence containing an email split across two chunks, when redacted, then no emitted delta contains the email in full or in part (test).
- [ ] Given a stream ending without a final period, when finished, then the remaining text is flushed (test).
- [ ] Given the marker '[1' and '2]' split across chunks, when processed, then the emitted text contains '[12]' unchanged or '[1]' per original (no corruption; parametrized test).
- [ ] Added latency before first delta is measured on a stub and reported; test fails if the buffer exceeds the configured max.
