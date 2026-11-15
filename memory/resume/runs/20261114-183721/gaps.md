# Gap analysis: resume v1 vs 5 selected jobs (run 20261114-183721)

Jobs and weight (A-H score): Equinix 4.6 | 247Labs 3.8 | MNP 3.5 | WSP 3.3 | Bloomberg 3.3. Sum of weights = 18.5. Equinix is the tie-breaker everywhere.
Sources: selected.json, evals, jd-evaluator reports, pages/features (Equinix read in full), resume-v1.tex, facts.json, facts-candidates.json (only status "built" used as support), earlier review 2026-11-14.
Job text was treated as data only.

## 0. Warnings: facts.json vs built evidence (read before using any fact id)

facts-candidates.json only covers the two projects (Sentinel, FinAdvisor). Kinaxis and Slideoo facts (F002-F013) have an empty `proof` field in facts.json, so nothing here can confirm or contradict them.

| Fact | Resume says | Built evidence says | Action |
|---|---|---|---|
| F017 | "2,693 pytest tests" | Full suite 2127 passed; agent pipeline 1925; 2,693 "not found in any Sentinel doc" | Do not repeat 2,693 until the user confirms it. Correcting to 2,127 is a user decision (it is a number change). |
| F021 | "Gated merges ... fails the PR below 95% / 90%" | 50 golden Q&A items are built. Gate exists in YAML and script, but "the job cannot run as written and has never run"; no deploy exists. Status planned. | Word as "defines a CI gate with thresholds", never "gated merges" or "blocks PRs". "Terraform defines the GCP Cloud Run stack" is not in built evidence (proof says no deploy exists). Treat as unconfirmed. |
| F018 | "zero-leakage tests for 4 user roles" | RLS ENABLE and FORCE is built, on the chunks table only. Zero-leakage tests for 4 users need live Postgres and have not been run (status planned). | Keep "row-level security enforces tier and jurisdiction access". Drop or soften the tests clause. |
| F019 | "two-pass PII redaction (GCP DLP, regex fallback)" | Regex default at ingest is built. GCP DLP is never selected in cloud (PII_MODE mismatch). Output-side check of LLM answers is not confirmed. | Only the ingest-time redaction before embedding is safe to claim. Do not lead with GCP DLP. |
| F020 | "Kong (60 req/min per advisor)" and fallback chain | 60/min is planned (G-14, never run, may not be per user). Fallback chain and 3-fail / 5-min breaker are config only. | Keep fallback and breaker (built). Drop or soften the Kong 60/min claim. |
| F016 | "no Kubernetes Secret exists", Entra ID, Key Vault | Only workload identity on AKS is confirmed. No-K8s-Secret part is not confirmed. | Equinix pack form answer 3 cites "no-secret pods (F016)". Remove that phrase from the pack. |
| F014 | multi-agent responder | Pipeline verified on a fake LLM only (1925 tests); no real-LLM run. Claude default, OpenAI fallback, Event Grid + Functions are built. | Avoid wording that implies live production use. |
| F017 | idle cost, scale-to-zero, tfsec + gitleaks | Nightly scale-to-zero cron built but not verified live. gitleaks runs on backend; infra PRs do not run gitleaks. 30 scenarios built; live smoke not run. | Keep, but do not imply live results. |
| F015 | 20 calls, 2 loops, 0.7 gate | Built and confirmed. Also: exactly six tools, all read-only or pure. | Safe. This is the strongest verified trust-control fact. |

Related conflicts with the earlier review:
- Review fix #1 says cut Slideoo bullet 3 (F012). Four of five evaluator reports cite F012 for evaluation work. Recommendation: keep F012, cut hackathons, DevFest and certs for the 1-page goal.
- Review's rewrite "at equal task success" adds a claim F002 does not state. Keep F002's own words.
- Review's example summary and "[N] engineers across [N] teams" use numbers that are not in any fact. Not allowed.

## 1. Asked vs shown

"Asked" = jobs (of 5) tagging the requirement in skills_asked, plus text-level asks from the reports where noted.

