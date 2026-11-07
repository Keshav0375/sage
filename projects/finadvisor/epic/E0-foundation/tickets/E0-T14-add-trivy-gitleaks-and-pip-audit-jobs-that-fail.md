---
key: "E0-T14"
title: "Add trivy, gitleaks and pip-audit jobs that fail the PR"
epic: "E0"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T2", "E0-T10", "E0-T13"]
arch_refs: ["deep-dive/01-context-and-goals.md#1", "decision-logs.md#adr-021", "deep-dive/11-tech-stack.md#cicd"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 15, "id": 6155586365, "url": "https://github.com/Keshav0375/FinAdvisor/issues/15"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Every PR is scanned for vulnerable dependencies, leaked secrets and image vulnerabilities, and findings fail the job.

## Description
Why: G-05 / plan.md E0: CI runs "trivy, gitleaks, pip-audit" and "each ... runs and can fail a PR". ADR-021: security: trivy, gitleaks, pip-audit.

Add to `.github/workflows/ci.yml` (or a `security.yml` called from it; tool and action versions pinned, actions by SHA):
- `pip-audit`: export the locked main and dev dependencies from `backend/poetry.lock` (`poetry export --with dev --without-hashes`, or the supported equivalent) and run `pip-audit -r <file> --strict`; non-zero on any known vulnerability.
- `gitleaks`: scan the full git history of the PR (`fetch-depth: 0`) with a repo `.gitleaks.toml` that extends the default rules; the only allowlist entries are `.env.example` placeholders and test fixtures with a written reason each.
- `trivy`: `fs` scan of the repo (lockfiles, Dockerfiles, IaC misconfig) and an `image` scan of the `runtime` backend image from E0-T2 and the frontend dev image, `--severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed`, with `.trivyignore` entries allowed only with a comment and expiry date.
- If the first run reports existing findings, fix them by upgrading the locked dependency or base image; do not blanket-ignore. Record any unavoidable exception in `.trivyignore` / pip-audit `--ignore-vuln` with an expiry.
- Extend `docs/ci.md` with these jobs and their negative controls.

Out of scope: SBOM, image signing, Model Armor, `terraform` scanning of the target state (E10).

## Acceptance criteria
- [ ] Given a clean PR branch, the `pip-audit`, `gitleaks` and `trivy` jobs all pass on GitHub.
- [ ] Negative control (recorded run links in `docs/ci.md`): adding a fake high-entropy cloud key such as `AKIAIOSFODNN7EXAMPLE` with a matching secret pattern to a tracked file turns `gitleaks` red.
- [ ] Negative control: pinning a package with a known CVE in `backend/poetry.lock` (for example an old `urllib3` or `jinja2` version) turns `pip-audit` red.
- [ ] Negative control: a Dockerfile base image with a known HIGH/CRITICAL OS vulnerability (an old `python:3.8` image) turns `trivy` red.
- [ ] `gitleaks detect --source . --config .gitleaks.toml` run locally on the merged branch exits 0, and `.trivyignore` and the gitleaks allowlist contain only entries with a reason (checked in review).
