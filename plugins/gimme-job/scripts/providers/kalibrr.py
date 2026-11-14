"""Kalibrr (PH/ID) — public job_board search JSON.

GET https://www.kalibrr.com/kjs/job_board/search?limit=100&offset=N&text=<kw>
Mechanism from career-ops providers/kalibrr.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import quote, urlencode

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

API = "https://www.kalibrr.com/kjs/job_board/search"
SITE = "https://www.kalibrr.com"


class Kalibrr(Provider):
    name = "kalibrr"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("www.kalibrr.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        size = min(int(target.options.get("page_size") or 100), 500)
        pages = min(int(target.options.get("max_pages") or 3), 200)
        jobs: list[Job] = []
        seen: set[str] = set()
        offset, total = 0, None
        for _ in range(pages):
            q = {"limit": size, "offset": offset}
            if target.query:
                q["text"] = target.query
            data = ctx.http.get_json(f"{API}?{urlencode(q)}")
            if not data:
                break
            if "jobs" not in data:
                raise ProviderError("kalibrr: unexpected response, expected {jobs: [...]}")
            rows = data["jobs"] or []
            if not isinstance(rows, list):
                raise ProviderError("kalibrr: `jobs` is not an array")
            if total is None and isinstance(data.get("count"), int):
                total = data["count"]
            for r in rows:
                jid = str(r.get("id") or "").strip()
                title = str(r.get("name") or "").strip()
                if not jid or not title:
                    continue
                co = r.get("company") or {}
                code = str(co.get("code") or "").strip() or "-"
                slug = str(r.get("slug") or "").strip()
                url = f"{SITE}/c/{quote(code, safe='')}/jobs/{quote(jid, safe='')}" + (f"/{quote(slug, safe='')}" if slug else "")
                if url in seen:
                    continue
                seen.add(url)
                addr = (r.get("google_location") or {}).get("address_components") or {}
                parts: list[str] = []
                for k in ("city", "region", "country"):
                    v = str(addr.get(k) or "").strip()
                    if v and v not in parts:
                        parts.append(v)
                remote = r.get("is_work_from_home") is True
                jobs.append(self.job(
                    title=title, url=url,
                    company=str(co.get("name") or r.get("company_name") or "").strip(),
                    location=", ".join(parts + (["Remote"] if remote else [])), locations=parts,
                    workplace="remote" if remote else "",
                    posted_at=to_iso(r.get("activation_date") or r.get("created_at")),
                    description=html_to_text(" ".join(x for x in (r.get("description"), r.get("qualifications")) if x)),
                    source_id=jid,
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            offset += size
            if (total is not None and offset >= total) or len(rows) < size:
                break
        return jobs


PROVIDER = Kalibrr()
