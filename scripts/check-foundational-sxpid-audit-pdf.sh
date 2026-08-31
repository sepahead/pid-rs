#!/usr/bin/env bash
# Method catalog: validation.foundational-shared-exclusions-audit
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="audit/formal/latex/foundational-shared-exclusions-pid-audit.tex"
COMMITTED="output/pdf/foundational-shared-exclusions-pid-audit.pdf"
EXACT_CHECKER="audit/tools/foundational_sxpid/check_lcr_relation_witness.py"
EVIDENCE="audit/evidence/foundational-sxpid-lcr-exact-audit.json"
LEAN_SOURCE="audit/formal/lean-foundational-sxpid/PidDescriptorFactorization.lean"
LEAN_CHECKER="scripts/check-lean-descriptor-factorization.py"
LEAN_EVIDENCE="audit/evidence/foundational-sxpid-descriptor-factorization-lean-4.33.0.json"
MUTATION_CHECKER="scripts/check-lean-descriptor-factorization-self-test.py"
MUTATION_EVIDENCE="audit/evidence/foundational-sxpid-descriptor-factorization-mutations-4.33.0.json"
SOURCE_DATE_EPOCH_VALUE="1784937600"
MODE="${1:---exact}"
CHECK_NAME="foundational shared-exclusions PID audit PDF check"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

commands=(latexmk cmp pdffonts pdfinfo pdftotext pdftoppm chktex lacheck lake python3)
for command in "${commands[@]}"; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "$CHECK_NAME: missing command: $command" >&2
    exit 2
  fi
done

for required in \
  "$SOURCE" \
  "$COMMITTED" \
  "$EXACT_CHECKER" \
  "$EVIDENCE" \
  "$LEAN_SOURCE" \
  "$LEAN_CHECKER" \
  "$LEAN_EVIDENCE" \
  "$MUTATION_CHECKER" \
  "$MUTATION_EVIDENCE"; do
  if [[ ! -f "$ROOT/$required" ]]; then
    echo "$CHECK_NAME: missing artifact: $required" >&2
    exit 1
  fi
done

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_DIR="$(mktemp -d "$TMP_ROOT/pid-rs-foundational-sxpid-audit-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

cd "$ROOT"

KNOWN_CHKTEX_CONFIG_WARNING='chktex: WARNING -- Compilation of regular expression \[(?![^\]\[{}]*{(?![^\]\[{}]*}))[^\]]*\[ failed with error repetition-operator operand invalid.'
set +e
chktex -q "$SOURCE" >"$BUILD_DIR/chktex.stdout" 2>"$BUILD_DIR/chktex.stderr"
CHKTEX_STATUS=$?
set -e
if grep -E '^Warning [0-9]+ in ' "$BUILD_DIR/chktex.stdout" "$BUILD_DIR/chktex.stderr" >/dev/null; then
  cat "$BUILD_DIR/chktex.stdout" "$BUILD_DIR/chktex.stderr" >&2
  echo "$CHECK_NAME: ChkTeX reported a source diagnostic" >&2
  exit 1
fi
grep -Fvx -- "$KNOWN_CHKTEX_CONFIG_WARNING" "$BUILD_DIR/chktex.stderr" \
  | grep -v -E '^[[:space:]]*$' >"$BUILD_DIR/chktex.unexpected" || true
if [[ -s "$BUILD_DIR/chktex.stdout" || -s "$BUILD_DIR/chktex.unexpected" ]]; then
  cat "$BUILD_DIR/chktex.stdout" "$BUILD_DIR/chktex.stderr" >&2
  echo "$CHECK_NAME: ChkTeX reported an unexpected diagnostic" >&2
  exit 1
fi
if [[ "$CHKTEX_STATUS" -ne 0 ]]; then
  cat "$BUILD_DIR/chktex.stderr" >&2
  echo "$CHECK_NAME: ChkTeX exited unsuccessfully" >&2
  exit 1
fi

