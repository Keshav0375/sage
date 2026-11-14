"""Collage (collage.co) — GET https://api.collage.co/v1/positions/<job-site-address>.

Mechanism from career-ops providers/collage.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import quote, unquote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

API = "https://api.collage.co/v1/positions/"


def _site(url: str) -> str:
    p = urlsplit((url or "").strip())
    host = (p.hostname or "").lower()
    if p.scheme != "https":
        return ""
    if host == "api.collage.co":
        m = re.match(r"^/v1/positions/([^/?#]+)$", p.path)
        return unquote(m.group(1)) if m else ""
    if host == "secure.collage.co":
        m = re.match(r"^/jobs/([^/]+)/?$", p.path)
        site = unquote(m.group(1)) if m else ""
        return site if site and "." not in site else ""
    return ""


def _t(v) -> str:
    return v.strip() if isinstance(v, str) else ""


def _https(v) -> str:
    u = _t(v)
    p = urlsplit(u)
    return u if p.scheme == "https" and p.hostname and not p.username and not p.password else ""


class Collage(Provider):
    name = "collage"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("collage.co",)

    def detect(self, careers_url: str):
        s = _site(careers_url)
        return Target(slug=s, careers_url=careers_url, api_url=API + quote(s, safe="")) if s else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        s = target.slug or _site(target.api_url) or _site(target.careers_url)
        if not s:
            raise ProviderError("collage needs https://secure.collage.co/jobs/<job-site-address>")
        data = ctx.http.get_json(API + quote(s, safe=""))
        rows = data if isinstance(data, list) else (data or {}).get("positions") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ProviderError("collage: unrecognized response envelope (expected a positions array)")
        jobs: list[Job] = []
        for j in rows[: ctx.max_jobs]:
            if not isinstance(j, dict) or not _t(j.get("title")):
                continue
            url = _https(j.get("hostedUrl")) or _https(j.get("url")) or _https(j.get("applyUrl"))
            if not url:
                continue
            loc = j.get("location")
            location = "; ".join(x for x in (_t(v) for v in loc) if x) if isinstance(loc, list) else _t(loc)
            meta = [f"{label}: {_t(j.get(k))}" for k, label in (("department", "Department"), ("commitment", "Commitment"),
                                                                ("employmentType", "Employment type")) if _t(j.get(k))]
            desc = "\n\n".join(x for x in (_t(j.get("descriptionPlain")), "\n".join(meta)) if x)
            jobs.append(self.job(
                title=_t(j["title"]), url=url, company=target.company or s, location=location,
                department=_t(j.get("department")), description=desc,
                posted_at=to_iso(j.get("createdDate") or j.get("createdAt") or j.get("publishedAt")),
                source_id=str(j.get("id", "")),
            ).validate())
        return jobs


PROVIDER = Collage()
