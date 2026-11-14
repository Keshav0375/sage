"""Greenhouse — public boards API (no auth).

GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
Reference scanner: every other scanner follows this shape (detect → fetch → normalise → validate).
Mechanism from career-ops providers/greenhouse.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

API = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"


class Greenhouse(Provider):
    name = "greenhouse"
    wave = "W1"
    kind = "ats"
    tenant = True
    hosts = ("greenhouse.io",)

    def detect(self, careers_url: str):
        p = urlsplit(careers_url or "")
        host = p.netloc.lower()
        if not host.endswith("greenhouse.io"):
            return None
        q = parse_qs(p.query)
        if "for" in q:                                   # embed boards: ?for=<slug>
            slug = q["for"][0]
        else:
            parts = [x for x in p.path.split("/") if x]
            if host.startswith("boards-api.") and len(parts) >= 3:
                slug = parts[2]                          # /v1/boards/<slug>/jobs
            else:
                slug = parts[0] if parts else ""
        if not slug or slug == "embed":
            return None
        return Target(slug=slug, careers_url=careers_url, api_url=API.format(slug=slug))

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        slug = target.slug or (self.detect(target.careers_url) or Target()).slug
        if not slug:
            raise ProviderError("greenhouse needs a board slug")
        data = ctx.http.get_json(target.api_url or API.format(slug=slug))
        jobs: list[Job] = []
        for j in (data or {}).get("jobs", [])[: ctx.max_jobs]:
            offices = [o.get("name", "") for o in j.get("offices") or [] if o.get("name")]
            loc = (j.get("location") or {}).get("name", "")
            depts = [d.get("name", "") for d in j.get("departments") or [] if d.get("name")]
            jobs.append(self.job(
                title=j.get("title", ""),
                url=j.get("absolute_url", ""),
                company=target.company or j.get("company_name", "") or slug,
                location=loc,
                locations=offices or ([loc] if loc else []),
                posted_at=to_iso(j.get("first_published") or j.get("updated_at")),
                description=html_to_text(j.get("content", "")),
                department=", ".join(depts),
                source_id=str(j.get("id", "")),
            ).validate())
        return jobs


PROVIDER = Greenhouse()
