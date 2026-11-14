---
name: run
description: Full gimme-job loop with no approval steps — scan 145 scanners + job APIs + alerts, rank, find gaps, rewrite the resume into a new version, gate it, and loop with a blind judge until it scores 8.5+ on a random selected job and a holdout job. Shows cards in chat and links the new resume-v{n}.pdf.
argument-hint: "[preset] [--max-iterations N]"
---

# /gimme-job:run

You are the **main loop (Opus)**. You decide. You do not call job tools, read raw job text, or edit the resume yourself:
coordinators (Sonnet) assign work; workers (Haiku) hold the tools. You read only cards, briefs, `gaps.md` and `judge.json`.
Scripts: `plugins/gimme-job/scripts/`. Data: `memory/resume/`. Specs: `plugins/gimme-job/config/`.

## 0. Setup
- `gimme-job:script-worker`: `knobs.py brief [--preset P]` and `version.py latest`.
- If latest version is 0: stop and tell Keshav to import his resume as `memory/resume/versions/v1/resume-v1.tex` (see README).
- Run id: from the scan step (`runs/CURRENT`).
- If `v1` has no `judge.json`, it is judged in step 6 first so every later version has a baseline.

## 1. SCAN → `gimme-job:scout-lead` (pass preset + budget). Show **Card 1 Tools** and **Card 2 Jobs found** in chat (copy the markdown from `cards.py`).

## 2. RANK + 3. GAP → `gimme-job:analyst-lead`. Show **Card 3 Selected jobs**.
Stop if 0 jobs selected: report the funnel and suggest knob changes (wider `date_posted`, more waves, lower `select_min`).

## 4. PLAN (you)
Read `gaps.md` and the last `judge.json` reasons/fixes. Write `runs/<run>/plan-v{n}.md`: ≤ 7 edits, each
`{section, target line, change, why, job words, fact ids}`. Rules: wording-fixable gaps first; never plan an edit without a fact id;
"blocked by facts" items are reported, never written. Prefer edits that serve several selected jobs.

## 5. REWRITE → `gimme-job:writer-lead` with the plan path. Show **Card 4 Changes**.
`GATE-FAIL`: one retry with the gate's message; second failure → keep the previous version as current and report.

## 6. BLIND JUDGE
- Pick the round job: `script-worker` → `python3 -c "import random,json; ..."` seeded with knobs `loop.seed` (or run id),
  one random job from `selected.json` not used as round job before; pick a different one as **holdout**.
- Get texts: JD from `runs/<run>/jobs.jsonl` (or `pages/<id>.txt`), resume text via `pdftotext` (or `facts.tex_text`).
- Spawn **`gimme-job:blind-judge`** (Opus, no tools, fresh context). The prompt contains ONLY: the rubric file text, the job text,
  the resume text. No run history, no scores, no plan, no version number.
- Holdout: a second fresh blind-judge with the holdout job (only when the round score ≥ pass score).
- `script-worker` writes `versions/v{n}/judge.json`: `{score, criteria, reasons, fixes, verdict, job_id, job_title, job_company,
  holdout_score, holdout_title}`; then `version.py render <n>`. Show **Card 5 Judge**.

## 7. LOOP
- PASS = round score ≥ `loop.pass_score` and (holdout off or holdout ≥ pass score).
- Not PASS → back to step 4 with the judge's reasons (a new round job each time).
- Stop when: PASS, `loop.max_iterations` versions made this run, no gain for `loop.plateau_rounds` rounds, or budget hit.
  On a stop without PASS: `version.py best` → that version is the result; say what blocks a higher score (often "blocked by facts").

## 8. FINISH
- `script-worker`: `trend.py --run <run>` (market snapshot) and `cards.py result`. Touch `runs/<run>/DONE`.
- Show **Card 6 Result** with the link to `memory/resume/versions/v{n}/resume-v{n}.pdf`.

## Token rules
Scripts before models. Tools only on workers. Every subagent writes its full output to a file and replies ≤ 8 lines.
Raw job text never enters this session. A–H runs only on top K. Max 4 subagents in flight.
