# gimme-job — plan (v2, for builder)

> Status: **ready to split into tickets** (2026-11-14).
> Next: `/researcher:plan gimme-job` turns section 12 into `epic/E*/tickets/`, then `/builder:build gimme-job E0`.
> Everything is built in-house. No runtime dependency on career-ops or any other job tool.
> We study career-ops (MIT, v1.40.0) for *mechanisms* and write our own code. Credit it in the README.

---

## 1. Goal

One command runs the full loop with **no human approval steps**:

```
/gimme-job:run
  knobs → scan 150+ job sources → de-dupe → liveness → rank → select top N
  → gap analysis (resume vs selected jobs vs sage evidence)
  → rewrite resume (facts locked) → build resume-v{n}.pdf → gates
  → BLIND JUDGE on a random selected job → score ≥ 8.5 ? done : loop with reasons
  → cards in chat + link to resume-v{n}.pdf
```

Keshav reads the result and applies. **The plugin never submits an application and never sends email.**

### Success metrics
| Metric | Target |
|---|---|
| Blind judge score on final version | ≥ 8.5 / 10 on the round job **and** on a holdout job |
| Claims on a PDF with no fact behind them | 0 (automatic hard gate) |
| LLM tokens spent on scanning, de-dupe, ranking pre-filter, PDF build, cards | 0 (scripts only) |
| Cost of one full run | ≤ knob `budget.max_usd_per_run` (default USD 0.50) |
| Personal data in the public repo | 0 (hook gate) |

---

## 2. Decisions (locked by Keshav, 2026-11-14)

| # | Decision |
|---|---|
| D1 | **In-house only.** Port career-ops mechanisms (provider contract, A–H evaluation, liveness, fact gate, de-dupe fingerprint) into our own code. No vendored code, no Node. |
| D2 | **No manual approval.** Every change is saved as a version folder `v{n}` with what / why / sources. The automatic gates replace the human check. |
| D3 | **Blind judge loop.** A fresh subagent with zero context rates the new resume against one random ranked job. Pass = ≥ 8.5. Otherwise loop with its reasons. |
| D4 | **Model tiers.** Opus = main reasoning. Sonnet = coordination. Haiku = workers that call tools. Only workers get tools. |
| D5 | **Data root stays `memory/resume/`.** Private files are gitignored (contact info, PDFs, raw job text). |
| D6 | **Runtime:** Python 3.11+ standard library only. System binaries: `tectonic` (PDF) and `pdftotext` (poppler, ATS check). Nothing else. |
| D7 | **LinkedIn only through APIs** (Composio job_search). No scraping, no login automation. Scanners respect robots.txt and crawl delays. |

---

## 3. Folder structure

