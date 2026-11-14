"""Stable listing fingerprint and text hash."""
from __future__ import annotations

import hashlib
import re

_CORP = re.compile(r"\b(inc|incorporated|ltd|limited|llc|corp|corporation|co|gmbh|plc|ulc|lp)\b\.?", re.I)


def _norm(s: str) -> str:
    s = re.sub(r"[^\w\s]", " ", (s or "").lower())
    return re.sub(r"\s+", " ", s).strip()


def norm_title(title: str) -> str:
    t = re.sub(r"\((?:[^)]*)\)|\[(?:[^\]]*)\]", " ", title or "")      # drop (m/f/d), (Remote), [Toronto]
    t = re.split(r"\s[-–|]\s", t)[0]
    return _norm(t)


def norm_company(c: str) -> str:
    return _norm(_CORP.sub(" ", c or ""))


def _city(job: dict) -> str:
    city = job.get("city") or ""
    if not city:
        loc = job.get("location") or (job.get("locations") or [""])[0]
        city = re.split(r"[,|;/(]", loc or "")[0]
    return _norm(city)


def fingerprint(job: dict) -> str:
    key = "|".join([norm_title(job.get("title", "")), norm_company(job.get("company", "")), _city(job)])
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def text_hash(text: str) -> str:
    norm = re.sub(r"\s+", " ", (text or "")).strip().lower()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()
