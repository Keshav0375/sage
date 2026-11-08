---
key: "E13-T14"
title: "move-tenant: ordered Postgres copy and hash verify"
epic: "E13"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E13-T13", "E13-T6", "E1-T5", "E1-T6", "E1-T7"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.6", "decision-logs.md#adr-033"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 319, "id": 6263818763, "url": "https://github.com/Keshav0375/FinAdvisor/issues/319"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The tenant's Postgres rows are copied table by table into the target cell and verified by counts and per-table md5 hashes.

## Description
Implements ADR-033: "Copy: ordered per-table `COPY` of the tenant's rows (same `tenant_id`, embeddings as-is, same `embed_model`) ... Verify: row counts and `md5(string_agg(id||hash ORDER BY id))` per table equal."

In the `copying` and `verifying` steps of E13-T13: derive the table list and the FK-safe order from the schema (`information_schema` plus FK graph; parents before children, covering every table with a `tenant_id`, including partitioned content tables, conversations, messages, `outbox`, and the tenant's `advisors`/`tenants` rows), `COPY ... TO STDOUT` from the source filtered by `tenant_id` and `COPY FROM STDIN` into the target as the job role. Embeddings are copied as stored; the target `embed_model` must equal the source's or the job fails before copying. `verifying` computes `count(*)` and `md5(string_agg(id||hash ORDER BY id))` per table on both sides (tables without a `hash` column use the table's natural content hash column named in a per-table map kept in code, with a test that every tenant table is mapped) and requires equality. A missing table mapping or mismatch triggers E13-T13 rollback.

Out of scope: GCS and BigQuery (E13-T15), cutover (E13-T16).

## Acceptance criteria
- [ ] Given a seeded source tenant in compose, when a move reaches `verifying`, then every tenant-scoped table has equal counts and equal md5 on source and target (`test_move_copy.py::test_counts_and_hashes_equal`, #18 success path).
- [ ] Given the list of tables with a `tenant_id` column, then each has an entry in the copy order and the hash map (`test_move_copy.py::test_every_tenant_table_covered`).
- [ ] Given a source and target with different `embed_model`, then the job fails before copying any row and the target stays empty (`test_move_copy.py::test_embed_model_mismatch`).
- [ ] Given one target row altered after the copy, then `verifying` fails and rollback empties the target (`test_move_copy.py::test_verify_detects_difference`).
