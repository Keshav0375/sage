---
key: "E8-T2"
title: "Add tenant discovery at /t/<slug>"
epic: "E8"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E8-T1", "E1-T16", "E13-T3"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.2", "deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/06-interfaces-and-contracts.md#6.11", "decision-logs.md#adr-010", "decision-logs.md#adr-031"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The SPA resolves the firm's cell from the URL slug, then the firm from that cell's public tenant endpoint, and shows a not-found state.

## Description
Implements deep-dive/08-security-and-privacy.md §8.2 step 1, 6.1 `GET /v1/tenants/{slug}` -> `{display_name, idp_tenant_id}` only (404 `TENANT_NOT_FOUND`), and the cell step of 06 6.11: "`GET /resolve?slug=` (public, rate limited by IP ...) returns `{cell_id, api_endpoint}`. The SPA then talks to the per-cell hostname" (ADR-031).

Flow for route `/t/:slug`: (1) `fetchResolve(slug)` -> `{cell_id, api_endpoint}` (unauthenticated, no Authorization header; 404 `TENANT_NOT_FOUND` renders the not-found page); (2) `fetchTenant(slug)` against `api_endpoint` -> `{display_name, idp_tenant_id}`; (3) a tenant context holds {slug, display_name, idp_tenant_id, cell_id, apiBase}; every later API call of the firm uses `apiBase` (a per-firm base URL held in memory only, never persisted). The firm display_name is shown in the header. Unknown slug renders a firm-not-found page keyed by the error code (no crash). Routes outside /t/:slug show a short 'use your firm link' page. Out of scope: sign-in (E8-T3), the endpoints (E1-T16, E13-T3), cell redirect on 421 (E8-T4, E8-T14).

## Acceptance criteria
- [ ] Given mocked `/resolve` returning `{cell_id:'us', api_endpoint:'https://us.example'}` and tenant 200 `{display_name:'Acme', idp_tenant_id:'t-1'}`, when /t/acme renders, then 'Acme' appears, the tenant context holds idp_tenant_id 't-1' and apiBase 'https://us.example', and the tenant request went to that host (vitest + testing-library).
- [ ] Given a mocked 404 `TENANT_NOT_FOUND` from `/resolve`, when /t/nope renders, then the not-found page shows, no tenant request is made and no sign-in form renders.
- [ ] Given the captured requests, when fetchResolve and fetchTenant run, then neither carries an Authorization header (unit test).
- [ ] Given a network failure on `/resolve`, when /t/acme renders, then a retryable error state shows, not an unhandled exception.
- [ ] Given the context after load, when localStorage, sessionStorage and IndexedDB are inspected, then none contains `apiBase` or `cell_id` (unit test).
