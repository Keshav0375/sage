"""Alibaba Group careers — POST https://talent.alibaba.com/position/search.

Mechanism from career-ops providers/alibaba.mjs (MIT); code is our own.
"""
from __future__ import annotations

import uuid
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

API = "https://talent.alibaba.com/position/search"
DETAIL = "https://talent.alibaba.com/off-campus/position-detail?positionId="
PAGE_SIZE = 100


class Alibaba(Provider):
    name = "alibaba"
    wave = "W6"
    kind = "company"
    tenant = False
    hosts = ("talent.alibaba.com",)

    def detect(self, careers_url: str):
        if urlsplit(careers_url or "").netloc.lower() == "talent.alibaba.com":
            return Target(careers_url=careers_url)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        token = str(uuid.uuid4())
        headers = {"content-type": "application/json", "cookie": f"XSRF-TOKEN={token}", "x-xsrf-token": token}
        key = target.query or ""
        jobs: list[Job] = []
        page = 1
        while len(jobs) < ctx.max_jobs:
            data = ctx.http.post_json(API, {
                "channel": "group_official_site", "language": "zh", "batchId": "", "categories": "",
                "deptCodes": [], "key": key, "pageIndex": page, "pageSize": PAGE_SIZE,
                "regions": "", "subCategories": ""}, headers=headers)
            if isinstance(data, dict) and data.get("success") is False:
                raise ProviderError(f"alibaba: {data.get('errorMsg') or data.get('errorCode')}")
            content = (data or {}).get("content") or {}
            rows = content.get("datas")
            if not isinstance(rows, list) or not rows:
                break
            for p in rows:
                if not p.get("name") or p.get("id") is None:
                    continue
                cats = [c for c in p.get("categories") or [] if c]
                desc = "\n".join(x for x in [p.get("description"), p.get("requirement")] if x)
                jobs.append(self.job(
                    title=p["name"], url=DETAIL + quote(str(p["id"])),
                    company=target.company or "阿里巴巴",
                    locations=[x for x in p.get("workLocations") or [] if x],
                    posted_at=to_iso(p.get("publishTime") or p.get("modifyTime")),
                    description=desc[:4000], department=cats[0] if cats else "",
                    source_id=str(p["id"])).validate())
            total = int(content.get("totalCount") or 0)
            if page * PAGE_SIZE >= total:
                break
            page += 1
        return jobs[: ctx.max_jobs]


PROVIDER = Alibaba()
