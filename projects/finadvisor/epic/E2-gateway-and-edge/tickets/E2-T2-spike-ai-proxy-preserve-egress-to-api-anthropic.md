---
key: "E2-T2"
title: "Spike: ai-proxy preserve egress to api.anthropic.com"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/10-open-questions.md#10", "deep-dive/06-interfaces-and-contracts.md#6.5", "deep-dive/08-security-and-privacy.md#8.3", "decision-logs.md#adr-011"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 40, "id": 6155618507, "url": "https://github.com/Keshav0375/FinAdvisor/issues/40"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Decide by measurement whether LLMClient can use an internal Kong egress route in the native Messages format with streaming and tool use.

## Description
Overview section 10 item 4, ADR-011 (LLM egress), 6.5 llm-egress row, 8.3 'Kong egress route: key-auth (consumer chat-api) + ip-restriction to the VPC range'. Scratch harness under spikes/e2/egress/ (kong:3.9.4 local). Build route prefix /egress/anthropic to https://api.anthropic.com with ai-proxy route_type: preserve (or, if that is not usable on OSS 3.9.4 without Anthropic llm_format, a plain proxy service), key-auth with consumer chat-api, ip-restriction, request-transformer that adds x-api-key from an environment variable (the client sends no Anthropic key), a global rate-limiting for LLM calls, and log_statistics. Native Messages format only; no OpenAI-format translation. The Anthropic key comes from the developer's environment and is never committed. Compare time to first byte and total time against a direct call. Out of scope: changing LLMClient (E4), the production route (E2-T20).

## Acceptance criteria
- [ ] Given stream: true on POST /egress/anthropic/v1/messages through Kong, when the call completes, then the client receives the native event sequence message_start ... content_block_delta ... message_stop and the first event arrives; time to first byte via Kong minus direct (median of 20 runs) is recorded in the ADR.
- [ ] Given a request with a tools array, when the model returns a tool_use block, then a follow-up request carrying the matching tool_result is accepted through the same route (HTTP 200).
- [ ] Given no apikey header, then the route returns 401; given a source address outside the ip-restriction allow list, then it returns 403 (two named tests in spikes/e2/egress/).
- [ ] Given a completed call, then Kong's log output contains the log_statistics token counts and contains neither the Anthropic key, the egress key nor the prompt text (grep -c over captured logs = 0).
- [ ] ADR exists with verdict. The result is recorded as an ADR file in the repo (see question 1 for location and numbering) containing the measured values, the pass/fail verdict and the named fallback. Fail fallback per deep-dive/10-open-questions.md §10: LLMClient calls Anthropic directly and the egress route is dropped (E2-T20 closes as not applicable).