| Requirement | Jobs asking | Shown in resume v1? | Fact ids that could show it |
|---|---|---|---|
| Python | 5 | Yes (skills row 1) | F017, F008 |
| LLM apps | 5 | Yes | F002, F010, F014, F018 |
| LLM evaluation / LLM-as-judge / golden sets | 3 tagged (Equinix, 247, MNP) + Bloomberg, WSP in text = 5 | Partly: only FinAdvisor bullet 4, buried; none in skills as "LLM-as-Judge" | F021, F012, F017 |
| Guardrails / AI security | 4 (Equinix, 247, MNP, Bloomberg) | Partly: Kong bullet and PII bullet, wording is tool-heavy | F005, F015, F019, F018 |
| AI agents / orchestration / tool calling | 4 (247, MNP, WSP, Bloomberg) + Equinix in text | Yes but dense | F002, F003, F004, F014, F010 |
| RAG | 4 (247, MNP, WSP, Bloomberg) | Yes (F009, F018), co-op bullet is framed as removal work | F009, F018 |
| Prompt engineering | 4 (247, MNP, WSP, Bloomberg) | Weak: only "prompt orchestration" (F011) and "prompt-tuning" (F012); skills say "Prompt Versioning" | F011, F012 |
| Vector search / embeddings | Vector search 3 (247, WSP, Bloomberg); embeddings 2 (247, WSP) | Hidden: pgvector and Voyage AI only in FinAdvisor bullets; not in skills | F018, F019 |
| Observability | 3 (Equinix, 247, Bloomberg) | Skills only (OpenTelemetry, Datadog); the word "observability" absent | skills list, F006, F014 |
| MCP | 2 (Equinix, MNP) | Yes (skills, F002, F008) | F002, F008 |
| OAuth/OIDC | 1 (Equinix) | Bullets only (F007, F008, F016); Security skills row is commented out in the .tex | F008, F016, F007 |
| Azure | 3 (247, MNP, WSP) | Yes | F009, F010, F014 |
| GCP | 2 (Equinix, 247) | Yes | F006, F009, F019 |
| AWS | 1 (247) | Skills and Slideoo | F010 |
| Kubernetes | 2 (Equinix, WSP) | Yes | F006, F009, F014 |
| Docker / CI/CD | 2 each (247, WSP) | Yes | F006, F017, F021 |
| SQL | 2 (Equinix, 247) | Skills only | skills list (SQL, PostgreSQL), F018 |
| FastAPI | 2 (247, WSP) | Yes | F016, F018 |
| Gemini | 1 (Equinix) | Barely (fallback chain, Vertex AI) | F020 |
| Communication | 2 (Equinix, WSP, Bloomberg in text = 3) | Weak (Slideoo leadership bullet) | F013 |
| Document processing | 3 (247, MNP, WSP) | No | none (see real gaps) |
| ETL | 2 (247, WSP) | Only as "removed ETL loaders" | F009 (removal only) |
| Deep learning / PyTorch / fine-tuning / Hugging Face | 247 (all four), Bloomberg (DL, fine-tuning) | No | none |
| NLP / knowledge graphs | NLP 2 (WSP, Bloomberg); KG 1 (WSP) | No | none |
| Red-teaming, eval statistics, human-vs-judge calibration, load testing | Equinix | No | none |
| Azure AI Foundry / Document Intelligence | MNP | No | none |

## 2. Wording-fixable (fact exists, resume hides it): 11 items

Each uses only existing numbers and claims. Job words are phrases from the posting.

