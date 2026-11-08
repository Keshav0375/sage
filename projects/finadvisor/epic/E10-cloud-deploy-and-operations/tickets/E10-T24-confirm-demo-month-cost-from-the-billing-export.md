---
key: "E10-T24"
title: "Confirm demo month cost from the billing export"
epic: "E10"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E10-T21", "E10-T23", "E10-T3"]
arch_refs: ["deep-dive/02-quality-attributes.md#2.5", "ADR-020", "ADR-012"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 246, "id": 6263664042, "url": "https://github.com/Keshav0375/FinAdvisor/issues/246"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Read a demo month from the BigQuery billing export and check it is within 100-200 USD.

## Description
Epic done-when: 'Monthly cost for a demo month read from the billing export is within 100-200 USD (expected 110-160).' Budget table in 2.5: idle 40-55, demo month (~40 h up, ~2,000 chats) 110-160. Uses E10-T3 for idle line items and E10-T1 for Cloud SQL hours. E9 owns dashboards/alerts; this ticket produces a one-off report only.

Build: Terraform for the Cloud Billing export to BigQuery dataset if not present (enable detailed usage export, in the existing BigQuery dataset project), scripts/cost_report.py running a parameterised query for a month, grouped by service and SKU, with labels for Cloud SQL, Cloud Run, ALB, Cloud Armor, Memorystore, Confluent (via Marketplace/direct if visible), and summing. Compare against the 2.5 rows and BQ_MAX_BYTES_BILLED for the query itself. Write docs/adr/demo-month-cost.md with the table, hours up from the demo-up/demo-down logs (from Cloud Logging), chats count (from Langfuse or turns table) and verdict.

Precondition: a month of operation, or at least a ~40 h up window with ~2,000 chats; if not available the report extrapolates and says so.

## Acceptance criteria
- [ ] scripts/cost_report.py --month YYYY-MM prints per-service cost and a total and exits non-zero if total is outside 100-200 USD
- [ ] docs/adr/demo-month-cost.md lists Cloud SQL, Cloud Run, ALB, Cloud Armor, Memorystore, Confluent, LLM costs with amounts and the hours up taken from logs, plus a verdict against the 110-160 expected range
- [ ] The query runs with maximum_bytes_billed set to BQ_MAX_BYTES_BILLED (unit test asserts the job config)
