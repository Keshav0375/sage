---
key: "E1-T7"
title: "Migration: ACL, eval, outbox, dedupe and tenant_usage tables"
epic: "E1"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T4"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/05-data-model-and-storage.md#5.1"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 23, "id": 6155596523, "url": "https://github.com/Keshav0375/FinAdvisor/issues/23"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
acl_change_requests, eval_scores, outbox, processed_events and tenant_usage exist with their keys and indexes.

## Description
Add an Alembic revision (0002 or later; baseline 0001 is immutable) as `fa_owner` creating the five tables per deep-dive/05-data-model-and-storage.md §5.2 (the outbox is written in E4 and relayed in E5). All have `tenant_id uuid NOT NULL`, `ENABLE` + `FORCE` RLS at creation.

- `acl_change_requests (tenant_id, id)`: `requested_by` (composite FK `(tenant_id, requested_by)` to advisors), `target_type` CHECK (`document`), `document_id`, `action` CHECK (`update_acl`,`delete`), `new_tier_required`, `new_jurisdiction`, `status` CHECK (`pending`,`applied`,`failed`) default `pending`, `error_code`, `requested_at`, `applied_at`.
- `eval_scores (tenant_id, id)`: `message_id` (logical), `judge_model`, `metric`, `score real`, `rationale`, `created_at`.
- `outbox (tenant_id, id)`: `topic`, `key`, `event_type`, `schema_version`, `payload jsonb`, `created_at`, `published_at`, `attempts int default 0`; `id` is the Kafka `event_id`; partial index on `(tenant_id, created_at) WHERE published_at IS NULL`.
- `processed_events (tenant_id, consumer, event_id)` key, `processed_at`.
- `tenant_usage (tenant_id, day)` key: `day date` (UTC day), `tokens_in bigint NOT NULL default 0`, `tokens_out bigint NOT NULL default 0`; counters for the per-tenant daily token budget (R47), written by chat-api in E4 instead of Valkey. FK `tenant_id` to `tenants(id)`.

Out of scope: policies and grants (E1-T10), writers (E4, E5).

## Acceptance criteria
- [ ] Given `alembic upgrade head`, then `tests/db/test_schema_pipeline.py` passes: the five tables (including `tenant_usage` with columns `tenant_id, day, tokens_in, tokens_out`) exist, each with `relrowsecurity` and `relforcerowsecurity` true.
- [ ] Given `pg_indexes`, then `outbox` has an index whose definition contains `WHERE (published_at IS NULL)` on `(tenant_id, created_at)` (test).
- [ ] Given an `acl_change_requests` row with `action = 'purge'`, or with `status = 'done'`, then each raises a CheckViolation; one whose `(tenant_id, requested_by)` names an advisor of another tenant raises a ForeignKeyViolation.
- [ ] Given two `processed_events` rows with the same `(tenant_id, consumer, event_id)`, then the second raises a UniqueViolation.
