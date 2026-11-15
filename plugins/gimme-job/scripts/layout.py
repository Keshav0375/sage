#!/usr/bin/env python3
"""Design lock for resume versions: measure the PDF, compare to the original design, make snapshots.

  layout.py measure FILE.pdf [--json]                  lines, bullets, fills, overflow per page
  layout.py baseline FILE.pdf [--tex FILE.tex]         save memory/resume/design/baseline.json + redacted snapshots
  layout.py check FILE.pdf [--json]                    gate vs baseline: exit 1 on errors; per-bullet char advice
  layout.py snap FILE.pdf OUTDIR [--tex FILE.tex]      PNG per page (contact info redacted when --tex is given)
  layout.py compare NEW.pdf OUT.png [--tex NEW.tex]    side-by-side original | new | difference (Playwright screenshot)

Gate rules (knobs.layout):
  - same page count and same section order as the original design
  - skills: same row labels, one line per row, nothing past the right margin
  - every bullet: no more lines than its slot in the original; last line at least min_last_line_fill full
  - no line past the right margin (+ overflow_tolerance_pt)
  - bottom gap per page not larger than the original's + max_extra_bottom_gap_pt
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts import knobs as knobs_mod  # noqa: E402

SECTIONS = {"PROFESSIONAL SUMMARY", "EDUCATION", "SKILLS", "EXPERIENCE", "PROJECTS", "HACKATHONS & EVENTS",
            "CERTIFICATIONS & TRAINING", "SUMMARY", "AWARDS", "PUBLICATIONS"}
LINE_RX = re.compile(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>', re.S)


def design_dir(k: dict) -> Path:
    return common.data_root(k) / "design"


# ------------------------------------------------------------------ measure
def _lines(pdf: Path) -> list[dict]:
    out = subprocess.run(["pdftotext", "-bbox-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    pages = re.findall(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', out, re.S)
    rows = []
    for pno, (pw, ph, body) in enumerate(pages, 1):
        for m in LINE_RX.finditer(body):
            words = [html.unescape(w) for w in re.findall(r">([^<]*)</word>", m.group(5))]
            rows.append({"page": pno, "pw": float(pw), "ph": float(ph), "x0": float(m.group(1)), "y0": float(m.group(2)),
                         "x1": float(m.group(3)), "y1": float(m.group(4)), "text": " ".join(words)})
    rows.sort(key=lambda r: (r["page"], round(r["y0"]), r["x0"]))
    return rows


def margins_from_tex(tex: Path | None) -> tuple[float, float]:
    left = right = 36.0
    if tex and tex.exists():
        m = re.search(r"\\usepackage\[([^\]]*)\]\{geometry\}", tex.read_text(encoding="utf-8"))
        if m:
            for side in ("left", "right"):
                mm = re.search(side + r"=([\d.]+)in", m.group(1))
                if mm:
                    val = float(mm.group(1)) * 72
                    left, right = (val, right) if side == "left" else (left, val)
    return left, right


def measure(pdf: Path, tex: Path | None = None) -> dict:
    lines = _lines(pdf)
    if not lines:
        return {"pages": 0}
    pw = lines[0]["pw"]
    lm, rm = margins_from_tex(tex)
    right = pw - rm
    pages = max(r["page"] for r in lines)
    section, sections, bullets, skills, overflow = "", [], [], [], []
    cur = None
    label_x = None
    for r in lines:
        t = r["text"].strip()
        if r["x1"] > right + 1e-6:
            overflow.append({"page": r["page"], "x1": round(r["x1"], 1), "text": t[:60]})
        if t.upper() == t and t in SECTIONS:
            section = t
            sections.append(t)
            cur = None
            continue
        if t.startswith("•"):
            cur = {"section": section, "page": r["page"], "text": t[:70], "lines": 1, "first_chars": len(t),
                   "x_start": None, "last_x1": r["x1"], "max_x1": r["x1"], "y0": r["y0"]}
            bullets.append(cur)
            continue
        if cur and r["page"] == cur["page"] and abs(r["x0"] - 46.8) < 4 and r["y0"] - cur["y0"] < 16 * cur["lines"] + 4:
            cur["lines"] += 1
            cur["x_start"] = r["x0"]
            cur["last_x1"] = r["x1"]
            cur["max_x1"] = max(cur["max_x1"], r["x1"])
            continue
        cur = None
        if section == "SKILLS":
            if t.endswith(":") and r["x0"] < lm + 2:
                skills.append({"label": t.rstrip(":"), "y0": r["y0"], "rows": 0, "x1": 0.0})
                label_x = r["x0"]
            elif skills and r["x0"] > lm + 40:
                row = min(skills, key=lambda s: abs(s["y0"] - r["y0"]))
                if abs(row["y0"] - r["y0"]) < 3:
                    row["rows"] += 1
                    row["x1"] = max(row["x1"], r["x1"])
                else:  # a value line with no label next to it = wrapped / extra row
                    skills.append({"label": "", "y0": r["y0"], "rows": 1, "x1": r["x1"]})
    for b in bullets:
        x_start = b["x_start"] or 46.8
        b["last_fill"] = round(max(0.0, (b["last_x1"] - x_start) / (right - x_start)), 3) if b["lines"] > 1 else \
            round((b["last_x1"] - lm) / (right - lm), 3)
        b.pop("x_start", None)
    bottoms = {}
    for p in range(1, pages + 1):
        ys = [r["y1"] for r in lines if r["page"] == p]
        bottoms[str(p)] = round(lines[0]["ph"] - max(ys), 1) if ys else None
    return {"pages": pages, "right_margin_x": right, "sections": sections, "bullets": bullets, "skills": skills,
            "overflow": overflow, "bottom_gap_pt": bottoms}


# ------------------------------------------------------------------ check
def check(new: dict, base: dict, cfg: dict) -> dict:
    errors, warnings, advice = [], [], []
    tol = cfg["overflow_tolerance_pt"]
    if new["pages"] != base["pages"]:
        errors.append(f"pages {new['pages']} != original {base['pages']}")
    if new["sections"] != base["sections"]:
        errors.append(f"section order changed: {new['sections']} vs original {base['sections']}")
    bl = [s["label"] for s in base["skills"]]
    nl = [s["label"] for s in new["skills"]]
    if nl != bl:
        errors.append(f"skills rows changed: {nl} vs original {bl}")
    for s in new["skills"]:
        if s["x1"] > new["right_margin_x"] + tol:
            errors.append(f"skills row '{s['label']}' runs past the right margin ({s['x1']:.0f} > {new['right_margin_x']:.0f}pt)")
    for o in new["overflow"]:
        if o["x1"] > new["right_margin_x"] + tol:
            errors.append(f"p{o['page']} line past right margin ({o['x1']}pt): {o['text']}")
    by_sec_base: dict[str, list] = {}
    for b in base["bullets"]:
        by_sec_base.setdefault(b["section"], []).append(b)
    by_sec_new: dict[str, list] = {}
    for b in new["bullets"]:
        by_sec_new.setdefault(b["section"], []).append(b)
    for sec, items in by_sec_new.items():
        slots = by_sec_base.get(sec, [])
        for i, b in enumerate(items):
            slot = slots[i] if i < len(slots) else None
            max_lines = min(cfg["max_lines"], slot["lines"]) if slot else cfg["max_lines"]
            cpl = max(60, b["first_chars"])  # chars on one full line
            tag = f"{sec} #{i + 1} \"{b['text'][2:42]}…\""
            if b["lines"] > max_lines:
                cut = int((b["lines"] - max_lines - 1 + b["last_fill"]) * cpl) + 3
                errors.append(f"{tag}: {b['lines']} lines (slot {max_lines}); last line {b['last_fill']:.0%}")
                advice.append({"bullet": tag, "action": "cut", "chars": cut, "lines_now": b["lines"], "lines_target": max_lines})
            elif b["last_fill"] < cfg["min_last_line_fill"]:
                add_max = int((0.99 - b["last_fill"]) * cpl)
                add_min = max(1, int((cfg["min_last_line_fill"] - b["last_fill"]) * cpl) + 1)
                errors.append(f"{tag}: last line only {b['last_fill']:.0%} full (min {cfg['min_last_line_fill']:.0%})")
                advice.append({"bullet": tag, "action": "add", "chars_min": add_min, "chars_max": add_max,
                               "or": f"cut ~{int(b['last_fill'] * cpl) + 3} chars to drop the last line" if b["lines"] > 1 else ""})
        if len(items) != len(slots):
            warnings.append(f"{sec}: {len(items)} bullets vs {len(slots)} in the original")
    for p, gap in new["bottom_gap_pt"].items():
        bg = base["bottom_gap_pt"].get(p)
        if gap is not None and bg is not None and gap > bg + cfg["max_extra_bottom_gap_pt"]:
            errors.append(f"page {p}: bottom gap {gap:.0f}pt vs original {bg:.0f}pt (empty space)")
    return {"verdict": "FAIL" if errors else "PASS", "errors": errors, "warnings": warnings, "advice": advice}


# ------------------------------------------------------------------ snapshots
def _redacted_pdf(pdf: Path, tex: Path | None) -> Path:
    """Rebuild with contact digits/emails masked (same length) so snapshots are safe to commit."""
    if not tex:
        return pdf
    contact = common.data_root() / "contact.tex"
    if not contact.exists():
        return pdf
    tmp = Path(tempfile.mkdtemp(prefix="gj-redact-"))
    src = contact.read_text(encoding="utf-8")
    red = re.sub(r"\d", "0", src)
    red = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", lambda m: "x" * (len(m.group(0)) - 12) + "@example.com", red)
    (tmp / "contact.tex").write_text(red, encoding="utf-8")
    shutil.copy(tex, tmp / tex.name)
    build = Path(__file__).resolve().parent / "build.sh"
    r = subprocess.run(["bash", str(build), str(tmp / tex.name)], capture_output=True, text=True)
    out = tmp / (tex.stem + ".pdf")
    return out if r.returncode == 0 and out.exists() else pdf


def snap(pdf: Path, outdir: Path, tex: Path | None = None, dpi: int = 100) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    src = _redacted_pdf(pdf, tex)
    for old in outdir.glob("page-*.png"):
        old.unlink()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(src), str(outdir / "page")], check=True)
    return sorted(outdir.glob("page-*.png"))


COMPARE_JS = r"""
const { chromium } = require('playwright');
(async () => {
  const [,, htmlPath, outPath] = process.argv;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1900, height: 1200 }, deviceScaleFactor: 1 });
  await page.goto('file://' + htmlPath);
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: outPath, fullPage: true });
  await browser.close();
})();
"""


def compare(new_pdf: Path, out_png: Path, k: dict, new_tex: Path | None = None) -> Path:
    base_dir = design_dir(k) / "snapshots"
    tmp = Path(tempfile.mkdtemp(prefix="gj-cmp-"))
    new_pngs = snap(new_pdf, tmp / "new", new_tex)
    base_pngs = sorted(base_dir.glob("page-*.png"))
    rows = []
    for i in range(max(len(base_pngs), len(new_pngs))):
        b = base_pngs[i].resolve().as_uri() if i < len(base_pngs) else ""
        n = new_pngs[i].resolve().as_uri() if i < len(new_pngs) else ""
        rows.append(f"""<div class=row><figure><figcaption>original p{i+1}</figcaption><img src="{b}"></figure>
