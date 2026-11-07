---
key: "E11-T3"
title: "Spike: eCFR terms page and API limits"
epic: "E11"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/11-tech-stack.md#source-connectors-r4", "deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "decision-logs.md#adr-26"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 279, "id": 6263727793, "url": "https://github.com/Keshav0375/FinAdvisor/issues/279"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Confirm the eCFR terms page and vendor limit that are UNVERIFIED so the ecfr connector can be built to them.

## Description
Read the eCFR terms page and probe the versioner API (`versions/title-17.json?part=275`, `titles.json`, point-in-time `/full/{date}/`): whether a vendor limit is published, what happens without `Accept-Encoding: gzip` (arch says 406), the `removed: true` and `substantive: false` fields, and the 143 versions / 9 removed counts in the arch.

Output: a note under `docs/`, recorded samples for fixtures, and the confirmed `rate_limit_rps` (arch: 1 rps) in config. If the terms page forbids something the arch assumes, record it as a finding in the note (the orchestrator turns it into a question).

Out of scope: the connector (E11-T15).

## Acceptance criteria
- [ ] The note quotes the terms page wording on automated access and reuse, or states that none was found, with the URL and date read.
- [ ] A test (`test_ecfr_request_without_gzip_is_not_sent`) is not required here; instead the note records the status returned without the gzip header and with it.
- [ ] Recorded samples for `versions/title-17.json?part=275` and `titles.json` load in `test_ecfr_samples_load`, and the version and removed counts are stated next to the arch figures (143 and 9).
