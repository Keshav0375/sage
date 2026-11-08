---
key: "E4-T23"
title: "Admin: PATCH /v1/admin/advisors/{id}"
epic: "E4"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E4-T21", "E1-T21"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 129, "id": 6263471908, "url": "https://github.com/Keshav0375/FinAdvisor/issues/129"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Tenant admins update advisors directly, bumping entitlement_version with an outbox event.

## Description
Endpoint (6.1): role tenant_admin via principal; body {role?, tier?, jurisdictions?, licenses?, status?} validated; direct UPDATE advisors (policy allows tenant_admin only), bump entitlement_version, outbox AdvisorEntitlementChanged in the same transaction; own-tenant only (RLS). Takes effect within ENTITLEMENT_CACHE_TTL_S (no Kafka invalidation).

## Acceptance criteria
- [ ] Given a tenant_admin, when patching tier, then 200, entitlement_version increments by 1 and one outbox row exists.
- [ ] Given a non-admin, then 403 FORBIDDEN and no row changes.
- [ ] Given an advisor of another tenant, then 404 and no change (RLS test).
- [ ] Given an invalid tier value, 422/400 with a stable code.
