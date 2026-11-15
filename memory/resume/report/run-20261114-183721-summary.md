### Tool calls

| Tool call | Where | Success or fail | Reason |
|---|---|---|---|
| LinkedIn search | LinkedIn (Composio job_search) | success | — |
| LinkedIn search | LinkedIn (Composio job_search) | success | — |
| LinkedIn search | LinkedIn (Composio job_search) | success | — |
| LinkedIn search | LinkedIn (Composio job_search) | success | — |
| LinkedIn search | LinkedIn (Composio job_search) | success | — |
| LinkedIn search | LinkedIn (Composio job_search) | success | — |
| JSearch | JSearch / Google for Jobs (Composio) | success | — |
| JSearch | JSearch / Google for Jobs (Composio) | success | — |
| Glassdoor | Glassdoor (Composio) | fail | HTTP 400 (provider rejected city/query) |
| scanners (145, W1-W3 planned) | scanners (145, W1-W3 planned) (in-house scan… | fail | sandbox network: tunnel 403 (run on Mac) |
| LinkedIn get job | LinkedIn (Composio job_search) | success | — |
| LinkedIn get job | LinkedIn (Composio job_search) | success | — |
| LinkedIn get job | LinkedIn (Composio job_search) | success | — |
| LinkedIn get job | LinkedIn (Composio job_search) | success | — |
| LinkedIn get job | LinkedIn (Composio job_search) | success | — |
| LinkedIn get job | LinkedIn (Composio job_search) | success | — |
| Glassdoor | Glassdoor (Composio) | fail | HTTP 400 again on retest with query only (provider problem) |

### Jobs selected

| Job title | Years of exp | Company | Link |
|---|---|---|---|
| AI Engineer, Trust & Evaluation | 1-4 years | Equinix | [link](https://careers.equinix.com/nl/jobs/ai-engineer-trust-evaluation-toronto-ontario-canada) |
| AI Engineer - Applied AI, Data & LLM Systems | 4+ years | 247Labs | [link](https://ca.indeed.com/viewjob?jk=fe42f74376708489) |
| AI Engineer, Innovation | 5+ years | MNP | [link](https://www.linkedin.com/jobs/view/4487681731) |
| AI Developer (LLM & Agentic Systems) | 5+ years / 2+ years | WSP in Canada | [link](https://www.linkedin.com/jobs/view/4472100123) |
| Senior Applied AI Engineer - Artificial Intellige… | 4+ years / 5+ years | Bloomberg | [link](https://www.linkedin.com/jobs/view/4478918069) |

### Resume analysis

**Strengths we have**

- Agent platform work in production: orchestrator-subagent system over MCP, tiered model routing cut token cost 48% (Kinaxis).
- LLM gateway with guardrails: Kong AI Prompt Guard, content-safety filters, token rate limits, custom Lua token metrics.
- Measured results at a startup: generation latency 77% lower (3+ min to 40s), 10x traffic, 2,000+ users, cloud cost 35% lower.
- Evaluation and trust controls in projects: LLM judge on 50 golden Q&A pairs, 30 scored agent scenarios, 0.7 confidence gate.
- Wide production stack: Azure, GCP, AWS, Kubernetes, Terraform, OAuth2/OIDC, CI/CD; matches 9 of 12 common job asks.
- Rare mix that banks and enterprise AI teams ask for: MCP + LLM gateway + guardrails.

**Weaknesses we have**

- About 2 years of experience; 4 of 5 selected jobs ask 4–5+ years. Wording cannot fix this.
- The current Kinaxis role shows 'Internship' after a finished Master's; it reads junior.
- Evaluation work at Kinaxis has no numbers (eval set size, task success, number of users or teams).
- No evaluation statistics, judge-vs-human agreement or red-teaming facts (Equinix asks for them).
- No facts for fine-tuning, data pipelines (ETL), document processing, knowledge graphs or Azure AI Foundry.
- Best RAG and eval proof is in personal projects, and 5 project claims conflict with sage docs (F017–F021): confirm them.

### Lines before (v1) / lines now (v2)

| Section | Before | Now |
|---|---|---|
| Professional Summary | AI Engineer with 2 years building production agentic AI, RAG, and LLM gateway systems on Azure, GCP, and AWS. Startup-trained to own systems from architecture to production; now designs reusable agent platforms built around cost, safety, and team adoption. | AI Engineer, 2 years shipping production agent platforms: multi-agent orchestration over MCP, RAG, LLM gateways with guardrails and eval-driven tuning. Cut token cost 48% at Kinaxis and latency 77% at a startup. |
| Experience | Built an orchestrator-subagent SDLC system turning Jira epics into research, plans, code, and Playwright tests over GitHub, Bitbucket, Atlassian, and Microsoft MCP; tiered model routing cut token cost 48% at task success. | Built an orchestrator-subagent SDLC system that turns Jira epics into research, plans, code and Playwright tests over GitHub, Bitbucket and Atlassian MCP; tiered model routing cut token cost 48% at task success. |
| Experience | Generalized it into a team shared agentic harness and plugin marketplace with custom orchestration, lazy tool loading, declarative sandbox policies, and eval-driven tuning, porting legacy code to a UI/UX-driven web client. | Generalized it into a shared agentic harness and plugin marketplace for the team: custom orchestration, lazy tool loading, declarative sandbox policies, eval-driven tuning and a port of legacy code to a web client. |
| Experience | Built rolling LLM conversation compaction for MAF agents in C#/.NET, replacing 100-message truncation with summarization triggered past 120K tokens, bounding context while retaining history in unbounded sessions. | Built rolling conversation compaction for Microsoft Agent Framework agents in C#/.NET: summarization past 120K tokens replaced 100-message truncation, bounding context while keeping history in unbounded sessions. |
| Experience | Hardened Kong AI Gateway as the control layer for LLM traffic with AI Prompt Guard allow/deny policies, content-safety guardrails, and token-based rate limiting, plus custom Lua plugins for per-user token metrics. | Hardened Kong AI Gateway as the guardrail layer for LLM traffic: AI Prompt Guard allow/deny policies, content-safety filters, token-based rate limits and custom Lua plugins for per-user token metrics. |
| Experience | Debugged a failing GCP Cloud SQL backup pipeline (0/21 exports) across GitHub Actions CI/CD, Kubernetes, ArgoCD, and IAM; added alerting cutting failure detection from 30 min to ~15s, fixed in Terraform. | Debugged a GCP Cloud SQL backup pipeline failing 0/21 exports across GitHub Actions CI/CD, Kubernetes, ArgoCD and IAM, fixed it in Terraform, and added alerting that cut failure detection from 30 min to ~15s. |
| Experience | Built zero-downtime credential rotation for a multi-tenant Kong Konnect gateway with Azure Event Grid, HashiCorp Vault, and OIDC auth using dual-write grace periods, keeping tenant traffic live during rollovers. | Built zero-downtime credential rotation for a multi-tenant Kong Konnect gateway (Azure Event Grid, HashiCorp Vault, OIDC auth) with dual-write grace periods, keeping tenant traffic live during rollovers. |
| Experience | Decommissioned a retired data source from 3 RAG agents on Azure AI Search and GCP Vertex AI, removing ETL loaders and Helm/ArgoCD Kubernetes templates, with regression tests protecting retrieval quality. | Removed a retired data source from 3 RAG agents on Azure AI Search and GCP Vertex AI, removing ETL loaders and Helm/ArgoCD Kubernetes templates, with regression tests protecting retrieval quality. |
| Experience | Owned the end-to-end architecture of Slideoo’s AI document-generation backend with agent orchestration, LLM tool calling, & reasoning on Azure and AWS, scaling to 10x traffic & 2,000+ users while cutting cloud spend 35%. | Owned the end-to-end architecture of Slideoo’s AI document-generation backend with agent orchestration, LLM tool calling and reasoning on Azure and AWS, scaling to 10x traffic and 2,000+ users, cutting cloud spend 35%. |
| Experience | Rebuilt the multimodal LLM pipeline for PowerPoint generation by profiling bottlenecks and re-engineering prompt orchestration, cutting generation latency 77% (3+ min to 40s) & directly lifting subscription growth 43%. | Rebuilt the multimodal LLM pipeline for PowerPoint generation by profiling bottlenecks and reworking prompt orchestration, cutting generation latency 77% (3+ min to 40s) and lifting subscription growth 43%. |
| Experience | Benchmarked competing LLM candidates for production by analyzing evaluation results and datasets across generation, surfacing quality regressions early & driving data-backed prompt-tuning decisions as traffic scaled. | Benchmarked candidate LLMs for production by analyzing evaluation results and datasets across generation, surfacing quality regressions early and driving data-backed prompt-tuning decisions as traffic scaled. |
| Experience | Led a team of interns and partnered with company leadership to shape the AI document-generation product roadmap, driving sprint planning, reviews, & technical mentorship to ship features from prototype to production. | Led a team of interns and partnered with company leadership to shape the AI document-generation product roadmap, driving sprint planning, reviews, and technical mentorship to ship features from prototype to production. |
| Projects | Kept a human in control: read-only agent tools, a revert PR as the only rollback, and code-enforced limits of 20 tool calls, 2 reflexion loops, and a 0.7 confidence gate per incident. | Built trust controls into the agents to keep a human in control: read-only agent tools, a revert PR as the only rollback, and code-enforced limits of 20 tool calls, 2 reflexion loops, and a 0.7 confidence gate per incident. |
| Projects | Secured the FastAPI pod with Entra ID bearer tokens, app roles, workload identity, and Key Vault, so no Kubernetes Secret exists; CI signs in with GitHub OIDC and no client secrets. | Secured the FastAPI pod on AKS with Entra ID bearer tokens, app roles, workload identity, and Key Vault, so no Kubernetes Secret exists; GitHub Actions CI signs in with GitHub OIDC and no client secrets. |
| Projects | Cut idle cost with Terraform, one ARM64 node, and pod scale-to-zero; PRs must pass 2,693 pytest tests, strict pyright, tfsec, and gitleaks, and agent runs are scored on 30 test scenarios. | Cut idle cost with Terraform, one ARM64 AKS node, and pod scale-to-zero; every PR must pass 2,693 pytest tests, strict pyright type checks, tfsec, and gitleaks, and agent runs are scored on 30 test scenarios. |
| Projects | Built a wealth-advisor RAG agent (Anthropic SDK, FastAPI, 4 tools) over pgvector; PostgreSQL row-level security enforces tier and jurisdiction access, with zero-leakage tests for 4 user roles. | Built a wealth-advisor RAG agent (Anthropic SDK, FastAPI, 4 tools) over pgvector; PostgreSQL row-level security enforces tier and jurisdiction access, with zero-leakage tests for each of 4 user roles. |
| Projects | Added two-pass PII redaction (GCP DLP, regex fallback): one pass cleans documents before Voyage AI embedding, one checks each LLM answer, keeping personal data out of retrieval and responses. | Added two-pass PII redaction (GCP DLP, regex fallback): one pass cleans source documents before Voyage AI embedding, one checks each LLM answer, keeping personal data out of both retrieval and responses. |
| Projects | Routed LLM calls through Kong (60 req/min per advisor, request logging) and LiteLLM fallback from Claude to GPT-4o to Gemini, with a circuit breaker that pulls a model for 5 min after 3 failures. | Routed LLM calls through Kong (60 req/min per advisor, request logging) and LiteLLM fallback from Claude to GPT-4o to Gemini, with a circuit breaker that pulls a failing model for 5 min after 3 failures. |
| Hackathons & Events | DevFest, Google Developer Groups Sep 2025: Attended sessions on Gemini, GCP, and agentic AI. | (removed) |
