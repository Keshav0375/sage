---
key: "E6-T19"
title: "BigQuery isolation, byte-cap and time-travel acceptance test"
epic: "E6"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E6-T17"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.11", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.8", "decision-logs.md#adr-029"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Prove tenant views isolate rows, queries are capped and every dataset keeps 48 h max time travel.

## Description
Plan E6 done-when: 'BigQuery tables are day-partitioned, clustered by `tenant_id`, with `maximum_bytes_billed` set; a tenant's authorized view returns only that tenant's rows.' Round 4 (ADR-029 amended, R4-D18 V2): add the time-travel assertion. Add a test that provisions two tenants' views from E6-T17, inserts rows for both and checks (1) tenant A's view never returns B's rows including via `SELECT *`, filters on B's id and a join on the base dataset (denied for tenant A's principal), (2) a query exceeding `BQ_MAX_BYTES_BILLED` is rejected with `bytesBilledLimitExceeded`, (3) table metadata partitioning and clustering, (4) EVERY dataset in the project, including one created by a dbt run (E6-T18), reports `max_time_travel_hours = 48` from `INFORMATION_SCHEMA.SCHEMATA_OPTIONS`. Runs in CI against the emulator where it can, and as a gated job against a real test project for authorized views and item (4); the test docs record which.

## Acceptance criteria
- [ ] Tenant A principal selecting from tenant A's view returns 0 rows with tenant_id != A; querying the base table directly is denied.
- [ ] A query estimated above `BQ_MAX_BYTES_BILLED` fails with `bytesBilledLimitExceeded`.
- [ ] Given a dataset created by `dbt run` in the test project, when the options are read, then `max_time_travel_hours` is 48 for it and for every other dataset; a dataset at 168 h makes the test fail (test_every_dataset_48h).
