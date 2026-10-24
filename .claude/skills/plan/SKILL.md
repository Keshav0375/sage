---
name: plan
description: Cut the architecture into phases and PR-sized tasks with explicit deps, written into phases/TODO.md + task files, so /build can run them as parallel waves. Trigger /plan [phase number to (re)plan].
argument-hint: "[phase number]"
disable-model-invocation: true
---

# /plan

1. `sagectl arch --list` + `sagectl where --all`. What's built, what's next.
2. A **phase** = one branch + one PR + one sign-off, delivering something you can see working.
   A **task** = one commit, ≤ ~400 changed lines, one owner file-set.
3. Deps are **explicit** (`· deps 2.1, 2.3`). Two tasks in one phase that will touch the same
   file must depend on each other, or they'll land in the same wave and collide.
4. Append to `projects/<p>/phases/TODO.md` in the tracker format (header comment shows it), and
   write `phases/phase-<N>/task-<N.K>-<slug>.md` from `_templates/task.md` (spec, acceptance
   criteria that can fail, out of scope).
5. `python3 bin/sagectl where --phase <N>` and check the WAVES line looks right (no CYCLE).
6. Show Keshav the phase list + waves. He approves before `/build`.
