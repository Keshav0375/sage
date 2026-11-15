# Equinix - AI Engineer, Trust & Evaluation (b7886a49f0543311)
Score 4.6 / strong / confidence medium

## A - Role summary
AI Engineer, Trust & Evaluation. Platform team, Toronto Office (work model not stated beyond office). CAD 102,000-152,000 base. Asks 1-4 years.
- Build evaluation platform features: golden/synthetic datasets, LLM-as-judge, tool-call and grounding checks, human-review calibration.
- Build and test trust controls (agent identity, access, guardrails, data boundaries); red-team and turn findings into regression tests.
- Root-cause agent failures; build e2e, load and latency tooling.

## B - Match
| Requirement | Importance | Evidence | Match |
|---|---|---|---|
| 1-4 yrs AI/ML or SWE | must | F001, F010, F002 | yes |
| Python, testing, backend services | must | F017, F008 | yes |
| Built evals/test systems for LLM apps | must | F021, F012, F017 | yes |
| LLM apps (prompting, retrieval, agents) | must | F002, F009, F018 | yes |
| Evaluation statistics, reviewer agreement | must | none | no |
| SQL and results analysis | must | skills list (SQL, PostgreSQL), F018 | partial |
| Communication | must | F013 | partial |
| Guardrails / trust controls | strong | F005, F015, F019 | yes |
| Red-teaming | strong | none | no |
| OAuth/OIDC, MCP | nice | F008, F016 | yes |
| Observability / OpenTelemetry | nice | skills list, F006 | partial |
| GCP, Kubernetes | nice | F009, F006 | yes |
| Perf/load testing | nice | none | no |

## C - Level and strategy
Fit. 1-4 years vs ~2 years. Use the agentic/platform base; lead with eval gating and guardrails, then the Kinaxis harness.

## D - Comp and demand
Floor of range (102k) clears min base 95k. Posted 2026-11-12, fresh. No applicant count.

## E - Customisation plan
1. Lead with CI eval gate (F021). 2. Agent scenario scoring and limits as quality/trust (F015, F017). 3. Guardrail stack (F005, F019, F018). 4. OAuth2/OIDC/MCP under agent identity (F008, F016). 5. Red-teaming and eval statistics: blocked by facts.

## F - Interview plan
1. Golden dataset + judge calibration design: answer with F021, F012. 2. Eval gate thresholds and variance: F021. 3. Red-teaming an agent: F015, F018 zero-leakage tests (honest gap on formal red-teaming).

## G - Legitimacy
legit. Named company, specific duties, plausible pay band, posted pay transparency.

## H - Application pack (drafts)
Referral search terms: "Equinix AI platform Toronto", "Equinix GenAI evaluation", "Equinix agent trust engineer".
Form answers:
1. Why this role: I build eval gates and guardrails for agents, e.g. an LLM-judge CI gate over 50 golden Q&A pairs (F021) and Kong-based guardrails (F005).
2. Evaluation experience: benchmarked competing LLMs and drove prompt-tuning decisions (F012); scored agent runs on 30 scenarios (F017).
3. Trust/security experience: OAuth2 validation via MCP in CI (F008), workload identity and no-secret pods (F016).
Cover note: I build evaluation and guardrail tooling for production agents, including CI eval gates and gateway-level controls. Equinix's trust and evaluation platform is the exact problem I want to work on full time.
