---
key: "E4-T32"
title: "llm_egress_ack enforcement on the LLM prompt path"
epic: "E4"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E4-T19", "E11-T14"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.7", "deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#adr-038", "decision-logs.md#adr-039"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 138, "id": 6263484957, "url": "https://github.com/Keshav0375/FinAdvisor/issues/138"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Refuse to send private chunk text to Anthropic for a tenant whose llm_egress_ack is false, with zero provider calls.

## Description
Enforce ADR-038 on the egress path E4 builds. Quote 8.7: 'Three egress paths for private text: the Anthropic prompt, Voyage embedding (ingest and query) and Voyage rerank. Each tenant has `llm_egress_ack` (default false); it must be true before private ingest ... The flag records the tenant's acceptance of these paths; it is not a residency or zero-retention claim. PUBLIC law is unaffected.' The column `tenants.llm_egress_ack` is added by E11-T14; this ticket reads it through the Principal or a tenant row read. Before the LLM call (E4-T19) and before the query-time embed and rerank calls, if the retrieval result or query involves any non-PUBLIC chunk and `llm_egress_ack` is false, the turn is refused with `error {FORBIDDEN}`-class code `LLM_EGRESS_NOT_ACKNOWLEDGED` (fixed message, defined in E4-T4's mapping; code name set in E4-T32 per orchestrator, R4-D20) and the Anthropic, Voyage embed and rerank clients record zero calls for that turn. PUBLIC-only questions are unaffected. The guard is defensive (private ingest is already refused by E11-T14) and is the runtime half of the L0 proof 'stub providers record that private text leaves only when the flag is true, on all three paths'. Out of scope: ingest refusal (E11-T14), wording of the documented promise (E12-T18).

## Acceptance criteria
- [ ] Given a tenant with llm_egress_ack=false and a retrieval result containing a non-PUBLIC chunk, when a turn runs, then it ends with LLM_EGRESS_NOT_ACKNOWLEDGED and the Anthropic, Voyage embed and Voyage rerank stubs record 0 calls (test_private_text_not_sent_without_ack).
- [ ] Given llm_egress_ack=true, when the same turn runs, then the stubs record that private text reached the Anthropic prompt (test_private_text_leaves_only_when_flag_true, path 1 of 3).
- [ ] Given a PUBLIC-only question and llm_egress_ack=false, when run, then the turn proceeds normally (test).
- [ ] Given the error mapping, when LLM_EGRESS_NOT_ACKNOWLEDGED is raised, then the body carries the fixed message and no tenant data.
