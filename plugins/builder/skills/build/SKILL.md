---
name: build
description: The builder's main loop for one epic of a project — takes the tickets from tracker.json and the GitHub Project, treats the project's arch docs as the source of truth, and drives fetcher, brancher, editor, code-reviewer, runner, warden and verifier subagents ticket by ticket until each is verified, then opens PRs. Trigger /builder:build <project> <epic>.
argument-hint: "<project> <epic key, e.g. E1>"
---

# /builder:build

You are the main loop (Opus). Load `brain:pipeline` and `brain:tracker`. You orchestrate and
decide; subagents (Sonnet) do every task. You never edit project code, run the tests or write
reports yourself. Per-ticket files live in `context/.runtime/builder/<p>/<ticket>/`.

## 0. Orient
- `mcp__brain__where <project>`: repos, GitHub project, epic progress.
- Read `tracker.json`. Pick the epic. Its tickets with status `todo` whose `depends_on` are all
  `done` are **ready**. Tickets `in_progress` or `review` resume where they stopped.
- Halt on an open decision in `STATE.md` that the epic depends on.
- Ask Keshav once: "Push branches and open PRs for <epic> when verified?" His answer covers
  this epic in this session.

## 1. Fetch (one message, one fetcher per ready ticket, at most 3 at a time)
`builder:fetcher` per ticket. Read each reply. `HALT` → resolve with Keshav or mark the ticket
`blocked` with the reason. Skip to the next wave.

## 2. Branch (one message)
`builder:brancher mode=start` per ticket. Set ticket `status: in_progress` and `branch` in
`tracker.json`.

## 3. Edit (one message)
`builder:editor mode=build` per ticket, with its worktree and context pack path.
`GAP` → decide it from the arch, or ask Keshav when the arch is silent. Then spawn the editor
again with the answer. Never edit the code yourself.

## 4. Check (one message: three agents per ticket)
`builder:code-reviewer`, `builder:runner`, `builder:warden` for each ticket, in parallel.

## 5. Verify (one message)
`builder:verifier` per ticket. It reads all reports and gives `GREEN` or `RED`.

## 6. Decide and loop (main loop)
- **RED**: read the blocking items. Choose which findings to fix (always 🚨 and failed tests or
  criteria; ⚠️ when cheap). `ARCH-GAP` → ask Keshav, then update the arch through
  `/researcher:validate` or `researcher:arch-writer`. Spawn `builder:editor mode=fix` with the
  accepted findings, then go back to step 4. After three RED loops, set `status: blocked`, write
  the reason in `STATE.md`, and report to Keshav.
- **GREEN**: set `status: review`. If Keshav said yes in step 0, spawn
  `builder:brancher mode=ship` and save the `pr` URL in `tracker.json`.

## 7. Next wave
Recompute the ready tickets (dependencies now in `review` count as done only after their PRs
merge; ask Keshav whether to stack branches). Loop to step 1 until the epic has no ready tickets.

## 8. Report
Per ticket: verdict, PR link or blocker. Update `STATE.md` (`## Now`). Merging PRs is Keshav's
call; after merges, `/builder:status` marks tickets `done`.
