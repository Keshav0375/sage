"""Himalayas — public jobs API (no auth).

GET https://himalayas.app/jobs/api?limit=20[&cursor=...]
Mechanism from career-ops providers/himalayas.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import employment_from, to_iso

FEED = "https://himalayas.app/jobs/api?limit=20"


def _ok(url: str) -> str:
    p = urlsplit(url or "")
    host = p.netloc.lower()
    return url if p.scheme == "https" and (host == "himalayas.app" or host.endswith(".himalayas.app")) else ""


class Himalayas(Provider):
    name = "himalayas"
    wave = "W1"
    kind = "board"
    tenant = False
    hosts = ("himalayas.app",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        words = [w.lower() for w in (target.query or "").split()]
        max_pages = int(target.options.get("max_pages", 10))
        jobs: list[Job] = []
        cursor, seen = "", set()
        for _ in range(max_pages):
            data = ctx.http.get_json(FEED + (f"&cursor={quote(cursor)}" if cursor else ""))
            if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
                raise ProviderError("himalayas: expected {jobs: [...]}")
            for it in data["jobs"]:
                title = (it.get("title") or "").strip()
                url = _ok(it.get("applicationLink") or "") or _ok(it.get("guid") or "")
                if not title or not url:
                    continue
                if words and not any(w in (title + " " + " ".join(it.get("categories") or [])).lower() for w in words):
                    continue
                locs = [l for l in it.get("locationRestrictions") or [] if isinstance(l, str) and l.strip()]
                lo, hi = it.get("minSalary"), it.get("maxSalary")
                extra = {}
                if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and hi > 0:
                    extra = dict(salary_min=float(lo), salary_max=float(hi),
                                 currency=it.get("salaryCurrency") or "", salary_period="year")
                jobs.append(self.job(
                    title=title, url=url, company=(it.get("companyName") or "").strip(),
                    location=", ".join(locs) if locs else "Remote (worldwide)", locations=locs,
                    workplace="remote", employment=employment_from(it.get("employmentType")),
                    posted_at=to_iso(it.get("pubDate")), source_id=str(it.get("guid", "")), **extra,
                ).validate())
            cursor = data.get("nextCursor") or ""
            if not cursor or cursor in seen or len(jobs) >= ctx.max_jobs:
                break
            seen.add(cursor)
        return jobs[: ctx.max_jobs]


PROVIDER = Himalayas()
