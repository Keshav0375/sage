# sentinel: library index

One row per source this port used. Raw downloads live in `files/` (git-ignored; none for this
project). The code repos are linked, never copied. Licence "own" = Keshav's own work.

| id | title | link | type | date read | licence | used in |
|---|---|---|---|---|---|---|
| S1 | sentinel-brain: architecture index and per-repo architecture (backend, deployment, infra, ops dashboard) | `sentinel-brain/architecture/` (private control plane) | architecture | 2026-11-08 | own | arch/architecture.md, all deep-dive files |
| S2 | sentinel-brain: decision log (about 90 entries, 2026-06-30 to 2026-10-28) | `sentinel-brain/architecture/decisions.md` | decisions | 2026-11-08 | own | arch/decision-logs.md, research/r1-planning/* |
| S3 | sentinel-brain: tracker (TODO, STATE, history) and 72 task files | `sentinel-brain/implementation/` | tracker | 2026-11-08 | own | epic/**, state.md, research/r1-planning/revisions-and-reconciliations.md |
| S4 | sentinel-brain: phase reports (infra 1-6, deployment 1-3, backend 1-9) and DEMO runbook | `sentinel-brain/reports/` | reports | 2026-11-08 | own | epic/*/epic.md, research/r2-build/phase-digest.md, deep-dive/15 |
| S5 | sentinel-brain: agents and skills (`/implement-phase`, ground rules, nine agents) and helper scripts | `sentinel-brain/.claude/`, `sentinel-brain/scripts/` | process | 2026-11-08 | own | epic/plan.md |
| S6 | Sentinel (backend, infra since phase 7, dashboard) | https://github.com/Keshav0375/Sentinel | code | 2026-11-08 | own | deep-dive 04-07, 09, 11, 12 |
| S7 | Sentinel-deployment (target app, pipeline, scenario branches) | https://github.com/Keshav0375/Sentinel-deployment | code | 2026-11-08 | own | deep-dive/08 |
| S8 | Sentinel-infra (Terraform, infra phases 1-6; read-only backup) | https://github.com/Keshav0375/Sentinel-infra | code | 2026-11-08 | own | deep-dive/09, 09-1 |
| S9 | Sentinel PR #29: Phase 2 release | https://github.com/Keshav0375/Sentinel/pull/29 | PR | 2026-11-08 | own | epic/plan.md, deep-dive/07 |
| S10 | Sentinel PR #32: infra phase 7, monorepo | https://github.com/Keshav0375/Sentinel/pull/32 | PR | 2026-11-08 | own | epic/E7-infra-7-monorepo |
| S11 | Sentinel PR #33: backend phase 10, ops dashboard | https://github.com/Keshav0375/Sentinel/pull/33 | PR | 2026-11-08 | own | epic/E20-backend-10-ops-dashboard |
| S12 | Sentinel PR #35: backend phase 11, memory hardening, eval, README | https://github.com/Keshav0375/Sentinel/pull/35 | PR | 2026-11-08 | own | epic/E21-backend-11-memory-hardening-and-eval |
| S13 | Sentinel project board (one-way mirror of the tracker) | https://github.com/users/Keshav0375/projects/4 | board | 2026-11-08 | own | epic/README.md, ticket `issue` fields |
| S14 | Ops dashboard (not live until GitHub Pages is enabled) | https://keshav0375.github.io/Sentinel/ | site | 2026-11-08 | own | deep-dive/11, state.md |
| S15 | OpenAI Agents SDK documentation | https://openai.github.io/openai-agents-python/ | docs | cited by S1 | vendor docs | deep-dive/04 |
| S16 | Langfuse documentation (v3 SDK, prompts, scores, datasets) | https://langfuse.com/docs | docs | cited by S2 | vendor docs | deep-dive/11, 12 |
| S17 | Azure AKS workload identity overview | https://learn.microsoft.com/azure/aks/workload-identity-overview | docs | cited by S1 | vendor docs | deep-dive/09-1 |
| S18 | GitHub Actions OpenID Connect | https://docs.github.com/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect | docs | cited by S1 | vendor docs | deep-dive/09-1 |
| S19 | Azure Database for PostgreSQL, Microsoft Entra authentication | https://learn.microsoft.com/azure/postgresql/flexible-server/concepts-azure-ad-authentication | docs | cited by S1 | vendor docs | deep-dive/05, 09 |
| S20 | Datadog Synthetics API tests | https://docs.datadoghq.com/synthetics/api_tests/ | docs | cited by S1 | vendor docs | deep-dive/08 |
| S21 | Terraform azurerm provider | https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs | docs | cited by S1 | vendor docs | deep-dive/09 |

Research notes: [research/r1-planning/revisions-and-reconciliations.md](research/r1-planning/revisions-and-reconciliations.md),
[research/r1-planning/live-findings.md](research/r1-planning/live-findings.md),
[research/r2-build/phase-digest.md](research/r2-build/phase-digest.md). Glossary: [glossary.md](glossary.md).
