---
key: "E3-T16"
title: "Retrieval benchmark and rerank ablation on 10k chunks"
epic: "E3"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E3-T1", "E3-T2", "E3-T9"]
arch_refs: ["deep-dive/02-quality-attributes.md#2.1", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.6", "decision-logs.md#adr-008", "decision-logs.md#adr-037", "decision-logs.md#adr-039", "deep-dive/06-interfaces-and-contracts.md#6.6"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 76, "id": 6155660458, "url": "https://github.com/Keshav0375/FinAdvisor/issues/76"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Measure first-stage and rerank p95 against the latency targets on the synthetic corpus, run the rerank on/off ablation, and record the ADR.

## Description
Add `backend/scripts/bench_retrieval.py` and run it against the E3 pipeline (`RetrievalService.retrieve`, E3-T9) on the 10,000-chunk synthetic corpus from E3-T2; record the result as `docs/adr/ADR-E3-03-retrieval-latency-and-rerank-ablation.md`.

Arch targets (deep-dive/02-quality-attributes.md §2.1): "Retrieval first stage (embed + hybrid SQL) | p95 <= 600 ms" (R4-D19 M3, ADR-039; the MVP 300 ms was rejected); "Rerank | p95 < 700 ms". ADR-008: "kept or dropped by the eval ablation on recall and latency ... Trigger to revisit: ... ANN p95 > 100 ms; rerank latency or TPM unmet". Epic done-when: "On a 10k-chunk synthetic corpus, retrieval first stage (embed + SQL) p95 <= 600 ms and rerank p95 < 700 ms are measured against deep-dive/02-quality-attributes.md §2.1 (fail if above, or the ablation drops rerank and the ADR says why)."

The script: runs >= 400 queries per configuration with the real Voyage `voyage-4` query embedding and real `rerank-3-lite` (needs `VOYAGE_API_KEY`; a `--stub-voyage` mode with fixed delays exists only for CI smoke and its output is labelled non-authoritative), for caller profiles (unrestricted tier-4 all-jurisdictions; restrictive tier-1 US). Reports p50/p95/p99 for `retrieval_first_stage_ms` and `rerank_ms`, the degraded-turn share, and (ablation) recall@RERANK_TOP_N on the synthetic set's known relevant chunks for rerank enabled vs disabled, at `RERANK_CANDIDATES` 10, 15 and 30. Exit code 1 if first-stage p95 > 600 ms or rerank p95 >= 700 ms. The default reranker is `rerank-3-lite`; the same run may be repeated with `RERANK_MODEL=rerank-3` through configuration only (ablation arm 3 is E7's).

The ADR states: measured table; whether `RERANK_ENABLED` stays true (if the ablation drops rerank, the ADR gives the recall and latency numbers that justify it); the preliminary `RERANK_CANDIDATES` (E7 L1 ablation makes the final call); the initial `GATE_MIN_SCORE` with the rerank-score distribution for answerable vs unanswerable synthetic queries (E3-T7); and the `RERANK_TIMEOUT_MS` consistency with E3-T1.

Out of scope: the full eval harness and final threshold tuning (E7), load testing of chat-api (E10).

## Acceptance criteria
- [ ] Given `VOYAGE_API_KEY` and the 10k corpus when `python backend/scripts/bench_retrieval.py --queries 400` runs then it exits 0 only if measured first-stage p95 <= 600 ms and rerank p95 < 700 ms, and exits 1 otherwise (script exit code; `backend/tests/test_bench_retrieval.py::test_exit_code_reflects_targets` feeds fixed latencies of 600/699 ms (exit 0), 601/699 ms (exit 1) and 600/700 ms (exit 1) through the evaluator function).
- [ ] The ADR contains a measured table with p50/p95/p99 for first stage and rerank for both caller profiles, and a recall@6 comparison of rerank on vs off at candidates 10, 15 and 30.
- [ ] If rerank p95 >= 700 ms or the ablation shows no recall gain, then the ADR sets `RERANK_ENABLED=false` with the numbers, otherwise it states `RERANK_ENABLED=true`; a test (`test_adr_has_decision_line`) asserts the ADR file contains a line matching `^RERANK_ENABLED=(true|false)$` and `^GATE_MIN_SCORE=\d`.
- [ ] Given the restrictive caller profile then 0 of 400 queries return fewer than the requested number of rows in the benchmark's run (reported in the output and asserted by the script, which exits 1 on any short result).
