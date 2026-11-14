"""Consider-hosted job boards (VC portfolio boards) — CSRF handshake + search POST.

GET  {origin}/jobs  -> window.serverInitialData = {csrfToken, board:{id,isParent}} (+ cookie)
POST {origin}/api-boards/search-jobs {meta:{size,sequence}, board:{id,isParent}, query:{}} -> {jobs, total, meta:{sequence}}
Tenant = a careers_url on the board's own host; ``options['consider_board']`` overrides the board id.
Mechanism from career-ops providers/consider.mjs (MIT); code is our own.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

ENDPOINT = "/api-boards/search-jobs"


def _origin(url: str) -> str:
    p = urlsplit(url or "")
    host = (p.hostname or "").lower().rstrip(".")
    if p.scheme != "https" or "." not in host or re.fullmatch(r"[\d.]+", host):
        return ""
    if host.endswith((".local", ".internal")) or host.startswith("localhost"):
        return ""
    return f"https://{p.netloc}"


class Consider(Provider):
    name = "consider"
    wave = "W3"
    kind = "ats"
    tenant = True
    hosts = ()

    def detect(self, careers_url: str):
        return None  # tenant boards live on arbitrary hosts; configured explicitly

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        origin = _origin(target.careers_url)
        if not origin:
            raise ProviderError("consider needs an https careers_url on a public host")
        size = min(int(target.options.get("consider_size") or 500), 1000)
        max_pages = min(int(target.options.get("max_pages") or 10), 100)

        headers = {"Referer": origin + "/jobs"}
        board = None
        try:
            r = ctx.http.get(origin + "/jobs", headers={"Accept": "text/html,*/*"})
            m = re.search(r"window\.serverInitialData\s*=\s*(\{.*?\})\s*;?\s*(?:</script>|$)", r.text, re.M)
            data = json.loads(m.group(1)) if m else {}
            tok = data.get("csrfToken")
            if isinstance(tok, str) and len(tok) >= 8:
                headers["X-CSRF-Token"] = tok
            b = data.get("board") or {}
            if isinstance(b.get("id"), str) and b["id"].strip():
                board = {"id": b["id"].strip(), "isParent": b.get("isParent") if isinstance(b.get("isParent"), bool) else True}
            cookie = r.headers.get("set-cookie", "")
            if cookie:
                headers["Cookie"] = "; ".join(c.split(";")[0].strip() for c in re.split(r",(?=\s*\w+=)", cookie))
        except (ProviderError, ValueError):
            pass
        if target.options.get("consider_board"):
            board = {"id": str(target.options["consider_board"]), "isParent": True}
        if not board:
            raise ProviderError("consider: could not read board id (set options.consider_board)")

        jobs: list[Job] = []
        sequence = None
        for _ in range(max_pages):
            body = {"meta": {"size": size, **({"sequence": sequence} if sequence else {})},
                    "board": board, "query": {"promoteFeatured": True}}
            data = ctx.http.post_json(origin + ENDPOINT, data=body, headers=headers)
            rows = data.get("jobs") if isinstance(data, dict) else None
            rows = rows if isinstance(rows, list) else []
            for j in rows:
                raw = j.get("url") or j.get("applyUrl") or ""
                if not raw:
                    continue
                locs = [x for x in (j.get("locations") or []) if isinstance(x, str)]
                if not locs:
                    locs = [(x.get("label") or x.get("value")) for x in (j.get("normalizedLocations") or []) if isinstance(x, dict)]
                    locs = [x for x in locs if x]
                jobs.append(self.job(
                    title=j.get("title") or "", url=urljoin(origin, raw),
                    company=j.get("companyName") or target.company,
                    location=", ".join(locs) or ("Remote" if j.get("remote") else ""),
                    locations=locs, workplace="remote" if j.get("remote") else "",
                    posted_at=to_iso(j.get("timeStamp")),
                    source_id=str(j.get("jobId") or j.get("id") or ""),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            nxt = (data.get("meta") or {}).get("sequence") if isinstance(data, dict) else None
            if len(rows) < size or not nxt or nxt == sequence:
                break
            sequence = nxt
        return jobs


PROVIDER = Consider()
