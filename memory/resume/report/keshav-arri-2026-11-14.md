# Resume Review: Keshav Arri — 2026-11-14

- **Resume file:** [`../keshav-arri-2026-11-14.pdf`](../keshav-arri-2026-11-14.pdf) (2 pages)
- **Target roles:** AI Engineer, Applied AI Engineer, Agentic AI Engineer, Forward Deployed Engineer (Canada first, remote US second)
- **Market:** Canada (Ottawa, Toronto, Montréal, remote Canada), November 2026

---

## 1. Score

| Target band | Score | Why |
|---|---|---|
| Junior / intermediate AI Engineer (0–3 yrs), Canada | **8.0 / 10** | Skills match almost every bullet in the job posts. Real production work. Strong numbers. |
| Mid-level Applied AI Engineer (3+ yrs asked) | **7.0 / 10** | Skills match, but 22 months of full-time-type work and an "Internship" label pull you down. |
| Top AI labs / FDE (Anthropic, OpenAI, Cohere FDE) | **6.0 / 10** | They ask for 4+ yrs and customer-facing work. You show no customer-facing work. |

**Overall: 7.5 / 10.** The content is top 10–15% for your level. The packaging costs you about 1.5 points.

### Score by area

| Area | Score | Note |
|---|---|---|
| Keyword / ATS match | 9.0 | MCP, Agents SDK, LangGraph, evals, guardrails, gateway, OTel, Terraform, K8s. All hit. |
| Impact and numbers | 8.5 | 48%, 77%, 35%, 43%, 10x, 30 min → 15 s. Good. Some bullets have no number. |
| Proof (links, projects) | 8.0 | Two serious projects with test counts and eval gates. One link goes to a Projects board, not a repo. |
| Positioning (story) | 6.5 | Co-op bullets read like DevOps / platform work, not AI work. "Internship" after a finished Master's reads junior. |
| Readability (6-second scan) | 6.5 | Bullets are dense with tool names. Two pages. Weak filler on page 2. |

---

## 2. What the market asks for (job post comparison)

Two data sets: (A) 9 live LinkedIn posts (full text, pulled through Composio on 2026-11-14), and (B) 10 posts from web search summaries.

### 2A. Live LinkedIn posts (posted Oct 19 – Nov 13, 2026)

