"""Deel job boards — https://jobs.deel.com/<slug> (Next.js RSC flight stream carries jobPostings).

Mechanism from career-ops providers/deel.mjs (MIT); code is our own.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

HOST = "jobs.deel.com"
SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
PUSH = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')


def _slug(url: str) -> str:
    p = urlsplit((url or "").strip())
    if p.scheme != "https" or (p.hostname or "").lower() != HOST:
        return ""
    parts = [x for x in p.path.split("/") if x]
    return parts[0] if parts and SLUG.match(parts[0]) else ""


def _stream(html: str) -> str:
    out = []
    for m in PUSH.finditer(html):
        try:
            out.append(json.loads('"' + m.group(1) + '"'))
        except ValueError:
            continue
    return "".join(out)


def _text_rows(stream: str) -> dict[str, str]:
    """Rows '<id>:T<hexlen>,<payload>' (length in UTF-8 bytes). Best effort."""
    b = stream.encode("utf-8")
    texts: dict[str, str] = {}
    o = 0
    while o < len(b):
        colon = b.find(b":", o)
        if colon < 0:
            break
        rid = b[o:colon].decode("utf-8", "replace")
        if not re.fullmatch(r"[0-9a-f]*", rid):
            break
        if b[colon + 1:colon + 2] == b"T":
            comma = b.find(b",", colon + 2)
            if comma < 0:
                break
            hx = b[colon + 2:comma].decode("utf-8", "replace")
            if not re.fullmatch(r"[0-9a-f]+", hx):
                break
            n = int(hx, 16)
            texts[rid] = b[comma + 1:comma + 1 + n].decode("utf-8", "replace")
            o = comma + 1 + n
            if b[o:o + 1] == b"\n":
                o += 1
        else:
            nl = b.find(b"\n", colon + 1)
            o = len(b) if nl < 0 else nl + 1
    return texts


def _array_at(stream: str, start: int):
    return json.JSONDecoder().raw_decode(stream[start:])[0]


def _location(job) -> str:
    places = []
    for jl in (job or {}).get("jobLocations") or []:
        loc = (jl or {}).get("location") or {}
        name = (loc.get("name") or "").strip()
        if not name:
            continue
        country = ((loc.get("country") or {}).get("name") or "").strip() if isinstance(loc.get("country"), dict) else ""
        places.append(f"{name}, {country}" if country and country.lower() not in name.lower() else name)
    text = "; ".join(places)
    if (job or {}).get("workArrangementEnum") == "REMOTE" and not re.search("remote", text, re.I):
        text = f"{text}; Remote" if text else "Remote"
    return text


class Deel(Provider):
    name = "deel"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = (HOST,)

    def detect(self, careers_url: str):
        s = _slug(careers_url)
        return Target(slug=s, careers_url=careers_url, api_url=f"https://{HOST}/{s}") if s else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        slug = target.slug or _slug(target.careers_url)
        if not slug:
            raise ProviderError("deel needs https://jobs.deel.com/<slug>")
        html = ctx.http.get_text(f"https://{HOST}/{slug}")
        if re.search(r"<title>\s*Job Board Not Found\s*</title>", html, re.I):
            raise ProviderError(f"deel: no board at jobs.deel.com/{slug}")
        stream = _stream(html)
        if not stream:
            raise ProviderError("deel: page carries no Next.js flight data")
        i = stream.find('"jobPostings":[')
        if i < 0:
            raise ProviderError("deel: no jobPostings in page payload")
        rows = _array_at(stream, i + len('"jobPostings":'))
        texts = _text_rows(stream) if any(
            isinstance(r, dict) and str(r.get("richtextDescription", "")).startswith("$") for r in rows) else {}
        jobs: list[Job] = []
        for r in rows[: ctx.max_jobs]:
            if not isinstance(r, dict) or not (r.get("title") or "").strip() or not isinstance(r.get("id"), str):
                continue
            pub = None
            for p in r.get("jobPostingPublications") or []:
                st = (p or {}).get("currentState") or {}
                if str(st.get("stateSlug", "")).startswith("published"):
                    pub = st
                    break
            ref = r.get("richtextDescription")
            html_desc = ""
            if isinstance(ref, str):
                html_desc = texts.get(ref[1:], "") if re.fullmatch(r"\$[0-9a-f]+", ref) else ref
            job = r.get("job") or {}
            jobs.append(self.job(
                title=r["title"], url=f"https://{HOST}/{slug}/job-details/{r['id']}/overview",
                company=target.company or slug, location=_location(job),
                workplace="remote" if job.get("workArrangementEnum") == "REMOTE" else "",
                posted_at=to_iso((pub or {}).get("createdAt") or r.get("createdAt")),
                description=html_to_text(html_desc) if html_desc else "", source_id=r["id"],
            ).validate())
        return jobs


PROVIDER = Deel()
