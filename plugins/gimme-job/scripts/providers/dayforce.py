"""Dayforce HCM candidate portal — public geo/jobposting search API.

Board:  https://jobs.dayforcehcm.com/{culture}/{tenant}/{board}
CSRF:   GET  https://jobs.dayforcehcm.com/api/auth/csrf
Search: POST https://jobs.dayforcehcm.com/api/geo/{tenant}/jobposting/search   (paginationStart)
Mechanism from career-ops scan-dayforce.mjs (MIT); code is our own.
Simplified: upstream drives a Playwright page for cookies; here the CSRF cookie is forwarded by hand
and no per-job detail fetch is made. Boards behind a bot challenge will fail with a ProviderError.
"""
from __future__ import annotations

import html
import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

HOST = "jobs.dayforcehcm.com"
ID = re.compile(r"^[A-Za-z0-9_-]+$")


def _locations(rows) -> list[str]:
    out = []
    for loc in rows or []:
        if not isinstance(loc, dict):
            continue
        s = (loc.get("formattedAddress") or "").strip() or ", ".join(
            x for x in (loc.get("cityName"), loc.get("stateCode"), loc.get("isoCountryCode")) if x)
        if s and s not in out:
            out.append(s)
    return out


class Dayforce(Provider):
    name = "dayforce"
    wave = "W1"
    kind = "ats"
    tenant = True
    hosts = (HOST,)

    def detect(self, careers_url: str):
        p = urlsplit(careers_url or "")
        if p.netloc.lower() != HOST:
            return None
        parts = [x for x in p.path.split("/") if x]
        if len(parts) < 2:
            return None
        culture = parts[0] if re.fullmatch(r"[a-z]{2}-[A-Z]{2}", parts[0]) else "en-US"
        rest = parts[1:] if culture == parts[0] else parts
        if not rest or not ID.match(rest[0]):
            return None
        board = rest[1] if len(rest) > 1 and ID.match(rest[1]) else "CANDIDATEPORTAL"
        return Target(slug=rest[0], careers_url=careers_url, options={"culture": culture, "board": board})

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        det = self.detect(target.careers_url) if target.careers_url else None
        tenant = target.slug or (det.slug if det else "")
        if not tenant or not ID.match(tenant):
            raise ProviderError("dayforce needs a tenant slug or jobs.dayforcehcm.com url")
        opts = {**(det.options if det else {}), **target.options}
        culture, board = opts.get("culture", "en-US"), opts.get("board", "CANDIDATEPORTAL")
        resp = ctx.http.get(f"https://{HOST}/api/auth/csrf")
        token = (resp.json() or {}).get("csrfToken")
        if not token:
            raise ProviderError("dayforce: csrf response missing csrfToken")
        headers = {"X-CSRF-TOKEN": token, "Content-Type": "application/json"}
        cookie = resp.headers.get("set-cookie")
        if cookie:
            headers["Cookie"] = "; ".join(c.split(";")[0] for c in cookie.split(", ") if "=" in c.split(";")[0])
        jobs: list[Job] = []
        start = 0
        for _ in range(200):
            data = ctx.http.post_json(f"https://{HOST}/api/geo/{tenant}/jobposting/search", {
                "clientNamespace": tenant, "jobBoardCode": board, "cultureCode": culture,
                "distanceUnit": 0, "paginationStart": start}, headers=headers)
            rows = data.get("jobPostings") if isinstance(data, dict) else None
            if not isinstance(rows, list):
                raise ProviderError("dayforce: expected jobPostings[]")
            for r in rows:
                jid = str(r.get("jobPostingId") or r.get("id") or "")
                title = html.unescape(str(r.get("jobTitle") or r.get("title") or "")).strip()
                if not title or not jid.isdigit():
                    continue
                locs = _locations(r.get("postingLocations"))
                jobs.append(self.job(
                    title=title, url=f"https://{HOST}/{culture}/{tenant}/{board}/jobs/{jid}",
                    company=target.company or tenant, locations=locs,
                    posted_at=to_iso(r.get("postingStartTimestampUTC")),
                    description=html_to_text(r.get("jobDescription") or ""), source_id=jid,
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            try:
                nxt = int(data.get("offset")) + int(data.get("count"))
                if int(data.get("count")) <= 0 or nxt >= int(data.get("maxCount")):
                    break
            except (TypeError, ValueError):
                break
            start = nxt
        return jobs


PROVIDER = Dayforce()
