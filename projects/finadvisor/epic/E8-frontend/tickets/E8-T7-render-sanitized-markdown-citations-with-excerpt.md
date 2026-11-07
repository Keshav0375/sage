---
key: "E8-T7"
title: "Render sanitized markdown, citations with excerpts and stale badges"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T6"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.4", "deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/08-security-and-privacy.md#8.1"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Answers render as sanitized markdown with server-emitted citations, excerpts, jurisdiction chips and stale badges.

## Description
Implements deep-dive/04-components-and-responsibilities.md §4.4 'citations with excerpts, stale badges ... Renders sanitized markdown only' and the `citation` event `{index, chunk_id, source_title, regulatory_ref, jurisdiction, last_reviewed_at, stale, excerpt}` (06 6.2; `jurisdiction` is new in round 4). Markdown via react-markdown with no raw HTML (no rehype-raw), plus an explicit sanitiser (rehype-sanitize with a minimal allowlist; links limited to http/https/mailto and rel=noopener noreferrer; images not rendered). Inline `[n]` markers link to the citation with that index from `citation` events only; a marker with no matching event renders as plain text. The citation panel lists source_title, regulatory_ref, a jurisdiction chip (US, EU or UK, from `jurisdiction`; an unknown value renders the raw value as text), last_reviewed_at, excerpt (as text, never HTML) and a StaleBadge when stale=true. Reuse/adapt existing MarkdownContent, CitationPanel, StaleBadge, SourcesPanel. Also used for history messages (E8-T8). Out of scope: client-side citation verification, licence footers and the private_demo label (E8-T15), the as-of chip (E8-T13).

## Acceptance criteria
- [ ] Given answer text containing `<script>alert(1)</script>`, `<img src=x onerror=...>` and `[x](javascript:alert(1))`, when rendered, then the DOM has no script/img element, no onerror attribute and no javascript: href (vitest + testing-library).
- [ ] Given a `citation` event with stale=true, when rendered, then the stale badge shows; with stale=false it does not.
- [ ] Given citations with `jurisdiction` 'US', 'EU' and 'UK', when rendered, then each panel entry shows its own chip text; given `jurisdiction:'<b>X</b>'` it appears as literal text.
- [ ] Given a citation excerpt `<b>x</b>`, when rendered, then it appears as literal text with no <b> element.
- [ ] Given `[2]` in the text with no citation index 2, when rendered, then it is plain text, not a link.
- [ ] Given a citation with index 1, when `[1]` is clicked, then the panel entry for index 1 is highlighted.
