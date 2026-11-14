"""Meituan careers — POST https://zhaopin.meituan.com/api/official/job/getJobList.

Mechanism from career-ops providers/meituan.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, Target
from ._parse import to_iso

HOST = "zhaopin.meituan.com"
API = f"https://{HOST}/api/official/job/getJobList"
DETAIL = f"https://{HOST}/web/position/detail?jobUnionId="
PAGE_SIZE = 100


def _names(arr) -> list[str]:
    out = [x if isinstance(x, str) else (x or {}).get("name", "") for x in (arr or [])]
    return [n for n in out if n]


class Meituan(Provider):
    name = "meituan"
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
            data = ctx.http.post_json(API, {
                "page": {"pageNo": page, "pageSize": PAGE_SIZE}, "keywords": target.query or "",
                "jobShareType": "1", "jobType": [{"code": "3", "subCode": []}],
                "cityList": [], "department": [], "jfJgList": [], "typeCode": [], "specialCode": []})
            d = (data or {}).get("data") or {}
            rows = d.get("list")
            if not isinstance(rows, list) or not rows:
                break
            for p in rows:
                jid = str(p.get("jobUnionId") or "")
                if not p.get("name") or not jid or jid in seen:
                    continue
                seen.add(jid)
                desc = "\n".join(x for x in [p.get("jobDuty"), p.get("jobRequirement")] if x)
                jobs.append(self.job(
                    title=p["name"], url=DETAIL + quote(jid, safe=""),
                    company=target.company or "美团", locations=_names(p.get("cityList")),
                    department=", ".join(_names(p.get("department"))),
                    posted_at=to_iso(p.get("refreshTime") or p.get("firstPostTime")),
                    description=desc[:4000], source_id=jid).validate())
            total = int(((d.get("page") or {}).get("totalCount")) or 0)
            if total and page * PAGE_SIZE >= total:
                break
            page += 1
        return jobs[: ctx.max_jobs]


PROVIDER = Meituan()
