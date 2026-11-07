---
key: "E7-T22"
title: "Add the golden_stats cluster-rule and split check"
epic: "E7"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E7-T2"]
arch_refs: ["deep-dive/02-quality-attributes.md#2.10", "decision-logs.md#adr-037"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add an L0 check that the golden set has at least 40 clusters, at most 5 items per cluster and the public/private split.

## Description
Add `python -m scripts.golden_stats [--check]` and an L0 test that runs on every PR. It prints counts per slice, per cluster and per split, and with `--check` fails on the sampling rule of ADR-037 and deep-dive/02 2.10: at least 40 clusters, at most 5 items per cluster (200 items mean exactly 5 items in each of 40 clusters; the floor is a constant `GOLDEN_MIN_CLUSTERS = 40` that is raised if the corpus yields more usable provisions). The cluster key is `cluster_id` (the provision or product, R4-D17). It also fails on unresolved `expected_evidence` (doc_key and version_key must exist in the seeded eval-tenant corpus) and on a `private` item in a committed file. `synthetic` cases are excluded from the counts. While the set is partial (pilot, tranche 1) the check runs in `--partial` mode: the cap of 5 is enforced and the 40-cluster floor is only reported. Out of scope: statistics (E7-T23).

## Acceptance criteria
- [ ] Given a fixture set of 200 items in 39 clusters, `--check` exits non-zero naming the cluster count; with 40 clusters of 5 items it exits 0 (tests `test_golden_stats.py::test_min_clusters`).
- [ ] Given a cluster with 6 items, `--check` and `--partial` both exit non-zero naming the cluster (`test_golden_stats.py::test_cluster_cap`).
- [ ] Given an item whose `expected_evidence.version_key` does not exist in the seeded corpus, `--check` fails (`test_golden_stats.py::test_unresolved_evidence`).
- [ ] Given a committed file containing `split: private`, the check fails; the L0 CI job runs `--partial` on every PR (workflow assertion).
