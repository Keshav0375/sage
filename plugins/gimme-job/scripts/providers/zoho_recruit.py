"""Zoho Recruit career sites — https://<tenant>.zohorecruit.<tld>/jobs/Careers (JSON in <input id="jobs">).

Mechanism from career-ops providers/zoho-recruit.mjs (MIT); code is our own.
Simplified: list page only (no per-posting detail enrichment).
"""
from __future__ import annotations

import html as htmllib
import json
import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

HOST = re.compile(r"^([a-z0-9][a-z0-9-]*)\.zohorecruit\.(?:com|ca|eu|in|com\.au|jp|sa|com\.cn)$")
BOARD_PATH = "/jobs/Careers"
INPUT = re.compile(r"""<input\b(?:[^>"']|"[^"]*"|'[^']*')*>""", re.I)


def _origin(url: str) -> str:
    p = urlsplit((url or "").strip())
    host = (p.hostname or "").lower()
    return f"https://{host}" if p.scheme == "https" and HOST.match(host) else ""


def _s(v) -> str:
    return v.strip() if isinstance(v, str) else ""


class ZohoRecruit(Provider):
    name = "zoho-recruit"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("zohorecruit.com",)

    def detect(self, careers_url: str):
        o = _origin(careers_url)
        if not o:
            return None
        return Target(slug=HOST.match(urlsplit(o).hostname).group(1), careers_url=careers_url, api_url=o + BOARD_PATH)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = _origin(target.careers_url) or _origin(target.api_url)
        if not o:
            raise ProviderError("zoho-recruit needs https://<tenant>.zohorecruit.<tld>")
        page = ctx.http.get_text(o + BOARD_PATH)
        value = None
        for m in INPUT.finditer(page):
            tag = m.group(0)
            if not re.search(r"""\sid\s*=\s*["']?jobs["'\s/>]""", tag, re.I):
                continue
            a = re.search(r"""\svalue\s*=\s*(?:"([^"]*)"|'([^']*)')""", tag, re.I)
            value = (a.group(1) if a and a.group(1) is not None else (a.group(2) if a else "")) or ""
            break
        if value is None:
            raise ProviderError("zoho-recruit: no id=\"jobs\" input (unknown tenant or legacy career site)")
        try:
            records = json.loads(htmllib.unescape(value))
        except ValueError as e:
            raise ProviderError(f"zoho-recruit: jobs value is not JSON ({e})")
        if not isinstance(records, list):
            raise ProviderError("zoho-recruit: jobs value is not an array")
        jobs: list[Job] = []
        seen: set[str] = set()
        for r in records:
            if not isinstance(r, dict) or r.get("Is_Locked") is True or r.get("Publish") is False:
                continue
            title = _s(r.get("Posting_Title")) or _s(r.get("Job_Opening_Name"))
            rid = str(r["id"]) if isinstance(r.get("id"), (int, str)) and str(r.get("id")).strip() else ""
            if not title or not rid:
                continue
            url = f"{o}{BOARD_PATH}/{rid}"
            if url in seen:
                continue
            seen.add(url)
            parts = [x for x in (_s(r.get("City")), _s(r.get("State")), _s(r.get("Country"))) if x]
            if r.get("Remote_Job") is True:
                parts.append("Remote")
            jobs.append(self.job(
                title=title, url=url, company=target.company or target.slug or urlsplit(o).hostname.split(".")[0],
                location=", ".join(dict.fromkeys(parts)),
                workplace="remote" if r.get("Remote_Job") is True else "",
                posted_at=to_iso(_s(r.get("Date_Opened"))),
                description=html_to_text(_s(r.get("Job_Description"))), source_id=rid,
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = ZohoRecruit()
