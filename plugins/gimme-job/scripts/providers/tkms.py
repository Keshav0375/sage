"""TKMS (thyssenkrupp Marine Systems) — POST https://jobs.tkmsgroup.com/api/filter/query.

Mechanism from career-ops providers/tkms.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html
import re
import unicodedata
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, Target
from ._parse import to_iso

HOST = "jobs.tkmsgroup.com"
MAX_PAGES = 60


def slugify(title: str) -> str:
    s = unicodedata.normalize("NFKD", str(title))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-") or "job"


def _location(d: dict) -> str:
    out = []
    for l in d.get("locations") or []:
        s = str((l or {}).get("cityState") or (l or {}).get("city") or "").strip()
        if s and s not in out:
            out.append(s)
    if out:
        return " / ".join(out)
    flat = [str(x or "").strip() for x in (d.get("city"), d.get("country"))]
    return ", ".join(dict.fromkeys(x for x in flat if x))


class Tkms(Provider):
    name = "tkms"
    wave = "W6"
    kind = "company"
    tenant = False
    hosts = (HOST,)

    def detect(self, careers_url: str):
        p = urlsplit(careers_url or "")
        if p.scheme == "https" and p.netloc.lower() == HOST:
            return Target(careers_url=careers_url)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        origin = f"https://{HOST}"
        locale = str(target.options.get("locale") or "en")
        sub = str(target.options.get("subclient") or "tkms")
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(MAX_PAGES):
            data = ctx.http.post_json(f"{origin}/api/filter/query", {
                "searchQuery": target.query or "", "filter": {}, "subclient": sub,
                "locale": locale, "page": page})
            rows = (data or {}).get("jobs")
            if not isinstance(rows, list) or not rows:
                break
            fresh = 0
            for item in rows:
                d = (item or {}).get("data") or {}
                jid = str(d["id"]) if d.get("id") is not None else ""
                title = " ".join(html.unescape(re.sub(r"<[^>]*>", " ", str(d.get("title") or ""))).split())
                if not jid or not title or jid in seen:
                    continue
                seen.add(jid)
                fresh += 1
                ts = d.get("postingDate_timestamp")
                posted = to_iso(ts) if isinstance(ts, (int, float)) else to_iso(d.get("postingDate"))
                jobs.append(self.job(
                    title=title, url=f"{origin}/{quote(locale, safe='')}/job/{slugify(title)}/{quote(jid, safe='')}",
                    company=target.company or "TKMS", location=_location(d), posted_at=posted,
                    source_id=jid).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if not fresh or not isinstance((data or {}).get("nextPage"), int):
                break
        return jobs


PROVIDER = Tkms()