| # | Role | Company | Where | Yrs asked | Applicants | Pay | Your fit |
|---|---|---|---|---|---|---|---|
| L1 | [Senior AI Engineer, Agentic AI](https://ca.linkedin.com/jobs/view/senior-ai-engineer-agentic-ai-at-thomson-reuters-4450900129) | Thomson Reuters | Toronto | **2+ applied AI** | 200+ | CAD 100–145K | **9/10 — apply now** |
| L2 | [Agentic AI Developer](https://ca.linkedin.com/jobs/view/agentic-ai-developer-at-cgi-4484083890) | CGI (Gov of Canada) | Ottawa | 3+ | 151 | — | 8/10 (yrs short; needs Reliability Status) |
| L3 | [Software Engineer, AI](https://ca.linkedin.com/jobs/view/software-engineer-ai-at-softchoice-4470723434) | Softchoice | Ottawa | Intermediate | 200+ | — | 8/10 |
| L4 | [AI Engineer](https://ca.linkedin.com/jobs/view/ai-engineer-at-first-national-financial-lp-4481154397) | First National Financial | Toronto | — | 200+ | — | 8/10 (closes Nov 23) |
| L5 | [Junior AI Developer](https://ca.linkedin.com/jobs/view/junior-ai-developer-at-ericsson-4485784682) | Ericsson | Ottawa | Junior | 200+ | — | 9/10 skills, you are over-qualified; no sponsorship |
| L6 | [AI Engineer, Innovation](https://ca.linkedin.com/jobs/view/ai-engineer-innovation-at-mnp-4487681731) | MNP | Calgary | 5+ | 68 | — | 7/10 (stack is a 1:1 match, yrs short) |
| L7 | [AI Developer (LLM & Agentic)](https://ca.linkedin.com/jobs/view/ai-developer-llm-agentic-systems-at-wsp-in-canada-4471996035) | WSP | Anywhere in Canada | 5+ (2+ LLM) | 199 | CAD 95.5–130.8K (ON) | 6/10 |
| L8 | [Applied AI Engineer](https://ca.linkedin.com/jobs/view/applied-ai-engineer-at-openloop-4474609595) | OpenLoop | GTA | 5–15+ | 200+ | — | 5/10 (Senior+ only) |
| L9 | [AI Native Developer (Agentic)](https://ca.linkedin.com/jobs/view/ai-native-developer-agentic-applied-at-accenture-4477104369) | Accenture | Ottawa | 7+ | 101 | — | 4/10 |

**What the live posts tell us:**

1. **Every one of the 9 asks for evals with real numbers.** OpenLoop: "show 'this got better' with numbers". Accenture: "you have owned the eval harness". MNP: "offline evals, LLM as a judge, and human in the loop review". Your projects show this. **Your Kinaxis bullets do not.** Fix this first.
2. **Thomson Reuters reads like your resume.** "Orchestrator and sub-agent patterns", "MCP servers and gateways", "guardrails, automated evals", "shared agent patterns so new agents reuse common context, guardrail, and evaluation components", "Claude Code". Only 2+ yrs asked. This is your best live target.
3. **Multi-provider fallback + cost per agent is a common ask** (OpenLoop, Accenture, TR). You have it (LiteLLM fallback, circuit breaker, Kong per-user token metrics, tiered routing). Say "cost per agent / per user" in words.
4. **Safety is a hard ask in regulated jobs** (OpenLoop PHI + prompt injection, First National auditability + rollback, MNP PII, TR responsible AI). FinAdvisor and Kong Prompt Guard cover this. Add the words "prompt injection" if true.
5. **MCP is in 3 of 9** (CGI, MNP, TR). Still a rare edge.
6. **"Built a platform used by other teams"** is a named plus at OpenLoop. Your harness + plugin marketplace is exactly this. Put the user count on it.
7. **New gap: document processing.** MNP, First National, WSP ask for PDF / scan / unstructured text → LLM-ready input (Document Intelligence, extraction). Not on your resume. If you did any at Slideoo (PowerPoint pipeline is close), say it.
8. **New gap: client-facing work.** CGI, Accenture, Softchoice, WSP all say "work directly with clients / translate requirements". One bullet with stakeholders (Slideoo leadership, Kinaxis teams) helps.
9. **Years are the main filter.** 6 of 9 ask 3+ yrs. Many still interview strong 2-yr candidates (TR, CGI says "Entry level" in LinkedIn tags but 3+ in text). Apply anyway when the stack is a match.
10. **Competition is heavy.** 100–200+ applicants in 1–2 weeks on every post. Referrals matter more than polish.
11. **Work auth shows up.** Ericsson: "must be legally authorized… no sponsorship". CGI: Reliability Status. Put your status on the resume if it helps you.

### 2B. Web search posts

| # | Role | Company | Where | Pay (if listed) | Key asks |
|---|---|---|---|---|---|
| 1 | Applied AI Engineer, Agents & Automations | Cohere | Remote Canada (Toronto/Ottawa) | — | Ship and improve LLM/agent products, evals for multi-step agent workflows, product judgment |
| 2 | Applied AI Engineer – Agentic Workflows | Cohere | Multiple | — | Python + TS, cloud deploy + prod ops, agent design, failure handling, eval standards, strong communication, 25% travel |
| 3 | Agentic AI Engineer, AI Model Methodology | RBC | Toronto | — | Agents, MCP integration, agent skills, modular RAG in agent workflows |
| 4 | Applied AI Engineer | Fulfillment IQ | Toronto (hybrid) | CAD 135–170K | RAG, agents, eval frameworks |
| 5 | Applied AI Engineer | ContactMonkey | Toronto | CAD 140–160K | 3+ yrs SWE incl. LLM features |
| 6 | Senior Agentic AI Developer | MindBridge AI | Ottawa | USD 152–195K | 2+ yrs LLM / agentic systems |
| 7 | Senior/Staff Applied AI Engineer | Tali AI | Toronto | CAD 170–230K | 5+ yrs, own evals |
| 8 | Applied AI Engineer | Giesecke+Devrient | Montréal | — | RAG, embeddings, vector search, one of LangGraph / ADK / Claude Agent SDK / OpenAI Agents SDK |
| 9 | Forward Deployed Engineer, Applied AI | Anthropic | US | USD 200–300K | Build prod apps with Claude inside customer systems, 4+ yrs customer-facing, autonomy |
| 10 | Software Developer, AI Platform Foundations | Wealthsimple | Toronto | — | First-party AI tools and platforms |

### Match matrix

| Requirement (how often seen) | Your evidence | Match |
|---|---|---|
| RAG, embeddings, vector search (almost all) | FinAdvisor pgvector + Voyage; 3 RAG agents on Azure AI Search / Vertex | Strong |
| Agent frameworks + tool calling (almost all) | MAF, OpenAI Agents SDK, Anthropic SDK, orchestrator-subagent system | Strong |
| Evals: task success, cost, latency (most) | CI eval gate (95% citation / 90% faithfulness), 30 scenarios, "eval-driven tuning" | Strong on projects, **weak at work** (no eval number at Kinaxis) |
| MCP (RBC, Cohere, rising) | Self-hosted MCP server, MCP over GitHub / Bitbucket / Atlassian / Microsoft | **Rare edge** |
| Guardrails, safety, gateway (rising) | Kong AI Gateway, Prompt Guard, PII redaction, RLS, rate limits | **Rare edge** |
| Production cloud + CI/CD (most) | Terraform, K8s, ArgoCD, GitHub Actions, Azure / GCP / AWS | Strong |
| Strong Python (all) | Python first in list, pytest, FastAPI, pyright | Strong |
| TypeScript / product UI (Cohere, Ada) | Listed; "UI/UX-driven web client" only | Medium |
| Product judgment / user impact (Cohere, FDE) | Slideoo subscription growth, roadmap work | Medium |
| Customer-facing / communication (FDE, Cohere) | Not shown | **Gap** |
| Years: 3+ (ContactMonkey, Cohere mid) | ~22 months (Slideoo 12 + Kinaxis ~10.5) | **Gap** |
| ML fundamentals: fine-tuning, retrieval metrics (some) | Not shown | Gap (small) |

**Read:** You match 9 of 12 common asks. Your two rare edges (MCP + LLM gateway / guardrails) are the exact things banks and enterprise AI teams post for now. The gaps are years, customer-facing proof, and work-side eval numbers.

---

## 3. What Reddit says (r/cscareerquestionsCAD, r/MachineLearningJobs, r/LangChain, r/ITManagers)

1. **Recruiters scan for keywords first.** "Recruiters are non-technical… they just look for keywords" — [r/MachineLearningJobs](https://www.reddit.com/r/MachineLearningJobs/comments/1u032xt/what_aiml_projects_actually_impress_recruiters_in/). You pass this test easily.
2. **F-shape scan.** "People glance through pages in an F shape. So all the important things should be on the first and second section" — [r/MachineLearningJobs](https://www.reddit.com/r/MachineLearningJobs/comments/1ut1uac/aiml_engineer_resume_review_before_i_start/). Your page 1 is strong. Page 2 tail is weak.
3. **Judgment beats tool use.** "In 2026 the scarce skill is not writing code with a model… it is judgment about when not to use the model and how to make its output safe to run in production" — [r/ITManagers](https://www.reddit.com/r/ITManagers/comments/1uj91iy/hiring_an_ai_engineer_in_2026/). Your Sentinel limits (20 tool calls, 0.7 confidence gate, read-only tools) are exactly this. Lead with it in interviews.
4. **Prod vs POC.** Hiring managers ask "what would make you instantly believe this candidate built systems that work in production vs only POCs" — [r/MachineLearningJobs](https://www.reddit.com/r/MachineLearningJobs/comments/1unetp6/what_helped_you_crack_your_ai_engineer_interview/). Your answer: real users, real cost cuts, real incidents. Make that loud.
5. **Evals and tracing get asked about.** On an agents-engineer resume thread, reviewers pushed the poster to make evals and tracing (LangFuse) stand out more — [r/LangChain](https://www.reddit.com/r/LangChain/comments/1wfhs4h/help_me_review_my_resume_for_aiagents_engineer/).
6. **Canada junior market is brutal.** Grads report 650+ applications and 2-year hunts — [r/cscareerquestionsCAD](https://www.reddit.com/r/cscareerquestionsCAD/comments/1xb8wpr/cs_new_grad_no_internship_career_path/), [r/cscareerquestionsCAD](https://www.reddit.com/r/cscareerquestionsCAD/comments/1x38ig6/2_years_job_hunting_as_a_junior_dev_in_canada/). Referrals and a Kinaxis return offer beat cold applications.

### Web research (market)

- AI Engineer is LinkedIn's fastest-growing title for young workers two years in a row, but new-grad hiring overall fell ~20% vs 2019 ([letsdatascience](https://letsdatascience.com/news/linkedin-identifies-ai-engineer-as-fastest-growing-role-e82f85f1), [designnews](https://www.designnews.com/industry/entry-level-engineers-can-t-catch-a-break)).
- ML engineer openings sit ~59% above the Feb 2020 base while general SWE sits ~49% below ([aiweekly](https://aiweekly.co/alerts/ml-roles-surge-59-as-tech-cuts-hit-148092-in-2026)). You are in the right lane.
- A list of generic AI tools ("ChatGPT, Copilot, LangChain") no longer makes you stand out ([dataexec1](https://dataexec1.substack.com/p/ai-engineering-hiring-trends-2026)). Systems you shipped make you stand out.
- Internship is now close to a screening must ([resumetemplates](https://www.resumetemplates.com/career-advice/the-class-of-2026-hiring-report-how-ai-is-raising-the-bar-on-entry-level-hiring/)). You have it; Kinaxis is a known Canadian brand.

---

## 4. SWOT

### Strengths
- **On-market stack.** MCP, multi-agent orchestration, evals, LLM gateway, guardrails. This is the 2026 stack, not the 2023 "chat with PDF" stack.
- **Hard numbers.** 48% token cost cut, 77% latency cut, 35% cloud spend cut, 43% subscription lift, 10x traffic, 30 min → 15 s detection.
- **Production rigor.** Terraform, K8s, ArgoCD, OIDC, Vault, zero-downtime credential rotation. Most AI candidates cannot show this.
- **Safety thinking.** Prompt Guard, PII redaction, row-level security, human-in-the-loop limits, confidence gates. Banks and regulated companies want this.
- **Projects look like work, not toys.** 2,693 tests, strict pyright, tfsec, gitleaks, CI eval gates with thresholds.
- **Ownership story.** Startup architecture owner (Slideoo) → enterprise platform builder (Kinaxis). Co-op → internship return shows they wanted you back.

### Weaknesses
- **"Internship" after a finished Master's (Aug 2026 – Present).** Screeners read this as "still a student" and place you in the junior pile.
- **Co-op section reads DevOps.** 3 of 4 co-op bullets are backup pipelines, credential rotation, OAuth tests. A screener for AI roles may tag you "platform engineer".
- **Tool soup.** Bullets like "GitHub Actions CI/CD, Kubernetes, ArgoCD, and IAM" crowd out the result. Hard to scan in 6 seconds.
- **No work-side adoption or eval number for the harness.** "Team shared agentic harness and plugin marketplace" — how many engineers? how many plugins? what task success rate?
- **Weak bullets:** "Decommissioned a retired data source" (removal work, low signal). Slideoo bullet 3 ("Benchmarked competing LLM candidates…") has no number.
- **Skills list sprawl.** 8 languages incl. Lua, Java; Django, MongoDB, Snowflake. Dilutes focus; invites "tell me about your Snowflake work" with no answer on the page.
- **Page 2 filler.** "DevFest… Attended sessions" has zero signal. Short Anthropic / Databricks courses add little.
- **Sentinel link** goes to `github.com/users/Keshav0375/projects/4` (a Projects board), not a repo with code.
- **Style drift.** "&" in Slideoo bullets, "and" everywhere else.

### Opportunities
- **MCP + gateway + guardrails is a rare combo.** RBC, Cohere, banks, insurance, and enterprise SaaS post for it now. Target "AI platform" and "agentic platform" roles, not generic "AI Engineer".
- **Kinaxis return offer.** Best odds in this market. Convert the internship to full-time and the "Internship" label problem goes away.
- **Ottawa niche.** Kinaxis, Cohere (remote Canada), MindBridge, Shopify, Ciena, Nokia, government AI work. Less competition than Toronto.
- **FDE track later.** Your startup ownership + platform work fits Forward Deployed roles once you show customer-facing work.
- **Your public `sage` harness.** Itself is a portfolio piece (orchestrator + cheap subagents + review gates). Link it.

### Threats
- **Junior market crunch in Canada.** Hundreds of applications per role; many mid roles hard-filter at 3+ years.
- **Work authorization screens.** If you are on a PGWP, some ATS forms filter on "require sponsorship". Not on the resume today.
- **Attribution probes.** "Directly lifting subscription growth 43%" — interviewers will push on how you know your change caused it. Have the story ready, or soften the claim.
- **Keyword-rich resumes are everywhere.** AI tools make every resume look polished. Depth in interviews decides it.

---

## 5. Fix list (in order of impact)

1. **Cut to 1 page.** Drop Hackathons & Events (keep WinHacks only if space), drop DevFest, shrink certs to one line or drop. Cut Slideoo bullet 3 and the decommission bullet.
2. **Fix the "Internship" signal.** First choice: get the full-time conversion and update the line. Until then, use the title HR gave you and keep "Internship" in the small italic slot, not next to the title. Do not change it to anything that is not true.
3. **Put AI first in the co-op section.** Order: MCP OAuth framework → RAG regression tests → credential rotation → backup pipeline. Or merge the two backup / rotation bullets into one "platform reliability" bullet.
4. **Add numbers to the harness bullets.** Number of engineers / teams using it, number of plugins, task success rate, hours saved per epic.
5. **Kill tool soup.** Max 2–3 tools per bullet. Lead with the result. Example below.
6. **Trim skills to what you can defend for 20 minutes.** Drop Lua (keep it only in the Kong bullet), Java, Django, MongoDB, Snowflake unless the target post asks.
7. **Fix the Sentinel link** to a real repo. Add the `sage` repo link.
8. **Add a work-auth line** if true, e.g. "Open Work Permit (PGWP), no sponsorship needed".
9. **Rewrite the summary** to name your edge: agent platforms + LLM gateway + evals, not "startup-trained".
10. **Unify style:** "and" not "&"; "at equal task success" not "at task success".
11. **Add an eval number to a Kinaxis bullet** (all 9 LinkedIn posts ask for evals). Example: "eval suite of N tasks; success rose from X% to Y%".
12. **Add document processing** if you did any (Slideoo PowerPoint pipeline, PDF ingestion). MNP, First National, WSP ask for it.
13. **Apply this week:** Thomson Reuters Senior AI Engineer, Agentic AI (L1); First National AI Engineer (L4, closes Nov 23); Softchoice SE AI (L3); CGI Agentic AI Developer (L2). Find a referral for each on LinkedIn before you apply.

### Example rewrites

**Before:** Debugged a failing GCP Cloud SQL backup pipeline (0/21 exports) across GitHub Actions CI/CD, Kubernetes, ArgoCD, and IAM; added alerting cutting failure detection from 30 min to ∼15s, fixed in Terraform.
**After:** Fixed a GCP backup pipeline that failed 21 of 21 exports (IAM root cause, Terraform fix) and added alerts that cut failure detection from 30 min to 15 s.

**Before:** Built an orchestrator-subagent SDLC system turning Jira epics into research, plans, code, and Playwright tests over GitHub, Bitbucket, Atlassian, and Microsoft MCP; tiered model routing cut token cost 48% at task success.
**After:** Built a multi-agent system that turns Jira epics into plans, code, and Playwright tests through MCP; tiered model routing cut token cost 48% at equal task success, used by [N] engineers across [N] teams.

**Before (summary):** AI Engineer with 2 years building production agentic AI, RAG, and LLM gateway systems on Azure, GCP, and AWS. Startup-trained to own systems from architecture to production; now designs reusable agent platforms built around cost, safety, and team adoption.
**After:** AI Engineer who builds production agent platforms: multi-agent orchestration over MCP, LLM gateways with guardrails, and CI eval gates. Cut LLM token cost 48% at Kinaxis and generation latency 77% at an AI startup (2,000+ users).

---

## 6. Interview prep from this resume (they will ask)

- "48% token cost at task success" — how did you measure task success? What was the eval set?
- "Subscription growth 43%" — how did you separate your change from other causes?
- Compaction at 120K tokens — why 120K? What do you lose in summaries? How did you test it?
- Kong rate limits per token — how do you count tokens before the model answers?
- Sentinel 0.7 confidence gate — where does the confidence number come from? Is it calibrated?
- FinAdvisor LLM judge — how did you check the judge itself is right?

---

## 7. Limits of this review

- LinkedIn: 30 posts listed (3 searches: Canada entry/associate, Toronto, Ottawa; past month). Full text read for 9. The Kinaxis "ML/OR Platform Engineer" post (id 4438104987) failed to load; look at it by hand, it is at your own company.
- These job sites were blocked by the session network, so no full-text read: builtinottawa.com, swooped.co, apply.workable.com, careers.gi-de.com, wellfound.com.
- Job details come from web search summaries of aggregator pages. Some posts may be closed or reposted.

### Sources
- [Cohere — Applied AI Engineer, Agents & Automations (Built In Vancouver)](https://builtinvancouver.org/job/applied-ai-engineer-agents-automations/10577856)
- [Cohere — Applied AI Engineer, Agentic Workflows (Built In)](https://builtin.com/job/applied-ai-engineer-agentic-workflows/8115165)
- [Cohere — Agentic Workflows (Jobgether)](https://jobgether.com/offer/696a59bb96ae97ba4ad5f1b3-applied-ai-engineer---agentic-workflows-singapore)
- [RBC — Agentic AI Engineer](https://swooped.co/job-postings/agentic-ai-engineer-ai-model-methodology-toronto-rbc-0aa21)
- [Fulfillment IQ — AI Engineer](https://apply.workable.com/fiq/jobs/view/58B4201079.md)
- [ContactMonkey — Applied AI Engineer](https://wellfound.com/jobs/4822819-applied-ai-engineer)
- [MindBridge — Senior Agentic AI Developer](https://jobs.8vc.com/companies/mindbridge-ai-2/jobs/68717477-senior-agentic-ai-developer)
- [Tali AI — Senior/Staff Applied AI Engineer](https://www.choppingblock.ai/jobs/senior-staff-applied-ai-engineer-at-tali-ai)
- [Giesecke+Devrient — Applied AI Engineer](https://careers.gi-de.com/GieseckeDevrientEP/job/Montreal-Applied-AI-Engineer-QC/1393015233/)
- [Anthropic — Forward Deployed Engineer, Applied AI](https://jobs.generalcatalyst.com/companies/anthropic/jobs/70192292-forward-deployed-engineer-applied-ai)
- [Wealthsimple — Software Developer, AI Platform Foundations](https://careers.inovia.vc/companies/wealthsimple/jobs/87511541-software-developer-ai-platform-foundations)
- [AI Engineering Hiring Trends 2026](https://dataexec1.substack.com/p/ai-engineering-hiring-trends-2026)
- [LinkedIn: AI Engineer fastest-growing role](https://letsdatascience.com/news/linkedin-identifies-ai-engineer-as-fastest-growing-role-e82f85f1)
- [Entry-Level Engineers Can't Catch a Break](https://www.designnews.com/industry/entry-level-engineers-can-t-catch-a-break)
- [ML Roles Surge 59%](https://aiweekly.co/alerts/ml-roles-surge-59-as-tech-cuts-hit-148092-in-2026)
- [Class of 2026 Hiring Report](https://www.resumetemplates.com/career-advice/the-class-of-2026-hiring-report-how-ai-is-raising-the-bar-on-entry-level-hiring/)
- Reddit threads linked in section 3.