```
plugins/gimme-job/
  .claude-plugin/plugin.json             # name gimme-job, dependencies ["brain", "observe"]
  .mcp.json                              # composio, playwright, exa (all alwaysLoad: false)
  README.md                              # usage, knobs, credit to career-ops (MIT) for ideas
  config/
    knobs.schema.json                    # every knob: type, default, allowed values, doc
    knobs.default.yaml
    presets/ottawa-junior.yaml  canada-remote.yaml  us-reach.yaml
    skills-taxonomy.yaml                 # canonical skill names + aliases
    companies.yaml                       # tracked companies: name, careers_url, ats, slug, tier
    judge-rubric.md                      # fixed rubric for the blind judge (versioned)
    evaluation-blocks.md                 # our A–H block spec (section 7)
  skills/
    run/SKILL.md          /gimme-job:run [preset]          full loop (main session, Opus)
    scan/SKILL.md         /gimme-job:scan [preset]         phase 1 only
    rank/SKILL.md         /gimme-job:rank                  phase 2 only
    improve/SKILL.md      /gimme-job:improve               phases 3–6 on the current ranking
    knobs/SKILL.md        /gimme-job:knobs show|set|preset
    versions/SKILL.md     /gimme-job:versions [diff vA vB]
    doctor/SKILL.md       /gimme-job:doctor                tools, MCP links, binaries, gitignore, budget
  agents/
    # L1 coordinators — Sonnet, tools: Agent, Read (small files only)
    scout-lead.md         plans source batches from knobs, fans out to source workers, merges status
    analyst-lead.md       runs extract → evaluate → gap, returns gap brief
    writer-lead.md        turns Opus change plan into edit tasks, runs fact + lint gates
    # L2 workers — Haiku, the ONLY agents with tools
    source-worker.md      Bash (scanner scripts) + Composio job_search tools; one source batch
    signal-worker.md      Composio reddit + HN script; themes from posts
    mail-worker.md        Gmail read-only: LinkedIn alert emails → job URLs
    page-worker.md        WebFetch / Playwright: one job page → text (liveness + full JD)
    extract-worker.md     job text → features JSON (skills, years, pay, work auth, flags); cached by hash
    evidence-worker.md    Read/Grep sage projects/*/arch + GitHub MCP → fact candidates with proof links
    script-worker.md      Bash only: rank.py, build.sh, ats_check.py, lint_tex.py, cards.py, version.py
    # L2 reasoners — Sonnet, tools: Read only (inputs passed as file paths)
    jd-evaluator.md       A–H report + 1–5 score for one job (from features + full text)
    gap-analyst.md        selected jobs × resume × facts → lacking list (fixable by wording vs real skill gap)
    resume-writer.md      applies one edit task to resume-v{n}.tex (Edit tool on that one file only)
    fact-checker.md       every claim / number in the .tex → fact id, or BLOCK
    # Isolated
    blind-judge.md        Opus (knob), NO tools, fresh context; gets only JD text + resume text + rubric
  scripts/
    knobs.py              merge default → preset → memory/resume/knobs.yaml → flags; validate; print effective
    providers/            one module per source (section 6), shared contract in _base.py
      _base.py  _http.py (stdlib urllib, retry, backoff, robots, crawl delay)  _registry.py
      greenhouse.py lever.py ashby.py workday.py smartrecruiters.py workable.py ...
    scan.py               run enabled providers in parallel (thread pool, per-host limits) → jobs.jsonl
    composio_ingest.py    normalise Composio JSON (LinkedIn, JSearch, Glassdoor, Indeed, Google Jobs) → jobs.jsonl
    discover_ats.py       careers URL → ATS type + slug (fills companies.yaml)
    dedupe.py             source id, then fingerprint(title, company, city) → unique jobs
    liveness.py           HTTP status + "no longer accepting" patterns → live / dead / unknown
    rank.py               deterministic pre-score (section 7) → top K for LLM evaluation
    trend.py              skill frequency per week → market/snapshots/<date>.md
    build.sh              tectonic → resume-v{n}.pdf
    ats_check.py          pdftotext: contact parsed, links valid, page count, reading order, \ats text match
    lint_tex.py           lint knobs: tools per bullet, number per bullet, line count, banned words
    keyword_score.py      job keywords vs PDF text → coverage %, missing list
    facts.py              load / query memory/resume/facts.json; check claim ↔ fact match
    version.py            create v{n}: copy tex, write changes.md skeleton, scores.json, link to parent
    ledger.py             run ledger: tool calls ok/failed + reason, cost, per phase (reads observe traces)
    cards.py              ledger + jobs + version → markdown cards for chat (zero LLM tokens)
    pii_guard.py          scan staged files for phone, email, PDFs, raw JD dumps
  hooks/hooks.json        (section 9)
  templates/resume.cls    Trey Hunner class (keep its copyright notice)
  tests/                  pytest, stdlib unittest style; fixtures per provider (recorded JSON)

memory/resume/                          # data root (Keshav: "memory/resume stays")
  knobs.yaml                            # Keshav's overrides                       (tracked)
  facts.json                            # fact bank: id, claim, metric, source, proof link   (tracked, no PII)
  contact.tex                           # phone + email, \input by resume          (GITIGNORED)
  report/                               # market reviews, e.g. keshav-arri-2026-11-14.md (tracked)
  versions/
    v1/  resume-v1.tex  resume-v1.pdf  changes.md  scores.json  judge.json
    v2/  ...                            # .pdf GITIGNORED; .tex / .md / .json tracked
  runs/<run-id>/                        # GITIGNORED scratch
    ledger.jsonl  jobs.raw.jsonl  jobs.jsonl  features/  evals/  ranking.json  gaps.md  cards.md
  market/
    snapshots/<date>.md                 # tracked (aggregate counts only)
    jobs-index.jsonl                    # GITIGNORED (seen job ids, dates, scores; skip re-eval)
```

