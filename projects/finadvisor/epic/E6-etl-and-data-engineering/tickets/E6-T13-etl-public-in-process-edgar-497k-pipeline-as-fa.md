---
key: "E6-T13"
title: "etl-public: in-process EDGAR 497K pipeline as fa_etl_public"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T10", "E6-T1", "E1-T8", "E1-T3", "E5-T15", "E6-T20"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/04-1-key-flows.md#4.14", "decision-logs.md#adr-014", "decision-logs.md#adr-028", "decision-logs.md#adr-026"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 146, "id": 6263502006, "url": "https://github.com/Keshav0375/FinAdvisor/issues/146"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Run all stages in-process for PUBLIC EDGAR 497K filings with the scan stage and atomic publish, and publish only analytics events.

## Description
Arch (4.8 `etl-public`; 4.7): 'runs every stage in-process and publishes only analytics topics (`ingest.analytics.v1`); the only writer of PUBLIC rows'; 'bumps the PUBLIC `corpus_version` itself'; 'worker consumers reject PUBLIC'. Build `jobs etl-public`: fetch 497K filings from EDGAR (declared User-Agent, under 10 req/s), bronze to `bronze/PUBLIC_TENANT_ID/{sha256}`, then call the same functions from E6-T5..T10 and E6-T20 in-process (no Kafka between stages), writing as DB role `fa_etl_public` with the PUBLIC tenant id. Round 4: the in-process path uses the SAME gates as the workers (4.25 scan stage; E6-T10 atomic publish with the ledger check, `contract_passed AND scan_passed`, corpus_version last), and the silver step writes under the versioned prefix and checks the ledger before and after writing. Publish only `ingest.analytics.v1` events (counts, durations, reject counts; no text, no `source='fca_api'`; FCA content never enters Kafka or BigQuery, ADR-026, ADR-013 amended). Real connectors (eCFR, EUR-Lex, SEC, FCA) are E11; this ticket covers the EDGAR 497K fixture path only. Out of scope: schema of `ingest.analytics.v1` beyond E5.

## Acceptance criteria
- [ ] Given fa_etl_public, when the job ingests a fixture 497K filing, then `documents` and `chunks` rows exist with the PUBLIC tenant id and PUBLIC `corpus_version` increased by 1 (integration).
- [ ] Given a fixture filing with an injected instruction-override phrase, when ingested, then the version is quarantined and no chunk exists (scan stage in the in-process path).
- [ ] Given a ledger tombstone for a PUBLIC document key, when the job reaches it, then nothing is written for it (guard applied in-process).
- [ ] Given role `fa_worker`, when it inserts a PUBLIC chunk, then the policy denies it; given a PUBLIC event published on `docs.bronze.v1`, a worker consumer sends it to `dlq.v1`.
- [ ] Given a run, when topics are inspected, then the only topic written is `ingest.analytics.v1` and no payload contains chunk text or the value `fca_api` (scan test).
