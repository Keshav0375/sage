#!/usr/bin/env python3
"""Discovery: find ATS + new employers, keep the source list healthy (zero LLM tokens).

  discover.py ats URL [URL ...]          careers URL → ATS name + slug (first scanner whose detect() claims it,
                                          else fetch the page and look for ATS links/embeds)
  discover.py companies [--run ID]       employers seen in scan results not yet in companies.toml (+ detected ATS)
  discover.py audit                      check every companies.toml careers_url still resolves; flag moved ATS
  discover.py dead [--run ID] [--after N] boards/targets that returned 0 jobs N scans in a row → disable list
  discover.py robots HOST|URL [...]      robots.txt verdict + crawl delay per host (cached in the Http layer)
company_funded (funding news → likely hiring) runs on the agent side through Exa (see agents/evidence-worker.md).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts.providers import _registry  # noqa: E402
from scripts.providers._http import Http  # noqa: E402

COMPANIES = common.PLUGIN / "config" / "companies.toml"
ATS_HINTS = [
    (r"boards\.greenhouse\.io/(?:embed/job_board\?for=)?([\w-]+)|job-boards(?:\.eu)?\.greenhouse\.io/([\w-]+)", "greenhouse"),
    (r"jobs\.(?:eu\.)?lever\.co/([\w.-]+)", "lever"),
    (r"jobs\.ashbyhq\.com/([\w.%-]+)", "ashby"),
    (r"([\w-]+)\.wd\d+\.myworkdayjobs\.com", "workday"),
    (r"(?:careers|jobs)\.smartrecruiters\.com/([\w-]+)", "smartrecruiters"),
    (r"apply\.workable\.com/([\w-]+)", "workable"),
    (r"([\w-]+)\.recruitee\.com", "recruitee"),
    (r"([\w-]+)\.bamboohr\.com", "bamboohr"),
    (r"([\w-]+)\.teamtailor\.com", "teamtailor"),
    (r"([\w-]+)\.jobs\.personio\.(?:de|com)", "personio"),
    (r"([\w-]+)\.breezy\.hr", "breezy"),
    (r"([\w-]+)\.icims\.com", "icims"),
    (r"([\w-]+)\.taleo\.net", "taleo"),
    (r"jobs\.jobvite\.com/([\w-]+)", "jobvite"),
    (r"ats\.rippling\.com/([\w-]+)", "rippling"),
    (r"([\w-]+)\.pinpointhq\.com", "pinpoint"),
    (r"([\w-]+)\.dayforcehcm\.com", "dayforce"),
]


def detect_ats(url: str, http: Http | None = None) -> dict:
    hit = _registry.detect(url)
    if hit:
        p, t = hit
        return {"url": url, "ats": p.name, "slug": t.slug, "how": "detect"}
    http = http or Http(retries=1)
    try:
        html = http.get_text(url)
    except Exception as e:
        return {"url": url, "ats": "", "slug": "", "how": f"fetch failed: {e}"}
    for rx, name in ATS_HINTS:
        m = re.search(rx, html)
        if m:
            slug = next((g for g in m.groups() if g), "")
            return {"url": url, "ats": name, "slug": slug, "how": "page link"}
    return {"url": url, "ats": "local-parser" if "JobPosting" in html else "", "slug": "", "how": "no ATS link"}


def known_companies() -> list[dict]:
    return tomllib.load(open(COMPANIES, "rb")).get("company", []) if COMPANIES.exists() else []


def cmd_companies(run: str | None) -> list[dict]:
    rd = common.run_dir(run)
    have = {c["name"].lower() for c in known_companies()}
    seen = Counter()
    sample: dict[str, dict] = {}
    for j in common.read_jsonl(rd / "jobs.jsonl"):
        name = (j.get("company") or "").strip()
        if name and name.lower() not in have:
            seen[name] += 1
            sample.setdefault(name, j)
    out = []
    for name, n in seen.most_common(50):
        j = sample[name]
        out.append({"name": name, "jobs": n, "example_url": j["url"], "source": j.get("source"),
                    "ats_guess": detect_ats(j["url"])["ats"] if j.get("source") in _registry.all_providers() else ""})
    return out


def cmd_audit() -> list[dict]:
    http = Http(retries=1)
    out = []
    for c in known_companies():
        url = c.get("careers_url")
        if not url:
            out.append({"name": c["name"], "status": "no careers_url"})
            continue
        try:
            r = http.get(url, ok=(200, 301, 302))
            d = detect_ats(url, http)
            moved = c.get("ats") and d["ats"] and d["ats"] != c["ats"]
            out.append({"name": c["name"], "status": "moved" if moved else "ok", "ats_now": d["ats"], "http": r.status})
        except Exception as e:
            out.append({"name": c["name"], "status": "broken", "error": str(e)[:120]})
    return out


def cmd_dead(after: int) -> list[str]:
    streak: Counter = Counter()
    for rd in sorted(common.runs_dir().glob("2*")):
        st = common.read_json(rd / "scan-status.json", {}) or {}
        for t in st.get("targets", []):
            streak[t["target"]] = streak[t["target"]] + 1 if t["jobs"] == 0 else 0
    return sorted(t for t, n in streak.items() if n >= after)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["ats", "companies", "audit", "dead", "robots"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--run")
    ap.add_argument("--after", type=int, default=3)
    a = ap.parse_args(argv)
    if a.cmd == "ats":
        out = [detect_ats(u) for u in a.args]
    elif a.cmd == "companies":
        out = cmd_companies(a.run)
    elif a.cmd == "audit":
        out = cmd_audit()
    elif a.cmd == "dead":
        out = cmd_dead(a.after)
    else:
        http = Http()
        out = []
        for h in a.args:
            url = h if h.startswith("http") else f"https://{h}/"
            out.append({"url": url, "allowed": http.allowed(url), "crawl_delay": http._delay.get(url.split("/")[2])})
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
