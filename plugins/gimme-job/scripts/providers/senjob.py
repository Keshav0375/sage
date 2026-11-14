"""Senjob (Senegal) — server-rendered listing table, board-wide.

GET https://senjob.com/offres-d-emploi.php[?page=N]
Mechanism from career-ops providers/senjob.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re

from ._base import Context, Job, Provider, Target
from ._parse import html_to_text, to_iso

LIST_URL = "https://senjob.com/offres-d-emploi.php"
LINK_RE = re.compile(r'href="(https://senjob\.com/jobseekers/[^"]*?_e_(\d+)\.html)"', re.I)
ANCHOR_RE = re.compile(r'<a\s[^>]*href="https://senjob\.com/jobseekers/[^"]*?_e_\d+\.html"[^>]*>([\s\S]*?)</a>', re.I)
DATE_RE = re.compile(r'display:\s*none;?\s*"?>\s*(\d{4}-\d{2}-\d{2})\s*<', re.I)


def _text(h: str) -> str:
    # drop hidden spans (ISO dates) before flattening
    h = re.sub(r"<span[^>]*display:\s*none[^>]*>[\s\S]*?</span>", " ", h, flags=re.I)
    return " ".join(html_to_text(re.sub(r"<[^>]+>", " ", h)).split())


def parse_listing(html: str) -> list[dict]:
    by_id: dict[str, dict] = {}
    for row in re.split(r"<tr\b", html or "", flags=re.I):
        link = LINK_RE.search(row)
        if not link:
            continue
        url, jid = link.groups()
        rec = by_id.setdefault(jid, {"id": jid, "url": url, "title": "", "location": "", "posted": ""})
        anchor = ANCHOR_RE.search(row)
        if anchor and not rec["title"]:
            rec["title"] = _text(anchor.group(1))
            tail = _text(row[anchor.end():])
            rec["location"] = re.split(r"(?i)publi[ée]", tail)[0].strip(" |:-\t\n")
        d = DATE_RE.search(row)
        if d and not rec["posted"]:
            rec["posted"] = d.group(1)
    return [r for r in by_id.values() if r["title"]]


class Senjob(Provider):
    name = "senjob"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("senjob.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        max_pages = min(int(target.options.get("max_pages") or 10), 50)
        jobs: dict[str, Job] = {}
        for page in range(1, max_pages + 1):
            rows = parse_listing(ctx.http.get_text(LIST_URL if page == 1 else f"{LIST_URL}?page={page}"))
            fresh = 0
            for r in rows:
                if r["url"] in jobs:
                    continue
                fresh += 1
                jobs[r["url"]] = self.job(
                    title=r["title"], url=r["url"], location=r["location"], country="SN",
                    posted_at=to_iso(r["posted"]), source_id=r["id"]).validate()
                if len(jobs) >= ctx.max_jobs:
                    return list(jobs.values())
            if not fresh:
                break
        return list(jobs.values())


PROVIDER = Senjob()
