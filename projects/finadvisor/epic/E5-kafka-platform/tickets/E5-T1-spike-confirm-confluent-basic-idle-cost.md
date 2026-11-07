---
key: "E5-T1"
title: "Spike: confirm Confluent Basic idle cost"
epic: "E5"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["decision-logs.md#adr-013", "deep-dive/06-interfaces-and-contracts.md#6.4"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 78, "id": 6155662379, "url": "https://github.com/Keshav0375/FinAdvisor/issues/78"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Measure the real idle monthly cost of a Confluent Cloud Basic cluster and record it as an ADR.

## Description
ADR-013 quotes ~$0-10/month for Confluent Cloud Basic (first eCKU free then $0.14/eCKU-h, $0.05/GB; Essentials Schema Registry free to 100 schemas) and marks it UNVERIFIED: 'confirm in console'. Create the Basic cluster in us-central1 FIRST (the Schema Registry region is fixed by the first cluster, D13q), leave it idle with one test topic for at least 24 h, read the cost and usage view in the console, and project the monthly idle cost with the demo up and down. Record the result as a new ADR in projects/finadvisor/arch/decision-logs.md (status, measured numbers, date, console screenshot path or figures, decision to keep or revisit). Out of scope: Terraform, service accounts, topics for the product (E5-T13).

## Acceptance criteria
- [ ] Given the cluster has been idle 24 h, when the console cost view is read, then the ADR records the measured idle cost per day in USD and the projected monthly figure, replacing the UNVERIFIED label.
- [ ] Given the ADR, when read, then it states the cluster region (us-central1) and the Schema Registry region, and whether the projection is within the ADR-013 estimate of $0-10/month (yes/no with the figure).
- [ ] Given the ADR is merged, when `grep -n 'UNVERIFIED' decision-logs.md` is run on the ADR-013 cost line, then it is annotated with a pointer to the new ADR.
