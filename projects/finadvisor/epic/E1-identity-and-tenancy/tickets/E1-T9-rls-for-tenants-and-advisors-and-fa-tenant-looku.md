---
key: "E1-T9"
title: "RLS for tenants and advisors, and fa_tenant_lookup"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T3", "E1-T4"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.4", "deep-dive/05-data-model-and-storage.md#5.3", "decision-logs.md#adr-010", "decision-logs.md#adr-002"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 25, "id": 6155599197, "url": "https://github.com/Keshav0375/FinAdvisor/issues/25"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
tenants and advisors policies and grants are in place, advisors cannot self-escalate, and the single SECURITY DEFINER function fa_tenant_lookup exists.

## Description
Add an Alembic revision implementing the `tenants` and `advisors` items of deep-dive/05-data-model-and-storage.md §5.4 and the 5.3 grants.

`tenants`: `tenants_select_app TO fa_app FOR SELECT USING (id = current_setting('app.tenant_id')::uuid OR id = '<PUBLIC>'::uuid)`; `tenants_lookup TO fa_lookup FOR SELECT USING (true)`; `tenants_owner TO fa_owner` for SELECT, INSERT, UPDATE; `tenants_upd_worker TO fa_worker FOR UPDATE USING / WITH CHECK (id = app.tenant_id AND id <> <PUBLIC>)`; `tenants_upd_public TO fa_etl_public FOR UPDATE USING / WITH CHECK (id = <PUBLIC>)`. Column grants: `fa_app` SELECT on (`id`, `slug`, `corpus_version`, `acl_version`, `budgets`) only; `fa_lookup` SELECT on the columns the function returns plus `slug`; UPDATE limited to `corpus_version` and `acl_version` for `fa_worker` and to `corpus_version` for `fa_etl_public`.

`advisors`: SELECT `TO fa_app` when `tenant_id = app.tenant_id AND (id = app.user_id OR idp_uid = app.idp_uid OR app.role = 'tenant_admin')`; UPDATE `TO fa_app` only when `tenant_id = app.tenant_id AND app.role = 'tenant_admin'`, `WITH CHECK (tenant_id = app.tenant_id)`. Column grants: UPDATE on `tier, jurisdictions, licenses, role, status, entitlement_version` only (`tenant_id` immutable). No self-escalation: "an advisor cannot raise their own tier or role".

`fa_tenant_lookup(p_slug text DEFAULT NULL, p_idp_tenant_id text DEFAULT NULL)`: `SECURITY DEFINER`, owned by `fa_lookup` (not `fa_owner`), explicit `SET search_path`, returns `(id, display_name, idp_tenant_id)`, serves both slug discovery and the `idp_tenant_id` to `tenants.id` mapping (D14.4); `REVOKE EXECUTE ... FROM PUBLIC; GRANT EXECUTE ... TO fa_app;`. It is the only `SECURITY DEFINER` function allowed in the database. With both arguments NULL it returns no rows.

Out of scope: the HTTP endpoint (E1-T16), the principal that calls the function (E1-T14).

## Acceptance criteria
- [ ] Given a principal of tenant A, when `fa_app` selects from `tenants`, then it sees exactly the tenant A row and the PUBLIC row; selecting a column outside the grant (e.g. `idp_tenant_id`) fails with permission denied; any UPDATE on `tenants` by `fa_app` fails with permission denied (`tests/db/test_rls_identity.py`).
- [ ] Given an advisor with `app.role = 'advisor'`, when it runs `UPDATE advisors SET tier = 4, role = 'tenant_admin' WHERE id = app.user_id`, then rowcount is 0 and the stored tier and role are unchanged.
- [ ] Given `app.role = 'tenant_admin'` of tenant A, when it updates the tier of an advisor of tenant A then it succeeds; of an advisor of tenant B then rowcount is 0; `UPDATE advisors SET tenant_id = ...` fails with permission denied.
- [ ] Given `fa_tenant_lookup(p_slug => 'acme')` called as `fa_app`, then it returns exactly the columns `id, display_name, idp_tenant_id`; called as `fa_worker` it fails with permission denied; `has_function_privilege('public', ...)` is false.
- [ ] Given `pg_proc`, then exactly one function with `prosecdef = true` exists in the app schemas, it is `fa_tenant_lookup`, and its owner is `fa_lookup` (test).
- [ ] Given `fa_tenant_lookup(NULL, NULL)` called as `fa_app`, then it returns zero rows (test).
