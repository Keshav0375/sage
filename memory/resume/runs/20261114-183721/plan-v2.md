# Change plan v2 (main / Opus) — from gaps.md top 7 + v1 judge reasons

Rules: wording only. Keep every number, title, employer, date exactly. No new claims. Do NOT strengthen F017 (2,693 tests),
F018 (zero-leakage), F019 (two-pass PII), F020 (Kong 60/min), F021 ("gated merges") beyond the v1 wording — keep their meaning as-is.
Use "and", never "\&" in prose. ≤ 2 lines per bullet. ≤ 3 tool names per bullet where possible.

E1 Summary (F001,F002,F010,F011,F021,F005): replace with
   "AI Engineer with 2 years building production agent platforms, RAG and LLM evaluation on Azure, GCP and AWS: multi-agent
    orchestration over MCP, LLM gateways with guardrails, and CI eval gates. Cut LLM token cost 48\% at Kinaxis and generation
    latency 77\% at an AI startup serving 2,000+ users."
E2 Kinaxis intern #1 (F002): "Built an orchestrator-subagent SDLC system that turns Jira epics into research, plans, code and Playwright
    tests through MCP (GitHub, Bitbucket, Atlassian, Microsoft); tiered model routing cut token cost 48\% at equal task success."
E3 Kinaxis intern #2 (F003): "Generalized it into a shared agentic harness and plugin marketplace for the team: custom orchestration,
    lazy tool loading, declarative sandbox policies and eval-driven tuning."  (drop the UI/UX porting clause)
E4 Kinaxis intern #3 (F004): "Built rolling conversation compaction for Microsoft Agent Framework agents in C\#/.NET: summarization past
    120K tokens replaced 100-message truncation, bounding context while keeping history in unbounded sessions."
E5 Kinaxis intern #4 (F005): "Hardened Kong AI Gateway as the guardrail layer for LLM traffic: AI Prompt Guard allow/deny policies,
    content-safety filters, token-based rate limits and custom Lua plugins for per-user token metrics."
E6 Kinaxis co-op: reorder to MCP/OAuth2 (F008) → RAG (F009) → credential rotation (F007) → backup (F006). Rewrite:
    F009 "Removed a retired data source from 3 RAG agents on Azure AI Search and GCP Vertex AI, with regression tests protecting retrieval quality."
    F006 "Fixed a GCP Cloud SQL backup pipeline failing 0/21 exports (IAM root cause, fixed in Terraform) and added alerts that cut failure
          detection from 30 min to $\sim$15s."
    F007 keep meaning, ≤ 3 tools named: "Built zero-downtime credential rotation for a multi-tenant Kong Konnect gateway (Vault, OIDC) with
          dual-write grace periods, keeping tenant traffic live during rollovers."
E7 Slideoo (F010,F011,F012,F013): "\&" → "and" everywhere. F012: "Benchmarked candidate LLMs for production on evaluation datasets,
    surfacing quality regressions early and driving data-backed prompt-tuning decisions as traffic scaled."
E8 Projects: FinAdvisor eval bullet (F021) moves to FinAdvisor bullet 1, same meaning; Sentinel bullet 2 (F015) opens with
    "Built trust controls into the agents:" then the same items and numbers.
E9 Skills: new row first "LLM \& Evaluation" = LLM-as-Judge, RAG, Vector Search (pgvector), Tool Calling, Guardrails, Prompt Engineering,
    Observability (LangFuse). Merge "LLM \& RAG" items into it (Azure OpenAI, Vertex AI, Azure AI Search). Drop Java, Django, MongoDB,
    Snowflake. Keep everything else.
E10 Hackathons: delete the DevFest line (attendance only).
