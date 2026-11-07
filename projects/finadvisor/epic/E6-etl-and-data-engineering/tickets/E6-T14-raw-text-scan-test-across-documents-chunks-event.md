---
key: "E6-T14"
title: "Raw-text scan test across documents, chunks, events, BigQuery"
epic: "E6"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E6-T11", "E6-T13", "E6-T17"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.10", "deep-dive/05-data-model-and-storage.md#5.2", "decision-logs.md#adr-014", "decision-logs.md#adr-013", "decision-logs.md#adr-026"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add a test that fails if raw document text, FCA content or answer text exists anywhere except GCS bronze and Postgres messages.

## Description
Plan E6 done-when: 'no raw document text exists outside GCS bronze (scan test of `documents`, `chunks`, events, BigQuery)'. Using the planted-PII manifest from E6-T3, run the full synthetic pipeline, then scan (a) every column of `documents`, `chunks`, `suitability_rules`, `ingest_rejects`, (b) every payload captured from pipeline topics, (c) the BigQuery tables fed by the pipeline (emulator or recorded sink rows) for planted raw strings and any substring of a bronze body longer than a threshold. Round 4 additions (test #15, ADR-013 amended, ADR-026, R4-D19 M5): (d) plant a document with `source='fca_api'` and a marker string via a test-only fixture: the marker and the value `fca_api` appear in no Kafka payload and no BigQuery row; (e) run a chat turn with a planted answer sentence and excerpt: no `chat.audit`, `eval.sample` or BigQuery chat row contains them (they exist only in Postgres `messages`). Also assert every Pandera failure in a seeded bad-input run has an `ingest_rejects` row. Out of scope: new product code, except fixing leaks.

## Acceptance criteria
- [ ] Given the full pipeline run, when scanning all four stores, then 0 planted PII strings and 0 raw bronze substrings (>=40 chars) are found.
- [ ] Given the `fca_api` planted document, when the pipeline and the sinks run, then 0 Kafka payloads and 0 BigQuery rows contain its marker or the value `fca_api` (test_fca_never_in_kafka_or_bigquery).
- [ ] Given a planted answer sentence and excerpt in a chat turn, when scanning outbox rows, Kafka captures and BigQuery chat tables, then 0 matches, and `messages` holds the redacted answer.
- [ ] Given a deliberately leaky stub (test-only toggle writing raw text into an event), when scanned, then the test fails (negative control); given N invalid rows seeded, `ingest_rejects` count for the run == N.
