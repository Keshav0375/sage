# script-worker: dedupe and cards (run 20261115-001544)

Status: DONE

## 1. dedupe.py

Command: `python3 plugins/gimme-job/scripts/dedupe.py --run 20261115-001544` (exit 0)

Output:

```json
{"found": 1681, "unique": 1269, "after_filters": 406, "dropped": {"missing must_have_any": 48, "excluded title": 716, "too old": 90, "agency": 9}, "liveness": {"live": 244, "dead": 1, "unknown": 161, "skipped": 0}, "kept": 405, "by_source": {"hackernews": 3, "cryptocurrencyjobs": 51, "atlassian": 280, "google": 11, "generalist-world": 51, "pythonorg": 20, "remoteok": 90, "remote-com": 55, "workingnomads": 34, "weworkremotely": 68, "amazon": 300, "himalayas": 152, "ibm": 300, "jobbankca": 48, "jsearch": 38, "linkedin": 180}}
```

Funnel (from `memory/resume/runs/20261115-001544/funnel.json`): found 1681, unique 1269, after filters 406, kept 405.

Liveness: live 244, dead 1, unknown 161, skipped 0.

Note: 161 unknown liveness results. No page-worker was spawned.

## 2. cards.py tools

Command: `python3 plugins/gimme-job/scripts/cards.py tools --run 20261115-001544 > memory/resume/runs/20261115-001544/card1-tools.md` (exit 0, 41 lines)

## 3. cards.py jobs

Command: `python3 plugins/gimme-job/scripts/cards.py jobs --run 20261115-001544 > memory/resume/runs/20261115-001544/card2-jobs.md` (exit 0, 24 lines)

## Knobs

No knobs changed.
