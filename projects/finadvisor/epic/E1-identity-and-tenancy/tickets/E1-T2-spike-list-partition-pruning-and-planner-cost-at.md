---
key: "E1-T2"
title: "Spike: LIST-partition pruning and planner cost at 52 partitions"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.5", "deep-dive/05-data-model-and-storage.md#5.4", "decision-logs.md#adr-003"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 18, "id": 6155589772, "url": "https://github.com/Keshav0375/FinAdvisor/issues/18"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Partition pruning under the RLS current_setting policy and planning/query cost at about 52 chunks partitions are measured and recorded as an ADR.

## Description
Spike. ADR-003: "Runtime pruning with the RLS `current_setting` policy confirmed by test on the 8-partition setup ("Subplans Removed: 6 of 8") ... planner and migration cost at ~50 partitions is unmeasured (E1 measures it); the pruning test must be repeated on LIST partitions." Scope line: "LIST-partition pruning with the RLS `current_setting` policy plus planner cost at ~52 partitions."

Build `backend/scripts/spikes/list_partition_probe.py` (throwaway, uses the `pgvector/pgvector:0.8.5-pg16` image from E0 compose/CI):
1. Create a scratch database and a `chunks` table `PARTITION BY LIST (tenant_id)` with 50 tenant partitions, 1 PUBLIC partition and 1 DEFAULT partition (52 total), columns reduced to those needed: `tenant_id, id, kind, content, tsv, embedding halfvec(1024), tier_required, jurisdiction`, with the per-partition indexes declared on the parent exactly as in deep-dive/05-data-model-and-storage.md §5.5 (HNSW `halfvec_cosine_ops` m=16 ef_construction=64 partial `WHERE kind='child'`, GIN on tsv, btrees).
2. Enable `ENABLE` + `FORCE ROW LEVEL SECURITY` and the `chunks_select_app` policy text from deep-dive/05-data-model-and-storage.md §5.4 (own tenant OR PUBLIC, tier, jurisdiction) for a non-owner NOBYPASSRLS role; seed 200 child chunks per partition with random embeddings.
3. As that role, in a transaction with `set_config('app.tenant_id', ..., true)` etc., run the dense leg and the FTS leg of the deep-dive/05-data-model-and-storage.md §5.6 hybrid statement with `SET LOCAL hnsw.iterative_scan = relaxed_order` and `EXPLAIN (ANALYZE, VERBOSE)`; capture which partitions executed vs "never executed"/removed, planning time and execution time over 200 runs; repeat for 2, 8 and 52 partitions to show the trend.
4. Measure the wall time to create one partition with its indexes (the onboarding cost).

Record the result as `docs/adr/list-partition-pruning.md` in this repo (the researcher copies it into `arch/decision-logs.md` as the next ADR number after merge; do not write to the harness repo) with the numbers, the EXPLAIN excerpt, the fallback taken if a check failed, and a keep / change decision on LIST partitions.

Out of scope: production migrations (E1-T5), tuning HNSW parameters.

## Acceptance criteria
- [ ] Given 52 partitions and the RLS policy, when the probe runs `EXPLAIN (ANALYZE)` on the dense leg for one tenant, then no partition other than the caller's tenant partition, the PUBLIC partition and the DEFAULT partition is executed; the script exits non-zero otherwise and prints the 'Subplans Removed' value.
- [ ] The probe's p95 of planning time + execution time over 200 runs of the hybrid statement at 52 partitions is <= 100 ms (the ADR-003 revisit trigger) and the planning-time p95 alone is <= 10 ms; the script exits non-zero if either is exceeded and prints both measured p95 values.
- [ ] `docs/adr/list-partition-pruning.md` exists and contains a table of planning time p50/p95 for 2, 8 and 52 partitions and the measured time to create one partition with indexes.
- [ ] The ADR ends with an explicit decision line (keep LIST partitions, or change with the reason); if the 52-partition check failed, the line names the fallback.
