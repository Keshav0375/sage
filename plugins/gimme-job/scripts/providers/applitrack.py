"""AppliTrack (Frontline) K-12 districts — GET https://www.applitrack.com/<slug>/onlineapp/jobpostings/Output.asp?all=1

Mechanism from career-ops providers/applitrack.mjs (MIT); code is our own.
The response is a JS file whose string literals hold the posting HTML.
"""
from __future__ import annotations

import html
import re
from datetime import date
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

HOSTS = ("www.applitrack.com", "applitrack.com")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$", re.I)


def _slug(url: str) -> str:
    p = urlsplit((url or "").strip())
    if p.scheme != "https" or p.netloc.lower() not in HOSTS:
        return ""
    parts = [x for x in p.path.split("/") if x]
    return parts[0].lower() if parts and SLUG_RE.match(parts[0]) else ""


def _text(s: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s or "")).replace("�", "").split())


class AppliTrack(Provider):
    name = "applitrack"
    wave = "W6"
    kind = "ats"
    tenant = True
    hosts = HOSTS

    def detect(self, careers_url: str):
        s = _slug(careers_url)
        if not s:
            return None
        base = f"https://www.applitrack.com/{s}/onlineapp"
        return Target(slug=s, careers_url=careers_url, api_url=f"{base}/jobpostings/Output.asp?all=1")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        slug = target.slug or _slug(target.careers_url)
        if not slug:
            raise ProviderError("applitrack: need an https://www.applitrack.com/<slug>/ url")
        base = f"https://www.applitrack.com/{slug}/onlineapp"
        body = ctx.http.get_text(f"{base}/jobpostings/Output.asp?all=1")
        if not body.strip():
            return []
        if "function applyFor" not in body:
            raise ProviderError("applitrack: response is not an Output.asp script")
        page = body.replace("\\'", "'").replace('\\"', '"')
        default_loc = str(target.options.get("default_location") or "")
        city = default_loc.split(",")[0].strip().lower()
        jobs: list[Job] = []
        seen: set[str] = set()
        for block in re.split(r"<table class='title'", page, flags=re.I)[1:]:
            idm = re.search(r"JobID:\s*(\d+)", block, re.I)
            tm = re.search(r"<td id='wrapword'[^>]*>([\s\S]*?)</td>", block, re.I)
            title = _text(tm.group(1)) if tm else ""
            if not idm or not title or idm.group(1) in seen:
                continue
            jid = idm.group(1)
            seen.add(jid)

            def field(name: str) -> str:
                m = re.search(rf"{name}:\s*</span>[\s\S]*?<span class=['\"]normal['\"][^>]*>([\s\S]*?)</span>",
                              block, re.I)
                return _text(m.group(1)) if m else ""

            site = field("Location")
            loc = site if site and (not city or city in site.lower()) else " - ".join(x for x in [site, default_loc] if x)
            posted = ""
            dm = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", field("Date Posted"))
            if dm:
                try:
                    posted = date(int(dm[3]), int(dm[1]), int(dm[2])).isoformat()
                except ValueError:
                    pass
            jobs.append(self.job(
                title=title, url=f"{base}/default.aspx?AppliTrackJobId={jid}&AppliTrackLayoutMode=detail&AppliTrackViewPosting=1",
                company=target.company or slug, location=loc, posted_at=posted, source_id=jid).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = AppliTrack()
