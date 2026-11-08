---
key: "E10-T15"
title: "Add deploy workflow: migrate, tagged revision, smoke test, shift"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T8", "E10-T9", "E10-T10", "E10-T14", "E0-T14"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.12", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.1", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.3", "ADR-021"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 236, "id": 6263648763, "url": "https://github.com/Keshav0375/FinAdvisor/issues/236"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Deploy images by digest with the migrate job first, a tagged no-traffic revision, a smoke test and a traffic shift.

## Description
ADR-021 deploy order: 'migrate Cloud Run job before traffic, then a tagged no-traffic revision, smoke test, then traffic shift', images by digest only; 7.1: Migration failure -> 'deploy halts before traffic shift'; Bad deploy -> 'smoke test on tagged no-traffic revision: traffic not shifted'; 7.3: 'rollback is a traffic shift to the previous revision'. Boundary: E0 builds PR CI; this is the CD workflow.

Build .github/workflows/deploy.yml (WIF via E10-T14, environment gated), triggered on main after CI: (1) build and push the image to Artifact Registry and capture the digest; (2) update job `migrate` to the digest and `gcloud run jobs execute migrate --wait`; stop on non-zero; (3) update the other jobs and worker pool to the digest; (4) deploy chat-api and fa-gateway with `--no-traffic --tag=cand-<sha>` using digest references; (5) run scripts/smoke_test.py against the tagged revision URL from inside the VPC via a Cloud Run job execution (the services are internal; do not hit them from the runner), checking /readyz and one authenticated SSE-free read endpoint defined in E4; (6) on pass `gcloud run services update-traffic --to-tags cand-<sha>=100`; on fail leave traffic unchanged and exit 1; (7) sync the SPA build to the SPA bucket. Also add `make rollback SERVICE=<name>` that shifts traffic to the previous revision. If Cloud SQL is stopped (demo down) the workflow must refuse to run migrate and exit with a clear message rather than start the instance.

Out of scope: demo-up/down.

## Acceptance criteria
- [ ] Workflow test with a failing migrate (bad migration in a test branch against a throwaway DB or a stubbed `gcloud run jobs execute` exiting 1) ends with no `update-traffic` call (assert in a bats/pytest wrapper around the deploy script)
- [ ] Smoke test failure on the tagged revision leaves 100% traffic on the previous revision: `gcloud run services describe chat-api --format='value(status.traffic)'` unchanged (verified in a staged run, output attached)
- [ ] The workflow rejects an image reference that is a tag instead of a sha256 digest (unit test of the script)
- [ ] `make rollback SERVICE=chat-api` moves 100% traffic to the previous revision; asserted by describe output
- [ ] With Cloud SQL in activation policy NEVER the workflow exits non-zero before running migrate with a message containing 'demo is down'
