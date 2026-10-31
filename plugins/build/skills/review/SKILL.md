---
name: review
description: Review uncommitted or last-commit changes in the active project's repo for correctness and security, with independent reviewers in parallel. Trigger /build:review [ref].
argument-hint: "[git ref]"
---

# /build:review

1. Collect the diff: uncommitted changes, or `git diff <ref>` when given a ref.
2. In one message, spawn `build:reviewer`, and `build:safety-reviewer` when the diff touches
   auth, IO, secrets, infra or agent code.
3. Merge the findings, drop duplicates, keep the most severe first. Report in the finding format:
   verdict on line 1, then `<🚨|⚠️> <file:line>  <defect>`.
