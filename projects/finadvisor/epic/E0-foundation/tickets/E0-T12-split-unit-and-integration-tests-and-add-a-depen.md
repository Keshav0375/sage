---
key: "E0-T12"
title: "Split unit and integration tests and add a dependency start script"
epic: "E0"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T3", "E0-T9", "E0-T11"]
arch_refs: ["deep-dive/01-context-and-goals.md#1", "deep-dive/06-interfaces-and-contracts.md#6.6", "decision-logs.md#adr-021", "deep-dive/11-tech-stack.md#kafka-client"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 13, "id": 6155583763, "url": "https://github.com/Keshav0375/FinAdvisor/issues/13"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Tests are marked unit or integration, integration tests cannot silently skip when services are required, and one command starts the dependencies and runs them.

## Description
Why: the suite shows `97 passed, 25 skipped`: every DB test uses `requires_db`, which skips silently when Postgres is absent and hard-codes `localhost:5432` with the `localdev` password in `backend/tests/conftest.py`. A CI that skips them is green and dishonest (G-05 intent: CI can fail). builder:engineering needs "a way to start dependencies for integration tests".

Do:
- Register pytest markers `unit` (default for tests without a marker) and `integration` in `backend/pyproject.toml`; mark all DB-backed tests (`requires_db` users: test_rls, test_rls_context, test_rls_e2e, test_integration, test_search_kb and similar) as `integration`.
- `conftest.py`: build the test database URL from the Settings env keys (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`), not a literal. When env `REQUIRE_SERVICES=1` is set, an unreachable database makes the test fail (not skip).
- Add `backend/tests/integration/test_kafka_reachable.py`: lists topics through the Kafka admin client against `KAFKA_BOOTSTRAP` (test-only env var for now; add `confluent-kafka==2.16.1` to the dev group, deep-dive/11-tech-stack.md pin) and fails if the broker is unreachable. The same test is skipped unless `REQUIRE_SERVICES=1` or the broker answers.
- Add a `Makefile` at the repo root with targets `deps-up` (`docker compose up -d --wait postgres kafka migrate`), `deps-down` (`docker compose down -v`), and `test-integration` (`deps-up` then `REQUIRE_SERVICES=1 pytest -m integration`, then `deps-down` on exit), plus `test-unit` (`pytest -m "not integration"`).

Out of scope: the CI workflow (E0-T13), the eval gate (E7), Kafka produce/consume logic (E5).

## Acceptance criteria
- [ ] `cd backend && pytest -m "not integration" -q` passes with Postgres stopped and reports 0 skipped.
- [ ] Given Postgres stopped and `REQUIRE_SERVICES=1`, `pytest -m integration` fails (non-zero exit, tests reported failed, not skipped); given Postgres stopped and `REQUIRE_SERVICES` unset the tests skip with a reason naming the missing service.
- [ ] `make test-integration` on a clean machine brings up postgres and kafka, runs the integration tests with 0 skipped and 0 failed, and removes the containers afterwards (`docker compose ps -a` empty).
- [ ] `grep -rn "localdev" backend/tests` returns no match.
- [ ] `pytest --collect-only -m integration -q` lists every test that previously used `requires_db` (count equals the 25 formerly skipped tests, none lost).
