---
key: "E2-T8"
title: "Terraform: external ALB, URL map, serverless NEG"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T5"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.1", "deep-dive/04-components-and-responsibilities.md#4.24", "decision-logs.md#adr-012", "decision-logs.md#adr-031"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 46, "id": 6155625621, "url": "https://github.com/Keshav0375/FinAdvisor/issues/46"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Provide the single public entry: managed certificate, /* to the SPA bucket, /v1/* to fa-gateway.

## Description
Overview 4.1 and ADR-012. Quote: 'URL map: /* to the GCS backend bucket (SPA, CDN); /v1/* to the fa-gateway serverless NEG. Managed certificate. Persistent ... never torn down by demo-down.' In terraform/edge/: global external Application Load Balancer, reserved IP, Google-managed certificate for a domain variable, HTTP to HTTPS redirect, backend bucket (name taken from a variable, CDN on), serverless NEG and backend service for fa-gateway with an explicit timeout variable large enough for the SSE streams (E2-T9 measures what is required), URL map with the two paths. Cloud Armor is attached in E2-T18, not here. Questions 4 and 12 cover the domain and the SPA bucket owner. Out of scope: the SPA build (E8).

Round 4 (ADR-031: per-cell hostnames and ALB host rules): add a Terraform variable `cell_hostnames` (map `cell_id` to hostname, default one entry for the deployed cell) and one URL-map host rule per entry that sends `/v1/*` and `/resolve` to that cell's gateway backend service; the managed certificate lists every hostname. With one deployed cell all hostnames map to the same backend service. The apex host keeps `/*` to the SPA bucket and serves `GET /resolve`. Whether host rules work at all on the global ALB is E2-T22's spike; this ticket must not claim more than that spike proves. Cell contents (`cells.json`) are E13's.

## Acceptance criteria
- [ ] Given `terraform validate` and `terraform plan`, then the plan contains a URL map whose path matcher routes /v1/* to the gateway backend service and defaults to the backend bucket.
- [ ] Given the applied ALB, when GET https://<domain>/v1/does-not-exist is requested, then the response is Kong's 404 JSON (`no Route matched`) with a Kong Via/Server header, proving the request reached Kong.
- [ ] Given GET https://<domain>/ , then the SPA bucket object (or its 404 page) is served by the backend bucket, not Kong.
- [ ] Given the fa-gateway run.app URL requested directly from the internet, then it is still refused (as in E2-T5).
- [ ] Given `terraform plan` with `cell_hostnames = {us = "us.example.test", eu = "eu.example.test"}`, then the URL map contains one host rule per hostname routing `/v1/*` and `/resolve` to a gateway backend service, and the certificate resource lists both names (plan JSON assertion `tests/terraform/test_alb_host_rules.py`).
- [ ] Given the applied ALB and `curl --resolve us.example.test:443:<ip> https://us.example.test/resolve?slug=x`, then the response comes from Kong (Kong `Via` header).
