---
key: "E11-T11"
title: "Boundary contracts and blocking rules"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T5", "E11-T6", "E6-T6"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.8", "deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "decision-logs.md#adr-34", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4 (#5, #28)"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 260, "id": 6263691828, "url": "https://github.com/Keshav0375/FinAdvisor/issues/260"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Implement the blocking contract rules and set failing versions to quarantined.

## Description
Implement `contracts.check(version, parsed, scan_result)` as a stage between bronze and silver/indexer, returning pass or a list of violations. A failure sets `document_versions.status='quarantined'`, `contract_passed=false`, `quarantine_reason`, moves bytes under `quarantine/` in GCS, and never writes silver or chunks.

Blocking rules (6.8): `licence_class` and `attribution_text` non-null; jurisdiction and tier non-null; eCFR part has the expected section ids; every CELEX arrives with all three languages or none; every 497K has a recognisable fee table or is `parse_incomplete`; chunk token bounds; non-empty `provision_path`; ingest scan passed. A 200 response with an HTML error page fails the contract. Pandera depth `SCHEMA_AND_DATA` is set explicitly (E6-T6). The indexer's atomic gate (ADR-028) remains the control; Dagster checks are advisory.

Out of scope: operator release/reject and the 5% batch circuit (E11-T12).

## Acceptance criteria
- [ ] Given a fixture version with null `licence_class` (and separately null `attribution_text`, null jurisdiction, empty `provision_path`) then each is quarantined with the matching `quarantine_reason` (parametrized `backend/tests/contracts/test_blocking_rules.py::test_rule_violation_quarantines`).
- [ ] Given a CELEX set with EN and DE but no FR then the set is quarantined; with all three or none it passes (test `test_celex_all_three_languages_or_none`).
- [ ] Given an HTTP 200 body that is an HTML error page then the version is quarantined and no silver object exists (#5; test `test_html_error_page_fails_contract`, PR).
- [ ] Given a planted bad row in silver then Pandera fails at `SCHEMA_AND_DATA` depth (#28; test `test_planted_bad_row_fails`, PR).
