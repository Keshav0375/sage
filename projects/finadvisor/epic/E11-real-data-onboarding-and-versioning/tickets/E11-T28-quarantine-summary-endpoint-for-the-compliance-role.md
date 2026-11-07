---
key: "E11-T28"
title: "GET /v1/admin/quarantine/summary for the compliance role"
epic: "E11"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E11-T12", "E4-T4"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.8", "deep-dive/08-security-and-privacy.md#8.6", "deep-dive/08-security-and-privacy.md#8.8", "decision-logs.md#adr-036", "decision-logs.md#adr-028"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
A compliance officer can read counts of quarantined versions by source and reason code, and never any quarantined text.

## Description
Implements 8.6 and 8.8: "a compliance officer sees a summary, never raw quarantined text" and the role row "compliance_officer: advisor tools plus the quarantine summary (never raw quarantined text)". R4-D20 (Q1 of the stage-4 answers) adds the endpoint: `GET /v1/admin/quarantine/summary`, allowed for role `compliance_officer` (and `tenant_admin`), body `{generated_at, by_source: [{source_id, reason, count, oldest_at}]}` where `reason` is the `quarantine_reason` code of `document_versions` (E11-T5, E11-T11) and `count` the number of versions with `status = 'quarantined'` in the caller's tenant (RLS applies; PUBLIC rows are included for the PUBLIC-visible sources only as counts). The response carries no title, URL, excerpt, hash of content or bytes location, only source id, reason code, count and the oldest quarantine time. It is a read-only query through `fa_app`; release and reject stay admin CLI only (R4-D20 E11-Q3). Add the row to the endpoint table of 6.1 and the role policy table of 8.8 (default deny: a role without a row gets 403).

Out of scope: the SPA view (E8-T17), release or reject endpoints, the summary query function of E11-T12 (reused here).

## Acceptance criteria
- [ ] Given 3 quarantined versions (2 `contract_failed`, 1 `scan_failed`) in tenant A and 4 in tenant B, when the compliance officer of A calls the endpoint, then the body has counts 2 and 1 only and no row of B (test `test_quarantine_summary.py::test_counts_and_tenant_isolation`).
- [ ] Given a quarantined version whose bytes contain the marker `SECRET-MARKER-123`, when the endpoint is called, then the response body does not contain it, nor any title or URL field (test `test_quarantine_summary.py::test_never_returns_text`).
- [ ] Given role `advisor`, when called, then 403 `FORBIDDEN`; given `compliance_officer` and `tenant_admin`, 200 (test `test_quarantine_summary.py::test_role_policy`).
- [ ] The role-policy matrix test (8.8) fails if the row for this endpoint is removed.
