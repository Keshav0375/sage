# Mail worker report, run 20261115-001544

Status: DONE (query ran; zero matching alert emails; zero job records added)

## Query
`from:(jobalerts-noreply@linkedin.com OR alert@indeed.com OR noreply@glassdoor.com) newer_than:14d`

Gmail tool used: `mcp__claude_ai_Gmail__search_threads` (read-only). Gmail tools now connected in this session. The earlier report in this folder (FAILED, no Gmail tool) is replaced by this one.

## Results
- The exact query returned no threads.
- Check with `from:jobalerts-noreply@linkedin.com` (no date limit): no threads.
- Check with `from:indeed` or `from:glassdoor` over 90 days: 18 threads, all from `noreply@glassdoor.com`, `info@glassdoor.com`, or Glassdoor Community. Dates 2026-10-06 to 2026-10-27. All are outside the 14-day window, so none were read or saved. Not used for this run.
- Other LinkedIn mail in the window (social notifications, "Complete your profile" from linkedin@em.linkedin.com) is not a job alert. Not read.

## Steps run
- Saved an empty batch: `memory/resume/runs/20261115-001544/mail/alerts.json` (`[]`).
- Ran `plugins/gimme-job/scripts/inbox_scan.py --json-messages ... --run 20261115-001544`. Output: `{"run": "20261115-001544", "jobs": 0, "by_source": {}}`, exit 0.

## Emails read
0

## Job URLs added
none

## Next step
- No alert mail in the last 14 days from the three senders. If alerts are expected, check that the alerts are enabled on each site and that they go to this Gmail account. Or widen the window (for example `newer_than:45d`) and rerun. Keshav decides whether to widen.
