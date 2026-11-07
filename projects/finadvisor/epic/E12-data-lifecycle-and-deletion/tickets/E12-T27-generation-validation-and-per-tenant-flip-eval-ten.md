---
key: "E12-T27"
title: "Generation validation and per-tenant flip, eval tenant first"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T26", "E12-T25"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.27", "decision-logs.md#adr-35", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.10", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#19"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Validate a green generation with the ADR-035 gates and flip active_embed_model per tenant.

## Description
Command `embed-generation validate --model M --tenant T` sets `validating` and computes: counts and `chunk_set_hash` equal between blue and green; ANN self-hit >= 0.99 on green; recall@10 non-inferior on the golden set (paired lower bound >= -2 pp, using the E7 eval runner); retrieval p95 within +20% of blue. Command `embed-generation flip --model M --tenant T` refuses unless validation passed for that tenant, then in one transaction sets `tenants.active_embed_model` and bumps `corpus_version` (cache invalidation); the `eval` tenant must flip first (refuse another tenant before it). Out of scope: retire and drop, the eval harness itself.

## Acceptance criteria
- [ ] Given a green generation with one chunk missing, when validation runs, then it fails on counts and the flip command refuses (#19).
- [ ] Given a passing validation for tenant `eval`, when flip runs, then queries for `eval` use green, other tenants still use blue, and `corpus_version` increased.
- [ ] Given tenant X without `eval` having flipped, when flip runs for X, then it refuses with `EVAL_TENANT_FIRST`.
- [ ] Given a recall paired lower bound of -3 pp (fixture), then validation fails; at -1 pp it passes (statistics unit test).
- [ ] Given a green generation with p95 +25% over blue, then validation fails on latency.
