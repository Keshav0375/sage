"""The Hub (Nordic startup jobs) — public jobs feed, board-wide.

GET https://thehub.io/api/v2/jobsandfeatured?page=N&countryCode=<CC> [&isRemote=true]
Mechanism from career-ops providers/thehub.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import quote

from ._base import Context, Job, Provider, ProviderError, Target

FEED = "https://thehub.io/api/v2/jobsandfeatured"
PER_PAGE = 15


class TheHub(Provider):
    name = "thehub"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("thehub.io",)

    def _scope(self, query: str, max_pages: int, ctx: Context, out: dict[str, Job], state: dict) -> None:
        for page in range(1, max_pages + 1):
            try:
                data = ctx.http.get_json(f"{FEED}?page={page}&{query}")
                jobs = (data or {}).get("jobs")
                if not isinstance(jobs, dict) or not isinstance(jobs.get("docs"), list):
                    raise ProviderError("thehub: unexpected response, expected {jobs: {docs: [...]}}")
            except ProviderError:
                if not state["ok"]:
                    raise
                return
            state["ok"] = True
            for j in jobs["docs"]:
                jid = str(j.get("id") or "").strip()
                title = str(j.get("title") or "").strip()
                if not jid or not title:
                    continue
                url = f"https://thehub.io/jobs/{quote(jid, safe='')}"
                if url in out:
                    continue
                loc = j.get("location") or {}
                base = (loc.get("address") or "").strip() or ", ".join(
                    x.strip() for x in (loc.get("locality") or "", loc.get("country") or "") if x and x.strip())
                remote = j.get("isRemote") is True
                label = ", ".join(x for x in (base, "Remote" if remote else "") if x)
                out[url] = self.job(
                    title=title, url=url, company=((j.get("company") or {}).get("name") or "").strip(),
                    location=label, workplace="remote" if remote else "", source_id=jid,
                ).validate()
                if len(out) >= ctx.max_jobs:
                    return
            if len(jobs["docs"]) < PER_PAGE or (isinstance(jobs.get("pages"), int) and page >= jobs["pages"]):
                return

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = target.options
        cc = (o.get("countryCode") or target.location or "EU").strip()
        max_pages = min(int(o.get("max_pages") or 3), 67)
        out: dict[str, Job] = {}
        state = {"ok": False}
        self._scope(f"countryCode={quote(cc)}", max_pages, ctx, out, state)
        if o.get("includeRemote") and len(out) < ctx.max_jobs:
            self._scope("isRemote=true", max_pages, ctx, out, state)
        return list(out.values())


PROVIDER = TheHub()
