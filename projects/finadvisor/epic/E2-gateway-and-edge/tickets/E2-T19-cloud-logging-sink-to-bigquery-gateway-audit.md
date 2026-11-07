---
key: "E2-T19"
title: "Cloud Logging sink to BigQuery gateway_audit"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T15", "E2-T5"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.3", "deep-dive/04-components-and-responsibilities.md#4.11", "decision-logs.md#adr-023"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 57, "id": 6155638558, "url": "https://github.com/Keshav0375/FinAdvisor/issues/57"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Route the whitelisted Kong audit lines into a partitioned BigQuery table.

## Description
ADR-023 and deep-dive/04-components-and-responsibilities.md §4.3 / 4.11. Quote: 'A Cloud Logging sink exports to BigQuery gateway_audit. The /internal/audit/gateway route and the gateway.audit.v1 topic do not exist.' In terraform/edge/: dataset gateway_audit, a google_logging_project_sink with a filter selecting fa-gateway Cloud Run audit JSON lines (exclude Kong's stderr text), unique writer identity with BigQuery data editor on the dataset, partitioned tables (day-partitioned on timestamp). Columns are exactly the whitelist from E2-T15. No tenant column (Kong cannot see it). Fixes G-48. Out of scope: marts, authorized views (E5/E9).

## Acceptance criteria
- [ ] Given traffic through the deployed gateway including a sentinel bearer and query string, when queried 5 minutes later, then `SELECT COUNT(*) FROM gateway_audit.*` for the test request ids returns the number of requests sent.
- [ ] Given the table schema, then its column names equal the E2-T15 whitelist exactly and `SELECT COUNT(*) WHERE TO_JSON_STRING(t) LIKE '%SENTINEL%'` returns 0 (test script tests/gateway/test_audit_sink.sh).
- [ ] Given `terraform validate`, then it exits 0, and the table is day-partitioned (bq show output asserted).
