#!/usr/bin/env python3
"""De-dupe + knob filters + liveness → runs/<id>/jobs.jsonl and funnel counts.

  dedupe.py [--run ID] [--no-liveness] [--preset NAME]
Steps: source-id de-dupe → fingerprint de-dupe (title+company+city) → hard filters from knobs
(excluded titles/companies/agencies, must_have_any, must_not_have, workplace, age) → liveness (HTTP).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts import knobs as knobs_mod  # noqa: E402

AGENCY = re.compile(r"\b(staffing|recruit(ing|ment)|talent solutions|consulting group|insight global|robert half|randstad|"
                    r"teksystems|hays|adecco|kforce|beacon hill|jobgether)\b", re.I)
AGE_DAYS = {"day": 1, "week": 7, "month": 31}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def fingerprint(j: dict) -> str:
    city = norm((j.get("location") or "").split(",")[0].split("|")[0])
    title = re.sub(r"\b(sr|senior|jr|junior|i{1,3}|iv)\b", "", norm(j.get("title", "")))
    return hashlib.sha1(f"{' '.join(title.split())}|{norm(j.get('company', ''))}|{city}".encode()).hexdigest()[:16]


def _richer(a: dict, b: dict) -> dict:
    keep, other = (a, b) if len(a.get("description") or "") >= len(b.get("description") or "") else (b, a)
    merged = dict(keep)
    for k, v in other.items():
        if merged.get(k) in (None, "", [], {}) and v not in (None, "", [], {}):
            merged[k] = v
    merged["sources"] = sorted(set(a.get("sources", [a.get("source")]) + b.get("sources", [b.get("source")])))
    return merged


def dedupe(rows: list[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for r in rows:
        r.setdefault("sources", [r.get("source")])
        key = r.get("id") or r.get("url")
        by_id[key] = _richer(by_id[key], r) if key in by_id else r
    by_fp: dict[str, dict] = {}
    for r in by_id.values():
        fp = fingerprint(r)
        r["fingerprint"] = fp
        by_fp[fp] = _richer(by_fp[fp], r) if fp in by_fp else r
    return list(by_fp.values())


def drop_reason(j: dict, k: dict) -> str:
    p, s = k["profile"], k["search"]
    title = j.get("title", "")
    text = f"{title}\n{j.get('description', '')}".lower()
    if any(x.lower() in title.lower() for x in p["exclude_titles"]):
        return "excluded title"
    if any(x.lower() == (j.get("company") or "").lower() for x in s["exclude_companies"]):
        return "excluded company"
    if s["exclude_agencies"] and AGENCY.search(j.get("company") or ""):
        return "agency"
    if s["must_have_any"] and j.get("description") and not any(w.lower() in text for w in s["must_have_any"]):
        return "missing must_have_any"
    if any(w.lower() in text for w in s["must_not_have"]):
        return "must_not_have hit"
    if j.get("workplace") and j["workplace"] not in s["workplace"]:
        return "workplace"
    if p["needs_sponsorship"] and re.search(r"(no|not|unable to)[^.]{0,40}sponsor", text):
        return "no sponsorship"
    if j.get("posted_at"):
        try:
            dt = datetime.fromisoformat(j["posted_at"].replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc) - dt).days > max(AGE_DAYS[s["date_posted"]], k["ranking"]["fresh_days"]):
                return "too old"
        except ValueError:
            pass
    return ""


DEAD = re.compile(r"no longer (accepting|available)|position (has been )?filled|job (is )?closed|this job has expired|"
                  r"posting (is )?closed|not accepting applications", re.I)


def liveness(j: dict, http) -> str:
    try:
        r = http.get(j["url"], ok=(200, 301, 302))
    except Exception as e:
        msg = str(e)
        return "dead" if re.search(r"HTTP (404|410)", msg) else "unknown"
    return "dead" if DEAD.search(r.text[:200000]) else "live"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run")
    ap.add_argument("--preset")
    ap.add_argument("--no-liveness", action="store_true")
    a = ap.parse_args(argv)
    k, _ = knobs_mod.load(a.preset)
    rd = common.run_dir(a.run, k)
    raw = list(common.read_jsonl(rd / "jobs.raw.jsonl"))
    uniq = dedupe(raw)
    kept, dropped = [], {}
    for j in uniq:
        why = drop_reason(j, k)
        if why:
            dropped[why] = dropped.get(why, 0) + 1
        else:
            kept.append(j)
    live_counts = {"live": 0, "dead": 0, "unknown": 0, "skipped": 0}
    if not a.no_liveness:
        from scripts.providers._http import Http
        http = Http(retries=1, min_delay=0.5)
        final = []
        for j in kept:
            st = liveness(j, http)
            j["liveness"] = st
            live_counts[st] += 1
            if st != "dead":
                final.append(j)
            common.append_jsonl(rd / "ledger.jsonl", {"ts": time.time(), "tool": "http", "source": "liveness",
                                                     "status": "ok" if st != "unknown" else "failed",
                                                     "reason": "" if st != "unknown" else "unreachable"})
        kept = final
    else:
        live_counts["skipped"] = len(kept)
    common.write_jsonl(rd / "jobs.jsonl", kept)
    by_source: dict[str, int] = {}
    for r in raw:
        by_source[r.get("source", "?")] = by_source.get(r.get("source", "?"), 0) + 1
    funnel = {"found": len(raw), "unique": len(uniq), "after_filters": len(uniq) - sum(dropped.values()),
              "dropped": dropped, "liveness": live_counts, "kept": len(kept), "by_source": by_source}
    common.write_json(rd / "funnel.json", funnel)
    print(json.dumps(funnel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