---

## 4. How the flow works

```
L0  MAIN (Opus, skill /gimme-job:run)  — decides only; no tools except Agent + Read of cards/briefs
 │
 ├─ PHASE 1 SCAN ──────────► L1 scout-lead (Sonnet)
 │                              ├─► L2 source-worker ×k (Haiku)  ATS scanners batch A/B/C (scan.py)
 │                              ├─► L2 source-worker   (Haiku)   Composio: LinkedIn search+get, JSearch, Glassdoor, Indeed, Google Jobs
 │                              ├─► L2 mail-worker     (Haiku)   Gmail LinkedIn alerts → URLs
 │                              ├─► L2 signal-worker   (Haiku)   Reddit + HN themes
 │                              └─► L2 script-worker   (Haiku)   dedupe.py → liveness.py (→ L3 page-worker for unknowns)
 │    ⇒ CARD 1 Tools  +  CARD 2 Jobs found
 │
 ├─ PHASE 2 RANK ──────────► L1 analyst-lead (Sonnet)
 │                              ├─► L2 script-worker  rank.py pre-score → top K (knob, default 12)
 │                              ├─► L2 extract-worker ×K (Haiku)  features JSON (cached by text hash)
 │                              └─► L2 jd-evaluator ×K (Sonnet)   A–H + 1–5 → ranking.json → select top N (default 5)
 │    ⇒ CARD 3 Selected jobs (detail)
 │
 ├─ PHASE 3 GAP ───────────► L1 analyst-lead
 │                              ├─► L2 evidence-worker (Haiku)  refresh facts.json from sage projects + GitHub
 │                              └─► L2 gap-analyst (Sonnet)     → gaps.md: fixable-by-wording | real skill gap | blocked by facts
 │
 ├─ PHASE 4 PLAN (MAIN, Opus) reads gaps.md + last judge reasons → change plan (what, where, why, fact ids)
 │
 ├─ PHASE 5 REWRITE ───────► L1 writer-lead (Sonnet)
 │                              ├─► L2 script-worker  version.py → v{n} folder (copy of v{n-1})
 │                              ├─► L2 resume-writer ×edits (Sonnet)  edits resume-v{n}.tex
 │                              ├─► L2 fact-checker (Sonnet)   BLOCK → writer-lead fixes or drops the edit
 │                              └─► L2 script-worker  lint → build.sh → ats_check → keyword_score → changes.md + scores.json
 │    ⇒ CARD 4 What / why changed
 │
 ├─ PHASE 6 BLIND JUDGE ───► blind-judge (Opus, no tools, fresh context)
 │       input: rubric + full text of ONE random job from the selected set (seeded, logged) + resume-v{n} text
 │       output: score 0–10, per-criterion scores, top 3 reasons, top 3 fixes → judge.json
 │       pass rule: ≥ 8.5 on round job AND ≥ 8.5 on a second unseen holdout job (stops overfitting)
 │    ⇒ CARD 5 Judge verdict
 │
 └─ LOOP: fail → back to PHASE 4 with judge reasons (new job drawn each round)
          stop when pass, or max_iterations (knob, default 4), or no gain for 2 rounds
          → keep the best version, report the blocker ("facts cap: years of experience")
    ⇒ CARD 6 Final: link to versions/v{n}/resume-v{n}.pdf
```

Depth: L0 main → L1 coordinator → L2 worker → L3 helper (page-worker) = **4 levels**. E0-T5 checks nested
subagent spawning works in the current Claude Code; fallback is main → coordinator plan → main fans out workers.

