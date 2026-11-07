---
key: "E10-T28"
title: "Add the cloud restore drill with erasure-replay before traffic"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T6", "E10-T18", "E10-T25", "E12-T20", "E12-T21"]
arch_refs: ["deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.2", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.14", "decision-logs.md#adr-029", "decision-logs.md#adr-030"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
A script restores Cloud SQL to a point before a canary erasure into a scratch instance, runs erasure-replay, proves the erased data is gone, and deletes the scratch instance.

## Description
Implements edge case #14 (7.4: "Restore resurrects erased data | ledger replay before traffic | restore a backup taken before an erasure into scratch, replay: counts 0 | nightly (compose); weekly or demo start (cloud drill)") and the E10 line "a restore drill restores a backup taken before an erasure into scratch and runs `erasure-replay` before traffic (#14; N on compose, W in cloud)". The compose nightly part and `erasure-replay` itself are E12-T20; this ticket is the cloud drill.

Build scripts/restore_drill.py and `make restore-drill`:
1. Read the time of the latest canary erasure from the `canary_runs` object (E12-T21) and clone the production-profile instance with point-in-time recovery to a moment just before it into a scratch instance (`gcloud sql instances clone --point-in-time`; PITR is on, E10-T6; scratch name from a variable; same PSC and no public IP, the E10-T20 invariants apply to it).
2. Probe the scratch instance: the canary's rows are present (proves the drill is not vacuous; the script fails if they are absent).
3. Run the `erasure-replay` job (E12-T20) against the scratch instance with the exported ledger from the export bucket (E10-T25).
4. Assert counts 0 for every tombstone in the ledger (the same probe as `erasure-replay`'s exit code) and that readiness refuses traffic until replay exits zero (the `restore_replay_required` flag, E12-T20).
5. Always delete the scratch instance, also on failure (a `finally`), and write the result JSON (steps, counts, durations) to a GCS object.
It is run weekly by hand or with `demo-up --restore-drill` (off by default; arch says "weekly or demo start", see the report's questions); no Scheduler trigger is created. The scratch instance is billed while it exists, so the script logs its lifetime. No on-demand backup is created or kept (5.14).

Out of scope: the replay code (E12-T20), the compose variant (E12-T20), restoring production.

## Acceptance criteria
- [ ] Unit test with fake clients: the call order is clone (PITR before the canary time), probe present, replay, assert zero, delete scratch; an out-of-order call fails the test (`test_restore_drill.py::test_order`).
- [ ] Unit test: when the replay fake exits non-zero, the script exits non-zero and the delete-scratch call still happens (`test_restore_drill.py::test_scratch_deleted_on_failure`).
- [ ] Unit test: when the canary rows are absent in the scratch probe, the script exits non-zero with `drill vacuous`.
- [ ] Given a scratch instance created with a public IP in a fixture, the invariants check (E10-T20) fails the drill before step 3.
- [ ] On the real project `make restore-drill` ends with the scratch instance absent (`gcloud sql instances list` does not show it), result JSON written, counts 0; output attached.
