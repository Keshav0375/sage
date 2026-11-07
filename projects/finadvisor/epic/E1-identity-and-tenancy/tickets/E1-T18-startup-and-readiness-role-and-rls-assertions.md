---
key: "E1-T18"
title: "Startup and readiness role and RLS assertions"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T8", "E1-T9", "E1-T10", "E1-T11"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.3", "deep-dive/04-components-and-responsibilities.md#4.8", "decision-logs.md#adr-002"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 34, "id": 6155611007, "url": "https://github.com/Keshav0375/FinAdvisor/issues/34"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
chat-api, migrate and /readyz refuse to run when the DB role or schema posture violates the arch.

## Description
Implement deep-dive/05-data-model-and-storage.md §5.3: "Startup and `/readyz` assert, for the connected role: not superuser, not BYPASSRLS, not owner of any table (except the two exemptions above), FORCE ROW LEVEL SECURITY on every table in the tenant schemas including partitioned parents, pgvector version >= 0.8, the expected policies exist, and that the partitions of `chunks` and `messages` carry no grants to runtime roles (D16.3). A failure refuses to start (fail to boot)." The `migrate` job also "asserts role flags, FORCE RLS and that partitions carry no runtime grants" (4.8).

Build `src/db/posture.py`: `async assert_db_posture(conn, *, role_exemptions)` returning a list of violations and raising `PostureError` if any. Checks: `rolsuper`, `rolbypassrls` false for `current_user`; no table owned by `current_user` except `gold` objects for `fa_dbt` and `messages` (and its partitions) for `fa_maint`; `relforcerowsecurity` true on every table in the app schemas including partitioned parents; `extversion` of `vector` >= 0.8; every policy in a manifest `EXPECTED_POLICIES` (generated from the E1-T8 to E1-T10 migrations, listing `(table, policyname, roles)`) exists, and a test proves the manifest equals `pg_policies` so drift fails; no runtime role (`fa_app, fa_worker, fa_etl, fa_etl_public, fa_dbt, fa_eval, fa_maint`) holds any privilege on a partition of `chunks` or `messages`.
Wiring: call it in the FastAPI lifespan (exit non-zero on failure), expose it in `/readyz` (503 with violation names, no details of data), and call it at the end of `migrate` (as `fa_owner`, with owner exemption for the migrate role).

Out of scope: worker pool and jobs entrypoint wiring beyond `migrate` and `chat-api` (each later epic calls the same function).

## Acceptance criteria
- [ ] Given a Postgres connected as a superuser, or as a role with BYPASSRLS, or as `fa_owner` (the table owner), when the app starts, then it exits non-zero and logs the violated check (3 cases in `tests/db/test_posture.py` using throwaway roles).
- [ ] Given `ALTER TABLE chunks NO FORCE ROW LEVEL SECURITY` (the partitioned parent) or the same on `documents`, then `assert_db_posture` reports the table and `/readyz` returns 503.
- [ ] Given `GRANT SELECT ON <a chunks partition> TO fa_app`, or a grant on a `messages` partition, then the check fails; with grants absent it passes.
- [ ] Given the connected role is `fa_dbt` with only the `gold` schema owned, or `fa_maint` owning only `messages`, then the check passes (exemption tests); `fa_maint` owning any other table fails.
- [ ] Given a policy is dropped, then the check fails because the manifest lists it; and a test asserts `EXPECTED_POLICIES` equals the set in `pg_policies` after `alembic upgrade head`.
- [ ] Given pgvector 0.7 (simulated by patching the version query), then the check fails.