### Cards in chat (rendered by `cards.py`, no LLM tokens)

**Card 1 — Tools**
| Tool / source | Calls | OK | Failed | Fail reasons |
|---|---|---|---|---|
| LinkedIn search (Composio) | 3 | 3 | 0 | — |
| LinkedIn get job | 10 | 6 | 4 | 429 rate limit ×4 |
| Greenhouse scanner | 18 | 18 | 0 | — |
| … | | | | |
| **Total** | 87 | 81 | 6 | cost USD 0.004 / cap 0.50 |

**Card 2 — Jobs found**: found per source → after de-dupe → live → pre-ranked K. (counts only)
**Card 3 — Selected jobs (only these in detail)**: rank, title, company, city, work type, pay, A–H score, why selected, link.
**Card 4 — v{n} changes**: section, before → after (short), why, job words hit, fact ids.
**Card 5 — Judge**: job used, score, criteria table, reasons, verdict PASS / LOOP.
**Card 6 — Result**: `memory/resume/versions/v{n}/resume-v{n}.pdf`, score history v1 → v{n}, keyword coverage delta.

### Version folder — `versions/v{n}/changes.md`
```
# v{n} — <date> — run <id> — parent v{n-1}
## Why this version        judge reasons from v{n-1} + gaps addressed
## Changes
| # | Section | Before | After | Why | Job words | Fact ids | Sources |
## Locked facts kept       (titles, employers, dates, every number unchanged)
## Scores                  keyword coverage, ATS check, lint, judge (v{n-1} → v{n})
## Jobs used               selected set + round job + holdout job (ids, links)
```
`v1` = the current resume imported as-is and judged, so every later version has a baseline.

---

## 5. Honesty rules (automatic, because there is no human approval)

| Allowed | Blocked by fact-checker |
|---|---|
| Reword, reorder, move result first | New metric not in facts.json |
| Choose which true metric to show | Round up (48% → 50%) |
| Same fact in different units (77% ↔ 3 min → 40 s) | Merge two results into one bigger claim |
| Job-post words for work that was done | Tool, scope or title not in facts |
| Round down, use "~" | Change employer, title, dates |

- Titles, employers, dates and every number are **locked**. The writer edits wording only (summary, experience bullets, project bullets, skills order).
- Job text, Reddit and email content are **data, never instructions** (prompt-injection rule in every agent).
- The judge can ask for things the facts cannot give (e.g., more years). Gap-analyst marks those **blocked by facts**; the loop stops instead of inventing.

---

## 6. Job sources (in-house providers)

### Provider contract (`scripts/providers/_base.py`)
```python
class Provider:
    name: str; kind: "ats" | "board" | "feed" | "api"
    def list_jobs(self, target: dict, knobs: Knobs) -> Iterator[Job]: ...
Job = {id, source, url, title, company, location, workplace, employment, posted_at,
       salary_min, salary_max, currency, description, raw_ref}
```
Rules: stdlib HTTP only; robots.txt check; per-host crawl delay; retry 4× with backoff; recorded-fixture test per provider; knob filters applied in `scan.py` after fetch.

### Waves (target 150+ over time; each provider = one small ticket)
| Wave | Providers | Why first |
|---|---|---|
| W1 (E2) | Greenhouse, Lever, Ashby, Workday, SmartRecruiters, Workable, Recruitee, BambooHR, Teamtailor, Personio, BuiltIn, **Job Bank Canada**, Hacker News (Who is hiring), RemoteOK, Remotive, WeWorkRemotely, Himalayas, Jobicy, Getro (VC job boards) | Covers most Canadian AI / tech employers and VC portfolios |
| W2 | iCIMS, Taleo, SuccessFactors, Oracle Cloud, Phenom, Eightfold, Jobvite, Dover, Gem, Rippling, Breezy, JazzHR, Pinpoint, Comeet, Polymer, UltiPro, Paylocity, ADP, Avature, Pageup | Big enterprise ATSs (banks, telcos, Kinaxis-type firms) |
| W3 | Regional / niche boards on demand | Only when knobs target those markets |

