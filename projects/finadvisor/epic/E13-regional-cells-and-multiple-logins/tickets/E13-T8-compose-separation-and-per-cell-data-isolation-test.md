---
key: "E13-T8"
title: "Compose separation and per-cell data isolation tests"
epic: "E13"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E13-T6", "E13-T4"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.6", "decision-logs.md#adr-031"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 328, "id": 6263834370, "url": "https://github.com/Keshav0375/FinAdvisor/issues/328"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Tests prove a service in one cell cannot resolve the other cell's data services and that each cell holds only its own tenants.

## Description
Implements ADR-031 "Proved by": "Compose separation test (a service in one cell cannot resolve the other)" and "Each cell physically holds only its tenants ... Nothing is shared or replicated across cells" (04-2 §4.24, 07 §7.6: no Kafka links, no replication, no cross-region queries).

Add `tests/cells/test_separation.py` against the E13-T6 suite: from inside a cell-us container, DNS resolution and TCP connect to cell-eu's Postgres, Kafka and schema-registry hostnames fail (and the reverse). Add `test_isolation.py`: after seeding, the cell-us `tenants` table contains `alpha` and PUBLIC only and the cell-eu table contains `beta` and PUBLIC only; no row with the other cell's `tenant_id` exists in any tenant-scoped table (query by `information_schema` column `tenant_id`); no Kafka topic or message in one cluster carries the other cell's tenant id.

Out of scope: tenant move (E13-T13 to T16), manifests (E13-T9).

## Acceptance criteria
- [ ] Given the running suite, when a cell-us container resolves or connects to the cell-eu Postgres, Kafka or schema registry, then it fails, and the reverse also fails (`test_separation.py::test_no_cross_cell_resolution`).
- [ ] Given seeded tenants, then cell-us holds zero rows with `beta`'s `tenant_id` in every table that has a `tenant_id` column, and cell-eu holds zero rows with `alpha`'s (`test_isolation.py::test_rows_only_for_home_tenants`).
- [ ] Given chat traffic for both tenants, then a Kafka topic scan of each cell finds only its own tenant ids (`test_isolation.py::test_kafka_only_home_tenant`).
- [ ] A deliberately added shared network in a scratch copy of the compose file makes `test_no_cross_cell_resolution` fail (`test_separation.py::test_detects_shared_network`).
