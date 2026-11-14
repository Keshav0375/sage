# v3 — 2026-11-14 — run 20261114-183721 — parent v2

## Why this version

v2 judge 7.1 (Bloomberg) / 7.0 (247Labs): skills row clipped in PDF, Education above Experience, FinAdvisor eval below Sentinel. Remaining asks (years, fine-tuning, ETL, harness adoption numbers) are blocked by facts.

Judge reasons addressed:
- Fixed clipped skills entry ('O' → full list fits)
- Education moved below Projects
- FinAdvisor (financial RAG + eval) above Sentinel

## Changes

| # | Section | Before | After | Why | Job words | Fact ids | Sources |
|---|---|---|---|---|---|---|---|
| 1 | Skills | LLM & Evaluation row overflowed the page; 'Observability (LangFuse)' clipped | Row fits; LangFuse moved to LLMOps; 'Prompt Versioning' dropped (no fact) | ATS could not read the clipped item | observability | F014 | v2 judge, ats_check clipped-skill rule |
| 2 | Layout | Education 2nd section | Education after Projects | Lead with experience; judge ask |  |  | v2 holdout judge |
| 3 | Projects | Sentinel first | FinAdvisor (financial RAG, LLM-judge eval) first | Bloomberg/PSP/Equinix weight financial RAG + evaluation | financial, evaluation | F018, F021 | v2 round judge |

## Locked facts kept

Titles, employers, dates and every number are unchanged unless a fact id says otherwise.

## Scores

| Gate | Result |
|---|---|
| fact_gate | PASS |
| lint | PASS |
| ats | PASS (clipped-skill check) |
| keyword_coverage | 0.753 |
| pages | 2 |

## Jobs used

- Selected: —
- Round job: b5729698d052fcba
- Holdout job: b7886a49f0543311 (reused: all 5 selected jobs drawn)
