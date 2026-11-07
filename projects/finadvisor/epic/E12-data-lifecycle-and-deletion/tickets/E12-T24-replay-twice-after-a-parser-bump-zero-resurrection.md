---
key: "E12-T24"
title: "Replay twice after a parser bump: zero resurrection"
epic: "E12"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E12-T8", "E12-T22", "E6-T11"]
arch_refs: ["deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#8", "decision-logs.md#adr-34", "decision-logs.md#adr-28", "decision-logs.md#adr-35"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Test that two replays after a parser bump give the single-run hash and never resurrect an erased document.

## Description
Add a PR-tier test (no new production code beyond fixes it exposes): load the fixture corpus, erase one document (tombstone), bump `parser_version`, replay the corpus twice through the real indexer, then compute the end-state hash over chunks. Compare with a single replay of the same corpus; assert zero duplicates, zero rows for the tombstoned document, and that no chunk of the old parse is retrievable by `as_of` today. Run `reconcile` at the end and expect no findings (re-baseline).

## Acceptance criteria
- [ ] Given the fixture corpus replayed twice after a parser bump, then the end-state hash equals the hash from a single replay (#8).
- [ ] Given a tombstoned document in the replayed corpus, then it has zero chunks after both replays (zero resurrection).
- [ ] Given the replay, then no chunk row with the old `parser_version` is returned by a retrieval query at today's date.
- [ ] Given the end state, then `reconcile` returns zero findings.
