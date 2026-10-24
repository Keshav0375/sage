---
name: spec
description: Write or extend a project's binding architecture (arch/*.md, numbered sections) and ADRs, via an interview plus research on the hard choices. Trigger /spec [area].
argument-hint: "[area to spec, e.g. 'auth' — default: whole system]"
disable-model-invocation: true
---

# /spec

1. Read `projects/<p>/arch/` TOC (`sagectl arch --list`) and `STATE.md`. Know what exists.
2. **Grill first** (see /grill): purpose, users, scale (numbers: RPS, data size, latency, budget),
   hard constraints, non-goals. One batch of questions, max 7. Keshav answers, then you write.
3. For each real choice (datastore, queue, auth, hosting…) where the right answer isn't
   obvious: run `/research` on it (or `/council` if it's expensive to reverse).
4. `architect` mode=draft writes numbered sections + one ADR per choice in `decisions.md`.
5. Show Keshav the TOC and the ADR list. Anything he hasn't decided goes into `STATE.md` →
   "Open decisions", and agents halt on those.
6. Then `/plan` to cut it into phases.