lacheck "$SOURCE" >"$BUILD_DIR/lacheck.stdout" 2>"$BUILD_DIR/lacheck.stderr"
if [[ -s "$BUILD_DIR/lacheck.stdout" || -s "$BUILD_DIR/lacheck.stderr" ]]; then
  cat "$BUILD_DIR/lacheck.stdout" "$BUILD_DIR/lacheck.stderr" >&2
  echo "$CHECK_NAME: lacheck reported a source diagnostic" >&2
  exit 1
fi

python3 -I -S "$EXACT_CHECKER" --write-evidence "$BUILD_DIR/evidence.json" \
  >"$BUILD_DIR/exact-checker.stdout"
if ! cmp -s "$BUILD_DIR/evidence.json" "$EVIDENCE"; then
  echo "$CHECK_NAME: exact-rational evidence is stale or not reproducible" >&2
  exit 1
fi

python3 -I -S "$LEAN_CHECKER" >"$BUILD_DIR/lean-evidence.json"
if ! cmp -s "$BUILD_DIR/lean-evidence.json" "$LEAN_EVIDENCE"; then
  echo "$CHECK_NAME: Lean factorization evidence is stale or not reproducible" >&2
  exit 1
fi

python3 -I -S "$MUTATION_CHECKER" >"$BUILD_DIR/mutation-evidence.json"
if ! cmp -s "$BUILD_DIR/mutation-evidence.json" "$MUTATION_EVIDENCE"; then
  echo "$CHECK_NAME: Lean factorization mutation evidence is stale or not reproducible" >&2
  exit 1
fi

if ! SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" TZ=UTC \
  TEXINPUTS="$ROOT/audit/formal/latex:${TEXINPUTS:-}" latexmk \
  -pdf \
  -interaction=nonstopmode \
  -halt-on-error \
  -outdir="$BUILD_DIR" \
  "$SOURCE" \
  >"$BUILD_DIR/latexmk.stdout" 2>&1; then
  cat "$BUILD_DIR/latexmk.stdout" >&2
  echo "$CHECK_NAME: LaTeX build failed" >&2
  exit 1
fi

LOG="$BUILD_DIR/foundational-shared-exclusions-pid-audit.log"
BUILT="$BUILD_DIR/foundational-shared-exclusions-pid-audit.pdf"
TOC="$BUILD_DIR/foundational-shared-exclusions-pid-audit.toc"
OUT="$BUILD_DIR/foundational-shared-exclusions-pid-audit.out"
REJECTED_DIAGNOSTICS='(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error'
if grep -E "$REJECTED_DIAGNOSTICS" "$LOG" >/dev/null; then
  grep -E "$REJECTED_DIAGNOSTICS" "$LOG" >&2
  echo "$CHECK_NAME: LaTeX log contains a rejected diagnostic" >&2
  exit 1
fi

python3 -I -S - "$SOURCE" "$TOC" "$OUT" "$BUILT" "$ROOT/$COMMITTED" <<'PY'
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import re
import subprocess
import sys


def fail(detail: str) -> None:
    print(
        f"foundational shared-exclusions PID audit PDF check: {detail}",
        file=sys.stderr,
    )
    raise SystemExit(1)


def read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        fail(f"cannot read {label}: {error}")


source_path, toc_path, out_path, built_pdf_path, committed_pdf_path = map(
    Path, sys.argv[1:]
)
source = read_bytes(source_path, "TeX source")
anchor = (
    b"\\phantomsection\n"
    b"\\section*{Primary sources}\n"
    b"\\addcontentsline{toc}{section}{Primary sources}\n"
)
if source.count(anchor) != 1:
    fail("Primary sources must have exactly one adjacent fresh TeX anchor")

try:
    toc = read_bytes(toc_path, "LaTeX TOC auxiliary").decode("utf-8")
    out = read_bytes(out_path, "LaTeX bookmark auxiliary").decode("ascii")
