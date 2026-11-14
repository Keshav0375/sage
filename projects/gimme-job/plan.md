# gimme-job — plan

> Status: **draft for brainstorm** (2026-11-14). Next step after Keshav signs off: split into
> `arch/` + `epic/E*/tickets/` with `/researcher:plan gimme-job`, then `/builder:build gimme-job E0`.

## 1. Goal

A sage plugin that runs the whole job hunt from one place, using real market data:

```
discover jobs → check still open → score fit → tailor resume (.tex) → build PDF → gate (facts, ATS, lint)
→ prep application → track → follow up → interview prep → offer / negotiate → learn from outcomes
                ▲                                                                      │
                └──────── weekly market scan (LinkedIn, Glassdoor, Reddit, HN) ◄────────┘
```

**A human presses Submit. The plugin never applies for you.**

### Success metrics
| Metric | Target |
|---|---|
| Time from job URL to tailored, gated PDF | < 5 min |
| Claims on a PDF with no fact behind them | 0 (hard gate) |
| Weekly market scan cost | < USD 0.05 |
| Interview rate on applications scored ≥ 4.0 | track; beat cold baseline |
| Personal data in the public repo | 0 (hard gate) |

---

## 2. Key decisions (proposed — Keshav to confirm)

| # | Decision | Proposal | Why |
|---|---|---|---|
| D1 | career-ops | **Use as an engine, do not fork.** Install it beside sage; call its scripts through a thin adapter. | MIT, v1.40.0, 800+ contributors, 150+ job-source scanners, A–H evaluation with 1–5 score, CV fact gate, liveness check, tracker. Forking 300+ scripts = we maintain them forever. |
| D2 | Where personal data lives | **`memory/career/` = a private git repo as a submodule.** Until it exists: gitignored. | Sage is public. The resume has phone + email. |
| D3 | Fact source | **Reuse career-ops files:** `cv.md` + `config/cv-facts.json` + `article-digest.md`. No separate `facts.yaml`. | Their `verify-cv-facts.mjs` already gates on these. One source of truth. |
| D4 | PDF build | **Our own build for Keshav's `resume.cls`** (Tectonic). Run career-ops `verify-cv-facts.mjs` on our `.tex` before compile. | Keep your design. Reuse their gate. Spike E0-T3 checks the gate works on our `.tex`. |
| D5 | Resume variants | **3 role bases** (agentic, platform/LLMOps, forward-deployed) + small per-job tweaks. | Less to maintain than one file per job. |
| D6 | LinkedIn | **Composio job_search API only.** No scraping, no login automation. Plus career-ops `linkedin-watch.mjs` for alert emails (Gmail). | LinkedIn ToS. career-ops keeps auth-gated sources out of core for the same reason. |
| D7 | Model tiers | Haiku scouts, Sonnet analysts/writers, Opus decides + plays recruiter. Matches career-ops `spend_tier` (economy/standard/premium). | Same as rest of sage. |

---

## 3. Architecture

```
┌──────────────── plugins/gimme-job (public: code only) ─────────────────┐
│ skills: run · scan · market · evaluate · tailor · build · prep ·       │
│         track · interview · knobs · doctor                             │
│ agents: market-scout · reddit-scout · jd-analyst · gap-analyst ·       │
│         resume-writer · fact-checker · recruiter-sim · interviewer     │
│ scripts: build.sh · ats_check.py · lint_tex.py · keyword_score.py ·    │
│          market_store.py · trend.py · knobs.py · co.sh (career-ops)    │
│ hooks:  tex-autobuild · pii-push-guard · untrusted-content-tag         │
└───────┬───────────────────────────┬───────────────────────────┬────────┘
        │ MCP (Composio etc.)       │ shell adapter             │ files
        ▼                           ▼                           ▼
  LinkedIn · Glassdoor ·      career-ops engine           memory/career/ (private)
  JSearch · Indeed · Google   ~/Projects/career-ops       knobs.yaml · cv.md · cv-facts.json
  Jobs · Reddit · HN · Gmail  scan · liveness · oferta    resume/ (master.tex, variants, out/)
                              verify-cv-facts · tracker   market/ · reports/ · data/
```

