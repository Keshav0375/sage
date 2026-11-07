---
key: "E6-T11"
title: "Partition replay and ACL-change tests with zero embed calls"
epic: "E6"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E6-T10", "E5-T7", "E5-T9", "E5-T11"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.14", "decision-logs.md#adr-014"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Prove that replaying a partition and an ACL metadata change cost no embeddings.

## Description
Plan E6 done-when: 'Re-running the same partition re-embeds zero unchanged chunks (count asserted); an ACL change updates metadata with zero embed calls.' Arch (Flow 2 notes): 'A backfill or re-embed is a replay: Dagster re-publishes `docs.bronze.v1` for the partition (bronze is immutable), and unchanged chunk hashes cost nothing.' Write an end-to-end test (compose: Postgres, Redpanda or the E5 test broker, fake GCS, fake Voyage/Anthropic) that (1) materializes tenant x dt through all stages, (2) re-materializes the same partition and asserts embed calls == 0, chunk count and `corpus_version` unchanged, (3) creates an `acl_change_requests` row (`update_acl`, new tier) with its outbox event, lets the E5 acl-applier apply it, and asserts `chunks.tier_required`/`documents.tier_required` updated with 0 embed calls. If the applier does not update the denormalised chunk columns, fix it here only within the ETL stages; the applier itself is E5. Out of scope: building the applier.

## Acceptance criteria
- [ ] Replay test: second materialization of the same partition yields 0 Voyage embed calls (counter asserted == 0) and an unchanged `chunks` count
- [ ] ACL test: after the applier processes the change, every chunk of the document has the new `tier_required` and the Voyage counter delta == 0
- [ ] The tests run in CI as part of the integration suite and fail if the indexer is changed to embed unconditionally (mutation check documented)
