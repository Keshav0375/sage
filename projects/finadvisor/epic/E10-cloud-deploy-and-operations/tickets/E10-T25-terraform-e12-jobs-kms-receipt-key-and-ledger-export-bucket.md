---
key: "E10-T25"
title: "Terraform the E12 jobs, the receipt KMS key and the ledger export bucket"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T4", "E10-T6", "E10-T10"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/04-components-and-responsibilities.md#4.12", "deep-dive/06-interfaces-and-contracts.md#6.9", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.2", "decision-logs.md#adr-030", "decision-logs.md#adr-029", "decision-logs.md#adr-039"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 247, "id": 6263665026, "url": "https://github.com/Keshav0375/FinAdvisor/issues/247"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Define the Cloud Run jobs of the data-lifecycle epic with per-job service accounts, the per-cell KMS HMAC key that signs receipts, and the append-only ledger export bucket.

## Description
Implements, for E12, the Terraform of 4.12 ("Terraform ... owns every resource in this view"), the E12 rows of the 4.8 job table and ADR-030 ("A Cloud KMS key signs the erasure receipts (HMAC)", 4.12 Secret Manager line; "KMS keyrings sign receipts and hold the tenant keys of their cell", 7.2). Same pattern as E10-T10: one image, `jobs` entrypoint, Direct VPC egress private-ranges-only, one service account per job from E10-T4's pattern, only the secrets each job needs.

Jobs (new, by `for_each` over a local map in terraform/jobs_lifecycle.tf), DB role from 4.8:
- `erasure` (the pass of the `erasure-worker` code over every tenant, run by `demo-up`, E10-T18) `fa_worker`;
- `erasure-verify` `fa_worker`; `erasure-canary` `fa_worker` (canary tenant rows); `embed-backfill` `fa_worker`;
- `reconcile` `fa_worker` per tenant and `fa_etl_public` for PUBLIC (one job, role by argument); `purge-source` `fa_etl_public`;
- `ledger-export` (E12-T20; role `fa_worker`, triggered daily by Cloud Scheduler, E10-T12) and `erasure-replay` (E12-T20; role `fa_worker`, manual: run after any restore, no schedule).
`move-tenant` is not here (its role is set in E13). Grants per SA, least privilege: the erasure, erasure-verify and canary jobs get `roles/cloudkms.signerVerifier` on the receipt key only (E12-T16, E12-T17), secretAccessor on the individual secrets they use (DB password of `fa_worker`, the ledger-hash salt, Langfuse keys) and never project-level secretAccessor (E10-T4 check), the BigQuery roles needed for the tenant dataset DML of E12-T13, and object admin on the data bucket for the GCS step (E12-T12). `embed-backfill` also gets the Voyage key. Kafka (R4-D20 Q6): `erasure-verify` reads topics for its probe with a dedicated read-only Confluent key held in Secret Manager as `KAFKA_VERIFY_API_KEY` and `KAFKA_VERIFY_API_SECRET` (created in the Confluent module of E5-T13's pattern, read ACL on the subject-bearing topics only, no write); only the `erasure-verify` SA gets secretAccessor on them.

KMS: a `google_kms_key_ring` per cell (variable `cell_id`; one cell is deployed, ADR-031) and a `google_kms_crypto_key` with purpose `MAC` and `version_template.algorithm = "HMAC_SHA256"`; output the key id, passed to the jobs as env `KMS_RECEIPT_KEY_ID` (R4-D20 Q6; E12-T16 reads it).

Ledger export bucket (E12-T20: "a new GCS object per day under an append-only bucket policy (object versioning off, writes only, no overwrite)"): `google_storage_bucket` in the cell's location, uniform bucket-level access, versioning off, no retention lock; IAM: the `ledger-export` SA gets `roles/storage.objectCreator` only (create, no delete and so no overwrite), the `erasure-replay` SA gets `roles/storage.objectViewer`, nobody else; env `LEDGER_EXPORT_BUCKET` (R4-D20 Q6; E12-T20 reads it).

Out of scope: Scheduler triggers (E10-T12), alert policies (E9-T20), the job code (E12), the data bucket and BigQuery settings (E10-T26).

## Acceptance criteria
- [ ] `terraform plan` lists exactly these `google_cloud_run_v2_job` names beyond E10-T10's nine: erasure, erasure-verify, erasure-canary, embed-backfill, reconcile, purge-source, ledger-export, erasure-replay (terraform test counts and names).
- [ ] A plan-JSON test asserts the DB_USER per job against the list above (for example purge-source -> fa_etl_public, erasure -> fa_worker) and that no job SA holds `roles/owner`, `roles/editor` or a project-level secretAccessor binding.
- [ ] A plan-JSON test asserts `KAFKA_VERIFY_API_KEY` is readable only by the erasure-verify SA and that the Confluent key has read ACLs and no write ACL (`test_lifecycle_tf.py::test_verify_key_read_only`).
- [ ] A plan-JSON test asserts the KMS key purpose is MAC with HMAC_SHA256 and that `roles/cloudkms.signerVerifier` is bound only to the erasure, erasure-verify and erasure-canary SAs on that key.
- [ ] A plan-JSON test asserts the ledger export bucket has versioning false and no retention policy, that the only member with write access is the ledger-export SA through `roles/storage.objectCreator`, and that no binding grants `storage.objects.delete` on it (fails if `roles/storage.objectAdmin` appears).
- [ ] After apply, `gcloud kms keys describe` shows purpose MAC and the receipt sign-and-verify smoke (a one-line `jobs` command run by the erasure SA) returns a verifiable HMAC; output attached.
