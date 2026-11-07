---
key: "E6-T13"
title: "etl-public: in-process EDGAR 497K pipeline as fa_etl_public"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T10", "E6-T1", "E1-T8", "E1-T3"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/04-components-and-responsibilities.md#4.14", "deep-dive/04-components-and-responsibilities.md#4.7", "decision-logs.md#adr-014"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Run all stages in-process for PUBLIC EDGAR 497K filings and publish only analytics events.

## Description
Arch (4.8 `etl-public`; Flow 2 notes; 4.7): 'runs every stage in-process and publishes only analytics topics (`ingest.analytics.v1`); the only writer of PUBLIC rows'; 'bumps the PUBLIC `corpus_version` itself'; 'worker consumers reject PUBLIC'. Build `jobs etl-public`: fetch 497K filings from EDGAR (declared User-Agent, rate limit under 10 req/s per SEC rules), bronze to `bronze/PUBLIC_TENANT_ID/{sha256}`, then call the same transform/validation/contextualize/embed functions from E6-T5..T10 in-process (no Kafka between stages), writing as DB role `fa_etl_public` with the PUBLIC tenant id, then bump PUBLIC `corpus_version`. Publish only `ingest.analytics.v1` events (counts, durations, reject counts; no text). Apply Docling decisions from docs/adr/docling-497k.md. Out of scope: schema of `ingest.analytics.v1` beyond what E5 defines (see questions).

## Acceptance criteria
- [ ] Given fa_etl_public, when the job ingests a fixture 497K filing, then `documents` and `chunks` rows exist with PUBLIC tenant id and PUBLIC `corpus_version` increased by 1 (integration)
- [ ] Given role `fa_worker`, when it inserts a PUBLIC chunk, then the policy denies it (test)
- [ ] Given a PUBLIC event published on `docs.bronze.v1`, when a worker consumer receives it, then it is sent to `dlq.v1` (test)
- [ ] Given a run, when topics are inspected, then the only topic written is `ingest.analytics.v1` and no payload contains chunk text (scan test)
