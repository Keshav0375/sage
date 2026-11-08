---
key: "E20-T4"
title: "React SPA in dashboard-web/"
epic: "E20"
repo: "Sentinel"
size: "M"
status: "done"
depends_on: ["E20-T3"]
arch_refs: ["deep-dive/11-observability-and-ops-dashboard.md#11.3"]
issue: null
branch: "dev/backend-phase-10-ops-dashboard"
pr: "https://github.com/Keshav0375/Sentinel/pull/33"
updated: "2026-11-08"
---

## Summary
React 18 + TypeScript + Vite SPA: light/dark/system theme, KPI cards, needs-action lane, chain timeline, chain drawer with trace waterfall, detail toggles persisted in the URL, WCAG 2.1 AA.

## Description
Source: backend task 10.4 (built in https://github.com/Keshav0375/Sentinel/pull/33).

React 18 + TypeScript + Vite SPA: light/dark/system theme, KPI cards, needs-action lane, chain timeline, chain drawer with trace waterfall, detail toggles persisted in the URL, WCAG 2.1 AA.

## Acceptance criteria
- [x] Keyboard navigable and responsive to 360 px
- [x] Staleness banner when the snapshot is over 1 h old
- [x] Status never conveyed by colour alone

## Outcome
Merged in https://github.com/Keshav0375/Sentinel/pull/33 on 2026-10-28.
