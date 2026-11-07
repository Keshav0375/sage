---
key: "E9-T8"
title: "Complete /readyz with the 9.4 checks"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T5", "E4-T7", "E5-T6"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/09-observability.md#9.4"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
/readyz asserts every item in the 9.4 list and returns a per-check result, with Kafka failing only as degraded.

## Description
Implements deep-dive/06-interfaces-and-contracts.md §6.1 and 9.4: "/readyz (DB role flags, FORCE RLS, partition grants, pgvector >= 0.8, Kafka reachability (degraded for chat), model availability, verifier initialised)". E0-T5 built /healthz and /readyz with database and model checks; E4-T7 added the retired-model check. Extend, do not rewrite:
- Checks: db_reachable, role_flags (fa_app and fa_worker lack BYPASSRLS and SUPERUSER), force_rls (every tenant table has relforcerowsecurity), partition_grants (the app roles hold privileges on the current and future partitions of chunks and messages), pgvector_version >= 0.8, kafka_reachable (metadata request with a 2 s timeout), models_available (reuse the retired-model check), verifier_initialised (firebase-admin app created).
- Response 200 {status: 'ok' or 'degraded', checks: {name: 'ok'|'fail'|'degraded'}}; Kafka failure gives status 'degraded' and HTTP 200; any other failure gives 503. No error text, hostnames or credentials in the body.
- Record readiness_failing (gauge 0/1) via metrics.record for alerting (add it to the registry and to the 9.2 test list as an addition recorded in questions if not accepted).
Out of scope: /healthz, Kong's status listener, the demo-prewarm call.
readiness_failing (gauge 0/1) is part of the 9.2 registry (R74); it is set from the same checks as /readyz on each probe and by a 15 s background task. model_retirement_days is set by the E0-T4 check at each probe.

## Acceptance criteria
- [ ] Given a test DB where fa_app has BYPASSRLS, When GET /readyz, Then status 503 and checks.role_flags='fail' (pytest test_readyz.py).
- [ ] Given a table with FORCE RLS disabled, Then 503 with force_rls='fail'; given pgvector 0.7, Then 503 with pgvector_version='fail'.
- [ ] Given the Kafka broker unreachable and everything else healthy, When GET /readyz, Then HTTP 200 with status='degraded' and kafka_reachable='degraded'.
- [ ] Given any failure, When the response body is serialised, Then it contains none of the DB host, user or exception text (assert on string).
- [ ] Given a failing check, When /readyz is probed, Then readiness_failing=1; after recovery it is 0 (pytest).
