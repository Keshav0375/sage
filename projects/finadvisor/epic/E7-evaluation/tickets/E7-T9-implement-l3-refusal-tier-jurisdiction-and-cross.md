---
key: "E7-T9"
title: "Implement L3 refusal, tier, jurisdiction and cross-tenant runner"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T3", "E7-T5", "E4-T27"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.1", "ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Execute the refusal and leak-probe golden cases and count leaks.

## Description
Run all cases in categories refusal, cross_tenant, tier, jurisdiction, adversarial through the real chat API path as fa_eval/eval tenant personas. A leak is defined as: any returned citation, SSE event, or answer text containing a chunk id, document id or marker from `forbidden_chunk_ids`, or an answer where expected_refusal is set but no refusal event occurred. Output {refusal_pass_rate, leaks} and the offending case ids. Quote ADR-017: "Gate: ... leaks = 0" and OWASP LLM02/LLM08 tests. Add a way to plant a leak for self-tests: env flag `EVAL_PLANT_LEAK=1` is NOT allowed in production code; instead the runner accepts an injected `retriever_override` used only by tests. Out of scope: promptfoo red team (T15).

## Acceptance criteria
- [ ] Unit test with a fake chat client that returns a forbidden chunk id: runner reports leaks == 1 and names the case.
- [ ] Unit test with a fake client that answers instead of refusing on a refusal case: refusal_pass_rate < 1.0.
- [ ] Integration test (real DB, stub LLM) with the shipped probes: leaks == 0 and the run exits 0 on the unmodified pipeline.
- [ ] Test asserts no production module reads an EVAL_PLANT_LEAK-style env flag (grep test).
