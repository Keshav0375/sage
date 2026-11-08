---
github: {"owner": "Keshav0375", "status_field": "Status", "project_number": 4, "project_url": "https://github.com/users/Keshav0375/projects/4", "project_id": "PVT_kwHOBTMg2M4Blnby", "linked": true, "issues_repo": "Keshav0375/sentinel-brain", "board_number": 4}
updated: "2026-11-08"
---

# Epics

GitHub project: https://github.com/users/Keshav0375/projects/4 (the Sentinel board, a one-way mirror of the `sentinel-brain` tracker; issues live in `Keshav0375/sentinel-brain`).

The delivery plan (phases, epic order, the build process) is in [plan.md](plan.md).
Each epic folder holds `epic.md` and `tickets/`; the format is in the brain:layout skill.
One epic = one source phase = one branch + one PR. Epics E7, E20 and E21 were built from owner tickets and are not on the board yet.

| Epic | Title | Source phase | Phase | Done | PR | Signed | Issue |
|---|---|---|---|---|---|---|---|
| [E1](E1-infra-1-foundations-and-bootstrap/epic.md) | Foundations and bootstrap | infra 1 | 1 Infra | 3/3 | [Sentinel-infra#1](https://github.com/Keshav0375/Sentinel-infra/pull/1) | 2026-08-15 | https://github.com/Keshav0375/sentinel-brain/issues/2 |
| [E2](E2-infra-2-core-resource-modules/epic.md) | Core resource modules | infra 2 | 1 Infra | 3/3 | [Sentinel-infra#2](https://github.com/Keshav0375/Sentinel-infra/pull/2) | 2026-08-23 | https://github.com/Keshav0375/sentinel-brain/issues/6 |
| [E3](E3-infra-3-compute-and-networking/epic.md) | Compute and networking modules | infra 3 | 1 Infra | 6/6 | [Sentinel-infra#3](https://github.com/Keshav0375/Sentinel-infra/pull/3) | 2026-08-24 | https://github.com/Keshav0375/sentinel-brain/issues/10 |
| [E4](E4-infra-4-cross-repo-wiring-and-ci/epic.md) | Cross-repo wiring and CI | infra 4 | 1 Infra | 4/4 | [Sentinel-infra#4](https://github.com/Keshav0375/Sentinel-infra/pull/4), [Sentinel-infra#5](https://github.com/Keshav0375/Sentinel-infra/pull/5), [Sentinel-infra#6](https://github.com/Keshav0375/Sentinel-infra/pull/6) | 2026-08-24 | https://github.com/Keshav0375/sentinel-brain/issues/17 |
| [E5](E5-infra-5-dynamic-foundations/epic.md) | Dynamic foundations | infra 5 | 1 Infra | 6/6 | [Sentinel-infra#7](https://github.com/Keshav0375/Sentinel-infra/pull/7) | 2026-08-25 | https://github.com/Keshav0375/sentinel-brain/issues/22 |
| [E6](E6-infra-6-dynamic-deployments/epic.md) | Dynamic deployments and workflows | infra 6 | 1 Infra | 8/8 | [Sentinel-infra#8](https://github.com/Keshav0375/Sentinel-infra/pull/8), [Sentinel-infra#9](https://github.com/Keshav0375/Sentinel-infra/pull/9), [Sentinel-infra#10](https://github.com/Keshav0375/Sentinel-infra/pull/10) +5 fix PRs | 2026-09-13 | https://github.com/Keshav0375/sentinel-brain/issues/29 |
| [E7](E7-infra-7-monorepo/epic.md) | Monorepo: Sentinel-infra into Sentinel/infra | infra 7 | 4 Post-release | 2/2 | [Sentinel#32](https://github.com/Keshav0375/Sentinel/pull/32) | 2026-10-25 |  |
| [E8](E8-deployment-1-the-app/epic.md) | The app | deployment 1 | 2 Deployment | 2/2 | [Sentinel-deployment#1](https://github.com/Keshav0375/Sentinel-deployment/pull/1) | 2026-10-04 | https://github.com/Keshav0375/sentinel-brain/issues/39 |
| [E9](E9-deployment-2-deploy-pipeline/epic.md) | Deploy pipeline | deployment 2 | 2 Deployment | 3/3 | [Sentinel-deployment#2](https://github.com/Keshav0375/Sentinel-deployment/pull/2), [Sentinel-deployment#3](https://github.com/Keshav0375/Sentinel-deployment/pull/3) | 2026-10-07 | https://github.com/Keshav0375/sentinel-brain/issues/42 |
| [E10](E10-deployment-3-scenario-branches/epic.md) | Scenario branches | deployment 3 | 2 Deployment | 1/1 | [Sentinel-deployment#4](https://github.com/Keshav0375/Sentinel-deployment/pull/4) | 2026-10-07 | https://github.com/Keshav0375/sentinel-brain/issues/46 |
| [E11](E11-backend-1-data-layer-foundation/epic.md) | Data layer foundation | backend 1 | 3 Backend | 4/4 | [Sentinel#19](https://github.com/Keshav0375/Sentinel/pull/19) | 2026-10-12 | https://github.com/Keshav0375/sentinel-brain/issues/49 |
| [E12](E12-backend-2-memory-and-tracing/epic.md) | Memory and tracing rewrite | backend 2 | 3 Backend | 4/4 | [Sentinel#20](https://github.com/Keshav0375/Sentinel/pull/20) | 2026-10-14 | https://github.com/Keshav0375/sentinel-brain/issues/54 |
| [E13](E13-backend-3-tools-rewrite/epic.md) | Tools rewrite | backend 3 | 3 Backend | 7/7 | [Sentinel#21](https://github.com/Keshav0375/Sentinel/pull/21) | 2026-10-14 | https://github.com/Keshav0375/sentinel-brain/issues/59 |
| [E14](E14-backend-4-agent-pipeline-and-loops/epic.md) | Agent pipeline and loops | backend 4 | 3 Backend | 4/4 | [Sentinel#22](https://github.com/Keshav0375/Sentinel/pull/22) | 2026-10-19 | https://github.com/Keshav0375/sentinel-brain/issues/67 |
| [E15](E15-backend-5-api-and-app/epic.md) | API and app | backend 5 | 3 Backend | 6/6 | [Sentinel#23](https://github.com/Keshav0375/Sentinel/pull/23) | 2026-10-23 | https://github.com/Keshav0375/sentinel-brain/issues/72 |
| [E16](E16-backend-6-eval/epic.md) | Eval | backend 6 | 3 Backend | 2/2 | [Sentinel#24](https://github.com/Keshav0375/Sentinel/pull/24) | 2026-10-24 | https://github.com/Keshav0375/sentinel-brain/issues/79 |
| [E17](E17-backend-7-container-and-k8s/epic.md) | Container and K8s | backend 7 | 3 Backend | 3/3 | [Sentinel#26](https://github.com/Keshav0375/Sentinel/pull/26) | 2026-10-24 | https://github.com/Keshav0375/sentinel-brain/issues/82 |
| [E18](E18-backend-8-cicd-workflows/epic.md) | CI/CD workflows | backend 8 | 3 Backend | 4/4 | [Sentinel#27](https://github.com/Keshav0375/Sentinel/pull/27) | 2026-10-25 | https://github.com/Keshav0375/sentinel-brain/issues/86 |
| [E19](E19-backend-9-cleanup-and-e2e/epic.md) | Cleanup and end-to-end | backend 9 | 3 Backend | 2/2 | [Sentinel#28](https://github.com/Keshav0375/Sentinel/pull/28) | 2026-10-25 | https://github.com/Keshav0375/sentinel-brain/issues/91 |
| [E20](E20-backend-10-ops-dashboard/epic.md) | Ops dashboard | backend 10 | 4 Post-release | 5/5 | [Sentinel#33](https://github.com/Keshav0375/Sentinel/pull/33) | 2026-10-28 |  |
| [E21](E21-backend-11-memory-hardening-and-eval/epic.md) | Memory hardening, in-cluster eval and README | backend 11 | 4 Post-release | 4/4 | [Sentinel#35](https://github.com/Keshav0375/Sentinel/pull/35) | 2026-10-30 |  |

Infra task 6.8 (`E6-T8`, Pause/Resume) is counted done but has never executed; see its ticket.
