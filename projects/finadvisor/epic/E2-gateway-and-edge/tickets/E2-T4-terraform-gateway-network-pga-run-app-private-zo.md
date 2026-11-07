---
key: "E2-T4"
title: "Terraform: gateway network (PGA, run.app private zone)"
epic: "E2"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/08-security-and-privacy.md#8.3", "deep-dive/04-components-and-responsibilities.md#4.3", "decision-logs.md#adr-024"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 42, "id": 6155620869, "url": "https://github.com/Keshav0375/FinAdvisor/issues/42"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Create the subnet settings and Cloud DNS private zone that let Cloud Run services reach internal run.app URLs through the VPC with no Cloud NAT.

## Description
ADR-024 and deep-dive/04-components-and-responsibilities.md §4.3 / 8.3 network rows. In terraform/edge/ (question 3 on overlap with E10 and on the existing MVP terraform/): a subnet in the VPC with private_ip_google_access = true; a Cloud DNS private zone for run.app. attached to the VPC mapping run.app to private.googleapis.com (CNAME on *.run.app. plus the private.googleapis.com A records 199.36.153.8-11); outputs (network, subnetwork) consumed by Cloud Run services for Direct VPC egress with vpc_access egress PRIVATE_RANGES_ONLY. No Cloud NAT, no Serverless VPC Access connector. Out of scope: the Cloud Run services (E2-T5), SQL PSC (E10).

## Acceptance criteria
- [ ] Given `terraform validate` in terraform/edge/, then it exits 0; `terraform plan` shows private_ip_google_access = true and a private managed zone with dns_name run.app.
- [ ] Given a CI/policy check (script or conftest rule), when a google_compute_router_nat or a vpc_access_connector resource is added to terraform/, then the check fails (negative fixture included and asserted to fail).
- [ ] After apply in the test project, `gcloud dns managed-zones describe` shows visibility private bound to the VPC, and `gcloud compute routers nats list` returns nothing.
