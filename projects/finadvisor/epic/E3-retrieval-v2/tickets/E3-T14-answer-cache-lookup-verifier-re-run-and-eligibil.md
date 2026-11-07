---
key: "E3-T14"
title: "Answer cache lookup: verifier re-run and eligibility"
epic: "E3"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E3-T8", "E3-T13"]
arch_refs: ["decision-logs.md#adr-015", "decision-logs.md#adr-027", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.7", "deep-dive/06-interfaces-and-contracts.md#6.3", "deep-dive/04-components-and-responsibilities.md#4.5"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 74, "id": 6155658134, "url": "https://github.com/Keshav0375/FinAdvisor/issues/74"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Make a cache hit safe: re-verify citations against fresh chunks under RLS, recompute staleness, and never cache side-effect turns.

## Description
Add `AnswerCache.lookup(key, principal, verifier) -> CachedAnswer | None` and `AnswerCache.store_if_eligible(turn, ...)` in `backend/src/retrieval/answer_cache.py`.

Arch (ADR-015): "On a hit, re-run the citation verifier against freshly fetched chunks under the caller's RLS and recompute staleness; any failure is a miss. Turns that called a side-effect tool (`escalate_to_compliance`) are never cached." §5.7: "single-turn requests only". §6.3: "A turn that calls this tool [`escalate_to_compliance`] is never written to the answer cache". §4.5 `retrieval`: `fetch_chunks(ids)` "used by the citation verifier and the cache-hit path".

Behaviour of `lookup`: read the row (not expired); call `RetrievalService.fetch_chunks(citation chunk ids)` (E3-T8) under the caller's RLS; call the injected `verifier(answer, citations, chunks) -> bool` (the deterministic citation verifier is built in E4 `guardrails`; here define the `CitationVerifier` Protocol and depend only on it); recompute `stale` for each citation with `is_stale` and today's date; return the answer with fresh staleness flags. Any of: row missing, expired, a cited chunk not returned by `fetch_chunks` (deleted or ACL-restricted), verifier returns False or raises -> return None (a miss) and increment `answer_cache_total{result="miss_verifier"}`; a hit increments `answer_cache_total{result="hit"}`; a plain absence `result="miss"`. A verifier exception never propagates and never returns the cached answer.

`store_if_eligible` writes only when: `ANSWER_CACHE_ENABLED`, the request had no prior conversation history (single-turn), the turn's completed status is `complete`, the turn did not call `escalate_to_compliance` (the turn record passed in carries `tools_called`), and the answer passed the verifier on the live path. Otherwise it is a no-op.

Out of scope: the orchestrator's call order (E4), implementing the verifier, purge (E3-T15).

Round 4 (ADR-015 amended, ADR-027): `lookup(key, principal, verifier, as_of)` also requires, after `fetch_chunks(ids, as_of)` (E3-T8), that every cited chunk is returned and that its `valid_range @> as_of`; a cited chunk that is absent or whose range does not contain `as_of` makes the lookup a miss (`answer_cache_total{result="miss_verifier"}`). This is the as-of validity check that runs beside the citation verifier on a hit.

## Acceptance criteria
- [ ] Given a stored answer whose verifier stub returns False when `lookup` runs then it returns None and `answer_cache_total{result='miss_verifier'}` increased by 1 (test `backend/tests/test_answer_cache_lookup.py::test_verifier_failure_is_miss`).
- [ ] Given the verifier stub raises an exception when `lookup` runs then the result is None (test `test_verifier_exception_is_miss`).
- [ ] Given a stored answer citing chunk C and C has since been made invisible to the caller (higher `tier_required`) when `lookup` runs then None (test `test_acl_tightened_chunk_is_miss`, `integration`).
- [ ] Given a turn whose `tools_called` contains `escalate_to_compliance` when `store_if_eligible` runs then no row is written, even if the answer verified (test `test_side_effect_turn_never_cached`); given a multi-turn request then no row is written (test `test_multi_turn_not_cached`).
- [ ] Given a hit with a cited chunk whose `last_reviewed_at` crossed the stale threshold since storage when `lookup` runs then the returned citation has `stale=True` (test `test_staleness_recomputed_on_hit`).
- [ ] Given the cache holds an answer stored when `acl_version` was 3 and the tenant is now at 4 when the new key is computed then `lookup` returns None as a plain miss (test `test_acl_version_bump_makes_entry_unreachable`).
- [ ] Given a stored answer citing chunk C whose `valid_range` was closed by a newly published version so that it no longer contains `as_of`, when `lookup` runs, then it returns None and the miss counter `miss_verifier` increased by 1 (`test_answer_cache_lookup.py::test_cited_chunk_outside_as_of_is_miss`, `integration`).
- [ ] Given the same question after a new version is published (E3-T15 purge ran), then the cache misses and the freshly generated answer carries the new text (#3 core; `test_new_version_published_cache_misses`).
