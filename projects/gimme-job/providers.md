# gimme-job — source catalogue (157 sources)

Built in-house (Python standard library). The list of what to port comes from career-ops v1.40.0 (MIT):
144 provider modules + 3 extra scan scripts (`dayforce`, `topdev`, `interamt`), minus 2 that upstream
retired (`echojobs`, `torre`) = **145 scanners**. Plus **11 API sources** (Composio `job_search`) and **1 inbox source** (Gmail).

Every scanner follows `scripts/providers/_base.py` (section 6 of plan.md). One ticket = one family of 3–6 scanners, each with a recorded-fixture test.
Knobs decide which waves run (`sources.ats_scanners.waves`). Default: `[W1, W2, W3]`.

| Wave | Count | Default | Scanners |
|---|---|---|---|
| **W1** Core: Canada + global tech | 20 | on | greenhouse, lever, ashby, workday, smartrecruiters, workable, recruitee, bamboohr, teamtailor, personio, builtin, jobbankca, hackernews, remoteok, remotive, weworkremotely, himalayas, jobicy, getro, dayforce |
| **W2** Enterprise ATS (banks, telcos, big tech) | 25 | on | icims, taleo, successfactors, oraclecloud, phenom, eightfold, jobvite, dover, gem, rippling, breezy, jazzhr, pinpoint, comeet, polymer, ultipro, paylocity, adp-workforcenow, adp-myjobs, avature, pageup, csod, radancy, peoplesoft, jibeapply |
| **W3** AI / startup / remote + big-tech direct | 23 | on | agentic-jobs, a16z-speedrun-talent, consider, startup-jobs, generalist-world, 4dayweek, remote-com, workingnomads, nodesk, jobspresso, themuse, pythonorg, cryptocurrencyjobs, wp-job-manager, sitemap, telegram-channel, local-parser, amazon, apple, google, ibm, atlassian, notion |
| **W4** Small / mid ATS | 25 | off | hibob, deel, factorial, homerun, hirehive, join, keka, zoho-recruit, trakstar, taleez, prevueaps, clearcompany, applicantpro, turbohire, darwinbox, collage, flowxtra, talentlink, eploy, rexx, softgarden, beesite, inrecruiting, hiringroom, neogov |
| **W5** Regional boards (EU, LatAm, Asia, Africa) | 35 | off | arbeitnow, arbeitsagentur, bulldogjob, careerviet, computrabajo, germantechjobs, getonbrd, glints, gupy, itviec, jobscz, jobstreet, justjoin, kalibrr, landingjobs, larajobs, magneto, manfred, mycareersfuture, nofluffjobs, occ, platsbanken, pracecz, remotli, senjob, solidjobs, techinasia, thehub, vdab, wttj, yourator, joinup, higheredjobs, tes, topdev |
| **W6** Single-company non-tech, public sector, K-12 | 17 | off | aldi-nord, alibaba, bwi, dassault, deutschebahn, garena, hecklerkoch, meituan, mokahr, feishu-jobs, rheinmetall, tencent, tkms, applitrack, redrover, schoolspring, interamt |
| **Scanners total** | **145** | 68 on | |

### API sources (Composio `job_search`, run by `source-worker`)
| # | Source | Tool | Default |
|---|---|---|---|
| 1 | LinkedIn search | `JOB_SEARCH_JOBS_API_LINKEDIN_SEARCH_JOBS` + `..._GET_JOB` | on |
| 2 | LinkedIn active jobs (also Wellfound, YC) | `JOB_SEARCH_LINKEDIN_SEARCH_LIST_ACTIVE_JOBS` | off (price unchecked) |
| 3 | JSearch (Google for Jobs) | `JOB_SEARCH_JSEARCH_SEARCH_JOBS` | on |
| 4 | Glassdoor | `JOB_SEARCH_GLASSDOOR_REALTIME_JOBS_SEARCH` | on |
| 5 | Indeed | `JOB_SEARCH_JOBS_API_INDEED_SEARCH_JOBS` | off |
| 6 | Google Jobs | `JOB_SEARCH_GOOGLE_JOBS_LIST_JOBS` (+ BY_* lists) | off |
| 7 | ZipRecruiter | `JOB_SEARCH_ZIPRECRUITER_SEARCH_JOBS` | off |
| 8 | Bing jobs | `JOB_SEARCH_JOBS_API_BING_SEARCH_JOBS` | off |
| 9 | Xing | `JOB_SEARCH_JOBS_API_XING_SEARCH_JOBS` | off |
| 10 | Remote jobs | `JOB_SEARCH_REMOTE_JOBS_LIST_JOBS` | off |
| 11 | Daily International Jobs | `JOB_SEARCH_DAILY_INTERNATIONAL_JOBS_SEARCH` (+ `_STATISTICS`) | off |

### Inbox source
| 12 | Gmail LinkedIn job alerts (read only) | Gmail MCP | on |

### Candidate Canadian additions (not in career-ops; verify public feed + robots.txt first)
GC Jobs (federal public service), Talent.com, Eluta.ca. One spike ticket checks each; add only if a public, no-auth feed exists.

**Total: 145 + 11 + 1 = 157 sources.**
