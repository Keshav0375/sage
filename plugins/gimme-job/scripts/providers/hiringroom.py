"""HiringRoom — microsite at https://<tenant>.hiringroom.com (JSON-LD itemList, or legacy card markup).

Mechanism from career-ops providers/hiringroom.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html as htmllib
import json
import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

TRUSTED = "hiringroom.com"
VACANCY = re.compile(r"^/jobs/get_vacancy/[a-f0-9]+$", re.I)


def _ok(url: str) -> bool:
    p = urlsplit((url or "").strip())
    host = (p.hostname or "").lower()
    return p.scheme == "https" and (host == TRUSTED or host.endswith("." + TRUSTED))


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _ld_location(loc) -> str:
    place = loc[0] if isinstance(loc, list) and loc else loc
    addr = place.get("address") if isinstance(place, dict) else None
    if isinstance(addr, str):
        return _clean(addr)
    if isinstance(addr, dict):
        return ", ".join(v.strip() for v in (addr.get(k) for k in ("addressLocality", "addressRegion", "addressCountry"))
                         if isinstance(v, str) and v.strip())
    return ""


class HiringRoom(Provider):
    name = "hiringroom"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = (TRUSTED,)

    def detect(self, careers_url: str):
        if not _ok(careers_url):
            return None
        return Target(slug=urlsplit(careers_url).hostname.split(".")[0], careers_url=careers_url, api_url=careers_url)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        url = target.careers_url or target.api_url
        if not _ok(url):
            raise ProviderError("hiringroom needs an https *.hiringroom.com url")
        p = urlsplit(url)
        origin = f"https://{p.netloc}"
        html = ctx.http.get_text(url)
        company = target.company or p.hostname.split(".")[0]
        host = p.hostname.lower()
        rows: list[dict] = []
        seen: set[str] = set()
        for m in re.finditer(r"""<script[^>]*type="application/ld\+json"[^>]*>([\s\S]*?)</script>""", html, re.I):
            try:
                data = json.loads(m.group(1))
            except ValueError:
                continue
            for el in (data.get("itemListElement") or []) if isinstance(data, dict) else []:
                post = (el or {}).get("item") if isinstance(el, dict) else None
                if not isinstance(post, dict) or post.get("@type") != "JobPosting":
                    continue
                title = _clean(post.get("title") or "")
                u = urlsplit(str(post.get("url") or ""))
                if not title or (u.hostname or "").lower() != host or not VACANCY.match(u.path):
                    continue
                link = origin + u.path
                if link in seen:
                    continue
                seen.add(link)
                rows.append(dict(title=title, url=link, location=_ld_location(post.get("jobLocation")),
                                 description=html_to_text(post.get("description") or "") if isinstance(post.get("description"), str) else "",
                                 posted_at=to_iso(post.get("datePosted"))))
        if not rows:
            ms = list(re.finditer(r'href="(/jobs/get_vacancy/[a-f0-9]+)"', html, re.I))
            for i, m in enumerate(ms):
                block = html[m.start(): ms[i + 1].start() if i + 1 < len(ms) else len(html)]
                tm = re.search(r"name__vacancy[^>]*>([\s\S]*?)</h4>", block, re.I)
                title = _clean(tm.group(1)) if tm else ""
                link = origin + m.group(1)
                if not title or link in seen:
                    continue
                seen.add(link)
                lm = re.search(r"hr-Location-pin[^>]*></i>\s*([^<]+)", block, re.I)
                rows.append(dict(title=title, url=link, location=_clean(lm.group(1)) if lm else "",
                                 description="", posted_at=""))
        return [self.job(company=company, source_id=r["url"].rstrip("/").split("/")[-1], **r).validate()
                for r in rows[: ctx.max_jobs]]


PROVIDER = HiringRoom()
