---
key: "E20-T5"
title: "Pages deploy, web CI and pre-publish guard"
epic: "E20"
repo: "Sentinel"
size: "M"
status: "done"
depends_on: ["E20-T4"]
arch_refs: ["deep-dive/11-observability-and-ops-dashboard.md#11.3"]
issue: null
branch: "dev/backend-phase-10-ops-dashboard"
pr: "https://github.com/Keshav0375/Sentinel/pull/33"
updated: "2026-11-08"
---

## Summary
`ops_pages.yml` deploys only from `main` (never PRs or forks).

## Description
Source: backend task 10.5 (built in https://github.com/Keshav0375/Sentinel/pull/33).

`ops_pages.yml` deploys only from `main` (never PRs or forks); `ci_web.yml` runs e2e and Lighthouse; `check_site.py` guards the built site before publish.

## Acceptance criteria
- [x] e2e green on the built site in both themes
- [x] Lighthouse perf and a11y at least 0.90
- [x] Pages deploy refuses non-main refs

## Outcome
Merged in https://github.com/Keshav0375/Sentinel/pull/33 on 2026-10-28.
