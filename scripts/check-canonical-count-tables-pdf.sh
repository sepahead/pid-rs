#!/usr/bin/env bash
set -euo pipefail

root="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
mode="${1:---exact}"
if [[ $# -gt 1 || ( "$mode" != "--exact" && "$mode" != "--cross-toolchain" ) ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

paper=canonical-count-tables
source="$root/audit/formal/latex/$paper.tex"
reference="$root/output/pdf/$paper.pdf"
reader="$root/audit/research/categorical-count-table-encoding/wire.py"
temp_parent="$(CDPATH='' cd -- "${TMPDIR:-/tmp}" && pwd -P)"
work="$(mktemp -d "$temp_parent/pid-rs-count-tables.XXXXXX")"
trap 'rm -rf -- "$work"' EXIT
export LC_ALL=C TZ=UTC SOURCE_DATE_EPOCH=1794960000
export TEXINPUTS="$root/audit/formal/latex:"
cd "$work"

python3 -I -S -B "$reader" > normal.json
python3 -O -I -S -B "$reader" > optimized.json
cmp normal.json optimized.json
python3 -I -S -B - <<'PY'
import json
from pathlib import Path

observed = json.loads(Path("normal.json").read_bytes())
expected = {
    "one_row_tables": 243,
    "two_row_tables": 29160,
    "distinct_wires": 29403,
    "max_wire_bytes": 341,
    "ordered_u32be_framed_sha256":
        "29fcc1ccf5bce582b65acceb4989b63f79a425caa6393baecb21e7d7c222a876",
}
if observed != expected:
    raise SystemExit(f"canonical count-table census differs: {observed!r}")
PY

for pass in 1 2; do
  if ! lualatex --no-shell-escape -interaction=nonstopmode -halt-on-error -file-line-error \
      "-jobname=$paper" "$source" >"pass-$pass.log" 2>&1; then
    cat "pass-$pass.log" >&2
    exit 1
  fi
done
"$root/scripts/check-formal-pdf-log.sh" "$paper.log"

for document in built reference; do
  pdf="$reference"
  if [[ "$document" == built ]]; then pdf="$paper.pdf"; fi
  pdftotext -layout "$pdf" "$document.txt"
  pdfinfo -f 1 -l 4 "$pdf" > "$document.info"
  pdffonts "$pdf" > "$document.fonts"
  awk 'NR > 2 { seen=1; if ($(NF-4)!="yes" || $(NF-3)!="yes" || $(NF-2)!="yes") bad=1 }
       END { exit (!seen || bad) }' "$document.fonts"
  grep -Eq '^Pages: +4$' "$document.info"
  grep -Fxq '29fcc1ccf5bce582b65acceb4989b63f79a425caa6393baecb21e7d7c222a876' \
    <(sed 's/^[[:space:]]*//; s/[[:space:]]*$//' "$document.txt")
  for section in 'Unique readability' 'Rust implementation and computational cost'; do
    grep -Fq "$section" "$document.txt"
  done
  grep -E '^(Title|Author|Pages):|^Page +[1-4] (size|rot):' "$document.info" > "$document.summary"
  grep -Eq '^Author: +Sepehr Mahmoudian$' "$document.summary"
  grep -Fq 'When does a three-source count table have unique bytes?' "$document.summary"
  if [[ "$(grep -Ec '^Page +[1-4] size:.*\(A4\)' "$document.summary")" != 4 ]]; then
    echo 'canonical count-table paper requires four A4 page boxes' >&2
    exit 1
  fi
done

if [[ "$mode" == --exact ]]; then
  cmp "$paper.pdf" "$reference"
  echo 'OK: canonical count tables reproduced the reference PDF bytes and the 29,403-table census.'
else
  cmp built.txt reference.txt
  cmp built.summary reference.summary
  echo 'OK: canonical count tables matched extracted layout text, title, author, page dimensions and rotations. All fonts passed embedding, subset and Unicode checks. The 29,403-table census matched.'
fi
