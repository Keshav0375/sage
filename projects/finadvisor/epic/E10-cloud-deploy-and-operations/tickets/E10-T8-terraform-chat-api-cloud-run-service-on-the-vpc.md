---
key: "E10-T8"
title: "Terraform chat-api Cloud Run service on the VPC"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T4", "E10-T7", "E2-T4", "E2-T5", "E2-T8", "E2-T18", "E2-T19", "E4-T27"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/08-security-and-privacy.md#8.3", "deep-dive/04-components-and-responsibilities.md#4.12", "ADR-019", "ADR-024"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 256, "id": 6263688168, "url": "https://github.com/Keshav0375/FinAdvisor/issues/256"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Deploy chat-api as an internal-ingress Cloud Run service with Direct VPC egress, startup probe and invoker restricted to the Kong SA.

## Description
Implements 4.5, 8.3 and ADR-019: Cloud Run service `chat-api`, ingress internal, `run.invoker` only for the Kong (fa-gateway) service account via X-Serverless-Authorization, timeout 3600, explicit concurrency, one Uvicorn process per container, Direct VPC egress `private-ranges-only` with a startup probe (ADR-024), secrets mounted per service account from Secret Manager, no secret defaults in code (missing config fails boot). Config keys from 6.6: ENV_PROFILE, DB_HOST (PSC endpoint), DB_NAME, DB_USER=fa_app, DB_PASSWORD (secret), DB_POOL_SIZE, DB_STATEMENT_TIMEOUT_MS, IDP_PROJECT_ID, ANTHROPIC_BASE_URL, ANTHROPIC_API_KEY / KONG_EGRESS_KEY, VOYAGE_API_KEY, MODEL_ARMOR_*, LANGFUSE_*, OTEL_*. chat-api has no Kafka client, so no Kafka variables.

Build terraform/chat_api.tf: google_cloud_run_v2_service from the image digest (variable from E10-T4), min_instance_count 0 in demo and >=1 in prod, max_instance_count variable (default per the pool budget in E10-T20), concurrency variable, startup_probe on the health path from E1/E4, vpc_access with network_interfaces and egress PRIVATE_RANGES_ONLY, google_cloud_run_v2_service_iam_member run.invoker only for the gateway SA, no allUsers. lifecycle.ignore_changes on min_instance_count. Also confirm the fa-gateway module from E2 has ignore_changes on min_instance_count and add it there only if missing.

Out of scope: fa-gateway definition (E2).

## Acceptance criteria
- [ ] `terraform plan` has chat-api with ingress INGRESS_TRAFFIC_INTERNAL_ONLY, egress PRIVATE_RANGES_ONLY and a startup_probe block (terraform test asserting the three attributes)
- [ ] `gcloud run services get-iam-policy chat-api` lists exactly one binding: roles/run.invoker for the gateway SA; no allUsers or allAuthenticatedUsers (test script)
- [ ] A request with no ID token from outside the VPC to the chat-api run.app URL returns 403 or 404 (curl in the smoke script, status asserted)
- [ ] After `gcloud run services update chat-api --min-instances=1`, `terraform plan -detailed-exitcode` returns 0
