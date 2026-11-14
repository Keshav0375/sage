"""Normalised title, level, family."""
from __future__ import annotations

import re

_LEVELS = [
    ("intern", r"\b(intern|internship|co-?op|stagiaire)\b"),
    ("director", r"\b(director|head of|vp|vice president)\b"),
    ("manager", r"\b(manager|engineering manager)\b"),
    ("principal", r"\bprincipal\b"),
    ("staff", r"\bstaff\b"),
    ("lead", r"\b(lead|team lead|tech lead)\b"),
    ("senior", r"\b(senior|sr\.?|iii)\b"),
    ("junior", r"\b(junior|jr\.?|entry[- ]level|graduate|new grad|associate)\b"),
    ("mid", r"\b(mid[- ]level|intermediate|ii)\b"),
]
_FAMILIES = [
    ("fde", r"forward[- ]deployed|\bfde\b|solutions? engineer|customer engineer"),
    ("research", r"research (scientist|engineer)|\bresearcher\b"),
    ("data_scientist", r"data scientist|decision scientist|applied scientist"),
    ("ai_engineer", r"\bai\b.{0,20}(engineer|developer)|(engineer|developer).{0,12}\bai\b|agentic|\bllm\b|generative ai|\bgenai\b|applied ai|prompt engineer"),
    ("ml_engineer", r"machine learning|\bml\b|mlops|deep learning|computer vision|\bnlp\b"),
    ("platform", r"platform|devops|\bsre\b|site reliability|infrastructure|cloud engineer|\bdevsecops\b"),
    ("fullstack", r"full[- ]?stack"),
    ("backend", r"back[- ]?end|software (engineer|developer)|java developer|python developer|api developer"),
]


def normalise(title: str) -> str:
    t = re.sub(r"\s+", " ", title or "").strip()
    t = re.sub(r"\s*\((?:m|f|w|d|x|/|\s)+\)\s*$", "", t, flags=re.I)          # (m/f/d)
    t = re.sub(r"\s*[\(\[]\s*(remote|hybrid|on-?site)[^\)\]]*[\)\]]\s*$", "", t, flags=re.I)
    t = re.sub(r"\s*[-–|]\s*(remote|hybrid|on-?site)\s*$", "", t, flags=re.I)
    return t.strip(" -–|,")


def extract(text: str, job: dict | None = None) -> dict:
    job = job or {}
    raw = job.get("title") or ""
    if not raw:
        first = next((ln.strip() for ln in (text or "").splitlines() if ln.strip()), "")
        raw = first if 3 <= len(first) <= 120 and not first.endswith(".") else ""
    title = normalise(raw)
    if not title:
        return {}
    low = title.lower()
    out: dict = {"title": title}
    for level, pat in _LEVELS:
        if re.search(pat, low):
            out["level"] = level
            break
    fam = "other"
    for name, pat in _FAMILIES:
        if re.search(pat, low):
            fam = name
            break
    out["family"] = fam
    return out
