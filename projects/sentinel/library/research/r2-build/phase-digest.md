# r2: Build digest, phase by phase

Research note for sentinel. One line per phase: gate, tests, reviews, what the phase found, what it
carried. Source: `sentinel-brain/reports/*.md` and the phase gate ledger in `implementation/STATE.md`.
Epics: [../../../epic/README.md](../../../epic/README.md).

| Phase | Gate and tests | Found or fixed | Carried |
|---|---|---|---|
| infra 1 | gate PASS (5 ran); `plan` No changes | R5: CI could never have applied (Contributor cannot assign roles) | CI never authenticated yet |
| infra 2 | gate PASS (6 ran); tflint clean; live Entra psql login, KV write/read/purge | ACR Basic would have cost more than free Standard; R6 purge 403 swallowed | |
| infra 3 | gate PASS (8 ran); 14 handler unit tests | Datadog tags shape, dispatch payload 10-property cap, zip redeploy, KV-literal guard; test fixtures had encoded the author's own assumption | |
| infra 4 | first CI run proved OIDC, RBAC and state live | ten review fixes that had never reached disk (PR #5); identity-tenant credential gap | tflint/shellcheck/gitleaks not in infra CI |
| infra 5 | live: deployment workspace plans zero resources | every "gate PASS" came from an unmerged gate branch checked out locally; merge first blocked by the ruleset (workflows described the old contract) | |
| infra 6 | live lifecycle: apply 11 + 31, destroy, verify 11/11 | five defects from run history (PRs #11-#15) incl. the destroy deadlock | 6.8 Pause/Resume never executed |
| infra 7 | backend GREEN, infra GREEN (13 ran); 18 workflow tests | | owner re-binds credentials, sets `INFRA_OIDC_READY` |
| deployment 1 | 4 tests | review fix asserts exact `/health` shape | |
| deployment 2 | gate GREEN; live run green except the missing table | dispatch PAT expiry has no warning; app key unscoped | record stage waits for backend 1.3 |
| deployment 3 | gate GREEN, 248 tests | catalog redesigned for determinism | live smoke deferred |
| backend 1 | 1603 passed, 0 skipped (CI, locked install) | 2 code blockers + 6 warnings fixed; vulnerable deps upgraded | |
| backend 2 | GREEN; 1646 tests | `observe` would ship every argument; capture off by default; provenance labels | self-grading judge default |
| backend 3 | GREEN; 1634 tests | real tool-call counter needed; target-SHA cross-check; untrusted-data preamble | live Datadog check pending scoped keys |
| backend 4 | GREEN; 1925 passed, 1 skipped | vendor trace exporter uploading full spans; safety UNSAFE then SAFE | fake LLM only |
| backend 5 | GREEN (7 ran, 0 skipped) | v2 audience is the GUID | 37 s shutdown vs 30 s grace |
| backend 6 | GREEN (7 ran); boot OK | judge rubric anchored on ground truth; `judge_failed` flag | live eval needs real runs |
| backend 7 | GREEN (7 ran); boot OK | automount off, read-only root, manifest value validation | CI identity ticket gates phase 8 |
| backend 8 | GREEN (7 ran, 0 skipped) | `guard-main-source.yml` script injection; SHA pins everywhere | nothing run live |
| backend 9 | GREEN on full run; boot OK | branch-in-prompt leak of the ground-truth label (safety blocker, fixed) | live demo not run |
| backend 10 | GREEN (12 ran incl. web lanes); e2e 18/18; Lighthouse 0.97 / 1.00 | two code-review rounds | Pages not enabled |
| backend 11 | GREEN (backend and infra) | fail-open backup, server-wide backup role, stale-incident resume, inexact resume caps (all fixed) | not live-verified |
