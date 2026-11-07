---
key: "E11-T18"
title: "eurlex connector: CELLAR PRIIPs and MiFID in EN, DE, FR"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T2", "E11-T6", "E11-T7", "E11-T9"]
arch_refs: ["deep-dive/11-tech-stack.md#source-connectors-r4", "deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "deep-dive/06-interfaces-and-contracts.md#6.7", "decision-logs.md#adr-26"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 267, "id": 6263698710, "url": "https://github.com/Keshav0375/FinAdvisor/issues/267"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Implement the EUR-Lex CELLAR connector for three languages at 1 rps.

## Description
Implement `eurlex` (PUBLIC, class `law`, retire; `licence_class=eu_consolidated_ccby`).

Arch: CELLAR SPARQL and REST, no registration; XHTML and Formex (consolidated CELEX has no `text/html` or `pdf`); <= 1 rps (confirmed by E11-T2); poll `cdm:lastModificationDate` daily; 43 consolidated versions across five acts per language (MiFID II 14, MiFIR 11, PRIIPs 5, Delegated Reg 2017/565 6, RTS 2017/653 7); list all consolidated CELEX per act as the backstop; corrigenda are separate CELEX numbers; EN, DE, FR. Label "not authentic" and carry the base-act CELEX in `attribution_text` (only the Official Journal is authentic). The all-three-languages-or-none rule is enforced by the E11-T11 contract.

Out of scope: any other EU act.

## Acceptance criteria
- [ ] Given the recorded fixture then `list()` returns, per act and language, the consolidated CELEX versions and the counts match the E11-T2 note (test `backend/tests/connectors/test_eurlex.py::test_listing_counts_per_act_and_language`).
- [ ] Given `classify()` then `attribution_text` contains the not-authentic wording and the base-act CELEX, and `licence_class=eu_consolidated_ccby` (test `test_classify_attribution_not_authentic`).
- [ ] Given one act returned in EN and DE but not FR then the contract (E11-T11) quarantines the set (test `test_missing_language_quarantined_end_to_end`).
- [ ] Given any run then requests do not exceed 1 rps (test `test_throttle_1_rps`).
