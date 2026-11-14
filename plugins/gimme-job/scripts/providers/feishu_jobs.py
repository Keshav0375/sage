"""Feishu Jobs (ByteDance and *.jobs.feishu.cn tenants) — POST {origin}/api/v1/search/job/posts.

Mechanism from career-ops providers/feishu-jobs.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

PAGE_SIZE = 100


def _origin(url: str) -> str:
    p = urlsplit(url or "")
    h = p.netloc.lower()
    if p.scheme == "https" and (h == "jobs.bytedance.com" or h.endswith(".jobs.feishu.cn")):
        return f"https://{p.netloc}"
    return ""


class FeishuJobs(Provider):
    name = "feishu-jobs"
    wave = "W6"
    kind = "ats"
    tenant = True
    hosts = ("jobs.bytedance.com", "jobs.feishu.cn")

    def detect(self, careers_url: str):
        o = _origin(careers_url)
        if not o:
            return None
        return Target(slug=urlsplit(o).netloc, careers_url=careers_url, api_url=f"{o}/api/v1/search/job/posts")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        origin = _origin(target.careers_url)
        if not origin:
            raise ProviderError("feishu-jobs: careers_url must be https on jobs.bytedance.com or *.jobs.feishu.cn")
        api = f"{origin}/api/v1/search/job/posts"
        headers = {"Referer": origin + "/", "Accept": "application/json"}
        jobs: list[Job] = []
        seen: set[str] = set()
        offset = 0
        while len(jobs) < ctx.max_jobs:
            body = {"limit": PAGE_SIZE, "offset": offset}
            if target.query:
                body["keyword"] = target.query
            data = ctx.http.post_json(api, body, headers=headers)
            if (data or {}).get("code") != 0:
                raise ProviderError(f"feishu-jobs: API error code={(data or {}).get('code')}")
            d = data.get("data") or {}
            rows = d.get("job_post_list")
            if not isinstance(rows, list) or not rows:
                break
            for p in rows:
                pid = p.get("id")
                if not p.get("title") or pid is None or str(pid) in seen:
                    continue
                seen.add(str(pid))
                path = "/experienced/position/{}/detail" if origin == "https://jobs.bytedance.com" \
                    else "/index/position/{}/detail"
                desc = "\n".join(x for x in [p.get("description"), p.get("requirement")] if x)
                jobs.append(self.job(
                    title=p["title"], url=origin + path.format(quote(str(pid), safe="")),
                    company=target.company or urlsplit(origin).netloc,
                    locations=[c.get("name") for c in p.get("city_list") or [] if (c or {}).get("name")],
                    department=(p.get("job_category") or {}).get("name", ""),
                    posted_at=to_iso(p.get("publish_time")), description=desc[:4000],
                    source_id=str(pid)).validate())
            offset += PAGE_SIZE
            if offset >= int(d.get("count") or 0):
                break
        return jobs[: ctx.max_jobs]


PROVIDER = FeishuJobs()
