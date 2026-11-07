---
key: "E3-T15"
title: "Answer cache purge by document and by expiry"
epic: "E3"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E3-T13"]
arch_refs: ["decision-logs.md#adr-015", "decision-logs.md#adr-039", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.7", "deep-dive/05-data-model-and-storage.md#5.3"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 75, "id": 6155659288, "url": "https://github.com/Keshav0375/FinAdvisor/issues/75"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Provide the purge operations the acl-applier and maintenance job call, and prove each role can only delete what it should.

## Description
Add two functions in `backend/src/retrieval/answer_cache_purge.py` (no dependency on the rest of `retrieval`, so the worker and job entrypoints can import them without importing a content-table accessor): `purge_for_documents(conn, tenant_id, document_ids) -> int` and `purge_expired(conn) -> int`.

Arch (ADR-015): "Purged by the `acl-applier` on ACL change and document delete, and by the `maintenance` job when expired (D16.8, D16.18)." §5.7: "Purged by the `acl-applier` on ACL change and document delete (GIN on `source_document_ids`) and by `maintenance` when expired." §5.3: `fa_worker` "DELETE on `answer_cache`" (writes limited to its own non-PUBLIC tenant by policy); `fa_maint` "DELETE on `answer_cache` and `turn_events` limited by policy to expired rows".

Behaviour: `purge_for_documents` runs `DELETE FROM answer_cache WHERE tenant_id = $1 AND source_document_ids && $2::uuid[]` using the GIN index and returns the deleted count; `purge_expired` runs `DELETE FROM answer_cache WHERE expires_at < now()` (the `fa_maint` policy limits it to expired rows). Both use bind parameters. The call sites live in the acl-applier (E6) and the maintenance job (E1/E10); this ticket only ships and tests the functions, plus a one-paragraph note in `docs/` naming them for those epics. Cache entries for a PUBLIC document cited by a firm tenant's answer are deleted by the tenant-scoped call when the applier passes that tenant's id; how a PUBLIC document change reaches firm tenants' entries is covered by the `corpus_version` bump in the key (E3-T13), see questions.

Out of scope: the applier and maintenance job code themselves.

Round 4 (ADR-015 amended, ADR-039 M7; deep-dive/05-1 section 5.7: "Purged by the indexer in the same transaction as any version publish, supersede, retire, withdraw or erase of the document (GIN on `source_document_ids`), by the `acl-applier` on ACL change and by the `erasure-worker` on document delete, by `purge_source` ..., and by `maintenance` when expired"). This replaces the earlier statement that the `acl-applier` purges on document delete: document delete is the `erasure-worker`'s. `purge_for_documents(conn, tenant_id, document_ids)` is the one function all of those callers use; it runs on the caller's connection and transaction, so the indexer can call it inside its publish transaction (the call sites are E11, E12 and E6; this ticket ships and tests the function and the doc note naming the four callers). When PUBLIC `source_epoch` is bumped, firm-tenant rows become unreachable by key and each firm tenant's `erasure-worker` deletes them with this function after pulling `source_purges` (E12-T19).

## Acceptance criteria
- [ ] Given three cached rows where two list document D in `source_document_ids` when `purge_for_documents(tenant, [D])` runs as `fa_worker` then it returns 2 and the third row remains (test `backend/tests/test_answer_cache_purge.py::test_purge_by_document`, `integration`).
- [ ] Given one expired and one live row when `purge_expired` runs as `fa_maint` then exactly the expired row is deleted; attempting `DELETE ... WHERE expires_at > now()` as `fa_maint` deletes 0 rows (test `test_maint_deletes_only_expired`).
- [ ] Given `fa_worker` for tenant A tries to delete tenant B's cached row then 0 rows are deleted (test `test_worker_cannot_purge_other_tenant`).
- [ ] `EXPLAIN` of the `purge_for_documents` statement shows use of the GIN index on `source_document_ids` when the table has > 1000 rows (test `test_purge_uses_gin_index`).
- [ ] Given `purge_for_documents` called inside an open transaction that is then rolled back, then the cached rows are still present; given it is committed with the publish transaction, then the rows are gone (`test_answer_cache_purge.py::test_purge_is_part_of_caller_transaction`).
- [ ] Given a docs note `docs/answer-cache-purge.md`, then it lists the four callers (indexer on publish, supersede, retire, withdraw and erase; acl-applier on ACL change; erasure-worker on document delete; maintenance on expiry) and `grep -n 'acl-applier.*document delete' docs/answer-cache-purge.md` returns nothing (`test_docs_callers`).
