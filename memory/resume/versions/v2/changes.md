# v2 — 2026-11-15 — run 20261114-183721 — parent v1

## Why this version

One version per run. 3 loop iterations; iter-3 promoted: it is the only one that keeps the original design, and it beats v1 on the same two jobs.

## Iterations in this run

| Iteration | What | Round judge | Holdout judge | Design lock |
|---|---|---|---|---|
| iter-1 | Wording rewrite from gaps.md | 7.1 (Bloomberg) | 7.0 | FAIL |
| iter-2 | Skills clip fix, Education moved, FinAdvisor first | 6.8 (MNP) | 7.7 | FAIL |
| iter-3 | iter-2 wording on the original design; every line full | 6.9 (WSP in Canada, same job as v1) | 7.2 | PASS |

Promoted: **iter-3**

Judge reasons addressed:
- Design locked to original: same section order and skills rows
- Every bullet 2 full lines (last line ≥ 87%)
- No text past the margin; no lone words

## Changes

| # | Section | Before | After | Why | Job words | Fact ids | Sources |
|---|---|---|---|---|---|---|---|
| 1 | Summary | AI Engineer with 2 years building production agentic AI, RAG, and LLM gateway systems… Startup-trained… | AI Engineer, 2 years shipping production agent platforms: multi-agent orchestration over MCP, RAG, LLM gateways with guardrails and eval-driven tuning. Cut token cost 48% at Kinaxis and latency 77% at a startup. | All 5 jobs ask agents + evaluation + guardrails; drop filler | agent platform, guardrails, evaluation | F001, F002, F003, F005, F011 | gaps.md W2, v1 judge |
| 2 | Kinaxis intern #1 | …over GitHub, Bitbucket, Atlassian, and Microsoft MCP; … | …Playwright tests over MCP; tiered model routing cut token cost 48% at task success. | Tool soup; 2-line limit | MCP, orchestration | F002 | gaps.md W3 |
| 3 | Kinaxis intern #2 | …porting legacy code to a UI/UX-driven web client. | shared agentic harness and plugin marketplace for the team: custom orchestration, lazy tool loading, declarative sandbox policies and eval-driven tuning. | Keep the platform signal, drop off-target clause | agentic harness, tool routing | F003 | gaps.md W4 |
| 4 | Kinaxis intern #3-4 | MAF agents … / Hardened Kong AI Gateway as the control layer… | Microsoft Agent Framework agents … / Kong AI Gateway as the guardrail layer… | Spell out framework; use guardrail wording the jobs use | guardrails, content safety, memory management | F004, F005 | gaps.md W5 |
| 5 | Kinaxis co-op | Backup pipeline first; long tool lists | MCP/OAuth2 framework → RAG agents → credential rotation → backup; ≤3 tools each | Co-op read like DevOps; AI work first | OAuth 2.0, MCP, retrieval quality | F006, F007, F008, F009 | gaps.md W6, resume review |
| 6 | Slideoo | '&' in prose; 'Benchmarked competing LLM candidates…' | 'and'; 'Benchmarked candidate LLMs for production on evaluation datasets…' | Style + evaluation wording | evaluation datasets | F010, F011, F012, F013 | gaps.md W7 |
| 7 | Projects | FinAdvisor eval bullet last; Sentinel 'Kept a human in control' | FinAdvisor eval bullet first; Sentinel 'Built trust controls into the agents' | Equinix weights evaluation and trust | LLM-as-judge, trust controls | F015, F021 | gaps.md W1, W8 |
| 8 | Skills | 7 rows incl. Java, Django, MongoDB, Snowflake | 'LLM & Evaluation' row first (LLM-as-Judge, RAG, Vector Search, Tool Calling, Guardrails, Prompt Engineering, Observability); dropped 4 off-target items | Tool soup; lead with what jobs ask | LLM-as-judge, vector search, tool calling | F005, F010, F011, F014, F018, F021 | gaps.md W10 |
| 9 | Hackathons | DevFest attendance line | (removed) | No signal |  |  | resume review |
| 10 | Layout | v3: Education after Projects; FinAdvisor before Sentinel | Original order restored (Education 2nd; Sentinel before FinAdvisor) | Design lock to the original |  |  | layout.py check vs design/baseline.json |
| 11 | Skills | v3: 'LLM & Evaluation' row past margin + extra unlabeled row | Original 7 labels, one line each (LLM-as-Judge, Vector Search, Guardrails in 'LLM & RAG'; Tool Calling in 'AI & Agents'; LangFuse in 'LLMOps'; pgvector in 'Databases') | No overflow; same rows as original | LLM-as-judge, guardrails, vector search | F005, F014, F018, F021 | layout gate |
| 12 | All bullets | 14 bullets with short last lines (25–78%) or a lone word on line 3 | Every bullet 2 lines, last line 87–100% full | Lines full, no gaps (Keshav's rule) |  | F002, F003, F006, F007, F009, F010, F011, F012, F015, F016, F017, F018, F019, F020 | layout-fixer (words only, facts locked), semantic fact gate PASS |

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