except UnicodeDecodeError as error:
    fail(f"LaTeX navigation auxiliary has unexpected encoding: {error}")
if "\r" in toc or "\r" in out:
    fail("LaTeX navigation auxiliary contains a carriage return")

toc_matches = re.findall(
    r"^\\contentsline \{section\}\{Primary sources\}\{16\}\{([^{}]+)\}%$",
    toc,
    flags=re.MULTILINE,
)
if len(toc_matches) != 1:
    fail("Primary sources must have exactly one page-16 TOC destination")
destination = toc_matches[0]
if not destination.startswith("section*.") or destination == "section.15":
    fail("Primary sources TOC destination is not a fresh unnumbered-section anchor")

bookmark_pattern = re.compile(
    r"^\\BOOKMARK \[1\]\[-\]\{([^{}]+)\}"
    r"\{((?:\\[0-7]{3}|[^{}\\])+)\}\{\}% [0-9]+$"
)
primary_bookmarks: list[str] = []
for line in out.splitlines():
    match = bookmark_pattern.fullmatch(line)
    if match is None:
        continue
    encoded_title = bytearray()
    encoded = match.group(2)
    index = 0
    while index < len(encoded):
        if encoded[index] == "\\":
            encoded_title.append(int(encoded[index + 1 : index + 4], 8))
            index += 4
        else:
            encoded_title.append(ord(encoded[index]))
            index += 1
    try:
        title = bytes(encoded_title).decode("utf-16")
    except UnicodeDecodeError as error:
        fail(f"bookmark title is not valid BOM-marked UTF-16: {error}")
    if title == "Primary sources":
        primary_bookmarks.append(match.group(1))
if primary_bookmarks != [destination]:
    fail("Primary sources bookmark and TOC destinations do not agree exactly")

destination_pattern = re.compile(
    r'^\s*([0-9]+)\s+\[\s*XYZ\s+([^\]]+)\]\s+"([^"]+)"\s*$'
)


def pdf_destinations(
    pdf_path: Path,
    *,
    label: str,
) -> dict[str, list[tuple[int, Decimal]]]:
    environment = dict(os.environ)
    environment["LC_ALL"] = "C"
    environment["LANG"] = "C"
    try:
        completed = subprocess.run(
            ["pdfinfo", "-dests", os.fspath(pdf_path)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=environment,
        )
    except OSError as error:
        fail(f"cannot execute pdfinfo -dests for {label}: {error}")
    if completed.returncode != 0 or completed.stderr != b"":
        fail(
            f"pdfinfo -dests for {label} did not complete silently with status zero "
            f"(status {completed.returncode})"
        )
    try:
        destination_output = completed.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"pdfinfo -dests output for {label} is not UTF-8: {error}")
    if "\r" in destination_output:
        fail(f"pdfinfo -dests output for {label} contains a carriage return")

    destinations: dict[str, list[tuple[int, Decimal]]] = {}
    for line in destination_output.splitlines():
        match = destination_pattern.fullmatch(line)
        if match is None:
            continue
        coordinates = match.group(2).split()
        if len(coordinates) != 3 or coordinates[1] == "null":
            continue
        try:
            vertical = Decimal(coordinates[1])
        except InvalidOperation:
            continue
        destinations.setdefault(match.group(3), []).append(
            (int(match.group(1)), vertical)
        )
    return destinations


def validate_pdf_destinations(
    pdf_path: Path,
    *,
    primary_destination: str,
    label: str,
) -> None:
    destinations = pdf_destinations(pdf_path, label=label)
    primary_rows = destinations.get(primary_destination, [])
    reproducibility_rows = destinations.get("section.15", [])
    if len(primary_rows) != 1 or len(reproducibility_rows) != 1:
        fail(
            f"{label} must contain unique Primary sources and "
            "Reproducibility destinations"
        )
    primary_page, _primary_vertical = primary_rows[0]
    reproducibility_page, _reproducibility_vertical = reproducibility_rows[0]
    if primary_page != 16 or reproducibility_page != 15:
        fail(
            f"{label} navigation destinations moved off their declared "
            "Reproducibility-page-15/Primary-sources-page-16 structure"
        )


