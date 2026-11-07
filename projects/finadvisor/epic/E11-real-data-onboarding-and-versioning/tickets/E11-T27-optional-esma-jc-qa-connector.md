---
key: "E11-T27"
title: "Optional ESMA / JC Q&A connector with disclaimer"
epic: "E11"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E11-T6", "E11-T7", "E11-T10"]
arch_refs: ["deep-dive/11-tech-stack.md#source-connectors-r4", "deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "deep-dive/06-interfaces-and-contracts.md#6.7", "decision-logs.md#adr-26"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 277, "id": 6263725917, "url": "https://github.com/Keshav0375/FinAdvisor/issues/277"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add the optional ESMA Q&A connector with the transformed-text disclaimer.

## Description
Optional (arch: "ESMA / JC Q&A is an optional seventh"). Implement `esma_qa` (PUBLIC, class `qa`, retire; `licence_class=esma_transformed`). Arch: PDF and HTML Q&A tool; no rate number found (use the default conservative throttle of 1 rps, config); weekly hash of the news page and PDFs; delete signal is "Deleted" in the changes overview plus a curated `withdrawals.yaml` in the repo, human reviewed. Transformed text must carry "drafted using material downloaded from ESMA's website" and a non-endorsement in `attribution_text`. Build only if the epic owner enables it (`ESMA_QA_ENABLED`, default false).

## Acceptance criteria
- [ ] Given `ESMA_QA_ENABLED=false` then the connector is not registered (test `backend/tests/connectors/test_esma_qa.py::test_disabled_by_default`).
- [ ] Given the recorded fixture then `classify()` returns `licence_class=esma_transformed` and `attribution_text` contains both required phrases (test `test_attribution_disclaimer_present`).
- [ ] Given a `withdrawals.yaml` entry then the matching item is a withdrawal candidate subject to the two-strike rule (test `test_withdrawals_yaml_signal`).
