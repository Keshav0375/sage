---
key: "E6-T19"
title: "BigQuery tenant isolation and byte-cap acceptance test"
epic: "E6"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E6-T17"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.11", "deep-dive/05-data-model-and-storage.md#5.8"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Prove tenant views isolate rows and queries are capped.

## Description
Plan E6 done-when: 'BigQuery tables are day-partitioned, clustered by `tenant_id`, with `maximum_bytes_billed` set; a tenant's authorized view returns only that tenant's rows.' Add a test that provisions two tenants' views from E6-T17, inserts rows for both, and checks (1) tenant A's view never returns B's rows including via `SELECT *`, filters on B's id and a join on the base dataset (denied for tenant A's principal), (2) a deliberately large scan exceeding `BQ_MAX_BYTES_BILLED` is rejected with `bytesBilledLimitExceeded`, (3) table metadata partitioning and clustering. Runs in CI against the emulator, and a gated job against a real test project if the emulator cannot enforce authorized views (record which in the test docs).

## Acceptance criteria
- [ ] Tenant A principal selecting from tenant A's view returns 0 rows with tenant_id != A (assertion on result set)
- [ ] Tenant A principal querying the base table directly is denied (test)
- [ ] A query estimated above `BQ_MAX_BYTES_BILLED` fails with `bytesBilledLimitExceeded`
