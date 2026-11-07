---
key: "E4-T22"
title: "Per-tenant token budget and concurrency limits"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T19"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/06-interfaces-and-contracts.md#6.6", "deep-dive/08-security-and-privacy.md#8.1"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Enforce TENANT_TOKEN_BUDGET and TENANT_MAX_CONCURRENCY before generation.

## Description
Before the LLM call, check the tenant's token usage against TENANT_TOKEN_BUDGET (window defined in questions; source: usage rows already written, no new infra unless arch lists one) and in-flight turns against TENANT_MAX_CONCURRENCY. Exceeded budget -> TENANT_BUDGET_EXCEEDED; concurrency -> RATE_LIMITED 429 with Retry-After. Concurrency slot released in finally. Both limits are per tenant, not per instance (state in Postgres or Valkey per questions).

## Acceptance criteria
- [ ] Given budget exhausted, when a turn starts, then error TENANT_BUDGET_EXCEEDED is returned and the LLM stub is called 0 times.
- [ ] Given TENANT_MAX_CONCURRENCY=2 and 3 simultaneous turns, then the third gets 429 RATE_LIMITED with Retry-After; after one finishes a new turn is accepted.
- [ ] Given a turn that raises, the concurrency slot is released (test).
