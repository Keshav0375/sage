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
- Design lock: if `memory/resume/design/baseline.json` is missing, run `layout.py baseline memory/resume/versions/v1/resume-v1.pdf`
  (the ORIGINAL design: section order, skills rows, line fill, page breaks; snapshots are contact-redacted).
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

## 5. REWRITE → `gimme-job:writer-lead` with the plan path.
**One version per run.** Round 1: `version.py start --run <run>` (returns v{n}). Every round: `version.py iterate <n>` →
`v{n}/iterations/iter-k/resume.tex`; all gates and the judge write into that iter folder. At the end: `version.py promote <n> --best`
(design PASS first, then holdout score). Never create a second version folder in the same run.
 Show **Card 4 Changes**.
Design rules (never break them in the plan): same section order, same skills row labels (one line each), every bullet keeps
its line count and its last line ≥ `layout.min_last_line_fill` full, nothing past the margin. Plans change WORDS, not design.
After the edits, `layout.py check` must PASS; on FAIL writer-lead runs `gimme-job:layout-fixer`, which loops and then reads the
Playwright compare image (`layout.py compare <pdf> runs/<run>/compare-v{n}.png`) before it reports.
`GATE-FAIL`: one retry with the gate's message; second failure → keep the previous version as current and report.

## 6. BLIND JUDGE
- **Holdout is fixed for the whole run** (first draw), so every version is scored on the same job and scores compare.
  The round job rotates: seeded random draw (knobs `loop.seed` or run id) from `selected.json`, not used before.
  Also re-judge the final version on v1's round job, so the report shows a same-job before/after.
- Judge scores from one sample vary about ±0.5. Treat a gain < 0.5 as noise.
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
Show ONLY `cards.py summary` (tool calls · jobs selected · resume strengths/weaknesses · lines before/now) and the PDF link.
- `script-worker`: `trend.py --run <run>` (market snapshot) and `cards.py result`. Touch `runs/<run>/DONE`.
- Show **Card 6 Result** with the link to `memory/resume/versions/v{n}/resume-v{n}.pdf`.

## Commit rule
Run `bash plugins/gimme-job/scripts/check.sh` (all tests + PII guard) before every commit. Commit only when it prints `check.sh: OK`.

## Large API responses
Use `MULTI_EXECUTE(sync_response_to_workbench=true)`, then run `composio_ingest.py --workbench-snippet` in COMPOSIO_REMOTE_BASH_TOOL
to print one compact line per job; save that output as `runs/<run>/composio/<slug>.jsonl`. Full job text is fetched later for the
top K only (source-worker writes `runs/<run>/pages/<id>.txt`).

## Token rules
Scripts before models. Tools only on workers. Every subagent writes its full output to a file and replies ≤ 8 lines.
Raw job text never enters this session. A–H runs only on top K. Max 4 subagents in flight.
