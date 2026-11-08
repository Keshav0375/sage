---
key: "E6-T4"
title: "Bronze asset: GCS by sha256, register documents, publish"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T2", "E6-T3", "E1-T5", "E1-T8", "E5-T7", "E5-T9", "E5-T11"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/04-components-and-responsibilities.md#4.10", "deep-dive/05-data-model-and-storage.md#5.2", "decision-logs.md#adr-014"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 158, "id": 6263517995, "url": "https://github.com/Keshav0375/FinAdvisor/issues/158"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Fetch source documents into immutable GCS bronze, register a documents row and publish docs.bronze.v1.

## Description
Arch (4.8 `etl`; 4.10; Flow 2): 'Dagster run of tenant bronze assets (fetch, GCS by sha256, register `documents`, publish `docs.bronze.v1`)'. Bucket `GCS_DATA_BUCKET`, object `bronze/{tenant_id}/{sha256}` holding raw immutable bytes plus source URL and fetch time (object metadata); skip upload if the object exists. Register `documents` (5.2): `title, doc_type, jurisdiction, tier_required, regulatory_ref, last_reviewed_at, product_category, risk_level, source ('synthetic'|'edgar'), source_uri, bronze_uri, bronze_sha256, parser_version NULL, status 'active'`; unique `(tenant_id, bronze_sha256)` so re-registering is a no-op (INSERT ... ON CONFLICT DO NOTHING). No `raw_content` anywhere. Publish `docs.bronze.v1` keyed by tenant_id with the E5 envelope via the E5 idempotent producer; payload carries ids and bronze_uri only, never text. Runs as DB role `fa_etl` with `app.tenant_id` set. Asset is partitioned tenant x dt. Source adapter for synthetic corpus from E6-T3. Out of scope: EDGAR source (E6-T13).

## Acceptance criteria
- [ ] Given a doc already in bronze, when the asset reruns, then no GCS write occurs and no new `documents` row (asserted by counting GCS puts and rows, integration with fake-gcs)
- [ ] Given a new doc, when materialized, then exactly one `docs.bronze.v1` message with key == envelope.tenant_id and no content field is produced (test on payload schema)
- [ ] Given `fa_etl` and tenant A context, when inserting a documents row for tenant B, then RLS denies it (test)
- [ ] `documents` has no column named raw_content/content (reuse E1-T17 assertion passes)
