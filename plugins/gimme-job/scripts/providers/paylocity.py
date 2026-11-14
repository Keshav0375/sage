"""Paylocity Recruiting — board page embeds ``window.pageData = {... Jobs: [...]}``.

https://recruiting.paylocity.com/Recruiting/Jobs/All/<guid>
Mechanism from career-ops providers/paylocity.mjs (MIT).
"""
from __future__ import annotations

import json
import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

HOST = "recruiting.paylocity.com"
GUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
REMOTE_LABELS = {"0": "Remote", "1": "Hybrid", "2": "Remote"}


def _guid(url: str) -> str:
    p = urlsplit((url or "").strip())
    if p.scheme != "https" or p.netloc.lower() != HOST:
        return ""
    m = re.match(r"^/recruiting/jobs/all/([^/?#]+)", p.path, re.I)
    return m.group(1).lower() if m and GUID_RE.match(m.group(1)) else ""


class Paylocity(Provider):
    name = "paylocity"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = (HOST,)

    def detect(self, careers_url: str):
        g = _guid(careers_url)
        if not g:
            return None
        return Target(slug=g, careers_url=careers_url, api_url=f"https://{HOST}/Recruiting/Jobs/All/{g}")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        g = _guid(target.api_url) or _guid(target.careers_url)
        if not g:
            raise ProviderError("paylocity needs a recruiting.paylocity.com/Recruiting/Jobs/All/<guid> url")
        page = ctx.http.get_text(f"https://{HOST}/Recruiting/Jobs/All/{g}")
        m = re.search(r"window\.pageData\s*=\s*(\{.*?\});\s*</script>", page, re.S)
        if not m:
            raise ProviderError("paylocity: window.pageData not found")
        try:
            data = json.loads(m.group(1))
        except ValueError as e:
            raise ProviderError(f"paylocity: bad pageData JSON: {e}") from e
        rows = data.get("Jobs")
        if not isinstance(rows, list):
            raise ProviderError("paylocity: pageData has no Jobs[]")
        company = target.company or str(data.get("ModuleTitle") or "").strip()
        jobs: list[Job] = []
        for r in rows:
            if not isinstance(r, dict) or r.get("IsInternal") is True:
                continue
            title = str(r.get("JobTitle") or "").strip()
            jid = str(r.get("JobId") or "").strip()
            if not title or not jid:
                continue
            place = r.get("JobLocation") if isinstance(r.get("JobLocation"), dict) else {}
            hidden = r.get("ShouldDisplayLocation") is False
            name = "" if hidden else str(r.get("LocationName") or "").strip()
            parts = [] if hidden else ([name] if name else [x for x in (str(place.get("City") or "").strip(), str(place.get("State") or "").strip()) if x])
            mode = REMOTE_LABELS.get(str(r.get("IndeedRemoteType"))) if r.get("IsRemote") is True else None
            if mode:
                parts.append(mode)
            jobs.append(self.job(
                title=title, url=f"https://{HOST}/Recruiting/Jobs/Details/{quote(jid, safe='')}", company=company,
                location=", ".join(parts), workplace={"Remote": "remote", "Hybrid": "hybrid"}.get(mode or "", ""),
                posted_at=to_iso(r.get("PublishedDate")), source_id=jid).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Paylocity()
