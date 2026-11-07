---
key: "E11-T1"
title: "Spike: FCA Handbook API format and rate limit"
epic: "E11"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/11-tech-stack.md#source-connectors-r4", "deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "decision-logs.md#adr-26"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Record the real FCA API response format and rate behaviour so the fca_api throttle can be set.

## Description
Probe the FCA Handbook API (COBS 9A and 6) with a free account login and record: the JSON response format (UNVERIFIED in the evidence: "JSON format not seen"), the rate-limit behaviour ("rate-limited per authenticated user and endpoint path", no number), the response for a past date (docs say current and future versions only), the `Last modified` signal, and the status codes for a revoked or suspended login (401, 403).

Arch (deep-dive/11-tech-stack.md, Source connectors): FCA throttle "set when the format is seen (E11)". Output: a short note under `docs/` of the FinAdvisor repo plus recorded sample responses (no FCA text beyond what is needed for a fixture; stored only in the PUBLIC fixtures folder) and the chosen `rate_limit_rps` for `fca_api` written into config. The result is recorded as an ADR addendum by the orchestrator, not by this ticket.

Out of scope: the connector itself (E11-T20); any Handbook crawling (arch: current text only, no crawling).

## Acceptance criteria
- [ ] The note names the observed response format, the observed rate limit or states that none was reached after N requests at the tested rate, and the status code seen for a past-date request.
- [ ] A recorded fixture file for one COBS 9A module response exists and parses with the sample loader (`backend/tests/fixtures/fca_api/test_sample_loads` passes).
- [ ] `FCA_API_RATE_LIMIT_RPS` is set in config with the value justified in the note; a test (`test_fca_rate_limit_config_present`) fails if the key is missing.
