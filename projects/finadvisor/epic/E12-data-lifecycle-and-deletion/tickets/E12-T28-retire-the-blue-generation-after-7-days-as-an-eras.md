---
key: "E12-T28"
title: "Retire the blue generation after 7 days as an erasure-class operation"
epic: "E12"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E12-T27", "E12-T9"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.27", "decision-logs.md#adr-35", "decision-logs.md#adr-29", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.10"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 306, "id": 6263803248, "url": "https://github.com/Keshav0375/FinAdvisor/issues/306"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Keep blue for 7 days after a flip, then physically drop it with counts and VACUUM.

## Description
Command and scheduled check `embed-generation retire --model M` allowed only when `active_embed_model` of every tenant is not M and the flip is 7 d old (`EMBED_BLUE_KEEP_DAYS`, default 7: ask, 6.6 does not list it). It deletes the blue generation's chunk rows through the E12-T9 count-recording delete path (a `deletion_requests` row with scope `tenant`-level class `erasure`, counts in `erasure_steps`), drops its partial HNSW index, VACUUMs, and sets the generation `retired`. Rollback before day 7 is a flip back (E12-T27). Out of scope: Voyage-side retention.

## Acceptance criteria
- [ ] Given a flip 3 days ago, when retire runs, then it refuses with `BLUE_KEEP_WINDOW_OPEN` and rows remain.
- [ ] Given a flip 8 days ago and no tenant on blue, when retire runs, then blue rows are 0, the partial index is dropped, the generation is `retired` and `erasure_steps` hold the counts.
- [ ] Given one tenant still on blue, then retire refuses.
- [ ] Given a tombstoned document, then retire neither resurrects nor loses its tombstone (ledger unchanged).
