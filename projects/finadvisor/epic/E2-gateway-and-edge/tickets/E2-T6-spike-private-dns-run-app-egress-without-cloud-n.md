---
key: "E2-T6"
title: "Spike: private-DNS run.app egress without Cloud NAT"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T5"]
arch_refs: ["deep-dive/10-open-questions.md#10", "deep-dive/04-components-and-responsibilities.md#4.3", "deep-dive/08-security-and-privacy.md#8.3", "decision-logs.md#adr-024"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 44, "id": 6155623238, "url": "https://github.com/Keshav0375/FinAdvisor/issues/44"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Measure whether Kong on Direct VPC egress private-ranges-only reaches an internal-ingress service over the private zone while public SaaS calls still work.

## Description
Overview 10 item 3, ADR-024. Quote: 'With Direct VPC egress private-ranges-only, Private Google Access and a Cloud DNS private zone mapping run.app to private.googleapis.com, Kong reaches chat-api (ingress internal) through the VPC. Fail: all-traffic egress + Cloud NAT (about +$32/month) with an ADR.' Use the E2-T5 deployment and the E2-T3 stub as chat-api. Measurements are taken from a throwaway Cloud Run job in the same subnet and egress settings (diagnostics only, deleted afterwards). The Cloud Run IAM check on the stub still applies, so reachability is proven by the Google front end answering (HTTP 403 for a missing token) rather than a timeout; the authenticated 200 is proven in E2-T7. Include a negative control with the private zone removed.

## Acceptance criteria
- [ ] Given the diagnostic job, when it resolves the stub's run.app host, then the answers fall inside 199.36.153.8/30 (values recorded).
- [ ] Given a request to the stub's internal run.app URL from the job, then the response is HTTP 403 from the Google front end within 2 s, 200 of 200 attempts return a response (no timeouts); p50/p95 latency of 200 requests recorded.
- [ ] Given the private zone temporarily removed (control), then the same request fails differently (status or timeout recorded), proving the zone is what carries the traffic.
- [ ] Given no Cloud NAT in the project (`gcloud compute routers nats list` empty), when the job calls a public HTTPS endpoint (api.anthropic.com), then it gets a TLS response, proving public egress works without NAT.
- [ ] ADR exists confirming or superseding ADR-024. The result is recorded as an ADR file in the repo (see question 1 for location and numbering) containing the measured values, the pass/fail verdict and the named fallback. Fallback: all-traffic egress plus Cloud NAT (about +$32/month), recorded as an ADR.
