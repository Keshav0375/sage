{"run": "20261115-001544", "targets": 25, "ok": 16, "failed": 9, "jobs": 1460, "file": "/Users/keshav/Projects/sage/memory/resume/runs/20261115-001544/jobs.raw.jsonl"}

## Summary (script-worker)
Command: python3 plugins/gimme-job/scripts/scan.py --waves --run 20261115-001544
Status: SCANNED. Exit code 0. Targets 25, OK 16, failed 9, jobs 1460.
Jobs per wave (from scan-status.json, mapped with scan.py --list):
- W1: 358 (jobbankca, himalayas, remoteok, weworkremotely). Failed: jobicy, remotive, hackernews.
- W2: 0 (no board-wide targets in this run).
- W3: 1102 (amazon, ibm, atlassian, remote-com, cryptocurrencyjobs, generalist-world, workingnomads, pythonorg, google). Failed: 4dayweek, agentic-jobs, jobspresso, nodesk, themuse, startup-jobs.
- Total: 1460.
Failed scanners: 9. Top failure reasons:
1. robots.txt disallows (4): 4dayweek, agentic-jobs, jobspresso, remotive.
2. HTTP error (3): jobicy HTTP 400, themuse HTTP 403, startup-jobs HTTP 404.
3. Parse or URL error (2): hackernews "Invalid IPv6 URL", nodesk "bad feed: undefined entity".
Note: raw file jobs.raw.jsonl has 1463 rows. The extra 3 rows come from hackernews, which scan-status.json marks as failed.
Raw output: memory/resume/runs/20261115-001544/jobs.raw.jsonl
Status file: memory/resume/runs/20261115-001544/scan-status.json
