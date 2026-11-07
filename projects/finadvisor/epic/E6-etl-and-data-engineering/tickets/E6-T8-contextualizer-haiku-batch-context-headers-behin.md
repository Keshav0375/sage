---
key: "E6-T8"
title: "contextualizer: Haiku batch context headers behind a flag"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T7", "E5-T7", "E5-T9", "E5-T11"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "decision-logs.md#adr-016"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Generate contextual headers for chunks via the Haiku Batch API when CONTEXTUAL_RETRIEVAL_ENABLED is true.

## Description
Arch (4.7 `contextualizer`, ADR-016): 'Haiku 5.5 Batch API contextual headers (behind flag `CONTEXTUAL_RETRIEVAL_ENABLED`)', model `LLM_MODEL_AUX` (claude-haiku-5-5), input is redacted text only. Consume `docs.silver.v1`, read the silver Parquet, submit one Batch per document (the header prompt gets the redacted parent/section and the chunk), poll the batch, fill `context_header` on each child, emit `chunks.contextualized.v1` (ids, silver URI, no text). When the flag is false, pass chunks through with `context_header` NULL and make zero Anthropic calls. Header changes alter the text feeding `tsv`, but the embedding input and `chunk_hash` rules stay as the indexer defines (E6-T10). Batch failures retry then DLQ. Out of scope: suitability extraction (E6-T9), the L1 ablation that decides the flag default (E3-T16).

## Acceptance criteria
- [ ] Given the flag false, when a silver message is consumed, then `chunks.contextualized.v1` is emitted with null headers and the fake Anthropic client records 0 calls (test)
- [ ] Given the flag true, when consumed, then each child chunk has a non-empty header and the request used the Batch API with `claude-haiku-5-5` (test on the fake client)
- [ ] Given a request payload, when inspected, then it contains only redacted chunk text (scan test against planted PII manifest)
- [ ] Given a failed batch, when retries are exhausted, then the message lands in `dlq.v1` (test)
