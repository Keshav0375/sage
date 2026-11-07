---
key: "E13-T10"
title: "PUBLIC manifest comparison and drift alert"
epic: "E13"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E13-T9", "E12-T22"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.22", "deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "decision-logs.md#adr-031"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 315, "id": 6263814052, "url": "https://github.com/Keshav0375/FinAdvisor/issues/315"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The `reconcile` job compares PUBLIC manifests across cells and raises a ticket-level alert on any difference.

## Description
Implements the reconcile row "cell to cell | PUBLIC manifest (document count + `chunk_set_hash` per version) equal across cells | ticket" (04-2 §4.22), the cell-versus-cell pair of the E12 reconcile job. Depends on the E12 reconcile job (epic key E12 until exact ticket keys are set).

Add the pair `cell_to_cell` to the `reconcile` job: it fetches both cells' manifests (E13-T9) from their GCS buckets (the manifest hashes are declared global data, ADR-031), compares per `(doc_key, version)` and by `parser_version`, and emits the alert `public_manifest_drift` listing the first differing keys. Manifests with different `parser_version` are reported as a planned re-baseline, not an alert.

Out of scope: auto-repair, copying data between cells.

## Acceptance criteria
- [ ] Given equal manifests, when the pair runs, then it passes and emits no alert (`test_reconcile_cells.py::test_equal_passes`).
- [ ] Given one chunk deliberately altered in cell-eu PUBLIC, when the pair runs, then `public_manifest_drift` fires naming the differing version (`test_reconcile_cells.py::test_planted_difference_alerts`).
- [ ] Given a missing document in one cell, then the alert fires with the count difference (`test_reconcile_cells.py::test_missing_document`).
- [ ] Given different `parser_version` values, then no alert and a re-baseline event is logged (`test_reconcile_cells.py::test_parser_bump_rebaseline`).
