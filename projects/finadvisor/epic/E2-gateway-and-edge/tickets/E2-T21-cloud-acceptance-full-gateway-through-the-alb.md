---
key: "E2-T21"
title: "Cloud acceptance: full gateway through the ALB"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T9", "E2-T17", "E2-T18", "E2-T19", "E2-T20", "E1-T21", "E10-T18"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.1", "deep-dive/04-components-and-responsibilities.md#4.3", "deep-dive/08-security-and-privacy.md#8.3", "deep-dive/10-open-questions.md#10", "decision-logs.md#adr-011", "decision-logs.md#adr-012", "decision-logs.md#adr-023", "decision-logs.md#adr-024"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 59, "id": 6155640891, "url": "https://github.com/Keshav0375/FinAdvisor/issues/59"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Deploy the final kong.yml to fa-gateway and verify every done-when item in the cloud, re-measuring SSE with the full plugin set.

## Description
Done-when of the E2 section of plan.md. Deploy the final image to fa-gateway with CHAT_API_URL, Valkey endpoint (question 12: a manually created Memorystore Valkey instance outside Terraform, as in 4.6), CORS origin and secrets; run against the ALB domain. Re-run the E2-T9 SSE measurement with every plugin active (pre-function, rate-limiting on Valkey, file-log, opentelemetry, prometheus) and `response_buffering: false`. The chat-api target is the real service if E1/E4 have deployed it, otherwise the E2-T3 stub with the same IAM settings (question 15). Record all results in the PR and, for the measurements, in an ADR note appended to the E2-T9 ADR.

## Acceptance criteria
- [ ] Given the full plugin set, then SSE through ALB and Kong adds <= 50 ms p95 over the direct stream (2,000+ events per path, numbers recorded; fails the ticket otherwise).
- [ ] Given the E2-T17 smoke assertions run against https://<domain>/v1/..., then 429 with Retry-After (IP and session), 413 and header-spoof stripping all pass.
- [ ] Given an in-VPC call to chat-api carrying only a user bearer and no Kong ID token, then it is rejected (HTTP 403 from Cloud Run IAM); given the same call through Kong, then 200 (or the E2-T7 fallback is in place and the ADR says so).
- [ ] Given `gcloud compute routers nats list` is empty and Kong still reaches chat-api, then the no-NAT path works (or the E2-T6 fallback ADR is in place).
- [ ] Given the traffic, then rows reach BigQuery gateway_audit and Valkey scans show no raw bearer (reuse E2-T19 and E2-T14 tests against the cloud).
