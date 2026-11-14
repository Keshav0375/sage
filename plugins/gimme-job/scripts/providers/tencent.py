"""Tencent careers — GET https://careers.tencent.com/tencentcareer/api/post/Query.

Mechanism from career-ops providers/tencent.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
import time
from urllib.parse import urlencode, urlsplit

from ._base import Context, Job, Provider, Target

HOST = "careers.tencent.com"
API = f"https://{HOST}/tencentcareer/api/post/Query"
PAGE_SIZE = 100


def _cn_date(v) -> str:
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", str(v or ""))
    return f"{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}" if m else ""


class Tencent(Provider):
    name = "tencent"
    wave = "W6"
    kind = "company"
    tenant = False
    hosts = (HOST,)

    def detect(self, careers_url: str):
        if urlsplit(careers_url or "").netloc.lower() == HOST:
            return Target(careers_url=careers_url)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        jobs: list[Job] = []
        seen: set[str] = set()
        page = 1
        while len(jobs) < ctx.max_jobs:
            q = urlencode({"timestamp": int(time.time() * 1000), "keyword": target.query or "",
                           "pageIndex": page, "pageSize": PAGE_SIZE, "language": "zh-cn"})
            data = ctx.http.get_json(f"{API}?{q}")
            d = (data or {}).get("Data") or {}
            posts = d.get("Posts")
            if not isinstance(posts, list) or not posts:
                break
            for p in posts:
                title = p.get("RecruitPostName") or ""
                url = p.get("PostURL") or (
                    f"https://careers.tencent.com/jobdesc.html?postId={p['PostId']}" if p.get("PostId") else "")
                if not title or not url or url in seen:
                    continue
                seen.add(url)
                loc = "-".join(x for x in [p.get("CountryName"), p.get("LocationName")] if x)
                desc = "\n".join(x for x in [p.get("Responsibility")] if x)
                jobs.append(self.job(
                    title=title, url=url, company=target.company or "腾讯", location=loc,
                    department=p.get("BGName") or "", description=desc,
                    posted_at=_cn_date(p.get("LastUpdateTime")),
                    source_id=str(p.get("PostId") or "")).validate())
            if page * PAGE_SIZE >= int(d.get("Count") or 0):
                break
            page += 1
        return jobs[: ctx.max_jobs]


PROVIDER = Tencent()
