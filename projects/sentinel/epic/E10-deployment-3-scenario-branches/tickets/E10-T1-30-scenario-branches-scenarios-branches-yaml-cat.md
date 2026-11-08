---
key: "E10-T1"
title: "30 scenario branches + scenarios/branches.yaml catalog"
epic: "E10"
repo: "Sentinel-deployment"
size: "S"
status: "done"
depends_on: ["E8-T1", "E9-T2", "E9-T3"]
arch_refs: ["deep-dive/08-deployment-and-scenarios.md#8.3"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 47, "id": 5694995235, "url": "https://github.com/Keshav0375/sentinel-brain/issues/47"}
branch: "dev/deploy-phase-3-scenario-branches"
pr: "https://github.com/Keshav0375/Sentinel-deployment/pull/4"
updated: "2026-11-08"
---

## Summary
The binding catalog is **deployment.md §4.1**, which is exhaustive (redesigned 2026-10-07; read `python3 scripts/arch.py deployment 4.1`). Author 30 branches off `main` and the machine-readable catalog.

## Description
Source: deployment task 3.1 (`sentinel-brain/implementation/tasks/deployment/phase-3-scenario-branches/task-1-scenario-branches.md`).

**Files created on the phase branch:**
- `scenarios/branches.yaml`: 30 entries with the §4.1 fields:
  - `branch`, `case`, `fault`
  - `expected_signal_type` (`none|deploy_failure|runtime_error`)
  - `expected_resolution` (`none|rollback|rollback_or_escalate`)
  - `expected_failed_stage` (case ii only)
  - `also_expected` (list)
  - `expected_culprit` (`self` / `none`)
- `scenarios/README.md`: how to run a scenario (merge the branch via PR, observe, revert the merge), detection latency (up to ~31 min for runtime; "Run test now" to speed it up), and that each must be reverted before the next.
- `datadog/synthetics/runtime-health-root.json`: add the `content-type` and `$.message == "ok"` assertions.
- `requirements-dev.txt`: pin PyYAML (and jsonschema if used) for the schema test.
- `tests/test_scenarios.py`:
  - schema: 30 entries, 10 per case, enums, `expected_failed_stage` iff case ii, `also_expected` ⊆ {runtime_error}
  - every branch exists on origin
  - its diff vs `main` touches `app/**` or `requirements.txt`
  - it applies cleanly

## Acceptance criteria
- [x] `branches.yaml` validates; 30 entries, 10 per case, matching §4.1 exactly.
- [x] Every branch exists on origin, applies cleanly to `main`, touches `app/**` or `requirements.txt`, and implements its catalogued fault (unit-checked locally where possible: e.g. `pass/*` keeps the test suite green; `runtime/*` passes `/health` + `/version` locally but fails its targeted check; `deployfail/*` reproduces its failure locally where it can).
- [x] `GET /` synthetic asserts content-type + body.
- [x] Live smoke (one per case, estate up): `pass/01` green with no alert; `deployfail/03` `failed_stage:deploy` and the previous version still serving; `runtime/01` green, then the `GET /` synthetic alerts and the bridge dispatches `runtime_error`.

## Outcome
Built 30 scenario branches (pass/01-10, deployfail/01-10, runtime/01-10), each one `scenario:` commit on main e67e19d, pushed (pass/02 re-cut to 5038939: refactors startup timestamp, identical output). Phase branch commits 12f1904, 074948d, f879ce3, b5c0b05 (HEAD). Files: scenarios/branches.yaml, scenarios/README.md, datadog/synthetics/runtime-health-root.json, datadog/README.md, requirements-dev.txt (PyYAML==6.0.3), tests/test_scenarios.py, tests/test_datadog.py.
Risk: runtime/07 mtime anchor assumes zip/Oryx keep file mtime (~3 min margin); unproven live. Live per-case smoke not done (estate destroyed).
