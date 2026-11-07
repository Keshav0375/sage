---
key: "E2-T10"
title: "Spike: Cloud Armor cost from the billing catalog"
epic: "E2"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/10-open-questions.md#10", "deep-dive/04-components-and-responsibilities.md#4.2", "decision-logs.md#adr-012"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 48, "id": 6155627940, "url": "https://github.com/Keshav0375/FinAdvisor/issues/48"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Replace the UNVERIFIED Cloud Armor estimate with SKU prices and a computed monthly figure for the planned rule set.

## Description
Overview 10 item 9 (Cloud Armor part), 4.2 and ADR-012. Quote 4.2: 'Cost ~$0.75/1M requests + policy fee: exact cost UNVERIFIED.' Pull the Cloud Armor SKUs from the Cloud Billing Catalog API (policy fee, rule fee, per-million-request charge, any WAF/advanced charges), commit the query script (spikes/e2/armor-cost/), and compute the monthly cost for the planned policy: preconfigured WAF rules, geo rule, one coarse per-IP throttle rule (propose the rule count here for E2-T18) at 0, 1M and 5M requests per month. The idle-budget figure to compare against is the ~$6-10/month in ADR-012 / overview section 10. Confirming against the billing export happens in E10 during the cost month; note it. Out of scope: Confluent cost.

## Acceptance criteria
- [ ] Given the script, when run, then it prints each SKU id, unit price and currency, and exits non-zero if a Cloud Armor SKU is not found (test with a bogus service filter).
- [ ] Given the planned rule set, then the ADR table shows total monthly cost at 0, 1M and 5M requests; pass if the 0 request figure is <= $10/month.
- [ ] ADR exists with verdict. The result is recorded as an ADR file in the repo (see question 1 for location and numbering) containing the measured values, the pass/fail verdict and the named fallback. Trigger from ADR-012: if the idle budget fails, escalate to the researcher; the ticket does not remove Armor on its own.
