"""SchoolSpring K-12 districts — GET https://api.schoolspring.com/api/Jobs/GetPagedJobsWithSearch.

Mechanism from career-ops providers/schoolspring.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html
import re
from urllib.parse import urlencode, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

API_HOST = "api.schoolspring.com"
HOST_RE = re.compile(r"^[a-z0-9][a-z0-9-]*\.schoolspring\.com$")
NON_DISTRICT = {"www.schoolspring.com", API_HOST}
PAGE_SIZE = 100
MAX_PAGES = 20


def _host(url: str) -> str:
    p = urlsplit((url or "").strip())
    h = p.netloc.lower()
    if p.scheme != "https" or not HOST_RE.match(h) or h in NON_DISTRICT:
        return ""
    return h


class SchoolSpring(Provider):
    name = "schoolspring"
    wave = "W6"
    kind = "ats"
    tenant = True
    hosts = ("schoolspring.com", API_HOST)

    def detect(self, careers_url: str):
        h = _host(careers_url)
        return Target(slug=h.split(".")[0], careers_url=f"https://{h}/") if h else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        host = _host(target.careers_url)
        if not host:
            raise ProviderError("schoolspring: need https://<district>.schoolspring.com")
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, MAX_PAGES + 1):
            q = urlencode({"domainName": host, "keyword": "", "location": "", "category": "", "gradelevel": "",
                           "jobtype": "", "organization": "", "swLat": "", "swLon": "", "neLat": "", "neLon": "",
                           "page": page, "size": PAGE_SIZE, "sortDateAscending": "false"})
            data = ctx.http.get_json(f"https://{API_HOST}/api/Jobs/GetPagedJobsWithSearch?{q}")
            if not data:
                break
            if not isinstance(data, dict) or data.get("success") is not True:
                raise ProviderError(f"schoolspring: API error: {(data or {}).get('message') if isinstance(data, dict) else data}")
            rows = (data.get("value") or {}).get("jobsList")
            if not isinstance(rows, list):
                raise ProviderError("schoolspring: no jobsList array")
            fresh = 0
            for j in rows:
                jid = str((j or {}).get("jobId") or "").strip()
                title = html.unescape(str(j.get("title") or "")).strip()
                if not re.fullmatch(r"\d+", jid) or not title:
                    continue
                url = f"https://{host}/?jobid={jid}"
                if url in seen:
                    continue
                seen.add(url)
                fresh += 1
                loc = html.unescape(str(j.get("location") or "")).strip()
                emp = html.unescape(str(j.get("employer") or "")).strip()
                jobs.append(self.job(title=title, url=url, company=target.company or emp or host.split(".")[0],
                                     location=loc, posted_at=to_iso(j.get("displayDate")),
                                     source_id=jid).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if len(rows) < PAGE_SIZE or not fresh:
                break
        return jobs


PROVIDER = SchoolSpring()
