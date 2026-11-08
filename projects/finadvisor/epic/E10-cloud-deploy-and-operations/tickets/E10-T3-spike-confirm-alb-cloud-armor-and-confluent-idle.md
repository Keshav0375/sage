---
key: "E10-T3"
title: "Spike: confirm ALB, Cloud Armor and Confluent idle cost"
epic: "E10"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["deep-dive/02-quality-attributes.md#2.5", "deep-dive/10-open-questions.md#10 item 9", "ADR-012"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 251, "id": 6263673657, "url": "https://github.com/Keshav0375/FinAdvisor/issues/251"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Confirm the unverified idle cost items (ALB forwarding rule, Cloud Armor policy, Confluent Basic) against pricing and billing, as an ADR.

## Description
Overview section 2.5 and section 10 item 9: ALB 18.25 USD/month is a list-price figure, Cloud Armor ~6-10 USD and Confluent Basic ~0-5 USD are UNVERIFIED. ADR-012 trigger to revisit: 'Cloud Armor cost verification fails the idle budget'.

Build: docs/adr/idle-cost-confirmation.md containing, for us-central1: the external Application Load Balancer forwarding-rule hourly SKU x 730 h, the Cloud Armor policy and rule fees (count the actual rules in terraform/edge/ from E2) and per-request charge at the 2,000-chat demo month, the Confluent Basic cluster hourly/base cost plus ingress/egress/storage for the demo month, and Cloud SQL stopped storage (from E10-T1). Take SKUs from the Cloud Billing catalog (`gcloud billing` / Cloud Billing Catalog API) and the Confluent pricing page, and where the E2 edge and E5 Confluent resources already exist, cross-check against the real billing export lines of the last full day. Sum to an idle total.

Out of scope: changing the architecture; if the total exceeds 55 USD/month the ADR says so and the finding goes to the researcher.

## Acceptance criteria
- [ ] docs/adr/idle-cost-confirmation.md lists each idle line item with SKU id or pricing URL, unit price, quantity and monthly amount for ALB, Cloud Armor, Confluent Basic, Cloud SQL storage, Artifact Registry/Secrets/GCS/logs
- [ ] The ADR gives a summed idle monthly total and states pass or fail against the 40-55 USD idle range of deep-dive/02-quality-attributes.md §2.5; a missing total or missing verdict fails review
- [ ] Each previously UNVERIFIED value (Cloud Armor, Confluent Basic) is replaced by a number with its source, or is marked still unverified with the reason
