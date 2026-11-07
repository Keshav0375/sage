---
key: "E1-T12"
title: "Maintenance job: messages partitions and expired-row purge"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T6", "E1-T10"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/05-data-model-and-storage.md#5.3", "deep-dive/05-data-model-and-storage.md#5.5"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 28, "id": 6155603114, "url": "https://github.com/Keshav0375/FinAdvisor/issues/28"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
The maintenance job, running as fa_maint, creates messages partitions 3 months ahead, drops partitions past retention, and purges expired answer_cache and turn_events rows.

## Description
Add the `maintenance` entrypoint to the `jobs` image (deep-dive/04-components-and-responsibilities.md §4.8): role `fa_maint`; "Purges expired `answer_cache` and `turn_events` rows; creates `messages` partitions 3 months ahead and drops those past retention". Scheduling is E10; `demo-up` triggering is E10; this ticket makes the job runnable (`python -m src.cli maintenance`) and tested.

Behaviour:
1. `create_messages_partitions(conn, 3)` (E1-T6), idempotent.
2. Drop `messages` partitions whose whole range is older than the retention window. Retention is the config key `MESSAGES_RETENTION_MONTHS` (default 6), added to Settings. Never drop the DEFAULT partition.
3. `DELETE FROM answer_cache WHERE expires_at < now()` and `DELETE FROM turn_events WHERE expires_at < now()` (policy limits `fa_maint` to expired rows).
4. Log counts (structured, no row content). Exit non-zero if the DEFAULT partition of `messages` is non-empty after the run ("alert if non-empty").
Connects with `DB_USER=fa_maint` via Settings.

Out of scope: Cloud Scheduler, `demo-ttl` (E10), alert wiring (E9).

## Acceptance criteria
- [ ] Given the current month plus 3 months of partitions already exist, when `maintenance` runs, then no partition is created and exit code is 0; given the newest partition is only 1 month ahead, when it runs, then partitions up to current month + 3 exist afterwards (`tests/jobs/test_maintenance.py`).
- [ ] Given `MESSAGES_RETENTION_MONTHS=6` (the default) and a partition whose range ends more than 6 months ago, when `maintenance` runs, then that partition is dropped, a partition within 6 months is kept, and the DEFAULT partition is untouched.
- [ ] Given one expired and one live `turn_events` row and one expired and one live `answer_cache` row, when `maintenance` runs, then only the expired rows are removed.
- [ ] Given a row in the `messages` DEFAULT partition, when `maintenance` runs, then it exits non-zero.
- [ ] Given the job's DB connection, then `current_user = 'fa_maint'` and an attempt to `SELECT` from `chunks` fails with permission denied.
