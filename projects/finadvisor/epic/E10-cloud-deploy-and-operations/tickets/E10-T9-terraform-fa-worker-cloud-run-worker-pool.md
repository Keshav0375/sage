---
key: "E10-T9"
title: "Terraform fa-worker Cloud Run worker pool"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T2", "E10-T4", "E10-T7", "E5-T13", "E10-T6"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/04-components-and-responsibilities.md#4.12", "ADR-019", "ADR-020"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Deploy the fa-worker worker pool with its roles, Confluent secrets and ignore_changes on manual_instance_count.

## Description
Implements 4.7 and ADR-019: Cloud Run worker pool `fa-worker`, entrypoint `worker`, `WORKER_ROLES` = outbox-relay,silver,contextualizer,indexer,acl-applier,eval-judge,bq-sink, DB login role `fa_worker`, one Confluent service account and API key per service (KAFKA_BOOTSTRAP, KAFKA_API_KEY, KAFKA_API_SECRET, SCHEMA_REGISTRY_URL, SCHEMA_REGISTRY_API_KEY, SCHEMA_REGISTRY_API_SECRET read from Secret Manager secrets created by E5-T13 for fa-worker), GCS_DATA_BUCKET, BQ_DATASET, BQ_MAX_BYTES_BILLED, VOYAGE_API_KEY, ANTHROPIC_API_KEY or Kong URL, DB_POOL_SIZE. Instance count 0 when the demo is down; worker pool autoscaling is manual. Use the command and resource attributes recorded by E10-T2 (docs/adr/worker-pool-scale-to-zero.md).

Build terraform/worker_pool.tf with Direct VPC egress private-ranges-only, startup probe where supported, manual_instance_count = 0 initially in demo, lifecycle.ignore_changes = [the manual instance count attribute found in E10-T2]. Per-secret accessor grants for fa_worker only.

Out of scope: Confluent resources (E5-T13).

## Acceptance criteria
- [ ] `terraform plan` shows the worker pool with WORKER_ROLES containing exactly the 7 roles and egress PRIVATE_RANGES_ONLY (terraform test)
- [ ] After `gcloud run worker-pools update ... --scaling=2` (command from E10-T2), `terraform plan -detailed-exitcode` returns 0
- [ ] With count 1, a log query shows the worker booted and logs each of the 7 roles started (command and output attached); with a missing required secret the revision fails to start with a config error (negative test)
- [ ] No project-level secretAccessor was added; the worker SA appears only on its own per-secret bindings (check_iam.sh from E10-T4 passes)
