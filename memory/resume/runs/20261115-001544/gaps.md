# Gaps - run 20261115-001544

Base: versions/v2/resume-v2.tex (latest). Judge: versions/v2/judge.json (score 6.9, holdout 7.2). Jobs: E = Equinix f997beef22b3a673, G3 = Google SWD III 4821426bf3dadf81, G2 = Google SWD II 22b04aa3f2bbc5ee, M = MNP b5729698d052fcba, W = WSP 655f07473920532e, F = Fidus 58251ba27e0927ec.
Layout rule: words only. Same sections, same skills row labels, each bullet keeps its line count.
Candidates (NC01-NC07) are not facts. This file uses them only as "needs Keshav to confirm and merge".

## 1. Asked vs shown

| Requirement | Jobs asking (of 6) | Shown in v2? | Fact ids |
|---|---|---|---|
| LLM evaluation, LLM-as-judge, golden set, offline evals | 4 (E, G3, M, W) | Yes, but weak words. Slideoo bullet 3 and FinAdvisor bullet 1. No "offline evals" or "error analysis". | F012, F021 (open check) |
| Agents, MCP, tool workflows | 4 (E, M, W, F) | Yes. Kinaxis bullets 1-2, Sentinel, Skills row. | F002, F003, F004, F008, F014 |
| RAG, vector search, Azure AI Search | 3 (E, M, W) | Yes, but not in the summary. Co-op bullet 2, FinAdvisor bullet 2. | F009, F018 |
| Guardrails, content safety, PII, access control | 2 (E, M) | Yes. Kong bullet, FinAdvisor PII bullet, Sentinel bullet 3. | F005, F016, F019 (open check) |
| AI coding tools used daily | 3 (G2, M, F) | Weak. Only the Anthropic cert line and Kinaxis bullet 1 imply it. | F002, F003 |
| Deploy, evaluate, debug ML end to end | 2 (G3, E) | Partial. Slideoo bullets 2-3 and co-op bullet 4 do not use these verbs. | F010, F011, F012, F006 |
| Code review, sprint, Agile | 2 (M, G3) | Partial. Slideoo bullet 4 says "sprint planning, reviews". | F013 |
| OAuth, OIDC | 1 (E) | Yes. Co-op bullet 1, Sentinel bullet 3. | F008, F016 |
| Python, FastAPI, tests, CI/CD | 4 (E, W, F, G3) | Yes. | F008, F016, F017, F006 |
| Tracing, OpenTelemetry | 1 (E) | Skills row only. | F014 |
| Master's degree (nice) | 2 (G3, G2) | Yes. Education section. The evaluators marked "none" by mistake. | none needed |
| Evaluation statistics, reviewer agreement, dataset versioning | 1 (E) | No | none |
| Red-teaming, adversarial tests | 1 (E, nice) | Partial: limits only | F015 (NC04 pending) |
| Document processing (PDF, scans) | 1 (M) | No | none |
| NLP entity extraction and resolution, knowledge graphs | 1 (W) | No | none |
| Azure AI Foundry, Azure AI certificates | 1 (M) | No | none (Azure OpenAI, AI Search exist) |
| dev/UAT/prod multi-environment flow | 1 (W) | No | none |
| Embedded hardware, C/C++, RTOS, serial console | 1 (F) | No | none |
| Data structures and algorithms | 1 (G3, nice) | No | none |
| Accessible technologies | 2 (G3, G2, nice) | No | none (NC03 pending) |
| 5+ years | 2 (M, W) | No (2 years held) | F001 |

## 2. Wording-fixable (fact exists, resume hides it)

1. Slideoo bullet 3 (F012). Job words: "offline evals", "error analysis", "evaluation datasets" (M, E, W).
   Now: "Benchmarked candidate LLMs for production by analyzing evaluation results and datasets across generation, surfacing quality regressions early and driving data-backed prompt-tuning decisions as traffic scaled."
   Change: "Benchmarked candidate LLMs with offline evals on evaluation datasets across generation; error analysis surfaced quality regressions early and drove data-backed prompt tuning as traffic scaled."
   Fact-checker note: "offline evals" and "error analysis" are mild rewording of "analyzing evaluation results". Confirm.
2. FinAdvisor bullet 1 (F021, open check). Now says "Gated merges with a GitHub Actions eval". The check says the gate has not run. Candidate evidence shows the gate code and 50-item set exist (commit 6e6fbdb). Safer words: "Built a GitHub Actions eval gate: an LLM judge scores 50 golden Q\&A pairs and fails the PR below 95\% citation accuracy or 90\% faithfulness; ..." This lowers the claim to what is proven. Same line count.
3. Summary line (F001, F009, F005, F019). Job words: "RAG on Azure AI Search", "content safety", "PII", "offline evals" (M, W, E).
   Now: "...multi-agent orchestration over MCP, RAG, LLM gateways with guardrails and eval-driven tuning."
   Change: "...multi-agent orchestration over MCP, RAG on Azure AI Search, LLM gateways with content-safety guardrails and eval-driven tuning." Keep to the same line count; drop "Cut token cost 48\% ..." only if it wraps (do not drop; trim "shipping" first).
