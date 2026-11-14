"""Keka — careers shell gives an identifier, then /careers/api/embedjobs/default/active/<id>.

Mechanism from career-ops providers/keka.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

HOST = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.keka\.com$")
RESERVED = {"www", "app", "api", "help", "support", "blog", "docs", "status", "mail", "developers"}
IDENT = re.compile(r"/ats/documents/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/careerportal/", re.I)


def _origin(url: str) -> str:
    p = urlsplit((url or "").strip())
    host = (p.hostname or "").lower()
    if p.scheme != "https" or not HOST.match(host) or host[: -len(".keka.com")] in RESERVED:
        return ""
    return f"https://{host}"


def _location(row: dict) -> str:
    parts: list[str] = []
    for loc in row.get("jobLocations") or []:
        if not isinstance(loc, dict):
            continue
        place = ", ".join(x.strip() for x in (loc.get("city"), loc.get("countryName")) if isinstance(x, str) and x.strip())
        label = place or (loc.get("name") or "").strip()
        if label and label not in parts:
            parts.append(label)
    return "; ".join(parts)


class Keka(Provider):
    name = "keka"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("keka.com",)

    def detect(self, careers_url: str):
        o = _origin(careers_url)
        if not o:
            return None
        return Target(slug=urlsplit(o).hostname.split(".")[0], careers_url=careers_url, api_url=o + "/careers")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = _origin(target.api_url) or _origin(target.careers_url)
        if not o:
            raise ProviderError("keka needs https://<tenant>.keka.com/careers")
        shell = ctx.http.get_text(f"{o}/careers")
        m = IDENT.search(shell)
        if not m:
            raise ProviderError("keka: careers page is missing the embedjobs identifier")
        data = ctx.http.get_json(f"{o}/careers/api/embedjobs/default/active/{m.group(1).lower()}")
        if not isinstance(data, list):
            raise ProviderError("keka: expected a jobs array")
        jobs: list[Job] = []
        for r in data[: ctx.max_jobs]:
            if not isinstance(r, dict) or not isinstance(r.get("title"), str) or r.get("id") in (None, ""):
                continue
            title = re.sub(r"\s+", " ", r["title"]).strip()
            if not title:
                continue
            jobs.append(self.job(
                title=title, url=f"{o}/careers/jobdetails/{r['id']}",
                company=target.company or urlsplit(o).hostname.split(".")[0], location=_location(r),
                posted_at=to_iso(r.get("publishedOn")),
                description=html_to_text(r.get("description") or ""), source_id=str(r["id"]),
            ).validate())
        return jobs


PROVIDER = Keka()
