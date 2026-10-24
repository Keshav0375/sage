---
name: check
description: Run the active project's quality gate (its own commands from project.toml, in the right repo) and report the verdict, tree state and attribution check. Use when asked to check, lint, test or verify.
argument-hint: "[--fast] [project]"
---

# /check

Spawn `gate-runner` with `PROJECT <p>` (and `WORKDIR` if a worktree is in play). Relay its
4 lines verbatim. If RED, add the single most likely cause from the FAILED line, nothing more.
Only `VERDICT GREEN` from a full run is green. PARTIAL means a tool is missing: name it.
