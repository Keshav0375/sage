---
key: "E11-T26"
title: "First corpus, per-source fixtures and weekly live smoke"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T15", "E11-T16", "E11-T17", "E11-T18", "E11-T19", "E11-T20", "E11-T21", "E11-T13", "E11-T24"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "deep-dive/11-tech-stack.md#source-connectors-r4", "decision-logs.md#adr-26", "decision-logs.md#adr-27", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 276, "id": 6263724957, "url": "https://github.com/Keshav0375/FinAdvisor/issues/276"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Ingest the first real public set and private demo documents and add the weekly live source smoke.

## Description
Run the real ingest for the first corpus: the first public set (about 8-12 files, ESTIMATE, across US, EU and UK: eCFR 17 CFR 275 sections, EUR-Lex PRIIPs and MiFID, legislation.gov.uk items, FCA COBS modules) in PUBLIC, plus private demo documents in a firm tenant (`llm_egress_ack=true`). Record per-source fixtures for the PR gate (private demo fixtures stay out of the public repo). Add the weekly `live` smoke job (one item per connector, read-only, within the throttles) with a failure report; it is not in the PR gate. Add the Make targets `ingest-first-corpus` and `source-smoke`.

Out of scope: the 200-item golden set (E7), erasure (E12).

## Acceptance criteria
- [ ] Given the first-corpus run then `documents` and `document_versions` have rows for each of the three jurisdictions in PUBLIC and for the private demo documents only in the firm tenant (test `backend/tests/integration/test_first_corpus.py::test_jurisdictions_and_tenant_scope`, run on recorded fixtures in PR).
- [ ] Given every connector then its recorded-fixture suite passes in the PR gate (a CI job `connectors-fixtures` is green).
- [ ] Given `make source-smoke` against live sources then each connector fetches one item within its throttle and the job exits non-zero on any failure (checked weekly; test `test_source_smoke_exit_codes` uses stubs in PR).
- [ ] Given a search for a known eCFR section as of today then it is returned with its attribution text (test `test_first_corpus_known_section_retrievable`).
