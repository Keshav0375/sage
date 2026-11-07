---
key: "E8-T2"
title: "Add tenant discovery at /t/<slug>"
epic: "E8"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E8-T1", "E1-T16"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.2", "deep-dive/06-interfaces-and-contracts.md#6.1", "decision-logs.md#adr-010"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
The SPA resolves the firm from the URL slug through the public tenant endpoint and shows a not-found state.

## Description
Implements deep-dive/08-security-and-privacy.md §8.2 step 1 and 6.1 `GET /v1/tenants/{slug}` -> `{display_name, idp_tenant_id}` only; 404 `TENANT_NOT_FOUND`. Add react-router route `/t/:slug`; typed `fetchTenant(slug)` in src/lib/api.ts (unauthenticated, no Authorization header); a tenant context holding {slug, display_name, idp_tenant_id}; the firm display_name shown in the header. Unknown slug renders a firm-not-found page keyed by the error code (no crash). Routes outside /t/:slug show a short 'use your firm link' page. Out of scope: sign-in (E8-T3), the endpoint itself (E1-T16).

## Acceptance criteria
- [ ] Given a mocked 200 `{display_name:'Acme', idp_tenant_id:'t-1'}`, when /t/acme renders, then 'Acme' appears and the tenant context holds idp_tenant_id 't-1' (vitest + testing-library).
- [ ] Given a mocked 404 `TENANT_NOT_FOUND`, when /t/nope renders, then the not-found page shows and no sign-in form renders.
- [ ] Given the request is captured, when fetchTenant runs, then it carries no Authorization header (unit test).
- [ ] Given a network failure, when /t/acme renders, then a retryable error state shows, not an unhandled exception.
