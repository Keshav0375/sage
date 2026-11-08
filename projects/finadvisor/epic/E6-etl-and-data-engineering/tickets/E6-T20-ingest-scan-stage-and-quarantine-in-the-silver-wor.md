---
key: "E6-T20"
title: "Ingest scan stage and quarantine in the silver worker"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T7", "E11-T5"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.25", "deep-dive/04-components-and-responsibilities.md#4.7", "decision-logs.md#adr-036", "decision-logs.md#adr-034"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 154, "id": 6263514178, "url": "https://github.com/Keshav0375/FinAdvisor/issues/154"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add the parse-time sanitiser and deterministic pattern list to the silver worker and quarantine a failing version before anything reaches silver.

## Description
Implement the scan stage of 4.25 as a hook in the E6-T7 handler (in-process in `etl-public` for PUBLIC, E6-T13). Quote 4.25: 'Parse-time sanitiser: drop script and style, comments, hidden or off-screen text, zero-width and bidi characters, long base64 runs; keep a per-document diff count. Deterministic pattern list: instruction-override phrases, role markers, tool-call syntax, URLs outside an allow-list. ... Any failure: version `status = quarantined`, bytes under `quarantine/`, never silver, never chunks.' Sanitiser output replaces the parsed text; a diff count is stored. The pattern list is a versioned data file `etl/silver/scan_patterns.yaml`; the URL allow-list is a setting. A pattern hit or a sanitiser hard failure sets the `document_versions` row `status='quarantined'` and `scan_passed=false`, copies the bronze bytes to `quarantine/tenant_id=/doc_id=/version=/` in the data bucket, writes NOTHING to silver and creates no chunks, emits no `docs.silver.v1`, and the consumer continues with the next message. A pass sets `scan_passed=true`. Model Armor document screening (fail closed) is added to this stage by E11-T13; operator `release` and `reject` are E11-T12; the contract checks are E11-T11. Out of scope: classifier arms (ablation only).

## Acceptance criteria
- [ ] Given a document with hidden text, zero-width characters and a script block, when scanned, then the sanitised text contains none of them and the diff count equals the number removed (unit test).
- [ ] Given a document containing an instruction-override phrase from the pattern list, when consumed by the silver worker, then the version is `quarantined` with scan_passed=false, the bytes exist under `quarantine/`, no silver object and no chunk exist, and the next message in the partition is processed (test_injected_document_quarantined).
- [ ] Given a clean document, when consumed, then scan_passed=true and processing continues unchanged.
- [ ] Given a URL outside the allow-list in the text, when scanned, then it is a pattern hit; given an allow-listed URL, it passes (parametrised test).