### API sources (Composio `job_search`, via source-worker) — filters verified 2026-11-14
- **LinkedIn search** `JOB_SEARCH_JOBS_API_LINKEDIN_SEARCH_JOBS`: `query`, `location`, `date_posted` (day/week/month), `workplace_types` (remote;hybrid;onSite), `employment_types` (contractor;fulltime;parttime;intern;temporary), `experience_levels` (intern;entry;associate;midSenior;director), `organization_ids`, `token`. Detail: `..._LINKEDIN_GET_JOB` (`id`).
- **LinkedIn active jobs** `JOB_SEARCH_LINKEDIN_SEARCH_LIST_ACTIVE_JOBS`: `title(_advanced)`, `description(_advanced)`, `location(_advanced)`, `time_frame` (1h/24h/7d/6m), `ai_experience_level` (0-2/2-5/5-10/10+), `ai_work_arrangement`, `ai_employment_type`, `ai_visa_sponsorship`, `ai_education`, `ai_taxonomies_a`, `has_salary`, `direct_apply`, `organization(_slug/_size/_industry/_agency)`, `organization_headcount_gte/lt`, `exclude_organization`, `source` (linkedin/wellfound/ycombinator), `exclude_ats_duplicate`, `limit`, `cursor`. Price not checked yet → off by default.
- **JSearch** `JOB_SEARCH_JSEARCH_SEARCH_JOBS`: `query`, `country`, `language`, `date_posted` (all/today/3days/week/month), `work_from_home`, `employment_types`, `job_requirements` (under_3_years_experience/…/no_degree), `radius`, `exclude_job_publishers`, `num_pages` (≤20), `fields`, `cursor`. Salary: `..._JSEARCH_GET_ESTIMATED_SALARY`.
- **Glassdoor** `..._GLASSDOOR_REALTIME_JOBS_SEARCH`: `query`, `city`, `location_id`, `company`, `industry`, `job_function`, `job_type`, `seniority_level`, `min/max_salary`, `date_posted`, `remote_only`, `easy_apply_only`, `company_size`, `company_rating`, `sort`, `page_cursor`. Plus interviews, salaries, reviews.
- **Indeed** `..._JOBS_API_INDEED_SEARCH_JOBS`: `query`, `location`, `country_code`, `radius`, `radius_type`, `sort_type`, `token`.
- **Google Jobs** `..._GOOGLE_JOBS_LIST_JOBS` (+ BY_TECHNOLOGY_STACK, ENTRY_LEVEL, REMOTE, VISA_SPONSORSHIP, …).
- **Reddit** `REDDIT_SEARCH_ACROSS_SUBREDDITS`, `REDDIT_RETRIEVE_POST_COMMENTS` (signals, not jobs).

### Other MCPs
| Use | MCP | Phase |
|---|---|---|
| LinkedIn alert emails → job URLs (read only) | Gmail | 1 |
| Company research, eng blogs | Exa | 2 (jd-evaluator block G via page/extract workers) |
| Evidence for facts | GitHub | 3 |
| JS career pages, liveness | Playwright | 1 |
| Interview dates (later) | Google Calendar | E6 |
| Tracker board (later) | Notion | E6 |

---

## 7. Ranking and evaluation

### Pre-score (`rank.py`, deterministic, 0–100)
| Signal | Weight (knob) |
|---|---|
| Title match to `profile.target_titles` | 20 |
| Skill overlap (features vs facts skills, taxonomy-normalised) | 30 |
| Years asked vs `profile.years_experience` | 15 |
| Seniority / work type / location fit | 10 |
| Pay vs `profile.min_base_cad` | 10 |
| Freshness (posted days ago) | 10 |
| Company tier (companies.yaml) | 5 |
Hard drops: excluded titles / companies / agencies, `must_not_have` hits, dead postings, sponsorship mismatch.

