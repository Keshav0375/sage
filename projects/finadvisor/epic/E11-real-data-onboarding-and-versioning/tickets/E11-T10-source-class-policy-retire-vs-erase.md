---
key: "E11-T10"
title: "Source class policy: retire law, erase publisher and FCA"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T8", "E11-T9", "E12-T5"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.9", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.11", "deep-dive/06-interfaces-and-contracts.md#6.7", "decision-logs.md#adr-26"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Apply retire or erase on withdrawal by source class, and create the fund_rr_facts table.

## Description
Implement the withdrawal handler selected by `source_registry.on_withdraw`.

Arch: `law` and `qa` are RETIRED on withdrawal: `valid_to` set (`valid_range` upper), text kept so as-of questions still work; `fca_api` and `publisher` are ERASED: a `deletion_requests` row is inserted (scope `document`, reason `source_withdrawal`) and executed by E12 (this ticket inserts the row directly into `deletion_requests`, created by E12-T5; no stub). `pending` observations (legislation.gov.uk known change not yet applied) are stored as `status='known_pending'` and never shown as text; retrieval is unaffected and the compliance check warning is E4's.

Also create `fund_rr_facts` here (arch: "PUBLIC, source_class `law`, RETIRE"): key `(tenant_id = PUBLIC, id)`; columns fixed by this ticket (fund series, fact name, value, period, source version) with `fa_etl_public` write, every tenant read, ENABLE + FORCE RLS.

Out of scope: erasure execution (E12), the RR loader (E11-T17).

## Acceptance criteria
- [ ] Given a withdrawn `law` item then `valid_range` upper is set, the version row and chunks remain and a question as of a date inside the old range still returns it (test `test_withdraw_policy.py::test_law_retired_text_kept`, PR).
- [ ] Given a withdrawn `publisher` item and a withdrawn `fca_api` item then one `deletion_requests` row is inserted for each and no direct DELETE of chunks is issued by this code (test `test_erase_classes_insert_deletion_request`).
- [ ] Given a `pending` observation then the provision status is `known_pending` and no chunk text is added (test `test_pending_becomes_known_pending`).
- [ ] Given `fund_rr_facts` when a firm-tenant role selects then rows are readable, and an INSERT by that role is denied (L0 test `test_fund_rr_facts_rls`).
