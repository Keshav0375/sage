---
key: "E5-T11"
title: "acl-applier worker role"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T9", "E5-T10", "E1-T7", "E1-T10"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/05-data-model-and-storage.md#5.2", "decision-logs.md#adr-022", "decision-logs.md#adr-013"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 88, "id": 6155673894, "url": "https://github.com/Keshav0375/FinAdvisor/issues/88"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Consume AclChangeRequested and apply the ACL change, version bump and cache purge.

## Description
Implement role `acl-applier` on the E5-T7/T8 consumer framework: group `cg.acl-applier`, topic `acl.changes.v1`, handling `AclChangeRequested {request_id, document_id, action, new ACL}` only (other event types on the topic are skipped and recorded in processed_events). Per deep-dive/04-components-and-responsibilities.md#4.7 and ADR-022, in one transaction as `fa_worker` with app.tenant_id from the key: load the `acl_change_requests` row (E1-T7), then if action = update_acl, UPDATE only the ACL columns (`tier_required`, `jurisdiction`) on `documents` and `chunks` for that document_id (own-tenant WITH CHECK); if action = delete, DELETE the document and its chunks; set the request `status='applied'`, `applied_at`; UPDATE `tenants.acl_version` = acl_version + 1 on the own row; DELETE from `answer_cache` the rows whose `source_document_ids` contain the document (GIN index exists); insert an outbox row `AclChangeApplied {request_id, acl_version}` on `acl.changes.v1` for the relay. Idempotent on `request_id`: a request already `applied` is a no-op. A request that cannot be applied (document missing) is set `failed` with `error_code` and no version bump. No embedding call is made. Emit `acl_apply_lag_s` = applied_at - requested_at as an OTel histogram/metric (deep-dive/09-observability.md §09-observability.md). Out of scope: the admin endpoint that creates the request (E6), entitlement changes.

## Acceptance criteria
- [ ] Given a pending update_acl request on document D, when the applier processes the event, then all `chunks` rows of D have the new tier_required/jurisdiction, the request is `applied` with applied_at set, and `tenants.acl_version` is previous + 1 (integration test).
- [ ] Given answer_cache rows citing D and rows citing another document, when applied, then only the rows citing D are deleted.
- [ ] Given the Voyage client is replaced by a mock that fails on any call, when a request is applied, then the mock was called 0 times.
- [ ] Given the same AclChangeRequested delivered twice, when processed, then acl_version is bumped once, the second delivery changes no row, and exactly one AclChangeApplied outbox row exists with the new acl_version.
- [ ] Given a request for a missing document, when processed, then status is `failed` with a non-null error_code and acl_version is unchanged.
- [ ] Given an applied request, when metrics are read, then `acl_apply_lag_s` has one sample equal to applied_at - requested_at within 1 s.
