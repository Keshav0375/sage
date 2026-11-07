---
key: "E2-T7"
title: "Spike: X-Serverless-Authorization passthrough"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T6", "E2-T1"]
arch_refs: ["deep-dive/10-open-questions.md#10", "deep-dive/08-security-and-privacy.md#8.2", "deep-dive/04-components-and-responsibilities.md#4.3", "decision-logs.md#adr-011"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 45, "id": 6155624474, "url": "https://github.com/Keshav0375/FinAdvisor/issues/45"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Prove Cloud Run IAM accepts the Kong-issued ID token while the user Authorization reaches the app byte-identical.

## Description
Overview 10 item 2, 8.2 step 6 and ADR-011. Quote: 'A Kong pre-function sets X-Serverless-Authorization (metadata-server ID token, audience = chat-api URL) and Cloud Run IAM accepts it while the user Authorization header reaches FastAPI unchanged (documented for IAM; "unchanged" is inferred).' Spike pre-function (spikes/e2/idtoken/, promoted in E2-T13): fetch an ID token from the metadata server identity endpoint (audience = chat-api URL from env), cache in a shared dict until near expiry (record the refresh margin chosen), set X-Serverless-Authorization: Bearer <token> and leave Authorization alone. Use the E2-T5 deployment and the E2-T3 stub with run.invoker only for the fa-gateway service account.

## Acceptance criteria
- [ ] Given a call to the stub's internal URL with only a user Authorization bearer, when made from an in-VPC job, then Cloud Run IAM answers 403; given the same call through Kong, then it returns 200.
- [ ] Given three Authorization values (short, with embedded spaces, 2 KB), when sent through Kong, then the stub's echoed sha256 of Authorization equals the sha256 computed by the client for all three (byte-identical).
- [ ] Given the stub echo of the decoded token, then aud equals the chat-api URL and email equals the fa-gateway service account; a client-sent X-Serverless-Authorization: garbage is replaced (stub sees the Google token's aud).
- [ ] Given 100 requests in a minute, then the metadata server is called at most once (counter logged by the spike) and, with the refresh margin set to 3590 s, the next request triggers exactly one new metadata call.
- [ ] ADR exists with verdict. The result is recorded as an ADR file in the repo (see question 1 for location and numbering) containing the measured values, the pass/fail verdict and the named fallback. Fallback: ingress internal only plus application JWT verification on that hop, recorded as an ADR.
