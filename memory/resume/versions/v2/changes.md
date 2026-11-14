# v2 — 2026-11-14 — run 20261114-183721 — parent v1

## Why this version

v1 judge 6.5 (WSP) / 7.0 (Equinix): evaluation and trust work hidden, summary vague, tool soup, '&' style, co-op reads like DevOps. gaps.md top-7 wording changes.

Judge reasons addressed:
- Summary now names agent platforms, guardrails, eval-driven tuning
- Eval work moved up (FinAdvisor eval bullet first; LLM-as-Judge first in skills)
- Co-op reordered AI-first; fewer tools per bullet
- '&' replaced with 'and'
- Sentinel framed as trust controls

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

## Locked facts kept

Titles, employers, dates and every number are unchanged unless a fact id says otherwise.

## Scores

| Gate | Result |
|---|---|
| fact_gate | PASS (script + semantic; 2 blocks fixed) |
| lint | PASS |
| ats | FAIL (skills row clipped: 'Observability (LangFuse)') — found by the new ATS check after judging |
| keyword_coverage | 0.753 |
| pages | 2 |

## Blind judge

Score **7.1** / 10 → LOOP (round job: Senior Applied AI Engineer @ Bloomberg)

- Seniority: ~2 yrs vs Bachelor's+5 / Master's+4 for Senior
- No model training / SFT / RLHF, no code-gen over structured data, no publications
- Harness, compaction, Kong bullets have scope but no results; skills list cut off ('O')

## Jobs used

- Selected: b7886a49f0543311, a30716e346cc1cf4, b5729698d052fcba, 655f07473920532e, 151023ad6588a66e
- Round job: 151023ad6588a66e
- Holdout job: a30716e346cc1cf4
