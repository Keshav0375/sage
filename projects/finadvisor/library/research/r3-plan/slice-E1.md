# Slice E1

## Epic section (from arch/plan.md)

### E1 Identity and tenancy

- **Goal.** A caller is a verified person in a tenant, and the database refuses every cross-tenant read and write.
- **Scope.**
  - First ticket: verify the `firebase.tenant` claim name against a real Identity Platform tenant (D14.17).
  - `tenants` and `advisors`; Identity Platform multi-tenancy (one IdP tenant per firm); tenant-aware ID-token verification with firebase-admin (`auth`); `principal` with the 60 s entitlements cache and `entitlement_version`; IdP tenant provisioning script (Terraform comes in E10).
  - Schema for the whole target model in the baseline migration: `documents.raw_content` is dropped here (G-03 early); `acl_change_requests`, `eval_scores`, `turn_events`, `outbox` and `processed_events` tables are created (the outbox is written in E4 and relayed in E5).
  - RLS v2 on all tables: ENABLE + FORCE, SELECT own-or-PUBLIC, writes own-tenant only, PUBLIC writable only by `fa_etl_public`; roles `fa_app` (SELECT only on content), `fa_worker`, `fa_etl`, `fa_etl_public`, `fa_dbt`, `fa_owner`, `fa_lookup`, `fa_maint`, `fa_eval`, `fa_dagster`; `tenants` policies; `advisors` admin-only UPDATE; `advisor_id` owner clauses; `set_config(..., true)` in short transactions; composite FKs.
  - LIST partitions of `chunks` and monthly partitions of `messages` with no partition grants; tenant onboarding in the `migrate` job; `maintenance` job schema and role (scheduling in E10); startup / readiness role and RLS assertions.
  - Leak matrix: reads, writes, FK probes, direct partition access, advisor self-escalation, pooled-connection reuse, fail-closed. Tenant discovery endpoint and `fa_tenant_lookup` (owned by `fa_lookup`).
- **Arch sections.** overview.md#5, overview.md#8.2, overview.md#4.5 (`auth`, `principal`), overview.md#4.8; ADR-002, ADR-003, ADR-004, ADR-010.
- **Dependencies.** E0.
- **Spikes first.** Identity Platform multi-tenancy: confirm billing for > 2 tenants; LIST-partition pruning with the RLS `current_setting` policy plus planner cost at ~52 partitions.
- **Done when.**
  - The L0 leak matrix passes on every PR: cross-tenant read, cross-tenant insert, update and delete into PUBLIC, FK existence probes, direct SELECT / INSERT on a partition as `fa_app` / `fa_worker` gives permission denied, "advisor raises own tier / role" is denied, pooled-connection reuse, unset setting fails closed; leaks = 0.
  - Startup refuses to run when the role is superuser, BYPASSRLS or owner (except the `fa_dbt` and `fa_maint` exemptions), when any tenant table lacks FORCE RLS (including partitioned parents), or when a partition carries a runtime grant (tests).
  - A request with a forged, expired, wrong-audience or wrong-tenant token gets 401; a valid token for tenant A cannot read tenant B rows.
  - `EXPLAIN` shows partition pruning for LIST partitions under RLS.
  - `documents.raw_content` does not exist after the migration; the CI assertion that only `fa_tenant_lookup` is `SECURITY DEFINER` passes.
  - Fixes G-01, G-03, G-12, G-19, G-20, G-21, G-43.

## Arch files to read (paths; read only the named subsections)

- context/projects/finadvisor/arch/overview/04-components-and-responsibilities.md  (sections: 4.5, 4.8)
- context/projects/finadvisor/arch/overview/05-data-model-and-storage.md  (sections: 5)
- context/projects/finadvisor/arch/overview/08-security-and-privacy.md  (sections: 8.2)
- context/projects/finadvisor/arch/stack.md (versions)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md §6.6 (config keys), only the keys this epic uses

## ADRs (context/projects/finadvisor/arch/decisions.md; line of heading)

- line 477: ADR-002: Pool tenancy in one Postgres with RLS (read/write split, role per process)
- line 456: ADR-003: LIST partitions of chunks by tenant
- line 435: ADR-004: Single retrieval enforcement point
- line 305: ADR-010: Authentication with Identity Platform multi-tenancy and tenant discovery
