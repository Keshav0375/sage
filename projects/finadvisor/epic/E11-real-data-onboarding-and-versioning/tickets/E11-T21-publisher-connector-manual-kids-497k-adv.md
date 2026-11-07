---
key: "E11-T21"
title: "publisher connector: manual KIDs, 497K and ADV"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T6", "E11-T7", "E11-T14", "E11-T11"]
arch_refs: ["deep-dive/11-tech-stack.md#source-connectors-r4", "deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "deep-dive/06-interfaces-and-contracts.md#6.8", "decision-logs.md#adr-26", "decision-logs.md#adr-38"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Ingest manually fetched publisher documents into a firm tenant as private_demo.

## Description
Implement `publisher` (firm tenant only, class `publisher`, erase on withdraw, `licence_class=publisher`): documents placed manually (KIDs, 497K, ADV brochures) into a configured drop location; `list()` enumerates the drop; no incremental feed; withdrawal is an operator `erase` action only (calls the E11-T10 handler); no backstop listing. `private_demo`: bronze goes to the firm tenant's private bucket only, never to the public repo or a public eval set; the E11-T14 egress check runs first. Operator supplies `valid_from` ("accurate as at" for a KID, filing date) at drop time, `valid_from_basis='source'`.

Counsel's view on publisher documents is an open question for Keshav, not engineering (plan); this ticket adds no legal text.

Out of scope: licence footer rendering (E4).

## Acceptance criteria
- [ ] Given a dropped KID fixture then an observation and a bronze object in the firm tenant's bucket exist and `document_versions.valid_range` starts at the operator-supplied date (test `backend/tests/connectors/test_publisher.py::test_drop_creates_private_version`).
- [ ] Given the same file dropped twice then one version (test `test_same_file_noop`).
- [ ] Given the file is placed in a path under the public repo or public eval folder then ingest refuses it (test `test_refuses_public_paths`).
- [ ] Given an operator `erase` then a deletion enqueue is made and no data is silently retained as retired (test `test_operator_erase_enqueues_deletion`).
