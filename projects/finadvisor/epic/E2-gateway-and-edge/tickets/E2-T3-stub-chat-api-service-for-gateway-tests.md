---
key: "E2-T3"
title: "Stub chat-api service for gateway tests"
epic: "E2"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.3", "deep-dive/06-interfaces-and-contracts.md#6.5"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 41, "id": 6155619697, "url": "https://github.com/Keshav0375/FinAdvisor/issues/41"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
A minimal FastAPI stub that echoes received headers (never raw Authorization) and emits timestamped SSE, used by spikes and smoke tests.

## Description
Test tooling for E2 only, under tools/stub-chat-api/. Python 3.12 FastAPI app, image referenced by digest. Endpoints: GET/POST /echo returns JSON of received headers with Authorization replaced by {sha256, length}; GET /sse?events=N&interval_ms=M streams N SSE events whose data holds a server-side monotonic sequence number and a wall-clock emit timestamp in ns; GET /metadata-mock/computeMetadata/v1/instance/service-accounts/default/identity returns a fake unsigned JWT for local compose (aud taken from the audience query parameter) so the pre-function can run without GCE; /echo also decodes (without verifying) the payload of X-Serverless-Authorization and returns aud, email, exp. Never deployed outside spike and test environments. Not a substitute for chat-api (E4).

## Acceptance criteria
- [ ] Given a request with Authorization: Bearer SENTINEL_AAA, when /echo is called, then the response body contains the sha256 of that header value and does not contain SENTINEL_AAA (pytest test_echo_never_returns_raw_authorization).
- [ ] Given GET /sse?events=50&interval_ms=20, then exactly 50 events arrive with strictly increasing sequence numbers and emit timestamps (pytest test_sse_sequence).
- [ ] Given the metadata mock endpoint with audience=https://x, then /echo decoding of a header built from it returns aud == https://x (pytest).
- [ ] docker build of the image succeeds and `docker run` serves /echo with HTTP 200 (CI step or make target named in the PR).
