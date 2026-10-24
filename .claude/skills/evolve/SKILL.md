---
name: evolve
description: Self-improvement loop for the harness itself (after Self-Harness, arXiv 2606.09498) — mine failure mechanisms, have the harness-smith propose one minimal edit per mechanism on a branch, run held-in and sealed held-out evals for baseline vs candidate, and promote only on held-in gain with zero held-out regressions. Keshav approves every promotion. Trigger /evolve [mechanism].
argument-hint: "[mechanism id from /mine]"
disable-model-invocation: true
---

# /evolve

The referee (`sagectl/evals.py`, `sagectl/guard.py`, `evals/**/heldout`) is frozen for this loop.
Nothing in it may edit the thing that grades it.

1. **Preconditions** (else stop and say what's missing): `python3 bin/sagectl eval list` shows
   ≥ 3 held-in and ≥ 2 held-out tasks for the target; `claude` CLI is on PATH; tree is clean.
2. **Mine:** `miner` → pick the top mechanism (or the one Keshav named).
3. **Baseline:** `python3 bin/sagectl eval run --split heldin --label base-<slug> --trials 2` and
   the same with `--split heldout`. Run it on `main`.
4. **Propose:** `harness-smith` with the mechanism. Returns PROPOSAL + branch `evolve/<slug>`.
5. **Candidate:** `git worktree add ../.wt/sage-evolve-<slug> evolve/<slug>`, then run both splits
   with `--harness ../.wt/sage-evolve-<slug> --label cand-<slug> --trials 2`.
6. **Judge:** `python3 bin/sagectl eval compare --base base-<slug> --cand cand-<slug>`.
   PROMOTE requires held-in gain AND no held-out task that passed before failing now.
7. **Keshav decides.** Show: mechanism, the diff (`git diff main...evolve/<slug>`), the compare
   output. Only on his yes: merge to main. REJECT → delete the branch, log what was tried in
   the lesson (`sagectl lesson add … --source evolve`) so it isn't retried blindly.

## Improving the improver (quarterly, Keshav-triggered)
The harness-smith's own prompt is an editable surface too (Hyperagents idea). Its score =
fraction of its PROPOSALs that got PROMOTE over the last N cycles. Run `/evolve` with mechanism
"harness-smith proposals get rejected" using the history in `library/evolve-log.md`. Its
candidate is judged the same way, by whether *its* proposals then promote more often. Append
every cycle's result to `library/evolve-log.md`.

Reality check to tell Keshav: with a handful of eval tasks, one or two flips are noise. Use
`--trials 3`+ and treat small held-in gains with suspicion.
