---
key: "E2-T20"
title: "llm-egress route (conditional on the egress spike)"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T2", "E2-T12", "E2-T16"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.5", "deep-dive/08-security-and-privacy.md#8.3", "deep-dive/08-security-and-privacy.md#8.4", "decision-logs.md#adr-011"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 58, "id": 6155639775, "url": "https://github.com/Keshav0375/FinAdvisor/issues/58"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
If E2-T2 passed, add the internal Kong route that holds the Anthropic key and protects it with key-auth and ip-restriction.

## Description
6.5 llm-egress row, 8.3, 8.4, ADR-011, using the E2-T2 result. If the E2-T2 ADR failed, set this ticket to done with a note 'not applicable, see ADR' and make no changes (LLMClient calls Anthropic directly). If it passed: route prefix /egress/anthropic to https://api.anthropic.com with the working configuration from the spike (ai-proxy route_type: preserve or plain proxy), key-auth with consumer chat-api (key from Secret Manager, KONG_EGRESS_KEY), ip-restriction to the VPC range (variable), request-transformer adding the Anthropic key from env, global LLM rate-limiting, log_statistics, native Messages format only. Secrets are injected from Secret Manager into the fa-gateway service by Terraform (no values in state). LLMClient wiring via ANTHROPIC_BASE_URL is E4.

## Acceptance criteria
- [ ] Given the E2-T2 verdict is fail, then the ticket closes with no kong.yml change and a test asserts `grep -c egress kong/kong.yml` is 0.
- [ ] Given a pass, when POST /egress/anthropic/v1/messages is sent without apikey, then 401; from an address outside the VPC range, then 403 (tests in tests/gateway/test_egress.py against a mock Anthropic upstream).
- [ ] Given a valid key and stream: true against the mock upstream, then the native event sequence is relayed unchanged and Kong logs the log_statistics fields with no key or prompt text (grep -c = 0).
- [ ] Given `kong config parse` and the E2-T16 guard, then both exit 0 with the route present.