`CAREER_OPS_DATA_DIR=memory/career` points career-ops at our private folder, so both tools share
one tracker, one CV, one set of reports.

---

## 4. Folder structure

```
plugins/gimme-job/
  .claude-plugin/plugin.json          # dependencies: ["brain"]
  .mcp.json                           # composio, playwright (lazy, alwaysLoad: false)
  README.md
  config/
    knobs.schema.json                 # every knob, type, default, allowed values
    knobs.default.yaml                # safe defaults (copied on first run)
    presets/                          # ottawa-junior.yaml, canada-remote.yaml, us-reach.yaml, ...
    skills-taxonomy.yaml              # canonical skill names + aliases ("LangGraph" = "langgraph")
  skills/
    run/SKILL.md        /gimme-job:run <url | "query">     full loop for one job or a search
    scan/SKILL.md       /gimme-job:scan [preset]           pull jobs from all enabled sources
    market/SKILL.md     /gimme-job:market                  trend snapshot + what changed
    evaluate/SKILL.md   /gimme-job:evaluate <job>          career-ops A–H report + our gap table
    tailor/SKILL.md     /gimme-job:tailor <job>            variant .tex from a role base
    build/SKILL.md      /gimme-job:build [file]            .tex → PDF → all gates
    prep/SKILL.md       /gimme-job:prep <job>              referral targets, answers, cover note
    track/SKILL.md      /gimme-job:track                   pipeline, follow-ups due, stale apps
    interview/SKILL.md  /gimme-job:interview <job>         likely questions from resume + JD + Glassdoor
    knobs/SKILL.md      /gimme-job:knobs [show|set|preset] view / change knobs
    doctor/SKILL.md     /gimme-job:doctor                  checks tools, MCP links, data dir, gitignore
  agents/
    market-scout.md     haiku   run source queries from knobs → market/jobs.jsonl
    reddit-scout.md     haiku   subreddits + HN "Who is hiring" → market/signals.jsonl
    jd-analyst.md       sonnet  job text → skills (taxonomy), years, pay, work auth, red flags
    gap-analyst.md      sonnet  resume vs market / vs one job → match table + gaps
    resume-writer.md    sonnet  edit bullets in .tex; reword facts only, never add
    fact-checker.md     sonnet  every claim → cv.md / cv-facts.json line, or BLOCK
    recruiter-sim.md    opus    6-second scan, "would I call?", top 5 probe questions
    interviewer.md      sonnet  mock interview from resume claims + Glassdoor reports
  scripts/
    build.sh            tectonic → out/<name>.pdf (latexmk fallback)
    ats_check.py        pdftotext: contact parsed, links real, 1 page, reading order, no glyph junk
    lint_tex.py         style knobs: ≤N tools/bullet, number in bullet, ≤2 lines, "and" not "&"
    keyword_score.py    job keywords vs PDF text → coverage %, missing list
    market_store.py     normalise + de-dupe (source id, then title+company+city fingerprint)
    trend.py            skill frequency per week → snapshots/<date>.md, delta vs last
    knobs.py            load preset → merge user knobs → validate vs schema → print effective
    co.sh               adapter: runs a career-ops script with CAREER_OPS_DATA_DIR set
    pii_guard.py        scan staged files for phone / email / PDFs
  hooks/hooks.json
  templates/resume.cls                # Trey Hunner class (keep copyright notice)
  tests/                              # pytest: lint, ats_check, knobs, market_store, pii_guard

memory/career/                        # PRIVATE (submodule or gitignored)
  knobs.yaml                          # your overrides
  cv.md · config/cv-facts.json · article-digest.md · config/profile.yml   (career-ops user layer)
  resume/
    master.tex · contact.tex
    bases/agentic.tex · platform.tex · fde.tex
    variants/<company>-<role>-<date>.tex
    out/*.pdf
  market/
    jobs.jsonl · signals.jsonl · salaries.jsonl
    snapshots/<date>.md
  reports/  data/applications.md  interview-prep/       (career-ops layout)
```

---

## 5. Knobs (the tuning mechanism)

One file controls everything. Order: `knobs.default.yaml` → preset → `memory/career/knobs.yaml` →
command flags. `/gimme-job:knobs show` prints the effective values and where each came from.

