"""MyCareersFuture (Singapore national job bank) — public search API, board-wide.

POST https://api.mycareersfuture.gov.sg/v2/search?limit=100&page=N  {"search": kw, "sortBy": [...], "page": N}
Mechanism from career-ops providers/mycareersfuture.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

API = "https://api.mycareersfuture.gov.sg/v2/search"
HOST = "www.mycareersfuture.gov.sg"
PAGE = 100


def _keywords(target: Target) -> list[str]:
    raw = target.options.get("keywords") or target.options.get("queries") or target.query
    if isinstance(raw, str):
        raw = [x for x in raw.replace("\n", ",").split(",")]
    return list(dict.fromkeys(str(x).strip() for x in raw or [] if str(x).strip()))


class MyCareersFuture(Provider):
    name = "mycareersfuture"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("api.mycareersfuture.gov.sg", HOST)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        kws = _keywords(target)
        if not kws:
            raise ProviderError("mycareersfuture needs target.query / options.keywords")
        max_pages = int(target.options.get("max_pages") or 5)
        seen: dict[str, Job] = {}
        for kw in kws:
            for page in range(max_pages):
                data = ctx.http.post_json(
                    f"{API}?limit={PAGE}&page={page}",
                    {"search": kw, "sortBy": ["new_posting_date"], "page": page},
                )
                results = (data or {}).get("results") or []
                for r in results:
                    meta = r.get("metadata") or {}
                    jid = str(meta.get("jobPostId") or "")
                    url = meta.get("jobDetailsUrl") or ""
                    if not jid or jid in seen or urlsplit(url).netloc != HOST:
                        continue
                    company = ((r.get("hiringCompany") or {}).get("name")
                               or (r.get("postedCompany") or {}).get("name") or "")
                    districts = [d.get("location", "") for d in (r.get("address") or {}).get("districts") or []
                                 if d and d.get("location")]
                    sal = r.get("salary") or {}
                    seen[jid] = self.job(
                        title=r.get("title", ""), url=url, company=company,
                        location=", ".join(districts), locations=districts, country="SG",
                        posted_at=to_iso(meta.get("newPostingDate")),
                        salary_min=sal.get("minimum"), salary_max=sal.get("maximum"),
                        currency="SGD" if sal.get("minimum") else "",
                        salary_period="month" if sal.get("minimum") else "",
                        source_id=jid,
                    ).validate()
                    if len(seen) >= ctx.max_jobs:
                        return list(seen.values())
                if len(results) < PAGE:
                    break
        return list(seen.values())


PROVIDER = MyCareersFuture()
