# v4 — 2026-11-15 — run 20261114-183721 — parent v3

## Why this version

v3 broke the original design (section order, skills overflow, short last lines, lone words, page-1 gap). v4 = v3 wording on the original design; layout-fixer filled every line (87–100%).

Judge reasons addressed:
- Design locked to original: same section order and skills rows
- Every bullet 2 full lines (last line ≥ 87%)
- No text past the margin; no lone words

## Changes

| # | Section | Before | After | Why | Job words | Fact ids | Sources |
|---|---|---|---|---|---|---|---|
| 1 | Layout | v3: Education after Projects; FinAdvisor before Sentinel | Original order restored (Education 2nd; Sentinel before FinAdvisor) | Design lock to the original |  |  | layout.py check vs design/baseline.json |
| 2 | Skills | v3: 'LLM & Evaluation' row past margin + extra unlabeled row | Original 7 labels, one line each (LLM-as-Judge, Vector Search, Guardrails in 'LLM & RAG'; Tool Calling in 'AI & Agents'; LangFuse in 'LLMOps'; pgvector in 'Databases') | No overflow; same rows as original | LLM-as-judge, guardrails, vector search | F005, F014, F018, F021 | layout gate |
| 3 | All bullets | 14 bullets with short last lines (25–78%) or a lone word on line 3 | Every bullet 2 lines, last line 87–100% full | Lines full, no gaps (Keshav's rule) |  | F002, F003, F006, F007, F009, F010, F011, F012, F015, F016, F017, F018, F019, F020 | layout-fixer (words only, facts locked), semantic fact gate PASS |

## Locked facts kept

Titles, employers, dates and every number are unchanged unless a fact id says otherwise.

## Scores

| Gate | Result |
|---|---|
| fact_gate | PASS (script + semantic, 0 blocks) |
| layout | PASS (design-locked, every last line ≥ 87%) |
| lint | PASS |
| ats | PASS |
| keyword_coverage | 0.729 |
| pages | 2 |

## Blind judge

Score **6.9** / 10 → BEST (design-locked) — stop: blocked by facts (round job: AI Developer (LLM & Agentic Systems) — same job as v1 round @ WSP in Canada)

- 5+ yrs and 2+ yrs leading LLM systems vs ~2 yrs
- No entity extraction/resolution or knowledge-graph facts
- Best architecture/RAG evidence is in projects

## Jobs used

- Selected: —
- Round job: 655f07473920532e (same as v1)
- Holdout job: b7886a49f0543311 (same as v1)