```yaml
profile:
  target_titles: ["AI Engineer", "Applied AI Engineer", "Agentic AI Engineer", "LLM Engineer",
                  "AI Platform Engineer", "Forward Deployed Engineer"]
  exclude_titles: ["Principal", "Director", "Manager", "Data Scientist", "Sales"]
  years_experience: 2
  work_auth: "PGWP"                  # drives sponsorship filters + resume line
  needs_sponsorship: false
  min_base_cad: 95000

search:
  locations: ["Ottawa, Ontario, Canada", "Toronto, Ontario, Canada", "Canada"]
  remote_regions: ["Canada", "US"]
  date_posted: week                  # day | week | month
  workplace: [remote, hybrid, onSite]
  employment: [fulltime, contractor] # fulltime | contractor | parttime | intern | temporary
  seniority: [entry, associate]      # intern | entry | associate | midSenior | director
  experience_buckets: ["0-2", "2-5"] # used by LinkedIn active-jobs (Fantastic.jobs)
  company_size: ["51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+"]
  exclude_agencies: true
  exclude_companies: []
  include_companies: ["Cohere", "Shopify", "Kinaxis", "Wealthsimple", "Thomson Reuters"]
  must_have_any: ["LLM", "agent", "RAG", "MCP", "GenAI"]
  must_not_have: ["clearance: Secret", "10+ years"]

sources:                             # turn sources on/off, cap volume
  linkedin_search:      { enabled: true,  max_results: 30 }
  linkedin_active_jobs: { enabled: false, limit: 100, time_frame: "7d" }
  jsearch:              { enabled: true,  num_pages: 2, country: ca }
  glassdoor:            { enabled: true }
  indeed:               { enabled: false, country_code: CA }
  google_jobs:          { enabled: false }
  career_ops_scan:      { enabled: true }      # Greenhouse/Lever/Ashby/Workday/BuiltIn/Job Bank Canada (free)
  reddit:               { enabled: true, subreddits: [cscareerquestionsCAD, MachineLearningJobs, LangChain, ITManagers, ExperiencedDevs], time_filter: month }
  hackernews:           { enabled: true }       # "Who is hiring" threads (career-ops scan-hn.mjs)
  gmail_linkedin_alerts:{ enabled: false }      # career-ops linkedin-watch.mjs

scoring:
  apply_threshold: 4.0               # career-ops score band
  triage_threshold: 3.5
  weights_note: "career-ops uses holistic global score; keep it"

resume:
  base: agentic                      # agentic | platform | fde
  max_pages: 1
  lint: { max_tools_per_bullet: 3, require_number: true, max_lines: 2, ban: ["&", "Startup-trained"] }
  min_keyword_coverage: 0.70

budget:
  max_usd_per_run: 0.25
  max_calls_per_run: 60
  concurrency: 3                     # Composio returned 429 at 10 parallel calls
  retry: { attempts: 4, backoff: exponential }

models: { scout: haiku, analyst: sonnet, writer: sonnet, judge: opus }

schedule:
  market_scan: "weekly"              # scheduled task; off by default
  followup_after_days: 7

privacy:
  data_dir: memory/career
  block_push_patterns: ["\\(\\d{3}\\) \\d{3}-\\d{4}", "@gmail\\.com", "\\.pdf$"]
```

---

## 6. Job sources and every filter (verified 2026-11-14 from tool schemas)

Composio toolkit `job_search` (instant account). Cost seen today: about USD 0.0002 per call.

### LinkedIn — `JOB_SEARCH_JOBS_API_LINKEDIN_SEARCH_JOBS` (used today, works)
| Filter | Values |
|---|---|
| `query` | keywords, title, company |
| `location` | text; default Worldwide |
| `date_posted` | `day` · `week` · `month` |
| `workplace_types` | `remote;hybrid;onSite` |
| `employment_types` | `contractor;fulltime;parttime;intern;temporary` |
| `experience_levels` | `intern;entry;associate;midSenior;director` |
| `organization_ids` | numeric IDs from `..._LINKEDIN_LIST_ORGANIZATIONS` |
| `token` | pagination |
Details: `JOB_SEARCH_JOBS_API_LINKEDIN_GET_JOB` (`id`) → full description, applicants, seniority.

