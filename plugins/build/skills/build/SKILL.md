---
name: build
description: Execute planned tasks wave by wave — builders in parallel worktrees, then independent verification and review — and declare results only with verifier evidence. Trigger /build:build [plan paths].
argument-hint: "[plan paths]"
---

# /build:build

Run this from the project's code repo, so builder worktrees branch from that repo.

1. **Load** the plans (from the arguments or `brain/.runtime/plans/<project>/`). Group them in
   waves: tasks in a wave share no files.
2. **Build (one message per wave).** Spawn one `build:builder` per task in the wave, each with
   its plan path. Each runs in its own worktree.
3. **Handle gaps.** A `GAP` goes back to a `build:planner` with the question; then rebuild.
   Never fill the gap in the main session.
4. **Verify (one message).** For each `DONE`, spawn `build:verifier` and `build:reviewer`, plus
   `build:safety-reviewer` when the diff touches auth, IO, secrets, infra or agent code.
5. **Fix loop.** Findings go to a planner as a fix batch, then a builder, then verify again.
   Stop after three loops and report to Keshav.
6. **Declare** per task: verifier verdict, review findings, what did not run. Merges to protected
   branches are Keshav's call.