### A–H evaluation (`jd-evaluator`, our own spec in `config/evaluation-blocks.md`)
A role summary · B match with resume (requirement → evidence table, importance bands) · C level and strategy ·
D comp and demand · E customisation plan (feeds gap-analyst) · F interview plan · G posting legitimacy
(repost, vague, agency, too-good signals) · H application pack (only if score ≥ 4.5).
Global score 1–5. Bands: ≥ 4.5 strong, 4.0–4.4 apply, 3.0–3.9 maybe, < 3.0 skip. Select top N with score ≥ `scoring.select_min` (default 4.0).

### Blind judge rubric (`config/judge-rubric.md`, 10 points)
Requirement coverage 3 · Evidence strength (numbers, scope, ownership) 2.5 · Relevance and order of content 1.5 ·
Clarity / 6-second scan 1.5 · Seniority fit 1 · ATS readability 0.5. The judge never sees earlier scores, versions or this plan.

---

## 8. Knobs (`config/knobs.default.yaml`)

```yaml
profile:  { target_titles: [AI Engineer, Applied AI Engineer, Agentic AI Engineer, LLM Engineer, AI Platform Engineer, Forward Deployed Engineer],
            exclude_titles: [Principal, Director, Manager, Data Scientist, Sales],
            years_experience: 2, work_auth: PGWP, needs_sponsorship: false, min_base_cad: 95000 }
search:   { locations: ["Ottawa, Ontario, Canada", "Toronto, Ontario, Canada", "Canada"], remote_regions: [Canada],
            date_posted: week, workplace: [remote, hybrid, onSite], employment: [fulltime, contractor],
            seniority: [entry, associate], experience_buckets: ["0-2", "2-5"], exclude_agencies: true,
            include_companies: [], exclude_companies: [], must_have_any: [LLM, agent, RAG, MCP, GenAI], must_not_have: [] }
sources:  { ats_scanners: { enabled: true, waves: [W1] },
            linkedin_search: { enabled: true, max_results: 30, get_details_top: 15 },
            linkedin_active_jobs: { enabled: false }, jsearch: { enabled: true, num_pages: 2, country: ca },
            glassdoor: { enabled: true }, indeed: { enabled: false, country_code: CA }, google_jobs: { enabled: false },
            gmail_alerts: { enabled: true }, reddit: { enabled: true, subreddits: [cscareerquestionsCAD, MachineLearningJobs, LangChain, ITManagers] },
            hackernews: { enabled: true } }
ranking:  { pre_rank_top_k: 12, select_top_n: 5, select_min: 4.0, weights: { title: 20, skills: 30, years: 15, fit: 10, pay: 10, fresh: 10, tier: 5 } }
loop:     { pass_score: 8.5, holdout: true, max_iterations: 4, plateau_rounds: 2, seed: auto }
resume:   { max_pages: 2, min_keyword_coverage: 0.70,
            lint: { max_tools_per_bullet: 3, require_number: true, max_lines: 2, ban: ["&", "Startup-trained"] } }
budget:   { max_usd_per_run: 0.50, max_composio_calls: 80, concurrency: 3, retry: { attempts: 4, backoff: exponential } }
models:   { main: opus, coordinator: sonnet, reasoner: sonnet, worker: haiku, judge: opus }
privacy:  { block_push_patterns: ["\\(\\d{3}\\) \\d{3}-\\d{4}", "[\\w.]+@gmail\\.com", "\\.pdf$"] }
```

---

## 9. Lifecycle hooks (`hooks/hooks.json`)

| Event | Matcher | Script | Purpose |
|---|---|---|---|
| SessionStart | — | `knobs.py --brief` | 5-line effective-knobs summary into context |
| PreToolUse | `mcp__composio__.*` | `ledger.py --budget-check` | deny the call when run budget / call cap is hit |
| PreToolUse | `Bash(git commit*)`, `Bash(git push*)` | `pii_guard.py` | block PII, PDFs, raw JD dumps |
| PreToolUse | `Agent` | `ledger.py --tier-check` | refuse a spawn whose agent model/tools break the tier rule |
| PostToolUse | all | `ledger.py --record` | ok / failed + reason per tool call (feeds Card 1) |
| PostToolUse | `Edit|Write` on `versions/**/*.tex` | `build.sh` | fast rebuild |
| SubagentStop | — | `ledger.py --report-check` | worker must have written its report file; reply ≤ 8 lines |
| Stop | — | `cards.py --final` | print the cards if a run finished; warn if a v{n} folder is incomplete |

