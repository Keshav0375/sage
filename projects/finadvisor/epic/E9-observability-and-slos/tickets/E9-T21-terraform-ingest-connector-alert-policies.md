---
key: "E9-T21"
title: "Terraform: connector frozen, quarantine and silent-edit alerts"
epic: "E9"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E9-T11", "E9-T5", "E11-T7", "E11-T12"]
arch_refs: ["deep-dive/09-observability.md#9.5", "deep-dive/09-observability.md#9.2", "deep-dive/06-interfaces-and-contracts.md#6.8", "decision-logs.md#adr-026", "decision-logs.md#adr-036"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Alert policies exist for a frozen connector, more than 5% of a batch quarantined, and a silent edit.

## Description
Implements the 9.5 alerts "a frozen connector" and the R4 epic line "a connector frozen or more than 5% of a batch quarantined", and wires the paging that E11-T7 leaves to E9 ("`silent_edit` event as a metric and a structured log; paging wiring is E9"). Add terraform/alerts_ingest.tf with the E9-T11 channel, user_label `ticket`:
- `ingest_connector_unhealthy`: two conditions combined with OR: `source_frozen{source_id,reason}` > 0 for 5 min, and the quarantine ratio over 1 h greater than 0.05, computed as the increase of `quarantined_total` summed over reasons divided by the sum of `connector_listing_items{source_id}` (the contract rule of 6.8 pauses a connector above 5% of a batch, so the second condition is the early signal in the same policy).
- `silent_edit`: increase of `source_silent_edit_total{source_id}` > 0 over 1 h.
Missing data is inactive (connectors run only while the system runs). Names come from the E9-T5 registry; the check script compares them. Out of scope: freezing logic (E11-T8, E11-T12), the drill (E9-T23).

## Acceptance criteria
- [ ] Given terraform plan, Then policies `ingest_connector_unhealthy` (2 conditions, OR combiner) and `silent_edit` exist (script assertion on `terraform show -json`).
- [ ] Given the policy JSON, Then the ratio threshold is 0.05 with comparison GT and the frozen condition threshold is 0.
- [ ] Given every metric name used in these policies, When compared with the registry, Then each exists (the check script fails on an unknown name, so a rename in E11 is caught).
- [ ] Given the E9-T23 drill sets `source_frozen{source_id="x"}` to 1 in a scratch project, Then the incident opens within 15 minutes (drill record).
