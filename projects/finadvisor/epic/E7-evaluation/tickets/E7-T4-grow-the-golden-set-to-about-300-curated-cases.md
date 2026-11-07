---
key: "E7-T4"
title: "Grow the golden set to about 300 curated cases"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T3"]
arch_refs: ["ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Reach ~300 golden cases, curated per tenant and balanced by category.

## Description
Grow data/eval/golden_qa.json to 280-320 cases across answerable, adversarial and refusal categories, parameterised by tenant (the `eval` tenant plus the second fixture tenant). Cases are authored from the corpus documents (regulatory refs and chunk ids must resolve). Add a coverage script `python -m scripts.golden_stats` that prints counts per category and per document and fails on unresolved expected chunk ids. Quote ADR-017: "Golden set 50 growing to ~300"; consequence: "the golden set must be curated per tenant". Out of scope: the human calibration labels (E7-T1).

## Acceptance criteria
- [ ] `python -m scripts.golden_stats` exits 0 and reports total between 280 and 320.
- [ ] A test fails if any expected_chunk_id / expected_doc_ref does not exist in the seeded eval-tenant corpus.
- [ ] A test fails if any category has fewer than 5% of total cases or any single document is referenced by more than 10% of answerable cases.
