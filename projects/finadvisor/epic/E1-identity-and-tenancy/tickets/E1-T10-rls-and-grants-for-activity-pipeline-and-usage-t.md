---
key: "E1-T10"
title: "RLS and grants for activity, pipeline and usage tables"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T3", "E1-T6", "E1-T7", "E1-T9"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.4", "deep-dive/05-data-model-and-storage.md#5.3", "decision-logs.md#adr-002"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 26, "id": 6155600427, "url": "https://github.com/Keshav0375/FinAdvisor/issues/26"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
conversations, messages, turn_events, feedback, escalations, acl_change_requests, eval_scores, outbox, processed_events and answer_cache have their owner-clause policies and grants.

## Description
Add an Alembic revision implementing the "Other tables" part of deep-dive/05-data-model-and-storage.md §5.4 and the matching 5.3 grants.

Policies:
- `conversations`, `messages`, `turn_events`, `feedback`: tenant match AND `advisor_id = current_setting('app.user_id')::uuid` (an advisor sees only their own rows) for `fa_app` (SELECT / INSERT / UPDATE as granted).
- `escalations`: tenant match AND (`advisor_id = app.user_id` OR `app.role = 'compliance_officer'`).
- `acl_change_requests`: SELECT and INSERT `TO fa_app` when the tenant matches and `app.role = 'tenant_admin'`; UPDATE of (`status`, `applied_at`, `error_code`) `TO fa_worker` on the own non-PUBLIC tenant.
- `eval_scores`, `outbox`, `processed_events`: tenant match for the roles that hold grants, no PUBLIC clause; `eval_scores` has no grant to `fa_app`.
- `tenant_usage`: tenant match for `fa_app` (SELECT, INSERT, UPDATE; chat-api writes it) and `fa_eval` pinned to the eval tenant; no PUBLIC clause.
- `answer_cache`: tenant match for `fa_app` and `fa_worker` (worker: DELETE only); `fa_maint` may DELETE expired rows only (`expires_at < now()`); same limit for `fa_maint` on `turn_events`.
- `outbox`: `fa_app` SELECT / INSERT / UPDATE, `fa_worker` SELECT / INSERT / UPDATE, `fa_maint` SELECT (`id`, `published_at`) limited to unpublished rows.
- `messages` owned by `fa_maint`: `fa_maint` has no policy and so no row access.
- `fa_eval`: the `fa_app` policies pinned to the `EVAL_TENANT_ID` literal plus PUBLIC reads where `fa_app` has them.

Grants exactly per deep-dive/05-data-model-and-storage.md §5.3 (fa_app: SELECT / INSERT / UPDATE on `conversations, messages, turn_events, escalations, feedback, answer_cache, outbox`; SELECT / INSERT / UPDATE on `tenant_usage`; SELECT / INSERT on `acl_change_requests`; fa_worker lines for `acl_change_requests`, `eval_scores`, `answer_cache`, `outbox`, `processed_events`). No `GRANT ... ON ALL TABLES`; partitions of `messages` get no grants.

Out of scope: writers of these tables (E4, E5, E6).

## Acceptance criteria
- [ ] Given advisors X and Y of tenant A with conversations, when `fa_app` bound to X selects from `conversations`, `messages`, `turn_events` and `feedback`, then it sees only X's rows (`tests/db/test_rls_activity.py`).
- [ ] Given an `escalations` row of advisor Y, when a principal with `app.role = 'compliance_officer'` in tenant A selects, then it sees it; with `app.role = 'advisor'` and another `user_id` it does not; a compliance officer of tenant B does not.
- [ ] Given `app.role = 'advisor'`, when it inserts into `acl_change_requests`, then it raises a row-level-security violation; with `tenant_admin` it succeeds; `fa_worker` updating `acl_change_requests.document_id` fails with permission denied (column grant).
- [ ] Given an expired and a live row in `answer_cache`, when `fa_maint` runs `DELETE FROM answer_cache`, then only the expired row is deleted; `fa_maint` selecting from `messages` returns no rows (no policy).
- [ ] Given `fa_app`, when it selects from `eval_scores`, then it fails with permission denied; `fa_worker` inserting an `outbox` row with another tenant's `tenant_id` raises a row-level-security violation.
- [ ] Given `tenant_usage` rows for tenants A and B, when `fa_app` bound to A selects, inserts or updates, then it sees and changes only A's rows, and inserting a row with B's `tenant_id` raises a row-level-security violation (`tests/db/test_rls_activity.py`).
