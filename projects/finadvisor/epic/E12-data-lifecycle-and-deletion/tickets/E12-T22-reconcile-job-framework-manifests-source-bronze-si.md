---
key: "E12-T22"
title: "reconcile job: framework, manifests, source-bronze-silver-chunks"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T6", "E6-T4", "E6-T10"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.22", "deep-dive/09-observability.md#9.7", "decision-logs.md#adr-34", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.12"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Run hourly reconcile for source to bronze, bronze to silver and silver to chunks with parser_version keyed manifests.

## Description
Job `reconcile` (hourly only while the system runs; compares only versions idle more than `RECONCILE_MIN_IDLE_MIN` = 30). Pairs: (1) source to bronze: every `present` observation has a GCS object whose `sha256` object metadata equals the observation (ticket after 2 runs); (2) bronze to silver: `n_chunks` and `chunk_set_hash = sha256(sorted(chunk_hash))` per version; (3) silver to Postgres: same count and hash recomputed from `chunks`, and every child has an embedding for the active `embed_model` (ticket). Persist manifests in `reconciliation_manifests` keyed on `parser_version`; exact equality, no tolerance; a difference writes a `reconciliation_findings` row (pair, detail, status) and emits the alert metric; a `parser_version` bump creates a new baseline and one planned re-baseline event, not findings. A stopped system raises nothing; the first run at start catches up. Out of scope: the other pairs (E12-T23), the cell-versus-cell pair (E13).

## Acceptance criteria
- [ ] Given fixtures where all three pairs agree, when reconcile runs, then no findings are written and manifests exist for each hop.
- [ ] Given a planted difference per pair (a missing bronze object, a changed `n_chunks` in silver, a deleted child chunk), when reconcile runs, then each yields exactly one finding naming its pair.
- [ ] Given a parser bump and replay of the fixture corpus, when reconcile runs, then old-parser manifests are not compared with new ones and zero findings are raised (re-baseline).
- [ ] Given a version modified 10 min ago, then it is skipped; at 31 min it is compared.
- [ ] Given a source-to-bronze mismatch persisting for 2 runs, then the ticket alert metric fires on the second run, not the first.