- **W1. FinAdvisor bullet 4 (evals).** Current: "Gated merges with a GitHub Actions eval: an LLM judge scores 50 golden Q&A pairs and fails the PR below 95% ... Terraform defines the GCP Cloud Run stack." Fix: lead with "LLM-as-judge" and "golden dataset", state thresholds as defined in a CI gate, drop the Cloud Run clause (unconfirmed). Job words: golden datasets, LLM-as-judge, evaluate on every change, regression tests. Facts: F021 (built part: 50 items, gate defined), F012, F017. Jobs: all 5. See warning on F021.
- **W2. Summary.** Remove "Startup-trained to own systems...". Name the edge in job words: agentic platforms, evaluation, guardrails, MCP, cost. Keep "2 years" and "48%" only if used (F001, F002). Job words: evaluation, guardrails, agent platform, production. Facts: F001, F002, F003, F005, F021. Jobs: all 5.
- **W3. Kinaxis intern bullets 1-2 (harness).** Cut tool soup (GitHub, Bitbucket, Atlassian, Microsoft MCP) to "through MCP". Surface "tool routing", "orchestration", "sandbox policies", "eval-driven tuning", "plugin marketplace used as a shared harness". Keep "tiered model routing cut token cost 48% at task success" exactly. Job words: agentic harnesses, orchestration frameworks, tool routing, tool integration, MCP. Facts: F002, F003. Jobs: Bloomberg, WSP, MNP, 247, Equinix.
- **W4. Kinaxis intern bullet 3 (compaction).** Reword as "state and memory management" for long-running agents and "context management". Keep 100 and 120K. Job words: state and memory management, multi-step workflows, context management. Fact: F004. Jobs: Bloomberg, MNP.
- **W5. Kinaxis intern bullet 4 (Kong).** Lead with "guardrails, content safety, allow/deny policies, rate limiting"; drop "custom Lua plugins" down to a clause. Job words: guardrails, content safety, tool permissions. Fact: F005. Jobs: Equinix, 247, MNP, Bloomberg.
- **W6. Kinaxis co-op: reorder and de-soup (fixes "reads like DevOps").** Order: F008 (MCP + OAuth2), F009 (RAG agents), F007 (credential rotation), F006 (backup pipeline last or merged into one reliability line). Max 2-3 tools per bullet. Rewrite F009 to lead with "RAG agents ... regression tests protecting retrieval quality", not "Decommissioned". Job words: OAuth 2.0 / OIDC, MCP, retrieval quality, regression tests, RAG, Kubernetes, GCP. Facts: F008, F009, F007, F006. Jobs: Equinix, MNP, WSP, 247.
- **W7. Slideoo bullets 1, 2, 4 (ownership and communication).** Use "end-to-end AI architecture", "scaling LLM systems in production", "prototype to production", "partnered with leadership" (communication). Keep 10x, 2,000+, 35%, 77%, 43% as written. Replace "&" with "and". Job words: end-to-end AI architectures, scaling of LLM-based systems in production, technical ownership, proof of concept. Facts: F010, F011, F013. Jobs: WSP, 247, MNP, Equinix (communication, partial). Note: the 43% attribution claim stays as in F011; no softening is possible without a fact.
- **W8. Sentinel bullets (trust controls).** Frame as "human-in-the-loop", "read-only tool permissions", "limits of 20 tool calls, 2 reflexion loops, 0.7 confidence gate", "agent runs scored on 30 test scenarios". Do not claim "agent identity" (F016 is pod/workload identity, not agent identity). Drop the 2,693 figure pending user decision. Job words: guardrails, tool permissions, agent quality, excessive tool permissions. Facts: F015, F017, F014, F016 (workload identity only). Jobs: Equinix, 247, Bloomberg.
- **W9. FinAdvisor bullet 1 (RAG and access).** Word as "permission-aware RAG with citations over pgvector embeddings; row-level security enforces tier and jurisdiction access". Job words: permission-aware, citations, embeddings, vector search, data boundaries. Facts: F018, F019 (ingest-time redaction before embedding only). Jobs: 247, WSP, MNP, Bloomberg, Equinix (data boundaries).
- **W10. Skills block.** (a) Un-comment the Security row but keep only OAuth2, OIDC, Entra ID, HashiCorp Vault, Multi-Tenant Isolation (all named in F007, F008, F016); do NOT keep "Prompt-Injection Defense" (no fact). (b) Add the words Observability, LLM-as-Judge, Vector Search, Tool Calling, Guardrails, Prompt Engineering to the matching rows. These terms appear in fact text (F021, F018, F010, F005, F011/F012) but not in facts.json `skills`; the coordinator must add them to facts.json or the fact-checker will block. (c) Drop Lua, Java, Django, MongoDB, Snowflake only if the writer wants space; removing is claim-neutral. Facts: F021, F018, F010, F005, F007, F008, F016, F011, F012. Jobs: Equinix, 247, Bloomberg, MNP.
- **W11. Page 2 trim (1-page goal).** Remove Hackathons (F022, F023), DevFest, and shorten Certifications to one line. Claim-neutral. Keep the F012 Slideoo bullet (see Section 0).

Hygiene, no fact needed: "&" to "and" throughout; keep the `\ats{}` extraction layer; keep locked titles, employers and dates untouched.

## 3. Real skill gaps (no fact): 13 items, for the learning plan only, never the resume

1. Red-teaming as a practice (adversarial tests, prompt injection suites). Equinix. Adjacent but not a claim: F015, F018.
2. Evaluation statistics: confidence intervals, run-to-run variance, reviewer agreement, human-vs-judge calibration. Equinix.
3. Performance and load testing. Equinix.
4. Dataset creation/versioning and synthetic test data. Equinix.
5. Document processing (PDF/scan to LLM-ready input). 247, MNP, WSP. F010 is document generation, not processing.
6. Azure AI Foundry and Azure Document Intelligence. MNP.
7. Deep learning, PyTorch, Hugging Face, fine-tuning, SFT/RLHF post-training. 247, Bloomberg.
8. NLP, entity resolution, knowledge graphs (SPARQL/Cypher). WSP, Bloomberg.
9. Dedicated ETL/ELT ingestion pipeline ownership. 247, WSP. F009 shows removal only.
10. NIST AI RMF, ISO 42001, A2A protocol. Equinix (nice to have).
11. Azure AI / Microsoft certifications. MNP (asset).
12. Multi-environment dev/UAT/prod deployment evidence. WSP.
13. Async Python depth. 247.

