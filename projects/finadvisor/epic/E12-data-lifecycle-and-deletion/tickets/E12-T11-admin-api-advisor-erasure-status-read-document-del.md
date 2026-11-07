---
key: "E12-T11"
title: "Admin API: advisor erasure, status read, document delete queue"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T5", "E12-T7", "E4-T24"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.9", "deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "decision-logs.md#adr-29", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.13"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add DELETE /v1/admin/advisors/{id} and GET /v1/admin/deletion-requests/{id} and route document delete to deletion_requests.

## Description
Implement the three rows of deep-dive/06 6.9. `DELETE /v1/admin/documents/{id}` (tenant_admin) now inserts a `deletion_requests` row directly (scope `document`, `subject_ref` = the document's `doc_key`, reason `erasure` or `takedown`) and returns 202 `{request_id}`; 404 `NOT_FOUND` for an id outside the caller's tenant; it replaces the E4-T24 delete path through `acl_change_requests` (ACL changes there stay). `DELETE /v1/admin/advisors/{id}` inserts one row (scope `advisor`, `subject_ref` = the advisor's `pseudonym_id`) and returns 202. `GET /v1/admin/deletion-requests/{request_id}` returns `{status, phase, steps[], receipt_uri?}` from `deletion_requests`, `erasure_receipts` and `erasure_steps`; 404 for another tenant. The path of the two new endpoints is ratified here as 6.9 states. Out of scope: workers.

## Acceptance criteria
- [ ] Given a tenant_admin, when it calls DELETE on a document of its tenant, then 202, exactly one `deletion_requests` row (scope document) and no `acl_change_requests` row.
- [ ] Given a document id of another tenant, then 404 `NOT_FOUND` and zero rows (cross-tenant test).
- [ ] Given a non-admin role, then 403 and zero rows on all three endpoints.
- [ ] Given a closed request with phase-2 receipt, when GET runs, then it returns status `closed`, phase 2, the steps and the receipt GCS uri; for a phase-1 request it returns phase 1 and status `executed` or `windows_open`.
- [ ] The OpenAPI document lists the two new paths with the 6.9 response shapes (contract test).
