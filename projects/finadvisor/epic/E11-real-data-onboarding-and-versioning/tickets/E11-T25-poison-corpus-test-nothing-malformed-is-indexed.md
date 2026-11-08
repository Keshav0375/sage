---
key: "E11-T25"
title: "Poison corpus test: nothing malformed is indexed"
epic: "E11"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E11-T11", "E11-T13", "E11-T12", "E6-T10"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.25", "deep-dive/06-interfaces-and-contracts.md#6.8", "decision-logs.md#adr-36", "decision-logs.md#adr-34", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4 (#5)"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 275, "id": 6263724040, "url": "https://github.com/Keshav0375/FinAdvisor/issues/275"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Prove malformed, oversized and injection documents are quarantined or dead-lettered and consumers continue.

## Description
Build the poison corpus and the end-to-end test. The corpus holds malformed HTML and PDF, oversized files (over the 4 MB window cap), injection payloads (instruction-override phrases, role markers, tool-call syntax, hidden and zero-width text, long base64) and a stub `EXECUTION_SKIPPED` result. Arch: none may be indexed; all end in quarantine or the DLQ (a parse crash goes to the DLQ via E5-T8), and consumers continue with the next message. Corpus files are synthetic and live in the repo test fixtures.

Out of scope: the guardrail attack-success-rate sets (E7).

## Acceptance criteria
- [ ] Given the poison corpus then zero `chunks` rows exist for any of its documents after the pipeline runs (test `backend/tests/integration/test_poison_corpus.py::test_nothing_indexed`, PR).
- [ ] Given each poison document then it is in `quarantine/` with status `quarantined` or has a DLQ record, and the count of both equals the corpus size (test `test_all_quarantined_or_dlq`).
- [ ] Given a clean document placed after the poison documents in the same batch then it is indexed (consumers continue; test `test_clean_document_after_poison_is_indexed`).
