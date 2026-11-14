"""BambooHR — public careers list (no auth).

GET https://{tenant}.bamboohr.com/careers/list  ->  {"result": [...]}
Mechanism from career-ops providers/bamboohr.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import employment_from

HOST_RE = re.compile(r"^([a-z0-9][a-z0-9-]*)\.bamboohr\.com$")


class BambooHR(Provider):
    name = "bamboohr"
    wave = "W1"
    kind = "ats"
    tenant = True
    hosts = ("bamboohr.com",)

    def detect(self, careers_url: str):
        host = urlsplit(careers_url or "").netloc.lower()
        m = HOST_RE.match(host)
        if not m or m.group(1) in ("www", "api"):
            return None
        return Target(slug=m.group(1), careers_url=careers_url, api_url=f"https://{host}/careers/list")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        slug = target.slug or (self.detect(target.careers_url) or Target()).slug
        if not slug:
            raise ProviderError("bamboohr needs a tenant slug")
        origin = f"https://{slug}.bamboohr.com"
        data = ctx.http.get_json(target.api_url or f"{origin}/careers/list")
        rows = data.get("result") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ProviderError("bamboohr: expected {result: [...]}")
        jobs: list[Job] = []
        for j in rows[: ctx.max_jobs]:
            jid = str(j.get("id", "")).strip()
            if not jid or not j.get("jobOpeningName"):
                continue
            loc = j.get("location") or {}
            remote = "Remote" if j.get("isRemote") else ""
            jobs.append(self.job(
                title=str(j["jobOpeningName"]), url=f"{origin}/careers/{quote(jid)}",
                company=target.company or slug,
                location=", ".join(x for x in (loc.get("city"), loc.get("state"), remote) if x),
                country=loc.get("country") or "",
                workplace="remote" if j.get("isRemote") else "",
                employment=employment_from(j.get("employmentStatusLabel")),
                department=j.get("departmentLabel") or "", source_id=jid,
            ).validate())
        return jobs


PROVIDER = BambooHR()
