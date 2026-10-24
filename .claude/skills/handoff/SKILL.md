---
name: handoff
description: Write a resumable session snapshot — where we are, what's done, what's in flight, decisions made, next exact step — so a fresh session (or Keshav tomorrow) continues without re-deriving anything. Trigger /handoff before stopping mid-work.
---

# /handoff

Write `.sage/handoffs/<YYYYMMDD-HHMM>-<slug>.md` (local, gitignored):
```
# <project> · <phase/task> · <date>
DONE      <what's finished, with commit shas>
IN FLIGHT <uncommitted work: files + state>
DECIDED   <decisions made this session + why>
OPEN      <questions for Keshav>
NEXT      <the exact next command or step>
GOTCHAS   <anything that bit us>
```
Also run `/retro` if there were corrections this session. Reply with the path.
A fresh session gets the card from the SessionStart hook. Point it at this file.
