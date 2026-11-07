---
key: "E11-T20"
title: "fca_api connector: current text only"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T1", "E11-T6", "E11-T7", "E11-T9"]
arch_refs: ["deep-dive/11-tech-stack.md#source-connectors-r4", "deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "decision-logs.md#adr-26", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4 (#25)"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 270, "id": 6263710484, "url": "https://github.com/Keshav0375/FinAdvisor/issues/270"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Implement the FCA Handbook API connector, current text, PUBLIC tenant, in-process only.

## Description
Implement `fca_api` (PUBLIC only, class `fca_api`, erase on withdraw; `licence_class=ogl_fca`; `valid_from_basis='observed'`).

Arch: API with a free account login; current and future versions only; COBS 9A and 6; no Handbook crawling (module list only); weekly poll of listed modules by hash or last-modified, plus a manual monthly email check (documented in the runbook). Rate from the E11-T1 spike. FCA content lives only in the PUBLIC tenant and never enters Kafka or BigQuery: the connector runs in-process in `etl-public`; any ingest analytics carry source id, counts and opaque ids only, never text or titles. The suspend-on-401/403 rule is E11-T22.

Out of scope: purge and kill switch (E11-T22).

## Acceptance criteria
- [ ] Given the recorded fixture then `classify()` returns `valid_from_basis='observed'`, `licence_class=ogl_fca` and the FCA credit in `attribution_text` (test `backend/tests/connectors/test_fca_api.py::test_classify_observed_and_credit`).
- [ ] Given a full ingest of the fixture then no Kafka producer call and no BigQuery write is made for this source and no event payload contains chunk text or titles (test `test_fca_content_never_in_kafka_or_bigquery`, PR).
- [ ] Given a module not in the configured COBS list then it is not requested (test `test_no_handbook_crawl`).
- [ ] Given the target is not the PUBLIC tenant then the connector refuses to run (test `test_fca_public_tenant_only`).