validate_pdf_destinations(
    built_pdf_path,
    primary_destination=destination,
    label="built PDF",
)
validate_pdf_destinations(
    committed_pdf_path,
    primary_destination="section*.13",
    label="committed PDF",
)
PY

pdftotext -layout "$BUILT" "$BUILD_DIR/built.txt"
for sentinel in \
  'No fatal algebraic contradiction was found' \
  'Compatibility firewall' \
  'Descriptor-factorization firewall' \
  'Valid theorem on the stated Definition 6 domain' \
  'What arXiv:2604.03869v2 does and does not imply' \
  'Three complementary, implementation-distinct but correlated lanes' \
  'generates all eighteen nonempty antichains of the seven nonempty three-source subsets' \
  'performs exact Möbius inversion in formal prime-exponent logarithms' \
  'implementation-distinct corroboration, not independent proofs' \
  '0.58147874590342'; do
  if ! grep -F -- "$sentinel" "$BUILD_DIR/built.txt" >/dev/null; then
    echo "$CHECK_NAME: rendered-text sentinel is absent: $sentinel" >&2
    exit 1
  fi
done
if grep -F -- '??' "$BUILD_DIR/built.txt" >/dev/null; then
  echo "$CHECK_NAME: rendered text contains an unresolved reference marker" >&2
  exit 1
fi

for pdf in "$BUILT" "$ROOT/$COMMITTED"; do
  if ! pdffonts "$pdf" | awk '
    NR > 2 {
      seen = 1
      if ($(NF - 4) != "yes" || $(NF - 3) != "yes" || $(NF - 2) != "yes") bad = 1
    }
    END { exit (!seen || bad) }
  '; then
    echo "$CHECK_NAME: PDF font is not embedded, subset, and Unicode-mapped" >&2
    exit 1
  fi
done

mkdir "$BUILD_DIR/rendered"
pdftoppm -png -r 72 "$BUILT" "$BUILD_DIR/rendered/page" >/dev/null 2>&1
EXPECTED_PAGES="$(pdfinfo "$BUILT" | awk '/^Pages:/ {print $2}')"
RENDERED_PAGES="$(find "$BUILD_DIR/rendered" -type f -name 'page-*.png' | wc -l | tr -d ' ')"
if [[ "$RENDERED_PAGES" != "$EXPECTED_PAGES" ]]; then
  echo "$CHECK_NAME: rendered $RENDERED_PAGES of $EXPECTED_PAGES pages" >&2
  exit 1
fi

if [[ "$MODE" == "--exact" ]]; then
  if ! cmp -s "$BUILT" "$ROOT/$COMMITTED"; then
    echo "$CHECK_NAME: committed PDF is stale or not reproducible" >&2
    exit 1
  fi
else
  pdftotext -layout "$ROOT/$COMMITTED" "$BUILD_DIR/committed.txt"
  if ! cmp -s "$BUILD_DIR/built.txt" "$BUILD_DIR/committed.txt"; then
    echo "$CHECK_NAME: extracted text/layout changed across toolchains" >&2
    exit 1
  fi
  pdfinfo "$BUILT" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/built.info"
  pdfinfo "$ROOT/$COMMITTED" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/committed.info"
  if ! cmp -s "$BUILD_DIR/built.info" "$BUILD_DIR/committed.info"; then
    echo "$CHECK_NAME: page geometry changed across toolchains" >&2
    exit 1
  fi
fi

if command -v shasum >/dev/null 2>&1; then
  DIGEST="$(shasum -a 256 "$BUILT" | awk '{print $1}')"
else
  DIGEST="$(sha256sum "$BUILT" | awk '{print $1}')"
fi

echo "OK: foundational SxPID audit PDF, exact witnesses, and Lean firewall are warning-free and reproducible ($DIGEST)"
