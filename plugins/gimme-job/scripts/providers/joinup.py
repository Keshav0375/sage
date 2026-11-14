"""JoinUp (Swiss startup jobs) — Next.js page with embedded Algolia server state, board-wide.

GET https://joinup.ch/browse/jobs → __NEXT_DATA__.props.pageProps.serverState.initialResults.jobs.results[0].hits
Mechanism from career-ops providers/joinup.mjs (MIT); code is our own.
"""
from __future__ import annotations

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import dig, next_data, to_iso

BROWSE = "https://joinup.ch/browse/jobs"


class JoinUp(Provider):
    name = "joinup"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("joinup.ch",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        data = next_data(ctx.http.get_text(BROWSE))
        if data is None:
            raise ProviderError("joinup: page is missing __NEXT_DATA__ (structure changed?)")
        res = dig(data, "props.pageProps.serverState.initialResults.jobs.results", [])
        hits = res[0].get("hits") if isinstance(res, list) and res and isinstance(res[0], dict) else []
        out: list[Job] = []
        for h in hits or []:
            title = h.get("title") or h.get("headline")
            if not h.get("slug") or not title:
                continue
            loc = h.get("location")
            if isinstance(loc, dict):
                loc = loc.get("name") or loc.get("city") or ""
            out.append(self.job(
                title=title, url=f"https://joinup.ch/job/{h['slug']}", company=h.get("startup") or target.company,
                location=loc or "", country="CH", posted_at=to_iso(h.get("created")),
                source_id=str(h.get("objectID") or h["slug"]),
            ).validate())
            if len(out) >= ctx.max_jobs:
                break
        return out


PROVIDER = JoinUp()
