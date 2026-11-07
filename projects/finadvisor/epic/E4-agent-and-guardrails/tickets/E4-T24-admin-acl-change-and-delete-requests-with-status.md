---
key: "E4-T24"
title: "Admin: ACL change and delete requests with status endpoint"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T21", "E3-T12", "E1-T21"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.1", "decision-logs.md#ADR-022"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
ACL change/delete returns 202 and writes one acl_change_requests row plus one outbox row.

## Description
Endpoints (6.1, ADR-022): POST /v1/admin/documents/{id}/acl-changes {tier_required?, jurisdiction?} and DELETE /v1/admin/documents/{id} (action=delete), role tenant_admin; in one transaction insert acl_change_requests (pending) and outbox AclChangeRequested (acl.changes.v1) and return 202 {request_id}; validate that the document is visible to the admin's tenant by reading via RetrievalService (no write to content tables). GET /v1/admin/acl-changes/{request_id} returns {status: pending|applied|failed, applied_at}. The acl-applier worker is not in this epic. chat-api's DB role fa_app has no INSERT/UPDATE/DELETE on documents, chunks, suitability_rules.

## Acceptance criteria
- [ ] Given a tenant_admin POST, then 202 and exactly one acl_change_requests row and one outbox row are created in one transaction (count test; failure of outbox insert rolls back both).
- [ ] Given a non-admin, 403 and zero rows.
- [ ] Given the fa_app role, a privilege test asserts no INSERT/UPDATE/DELETE grant on documents, chunks and suitability_rules (information_schema.role_table_grants query).
- [ ] Given a request id of another tenant, GET status returns 404.
