---
key: "E11-T23"
title: "Cache invalidation on publish of a new PUBLIC version"
epic: "E11"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E11-T9", "E3-T13", "E3-T14", "E3-T15", "E6-T10"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.17", "deep-dive/04-2-source-lifecycle-and-cells.md#4.18", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.7", "decision-logs.md#adr-27", "decision-logs.md#adr-28", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4 (#3)"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 273, "id": 6263722119, "url": "https://github.com/Keshav0375/FinAdvisor/issues/273"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Make a question miss the cache after a new version publishes and re-verify a hit inside the publish transaction.

## Description
Wire version publish into the answer cache. Arch (4.17 step 5): the publish transaction deletes `answer_cache` rows whose `source_document_ids` contain the document, then bumps `corpus_version` last. The cache key carries `as_of`, `embed_model` and the PUBLIC `source_epoch` (4.18, amends ADR-015; the key fields are an E3 round-4 update, this ticket tests them end to end). A hit that races the publish transaction is re-verified by the hit-time verifier (E3-T14: citations' `valid_range` contain `as_of`, entitlement and versions) and misses if stale.

Out of scope: key construction and verifier (E3-T13, T14).

## Acceptance criteria
- [ ] Given a cached cited answer for a PUBLIC document when a new version of that document is published then the same question misses the cache and returns the new text (#3; test `backend/tests/integration/test_publish_cache.py::test_new_version_misses_cache`, PR).
- [ ] Given a cache hit served inside the publish transaction (race harness) then the verifier re-checks and the stale answer is not released (#3; test `test_hit_inside_publish_is_reverified`, PR).
- [ ] Given the purge deletes cache rows by `source_document_ids` then rows of other documents are untouched (test `test_publish_purges_only_matching_cache_rows`).
