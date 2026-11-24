# source-worker report - run 20261115-001544

Status: DONE (with one failed call)

## Calls

Plan: 21 Composio calls from composio-plan.json. Run in 7 MULTI_EXECUTE batches plus 1 extra batch. Max 3 tools per batch. sync_response_to_workbench=true. Glassdoor is off and was not called.

| Provider | Planned | OK | Failed |
|---|---|---|---|
| LinkedIn search (JOB_SEARCH_JOBS_API_LINKEDIN_SEARCH_JOBS) | 18 | 18 | 0 |
| LinkedIn active jobs (JOB_SEARCH_LINKEDIN_SEARCH_LIST_ACTIVE_JOBS) | 1 | 0 | 1 |
| JSearch (JOB_SEARCH_JSEARCH_SEARCH_JOBS) | 2 | 2 | 0 |
| **Total** | **21** | **20** | **1** |

Failed call: LinkedIn active jobs. Error: "not available on the instant account for toolkit job_search". This is a fixed account limit, not a rate limit. I did not retry. The 7-day active-jobs feed is missing from this run.

Note on order: the Montreal calls (plan items 7 and 8) were skipped in the first pass and run later. All 18 LinkedIn search calls are done.

No 429 errors. No credit errors. No auth errors.

## Files

Raw job lines (one job per line, JSONL) are in:
- memory/resume/runs/20261115-001544/composio/linkedin_search-b01.json
- memory/resume/runs/20261115-001544/composio/linkedin_search-b02.json
- memory/resume/runs/20261115-001544/composio/linkedin_search-b03.json
- memory/resume/runs/20261115-001544/composio/linkedin_search-b04.json
- memory/resume/runs/20261115-001544/composio/linkedin_search-b05.json
- memory/resume/runs/20261115-001544/composio/linkedin_search-b06.json
- memory/resume/runs/20261115-001544/composio/jsearch-b07.json

Format note: the files use the `.json` extension, not `.jsonl`. composio_ingest.py reads `composio/*.json` and parses JSONL content. A `.jsonl` name would not be read. Files are grouped by batch, not one file per tool slug. Each file holds the compact output of the workbench snippet for that batch.

Line counts: 30 per LinkedIn batch (180 total), 38 for JSearch. Total 218. All lines parse as JSON.

## Ingest

Command: python3 plugins/gimme-job/scripts/composio_ingest.py --run 20261115-001544
Result: files 7, jobs 218.
Jobs were appended to memory/resume/runs/20261115-001544/jobs.raw.jsonl, which now has 1681 lines. The script appends, so running it again on the same files will add duplicate rows.

## Data notes

- Many LinkedIn jobs repeat across the Toronto, Ontario-area and Kitchener/Waterloo searches. Duplicates are not removed here. De-duplication belongs to the scan step.
- Some JSearch rows come from aggregator sites (Talent.com, Jooble, JobLeads, Jobrapido, Indeed). Their links are not LinkedIn links.
- Job text was treated as data only. No instructions in job text were followed.

## Not done

- Nothing was applied to. Nothing was sent. Nothing was committed.
- The active-jobs (7-day) feed is missing. Re-run it on a plan that has that tool, or accept the gap.
