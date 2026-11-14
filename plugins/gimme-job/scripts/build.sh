#!/usr/bin/env bash
# Build a resume PDF with tectonic (fallback: latexmk / pdflatex). Usage:
#   build.sh path/to/resume-vN.tex            → resume-vN.pdf next to it
#   build.sh --hook                           → PostToolUse mode: reads the hook event, builds only versions/**/*.tex
set -euo pipefail
PLUGIN="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${1:-}" == "--hook" ]]; then
  file="$(python3 -c 'import json,sys; e=json.load(sys.stdin); print((e.get("tool_input") or {}).get("file_path",""))' 2>/dev/null || true)"
  [[ "$file" == *"/versions/v"*".tex" ]] || exit 0
  set -- "$file"
fi

tex="${1:?usage: build.sh FILE.tex}"
dir="$(cd "$(dirname "$tex")" && pwd)"
base="$(basename "$tex" .tex)"

# resume.cls + contact.tex must be next to the .tex (or on TEXINPUTS)
export TEXINPUTS="$dir:$PLUGIN/templates:$(dirname "$dir")/..:${TEXINPUTS:-}"
[[ -f "$dir/resume.cls" ]] || cp "$PLUGIN/templates/resume.cls" "$dir/resume.cls"

if command -v tectonic >/dev/null 2>&1; then
  (cd "$dir" && tectonic --keep-logs --outdir "$dir" "$base.tex" >"$dir/build.log" 2>&1) || { tail -30 "$dir/build.log"; exit 1; }
elif command -v latexmk >/dev/null 2>&1; then
  (cd "$dir" && latexmk -pdf -interaction=nonstopmode -halt-on-error "$base.tex" >"$dir/build.log" 2>&1) || { tail -30 "$dir/build.log"; exit 1; }
elif command -v pdflatex >/dev/null 2>&1; then
  (cd "$dir" && pdflatex -interaction=nonstopmode -halt-on-error "$base.tex" >"$dir/build.log" 2>&1 \
     && pdflatex -interaction=nonstopmode "$base.tex" >>"$dir/build.log" 2>&1) || { tail -30 "$dir/build.log"; exit 1; }
else
  echo "no LaTeX engine: install tectonic (brew install tectonic)" >&2
  exit 2
fi
rm -f "$dir/$base".{aux,out,fls,fdb_latexmk,log}
echo "$dir/$base.pdf"
