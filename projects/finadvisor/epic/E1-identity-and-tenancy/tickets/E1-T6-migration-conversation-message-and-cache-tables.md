---
key: "E1-T6"
title: "Migration: conversation, message and cache tables"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T4"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.5", "deep-dive/05-data-model-and-storage.md#5.3"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 22, "id": 6155595219, "url": "https://github.com/Keshav0375/FinAdvisor/issues/22"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
conversations, messages (monthly partitions, owned by fa_maint), turn_events, escalations, feedback and answer_cache exist in the target shape.

## Description
Add an Alembic revision (0002 or later; baseline 0001 is immutable) as `fa_owner` creating the user-activity tables per deep-dive/05-data-model-and-storage.md §5.2 and 5.5. All have `tenant_id uuid NOT NULL`, `ENABLE` + `FORCE` RLS at creation, and composite FKs starting with `tenant_id`.

- `conversations (tenant_id, id)`: `advisor_id` (composite FK to advisors), `title`, `created_at`, `updated_at`, `deleted_at`; index `(tenant_id, advisor_id, updated_at DESC)`.
- `messages (tenant_id, id, created_at)` `PARTITION BY RANGE (created_at)` monthly: `conversation_id` (composite FK), `advisor_id` (composite FK; used by the owner clause), `turn_id`, `role` CHECK (user, assistant), `content`, `status` CHECK (pending, streaming, complete, refused, failed), `model`, `prompt_version`, `citations jsonb`, `retrieval_chunk_ids uuid[]`, `retrieval_degraded boolean`, `usage jsonb`, `refusal_code`; local index `(tenant_id, conversation_id, created_at)`. A DEFAULT partition catches misses. The parent is owned by `fa_maint` ("Postgres requires ownership of the parent for partition DDL"); create the initial partitions (current month and 3 months ahead) in the migration and `ALTER ... OWNER TO fa_maint` on the parent and those partitions. Put the partition-creation SQL in a reusable function `src/db/partitions.create_messages_partitions(conn, months_ahead)` that E1-T12 reuses. No grants on partitions.
- `turn_events (tenant_id, turn_id, seq)`: `request_hash` (text, hash of the request body, used by E4 for idempotency-key reuse detection), `advisor_id`, `event`, `data jsonb`, `created_at`, `expires_at`; no FK.
- `escalations (tenant_id, id)`: `advisor_id` (composite FK), `reason`, `product_class`, `licenses`, `status`, `message_id`, `created_at`.
- `feedback (tenant_id, id)`: `message_id` (logical, no FK because the partitioned PK includes `created_at`), `advisor_id`, `score CHECK in (-1, 1)`, `comment`, `created_at`.
- `answer_cache (tenant_id, cache_key)`: UNLOGGED; `answer, citations jsonb, source_document_ids uuid[], created_at, expires_at`; index `(expires_at)` and GIN on `source_document_ids`.

This revision creates every remaining deep-dive/05-data-model-and-storage.md §5.2 table in full (including `answer_cache`, `turn_events`, `escalations`); later epics add only indexes/classes, not these tables.

Out of scope: policies and grants (E1-T10), the maintenance job (E1-T12), writing to these tables from `agent` (E4).

## Acceptance criteria
- [ ] Given `alembic upgrade head`, then `tests/db/test_schema_activity.py` passes: `answer_cache.relpersistence = 'u'`; `messages` is `relkind='p'`, `partstrat='r'`, owned by `fa_maint`, with partitions for the current month and the next 3 months plus a DEFAULT partition.
- [ ] Given a conversation insert whose `(tenant_id, advisor_id)` references an advisor of another tenant, then it raises a ForeignKeyViolation (test).
- [ ] Given `pg_constraint`, then `turn_events` has a `request_hash` column, `feedback` has no foreign key to `messages`, and every foreign key in the activity tables lists `tenant_id` as its first column (test iterating `pg_constraint`).
- [ ] Given `create_messages_partitions(conn, 3)` is called twice, then the second call creates nothing and does not raise (idempotent), and no partition of `messages` has a grant to a runtime role.
