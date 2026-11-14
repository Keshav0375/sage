"""RemoteOK — public JSON feed (no auth).

GET https://remoteok.com/api   (first array element is a legal notice, skipped)
Mechanism from career-ops providers/remoteok.mjs (MIT); code is our own.
"""
from __future__ import annotations

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

FEED = "https://remoteok.com/api"


class RemoteOK(Provider):
    name = "remoteok"
    wave = "W1"
    kind = "board"
    tenant = False
    hosts = ("remoteok.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        data = ctx.http.get_json(FEED)
        if not isinstance(data, list):
            raise ProviderError("remoteok: expected a JSON array")
        words = [w.lower() for w in (target.query or "").split()]
        jobs: list[Job] = []
        for j in data:
            if not isinstance(j, dict) or not str(j.get("position", "")).strip():
                continue
            url = str(j.get("url") or "").strip()
            if not url.startswith(("http://", "https://")):
                continue
            tags = [t for t in j.get("tags") or [] if isinstance(t, str)]
            if words:
                hay = " ".join([j["position"], j.get("company") or "", *tags]).lower()
                if not any(w in hay for w in words):
                    continue
            lo, hi = j.get("salary_min"), j.get("salary_max")
            extra = {}
            if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and hi > 0:
                extra = dict(salary_min=float(lo), salary_max=float(hi), currency="USD", salary_period="year")
            jobs.append(self.job(
                title=j["position"].strip(), url=url, company=(j.get("company") or "").strip(),
                location=(j.get("location") or "").strip(), workplace="remote",
                posted_at=to_iso(j.get("date")), description=html_to_text(j.get("description") or ""),
                source_id=str(j.get("id", "")), extra={"tags": tags} if tags else {}, **extra,
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = RemoteOK()
