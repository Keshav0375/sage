---
key: "E6-T11"
title: "Replay, parser-bump and ACL-change tests with zero embed calls"
epic: "E6"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E6-T10", "E6-T21", "E5-T7", "E5-T9", "E5-T11"]
arch_refs: ["deep-dive/04-1-key-flows.md#4.14", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.10", "decision-logs.md#adr-014", "decision-logs.md#adr-027", "decision-logs.md#adr-022"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Prove that replaying a partition, a parser bump with unchanged text and a polled ACL change cost no embeddings.

## Description
Plan E6 round 4: replay after a parser bump re-parses, and unchanged chunk hashes extend `valid_to` with no embed call; an ACL change updates metadata with zero embed calls. Write an end-to-end test (compose: Postgres, the E5 test broker, fake GCS, fake Voyage/Anthropic) that (1) materializes tenant x dt through all stages, (2) re-materializes the same partition: embed calls == 0, chunk count and `corpus_version` unchanged (the second publish extends nothing and bumps nothing when nothing changed), (3) bumps `parser_version`, replays: the document is re-parsed (silver version prefix rewritten), new rows carry the new parser_version, embed calls == 0 because hashes are unchanged, and the replaced parse swaps atomically (no moment with zero chunks visible: sampled by a concurrent reader), (4) inserts an `acl_change_requests` row (`update_acl`, new tier) and lets the E5-T11 applier POLL it with Kafka stopped, then asserts `chunks.tier_required` and `documents.tier_required` updated with 0 embed calls. If the applier does not update the denormalised chunk columns, fix it here only within the ETL stages; the applier is E5. Out of scope: building the applier; the twice-after-bump zero-resurrection test is E12-T24.

## Acceptance criteria
- [ ] Replay test: the second materialization of the same partition yields 0 Voyage embed calls, an unchanged `chunks` count and unchanged `corpus_version`.
- [ ] Parser-bump test: after bumping `parser_version` and replaying, rows exist for the new parser_version, Voyage embed calls == 0, and a concurrent reader polling every 50 ms never sees zero chunks for the document during the swap (test_parser_bump_atomic_swap).
- [ ] ACL test: with Kafka stopped, after the applier polls the request every chunk of the document has the new `tier_required` and the Voyage counter delta == 0.
- [ ] The tests run in CI in the integration suite and fail if the indexer is changed to embed unconditionally (mutation check documented).
