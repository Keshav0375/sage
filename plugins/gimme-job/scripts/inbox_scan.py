#!/usr/bin/env python3
"""Job alerts from email → job URLs → runs/<id>/jobs.raw.jsonl (title/company when the alert gives them).

  inbox_scan.py FILE.eml|FILE.mbox|FILE.txt|DIR ...  [--run ID]
  inbox_scan.py --json-messages FILE.json [--run ID]   (mail-worker saves Gmail MCP message bodies as JSON)
  linkedin export:  inbox_scan.py --linkedin-csv saved_jobs.csv [--run ID]
Reads LinkedIn, Indeed, Glassdoor, ZipRecruiter alert formats. Read-only: never sends or changes mail.
"""
from __future__ import annotations

import argparse
import csv
import email
import json
import mailbox
import re
import sys
from email import policy
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts.providers._base import Job, ProviderError  # noqa: E402
from scripts.providers._parse import html_to_text, links  # noqa: E402

JOB_URL = [
    (re.compile(r"linkedin\.com/(?:comm/)?jobs/view/(\d+)"), "linkedin", lambda m: f"https://www.linkedin.com/jobs/view/{m.group(1)}"),
    (re.compile(r"indeed\.com/(?:rc/clk|viewjob|pagead/clk)[^\s\"'<>]*?jk=([0-9a-f]+)"), "indeed", lambda m: f"https://www.indeed.com/viewjob?jk={m.group(1)}"),
    (re.compile(r"glassdoor\.[a-z.]+/(?:job-listing|partner/jobListing)[^\s\"'<>]*?(?:jobListingId|jl)=(\d+)"), "glassdoor",
     lambda m: f"https://www.glassdoor.com/job-listing/?jl={m.group(1)}"),
    (re.compile(r"ziprecruiter\.com/(?:c|jobs|k)/[^\s\"'<>]+"), "ziprecruiter", lambda m: m.group(0) if m.group(0).startswith("http") else "https://www." + m.group(0)),
]


def _unwrap(url: str) -> str:
    """Follow common redirect wrappers (?url=, ?u=) without network."""
    q = parse_qs(urlsplit(url).query)
    for key in ("url", "u", "redirect", "dest"):
        if key in q and q[key][0].startswith("http"):
            return unquote(q[key][0])
    return url


def jobs_from_html(html: str, sender: str = "") -> list[Job]:
    out: dict[str, Job] = {}
    for href, text in links(html):
        url = _unwrap(href)
        for rx, src, mk in JOB_URL:
            m = rx.search(url)
            if m:
                clean = mk(m)
                title = text if 3 < len(text) < 120 and not re.match(r"(?i)(view|apply|see|more|unsubscribe)", text) else ""
                if clean not in out or (title and not out[clean].title.strip("?")):
                    try:
                        out[clean] = Job(title=title or "(from alert)", url=clean, source=f"alert:{src}",
                                         extra={"sender": sender}).validate()
                    except ProviderError:
                        pass
    return list(out.values())


def _body(msg) -> str:
    if msg.is_multipart():
        parts = [p for p in msg.walk() if p.get_content_type() in ("text/html", "text/plain")]
        html = next((p for p in parts if p.get_content_type() == "text/html"), None)
        part = html or (parts[0] if parts else None)
        return part.get_content() if part else ""
    return msg.get_content()


def from_files(paths: list[Path]) -> list[Job]:
    jobs: list[Job] = []
    files: list[Path] = []
    for p in paths:
        files += sorted(x for x in p.rglob("*") if x.is_file()) if p.is_dir() else [p]
    for f in files:
        if f.suffix == ".mbox":
            for msg in mailbox.mbox(str(f)):
                jobs += jobs_from_html(_body(email.message_from_bytes(msg.as_bytes(), policy=policy.default)), msg.get("From", ""))
        elif f.suffix == ".eml":
            msg = email.message_from_bytes(f.read_bytes(), policy=policy.default)
            jobs += jobs_from_html(_body(msg), msg.get("From", ""))
        else:
            jobs += jobs_from_html(f.read_text(encoding="utf-8", errors="ignore"))
    return jobs


def from_json_messages(path: Path) -> list[Job]:
    data = json.loads(path.read_text(encoding="utf-8"))
    msgs = data if isinstance(data, list) else data.get("messages", [data])
    jobs: list[Job] = []
    for m in msgs:
        body = m.get("body") or m.get("html") or m.get("text") or m.get("snippet") or ""
        jobs += jobs_from_html(body if "<a" in body else re.sub(r"(https?://\S+)", r'<a href="\1">\1</a>', body), m.get("from", ""))
    return jobs


def from_linkedin_csv(path: Path) -> list[Job]:
    jobs = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            url = row.get("Job Url") or row.get("Job URL") or row.get("URL") or ""
            m = re.search(r"jobs/view/(\d+)", url)
            if not m:
                continue
            try:
                jobs.append(Job(title=row.get("Job Title") or row.get("Title") or "(saved job)",
                                url=f"https://www.linkedin.com/jobs/view/{m.group(1)}", source="linkedin-export",
                                company=row.get("Company Name") or row.get("Company") or "").validate())
            except ProviderError:
                pass
    return jobs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--json-messages")
    ap.add_argument("--linkedin-csv")
    ap.add_argument("--run")
    a = ap.parse_args(argv)
    jobs: list[Job] = []
    if a.paths:
        jobs += from_files([Path(p) for p in a.paths])
    if a.json_messages:
        jobs += from_json_messages(Path(a.json_messages))
    if a.linkedin_csv:
        jobs += from_linkedin_csv(Path(a.linkedin_csv))
    rd = common.run_dir(a.run, create=True)
    raw = rd / "jobs.raw.jsonl"
    rows = [j.to_dict() for j in jobs]
    common.write_jsonl(raw, list(common.read_jsonl(raw)) + rows)
    print(json.dumps({"run": rd.name, "jobs": len(rows), "by_source": {s: sum(1 for r in rows if r["source"] == s) for s in {r["source"] for r in rows}}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
