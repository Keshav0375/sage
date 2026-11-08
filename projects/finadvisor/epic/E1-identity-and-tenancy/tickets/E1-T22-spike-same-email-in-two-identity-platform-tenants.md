---
key: "E1-T22"
title: "Spike: same email in two Identity Platform tenants"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T1"]
arch_refs: ["decision-logs.md#adr-032", "decision-logs.md#adr-010", "deep-dive/08-security-and-privacy.md#8.2", "decision-logs.md#adr-039"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 119, "id": 6263452224, "url": "https://github.com/Keshav0375/FinAdvisor/issues/119"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Prove or disprove that one email address can hold a separate account in two Identity Platform tenants of one project, before any identity code is built.

## Description
Spike that gates the Identity Platform tickets of E1 (E1-T13 and E1-T21 depend on it; R4-D18 V5, ADR-032, ADR-039). Arch text under test (ADR-032): "One Identity Platform tenant per firm, one `advisors` row per `(tenant_id, idp_uid)`, one token per firm, no identity merge ... The 'same email in two tenants' test is a spike ticket that gates the Identity Platform tickets in E1 ... If it fails, onboarding uses per-firm email aliases and a new ADR says so." The Identity Platform pages are silent on this, so it is UNVERIFIED.

Reuse the E1-T1 probe setup (real GCP project, multi-tenancy and billing enabled, `IDP_PROJECT_ID`, ADC, the firebase-admin pin of E1-T1). Add `backend/scripts/spikes/idp_same_email_probe.py` (throwaway, not imported by app code):
1. Create two IdP tenants A and B (email/password) and sign up the SAME email in both through the REST endpoint with each `tenantId`.
2. Record whether both sign-ups succeed, the two `sub` values (expected different), and the tenant claim of each token.
3. Verify token A with `auth_for_tenant(A)` (ok) and with `auth_for_tenant(B)` (expect `TenantIdMismatchError`).
4. Record that the same email in both tenants does not link the accounts (the two `sub` values are unrelated).
Record the result as `docs/adr/idp-same-email-two-tenants.md` containing the line `SAME_EMAIL_TWO_TENANTS=pass` or `SAME_EMAIL_TWO_TENANTS=fail`, the observed errors and the date. If fail, the file names the fallback of ADR-032 option 2 (per-firm email aliases, no firm switcher in v1) and the builder stops: E1-T13 and E1-T21 are not started until the researcher records the new ADR.

Out of scope: any production auth code (E1-T13), the SPA firm switcher and the client `currentUser` behaviour when `tenantId` changes (E8, E13-T11), SSO.

## Acceptance criteria
- [ ] Given `IDP_PROJECT_ID` unset, when `idp_same_email_probe.py` runs, then it exits 2 and prints no credential material (`backend/tests/test_spike_scripts.py::test_same_email_probe_requires_project`).
- [ ] Given a real project, when `idp_same_email_probe.py --check` runs, then it exits non-zero if the observed outcome (both sign-ups succeed or not, two different `sub` values, `TenantIdMismatchError` for token A on tenant B) differs from the outcome recorded in the ADR file.
- [ ] The file `docs/adr/idp-same-email-two-tenants.md` exists and contains exactly one line matching `^SAME_EMAIL_TWO_TENANTS=(pass|fail)$`, the two `sub` values redacted to their first 6 characters, and the run date (`test_same_email_adr_has_verdict_line`).
- [ ] Given verdict `fail`, then the ADR names the alias fallback and the PR description lists E1-T13 and E1-T21 as blocked; given `pass`, then it states that one token per firm and one `advisors` row per `(tenant_id, idp_uid)` stand.
