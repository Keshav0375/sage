---
key: "E0-T15"
title: "Add test helpers: VCR replay, race harness, Kafka-off"
epic: "E0"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T11", "E0-T12"]
arch_refs: ["deep-dive/11-tech-stack.md#test-harnesses", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "decision-logs.md#adr-017", "decision-logs.md#adr-026", "decision-logs.md#adr-028"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The foundation ships three reusable test helpers that later epics (E11, E12) import: recorded-fixture HTTP replay, an erase-versus-indexer race harness and a way to stop Kafka in the compose stack.

## Description
Why: round 4 adds connectors that must run in the PR gate without live sources, deletion paths that must survive interleavings, and a delete path that must work with Kafka stopped. Arch (deep-dive/11-tech-stack.md, Test harnesses): "a race harness for erase vs indexer interleavings; recorded-fixture (VCR-style) HTTP replay for connectors in the PR gate, live source smoke weekly". ADR-017/026/028 name the use. Library choice is open in the arch ("libraries not chosen by the decision"): pin the chosen replay library in `backend/poetry.lock` and record the name in `docs/testing.md`.

Build under `backend/tests/helpers/`:
1. `http_replay.py`: a pytest fixture `replay(cassette_name)` that serves recorded HTTP request/response pairs from `backend/tests/fixtures/cassettes/` and FAILS the test on any request with no matching recording (no network fall-through) when `REPLAY_STRICT=1` (the default in CI). A `--record` mode (env `REPLAY_RECORD=1`) is allowed locally only and refuses to run when `CI=true`. Authorization and API-key headers are scrubbed from stored cassettes.
2. `race_harness.py`: `run_interleavings(step_a, step_b, n, seed)` runs two async step sequences (for example `erase` and `index`) in `n` seeded interleavings against the integration Postgres, yielding a result per interleaving and failing with the seed when an invariant callback returns false. Deterministic for a given seed.
3. Compose: `make kafka-stop` and `make kafka-start` (`docker compose stop kafka` / `start kafka` and wait for healthy) plus a pytest fixture `kafka_stopped` (integration marker) that stops the broker for the test and restarts it at teardown. This is the setup for edge case #7 (erasure with Kafka stopped), which E12 uses.

Out of scope: any connector, erasure or indexer logic (E11, E12), the weekly live-source smoke job, the two-cell compose suite (E13).

## Acceptance criteria
- [ ] Given a cassette with one recorded GET and `REPLAY_STRICT=1`, when the test issues that GET it receives the recorded body, and when it issues a different URL the test fails with a no-matching-recording error (`tests/helpers/test_http_replay.py::test_unmatched_request_fails`).
- [ ] Given a stored cassette, then `grep -il 'authorization\|api-key' backend/tests/fixtures/cassettes` returns nothing, and `REPLAY_RECORD=1 CI=true` exits non-zero (`test_record_refused_in_ci`).
- [ ] Given a deliberately racy toy pair (check-then-act without a lock) and `run_interleavings(..., n=200, seed=1)`, then the harness reports at least one violating interleaving with its seed, and the same seed reproduces it; given the locked version it reports none (`tests/helpers/test_race_harness.py::test_detects_and_reproduces_race`).
- [ ] Given `kafka_stopped`, when a test runs inside it, then `docker compose ps --format json kafka` shows the broker not running inside the test and healthy again after teardown (`tests/integration/test_kafka_stopped_fixture.py`).
