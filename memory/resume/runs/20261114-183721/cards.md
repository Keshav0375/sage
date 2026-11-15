### 🔧 Card 1 — Tools

| Tool / source | Calls | OK | Failed | Fail reasons |
|---|---:|---:|---:|---|
| LinkedIn get job | 6 | 6 | 0 | — |
| LinkedIn search | 6 | 6 | 0 | — |
| JSearch | 2 | 2 | 0 | — |
| Glassdoor | 1 | 0 | 1 | HTTP 400 (provider rejected city/query) ×1 |
| scanners (145, W1-W3 planned) | 1 | 0 | 1 | sandbox network: tunnel 403 (run on Mac) ×1 |
| **Total** | **16** | **14** | **2** | cost $0.0054 |

### 📥 Card 2 — Jobs found

**64** found → **63** unique → **59** after knob filters → **59** live (dead 0, unknown 0) → **12** pre-ranked for A–H

Dropped: excluded title 3, agency 1

| Source | Jobs |
|---|---:|
| linkedin | 32 |
| jsearch | 32 |

### 🎯 Card 3 — Selected jobs (5)

| # | Role | Company | Where | Pay | A–H | Pre | Why |
|---:|---|---|---|---|---:|---:|---|
| 1 | [AI Engineer, Trust & Evaluation](https://careers.equinix.com/nl/jobs/ai-engineer-trust-evaluation-toronto-ontario-canada) | Equinix | Toronto, Ontario  | CAD 102,000–152,000 | 4.6 | 94.3 | Eval/guardrails-centred AI platform role at Equinix Toronto, 1-4 yrs asked, CAD… |
| 2 | [AI Engineer - Applied AI, Data & LLM Sy…](https://ca.indeed.com/viewjob?jk=fe42f74376708489) | 247Labs | Toronto, Ontario · hybrid | 55–60/hr | 3.8 | 76.0 | Strong skills match (RAG, eval, FastAPI, tool calling, guardrails, 3 clouds), r… |
| 3 | [AI Engineer, Innovation](https://www.linkedin.com/jobs/view/4487681731) | MNP | Calgary, Alberta, Canada  | — | 3.5 | 67.9 | Stack match is excellent (Azure AI Search RAG, evals, guardrails, agents, MCP) … |
| 4 | [AI Developer (LLM & Agentic Systems)](https://www.linkedin.com/jobs/view/4472100123) | WSP in Canada | Vancouver, British Columbia, … | 104,100–138,000 | 3.3 | 83.5 | Strong agentic/RAG/Azure content fit and remote-anywhere-in-Canada, but asks 5+… |
| 5 | [Senior Applied AI Engineer - Artificial…](https://www.linkedin.com/jobs/view/4478918069) | Bloomberg | Toronto, Ontario, Canada  | — | 3.3 | 67.2 | Toronto Bloomberg role matches agentic-harness work well, but Senior level (Bac… |

### ✍️ Card 4 — v3 changes (parent v2)

| # | Section | Before → After | Why | Job words | Facts |
|---:|---|---|---|---|---|
| 1 | Skills | LLM & Evaluation row overflowed the page; 'O… → **Row fits; LangFuse moved to LLMOps; 'Prompt Versioning…** | ATS could not read the clipped item | observability | F014 |
| 2 | Layout | Education 2nd section → **Education after Projects** | Lead with experience; judge ask |  |  |
| 3 | Projects | Sentinel first → **FinAdvisor (financial RAG, LLM-judge eval) first** | Bloomberg/PSP/Equinix weight financial RAG + eval… | financial, evaluation | F018, F021 |

Gates: fact `PASS` · lint `PASS` · ATS `PASS (clipped-skill check)` · keyword coverage 0.753 · pages 2

### ⚖️ Card 5 — Blind judge on v3: **6.8 / 10** → **STOP — blocked by facts (best version)**

Round job: AI Engineer, Innovation @ MNP · holdout: 7.7 on AI Engineer, Trust & Evaluation (Equini…

| Criterion | Score |
|---|---:|
| Requirement coverage | 1.9 |
| Evidence strength | 2.0 |
| Relevance and order | 1.2 |
| Clarity / 6-second scan | 1.1 |
| Seniority fit | 0.3 |
| ATS readability | 0.3 |

**Reasons:** 5+ yrs asked vs ~2 · Azure AI Foundry / Document Intelligence not in facts · No document-processing pipeline in facts

**Fixes asked:** Azure AI Foundry work (no fact) · Document ingestion bullet (no fact) · Move eval/guardrail results into work bullets with numbers (no numbers in facts)

### 🏁 Card 6 — Result

**New resume:** [`memory/resume/versions/v3/resume-v3.pdf`](memory/resume/versions/v3/resume-v3.pdf)

| Version | Judge | Keyword coverage |
|---|---:|---:|
| v1 | 6.5 | — |
| v2 | 7.1 | 0.753 |
| v3 | 6.8 | 0.753 |