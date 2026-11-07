---
key: "E11-T16"
title: "sec connector: 497K per-CIK submissions"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T6", "E11-T7", "E11-T14", "E11-T9"]
arch_refs: ["deep-dive/11-tech-stack.md#source-connectors-r4", "deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "deep-dive/06-interfaces-and-contracts.md#6.7", "decision-logs.md#adr-26"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Implement the 497K publisher-document connector with declared User-Agent at 2 rps.

## Description
Implement the 497K half of `sec` (target a firm tenant, class `publisher`, `licence_class=publisher`, erase on withdraw; `private_demo`).

Arch: per-CIK submissions JSON on data.sec.gov plus daily-index; a declared User-Agent is required (config `SEC_USER_AGENT`, startup fails if absent); <= 2 rps against the 10 req/s vendor maximum; filings are immutable (a new accession for each change); no per-filing delete signal, so a weekly Saturday full-index comparison is the only removal signal: a missing accession is a `withdrawn` candidate and then follows the two-strike rule (E11-T8). Cadence daily and weekly. Bronze goes to the firm tenant's private bucket only; never to the public repo or a public eval set. Runs only if the E11-T14 egress check passes.

Out of scope: the RR datasets (E11-T17), the fee-table contract (E11-T11).

## Acceptance criteria
- [ ] Given the recorded per-CIK fixture then `list()` returns accession numbers as `external_id` and `version_key`, and `classify()` returns `licence_class=publisher` (test `backend/tests/connectors/test_sec_497k.py::test_list_and_classify_fixture`).
- [ ] Given `SEC_USER_AGENT` is unset then the connector refuses to start; every request carries it when set, and the rate does not exceed 2 rps (tests `test_user_agent_required`, `test_throttle_2_rps`).
- [ ] Given a Saturday full-index fixture that omits an accession seen last week then a withdrawal candidate is recorded, and not applied until the second listing (test `test_weekly_index_missing_accession_two_strike`).
- [ ] Given the target tenant has `llm_egress_ack=false` then the run is refused (test `test_497k_requires_egress_ack`).
- [ ] No fixture file or bronze object of this connector is under the public repo path or the public eval set (test `test_private_demo_fixtures_not_in_public_paths`).
