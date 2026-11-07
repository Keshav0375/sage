---
key: "E4-T3"
title: "Spike: Sonnet 5.5 prompt-cache hit behaviour with versioned tools"
epic: "E4"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T21"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#ADR-006"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 95, "id": 6155681434, "url": "https://github.com/Keshav0375/FinAdvisor/issues/95"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Measure prompt-cache hits for system prompt plus tools on claude-sonnet-5-5.

## Description
Spike. Using the Anthropic SDK against claude-sonnet-5-5 (cache minimum 512 tokens per ADR-006), put cache_control on the end of tools+system and send 20 sequential and 20 concurrent requests with varying tenant/user/date text after the breakpoint. Record cache_read_input_tokens vs cache_creation_input_tokens, hit rate, TTFT with and without hit, and show that changing one tool definition invalidates the cache. Repeat once for claude-sonnet-4-6 (1,024-token minimum) to feed the fallback. Record as an ADR-006 addendum. Out of scope: the production LLMClient.

## Acceptance criteria
- [ ] Given 20 sequential requests with a stable prefix, when run, then the hit rate and cache_read tokens are recorded and the ADR states whether the prefix reaches the 512-token minimum.
- [ ] Given one tool definition is edited, when the next request is sent, then cache_read_input_tokens is 0 and cache_creation is >0; the result is recorded.
- [ ] TTFT p50 with hit and without hit are both recorded.
