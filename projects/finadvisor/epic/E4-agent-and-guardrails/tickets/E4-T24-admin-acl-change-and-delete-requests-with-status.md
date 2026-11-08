---
key: "E4-T24"
title: "Admin: ACL change requests with status endpoint"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T21", "E3-T12", "E1-T21"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.1", "decision-logs.md#adr-022", "decision-logs.md#adr-029"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 130, "id": 6263472774, "url": "https://github.com/Keshav0375/FinAdvisor/issues/130"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
ACL and reclassification changes return 202 and write one acl_change_requests row plus one analytics outbox row; document delete is not handled here.

## Description
Endpoints (6.1, ADR-022 amended): POST /v1/admin/documents/{id}/acl-changes {tier_required?, jurisdiction?}, role tenant_admin; in one transaction insert acl_change_requests (pending, action `update_acl`) and an outbox row `AclChangeRequested` on acl.changes.v1 (analytics only: the applier polls the table, E5-T11) and return 202 {request_id}; validate that the document is visible to the admin's tenant by reading via RetrievalService (no write to content tables). GET /v1/admin/acl-changes/{request_id} returns {status: pending|applied|failed, applied_at}; another tenant's id gives 404. The acl-applier worker is E5-T11.

Round 4 (ADR-022 amended, ADR-029, R4-D17): `acl_change_requests` carries ACL and reclassification changes ONLY. The old `DELETE /v1/admin/documents/{id}` (action=delete through acl_change_requests) is REMOVED from this ticket; document delete is a `deletion_requests` row written by E12-T11, and no code here inserts an `acl_change_requests` row with action `delete` (the action enum has no `delete` value in the request model). chat-api's DB role fa_app has no INSERT/UPDATE/DELETE on documents, chunks, suitability_rules.

## Acceptance criteria
- [ ] Given a tenant_admin POST, then 202 and exactly one acl_change_requests row and one outbox row are created in one transaction (failure of the outbox insert rolls back both).
- [ ] Given a request body or route attempting action `delete`, when sent to the acl-changes endpoint, then 422 and zero rows (test_acl_changes_has_no_delete_action); the module registers no DELETE route for documents (route-table test).
- [ ] Given a non-admin, 403 and zero rows; given a request id of another tenant, GET status returns 404.
- [ ] Given the fa_app role, a privilege test asserts no INSERT/UPDATE/DELETE grant on documents, chunks and suitability_rules (information_schema.role_table_grants).