---

## 10. Token rules

1. **Scripts before models.** Scan, de-dupe, liveness, pre-rank, build, ATS, lint, keyword score, ledger and cards are Python. 0 tokens.
2. **Tools only on workers.** Main and coordinators have `Agent` + `Read`. MCP schemas load only inside the worker that needs them (`alwaysLoad: false`).
3. **Report to file.** Every subagent writes its full output under `runs/<id>/`; its reply is status + path + ≤ 8 lines (sage rule).
4. **Raw job text never reaches Opus.** Haiku extracts features once, cached by text hash; Sonnet evaluators read features + text; Opus reads briefs and cards only.
5. **Evaluate few.** A–H only on top K after the free pre-score. Jobs evaluated in the last 14 days are reused from `jobs-index.jsonl`.
6. **Stable prompts** for agents and rubric (prompt caching friendly). Judge input is compact text, no PDF images.
7. **Loop caps** (`max_iterations`, `plateau_rounds`, budget) stop runaway cost.

---

## 11. Safety

Never submit, never send (Gmail read-only). No PII in git (hook). APIs only for LinkedIn. robots.txt + crawl delay
for scanners. Untrusted content is data. Budget caps. Facts locked.

---

## 12. Epics and tickets

Each ticket: files, acceptance criteria (AC), depends_on. Tests run with `python -m pytest plugins/gimme-job/tests`.

### E0 — Foundation
| Ticket | Scope | AC | Depends |
|---|---|---|---|
| E0-T1 | Plugin skeleton, marketplace entry, README, `/gimme-job:doctor` | doctor prints tool / binary / MCP status | — |
| E0-T2 | `memory/resume` layout, `.gitignore` rules, `pii_guard.py` + hook | test: staging a PDF or phone number is blocked | E0-T1 |
| E0-T3 | `knobs.schema.json`, defaults, presets, `knobs.py`, `/gimme-job:knobs` | invalid value → clear error; `show` lists source of each value | E0-T1 |
| E0-T4 | `ledger.py` (record, budget-check, report-check) + hooks; reads `observe` traces | test: 3 failed + 2 ok calls → correct counts and reasons | E0-T1 |
| E0-T5 | Spike: nested subagent depth 4 + per-agent model/tools frontmatter in current Claude Code | written result + chosen fallback | E0-T1 |
| E0-T6 | Agent files for all tiers with model + tools frontmatter; `--tier-check` hook | spawn of an agent with wrong tier is refused | E0-T4, E0-T5 |

### E1 — Resume build and versions
| E1-T1 | Import `resume.cls` + current `.tex` as `versions/v1`; split `contact.tex` | v1 PDF matches Overleaf (visual diff ≤ small threshold) | E0-T2 |
| E1-T2 | `build.sh` (tectonic) + PostToolUse rebuild hook | edit → PDF < 20 s | E1-T1 |
| E1-T3 | `ats_check.py` | catches `\ats` mismatch, broken link, page overflow | E1-T2 |
| E1-T4 | `lint_tex.py` | flags known v1 issues (tool soup, "&") | E1-T1 |
| E1-T5 | `version.py` + `changes.md` template + `/gimme-job:versions diff` | v2 folder created with parent link and skeleton | E1-T1 |
| E1-T6 | `facts.json` schema + `facts.py`; seed from v1 resume + market report | every number in v1 maps to a fact id | E1-T1 |

