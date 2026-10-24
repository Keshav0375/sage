---
name: retro
description: End-of-session / end-of-phase retrospective — capture mistakes and corrections from this session as structured lessons, graduate repeat lessons into hard rules or hooks, and turn the important ones into eval tasks. Run it at the end of every real working session. Trigger /retro.
---

# /retro (the MISTAKES.md loop, made structured)

1. **Harvest this session:** every correction Keshav made, every tool failure that cost time,
   every gate RED, every review 🚨. Also `python3 bin/sagectl mine --days 1`.
2. **Log each as a lesson** (skip duplicates of open lessons, and bump those instead by noting
   recurrence in a new entry's `what`):
   `python3 bin/sagectl lesson add -p <p> --what "<what happened>" --root-cause "<why, the
   mechanism>" --rule "<the rule that prevents it>" --tags <area> <tech> --severity <…> --source retro`.
   Cross-project mistakes go to the project they happened in. Mining sees all projects.
3. **Graduate:** any lesson whose mechanism has appeared **3+ times** → propose the cheapest
   enforcing surface. A hook or gate step (deterministic) beats a CLAUDE.md line, which beats
   nothing. Show Keshav the proposed line/hook. On yes, add it, then
   `sagectl lesson status --id <L> --to graduated`.
4. **Evals:** for each critical/major lesson that's reproducible, create a task:
   `python3 bin/sagectl eval new -p <p> --id <slug> --prompt "…" --verify "…" --cluster <tag>`.
   The split is assigned by hash. Fill the fixture if it landed in heldin.
5. Commit lesson/eval files to sage (`docs: retro <date>`). Reply in ≤ 6 lines.
