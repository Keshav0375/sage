---
key: "E4-T29"
title: "Compliance checks: licence footer, jurisdiction label, staleness"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T11", "E4-T19"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.8", "deep-dive/08-security-and-privacy.md#8.6", "deep-dive/06-interfaces-and-contracts.md#6.2", "decision-logs.md#adr-036", "decision-logs.md#adr-026"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 135, "id": 6263477517, "url": "https://github.com/Keshav0375/FinAdvisor/issues/135"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Emit licence footers per cited licence class, jurisdiction labels and warnings, and block release when a required footer is missing.

## Description
Implement deterministic compliance checks as `ReleaseCheck`s and server events (ADR-036 decision 5; 8.8; 6.2 events `footer` and `notice`). (1) Licence footer: for every distinct `licence_class` among the cited chunks, build `footer {licence_class, text}` from `document_versions.attribution_text` (the text is data from the 8.8 table; this ticket does not hard-code legal wording); if the required text for a cited class is empty, the answer is withheld with `ANSWER_WITHHELD` reason `footer_missing`. (2) Jurisdiction label per citation (the `citation` event already carries `jurisdiction`); when the cited chunks span more than one of US, EU, UK, emit `notice {kind:"mixed_jurisdiction", text}`. (3) Staleness: `stale` per citation from today's date; for law texts a `notice {kind:"state"}` when the cited version state is `superseded` or `revoked`, and `notice {kind:"known_pending"}` when a known pending amendment is recorded. All notices are server text, never model text. Chunk and version fields come from `retrieval.fetch_chunks` (E3-T8). Out of scope: the footer wording table content (E11 connectors set `attribution_text`), the as-of check (E4-T11).

## Acceptance criteria
- [ ] Given cited chunks of licence classes A and B, when the answer is released, then exactly two `footer` events are emitted with the attribution_text of each class (#22 matrix test over every licence class in the fixture).
- [ ] Given a cited class whose attribution_text is empty, when released, then the turn ends with refusal ANSWER_WITHHELD reason footer_missing and no delta after the check (removing a footer blocks release; test_missing_footer_blocks_release).
- [ ] Given citations from US and UK sources, when released, then one `notice` of kind mixed_jurisdiction is emitted; given only EU sources, none.
- [ ] Given a cited law version in state `superseded`, then a `notice` of kind state is emitted and `citation.stale` is true; none for an `in_force` version.
