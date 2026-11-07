---
key: "E2-T14"
title: "Rate limits per IP and per session on Valkey"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T13"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.5", "deep-dive/06-interfaces-and-contracts.md#6.6", "deep-dive/06-interfaces-and-contracts.md#6.11", "deep-dive/04-components-and-responsibilities.md#4.6", "deep-dive/04-components-and-responsibilities.md#4.3", "decision-logs.md#adr-011", "decision-logs.md#adr-031"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 52, "id": 6155632654, "url": "https://github.com/Keshav0375/FinAdvisor/issues/52"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add the rate-limiting plugins with numeric limits, Retry-After and Valkey-backed counters.

## Description
Sections 4.3, 4.6, 6.5, 6.6 and ADR-011. Quote 6.5: rate-limiting 'limit_by: ip, and limit_by: header with header_name: X-RL-Key, policy: redis against Valkey, sync_rate: 0 on the chat route, 429 with Retry-After'. Plugins: per-IP on every route (tenant-discovery has only this one, no bearer), per-session on X-RL-Key for chat, chat-resume and api, stricter on POST /v1/chat. Values come from RATE_LIMIT_IP_PER_MIN, RATE_LIMIT_TOKEN_PER_MIN, RATE_LIMIT_CHAT_PER_MIN, which this ticket sets (section 6.6 'set in E2'); choose small demo values, document them next to the keys, and flag them for confirmation (question 6). Valkey host/port from environment. Counters live only in Valkey; no other use of Valkey. The behaviour if Valkey is down (fault_tolerant) is question 6; set it explicitly rather than rely on the default and record the choice. Use the missing-header behaviour found in E2-T1.

Round 4 (ADR-031, deep-dive/06 section 6.11): `GET /resolve` (E2-T12) is public and "rate limited by IP": give it the same per-IP plugin and `RATE_LIMIT_IP_PER_MIN` as tenant-discovery, and no per-session limit (it carries no bearer).

## Acceptance criteria
- [ ] Given RATE_LIMIT_IP_PER_MIN=N on tenant-discovery, when N+1 requests arrive from one IP within a minute, then the (N+1)th returns 429 with a Retry-After header (test_ip_limit).
- [ ] Given RATE_LIMIT_CHAT_PER_MIN=M and one bearer token, when M+1 POST /v1/chat requests are sent while the IP limit is not reached, then the (M+1)th returns 429 with Retry-After and a request with another token returns 200 (test_session_limit).
- [ ] Given traffic from the two tests, when Valkey is scanned, then no key or value contains a raw bearer sentinel and keys contain the 64-hex hash (test_no_raw_token_in_valkey).
- [ ] Given Valkey stopped, then requests behave as the documented fault_tolerant choice (test_valkey_down asserts the chosen status).
- [ ] Given `kong config parse`, then it exits 0 and policy is redis with sync_rate 0 on the chat route.
- [ ] Given RATE_LIMIT_IP_PER_MIN=N on `GET /resolve?slug=acme`, when N+1 requests arrive from one IP within a minute, then the (N+1)th returns 429 with a Retry-After header (`test_resolve_ip_limit`).
