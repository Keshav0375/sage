---
key: "E2-T22"
title: "Spike: ALB host rules for per-cell hostnames"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T8", "E2-T5", "E2-T3"]
arch_refs: ["decision-logs.md#adr-031", "deep-dive/04-components-and-responsibilities.md#4.24", "deep-dive/06-interfaces-and-contracts.md#6.11"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Prove on a real global external ALB that host rules route two per-cell hostnames to two different backends with the Host header preserved, and record cost and verdict.

## Description
Spike named in ADR-031: "ALB host rules are an unpriced spike" and "Trigger to revisit ... ALB host-rule spike fails". Under test: the SPA talks to a per-cell hostname chosen by `GET /resolve?slug=` (deep-dive/06 section 6.11), and the ALB must route by host to that cell's gateway.

Build `terraform/spikes/alb_host_rules/` (throwaway, destroyed after the run) reusing the E2-T8 module: two hostnames `cell-a.<domain>` and `cell-b.<domain>` on one managed certificate, two stub backends from E2-T3 (each returning its own `X-Cell` header) behind two serverless NEGs and two backend services, and host rules mapping each hostname to its backend. Measure:
1. `curl --resolve` with each hostname returns the matching `X-Cell` value; an unknown host gets the default backend, not a cell.
2. The `Host` header the stub sees equals the requested hostname.
3. One certificate with both names is served for both hostnames (SAN check with `openssl s_client`).
4. Latency added by host matching: 200 requests per hostname, p50 and p95, against the single-host E2-T8 URL map.
5. The monthly cost lines the second backend service, NEG and certificate add, read from the billing catalog (the spike is unpriced in the arch).
Record `docs/adr/alb-host-rules.md` with the line `ALB_HOST_RULES=pass` or `ALB_HOST_RULES=fail`, the numbers and the cost. On `fail` the ADR names the ADR-031 trigger and the fallback (path prefix per cell or one hostname with the router in `/resolve`) for the researcher to decide; nothing else changes.

Out of scope: `cells.json`, the SPA, the second deployed cell (E13).

## Acceptance criteria
- [ ] Given the spike stack, when each of the two hostnames is requested through the ALB, then `X-Cell` equals `a` for cell-a and `b` for cell-b in 100 of 100 requests each, and an unknown Host never returns a cell header (`tests/spikes/test_alb_host_rules.py`, run against the spike stack).
- [ ] Given a request to cell-a, then the stub's echo shows `Host: cell-a.<domain>` (the host reaches Kong's upstream unchanged).
- [ ] Given `openssl s_client -servername` for both hostnames, then the same certificate serving both names is returned and verifies.
- [ ] The file `docs/adr/alb-host-rules.md` contains exactly one line matching `^ALB_HOST_RULES=(pass|fail)$`, a p50/p95 table of 200 requests per hostname and the monthly cost of the added resources.
