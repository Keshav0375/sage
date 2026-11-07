---
key: "E10-T11"
title: "Terraform SPA bucket and ALB backend bucket wiring"
epic: "E10"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E10-T4", "E2-T4", "E2-T5", "E2-T8", "E2-T18", "E2-T19"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.4", "deep-dive/04-components-and-responsibilities.md#4.12", "ADR-012"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Create the private SPA GCS bucket and attach it to the E2 ALB url map as the /* backend with CDN.

## Description
4.12/ADR-012: '`/*` to a GCS backend bucket (SPA, CDN), `/v1/*` to the gateway'. E2 owns the ALB, url map and Cloud Armor; E10 owns the SPA bucket (4.12 lists GCS buckets spa, data). Check what terraform/edge/ exposes (expected input for a backend bucket); if E2 already declares the backend bucket resource, only add the bucket and reference it.

Build terraform/spa_bucket.tf: bucket `<project>-spa` with uniform bucket-level access, public access prevention not enforced only as needed for the CDN: serve through the backend bucket (google_compute_backend_bucket enable_cdn = true) with no allUsers on the bucket itself (use the load balancer service agent or the documented backend bucket access pattern; if the pattern requires allUsers objectViewer on the SPA bucket, put that into questions rather than adding it). The data bucket (GCS_DATA_BUCKET) is owned by E6/E5 or the MVP cloud_storage.tf; do not duplicate it.
Also add the deploy-pipeline step contract: the SPA is uploaded with `gcloud storage rsync` by E10-T16.

Out of scope: the SPA build (E8).

## Acceptance criteria
- [ ] `terraform plan` shows the backend bucket attached to the url map default service with enable_cdn true (terraform test)
- [ ] `curl -s -o /dev/null -w '%{http_code}' https://<alb-host>/` returns 200 for index.html after a manual upload of a placeholder file; the same object URL directly on storage.googleapis.com returns 403
- [ ] No `allUsers` or `allAuthenticatedUsers` member in `gcloud storage buckets get-iam-policy gs://<project>-spa` (test script), or the exception is documented under questions
