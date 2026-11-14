# gimme-job

Job hunt loop for sage. One command scans the market, ranks jobs, finds what your resume lacks, rewrites it into a
new version, gates it, and loops with a blind judge until it scores **8.5+**. No approval steps; every change is versioned.

```
/gimme-job:run [preset]
  knobs → scan (145 scanners + job APIs + Gmail alerts) → de-dupe → filters → liveness → rank → A–H → select
  → gaps (resume × jobs × sage evidence) → plan (Opus) → rewrite v{n} → fact gate → lint → PDF → ATS → keywords
  → blind judge (random selected job + holdout) → ≥ 8.5 ? done : loop
  → cards in chat + link to memory/resume/versions/v{n}/resume-v{n}.pdf
```

The plan behind this plugin: [`projects/gimme-job/plan.md`](../../projects/gimme-job/plan.md). Source list: [`providers.md`](../../projects/gimme-job/providers.md).

## Commands
| Command | What it does |
|---|---|
| `/gimme-job:run [preset]` | Full loop (main session = Opus) |
| `/gimme-job:scan` | Phase 1: scan + Tools / Jobs cards |
| `/gimme-job:rank` | Phase 2: pre-score + A–H + Selected card |
| `/gimme-job:improve` | Phases 3–7 on a ranked run |
| `/gimme-job:knobs show\|set\|get\|presets` | Tune everything; shows where each value comes from |
| `/gimme-job:versions list\|show\|diff\|best` | Resume versions with judge scores |
| `/gimme-job:doctor` | Setup check |

## Setup (once)
```bash
brew install tectonic poppler
```
```bash
python3 plugins/gimme-job/scripts/doctor.py
```
- Your resume lives at `memory/resume/versions/v1/resume-v1.tex` (imported from Overleaf). Phone + email are in
  `memory/resume/contact.tex` (**gitignored**), pulled in with `\input{contact}`.
- `memory/resume/facts.json` is the fact bank. The writer may only reword facts; the fact gate blocks anything else.
  Add facts with a `source` and `proof`.
- Composio (`job_search`, `reddit`) and Gmail connections give the API sources. Scanners need no keys
  (except Algolia-backed `techinasia`, `wttj`: set `GIMME_JOB_<NAME>_ALGOLIA_APP` / `_KEY`).
- Fill `config/companies.toml` (`ats`, `slug`) with `python3 plugins/gimme-job/scripts/discover.py ats <careers_url>`.

## Sources (157)
- **145 in-house scanners** in 6 waves (W1–W3 on by default): Greenhouse, Lever, Ashby, Workday, SmartRecruiters, BuiltIn,
  Job Bank Canada, Dayforce, Hacker News, Getro, iCIMS, Taleo, SuccessFactors, Oracle, Phenom, Eightfold, Amazon, Google, Apple, …
  `python3 plugins/gimme-job/scripts/scan.py --list`
- **11 Composio APIs**: LinkedIn search + details, LinkedIn active jobs, JSearch, Glassdoor, Indeed, Google Jobs, ZipRecruiter,
  Bing, Xing, Remote jobs, Daily International Jobs. `composio_ingest.py --plan` shows the exact calls for your knobs.
- **Gmail job alerts** (read only) + LinkedIn saved-jobs CSV export.
- Signals (not jobs): Reddit, HN.

Scan modes: `scan.py --waves [W1 ..]`, `--full-ats`, `--company NAME`, `--url URL`, `--provider NAME`.

## Model tiers and tokens
| Tier | Model | Agents | Tools |
|---|---|---|---|
| Main | Opus | the `run` skill | Agent + Read (cards, briefs only) |
| Coordinator | Sonnet | scout-lead, analyst-lead, writer-lead | Agent + Read |
| Reasoner | Sonnet | jd-evaluator, gap-analyst, resume-writer, fact-checker | Read / Edit one file |
| Worker | Haiku | source, signal, mail, page, extract, evidence, script | **the only agents with tools** |
| Judge | Opus | blind-judge | none, fresh context |

Scripts do all scanning, de-dupe, ranking pre-filter, PDF build, gates and cards (0 tokens). Raw job text never reaches Opus.
The `ledger.py --tier-check` hook refuses an agent spawn with the wrong model.

## Hooks
SessionStart knobs brief · PreToolUse Composio budget cap · PreToolUse PII guard on `git commit/push` · PreToolUse tier check ·
PostToolUse tool-call ledger (feeds Card 1) · PostToolUse auto-build on `versions/**/*.tex` · SubagentStop report-file check ·
Stop final cards.

## Versions
`memory/resume/versions/v{n}/`: `resume-v{n}.tex`, `resume-v{n}.pdf` (gitignored), `changes.md` / `changes.json`
(before / after / why / job words / fact ids / sources), `scores.json` (gates), `judge.json` (blind judge).

## Tests
```bash
cd plugins/gimme-job && python3 -m unittest discover -s tests -t . -p 'test_*.py'
```
320 tests: one fixture test file per scanner (no network), extractors, and the core pipeline.

## Limits (honest)
- Scanner tests use fixtures built from upstream response shapes; live endpoints were **not** hit while building
  (the build sandbox blocked outbound hosts). First live run: expect a few scanners to need small fixes — Card 1 shows which.
- A few sources work best with a browser upstream (`interamt`, `topdev`, `dayforce`, some Workday/SuccessFactors edge cases):
  ours use plain HTTP and may return nothing on bot-protected boards. `mokahr` needs the `openssl` CLI.
- Ideas and source list come from [career-ops](https://github.com/career-ops-hq/career-ops) (MIT, v1.40.0). All code here is our own Python.