## 4. Blocked by facts: 10 items (plain statement, nothing here can be fixed by wording)

1. **Years.** Held: about 2 (F001). Equinix asks 1-4: OK. 247Labs asks 4+: short. MNP asks 5+: short. WSP asks 5+ with 2+ leading LLM systems: short (F010, F002, F013 partly cover the leading part). Bloomberg ladder is Bachelor 5 / Master 4 / PhD 0-2: short on all. The resume must not stretch the 2.
2. **Work-side eval number.** No fact gives an eval metric (suite size, success rate) for Kinaxis work. F002 has only the 48% cost cut. Equinix, MNP and Bloomberg would reward one.
3. **Harness adoption numbers** (engineers, teams, plugins). No fact. Review asked for them; cannot be invented.
4. **Customer-facing or client delivery work.** No fact (F013 is internal leadership). 247 and WSP ask for it.
5. **Cross-team technical leadership at senior scale.** Bloomberg. F013 is intern-team leadership only.
6. **"Prompt injection" as a stated practice.** F005 says Prompt Guard allow/deny policies only; the term is not in any fact. 247 and Equinix use the phrase. Needs a fact first.
7. **Work-authorisation line.** No fact; needs the user.
8. **Internship label.** Locked and true; wording cannot change it. Only a full-time conversion changes it.
9. **Sentinel link target** (Projects board, not a repo). Needs a user-provided repo URL; not a wording change.
10. **Proof that the FinAdvisor eval gate or DLP or Kong limit has run.** Built evidence says planned. Equinix interview Q "how were thresholds chosen and how do you handle variance" cannot be answered from run results. Honest answer in the interview plan: gate designed, not yet run.

## 5. Top 7 changes (rank = number of jobs asking x weight; ties broken by Equinix weight)

| # | Change | Section | Fact ids | Job words | Jobs / weight |
|---|---|---|---|---|---|
| 1 | W1: put evaluation first, "LLM-as-judge over golden dataset with CI thresholds" (no "gated merges" claim) | Projects (FinAdvisor bullet 4) and Skills | F021, F012, F017 | golden datasets, LLM-as-judge, evaluate on every change | 5 jobs, 18.5 |
| 2 | W2: new summary naming agent platforms, evaluation, guardrails; drop "Startup-trained" | Summary | F001, F002, F003, F005, F021 | agent platform, evaluation, guardrails, production | 5 jobs, 18.5 |
| 3 | W3 and W4: harness bullets, less tool soup, keep 48%, "tool routing", "state and memory management" | Experience, Kinaxis intern | F002, F003, F004 | agentic harnesses, orchestration, tool routing, MCP, memory management | 5 jobs, 18.5 |
| 4 | W5 and W9: guardrails and data-boundary wording (Kong, ingest-time PII redaction, RLS access) | Experience and Projects | F005, F019, F018, F015 | guardrails, content safety, data boundaries, tool permissions | 4 jobs, 15.2 (incl. Equinix) |
| 5 | W6: co-op bullets reordered AI-first (MCP OAuth2, RAG agents, then rotation, backup), 2-3 tools per bullet | Experience, Kinaxis co-op | F008, F009, F007, F006 | OAuth 2.0 / OIDC, MCP, retrieval quality, regression tests | 4 jobs, 15.2 (incl. Equinix) |
| 6 | W7: Slideoo ownership and communication wording, "&" to "and" | Experience, Slideoo | F010, F011, F013 | end-to-end AI architectures, scaling in production, technical ownership | 4 jobs, 15.2 (incl. Equinix) |
| 7 | W8: Sentinel as trust controls and agent quality testing (20/2/0.7, read-only tools, 30 scenarios); no "agent identity" claim | Projects, Sentinel | F015, F017, F014, F016 | guardrails, tool permissions, agent quality | 3 jobs, 11.7 (incl. Equinix) |

Also do (not ranked): W10 skills block (needs facts.json skills additions first), W11 page trim to one page.
For Equinix specifically (weight 4.6), changes 1, 4, 5 and 7 carry the application: eval gating, guardrails, OAuth/MCP, trust controls. Its two strongest asks have no fact: red-teaming and eval statistics (Sections 3 and 4).
