---
name: scan
description: Phase 1 only — scan job sources (145 scanners by wave, Composio job APIs, Gmail alerts, Reddit/HN signals), de-dupe, filter by knobs, check liveness, then show the Tools and Jobs cards.
argument-hint: "[preset] [--company NAME | --url URL | --provider NAME]"
---

# /gimme-job:scan
Spawn `gimme-job:scout-lead` with the preset and any target flag. For a single target, skip the lead and use
`gimme-job:script-worker` with `scan.py --company NAME` / `--url URL` / `--provider NAME`, then `dedupe.py`.
Show Card 1 (tools) and Card 2 (jobs) from `cards.py`. Mention the run id.
Other modes: `scan.py --full-ats` (every tracked company), `scan.py --list` (scanners by wave), `discover.py ats <url>`.
