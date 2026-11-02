---
name: build
description: The builder's autonomous main loop for one epic of a project — takes the tickets from tracker.json and the GitHub Project, treats the project's arch docs as the source of truth, and drives fetcher, brancher, editor, code-reviewer, security-reviewer, runner, warden and verifier subagents ticket by ticket until each is verified and its CI is green, then opens PRs. Keshav only merges. Trigger /builder:build <project> <epic>.
argument-hint: "<project> <epic key, e.g. E1>"
---

# /builder:build

You are the main loop (Opus). Load `brain:pipeline`, `brain:tracker` and `builder:engineering`.
You orchestrate and decide; subagents (Sonnet) do every task. You never edit project code, run
the tests or write reports yourself. Per-ticket files live in `context/.runtime/builder/<p>/<ticket>/`.

**You run without Keshav.** The tracker, the arch and `builder:engineering` are the single source
of truth. You do not ask Keshav questions. You resolve gaps with the researcher (step 3), you
push branches and open PRs without asking, and you report at the end. Merging is the only step
that is his.

## The ledger (the brain mod enforces it)
- **Prompt header.** Every builder agent prompt starts with these lines, or the spawn is refused:
  ```
  project: <p>
  ticket: <E1-T1>
  worktree: <path>        (after step 2)
  mode: <build|fix|start|ship>   (editor and brancher)
  ```
- **Claims.** A spawn claims the ticket for this session for 2 hours. A ticket that another live
  session claimed is refused, so pick another ticket. Two sessions can build at the same time.
- **Reports.** Every report file starts with `sha: <git rev-parse HEAD>` and `status: <keyword>`.
  A report for another commit is stale and does not count.
- **Verifier gate.** `builder:verifier` is refused until `review.md`, `security.md`, `tests.md`
  and `arch-check.md` are all fresh for HEAD.
- **Ship gate.** `git push` and `gh pr create` from a ticket worktree are refused unless
  `verdict.md` is `GREEN` for HEAD. A commit after GREEN needs new checks.
- **Escalation.** The second and later `mode: fix` editor runs on Opus.
- **Tracker writes.** Change ticket fields only with `mcp__brain__ticket_update`.
- **Resume.** `mcp__brain__run_status <project>` shows each open ticket's step from the files and
  git on disk, its fix loops and the next action. Continue from that step; do not redo a step
  whose report is fresh.

## 0. Orient
- `mcp__brain__where <project>`: repos, GitHub project, epic progress.
- `mcp__brain__run_status <project>`: tickets that a stopped session left open.
- Read `tracker.json`. Pick the epic. If epic `E0` (foundation) is not done, build it first.
- Tickets with status `todo` whose `depends_on` are all `done` or `review` are **ready**
  (a dependency in `review` means a stacked branch; see `builder:engineering` section 6).
  Tickets `in_progress` or `review` resume where they stopped.
- An open decision in `STATE.md` that the epic depends on: resolve it with step 3 first.

## 1. Fetch (one fetcher per ready ticket, at most 2 tickets in flight)
`builder:fetcher` per ticket. `HALT` → resolve it with step 3, then fetch again.

## 2. Branch
`builder:brancher mode=start` per ticket, with the base branch (the default branch, or the
dependency's branch when it is still in review). Set `status: in_progress` and `branch` with
`mcp__brain__ticket_update`.

## 3. Edit
`builder:editor mode=build` per ticket, with its worktree, the base branch and the context pack path.

**Resolve a gap** (`GAP` from the editor, `HALT` from the fetcher, `ARCH-GAP` from the warden):
1. If the arch, the ADRs or `builder:engineering` answer it, decide and spawn again with the answer.
2. Else spawn `researcher:docs-reader` (and `researcher:reference-scout` when it is a design
   question) in parallel, then decide from their evidence the simplest option that keeps the
   arch's intent.
3. Record it: spawn `researcher:arch-writer` to add an ADR (marked `decided-by: builder`) and to
   update the arch section. Then spawn the agent again with the answer.
4. Only when the gap changes what the product does for its users (scope, a regulatory or
   compliance rule, money), set the ticket `blocked`, add the question to `STATE.md` open
   decisions, and continue with the other tickets.

## 4. Check (one wave of four agents per ticket; one ticket's wave at a time)
`builder:code-reviewer`, `builder:security-reviewer`, `builder:runner`, `builder:warden`
for each ticket, in parallel.

## 5. Verify
`builder:verifier` per ticket. It reads all reports and gives `GREEN` or `RED`.

## 6. Decide and loop (main loop)
- **RED**: fix every 🚨, every failed test or criterion, and every ⚠️ from the security review;
  other ⚠️ when cheap. `ARCH-GAP` → step 3. Spawn `builder:editor mode=fix` with the accepted
  findings, then go back to step 4.
- **GREEN**: spawn `builder:brancher mode=ship`. It pushes, opens the PR and waits for the
  GitHub Actions checks. Checks failed → treat the failed jobs as RED findings and loop.
  Checks green → set `status: review` and save the `pr` URL in `tracker.json`.
- The same finding (file and defect) back after a fix: do not send the same fix again. Change the
  approach: give the editor the arch section and the failed attempt, or resolve it with step 3.
- After three loops on one ticket, set `status: blocked`, write the reason in `STATE.md`, and
  continue with the other tickets.

## 7. Next wave
Recompute the ready tickets and loop to step 1 until the epic has no ready tickets.

## 8. Report
Per ticket: verdict, CI result, PR link, or blocker. The ADRs the builder decided. Update
`STATE.md` (`## Now`). Tell Keshav the order to merge the PRs (stacked PRs: base first). After
merges, `/builder:status` marks tickets `done`.
