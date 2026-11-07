---
key: "E12-T18"
title: "Document the deletion promise wording"
epic: "E12"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E12-T16"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "decision-logs.md#adr-29", "decision-logs.md#adr-38", "deep-dive/09-observability.md#9.8"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 295, "id": 6263775696, "url": "https://github.com/Keshav0375/FinAdvisor/issues/295"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Publish the store-window table and the promise wording once, and make receipts and the API quote it from one source.

## Description
Create `docs/erasure-promise.md` containing the 4.19 table verbatim in meaning: live stores (Postgres, index, answer cache, GCS) within 24 h of the system running (the erasure job runs first at every demo start); BigQuery and Kafka within 14 d (48 h time travel + 7 d fail-safe; Kafka 7 d + `segment.ms`); backups within 7 d plus ledger replay on restore; Langfuse provider best effort stated as provider-bound (R4-D9); Anthropic and Voyage outside the promise; text already shown to an advisor is not recalled. Add `erasure_promise.py` exposing the same strings as constants, used by the receipt builder (`window` text) and the status API. Pass-through rule: no string 'instant' or 'erased everywhere' appears in docs or code outside tests. Do not state a number the arch does not carry.

## Acceptance criteria
- [ ] Given the repo, when a grep test searches `docs/` and `src/` for 'instant' and 'erased everywhere' (excluding test files and the phase-2 sentence), then it finds none.
- [ ] Given the receipt builder, then each step's `window` text equals the constant from `erasure_promise.py` (unit test per store).
- [ ] The doc lists the five rows (live, analytics and streams, backups, Langfuse, providers) with the exact windows above (doc-lint test compares to the constants).
