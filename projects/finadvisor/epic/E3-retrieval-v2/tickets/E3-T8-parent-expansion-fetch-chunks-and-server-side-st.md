---
key: "E3-T8"
title: "Parent expansion, fetch_chunks and server-side staleness"
epic: "E3"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E3-T5"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.3", "decision-logs.md#adr-008", "decision-logs.md#adr-004"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 68, "id": 6155651010, "url": "https://github.com/Keshav0375/FinAdvisor/issues/68"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Add parent-chunk expansion, fetch_chunks(ids) for the citation verifier, and staleness computed from today's date.

## Description
Add to `RetrievalService`: `expand_parents(ranked_chunks) -> list[ExpandedChunk]` and `fetch_chunks(ids) -> list[Chunk]`, plus a pure function `is_stale(last_reviewed_at, today) -> bool` in `backend/src/retrieval/staleness.py`.

Arch: §4.5 `retrieval`: "Methods: ... `expand_parents`, ... `fetch_chunks(ids)` (used by the citation verifier and the cache-hit path)". ADR-008: "parent expansion; staleness computed server-side from today's date. Chunking: structure-aware 256-512-token children, ~1k-token parents". §6.3 `search_firm_kb` output: `{results:[{n, chunk_id, source_title, regulatory_ref, last_reviewed_at, stale, text}], total_found, today}`: "`stale` computed server-side from today's date; `today` placed after the cache breakpoint". G-52: the MVP only had a prompt instruction for staleness.

Behaviour: `expand_parents` replaces each child hit with its parent chunk text (via `(tenant_id, parent_id)` under RLS), de-duplicates parents that several children share (keep the best-ranked child's `n` and chunk id for citation), and keeps the child `chunk_id` as the citation id while returning the parent `text` (content is the redacted stored text; never `raw_content`). `fetch_chunks(ids)` returns the chunks by id under the caller's RLS; ids the caller cannot see are silently absent (the caller treats absence as verification failure). `today` is `date.today()` in UTC taken from an injectable clock. The stale threshold is a named constant (12 months, from G-52's "over 12 months old"; confirm in questions), not a literal in call sites.

Out of scope: building the full `search_firm_kb` payload (E3-T9), the citation verifier itself (E4).

## Acceptance criteria
- [ ] Given two child hits that share one parent when `expand_parents` runs then one expanded item is returned with the parent's text and the better-ranked child's chunk id (test `backend/tests/test_expand_parents.py::test_dedup_shared_parent`).
- [ ] Given a parent in another tenant that the caller cannot see when `expand_parents` runs then it is absent and no error text mentions the other tenant (test `test_parent_rls`).
- [ ] Given `last_reviewed_at` = today minus 366 days and a fixed clock when `is_stale` runs then True; today minus 365 days then False; None then True-or-False exactly as the constant's documented rule (test `backend/tests/test_staleness.py::test_threshold_boundary`).
- [ ] Given ids [visible, other-tenant, nonexistent] when `fetch_chunks` runs under RLS then exactly one chunk is returned (test `test_fetch_chunks_only_visible`).
