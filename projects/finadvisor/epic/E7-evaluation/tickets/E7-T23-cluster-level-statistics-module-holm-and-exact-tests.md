---
key: "E7-T23"
title: "Cluster-level statistics: permutation, exact McNemar and Holm"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T2"]
arch_refs: ["decision-logs.md#adr-037", "deep-dive/02-quality-attributes.md#2.10", "deep-dive/10-open-questions.md#10"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 179, "id": 6263551594, "url": "https://github.com/Keshav0375/FinAdvisor/issues/179"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Provide the statistics library for the eval: per-cluster aggregation, sign-flip permutation, exact McNemar, Holm over a fixed family and exact-or-exploratory handling of small slices.

## Description
Implements ADR-037: "Analysis at cluster level: per-document aggregation then sign-flip permutation, exact McNemar for binary metrics; no fixed n_eff claim ... Holm; slices under 30 items use exact tests or stay exploratory." Module `backend/src/evals/stats.py`:
- `aggregate_by_cluster(rows)` -> one value per `cluster_id` (mean of the paired difference for continuous metrics; discordant counts for binary).
- `paired_cluster_test(a, b)` -> mean difference, 95% interval over clusters, p from a sign-flip permutation over cluster differences (exact enumeration when clusters <= 20, else a seeded 100,000-draw Monte Carlo; the seed is recorded).
- `mcnemar_exact(b, c)` for binary metrics (exact binomial on the discordant pairs, two-sided).
- `holm(pvalues, family)` where the family is a frozen list of arm ids; calling it with an arm id outside the family raises.
- `slice_report(rows, min_items=30)` marks any slice with fewer than 30 items `exact_or_exploratory` and forbids a normal-approximation interval for it.
- `cluster_ci_lower_bound(values, seed)` used by E7-T8 and E7-T10.
No fixed n_eff or design effect is computed or claimed (the ICC assumption had no source). The detectable-effect computation lives in E7-T27 and reuses this module.

Out of scope: running arms (E7-T7), the pre-registration file (E7-T24).

## Acceptance criteria
- [ ] Unit test: 4 clusters with paired differences [+1, +1, +1, +1] give the exact one-sided count 1/16, two-sided p = 0.125 from exhaustive sign flips, to 3 decimals (`test_stats.py::test_signflip_exact`).
- [ ] Unit test: items from one cluster are never treated as independent: 5 items in each of 2 clusters give a permutation distribution of 2^2 = 4 sign patterns, not 2^10 (`test_stats.py::test_clusters_not_items`).
- [ ] Unit test: `mcnemar_exact(b=7, c=1)` equals the hand-computed two-sided exact p 0.0703 to 4 decimals.
- [ ] Unit test: Holm over p = [0.01, 0.02, 0.03, 0.04] rejects at 0.05 only the ones the step-down rule rejects (adjusted [0.04, 0.06, 0.06, 0.06]); passing a fifth arm id raises (`test_stats.py::test_holm_family_fixed`).
- [ ] Unit test: a slice with 29 items is reported `exact_or_exploratory` and asking it for a normal-approximation interval raises; a slice with 30 items is not marked.
