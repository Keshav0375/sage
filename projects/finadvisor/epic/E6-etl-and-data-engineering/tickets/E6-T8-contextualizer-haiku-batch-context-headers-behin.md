---
key: "E6-T8"
title: "contextualizer: Haiku headers (default off), guarded sink"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T7", "E5-T7", "E5-T9", "E5-T11", "E5-T15"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "decision-logs.md#adr-016", "decision-logs.md#adr-028", "decision-logs.md#adr-037"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Generate contextual headers via the Haiku Batch API only when CONTEXTUAL_RETRIEVAL_ENABLED is true (default false); otherwise keep the structural prefix.

## Description
Arch (4.7 `contextualizer`, ADR-016): 'Haiku 5.5 Batch API contextual headers (behind flag `CONTEXTUAL_RETRIEVAL_ENABLED`, default OFF: contextual retrieval is an ablation arm, ADR-016 amended)', model `LLM_MODEL_AUX` (claude-haiku-5-5), input redacted text only. Consume `docs.silver.v1`, read the silver Parquet, and emit `chunks.contextualized.v1` (ids, silver URI, no text). Round 4: with the flag false (the default) every child chunk KEEPS the free structural prefix (title plus section path, baseline B0, written by the E6-T5 chunker) as `context_header`, the stage passes through and makes ZERO Anthropic calls. With the flag true, submit one Batch per document (the prompt gets the redacted parent/section and the chunk), poll, and REPLACE the header on each child with the Haiku header (the structural prefix is the B0 arm's input, kept for the ablation); the flag may only be turned on after the ablation arm passes the ADR-037 line (E7), which this ticket does not enforce. Batch failures retry then DLQ. Suitability extraction is E6-T9.

Sink guard (ADR-028): before writing its output (the contextualized set and any `suitability_rules` handoff) it calls the E5-T15 uncached helper; a hit drops the message with reason `tombstoned`; an unreadable ledger pauses the worker. Out of scope: the L1 ablation that decides the flag (E7), suitability (E6-T9).

## Acceptance criteria
- [ ] Given the flag unset (default), when a silver message is consumed, then `chunks.contextualized.v1` is emitted, each child's context_header equals its structural prefix (title > section path) and the fake Anthropic client records 0 calls (test_flag_default_off_keeps_structural_prefix).
- [ ] Given the flag true, when consumed, then each child chunk has a non-empty Haiku header and the request used the Batch API with `claude-haiku-5-5`; the request payload contains only redacted chunk text (scan against the planted-PII manifest).
- [ ] Given a ledger tombstone for the document, when consumed, then nothing is written and no event is emitted (`tombstoned` counted); given an unreadable ledger, the offset is not committed.
- [ ] Given a failed batch, when retries are exhausted, then the message lands in `dlq.v1`.
