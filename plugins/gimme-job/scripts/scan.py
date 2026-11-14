#!/usr/bin/env python3
"""Scan job sources (zero LLM tokens) → runs/<id>/jobs.raw.jsonl, with every HTTP call in the ledger.

Modes:
  scan.py --waves [W1 W2 ...]          board-wide scanners in those waves + tenant scanners for companies.toml
  scan.py --full-ats                   every company in companies.toml (all open roles)
  scan.py --company NAME               one company from companies.toml
  scan.py --url URL                    one careers URL (auto-detects the ATS) or one job URL
  scan.py --provider NAME [--slug S] [--careers-url U] [--query Q]   one scanner
  scan.py --list                       list scanners by wave
Common: --preset NAME, --run ID (default: new run), --max-jobs N, --dry-run
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import sys
import time
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts import knobs as knobs_mod  # noqa: E402
from scripts.providers import _registry  # noqa: E402
from scripts.providers._base import Context, ProviderError, Target  # noqa: E402
from scripts.providers._http import Http  # noqa: E402

COMPANIES = common.PLUGIN / "config" / "companies.toml"


def load_companies() -> list[dict]:
    if not COMPANIES.exists():
        return []
    data = tomllib.load(open(COMPANIES, "rb"))
    return [c for c in data.get("company", []) if c.get("enabled", True)]


def target_for_company(c: dict) -> tuple[object, Target] | None:
    if c.get("ats") and c.get("slug"):
        try:
            p = _registry.get(c["ats"])
        except KeyError:
            return None
        t = p.detect(c.get("careers_url", "")) if c.get("careers_url") else None
        t = t or Target()
        t.company, t.slug = c["name"], c["slug"]
        t.careers_url = c.get("careers_url", t.careers_url)
        return p, t
    if c.get("careers_url"):
        hit = _registry.detect(c["careers_url"])
        if hit:
            p, t = hit
            t.company = c["name"]
            return p, t
        try:
            return _registry.get("local-parser"), Target(company=c["name"], careers_url=c["careers_url"])
        except KeyError:
            return None
    return None


def board_target(k: dict, provider_name: str) -> Target:
    s = k["search"]
    return Target(query=" OR ".join(s["keywords"]), location=s["locations"][0] if s["locations"] else "",
                  options={"keywords": s["keywords"], "locations": s["locations"], "countries": s["countries"],
                           "date_posted": s["date_posted"], "provider": provider_name})


def run_one(p, t: Target, k: dict, ledger: Path, max_jobs: int) -> tuple[str, list[dict], str, int]:
    calls = [0]

    def on_call(ev: dict) -> None:
        calls[0] += 1
        common.append_jsonl(ledger, {"ts": ev["ts"], "tool": "http", "source": f"scanner:{p.name}",
                                     "status": ev["status"], "reason": "" if ev["status"] == "ok" else ev["detail"],
                                     "host": ev["host"]})
    ctx = Context(http=Http(on_call=on_call, retries=k["budget"]["retry_attempts"]), knobs=k, max_jobs=max_jobs)
    label = f"{p.name}:{t.company or t.slug or t.query or t.careers_url}"
    try:
        jobs = p.fetch(t, ctx)
        rows = []
        for j in jobs:
            d = j.to_dict()
            d["company"] = d["company"] or t.company
            rows.append(d)
        return label, rows, "", calls[0]
    except (ProviderError, NotImplementedError) as e:
        return label, [], str(e), calls[0]
    except Exception as e:  # never let one scanner kill the run
        return label, [], f"{type(e).__name__}: {e}", calls[0]


def plan_targets(a, k: dict) -> list[tuple[object, Target]]:
    out: list[tuple[object, Target]] = []
    if a.url:
        hit = _registry.detect(a.url)
        if hit:
            out.append(hit)
        else:
            out.append((_registry.get("local-parser"), Target(careers_url=a.url)))
        return out
    if a.provider:
        p = _registry.get(a.provider)
        t = p.detect(a.careers_url) if a.careers_url else None
        t = t or (board_target(k, p.name) if not p.tenant else Target())
        if a.slug:
            t.slug = a.slug
        if a.query:
            t.query = a.query
        if a.careers_url:
            t.careers_url = a.careers_url
        return [(p, t)]
    companies = load_companies()
    if a.company:
        companies = [c for c in companies if c["name"].lower() == a.company.lower()]
        if not companies:
            raise SystemExit(f"company {a.company!r} not in {COMPANIES}")
    if a.company or a.full_ats or a.waves is not None:
        for c in companies:
            pt = target_for_company(c)
            if pt:
                out.append(pt)
    if a.waves is not None:
        waves = a.waves or k["sources"]["ats_scanners"]["waves"]
        for p in _registry.by_wave(waves):
            if not p.tenant and p.name not in ("local-parser", "sitemap", "wp-job-manager", "telegram-channel"):
                out.append((p, board_target(k, p.name)))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--waves", nargs="*")
    ap.add_argument("--full-ats", action="store_true")
    ap.add_argument("--company")
    ap.add_argument("--url")
    ap.add_argument("--provider")
    ap.add_argument("--slug")
    ap.add_argument("--careers-url")
    ap.add_argument("--query")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--preset")
    ap.add_argument("--run")
    ap.add_argument("--max-jobs", type=int)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    if a.list:
        provs = _registry.all_providers()
        by: dict[str, list[str]] = {}
        for p in provs.values():
            by.setdefault(p.wave or "?", []).append(p.name)
        for w in sorted(by):
            print(f"{w} ({len(by[w])}): {', '.join(sorted(by[w]))}")
        print(f"TOTAL {len(provs)} scanners")
        return 0

    k, _ = knobs_mod.load(a.preset)
    if not any([a.url, a.provider, a.company, a.full_ats, a.waves is not None]):
        a.waves = []
    targets = plan_targets(a, k)
    if a.dry_run:
        for p, t in targets:
            print(f"{p.name:22} {t.company or t.slug or t.query or t.careers_url}")
        print(f"{len(targets)} targets")
        return 0

    rd = common.run_dir(a.run, k, create=True) if a.run else common.new_run(k)
    ledger = rd / "ledger.jsonl"
    max_jobs = a.max_jobs or k["sources"]["ats_scanners"]["max_jobs_per_target"]
    rows: list[dict] = []
    status: list[dict] = []
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=k["sources"]["ats_scanners"]["workers"]) as ex:
        futs = [ex.submit(run_one, p, t, k, ledger, max_jobs) for p, t in targets]
        for f in cf.as_completed(futs):
            label, got, err, n_calls = f.result()
            rows.extend(got)
            status.append({"target": label, "jobs": len(got), "error": err})
            if err and not n_calls:  # failed before any HTTP call (e.g. missing key): record it once
                common.append_jsonl(ledger, {"ts": time.time(), "tool": "scanner", "source": f"scanner:{label.split(':')[0]}",
                                             "status": "failed", "reason": err[:160]})
    raw = rd / "jobs.raw.jsonl"
    existing = list(common.read_jsonl(raw))
    common.write_jsonl(raw, existing + rows)
    common.write_json(rd / "scan-status.json", {"targets": status, "seconds": round(time.time() - t0, 1)})
    ok = sum(1 for s in status if not s["error"])
    print(json.dumps({"run": rd.name, "targets": len(status), "ok": ok, "failed": len(status) - ok,
                      "jobs": len(rows), "file": str(raw)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
