"""Amazon Jobs — public search.json (no auth).

GET https://www.amazon.jobs/en/search.json?base_query=..&loc_query=..&result_limit=100&offset=N&sort=recent
-> {hits, jobs: [{title, job_path, company_name, normalized_location, location, locations[], posted_date}]}
Optional filters via ``target.options['amazon']`` (extra query params) and target.query / target.location.
Mechanism from career-ops providers/amazon.mjs (MIT); code is our own.
"""
from __future__ import annotations

import json
from urllib.parse import urlencode, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

ORIGIN = "https://www.amazon.jobs"
PAGE_SIZE = 100
MAX_PAGES = 20


def _s(v) -> str:
    return v.strip() if isinstance(v, str) else ""


def _location(j: dict) -> str:
    primary = _s(j.get("normalized_location")) or _s(j.get("location"))
    cities = [primary] if primary else []
    seen = set(cities)
    for e in j.get("locations") or []:
        try:
            loc = json.loads(e) if isinstance(e, str) else e
        except ValueError:
            continue
        if not isinstance(loc, dict):
            continue
        spelled = _s(loc.get("location"))
        name = _s(loc.get("normalizedLocation")) or spelled
        if name and name not in seen and spelled not in seen:
            cities.append(name)
        seen.update(x for x in (name, spelled) if x)
    return " · ".join(cities)


class Amazon(Provider):
    name = "amazon"
    wave = "W3"
    kind = "company"
    tenant = False
    hosts = ("amazon.jobs",)

    def detect(self, careers_url: str):
        h = urlsplit(careers_url or "").netloc.lower()
        if h == "amazon.jobs" or h.endswith(".amazon.jobs"):
            return Target(company="Amazon", careers_url=careers_url)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        cfg = target.options.get("amazon") if isinstance(target.options.get("amazon"), dict) else {}
        jobs: list[Job] = []
        seen: set[str] = set()
        pages = MAX_PAGES
        page = 0
        while page < pages:
            params: list[tuple[str, str]] = []
            for k, v in cfg.items():
                if isinstance(v, list):
                    params += [(k if k.endswith("[]") else k + "[]", str(i)) for i in v]
                elif v is not None:
                    params.append((k, str(v)))
            keys = {k for k, _ in params}
            if "base_query" not in keys:
                params.append(("base_query", target.query))
            if "loc_query" not in keys:
                params.append(("loc_query", target.location))
            params += [("sort", str(cfg.get("sort") or "recent")), ("result_limit", str(PAGE_SIZE)),
                       ("offset", str(page * PAGE_SIZE))]
            data = ctx.http.get_json(f"{ORIGIN}/en/search.json?{urlencode(params)}")
            rows = data.get("jobs") if isinstance(data, dict) else None
            if not isinstance(rows, list):
                raise ProviderError(f"amazon: expected jobs[], got {sorted(data) if isinstance(data, dict) else type(data).__name__}")
            if page == 0 and isinstance(data.get("hits"), int):
                pages = max(pages, min(-(-data["hits"] // PAGE_SIZE) + 1, 100))
            if not rows:
                break
            fresh = 0
            for j in rows:
                path = j.get("job_path")
                if not path or not isinstance(path, str):
                    continue
                url = path if path.lower().startswith(("http://", "https://")) else ORIGIN + ("" if path.startswith("/") else "/") + path
                if url in seen:
                    continue
                seen.add(url)
                fresh += 1
                jobs.append(self.job(
                    title=_s(j.get("title")), url=url, company=j.get("company_name") or "Amazon",
                    location=_location(j), country=_s(j.get("country_code")),
                    posted_at=to_iso(" ".join(str(j.get("posted_date") or "").split())),
                    department=_s(j.get("job_category")), source_id=str(j.get("id_icims") or j.get("id") or ""),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if fresh == 0 or len(rows) < PAGE_SIZE:
                break
            page += 1
        return jobs


PROVIDER = Amazon()