### E2 — Scan (in-house providers)
| E2-T1 | `_base.py`, `_http.py` (stdlib, robots, delay, retry), `_registry.py`, `scan.py` | fixture provider → normalised Job rows | E0-T3 |
| E2-T2…T20 | One ticket per W1 provider (Greenhouse … Getro), fixture test each | provider returns ≥ 1 normalised job from fixture; live smoke optional | E2-T1 |
| E2-T21 | `discover_ats.py` + seed `companies.yaml` (Canadian AI / tech list) | 20 careers URLs → ATS + slug | E2-T1 |
| E2-T22 | `composio_ingest.py` + `source-worker` for LinkedIn / JSearch / Glassdoor / Indeed / Google Jobs, concurrency 3, 429 backoff | 30 LinkedIn rows ingested; ledger shows ok/failed | E0-T4, E0-T6 |
| E2-T23 | `mail-worker` (Gmail alerts → URLs), `signal-worker` (Reddit + HN) | alert email fixture → URLs | E0-T6 |
| E2-T24 | `dedupe.py` + `liveness.py` (+ page-worker for unknowns) | duplicate across 2 sources merged; dead fixture dropped | E2-T1 |
| E2-T25 | `scout-lead` + `/gimme-job:scan` + Cards 1–2 via `cards.py` | one command → jobs.jsonl + 2 cards | E2-T22, E2-T24 |

### E3 — Rank and gap
| E3-T1 | `skills-taxonomy.yaml` + `extract-worker` with hash cache | same text twice → 1 model call | E2-T25 |
| E3-T2 | `rank.py` pre-score with knob weights + hard drops | fixture set ranks in expected order | E3-T1 |
| E3-T3 | `evaluation-blocks.md` + `jd-evaluator` (A–H, 1–5) | report has all blocks; score band correct | E3-T1 |
| E3-T4 | `analyst-lead` + `/gimme-job:rank` + Card 3 | top N selected with reasons | E3-T2, E3-T3 |
| E3-T5 | `evidence-worker` (sage projects + GitHub → fact candidates) | new facts carry a proof link | E1-T6 |
| E3-T6 | `gap-analyst` → `gaps.md` (wording / skill gap / blocked by facts) | each gap cites job ids and fact ids | E3-T4, E3-T5 |
| E3-T7 | `trend.py` market snapshot | snapshot with counts + delta | E3-T1 |

### E4 — Rewrite and gates
| E4-T1 | `resume-writer` (Edit on one .tex only) + `writer-lead` | change plan → edited v{n} tex | E1-T5, E3-T6 |
| E4-T2 | `fact-checker` with the honesty table (section 5) | invented / rounded-up number → BLOCK | E1-T6 |
| E4-T3 | Gate chain: fact → lint → build → ATS → keyword → `changes.md` + `scores.json` + Card 4 | failed gate stops the version and logs why | E4-T1, E4-T2, E1-T3, E1-T4 |

### E5 — Blind judge loop
| E5-T1 | `judge-rubric.md` + `blind-judge` (no tools, fresh context) → `judge.json` + Card 5 | judge prompt contains only rubric + JD + resume text (test asserts) | E4-T3 |
| E5-T2 | Loop control in `/gimme-job:run`: seeded random job, holdout, max_iterations, plateau, best-version keep, Card 6 | fixture run: fail → loop → pass; plateau stops with blocker | E5-T1, E3-T4 |
| E5-T3 | `/gimme-job:run` end to end + `/gimme-job:improve` | full run on live data writes v2+ and all cards within budget | E5-T2, E2-T25 |

### E6 — Later
W2 providers · Calendar interview events · Notion tracker · application tracker + follow-up drafts (Gmail drafts only) ·
interview prep from Glassdoor reports · weekly scheduled market scan.

---

## 13. Open items

1. **Private backup:** `memory/resume` private files are gitignored and stay on Keshav's Mac. A private repo submodule can come later.
2. **Paid source caps:** LinkedIn active-jobs price unknown → off until checked.
3. **Markets:** default Canada; `us-reach` preset exists but off.

## 14. Research behind this plan
- career-ops (MIT, v1.40.0) read 2026-11-14 for mechanisms: provider contract and 150+ provider list, A–H blocks, score bands, liveness, fact gate, de-dupe fingerprint, data/system split, spend tiers.
- Composio tool schemas pulled 2026-11-14 (section 6).
- Live market data: `memory/resume/report/keshav-arri-2026-11-14.md`.
