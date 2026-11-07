---
key: "E3-T7"
title: "CRAG-style confidence gate"
epic: "E3"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E3-T6"]
arch_refs: ["decision-logs.md#adr-008", "deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.6"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 67, "id": 6155649832, "url": "https://github.com/Keshav0375/FinAdvisor/issues/67"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Add RetrievalService.gate that decides from rerank scores whether firm documentation is firm enough to answer, with no LLM call.

## Description
Add `RetrievalService.gate(rerank_result) -> GateResult(passed: bool, top_score: float | None, reason: str)` in `backend/src/retrieval/gate.py`.

Arch (ADR-008): "CRAG-style gate yields 'no firm documentation' + escalate offer without an LLM call" (CRAG, arXiv 2401.15884; "no web fallback"). SSE §6.2: `refusal {code: "NO_FIRM_DOCUMENTATION", escalate_offer: bool}` when "confidence gate failed; no LLM call was made"; `done.finish_reason` includes `gate`. Config §6.6: `GATE_MIN_SCORE` "required; set in E3 by eval". Observability: `gate_refusals_total` counter and span `retrieval.gate`.

Behaviour: the gate passes when the best rerank score >= `GATE_MIN_SCORE`; it fails when there are no candidates or the best score is below the threshold. `GATE_MIN_SCORE` has no code default (missing key fails boot, like every required key). The value used in the repo's `.env.example` / test config comes from the E3-T16 benchmark and is re-tuned by the E7 eval; record the chosen value and the score distribution on answerable vs unanswerable queries from the synthetic set in the E3-T16 ADR. When the rerank result is `degraded` (RRF order, no rerank scores) the behaviour is not defined by the arch (see questions): implement it as a single explicit function `gate_degraded_policy` selected by a constant, defaulting to pass-through only when candidates exist, and flag in the PR description.

Output is data for the orchestrator (E4 emits the SSE `refusal` and skips the LLM call); this ticket does not emit SSE. Out of scope: threshold tuning against the full eval set (E7), web fallback (rejected).

## Acceptance criteria
- [ ] Given `GATE_MIN_SCORE=0.5` and a rerank result whose best score is 0.49 when `gate` runs then `passed=False` and `gate_refusals_total` increased by 1; with best score 0.5 then `passed=True` (test `backend/tests/test_gate.py::test_threshold_boundary`).
- [ ] Given an empty candidate list when `gate` runs then `passed=False` and no exception (test `test_empty_candidates_fail`).
- [ ] Given `GATE_MIN_SCORE` is unset when Settings loads then the app exits non-zero (test `test_gate_threshold_required`).
- [ ] Given a degraded rerank result (RRF order, no scores) with candidates present when `gate` runs then the outcome equals `gate_degraded_policy` and the result carries `reason='degraded_no_scores'` (test `test_degraded_policy_explicit`).