<figure><figcaption>new p{i+1}</figcaption><img src="{n}"></figure>
<figure><figcaption>difference p{i+1}</figcaption><div class=diff><img src="{b}"><img class=top src="{n}"></div></figure></div>""")
    page = f"""<!doctype html><meta charset=utf-8><style>
body{{margin:0;background:#fff;font:14px sans-serif}} .row{{display:flex;gap:12px;padding:12px}}
figure{{margin:0;border:1px solid #ccc}} figcaption{{background:#eee;padding:4px 8px}} img{{display:block;width:600px}}
.diff{{position:relative}} .diff .top{{position:absolute;top:0;left:0;mix-blend-mode:difference}}</style>{''.join(rows)}"""
    hp = tmp / "compare.html"
    hp.write_text(page, encoding="utf-8")
    js = tmp / "compare.js"
    js.write_text(COMPARE_JS)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["node", str(js), str(hp), str(out_png.resolve())], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"playwright compare failed: {r.stderr[-400:]}")
    return out_png


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["measure", "baseline", "check", "snap", "compare"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--tex")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    k, _ = knobs_mod.load()
    cfg = k["layout"]
    tex = Path(a.tex) if a.tex else None
    pdf = Path(a.args[0])
    if tex is None and pdf.with_suffix(".tex").exists():
        tex = pdf.with_suffix(".tex")
    if a.cmd == "measure":
        m = measure(pdf, tex)
        print(json.dumps(m, indent=2) if a.json else
              "\n".join(f"{b['section'][:10]:10} {b['lines']}L fill {b['last_fill']:.0%} | {b['text'][:60]}" for b in m["bullets"]))
    elif a.cmd == "baseline":
        d = design_dir(k)
        m = measure(pdf, tex)
        m["source"] = str(pdf.resolve().relative_to(common.repo_root())) if pdf.resolve().is_relative_to(common.repo_root()) else str(pdf)
        common.write_json(d / "baseline.json", m)
        snaps = snap(pdf, d / "snapshots", tex)
        print(json.dumps({"baseline": str(d / "baseline.json"), "snapshots": [str(s) for s in snaps],
                          "bullets": len(m["bullets"]), "pages": m["pages"]}))
    elif a.cmd == "check":
        base = common.read_json(design_dir(k) / "baseline.json")
        if not base:
            raise SystemExit("no design baseline: run `layout.py baseline <original.pdf>` first")
        res = check(measure(pdf, tex), base, cfg)
        if a.json:
            print(json.dumps(res, indent=2))
        else:
            print(res["verdict"])
            for e in res["errors"]:
                print("  error", e)
            for w in res["warnings"]:
                print("  warn ", w)
            for ad in res["advice"]:
                print("  fix  ", json.dumps(ad))
        return 1 if res["errors"] else 0
    elif a.cmd == "snap":
        print("\n".join(str(p) for p in snap(pdf, Path(a.args[1]), tex)))
    elif a.cmd == "compare":
        print(compare(pdf, Path(a.args[1]), k, tex))
    return 0


if __name__ == "__main__":
    sys.exit(main())
