---
key: "E11-T19"
title: "legislation_gov_uk connector: point-in-time XML"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T6", "E11-T7", "E11-T9"]
arch_refs: ["deep-dive/11-tech-stack.md#source-connectors-r4", "deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "deep-dive/06-interfaces-and-contracts.md#6.7", "decision-logs.md#adr-26"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Implement the legislation.gov.uk connector inside the stricter fair-use reading.

## Description
Implement `legislation_gov_uk` (PUBLIC, class `law`, retire; `licence_class=ogl`; `valid_from_basis='observed'` for UK sources per the plan).

Arch: XML API (CLML), User-Agent mandatory; point-in-time URLs; no bulk dump; fair use 1,500 requests per 5 min (stricter reading; the docs also say 3,000, an unresolved conflict, so 1,500 is used), 403 on breach; our throttle 1 rps (300 per 5 min); incremental `/update/data.feed` publication log filtered to the three items; titles "(revoked)" are the delete signal; `hasVersion` list per item (PRIIPs 12, 2017/653 8, 2017/565 17) as the backstop; effects lag 4-8 weeks, so a known unapplied change is a `pending` observation (shown as a warning, never as text). A 403 suspends the connector (shared rule with E11-T22).

Out of scope: other UK sources.

## Acceptance criteria
- [ ] Given the recorded fixture then `hasVersion` lists produce the counts 12, 8 and 17 for the three items (test `backend/tests/connectors/test_legislation_gov_uk.py::test_has_version_counts`).
- [ ] Given a title containing "(revoked)" then a retire-class withdrawal candidate is recorded after two listings (test `test_revoked_title_is_withdrawal_signal`).
- [ ] Given a 403 response then the connector sets `frozen` with reason `http_403` and stops (test `test_403_freezes_connector`).
- [ ] Given any run then requests do not exceed 300 per 5 minutes (fake clock test `test_throttle_inside_fair_use`).
