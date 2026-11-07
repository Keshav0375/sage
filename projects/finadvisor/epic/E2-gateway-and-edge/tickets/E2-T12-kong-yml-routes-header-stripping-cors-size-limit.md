---
key: "E2-T12"
title: "kong.yml routes, header stripping, CORS, size limit, correlation-id"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T11"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.5", "deep-dive/04-components-and-responsibilities.md#4.3", "decision-logs.md#adr-011"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 50, "id": 6155630387, "url": "https://github.com/Keshav0375/FinAdvisor/issues/50"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Define the four routes and the non-limiting plugins with the exact path rules of the arch.

## Description
Section 6.5 route table. Routes: chat POST ~/v1/chat$; chat-resume GET ~/v1/chat/[^/]+/events$; api prefix /v1/ (lower priority); tenant-discovery GET ~/v1/tenants/[^/]+$. Paths are prefixes or ~ regexes, never globs; anything unlisted gets Kong's 404; no /internal route. Upstream is the chat-api URL from the environment. chat and chat-resume: request_buffering false, response_buffering false, upstream service read_timeout 3,600,000 ms (a separate Kong service entry with the same URL carries the long timeout; question 14). Plugins per route as in the table: request-transformer removing client X-User-Id, X-Tenant-Id, X-Serverless-Authorization, X-RL-Key; cors with the SPA origin from CORS_ALLOWED_ORIGINS; correlation-id on X-Request-Id; request-size-limiting; bot-detection. tenant-discovery: cors, correlation-id, request-size-limiting (rate limit and file-log come in E2-T14/T15). Strip the identity headers on tenant-discovery too so the done-when holds (question 10). The size value is provisional (question 7). Not used: jwt, http-log, openid-connect, Enterprise plugins. Rate limits, pre-function, observability are separate tickets.

## Acceptance criteria
- [ ] Given the Kong container with this kong.yml, when `POST /v1/chat`, `GET /v1/chat/abc/events`, `GET /v1/anything` and `GET /v1/tenants/acme` are sent, then each returns the stub's 200; `GET /v1/tenants/a/b` is served by the api route (stub 200) (pytest tests/gateway/test_routes.py).
- [ ] Given `GET /internal/audit/gateway` and `GET /egress/anthropic/v1/messages`, then both return 404 from Kong.
- [ ] Given a request carrying X-User-Id, X-Tenant-Id, X-Serverless-Authorization and X-RL-Key with value 'evil' on each of the four routes, then the stub's /echo shows no X-User-Id and no X-Tenant-Id, and no header with the value 'evil'.
- [ ] Given a body larger than the size limit on POST /v1/chat, then Kong returns 413; given an Origin not in CORS_ALLOWED_ORIGINS, then no Access-Control-Allow-Origin is returned; given any request, then X-Request-Id is present on the upstream request and the response.
- [ ] Given `kong config parse kong/kong.yml`, then it exits 0, and the chat route in the parsed output has request_buffering false, response_buffering false and its service read_timeout 3600000.
