---
key: "E1-T16"
title: "Tenant discovery endpoint GET /v1/tenants/{slug}"
epic: "E1"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T9", "E1-T11"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.2", "deep-dive/05-data-model-and-storage.md#5.4", "decision-logs.md#adr-010"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 32, "id": 6155608349, "url": "https://github.com/Keshav0375/FinAdvisor/issues/32"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
A public endpoint returns only display_name and idp_tenant_id for a slug via fa_tenant_lookup.

## Description
Implement deep-dive/08-security-and-privacy.md §8.2 step 1: "The SPA ... calls the public `GET /v1/tenants/{slug}` (Kong IP rate limit) and receives only `{display_name, idp_tenant_id}` from `fa_tenant_lookup` (D13m). Slugs can be enumerated at the Kong IP rate; the response carries nothing else."

`GET /v1/tenants/{slug}` has no authentication dependency (it is the one public route). It calls `SELECT * FROM fa_tenant_lookup(p_slug => $1)` as `fa_app` in a transaction with no `app.*` settings. Response 200 `{"display_name": str, "idp_tenant_id": str}` and nothing else (no id, no kind, no status); unknown slug -> 404 with a generic body. The PUBLIC tenant is never resolved: if the function returns the row whose id is `PUBLIC_TENANT_ID` (slug `public`), the endpoint returns 404 as for an unknown slug. Slug is validated (lowercase letters, digits, hyphen, length bound) before the query. The Kong rate limit is E2.

Out of scope: Kong route and rate limits (E2), SPA (E8), the principal path's use of `p_idp_tenant_id` (E1-T14).

## Acceptance criteria
- [ ] Given tenant `acme` onboarded, when `GET /v1/tenants/acme` is called without any header, then the response is 200 with a JSON body whose keys are exactly `display_name` and `idp_tenant_id` (`tests/api/test_tenant_discovery.py`).
- [ ] Given an unknown slug, then the response is 404; given a slug `a'; drop table tenants;--` or one longer than the bound, then the response is 422/404 and the `tenants` table is intact.
- [ ] Given the request is served, then the SQL executed is only the `fa_tenant_lookup` call (asserted by capturing statements) and `fa_app` still has no direct SELECT on the `idp_tenant_id` column (covered by E1-T9 test remains green).
- [ ] Given the OpenAPI schema of the app, then this route is the only one without a security requirement (test).
- [ ] Given slug `public`, when `GET /v1/tenants/public` is called, then the response is 404 identical to an unknown slug (test).
