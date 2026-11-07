---
key: "E2-T16"
title: "CI: kong config parse, deck validation, forbidden-plugin guard"
epic: "E2"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E2-T12", "E0-T14"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.3", "deep-dive/11-tech-stack.md", "decision-logs.md#adr-011"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 54, "id": 6155634955, "url": "https://github.com/Keshav0375/FinAdvisor/issues/54"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Make CI fail on an unparsable or non-compliant kong.yml.

## Description
Overview 4.3 'kong.yml in git, validated in CI with kong config parse, smoke-tested with deck/curl' and deep-dive/11-tech-stack.md CI/CD row (kong config parse, deck; versions pinned at implementation). Add a job to .github/workflows/ci.yml: run kong config parse with kong:3.9.4 on kong/kong.yml (required env set to dummy values), run deck offline validation (pin the deck version), and a guard script that fails if kong.yml contains plugins or paths the arch lists as not used (jwt, http-log, openid-connect, rate-limiting-advanced, any Enterprise ai-* plugin) or any /internal path. The job must be required for the PR to pass.

## Acceptance criteria
- [ ] Given a fixture kong.yml with invalid YAML structure, when the parse step runs in the CI script, then it exits non-zero (tests/gateway/test_ci_negative.sh asserts this).
- [ ] Given a fixture adding an http-log plugin, a jwt plugin or an /internal route, then the guard exits non-zero for each (three named fixtures).
- [ ] Given the real kong/kong.yml, then the job exits 0.
- [ ] Given the workflow file, then the job id appears in the branch-protection required checks list documented in the PR (grep of the workflow for the job name).
