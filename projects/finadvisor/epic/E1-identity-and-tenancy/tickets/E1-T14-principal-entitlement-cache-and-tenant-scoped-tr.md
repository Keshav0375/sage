---
key: "E1-T14"
title: "principal: entitlement cache and tenant-scoped transactions"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T9", "E1-T10", "E1-T13"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.4", "decision-logs.md#adr-002", "decision-logs.md#adr-010"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 30, "id": 6155605798, "url": "https://github.com/Keshav0375/FinAdvisor/issues/30"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
A Principal is built from the verified identity with a 60 s cache, and the only code that sets app.* settings provides the tenant-scoped transaction context manager.

## Description
Implement the `principal` module (deep-dive/04-components-and-responsibilities.md §4.5): "maps `idp_tenant_id` to `tenants.id` (via `fa_tenant_lookup`, 5.4), loads `advisors` (tier, jurisdictions, licenses, role, `entitlement_version`) into a `Principal` object, cached <= 60 s per process; the TTL is the revocation bound (no Kafka invalidation). Owns the only function that sets the per-transaction settings `app.tenant_id`, `app.idp_uid`, `app.user_id`, `app.role`, `app.tier`, `app.jurisdictions` via `set_config(name, $n, true)` with bind parameters (the principal-load transaction sets `app.tenant_id` and `app.idp_uid` plus neutral values for the rest). Neutral values (R17): `app.user_id` = nil uuid (`00000000-0000-0000-0000-000000000000`), `app.role` = empty string, `app.tier` = `0`, `app.jurisdictions` = empty string; with these values RLS returns no content rows."

Build `src/principal/`:
- `Principal` (frozen dataclass): `tenant_id, advisor_id, idp_uid, role, tier, jurisdictions, licenses, entitlement_version`.
- `async load_principal(identity: VerifiedIdentity) -> Principal`: calls `fa_tenant_lookup(p_idp_tenant_id => ...)`; unknown tenant -> `UNAUTHENTICATED`; then, in a short transaction with `app.tenant_id` and `app.idp_uid` set and neutral values for the rest, selects the advisor by `(tenant_id, idp_uid)`; unknown or non-active advisor -> `UNAUTHENTICATED`. Result cached per process keyed by `(idp_tenant_id, sub)` for `ENTITLEMENT_CACHE_TTL_S` (default 60).
- `async scoped_tx(principal)`: async context manager yielding a connection in a transaction where `SELECT set_config('app.tenant_id', $1, true), set_config('app.idp_uid', $2, true), set_config('app.user_id', $3, true), set_config('app.role', $4, true), set_config('app.tier', $5, true), set_config('app.jurisdictions', $6, true)` ran with bind parameters (`jurisdictions` comma-joined). It is the only place that calls `set_config`; there are no `SET`, `SET ROLE` or `SET LOCAL app.*` statements anywhere in `src`. Transactions are short; the context manager refuses to be held open (a configurable max duration is not required).
- Remove the MVP session-level `SET` in `src/db/rls.py` (G-19) and make the DB engine connect with `DB_USER`, `DB_POOL_SIZE`, `DB_STATEMENT_TIMEOUT_MS` from Settings.

Out of scope: wiring into routes (E1-T15), the retrieval module (E3), cache invalidation by events: the entitlement cache is TTL-only, 60 s, with no Kafka or event invalidation (ADR-002, ADR-004; R19).

## Acceptance criteria
- [ ] Given an advisor row (tier 2, jurisdictions US,EU, role advisor), when `load_principal` runs for its verified identity, then the returned `Principal` has those values and `tenant_id` equals the `tenants.id` mapped from the IdP tenant id (`tests/principal/test_principal.py`, real Postgres as `fa_app`).
- [ ] Given the advisor's tier is changed in the DB, when `load_principal` is called again within `ENTITLEMENT_CACHE_TTL_S`, then the old tier is returned; after the clock passes the TTL (fake clock), the new tier is returned.
- [ ] Given an unknown IdP tenant id, or a known tenant with an unknown `sub`, or an advisor with `status != 'active'`, then `load_principal` raises `UNAUTHENTICATED` (3 cases).
- [ ] Given `scoped_tx(principal)`, when `SELECT current_setting('app.tenant_id'), current_setting('app.role'), current_setting('app.tier')` runs inside it, then the values equal the principal's; after the block exits, a new transaction on the same pooled connection reads `current_setting('app.tenant_id', true)` as empty/NULL.
- [ ] Given a static test (`tests/test_no_session_set.py`), then `grep` over `backend/src` finds no `SET ROLE`, no `SET app.`, no `set_config(` outside `src/principal`, and no `is_local = false` argument.
- [ ] Given the principal-load transaction with the neutral values, when `fa_app` selects from `chunks`, `documents` and `suitability_rules`, then zero rows are returned and no error is raised (test).
