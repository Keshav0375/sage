#!/usr/bin/env python3
"""Normalise Composio job_search responses → runs/<id>/jobs.raw.jsonl.

The source-worker (Haiku) calls Composio with sync_response_to_workbench=false, saves each raw JSON
response to runs/<id>/composio/<slug>-<n>.json, then runs:  composio_ingest.py [--run ID] [files...]
Handles: LinkedIn search + get job, LinkedIn active jobs, JSearch, Glassdoor, Indeed, Google Jobs,
ZipRecruiter, Bing, Xing, Remote jobs, Daily International Jobs (best-effort field mapping).
Also: composio_ingest.py --plan  → prints the Composio tool calls to make for the current knobs.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts import knobs as knobs_mod  # noqa: E402
from scripts.providers._base import Job, ProviderError  # noqa: E402
from scripts.providers._parse import dig, first, html_to_text, parse_salary, to_iso, workplace_from, employment_from  # noqa: E402


def _iter_records(obj: Any) -> Iterator[dict]:
    """Walk any Composio envelope and yield dicts that look like job records."""
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            keys = set(cur)
            if keys & {"title", "job_title", "jobTitle"} and keys & {"url", "linkedinUrl", "job_apply_link", "job_google_link",
                                                                    "jobUrl", "link", "id", "job_id", "listing_id", "jobLink"}:
                yield cur
                continue
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)


def normalise(rec: dict, source: str) -> Job | None:
    title = first(rec.get("title"), rec.get("job_title"), rec.get("jobTitle"))
    url = first(rec.get("linkedinUrl"), rec.get("url"), rec.get("job_apply_link"), rec.get("jobUrl"),
                rec.get("jobLink"), rec.get("link"), rec.get("job_google_link"))
    if not url and source.startswith("linkedin") and rec.get("id"):
        url = f"https://www.linkedin.com/jobs/view/{rec['id']}"
    company = first(rec.get("companyName"), rec.get("company"), rec.get("employer_name"), rec.get("organization"),
                    dig(rec, "company.name"), rec.get("employer"))
    if isinstance(company, dict):
        company = company.get("name", "")
    loc = first(rec.get("location"), rec.get("job_location"), rec.get("locations_derived"),
                ", ".join(x for x in [rec.get("job_city"), rec.get("job_state"), rec.get("job_country")] if x))
    if isinstance(loc, list):
        loc = " | ".join(str(x) for x in loc)
    desc = first(rec.get("description"), rec.get("job_description"), rec.get("description_text"))
    salary: dict = {}
    if rec.get("job_min_salary") or rec.get("job_max_salary"):
        salary = {"salary_min": rec.get("job_min_salary"), "salary_max": rec.get("job_max_salary"),
                  "currency": rec.get("job_salary_currency", ""), "salary_period": (rec.get("job_salary_period") or "").lower()}
    elif isinstance(rec.get("salary"), str):
        salary = parse_salary(rec["salary"])
    elif desc:
        salary = {}
    workplace = workplace_from(first(rec.get("workplaceType"), rec.get("work_arrangement"),
                                     (rec.get("ai_work_arrangement") or [None])[0] if isinstance(rec.get("ai_work_arrangement"), list) else rec.get("ai_work_arrangement"),
                                     rec.get("job_is_remote") if rec.get("job_is_remote") else None))
    try:
        j = Job(title=str(title or ""), url=str(url or ""), source=source, company=str(company or ""), location=str(loc or ""),
                workplace=workplace, employment=employment_from(first(rec.get("employmentType"), rec.get("job_employment_type"))),
                posted_at=to_iso(first(rec.get("datePosted"), rec.get("date_posted"), rec.get("job_posted_at_datetime_utc"),
                                       rec.get("postedAt"), rec.get("listed_at"))),
                description=html_to_text(str(desc)) if desc else "",
                source_id=str(first(rec.get("id"), rec.get("job_id"), rec.get("listing_id"), "")),
                extra={k: rec[k] for k in ("applicants", "seniorityLevel", "postedTimeAgo", "employer_reviews") if k in rec},
                **{k: v for k, v in salary.items() if v not in (None, "")})
        return j.validate()
    except (ProviderError, TypeError):
        return None


def source_from_file(path: str) -> str:
    name = Path(path).stem.lower()
    for key, src in [("linkedin_search_list_active", "linkedin-active"), ("linkedin", "linkedin"), ("jsearch", "jsearch"),
                     ("glassdoor", "glassdoor"), ("indeed", "indeed"), ("google_jobs", "google-jobs"),
                     ("ziprecruiter", "ziprecruiter"), ("bing", "bing"), ("xing", "xing"), ("remote_jobs", "remote-jobs"),
                     ("daily_international", "daily-international")]:
        if key in name:
            return src
    return "composio"


def ingest(files: list[str]) -> list[dict]:
    rows: list[dict] = []
    for f in files:
        try:
            data = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:
            continue
        src = source_from_file(f)
        for rec in _iter_records(data):
            j = normalise(rec, src)
            if j:
                rows.append(j.to_dict())
    return rows


def plan(k: dict) -> list[dict]:
    """The Composio calls the source-worker should make for the current knobs."""
    s, src = k["search"], k["sources"]
    calls: list[dict] = []
    if src["linkedin_search"]["enabled"]:
        for loc in s["locations"]:
            for kw in s["keywords"][:2]:
                calls.append({"tool_slug": "JOB_SEARCH_JOBS_API_LINKEDIN_SEARCH_JOBS", "arguments": {
                    "query": kw, "location": loc, "date_posted": s["date_posted"],
                    "workplace_types": ";".join({"onsite": "onSite"}.get(w, w) for w in s["workplace"]),
                    "employment_types": ";".join({"contract": "contractor"}.get(e, e) for e in s["employment"]),
                    "experience_levels": ";".join(s["seniority"])}})
    if src["linkedin_active_jobs"]["enabled"]:
        calls.append({"tool_slug": "JOB_SEARCH_LINKEDIN_SEARCH_LIST_ACTIVE_JOBS", "arguments": {
            "title_advanced": " | ".join(f"'{t}'" for t in k["profile"]["target_titles"]),
            "location_advanced": " OR ".join(s["locations"]), "time_frame": src["linkedin_active_jobs"]["time_frame"],
            "ai_experience_level": s["experience_buckets"], "limit": src["linkedin_active_jobs"]["limit"],
            "organization_agency": "exclude" if s["exclude_agencies"] else None, "description_format": "text"}})
    if src["jsearch"]["enabled"]:
        dp = {"day": "today", "week": "week", "month": "month"}[s["date_posted"]]
        for kw in s["keywords"][:2]:
            calls.append({"tool_slug": "JOB_SEARCH_JSEARCH_SEARCH_JOBS", "arguments": {
                "query": f"{kw} in {s['locations'][0]}", "country": src["jsearch"]["country"], "date_posted": dp,
                "num_pages": src["jsearch"]["num_pages"]}})
    if src["glassdoor"]["enabled"]:
        calls.append({"tool_slug": "JOB_SEARCH_GLASSDOOR_REALTIME_JOBS_SEARCH", "arguments": {
            "query": s["keywords"][0], "city": s["locations"][0].split(",")[0]}})
    if src["indeed"]["enabled"]:
        calls.append({"tool_slug": "JOB_SEARCH_JOBS_API_INDEED_SEARCH_JOBS", "arguments": {
            "query": s["keywords"][0], "location": s["locations"][0].split(",")[0], "country_code": src["indeed"]["country_code"],
            "sort_type": "date"}})
    if src["google_jobs"]["enabled"]:
        calls.append({"tool_slug": "JOB_SEARCH_GOOGLE_JOBS_LIST_JOBS", "arguments": {"query": s["keywords"][0], "location": s["locations"][0]}})
    for name, slug in [("ziprecruiter", "JOB_SEARCH_ZIPRECRUITER_SEARCH_JOBS"), ("bing", "JOB_SEARCH_JOBS_API_BING_SEARCH_JOBS"),
                       ("xing", "JOB_SEARCH_JOBS_API_XING_SEARCH_JOBS"), ("remote_jobs", "JOB_SEARCH_REMOTE_JOBS_LIST_JOBS"),
                       ("daily_international", "JOB_SEARCH_DAILY_INTERNATIONAL_JOBS_SEARCH")]:
        if src[name]["enabled"]:
            calls.append({"tool_slug": slug, "arguments": {"_note": "load schema with COMPOSIO_GET_TOOL_SCHEMAS, then fill from knobs",
                                                          "query": s["keywords"][0]}})
    for c in calls:
        c["arguments"] = {a: v for a, v in c["arguments"].items() if v not in (None, "", [])}
    return calls[: k["budget"]["max_composio_calls"]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--run")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--preset")
    a = ap.parse_args(argv)
    k, _ = knobs_mod.load(a.preset)
    if a.plan:
        print(json.dumps(plan(k), indent=2))
        return 0
    rd = common.run_dir(a.run, k, create=True)
    files = a.files or sorted(glob.glob(str(rd / "composio" / "*.json")))
    rows = ingest(files)
    raw = rd / "jobs.raw.jsonl"
    common.write_jsonl(raw, list(common.read_jsonl(raw)) + rows)
    print(json.dumps({"run": rd.name, "files": len(files), "jobs": len(rows)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
