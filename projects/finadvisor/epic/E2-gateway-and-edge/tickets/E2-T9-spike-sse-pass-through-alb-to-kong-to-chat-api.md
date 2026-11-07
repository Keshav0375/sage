---
key: "E2-T9"
title: "Spike: SSE pass-through ALB to Kong to chat-api"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T8", "E2-T7"]
arch_refs: ["deep-dive/10-open-questions.md#10", "deep-dive/04-components-and-responsibilities.md#4.3", "deep-dive/04-components-and-responsibilities.md#4.1", "decision-logs.md#adr-011"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 47, "id": 6155626813, "url": "https://github.com/Keshav0375/FinAdvisor/issues/47"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Measure SSE latency added by Kong and the ALB against a direct stream and decide pass or the route-around ADR.

## Description
Overview 10 item 1, 4.3 and D16.16. Quote: 'Verify tokens stream without buffering through ALB, Kong (response_buffering: false, request_buffering: false, read_timeout 3,600,000 ms) and chat-api. Pass: SSE through Kong adds <= 50 ms p95 over a direct chat-api stream.' Use the E2-T8 ALB, E2-T5 Kong and the E2-T3 stub /sse. A spike route POST|GET /v1/chat with the SSE settings and a service read_timeout of 3,600,000 ms. A client job in the same region and VPC opens the same event stream (a) directly against the stub's internal URL with its own ID token and (b) through the ALB and Kong, interleaved. Per-event delay = client receive time minus the stub's emit timestamp (clock skew cancels in the difference). Run at least 2,000 events per path at 20 ms intervals. Also hold one stream for 10 minutes and note the ALB backend timeout and Cloud Run request timeout (set to 3,600 s on the stub) needed. Run a control with response_buffering: true. Question 5 asks whether the ALB hop counts toward the 50 ms.

## Acceptance criteria
- [ ] Given 2,000+ events per path, then p95(via ALB+Kong delay) - p95(direct delay) is recorded in the ADR and is <= 50 ms for a pass.
- [ ] Given the control with response_buffering: true, then events arrive in bursts (max inter-arrival gap or p95 delay at least 5x the unbuffered run), showing the test can fail.
- [ ] Given one stream held for 10 minutes through the ALB, then it ends only when the server closes it (0 premature disconnects), and the ALB backend timeout / Cloud Run timeout values required are written down.
- [ ] ADR exists with the numbers and verdict. The result is recorded as an ADR file in the repo (see question 1 for location and numbering) containing the measured values, the pass/fail verdict and the named fallback. Fail fallback per deep-dive/10-open-questions.md §10: ADR routing the SSE route around Kong (ALB URL map sends the chat routes straight to chat-api).
