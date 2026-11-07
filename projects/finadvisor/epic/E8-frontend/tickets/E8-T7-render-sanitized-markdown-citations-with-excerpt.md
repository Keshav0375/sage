---
key: "E8-T7"
title: "Render sanitized markdown, citations with excerpts and stale badges"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T6"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.4", "deep-dive/06-interfaces-and-contracts.md#6.2"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Answers render as sanitized markdown with server-emitted citations, excerpts and stale badges.

## Description
Implements deep-dive/04-components-and-responsibilities.md §4.4 'citations with excerpts, stale badges ... Renders sanitized markdown only' and the `citation` event `{index, chunk_id, source_title, regulatory_ref, last_reviewed_at, stale, excerpt}`. Markdown via react-markdown with no raw HTML (no rehype-raw), plus an explicit sanitiser (rehype-sanitize with a minimal allowlist; links limited to http/https/mailto and rel=noopener noreferrer; images not rendered). Inline `[n]` markers link to the citation with that index from `citation` events only; a marker with no matching event renders as plain text. Citation panel lists source_title, regulatory_ref, last_reviewed_at, excerpt (as text, never HTML) and a StaleBadge when stale=true. Reuse/adapt existing MarkdownContent, CitationPanel, StaleBadge, SourcesPanel. Also used for history messages (E8-T8). Out of scope: client-side citation verification.

## Acceptance criteria
- [ ] Given answer text containing `<script>alert(1)</script>`, `<img src=x onerror=...>` and `[x](javascript:alert(1))`, when rendered, then the DOM has no script/img element, no onerror attribute and no javascript: href (vitest + testing-library).
- [ ] Given a `citation` event with stale=true, when rendered, then the stale badge shows; with stale=false it does not.
- [ ] Given a citation excerpt `<b>x</b>`, when rendered, then it appears as literal text with no <b> element.
- [ ] Given `[2]` in the text with no citation index 2, when rendered, then it is plain text, not a link.
- [ ] Given a citation with index 1, when `[1]` is clicked, then the panel entry for index 1 is highlighted.
