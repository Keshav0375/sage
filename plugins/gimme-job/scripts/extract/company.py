"""Explicit company size / industry hints."""
from __future__ import annotations

import re

_SIZE = re.compile(r"\b(?:over |more than |approximately |about |around )?(\d{1,3}(?:,\d{3})+|\d{2,6})\+?\s*(?:employees|team members|people worldwide|professionals|colleagues|associates)\b", re.I)
_SIZE_RANGE = re.compile(r"\b(\d{1,5}\s*-\s*\d{1,5})\s*employees\b", re.I)
_STAGE = re.compile(r"\b(early[- ]stage startup|seed[- ]stage|series [a-e]\b|pre-?seed|startup)\b", re.I)
_INDUSTRY_LINE = re.compile(r"(?im)^\s*industry\s*[:\-]\s*([A-Za-z,&/ \-]{3,60})$")
_INDUSTRY_IN = re.compile(r"\bin the ([a-z][a-z &/\-]{2,40}?) (?:industry|sector|space)\b", re.I)


def extract(text: str, job: dict | None = None) -> dict:
    text = text or ""
    out: dict = {}
    m = _SIZE.search(text)
    if m:
        out["company_size"] = m.group(1).replace(",", "") + ("+" if "+" in m.group(0) or re.search(r"over|more than", m.group(0), re.I) else "")
    else:
        m = _SIZE_RANGE.search(text)
        if m:
            out["company_size"] = re.sub(r"\s+", "", m.group(1))
        else:
            m = _STAGE.search(text)
            if m:
                out["company_size"] = m.group(1).lower()
    m = _INDUSTRY_LINE.search(text)
    if m:
        out["industry"] = m.group(1).strip()
    else:
        m = _INDUSTRY_IN.search(text)
        if m and not re.match(r"(?:same|current|field|tech)\b", m.group(1), re.I):
            out["industry"] = m.group(1).strip().lower()
    return out
