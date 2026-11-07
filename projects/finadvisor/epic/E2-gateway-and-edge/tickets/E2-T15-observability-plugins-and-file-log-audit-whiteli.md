---
key: "E2-T15"
title: "Observability plugins and file-log audit whitelist"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T13"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.3", "deep-dive/06-interfaces-and-contracts.md#6.5", "deep-dive/08-security-and-privacy.md#8.5", "decision-logs.md#adr-023"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 53, "id": 6155633807, "url": "https://github.com/Keshav0375/FinAdvisor/issues/53"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Emit traces, metrics and a whitelisted JSON audit line per request to stdout.

## Description
Sections 4.3, 6.5, 8.5 (D16.9, D16.10) and ADR-023. Quote 6.5: 'file-log writes to stdout with a field whitelist: timestamp, route, method, status, latency, request id, client IP hash; no Authorization, no bodies, no query strings.' Configure opentelemetry (OTLP endpoint from OTEL_EXPORTER_OTLP_ENDPOINT, W3C traceparent propagated to chat-api), prometheus (served on the status listener), and file-log to /dev/stdout implemented so only the whitelisted fields are emitted (remove the default request/response objects, headers, uri and querystring from the log entry). The client IP hash algorithm and salt are question 8 (until answered: sha256 with a salt from an environment variable, no default). Turn the nginx proxy access log off, since it carries the URI and query. Kong error-log lines on upstream failures can print the request line; the test below checks it and any leak is reported rather than hidden (question 13). Out of scope: the log sink (E2-T19).

## Acceptance criteria
- [ ] Given a request with Authorization: Bearer SENTINEL_TOKEN, query ?q=SENTINEL_QUERY and a JSON body containing SENTINEL_BODY, when the file-log line is captured, then it is valid JSON whose key set equals exactly {timestamp, route, method, status, latency, request_id, client_ip_hash} (set-equality assertion) and `grep -c SENTINEL` over all Kong stdout and stderr is 0.
- [ ] Given the same request with the upstream stopped (502/504 path), then `grep -c SENTINEL` over Kong stderr is 0; if the nginx error log leaks the query this test fails and the ticket records question 13 instead of weakening the test.
- [ ] Given a request carrying traceparent 00-<trace>-<span>-01, then the stub receives a traceparent with the same trace id.
- [ ] Given traffic, then GET /metrics on the status listener contains kong_http_requests_total with the route label and is not reachable on the proxy port.
