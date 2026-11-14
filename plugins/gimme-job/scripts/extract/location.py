"""City, region, country, workplace, remote regions."""
from __future__ import annotations

import re

from ..providers._parse import workplace_from

CA_PROV = {"ON": "Ontario", "QC": "Quebec", "BC": "British Columbia", "AB": "Alberta", "MB": "Manitoba",
           "SK": "Saskatchewan", "NS": "Nova Scotia", "NB": "New Brunswick", "NL": "Newfoundland and Labrador",
           "PE": "Prince Edward Island", "NT": "Northwest Territories", "YT": "Yukon", "NU": "Nunavut"}
US_STATES = {"CA", "NY", "TX", "WA", "MA", "IL", "CO", "VA", "FL", "GA", "NC", "OR", "PA", "NJ", "AZ", "MN", "UT", "OH", "MI", "MD", "DC"}
COUNTRIES = {"canada": "CA", "united states": "US", "united states of america": "US", "usa": "US", "u.s.": "US",
             "united kingdom": "GB", "uk": "GB", "germany": "DE", "france": "FR", "india": "IN", "ireland": "IE",
             "australia": "AU", "netherlands": "NL", "spain": "ES", "singapore": "SG", "poland": "PL"}
_PROV_NAMES = {v.lower(): k for k, v in CA_PROV.items()}
_NAME_ALT = "|".join(sorted((re.escape(v) for v in CA_PROV.values()), key=len, reverse=True))
_CITY_PROV = re.compile(r"\b([A-Z][A-Za-z.'\-]+(?: [A-Z][A-Za-z.'\-]+){0,2}),\s*(" + "|".join(CA_PROV) + r"|" + _NAME_ALT + r")\b")
_CITY_US = re.compile(r"\b([A-Z][A-Za-z.'\-]+(?: [A-Z][A-Za-z.'\-]+){0,2}),\s*(" + "|".join(sorted(US_STATES)) + r")\b(?!\w)")
_COUNTRY_RE = re.compile(r"\b(" + "|".join(sorted((re.escape(c) for c in COUNTRIES), key=len, reverse=True)) + r")\b", re.I)

_HYBRID = re.compile(r"\bhybrid\b(?!\s+cloud)", re.I)
_REMOTE = re.compile(r"fully remote|100% remote|remote[- ]first|remote[- ]only|"
                     r"(?:this|the) (?:is a |position is |role is )?(?:fully )?remote (?:position|role|job|opportunity)|"
                     r"work (?:fully )?remotely|work from home|location:\s*remote|remote\s*\(|\bremote work\b", re.I)
_ONSITE = re.compile(r"on-?site (?:position|role|only|work)|(?:this|the) (?:is an |position is |role is )?on-?site|"
                     r"work from (?:the|our) office|in-?office (?:position|role)|in-?person (?:position|role)", re.I)
_REMOTE_REGION = re.compile(
    r"remote(?:ly)?(?:\s*[-–:(,]\s*|\s+(?:within|in|across|from|anywhere in)\s+(?:the\s+)?)"
    r"(Canada|United States|USA|U\.S\.|US|UK|United Kingdom|EU|Europe|EMEA|APAC|North America|LATAM)\b", re.I)
_REGION_ISO = {"canada": "CA", "united states": "US", "usa": "US", "u.s.": "US", "us": "US", "uk": "GB",
               "united kingdom": "GB", "eu": "EU", "europe": "EU", "emea": "EMEA", "apac": "APAC",
               "north america": "NA", "latam": "LATAM"}


def _country_from(s: str) -> str:
    m = _COUNTRY_RE.search(s or "")
    return COUNTRIES[m.group(1).lower()] if m else ""


def _place(s: str) -> dict:
    out: dict = {}
    m = _CITY_PROV.search(s)
    if m:
        out["city"] = m.group(1)
        prov = m.group(2)
        out["region"] = prov.upper() if prov.upper() in CA_PROV else _PROV_NAMES.get(prov.lower(), prov)
        out["country"] = "CA"
        return out
    m = _CITY_US.search(s)
    if m:
        out.update(city=m.group(1), region=m.group(2), country="US")
        return out
    low = (s or "").lower()
    for name, code in _PROV_NAMES.items():
        if re.search(r"\b" + re.escape(name) + r"\b", low):
            out.update(region=code, country="CA")
            break
    c = _country_from(s)
    if c:
        out["country"] = c
    return out


def extract(text: str, job: dict | None = None) -> dict:
    job = job or {}
    text = text or ""
    out: dict = {}
    loc = (job.get("location") or "").strip()
    if not loc:
        m = re.search(r"(?im)^\s*(?:job\s+)?locations?\s*[:\-]\s*(.+)$", text)
        loc = m.group(1).strip() if m else ""
    if loc:
        out.update(_place(loc))
    if not out.get("country") and job.get("country"):
        out["country"] = str(job["country"]).upper()[:2]
    if not out:
        m = _CITY_PROV.search(text)
        if m:
            out.update(_place(m.group(0)))
    # workplace: dedicated field first, then explicit statements only
    wp = workplace_from(job.get("workplace"))
    if not wp:
        if _HYBRID.search(text):
            wp = "hybrid"
        elif _REMOTE.search(text):
            wp = "remote"
        elif _ONSITE.search(text):
            wp = "onsite"
    if wp:
        out["workplace"] = wp
    regions: list[str] = []
    for m in _REMOTE_REGION.finditer(text):
        code = _REGION_ISO.get(m.group(1).lower(), m.group(1))
        if code not in regions:
            regions.append(code)
    if regions:
        out["remote_regions"] = regions
    return out
