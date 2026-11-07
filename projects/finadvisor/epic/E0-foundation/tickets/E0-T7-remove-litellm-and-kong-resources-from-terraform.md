---
key: "E0-T7"
title: "Remove LiteLLM and Kong resources from Terraform"
epic: "E0"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E0-T6"]
arch_refs: ["deep-dive/01-context-and-goals.md#1", "decision-logs.md#adr-005", "deep-dive/04-components-and-responsibilities.md#4"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 8, "id": 6155572702, "url": "https://github.com/Keshav0375/FinAdvisor/issues/8"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
The Terraform files no longer define LiteLLM or the MVP Kong service and validate cleanly.

## Description
Why: plan.md E0 done-when: "the repo contains no LiteLLM service, config or dependency". `terraform/cloud_run.tf` defines `google_cloud_run_v2_service.litellm` (line ~162) and a Kong service that fronts it, `secrets.tf` holds `litellm_master_key`, `variables.tf` has `litellm_image` and `kong_image`, `outputs.tf` exports `litellm_url` and `kong_url`, and the backend service sets `KONG_URL`. The target Terraform (Kong `fa-gateway`, worker pool, jobs) is rebuilt in E2 and E10.

Do in `terraform/`:
- Delete the litellm service, the MVP Kong service (its image is built from the `kong/` directory deleted in E0-T6), the `litellm_master_key` secret and any IAM bindings for them, the OpenAI and Google API key secrets if present, and the variables and outputs that referenced them.
- Backend service env: remove `KONG_URL`; add `ANTHROPIC_BASE_URL` (variable, default `https://api.anthropic.com`).
- Do not add new infrastructure; do not change anything unrelated.

Out of scope: any target-state Terraform (E2, E10).

## Acceptance criteria
- [ ] `cd terraform && terraform fmt -check -recursive` exits 0.
- [ ] `cd terraform && terraform init -backend=false && terraform validate` exits 0.
- [ ] `grep -rniE "litellm|KONG_URL|kong_image|openai|gemini" terraform` returns no match.
- [ ] The backend Cloud Run service definition contains an `ANTHROPIC_BASE_URL` env entry (checked by grep in the PR).
