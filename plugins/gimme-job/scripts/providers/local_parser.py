"""Generic careers-page parser — works on any HTML careers page (no vendor API).

1. schema.org JobPosting JSON-LD on the page (via _parse.json_ld_jobs) — richest data.
2. Otherwise anchors whose href or text looks like a job posting.
URL from Target.careers_url; company from Target.company. Upstream ran a user script; we parse the page ourselves.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import absolute, employment_from, html_to_text, json_ld_jobs, links, to_iso

HREF_JOB = re.compile(r"/(jobs?|careers?|positions?|openings?|vacanc(?:y|ies)|requisitions?|apply|postings?|roles?)/[^/?#\s]+", re.I)
TEXT_ROLE = re.compile(r"\b(engineer|developer|manager|designer|analyst|scientist|director|specialist|architect|"
                       r"consultant|lead|intern|recruiter|researcher|product|marketing|sales|support|devops|sre|qa)\b", re.I)
NAV_TEXT = re.compile(r"^(careers?|jobs?|all jobs|view (all )?jobs?|open (positions|roles)|apply( now)?|learn more|"
                      r"read more|home|about|contact|login|sign in|back|next|previous|see all.*)$", re.I)


def _loc(d: dict) -> str:
    locs = d.get("jobLocation")
    locs = locs if isinstance(locs, list) else [locs]
    out = []
    for l in locs:
        a = (l or {}).get("address") if isinstance(l, dict) else None
        if isinstance(a, str):
            out.append(a)
        elif isinstance(a, dict):
            c = a.get("addressCountry")
            c = c.get("name") if isinstance(c, dict) else c
            out.append(", ".join(dict.fromkeys(str(x).strip() for x in (a.get("addressLocality"), a.get("addressRegion"), c) if x and str(x).strip())))
    return "; ".join(x for x in out if x)


class LocalParser(Provider):
    name = "local-parser"
    wave = "W3"
    kind = "feed"
    tenant = True
    hosts = ()

    def detect(self, careers_url: str):
        return None  # generic fallback; chosen explicitly

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        url = (target.careers_url or "").strip()
        if not url.startswith(("http://", "https://")):
            raise ProviderError("local-parser needs an http(s) careers_url")
        html = ctx.http.get_text(url)
        jobs: list[Job] = []
        seen: set[str] = set()

        for d in json_ld_jobs(html):
            title = html_to_text(str(d.get("title") or d.get("name") or "")).strip()
            raw = d.get("url") or d.get("sameAs") or ""
            if isinstance(d.get("identifier"), dict) and not raw:
                raw = ""
            href = absolute(url, raw) if raw else url
            org = d.get("hiringOrganization")
            company = (org.get("name") if isinstance(org, dict) else org) or target.company
            if not title:
                continue
            key = href if raw else f"{href}#{title}"
            if key in seen:
                continue
            seen.add(key)
            sal = ((d.get("baseSalary") or {}).get("value") or {}) if isinstance(d.get("baseSalary"), dict) else {}
            ident = d.get("identifier")
            jobs.append(self.job(
                title=title, url=href, company=str(company or ""), location=_loc(d),
                workplace="remote" if str(d.get("jobLocationType")).upper() == "TELECOMMUTE" else "",
                employment=employment_from(d.get("employmentType") if isinstance(d.get("employmentType"), str) else ""),
                posted_at=to_iso(d.get("datePosted")), closes_at=to_iso(d.get("validThrough")),
                salary_min=float(sal["minValue"]) if isinstance(sal.get("minValue"), (int, float)) else None,
                salary_max=float(sal["maxValue"]) if isinstance(sal.get("maxValue"), (int, float)) else None,
                currency=str((d.get("baseSalary") or {}).get("currency") or "") if isinstance(d.get("baseSalary"), dict) else "",
                description=html_to_text(d.get("description") or ""),
                source_id=str((ident.get("value") if isinstance(ident, dict) else ident) or ""),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                return jobs
        if jobs:
            return jobs

        base_host = urlsplit(url).netloc.lower()
        for href, text in links(html):
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            full = absolute(url, href).split("#")[0]
            if not full.startswith(("http://", "https://")) or full.rstrip("/") == url.rstrip("/") or full in seen:
                continue
            if not text or len(text) < 4 or len(text) > 140 or NAV_TEXT.match(text.strip()):
                continue
            if not (HREF_JOB.search(urlsplit(full).path) and (TEXT_ROLE.search(text) or urlsplit(full).netloc.lower() != base_host)
                    or (TEXT_ROLE.search(text) and HREF_JOB.search(full))):
                continue
            seen.add(full)
            jobs.append(self.job(title=text, url=full, company=target.company).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = LocalParser()
