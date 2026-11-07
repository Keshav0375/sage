---
key: "E8-T13"
title: "Add the as-of chip and the echoed parsed date"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T6", "E4-T18"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.10", "deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/04-2-source-lifecycle-and-cells.md#4.18", "decision-logs.md#adr-027"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The composer has an as-of date chip sent as `as_of`, and each answer shows the date the server actually applied.

## Description
Implements 06 6.10 and ADR-027: "`POST /v1/chat` accepts an optional `as_of` (ISO date) set by the UI chip. Resolution order (4.18): an explicit date or year found in the question by the deterministic parser; else the chip; else the Postgres `current_date` in UTC. The model never sets `as_of`." and "`meta` carries `as_of` and `as_of_source` (`chip`, `parsed`, `today`); the server emits a `notice {kind: "as_of"}` so the answer states the parsed date (not model text)."

Build:
- An as-of chip in the composer: empty means 'today' (no `as_of` sent); picking a date sends `as_of` as an ISO 8601 date `YYYY-MM-DD` in the `POST /v1/chat` body (the SPA never sends a locale-formatted date and never parses dates from the question text). A clear control removes the chip. The chip state is per conversation, in memory.
- An echo under each assistant message: 'Answered as of <as_of>' built from the `meta` event (`as_of`, `as_of_source`), with the source shown as 'from your question' (`parsed`), 'from the date chip' (`chip`) or 'today' (`today`). The server `notice {kind:"as_of"}` text is also shown (E8-T6). If the parsed date (from the question) differs from the chip, the echo shows the parsed date and a hint that the question's own date won; the SPA does not recompute it.
- Dates are displayed in an unambiguous form (for example 4 Mar 2024) so DD/MM versus MM/DD never has to be guessed by the reader (R4-D20 E11-Q2: the server echoes the parsed date).
Out of scope: the resolver and the date parsing rule (E4-T18, E11-T24).

## Acceptance criteria
- [ ] Given the chip set to 2024-03-04, when a question is sent, then the request body has `"as_of":"2024-03-04"`; with no chip the body has no `as_of` key (vitest, intercepted fetch).
- [ ] Given `meta {as_of:'2024-04-03', as_of_source:'parsed'}` while the chip shows 2024-03-04, when received, then the echo reads 'Answered as of 3 Apr 2024' with the 'from your question' text and the chip date is not shown as the applied date (test `asOf.test.tsx::echo_parsed_wins`).
- [ ] Given `as_of_source:'chip'` and `'today'`, when received, then the matching source text shows for each.
- [ ] Given the question text `03/04/2024` typed by the advisor, when sent, then the request body contains no `as_of` derived from it (the SPA does not parse question dates) (unit test).
- [ ] Given the clear control, when clicked, then the next request has no `as_of`.
