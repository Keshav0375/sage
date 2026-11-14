"""TurboHire — https://<tenant>.turbohire.co careers site backed by thapi.azurewebsites.net.

Flow: anonymous token → org id lookup → POST careerpagev2/filteredjobs.
Mechanism from career-ops providers/turbohire.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html as htmllib
import json
import re
from urllib.parse import quote, unquote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

API = "https://thapi.azurewebsites.net"
HOST = re.compile(r"^([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)\.turbohire\.co$")
VENDOR = {"app", "api", "www"}
ORG_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
NIL = "00000000-0000-0000-0000-000000000000"


def _tenant(url: str) -> str:
    p = urlsplit((url or "").strip())
    m = HOST.match((p.hostname or "").lower()) if p.scheme == "https" else None
    return m.group(1) if m and m.group(1) not in VENDOR else ""


def _clean(v) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(v)).strip() if isinstance(v, str) else ""


def _location(raw) -> str:
    sites = raw
    if isinstance(raw, str):
        t = raw.strip()
        if not t:
            return ""
        try:
            sites = json.loads(t)
        except ValueError:
            return "" if t[0] in "[{" else _clean(t)
    if not isinstance(sites, list):
        return ""
    parts: list[str] = []
    for s in sites:
        a = _clean(s.get("Address")) if isinstance(s, dict) else ""
        if a and a not in parts:
            parts.append(a)
    return "; ".join(parts)


class TurboHire(Provider):
    name = "turbohire"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("turbohire.co", "thapi.azurewebsites.net")

    def detect(self, careers_url: str):
        t = _tenant(careers_url)
        return Target(slug=t, careers_url=careers_url, api_url=f"https://{t}.turbohire.co/") if t else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = target.slug or _tenant(target.api_url) or _tenant(target.careers_url)
        if not t:
            raise ProviderError("turbohire needs https://<tenant>.turbohire.co/")
        origin = f"https://{t}.turbohire.co"
        tok = ctx.http.get_json(f"{API}/api/token/noauth",
                                headers={"Accept": "application/json", "Origin": origin, "Referer": origin + "/"})
        token = (tok or {}).get("access_token") if isinstance(tok, dict) else None
        if not isinstance(token, str) or not token.strip():
            raise ProviderError("turbohire: anonymous token request returned no access_token")
        auth = {"Accept": "application/json", "Authorization": f"Bearer {token.strip()}"}
        org = ctx.http.get_json(f"{API}/api/publicorganizations?accountName={t}", headers=auth)
        org_id = (org or {}).get("OrgID") if isinstance(org, dict) else None
        if not isinstance(org_id, str) or not ORG_ID.match(org_id) or org_id == NIL:
            raise ProviderError(f"turbohire: organization lookup for {t!r} returned no org id")
        data = ctx.http.post_json(f"{API}/api/careerpagev2/filteredjobs?orgId={org_id}&pageType=0", {}, headers=auth)
        rows = data.get("Result") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ProviderError("turbohire: unexpected response, expected a Result array")
        company = target.company or t
        jobs: list[Job] = []
        seen: set[str] = set()
        for r in rows:
            if not isinstance(r, dict):
                continue
            title = _clean(r.get("JobTitle"))
            raw_id = str(r.get("JobIdObfuscated") or "").strip()
            if not title or not raw_id:
                continue
            url = f"{origin}/job/publicjobs/{quote(unquote(raw_id), safe='')}"
            if url in seen:
                continue
            seen.add(url)
            employer = company
            if r.get("ShowClientName") is True:
                cn = _clean(r.get("ClientName"))
                if cn and cn != "[REDACTED]" and re.sub(r"[^a-z0-9]", "", cn.lower()) != re.sub(r"[^a-z0-9]", "", company.lower()):
                    employer = cn
            jobs.append(self.job(
                title=title, url=url, company=employer, location=_location(r.get("Location")),
                posted_at=to_iso(r.get("PublishedDate")), description=html_to_text(r.get("JobDescV2") or ""),
                source_id=str(r.get("JobCode") or ""),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = TurboHire()
