---
key: "E1-T19"
title: "L0 leak matrix part 1: cross-tenant reads, writes, FK probes"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T8", "E1-T9", "E1-T10", "E1-T11"]
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.4", "deep-dive/08-security-and-privacy.md#8.2", "decision-logs.md#adr-002", "decision-logs.md#adr-004"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 35, "id": 6155612323, "url": "https://github.com/Keshav0375/FinAdvisor/issues/35"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
A pytest leak-matrix harness proves cross-tenant read, insert, update, delete into PUBLIC, FK existence probes and fail-closed on every table, and reports leaks = 0.

## Description
Build the L0 leak matrix (deep-dive/05-1-rls-indexes-versioning-and-deletion.md §5.4: "The write split and the PUBLIC rule are tested by the L0 leak matrix"; 8.5 leak-path controls). `tests/leak/` with a harness: seed tenants A, B and PUBLIC (plus advisors with different tiers and roles) through `fa_owner`; helper `as_role(role, principal_settings)` opening a connection as that role's login and running statements inside a transaction with `set_config(..., true)`. A result collector counts a *leak* whenever a forbidden statement succeeds or returns a foreign row; the suite fails if `leaks != 0` and prints `LEAKS=<n>` in the output.

Matrix cases in this ticket, over every tenant table (parametrised from `pg_class` so a new table without a case fails):
1. Cross-tenant read: for each role holding SELECT (`fa_app`, `fa_worker`, `fa_etl`, `fa_dbt`, `fa_eval`) bound to tenant A, selecting from each table returns no tenant B row.
2. Cross-tenant insert: for each role holding INSERT, inserting a row with tenant B's `tenant_id` while bound to A raises a row-level-security violation or permission denied.
3. Update and delete into PUBLIC: `fa_worker`, `fa_etl`, `fa_app` (where granted) cannot INSERT, UPDATE or DELETE rows with the PUBLIC `tenant_id`; only `fa_etl_public` can, and only for PUBLIC.
4. FK existence probes: as tenant A, inserting `chunks`, `conversations`, `escalations`, `acl_change_requests` rows referencing ids of tenant B's `documents` / `advisors` fails with a foreign-key violation whose message is the same as for a nonexistent id (no oracle) or a permission error; cross-tenant composite pairs `(A, id_of_B)` fail.
5. Fail-closed: with `app.tenant_id` unset (new transaction on a fresh connection), every SELECT on a tenant table by a policy-bound role raises an error and returns zero rows.

Out of scope: direct partition access, self-escalation, pooled reuse, EXPLAIN pruning and CI gate wiring (E1-T20).

## Acceptance criteria
- [ ] Given the matrix runs against the migrated schema, then `pytest tests/leak -k 'read or insert or public or fk or failclosed'` passes and its output contains `LEAKS=0`.
- [ ] Given a deliberately weakened policy in a negative test (e.g. `chunks_select_pipe` USING (true) in a scratch database), then the matrix reports `LEAKS` greater than 0 and the test asserting detection passes.
- [ ] Given a new table is added to the schema without a matrix case, then `tests/leak/test_coverage.py` fails (table list from `pg_class` must equal the set of tables covered).
- [ ] Given case 4 for a nonexistent id and for an id of tenant B, then the error class and SQLSTATE are identical for both (no existence oracle) or both permission denied.
- [ ] Given case 3, then `fa_etl_public` inserting into tenant A raises a row-level-security violation (the only PUBLIC writer cannot write tenants).
