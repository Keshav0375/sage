"""Remotive — public JSON API (no auth).

GET https://remotive.com/api/remote-jobs[?search=...]
Mechanism from career-ops providers/remotive.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import quote

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import employment_from, html_to_text

FEED = "https://remotive.com/api/remote-jobs"


class Remotive(Provider):
    name = "remotive"
    wave = "W1"
    kind = "board"
    tenant = False
    hosts = ("remotive.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        url = FEED + (f"?search={quote(target.query)}" if target.query else "")
        data = ctx.http.get_json(url)
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise ProviderError("remotive: expected {jobs: [...]}")
        jobs: list[Job] = []
        for j in data["jobs"][: ctx.max_jobs]:
            if not isinstance(j, dict) or not str(j.get("title", "")).strip():
                continue
            if not str(j.get("url") or "").startswith(("http://", "https://")):
                continue
            pub = str(j.get("publication_date") or "")
            jobs.append(self.job(
                title=j["title"].strip(), url=j["url"].strip(), company=(j.get("company_name") or "").strip(),
                location=(j.get("candidate_required_location") or "").strip(), workplace="remote",
                employment=employment_from(j.get("job_type")), department=j.get("category") or "",
                posted_at=pub, description=html_to_text(j.get("description") or ""),
                source_id=str(j.get("id", "")), **_sal(j.get("salary")),
            ).validate())
        return jobs


def _sal(text):
    from ._parse import parse_salary
    return parse_salary(text) if isinstance(text, str) else {}


PROVIDER = Remotive()
