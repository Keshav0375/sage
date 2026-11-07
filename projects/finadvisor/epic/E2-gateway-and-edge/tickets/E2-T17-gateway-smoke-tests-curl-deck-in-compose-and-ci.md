---
key: "E2-T17"
title: "Gateway smoke tests (curl/deck) in compose and CI"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T14", "E2-T15", "E2-T16"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.3", "deep-dive/06-interfaces-and-contracts.md#6.5", "deep-dive/08-security-and-privacy.md#8.5", "plan.md#e2"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 55, "id": 6155636206, "url": "https://github.com/Keshav0375/FinAdvisor/issues/55"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
One repeatable suite proves the limits, size cap, header stripping and no-token-leak behaviour end to end locally.

## Description
Done-when of the epic (E2 section of plan.md). Quote: 'a smoke test shows 429 with Retry-After for the IP limit and the session-key limit, 413 over the size limit, and client-supplied X-User-Id / X-Tenant-Id / X-Serverless-Authorization / X-RL-Key never reaching chat-api; no raw bearer token appears in Valkey keys or in file-log output.' Implement tests/gateway/smoke.sh (curl plus deck where useful, with a browser-like User-Agent if bot-detection blocks curl) run by `make gateway-smoke` against compose with the stub and wired as a CI job. Fixes G-14 (the MVP identifier parameter did not exist) and G-46 (CORS) by test.

## Acceptance criteria
- [ ] Given compose up, when `make gateway-smoke` runs, then it exits 0 and prints PASS for each of: ip_limit_429_retry_after, session_limit_429_retry_after, size_413, header_spoof_stripped, no_raw_token_in_valkey, no_raw_token_in_filelog, unknown_route_404.
- [ ] Given a deliberately broken kong.yml (rate-limit plugin removed), then the same suite exits non-zero at ip_limit or session_limit (mutation test in tests/gateway/test_smoke_can_fail.sh).
- [ ] Given the CI workflow, then a job runs the suite and a failing assertion fails the PR.
