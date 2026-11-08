---
key: "E10-T1"
title: "Spike: measure Cloud SQL start time and stopped billing"
epic: "E10"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["deep-dive/10-open-questions.md#10 item 6", "ADR-020", "deep-dive/02-quality-attributes.md#2.5"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 230, "id": 6263638272, "url": "https://github.com/Keshav0375/FinAdvisor/issues/230"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Measure stopped-to-RUNNABLE time and confirm a stopped instance bills storage only, recorded as an ADR.

## Description
Overview section 10 item 6: the stopped-to-RUNNABLE time of Cloud SQL is undocumented; measure it. Also confirm stopped-instance billing is storage only (ADR-020: 'The idle estimate assumes a stopped instance bills storage only; unverified').

Build: scripts/spikes/cloudsql_start_time.sh that, against a throwaway Cloud SQL PostgreSQL 16 Enterprise 2 vCPU / 8 GiB instance created with gcloud (not Terraform, same size as ADR-020, with ~10 GB of data and private IP via PSC if the E2 VPC exists, otherwise public IP for the throwaway only), runs N=5 cycles of: patch --activation-policy=NEVER, wait STOPPED, patch --activation-policy=ALWAYS, record seconds until state RUNNABLE and until a psql SELECT 1 succeeds. Then leave the instance stopped for >= 24 h and read the Cloud Billing export / SKU lines for that instance to confirm only storage (and reserved IP, if any) is billed. Delete the throwaway instance.

Output: docs/adr/cloud-sql-start-time.md with the measured table (per cycle: seconds to RUNNABLE, seconds to first query), min/median/max, the billing finding, and a recommendation for the demo-up wait timeout (used by E10-T18). Context for the researcher: the file is copied into decision-logs.md later.
Out of scope: the demo-up script itself (E10-T17), Terraform for Cloud SQL (E10-T6).

## Acceptance criteria
- [ ] docs/adr/cloud-sql-start-time.md exists and contains a table with 5 measured cycles (seconds to RUNNABLE and to first SELECT 1), plus min, median and max; a file with fewer than 5 rows fails the check `grep -c '^| [0-9]' docs/adr/cloud-sql-start-time.md` >= 5
- [ ] The ADR states, with a billing-export SKU list or screenshot reference, whether a stopped instance bills storage only; if any other SKU is billed the ADR gives its monthly amount and the idle estimate delta against the 40-55 USD range
- [ ] The ADR gives a recommended demo-up wait timeout equal to the max measured start time plus a stated margin
- [ ] After the spike `gcloud sql instances list` shows no throwaway instance (command output attached in the PR)
