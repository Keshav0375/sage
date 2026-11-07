---
key: "E6-T14"
title: "Raw-text scan test across documents, chunks, events, BigQuery"
epic: "E6"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E6-T11", "E6-T13", "E6-T17"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.10", "deep-dive/05-data-model-and-storage.md#5.2", "decision-logs.md#adr-014"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Add a test that fails if raw document text exists anywhere except GCS bronze.

## Description
Plan E6 done-when: 'no raw document text exists outside GCS bronze (scan test of `documents`, `chunks`, events, BigQuery)'. Using the planted-PII manifest from E6-T3, run the full synthetic pipeline, then scan (a) every column of `documents`, `chunks`, `suitability_rules`, `ingest_rejects`, (b) every payload captured from pipeline topics, (c) the BigQuery tables fed by the pipeline (use the BQ emulator or recorded sink rows), for planted raw strings and for any substring of a bronze document body longer than a threshold. Also assert every Pandera failure in a seeded bad-input run has an `ingest_rejects` row. Out of scope: new product code, except fixing leaks found.

## Acceptance criteria
- [ ] Given the full pipeline run, when scanning all four stores, then 0 planted PII strings and 0 raw bronze substrings (>=40 chars) are found
- [ ] Given a deliberately leaky stub (test-only toggle writing raw text into an event), when scanned, then the test fails (negative control)
- [ ] Given a seeded bad-input run with N invalid rows, when finished, then `ingest_rejects` count for that run == N
