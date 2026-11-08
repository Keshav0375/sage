---
key: "E11-T9"
title: "reconcile_lineage: idempotent version and chunk reconcile"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T5", "E6-T10", "E3-T4"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.16", "deep-dive/04-2-source-lifecycle-and-cells.md#4.17", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.10", "decision-logs.md#adr-27", "decision-logs.md#adr-28", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4 (#8, #11)"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 285, "id": 6263747404, "url": "https://github.com/Keshav0375/FinAdvisor/issues/285"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Implement the one function that reconciles late, out-of-order, withdrawn and replayed versions.

## Description
Implement `reconcile_lineage(document_id)` in `backend/src/lineage/reconcile.py`, called by the indexer (tenant path) and `etl-public` (PUBLIC path) so the two paths cannot drift.

Arch (4.16): input = every non-withdrawn, non-quarantined `document_versions` row of the document in `valid_range` order plus its silver Parquet. Output = the target chunk set keyed by chunk identity `(tenant_id, document_id, provision_path, chunk_index, chunk_hash, valid_from, parser_version, embed_model)`. Applied as a diff in ONE transaction under the document's advisory lock (`pg_advisory_xact_lock(hash(tenant_id, doc_id))`, lock order of 4.17: advisory lock first, tenant `corpus_version` row last): insert missing rows (embed only hashes with no vector for the active `embed_model`), extend `valid_range` where the same chunk hash continues into the next version (no embed call), close superseded rows (`valid_range` upper and `system_range` upper set, never overwritten), delete extras. Swap order: close old rows' `system_range`, then insert new ones. `valid_from` and `parser_version` are in the identity so a replay after a parser fix re-parses and A-B-A text is two rows with disjoint ranges. `valid_from_basis='observed'` for UK sources (observed date as `valid_from`).

Out of scope: the indexer's publish transaction steps around it (E6-T10), erasure (E12).

## Acceptance criteria
- [ ] Given versions v3, v1, v2 fed in all 6 permutations then the final valid-time line and chunk set hash are identical (#11; test `backend/tests/lineage/test_reconcile.py::test_all_permutations_identical`, PR).
- [ ] Given text A, then B, then A again then two A rows exist with disjoint `valid_range` and no unique violation (#8; test `test_aba_reversion_representable`, PR).
- [ ] Given `reconcile_lineage` run twice then the chunk-set hash equals a single run and zero embed calls are made on the second run (test `test_replay_twice_idempotent`).
- [ ] Given a parser bump then replay then no chunk of the old parse is retrievable by `search` and the old parse is closed in the same transaction as the new one is opened (#8; test `test_parser_bump_replay_no_old_chunks`, PR).
- [ ] Given an unchanged chunk hash across two versions then `valid_range` is extended and the embed client mock is not called (test `test_unchanged_chunk_extends_range_without_embed`).
