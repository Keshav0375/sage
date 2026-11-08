---
key: "E7-T12"
title: "Prove the gate with four deliberate-regression test PRs"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T11"]
arch_refs: ["ADR-017"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 167, "id": 6263531794, "url": "https://github.com/Keshav0375/FinAdvisor/issues/167"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Show that the PR gate fails for each of four seeded regressions.

## Description
Create four regression patches kept as reviewed fixtures under tests/eval_gate/regressions/: (1) break the citation verifier call so citation < 0.95; (2) change the system prompt to encourage unsupported claims so faithfulness < 0.90; (3) plant a cross-tenant leak by dropping the tenant predicate in a retriever double used by the eval run (via the retriever_override from E7-T9, not by editing production RLS); (4) lower RERANK_CANDIDATES / disable the FTS leg so recall@10 drops by more than 2 points. Add a workflow `eval-gate-selftest.yml` (manual dispatch) that applies each patch to a throwaway branch, runs the PR eval job, and asserts the gate fails with the expected rule. Open four draft PRs and record their links and the failing rule in docs/eval/gate-proof.md. Quote the epic done-when: "The PR gate fails a deliberate regression in each of: citation < 0.95, faithfulness < 0.90, a planted cross-tenant leak, recall drop > 2 points (four test PRs)."

## Acceptance criteria
- [ ] For each of the four patches, the selftest workflow reports the eval job failed with the rule name citation, faithfulness, leaks or recall respectively (four recorded run URLs in docs/eval/gate-proof.md).
- [ ] A fifth control run with no patch passes the gate.
- [ ] A test fails if docs/eval/gate-proof.md lists fewer than four PR links or any entry lacks the measured value.
