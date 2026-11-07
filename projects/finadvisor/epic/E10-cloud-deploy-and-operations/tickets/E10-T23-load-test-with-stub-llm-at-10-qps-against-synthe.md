---
key: "E10-T23"
title: "Load test with stub LLM at 10 QPS against synthetic corpus"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T18", "E10-T20", "E3-T16", "E4-T27"]
arch_refs: ["deep-dive/02-quality-attributes.md#2.1", "deep-dive/02-quality-attributes.md#2.3", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.1 rerank 429", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.2", "ADR-020"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Run a 10 QPS peak load test with a stub LLM and report p95 against the deep-dive/02-quality-attributes.md §2.1 targets excluding LLM time.

## Description
Epic done-when: 'A load test with a stub LLM runs at ~10 QPS peak and reports the p95 targets of deep-dive/02-quality-attributes.md §2.1 (excluding LLM time) against the 10k-chunk synthetic corpus numbers (fail if above).' Targets (2.1): retrieval first stage (embed + hybrid SQL) p95 < 300 ms, rerank p95 < 700 ms, TTFT p50 < 2.0 s / p95 < 3.5 s, full answer p95 < 8 s, all excluding LLM time (the stub returns a fixed streamed answer after a configured delay that is subtracted from the report). 7.2 and 4.6/rerank notes: Voyage Tier 1 allows ~5 QPS of rerank, so request the tier upgrade before the run (record in the PR) or run with the rerank step stubbed and state which was used.

Build load/ (k6 or Locust; pick the one already in deep-dive/11-tech-stack.md, else k6) with a scenario that ramps to 10 QPS against the real ALB URL with a test tenant token, a stub LLM selected by a config setting on the deployed revision (ANTHROPIC_BASE_URL pointing at a stub Cloud Run service or the Kong egress route replaced by the stub; the stub service is deployed only for the test, internal, not allUsers), reads per-stage timings from the metrics/traces defined in section 9, and writes docs/adr/load-test-results.md with p50/p95 for each metric, DB connection count peak (must stay below the budget of E10-T20), error rate, and pass/fail per target. Corpus: the 10k-chunk synthetic corpus from E3/E6 numbers. Use the `prod`-profile HA flag only if the report states it. Out of scope: tuning (record findings only).

## Acceptance criteria
- [ ] `make load-test` runs 10 QPS at peak for at least 5 minutes against the demo environment and exits non-zero if any p95 target of 2.1 (retrieval 300 ms, rerank 700 ms, TTFT p95 3.5 s, full answer p95 8 s, LLM time excluded) is exceeded
- [ ] docs/adr/load-test-results.md contains the measured p50/p95 for each target, the peak Cloud SQL connection count and the error rate; peak connections < 300 asserted in the script
- [ ] Rerank 429 counter (`rerank_429_total`) and `rerank_fallback_total` are reported; the run fails if degraded turns exceed 5% of turns
- [ ] The stub LLM service has no allUsers binding and is removed after the test (`gcloud run services list` has no stub)
