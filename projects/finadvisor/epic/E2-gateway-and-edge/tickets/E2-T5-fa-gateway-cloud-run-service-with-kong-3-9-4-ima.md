---
key: "E2-T5"
title: "fa-gateway Cloud Run service with Kong 3.9.4 image"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T3", "E2-T4"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.1", "deep-dive/04-components-and-responsibilities.md#4.3", "deep-dive/08-security-and-privacy.md#8.3", "decision-logs.md#adr-011", "decision-logs.md#adr-012"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 43, "id": 6155622006, "url": "https://github.com/Keshav0375/FinAdvisor/issues/43"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Build the Kong image and Terraform the fa-gateway service with the required ingress, invoker, egress and health settings.

## Description
Overview 4.1, 4.3, 8.3 and ADR-011 / ADR-012. Quote 4.3: 'Image kong:3.9.4, DB-less, _format_version: "3.0", admin API off, status listener for health. Ingress internal-and-cloud-load-balancing, invoker check disabled. min instances 0 (demo), max 2.' Build kong/Dockerfile FROM kong:3.9.4 pinned by digest (replacing the MVP kong:3.9 image and its LiteLLM/http-log kong.yml); admin listener off (KONG_ADMIN_LISTEN=off), status listener on its own port used as the Cloud Run startup probe, proxy access log off. Terraform (terraform/edge/): google_cloud_run_v2_service fa-gateway with ingress INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER, invoker IAM check disabled on this service only (no allUsers binding), a dedicated service account fa-gateway, Direct VPC egress PRIVATE_RANGES_ONLY on the E2-T4 subnet, min 0 / max 2. The chat-api upstream URL and the Valkey endpoint reach Kong as environment variables (no hard-coded values); the baseline kong.yml here has one route to the upstream stub and is replaced in E2-T12. A spike-environment variable set also deploys the E2-T3 stub as `chat-api` (ingress internal, run.invoker only for the fa-gateway service account). Out of scope: ALB (E2-T8), full routes and plugins.

## Acceptance criteria
- [ ] Given `gcloud run services describe fa-gateway`, then ingress is internal-and-cloud-load-balancing and the invoker check is disabled; a script over every Cloud Run service in the project asserts no IAM binding contains allUsers or allAuthenticatedUsers (script exits non-zero on a planted binding in its self-test).
- [ ] Given a request to the fa-gateway run.app URL from the public internet, then it is refused (HTTP 403 or 404; the status is recorded in the PR).
- [ ] Given the deployed revision, then the Kong status endpoint returns 200 for the startup probe and a TCP connect to the admin port is refused (test in the deploy smoke script).
- [ ] Given `docker run` of the image with KONG_DECLARATIVE_CONFIG, then `kong config parse` of the baseline kong.yml exits 0 and the image tag is kong:3.9.4 by digest (grep test on kong/Dockerfile).