4. Kinaxis intern bullet 2 (F003). Job words: "AI coding tools", "daily" (G2, M, F). Change: "Generalized it into a shared agentic harness and plugin marketplace for the team's AI coding workflow: ..." Fact says "team shared"; do not write "daily use" or a user count. Fact-checker to confirm "AI coding workflow".
5. Slideoo bullet 2 (F011) and co-op bullet 4 (F006). Job words: "deploy, evaluate, debug, data" (G3); "trace failures to root cause" (E). Slideoo: "...cutting generation latency 77\% ... " add verb "profiled, reworked and shipped". Co-op 4 already says "Debugged"; add "root cause" only if line allows: "Traced a GCP Cloud SQL backup pipeline failing 0/21 exports to its root cause across ...". Fact-checker: "root cause" follows from "debugged and fixed". Confirm.
6. Skills row "LLM \& RAG" (skills list has "LLM Evaluation", "Prompt Engineering"). Job words: "LLM Evaluation" (E, G3, M, W). Swap "Vector Search" for "LLM Evaluation" (pgvector stays in Databases). Same row label, no new line.
7. Slideoo bullet 4 (F013). Job words: "code reviews", "sprint planning" (M, G3). "Led a team of interns ... driving sprint planning, code reviews, and technical mentorship ...". Do not write "Agile" or "Scrum": no fact says it.

## 3. Real skill gaps (no fact; learning plan only, never the resume)

1. Evaluation statistics, judge-vs-human agreement, dataset versioning (E; judge fix on holdout).
2. Red-teaming and prompt-injection tests (E). NC04 shows judge-conflict guard; Keshav must confirm before use.
3. Document processing pipelines: PDF, scans, Document Intelligence (M).
4. NLP entity extraction and entity resolution (W).
5. Knowledge graphs (W, nice).
6. Azure AI Foundry and Azure AI certificates (M).
7. dev/UAT/prod multi-environment release flow (W; judge fix).
8. Embedded hardware, C/C++, RTOS, serial console (F).
9. Data structures and algorithms coding rounds (G3).
10. Accessible technologies (G3, G2). NC03 shows Lighthouse a11y 1.00; not a fact yet.

Count: 10.

## 4. Blocked by facts

- 5+ years asked by M and W. Held: 2 (F001). Years cannot change. Both jobs are a stretch.
- "2+ years leading LLM or agent systems" (W): F001 and F013 show 2 years and an intern team lead. Say nothing more.
- Controlled Goods eligibility (F): no fact. Keshav must answer; the resume must not say.
- Open checks F017, F018, F019, F020, F021: writers must not strengthen. Note F017 "2,693 pytest tests": the README shows a collected count, not a pass count. Safer word is "collects 2,693 pytest tests". Note F020 "60 req/min per advisor" is not confirmed. Note F019 "GCP DLP" is not confirmed.
- No metric exists for eval-at-scale at work (judge holdout fix). Blocked until NC04/NC05 are confirmed and merged.

Count: 5 items.

## 5. Top 7 changes (jobs asking x judge weight)

Weight: 3 = named in judge fixes or holdout fixes; 2 = Requirement coverage or Evidence strength loss; 1 = keyword or order only.

| # | Change | Section | Facts | Job words | Jobs x weight |
|---|---|---|---|---|---|
| 1 | Eval wording: Slideoo bullet 3, and FinAdvisor bullet 1 lowered to "Built ... eval gate" | Experience (Slideoo), Projects | F012, F021 | offline evals, error analysis, evaluation datasets, LLM as judge | 4 x 3 = 12 |
| 2 | Lead Kinaxis intern bullets with the Kong guardrail bullet (reorder, same lines) | Experience | F005 | guardrails, content safety, PII | 2 x 3 = 6 |
| 3 | Summary: RAG on Azure AI Search, content-safety guardrails | Summary | F001, F009, F005 | RAG, Azure AI Search, content safety | 3 x 2 = 6 |
| 4 | Kinaxis intern bullet 2: "AI coding workflow" | Experience | F003 | AI coding tools | 3 x 2 = 6 |
| 5 | Slideoo bullet 2 and co-op bullet 4: deploy, evaluate, debug, root cause | Experience | F011, F006 | deploy, evaluate, debug, root cause | 2 x 2 = 4 |
| 6 | Skills row "LLM \& RAG": swap "Vector Search" for "LLM Evaluation" | Skills | skills list | LLM Evaluation | 4 x 1 = 4 |
| 7 | Slideoo bullet 4: "code reviews, sprint planning" | Experience | F013 | code review, sprint planning | 2 x 1 = 2 |

Notes for the writer: run a layout check after change 2 and change 3 (line count). Keep the design lock. Do not add Agile, Scrum, or any number not in facts.json.