### LinkedIn active jobs — `JOB_SEARCH_LINKEDIN_SEARCH_LIST_ACTIVE_JOBS` (Fantastic.jobs; richest filters)
`title`, `title_advanced` (boolean), `description`, `description_advanced`, `location`, `location_advanced`,
`time_frame` (`1h` `24h` `7d` `6m`), `date_posted_gte/lt`, `seniority`, `ai_experience_level` (`0-2` `2-5` `5-10` `10+`),
`ai_work_arrangement` (`Remote Solely` `Remote OK` `Hybrid` `On-site`), `ai_employment_type`,
`ai_visa_sponsorship` (`only`/`exclude`), `ai_education`, `ai_taxonomies_a` (Technology, Software, Data & Analytics…),
`has_salary`, `direct_apply`, `organization`, `exclude_organization`, `organization_slug`, `organization_size`
(`1` … `10001+`), `organization_headcount_gte/lt`, `organization_industry`, `organization_agency` (`exclude`),
`source` (`linkedin` `wellfound` `ycombinator`), `exclude_ats_duplicate`, `description_format`, `limit` (≤1000), `cursor`.
**Note:** covers Wellfound + YC too. Check price before turning on (not in today's price list).

### JSearch — `JOB_SEARCH_JSEARCH_SEARCH_JOBS` (Google for Jobs aggregate)
`query`, `country` (`ca`), `language`, `date_posted` (`all` `today` `3days` `week` `month`), `work_from_home`,
`employment_types` (`FULLTIME` `CONTRACTOR` `PARTTIME` `INTERN`), `job_requirements`
(`under_3_years_experience` `more_than_3_years_experience` `no_experience` `no_degree`), `radius` (km),
`exclude_job_publishers`, `num_pages` (≤20, 1 credit each), `fields`, `cursor`.
Salary: `JOB_SEARCH_JSEARCH_GET_ESTIMATED_SALARY` — `job_title`, `location`, `location_type`,
`years_of_experience` (`LESS_THAN_ONE` `ONE_TO_THREE` `FOUR_TO_SIX` …).

### Glassdoor — `JOB_SEARCH_GLASSDOOR_REALTIME_*`
Jobs search: `query`, `city`, `location_id`, `company`, `industry`, `job_function`, `job_type`, `seniority_level`,
`min_salary`, `max_salary`, `date_posted`, `remote_only`, `easy_apply_only`, `company_size`, `company_rating`, `sort`, `page_cursor`.
Also: company interviews (`company_id`, `sort`: `DATE` `DIFFICULTY` …), interview details, salaries, reviews, benefits.

### Indeed — `JOB_SEARCH_JOBS_API_INDEED_SEARCH_JOBS`
`query`, `location`, `country_code` (`CA`), `radius`, `radius_type` (`km`/`miles`), `sort_type` (`relevance`/`date`), `token`.

### Google Jobs — `JOB_SEARCH_GOOGLE_JOBS_*`
`LIST_JOBS` (`query`, `include`, `language`, `location`, `salary_range`), plus ready-made lists:
`BY_TECHNOLOGY_STACK` (`technologies`, `location`), `BY_EXPERIENCE`, `BY_COMPANY_SIZE`, `BY_MINIMUM_SALARY`,
`ENTRY_LEVEL_JOBS`, `REMOTE_JOBS`, `RECENT_JOBS`, `STARTUP_JOBS`, `VISA_SPONSORSHIP_JOBS`, `HIGH_PAYING_JOBS`.

### Also in the toolkit (not checked yet)
ZipRecruiter search + salary, Bing jobs, Xing, Remote jobs, Daily International Jobs (`..._STATISTICS` with
`field` = `workPlace` / `industry` → market share counts), salary API (`JOBS_API_SALARY_*`).

### career-ops built-in scanners (free, no auth, zero tokens)
Greenhouse, Lever, Ashby, Workday, SmartRecruiters, Workable, BambooHR, iCIMS, Taleo, SuccessFactors,
**BuiltIn**, **Job Bank Canada** (`jobbankca`), Hacker News, RemoteOK, Remotive, WeWorkRemotely, Wellfound-style
boards, and ~130 more under `providers/`. Best for tracking named companies (Cohere, Shopify, Kinaxis…).

### Signals (not jobs)
Reddit `REDDIT_SEARCH_ACROSS_SUBREDDITS` (`search_query`, `sort`, `time_filter`, `limit` ≤100, `restrict_sr`, `after`)
and `REDDIT_RETRIEVE_POST_COMMENTS` (`article`, `sort`, `depth`, `limit`).

---

## 7. More MCPs to make research stronger

| Tier | MCP / tool | What it adds | Status |
|---|---|---|---|
| Now | Composio `job_search` + `reddit` | jobs, salaries, interviews, signals | connected |
| Now | **Gmail** | LinkedIn alert emails → career-ops `linkedin-watch`; recruiter replies → `reply-watch` | connected in this account |
| Now | **Exa** (already in researcher) | company research, eng blogs, funding news | in sage |
| Now | **GitHub MCP** | evidence links for claims; company repos / tech stack | in sage |
| Next | **Playwright MCP** | read career pages, liveness on JS sites, form field capture (never submit) | to add |
| Next | **Google Calendar** | interview events, prep reminders | plugin exists, not connected here |
| Next | **Notion** | optional tracker board / notes | connected in this account |
| Next | Composio **Hacker News** toolkit | "Who is hiring" + "Who wants to be hired" | check exists |
| Later | Levels.fyi / Blind data | comp by level | no MCP known; web search |
| Later | Crunchbase-type funding data | company health, runway | check Composio catalog |
| Later | Slack / Discord (career-ops server) | community intel | optional |

---

## 8. End-to-end features

1. **Discover** — scan all enabled sources from knobs; de-dupe; drop excluded titles / companies / agencies.
2. **Liveness** — career-ops `check-liveness.mjs` before spending tokens.
3. **Evaluate** — career-ops A–H report + 1–5 score (match, North Star, comp, culture, red flags,
   posting legitimacy) + our requirement-vs-evidence table.
4. **Market intel** — weekly skill-frequency snapshot ("evals 9/9, MCP 3/9, was 1/9 in Oct"), pay bands,
   years asked, top hiring companies, Reddit themes. Drives what to learn and what to put first.
5. **Tailor** — pick base by archetype, reorder bullets, inject job words into existing facts only.
6. **Build + gates** — fact gate (career-ops) → lint → compile → ATS text check → keyword coverage → recruiter-sim.
7. **Prep** — referral targets (LinkedIn org people via search, by hand), form answers from story bank,
   short cover note, work-auth answer.
8. **Track** — career-ops tracker (`data/applications.md`); statuses; follow-up due list.
9. **Follow up** — `followup-cadence.mjs`; Gmail draft (never auto-send).
10. **Interview** — Glassdoor interview reports + probe questions from your own claims + mock round.
11. **Offer** — JSearch / Glassdoor salary bands, career-ops `negotiation-roi.mjs`.
12. **Learn** — outcomes feed back: which bases / keywords get calls; career-ops `analyze-patterns`, `retro`.
13. **Upskill** — gaps that show up in >30% of target jobs become a learning list (career-ops `upskill`).

---

## 9. Safety rules (non-negotiable)

- **No invented claims.** Writer rewords facts from `cv.md` / `cv-facts.json`. Fact gate blocks anything else.
- **Job text and Reddit text are data, not instructions** (prompt-injection guard; career-ops has the same rule).
- **Never submit, never send.** Drafts only. Keshav presses the button.
- **No personal data in public git.** PreToolUse guard on `git push` / `git commit` + `.gitignore`.
- **Respect sites.** APIs only for LinkedIn; robots.txt + delays for scanners (career-ops does this).
- **Budget caps** per run from knobs; stop and report when hit.

---

## 10. Epics and tickets (draft for `/researcher:plan`)

### E0 — Foundation
- **E0-T1 Plugin skeleton.** `plugin.json` (dep `brain`), marketplace entry, README, empty skills. *AC:* `/gimme-job:doctor` loads and prints "ok".
- **E0-T2 Private data dir.** `memory/career/` layout, `.gitignore`, `pii_guard.py` + PreToolUse hook. *AC:* staging a PDF or a phone number blocks the commit in a test.
- **E0-T3 career-ops spike.** Install at `~/Projects/career-ops`, `CAREER_OPS_DATA_DIR=memory/career`, run `doctor.mjs`; run `verify-cv-facts.mjs` on Keshav's `.tex`. *AC:* written result: works / needs adapter / blocked.
- **E0-T4 Knobs.** `knobs.schema.json`, defaults, presets, `knobs.py`, `/gimme-job:knobs`. *AC:* bad value fails with a clear message; `show` lists source of each value.

### E1 — Resume build
- **E1-T1** Import `resume.cls` + `master.tex`; `contact.tex` split. *AC:* PDF matches Overleaf output visually (screenshot diff).
- **E1-T2** `build.sh` (Tectonic) + PostToolUse hook on `.tex` edits. *AC:* edit → PDF in < 20 s.
- **E1-T3** `ats_check.py`. *AC:* catches hidden `\ats` text mismatch, broken links, >1 page.
- **E1-T4** `lint_tex.py` with lint knobs. *AC:* flags current resume's known issues (tool soup, "&").
- **E1-T5** Fact gate wired (from E0-T3 result).

### E2 — Market intel
- **E2-T1** `market-scout` + LinkedIn search/get via Composio, concurrency 3, retry on 429. *AC:* 30 jobs → `jobs.jsonl`.
- **E2-T2** JSearch + Glassdoor + salary estimate. 
- **E2-T3** career-ops scan adapter for tracked companies.
- **E2-T4** `market_store.py` de-dupe + `skills-taxonomy.yaml` + `jd-analyst`.
- **E2-T5** `trend.py` snapshot + `/gimme-job:market`. *AC:* snapshot shows counts and delta vs last week.
- **E2-T6** `reddit-scout` + HN.
- **E2-T7** Weekly scheduled task (off by default).

### E3 — Evaluate + tailor
- **E3-T1** `/gimme-job:evaluate` → career-ops `oferta` + gap table.
- **E3-T2** Role bases (agentic / platform / fde).
- **E3-T3** `resume-writer` + `fact-checker` loop.
- **E3-T4** `keyword_score.py` + `recruiter-sim`.
- **E3-T5** `/gimme-job:run` end-to-end on one URL.

### E4 — Apply + track
- **E4-T1** Tracker via career-ops; `/gimme-job:track`.
- **E4-T2** Prep pack (answers, referral list, cover note).
- **E4-T3** Gmail: LinkedIn alerts in, follow-up drafts out (drafts only).

### E5 — Interview + learn
- **E5-T1** Glassdoor interview reports + `interviewer` mock.
- **E5-T2** Outcome feedback → base / keyword stats; upskill list.
- **E5-T3** Offer + salary bands.

---

## 11. Open questions for Keshav

1. **career-ops:** engine beside sage (D1), or skip it and build only what we need? Runtime: Node.js on your Mac — OK?
2. **Private repo:** will you create `sage-memory` (private) so `memory/career/` becomes a submodule? (I can't create repos from here.)
3. **Paid sources:** OK to turn on LinkedIn active-jobs (Fantastic.jobs) + JSearch after we check prices? Monthly cap?
4. **Gmail:** OK to read LinkedIn alert + recruiter emails (read + drafts only)?
5. **Markets:** Canada only, or US remote too (changes work-auth + pay knobs)?
6. **Scope of v1:** E0–E3 first (build + market + tailor), E4–E5 later?

---

## 12. Research behind this plan

- career-ops repo read 2026-11-14: README, ARCHITECTURE.md, `modes/_shared.md` (scoring + spend tiers),
  `modes/oferta.md` (A–H blocks), `modes/latex.md` (Tectonic + fact gate), `providers/` (150+ scanners incl.
  `jobbankca`, `builtin`), `templates/portals.example.yml`, `.claude-plugin/plugin.json` (it ships as a Claude Code plugin).
- Composio tool schemas pulled 2026-11-14 (section 6).
- Live market data: `memory/resume/report/keshav-arri-2026-11-14.md` (9 LinkedIn JDs, Reddit, web).
