---
name: versions
description: List resume versions with judge scores, show what changed and why in a version, or diff two versions.
argument-hint: "[list | show N | diff A B | best]"
---

# /gimme-job:versions
- `list` → `version.py list`
- `show N` → print `memory/resume/versions/vN/changes.md` and Card 4 + Card 5 for N (`cards.py changes --version N`, `cards.py judge --version N`)
- `diff A B` → `version.py diff A B`
- `best` → `version.py best`
