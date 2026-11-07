---
key: "E13-T9"
title: "Per-cell etl-public ingest and PUBLIC manifest"
epic: "E13"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E13-T6", "E6-T13"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "deep-dive/04-2-source-lifecycle-and-cells.md#4.22", "decision-logs.md#adr-031"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Each cell ingests PUBLIC on its own and publishes a manifest of document count and `chunk_set_hash` per version.

## Description
Implements: "PUBLIC is ingested independently per cell by its own `etl-public` ... No Kafka links, no replication, no cross-region queries" (04-2 §4.24) and ADR-031: "a manifest (document count and `chunk_set_hash` per version) alerts on drift". `chunk_set_hash = sha256(sorted(chunk_hash))` per version (04-2 §4.22).

Run `etl-public` (E6-T13) in each compose cell from the same fixtures, with its own embeddings. Add `backend/app/cells/manifest.py`: `build_manifest(conn)` reads the PUBLIC tenant's `documents`/`document_versions`/`chunks` and returns `{cell_id, parser_version, documents:int, versions:[{doc_key, version, n_chunks, chunk_set_hash}]}`; keyed on `parser_version` (a parser bump is a planned re-baseline, not drift, per 04-2 §4.22); only versions idle more than 30 minutes. Expose it as job `public-manifest` writing the JSON to the cell's GCS bucket (fake GCS in compose) and as a read-only CLI. Each cell reads only its own data.

Out of scope: comparison and alerting (E13-T10), the hourly reconcile scheduling (E12).

## Acceptance criteria
- [ ] Given the same fixture corpus ingested in both compose cells, when `public-manifest` runs in each, then the two manifests are equal (`test_manifest.py::test_equal_across_cells`).
- [ ] Given a version idle less than 30 minutes, then it is absent from the manifest (`test_manifest.py::test_idle_filter`).
- [ ] Given `chunk_set_hash`, then it equals `sha256` of the sorted chunk hashes recomputed independently in the test (`test_manifest.py::test_hash_definition`).
- [ ] Given the manifest job, then it opens no connection to the other cell (checked with the E13-T8 network fixture) (`test_manifest.py::test_no_cross_cell_access`).
