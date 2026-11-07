---
key: "E1-T20"
title: "L0 leak matrix part 2: partitions, pooling, pruning, CI gate"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T19", "E1-T14"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.3", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.4", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.5", "decision-logs.md#adr-002", "decision-logs.md#adr-003"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 36, "id": 6155613681, "url": "https://github.com/Keshav0375/FinAdvisor/issues/36"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
The leak matrix also covers direct partition access, advisor self-escalation, pooled-connection reuse and EXPLAIN pruning, and gates every PR.

## Description
Extend `tests/leak/` (E1-T19) with the remaining cases from deep-dive/05-data-model-and-storage.md §5.3 and 5.4: "direct SELECT / INSERT on a partition as `fa_app` / `fa_worker` gives permission denied", "advisor raises own tier / role gives denied", pooled-connection reuse, and "`EXPLAIN` shows partition pruning for LIST partitions under RLS" (plan.md E1 done-when; deep-dive/05-1-rls-indexes-versioning-and-deletion.md §5.5: "the same check is repeated for LIST partitions in the E1 leak-matrix test").

Cases:
6. Direct partition access: as `fa_app` and `fa_worker`, `SELECT` and `INSERT` on the tenant's own `chunks` partition, on `chunks_public`, on `chunks_default` and on a `messages` monthly partition fail with permission denied (SQLSTATE 42501); the same statements through the parent succeed or are filtered by RLS.
7. Advisor self-escalation: an advisor binding raises its own `tier`, `role`, `jurisdictions` and `licenses`: rowcount 0 and values unchanged; `tenant_admin` of tenant A cannot change an advisor of B.
8. Pooled-connection reuse: using the real engine with `DB_POOL_SIZE=1`, request 1 is a tier-4 EU principal of tenant A, request 2 is a tier-1 US principal of tenant B on the same physical connection (assert same `pg_backend_pid()`): request 2 sees none of request 1's rows and `current_setting('app.tier', true)` is empty at the start of request 2's transaction before `scoped_tx` sets it. A third case runs a request that is cancelled mid-transaction, then reuses the connection.
9. Pruning: with partitions for at least 8 tenants plus PUBLIC and DEFAULT, `EXPLAIN (ANALYZE)` of the dense leg of the 5.6 hybrid statement as `fa_app` shows that only the caller's tenant, PUBLIC and DEFAULT partitions are executed (others "never executed" or removed by "Subplans Removed").
CI: add a required workflow job `leak-matrix` running `pytest tests/leak` on every PR (E0 CI), which fails when the output contains `LEAKS=` greater than 0 or when the job reports fewer collected tests than a pinned minimum.

Out of scope: L1-L3 evals, Kong-level tests (E2).

## Acceptance criteria
- [ ] Given `fa_app` and `fa_worker`, when each runs SELECT and INSERT on the tenant partition, `chunks_public`, `chunks_default` and a `messages` partition, then every attempt fails with SQLSTATE 42501 (`pytest tests/leak -k partition`).
- [ ] Given advisor self-escalation attempts on tier, role, jurisdictions and licenses, then rowcount is 0 and a re-read shows unchanged values (`-k escalation`).
- [ ] Given a pool of size 1 serving a tier-4 principal of tenant A then a tier-1 principal of tenant B on the same `pg_backend_pid()`, then B's queries return no A rows and no higher-tier rows, and the same holds after a cancelled transaction (`-k pooled`).
- [ ] Given 8 tenant partitions plus PUBLIC and DEFAULT, then the `EXPLAIN (ANALYZE)` text for the dense leg contains no executed scan of any other tenant's partition (`-k pruning`).
- [ ] Given the CI workflow, then a required job `leak-matrix` runs on `pull_request`, and a PR containing a weakened policy (a deliberately failing branch fixture) makes the job red with `LEAKS=` greater than 0.
