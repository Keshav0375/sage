---
key: "E3-T13"
title: "Answer cache: table, versioned key and store"
epic: "E3"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T21", "E3-T4"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.7", "deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/05-data-model-and-storage.md#5.3", "deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#adr-015"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 73, "id": 6155656885, "url": "https://github.com/Keshav0375/FinAdvisor/issues/73"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Create the UNLOGGED answer_cache table with own RLS and a cache_key that changes with every version input.

## Description
Add the `answer_cache` table (if the E1 baseline did not already create it; check first) and the `AnswerCache` class in `backend/src/retrieval/answer_cache.py`, owned by the `retrieval` module (§4.5: "Also owns the `answer_cache` read/write (not a content table)").

Arch (ADR-015): "Table `answer_cache` (UNLOGGED), own RLS + FORCE. Key = hash(tenant, tier, jurisdiction set, corpus_version (own and PUBLIC), acl_version, user entitlement version, prompt_version, model, normalized redacted question). Single-turn only, TTL 24 h." Overview §5.7: "`cache_key = sha256(tenant_id, tier, sorted jurisdictions, corpus_version of the tenant and of PUBLIC, acl_version, entitlement_version of the user, prompt_version, model, normalized redacted question)`. Columns: `cache_key`, `answer` (redacted), `citations` (chunk ids, indexes), `source_document_ids uuid[]`, `created_at`, `expires_at`." PK `(tenant_id, cache_key)`; indexes `(expires_at)` and GIN on `source_document_ids` (§5.5). RLS: tenant match for `fa_app`; `fa_worker` DELETE; `fa_maint` DELETE limited by policy to expired rows (§5.3, §5.4). Config: `ANSWER_CACHE_ENABLED` (true), `ANSWER_CACHE_TTL_S` (86400), `PROMPT_VERSION`.

Deliver: Alembic migration (UNLOGGED, ENABLE + FORCE RLS, policies, indexes, grants exactly per §5.3: `fa_app` SELECT/INSERT/UPDATE); `make_cache_key(principal, versions, prompt_version, model, question) -> str` as a pure function (fields joined with an unambiguous length-prefixed or JSON canonical encoding, not naive concatenation; question normalized by trim, lowercase and whitespace collapse; the input is already PII-redacted); `AnswerCache.put(...)` which writes `answer`, `citations`, `source_document_ids`, `expires_at = now + ANSWER_CACHE_TTL_S` and `AnswerCache.get_raw(key)` (no verification here; E3-T14). Versions are read in the same transaction: `tenants.corpus_version` and `acl_version` for the caller's tenant, `corpus_version` for PUBLIC, and `advisors.entitlement_version` from the Principal. Writes are skipped when `ANSWER_CACHE_ENABLED` is false.

Out of scope: hit verification and eligibility rules (E3-T14), purge (E3-T15), calling the cache from the orchestrator (E4).

## Acceptance criteria
- [ ] Given a base input when exactly one of {acl_version, own corpus_version, PUBLIC corpus_version, entitlement_version, tier, jurisdiction set, prompt_version, model, question text} changes then `make_cache_key` returns a different key for each of the nine changes (parametrized test `backend/tests/test_answer_cache_key.py::test_key_changes_with_each_input`).
- [ ] Given jurisdictions ['US','EU'] and ['EU','US'] and a question with extra whitespace/case differences then the keys are equal (test `test_key_is_order_and_whitespace_insensitive`); given field values that concatenate identically ('ab','c' vs 'a','bc') the keys differ (test `test_key_encoding_unambiguous`).
- [ ] Given a put by tenant A when tenant B's principal does `get_raw` with the same key then no row is returned (RLS; test `backend/tests/test_answer_cache_rls.py::test_cross_tenant_get_returns_nothing`, `integration`).
- [ ] `pg_class.relpersistence` for `answer_cache` is 'u' and `relforcerowsecurity` is true; `fa_app` has no DELETE grant on it (test `test_answer_cache_is_unlogged_forced_rls`).
- [ ] Given `ANSWER_CACHE_ENABLED=false` when `put` runs then no row is written (test `test_disabled_cache_writes_nothing`).
