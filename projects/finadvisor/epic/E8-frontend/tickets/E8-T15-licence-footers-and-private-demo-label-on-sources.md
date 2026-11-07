---
key: "E8-T15"
title: "Render licence footers and label private_demo sources"
epic: "E8"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E8-T7", "E8-T8"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/08-security-and-privacy.md#8.8", "decision-logs.md#adr-036", "decision-logs.md#adr-026"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 196, "id": 6263580970, "url": "https://github.com/Keshav0375/FinAdvisor/issues/196"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Each answer shows the licence footer for every cited licence class, and every citation from a private demo document is labelled as such.

## Description
Implements the `footer` SSE event (06 6.2: `{licence_class, text}`, "licence footer from `document_versions.attribution_text` for each cited licence class; a missing footer blocks release") and 8.8 ("Licence footers are built from `document_versions.attribution_text` per cited `licence_class`"; `publisher`: "quote cap (default 40 words) plus attribution; `private_demo` documents are firm-tenant only", ADR-026, K-R4-3). R4-D20 (stage-4 answers Q2): the `citation` event carries a per-citation `source_class` (`public`, `firm` or `private_demo`) and `GET /v1/conversations/{id}` returns the stored footers.

- Store every `footer` event on the message (one per licence class, deduplicated on `licence_class`) and render the footer texts as plain text below the citations, one line per class, in event order. The text is server-owned and rendered as text, never HTML or markdown. The SPA does not create, edit or hide a footer.
- Private demo label: in the citation panel, each citation whose `source_class` is `private_demo` shows a visible 'Private demo document' label; `public` and `firm` citations show a neutral 'Public source' or 'Firm document' tag; an unknown value shows no label and no crash.
- History messages (E8-T8): messages loaded from `GET /v1/conversations/{id}` render their stored footers and the same per-citation labels as a live turn.
Out of scope: producing footers and `source_class` (E4), the quarantine view (E8-T17), the as-of chip (E8-T13).

## Acceptance criteria
- [ ] Given three `footer` events with classes `ogl`, `eu_consolidated_ccby`, `us_gov`, when rendered, then three footer lines show with their texts in event order; a duplicate `ogl` event shows once (vitest `footers.test.tsx::one_per_class`).
- [ ] Given a footer text `<img src=x onerror=1>`, when rendered, then no img element exists and the text appears literally.
- [ ] Given citations with `source_class` `public`, `firm` and `private_demo`, when the sources render, then only the third shows 'Private demo document' (test `footers.test.tsx::private_demo_label_per_citation`).
- [ ] Given a history response with stored footers and a `private_demo` citation, when the conversation loads, then the footers and the label render as in a live turn (test `footers.test.tsx::history_footers_and_labels`).
- [ ] grep test: no source file builds footer text from `licence_class` (the string table lives on the server).
