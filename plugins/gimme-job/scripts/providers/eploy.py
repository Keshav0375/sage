"""Eploy — vacancy sitemap https://<host>/live-jobs.xml (titles derived from URL slugs).

Mechanism from career-ops providers/eploy.mjs (MIT); code is our own.
Simplified: sitemap only (no per-vacancy detail enrichment).
"""
from __future__ import annotations

import html as htmllib
import re
from urllib.parse import unquote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

JOB_PATH = re.compile(r"^/vacancies/(\d+)/([^/?#]+)\.html/?$", re.I)
ACRONYMS = {"ai": "AI", "api": "API", "cio": "CIO", "cto": "CTO", "eu": "EU", "hcm": "HCM", "hr": "HR", "it": "IT",
            "ml": "ML", "qa": "QA", "uk": "UK", "ui": "UI", "ux": "UX"}


def _origin(url: str) -> str:
    p = urlsplit((url or "").strip())
    if p.scheme != "https" or p.username or p.password or p.port:
        return ""
    host = (p.hostname or "").lower().rstrip(".")
    if (not host or ":" in host or re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host) or host.startswith("localhost")
            or host.endswith((".local", ".internal")) or "." not in host):
        return ""
    return f"https://{host}"


def title_from_slug(slug: str) -> str:
    out = []
    for seg in re.split(r"--+", unquote(slug)):
        words = re.sub(r"[-_\s]+", " ", seg).strip().split(" ")
        t = " ".join(ACRONYMS.get(w.lower()) or (w[:1].upper() + w[1:]) for w in words if w)
        if t:
            out.append(t)
    return " - ".join(out)


class Eploy(Provider):
    name = "eploy"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("eploy.net",)

    def detect(self, careers_url: str):
        p = urlsplit((careers_url or "").strip())
        host = (p.hostname or "").lower()
        if p.scheme != "https" or not host.endswith(".eploy.net") or host == "eploy.net":
            return None
        return Target(slug=host.split(".")[0], careers_url=careers_url, api_url=f"https://{host}/live-jobs.xml")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = _origin(target.careers_url) or _origin(target.api_url)
        if not o:
            raise ProviderError("eploy needs a public https careers_url")
        host = urlsplit(o).hostname
        xml = ctx.http.get_text(f"{o}/live-jobs.xml")
        if not xml.strip():
            return []
        if not re.search(r"<urlset\b[^>]*>", xml, re.I):
            raise ProviderError("eploy: unexpected live-jobs.xml response (expected an XML urlset)")
        company = target.company or host.split(".")[0]
        jobs: list[Job] = []
        seen: set[str] = set()
        for m in re.finditer(r"<url\b[^>]*>([\s\S]*?)</url\s*>", xml, re.I):
            lm = re.search(r"<loc\b[^>]*>([\s\S]*?)</loc\s*>", m.group(1), re.I)
            if not lm:
                continue
            u = urlsplit(htmllib.unescape(lm.group(1).strip()))
            uh = (u.hostname or "").lower().rstrip(".")
            if (u.scheme != "https" or u.username or u.port or u.query or u.fragment
                    or not (uh == host or (uh.endswith(".eploy.net") and uh != "eploy.net"))):
                continue
            pm = JOB_PATH.match(u.path)
            if not pm or pm.group(1) in seen:
                continue
            title = title_from_slug(pm.group(2))
            if not title:
                continue
            seen.add(pm.group(1))
            jobs.append(self.job(title=title, url=f"https://{uh}{u.path}", company=company,
                                 source_id=pm.group(1)).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Eploy()
