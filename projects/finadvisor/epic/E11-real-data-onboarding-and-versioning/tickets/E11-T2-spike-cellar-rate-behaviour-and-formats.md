---
key: "E11-T2"
title: "Spike: CELLAR rate behaviour and formats"
epic: "E11"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/11-tech-stack.md#source-connectors-r4", "deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "decision-logs.md#adr-26"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 269, "id": 6263705042, "url": "https://github.com/Keshav0375/FinAdvisor/issues/269"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Measure how CELLAR SPARQL and REST behave at 1 rps so the eurlex throttle and formats are fixed.

## Description
Probe EUR-Lex CELLAR (SPARQL endpoint and REST) for the PRIIPs and MiFID acts in EN, DE and FR: observed throttling or errors at 1 rps and at a burst, the `cdm:lastModificationDate` poll query, the content types available for consolidated CELEX (arch: XHTML and Formex, no `text/html` or `pdf`), and one corrigendum (a separate CELEX). Rate is "undocumented (UNVERIFIED) / 1 rps" in the arch.

Output: a note under `docs/` of the FinAdvisor repo, recorded SPARQL and REST samples for the fixtures, and the confirmed `rate_limit_rps` for `eurlex` in config.

Out of scope: the connector (E11-T18).

## Acceptance criteria
- [ ] The note lists, per act (MiFID II, MiFIR, PRIIPs, Delegated Reg 2017/565, RTS 2017/653), the consolidated CELEX versions found and the languages returned; the counts are compared with the arch figures (43 per language) and any difference is stated.
- [ ] The note states the observed behaviour at 1 rps and at a short burst (status codes seen, or none).
- [ ] Recorded sample files load in `test_cellar_samples_load` and `EURLEX_RATE_LIMIT_RPS` is set in config (`test_eurlex_rate_limit_config_present`).
