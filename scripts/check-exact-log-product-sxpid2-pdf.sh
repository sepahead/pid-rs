#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="audit/formal/latex/exact-log-product-sxpid2-assurance.tex"
COMMITTED="output/pdf/exact-log-product-sxpid2-assurance.pdf"
LEAN_CHECKER="scripts/check-lean-exact-log-product.py"
LEAN_EVIDENCE="audit/evidence/sxpid2-exact-product-lean-check-4.33.0.json"
SOURCE_DATE_EPOCH_VALUE="1784851200"
MODE="${1:---exact}"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

commands=(latexmk cmp lake python3)
if [[ "$MODE" == "--cross-toolchain" ]]; then
  commands+=(pdffonts pdfinfo pdftotext)
fi
for command in "${commands[@]}"; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "exact log-product SxPID2 PDF check: missing command: $command" >&2
    exit 2
  fi
done

for required in "$SOURCE" "$COMMITTED" "$LEAN_CHECKER" "$LEAN_EVIDENCE"; do
  if [[ ! -f "$ROOT/$required" ]]; then
    echo "exact log-product SxPID2 PDF check: missing artifact: $required" >&2
    exit 1
  fi
done

for required_text in \
  "current pinned Lean 4.33.0 project" \
  "sxpid2-exact-product-lean-check-4.33.0.json" \
  "historical Lean 4.32 evidence"; do
  if ! grep -Fq -- "$required_text" "$ROOT/$SOURCE"; then
    echo "exact log-product SxPID2 PDF check: source omits required current/history boundary: $required_text" >&2
    exit 1
  fi
done
if ! python3 - "$ROOT/$SOURCE" <<'PY'
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")
needle = (
    "The current execution receipt is the versioned\n"
    "\\texttt{sxpid2-exact-product-lean-check-4.33.0.json}."
)
raise SystemExit(0 if needle in text else 1)
PY
then
  echo "exact log-product SxPID2 PDF check: source lost the contextual current 4.33 receipt binding" >&2
  exit 1
fi
for forbidden_text in "standalone Lean 4.32" "current pinned Lean 4.32"; do
  if grep -Fq -- "$forbidden_text" "$ROOT/$SOURCE"; then
    echo "exact log-product SxPID2 PDF check: source contains stale current-toolchain wording: $forbidden_text" >&2
    exit 1
  fi
done

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_DIR="$(mktemp -d "$TMP_ROOT/pid-rs-exact-log-product-sxpid2-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

cd "$ROOT"
python3 "$LEAN_CHECKER" >"$BUILD_DIR/lean-evidence.json"
if ! python3 - "$BUILD_DIR/lean-evidence.json" "$LEAN_EVIDENCE" <<'PY'
import json
from pathlib import Path
import re
import sys

actual_path, expected_path = (Path(argument) for argument in sys.argv[1:])


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_strict(path):
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON token: {token}")
        ),
    )


actual = load_strict(actual_path)
expected = load_strict(expected_path)
pattern = re.compile(
    r"Lean \(version (?P<version>[0-9]+\.[0-9]+\.[0-9]+), "
    r"(?P<platform>[A-Za-z0-9_.+]+(?:-[A-Za-z0-9_.+]+){2,}), "
    r"commit (?P<commit>[0-9a-f]{40}), "
    r"(?P<build>[A-Za-z][A-Za-z0-9_.+-]*)\)"
)
portable = ("4.33.0", "d8b18978322de05a8f3dba51ef03cf5461676c17", "Release")
for role, payload in (("current", actual), ("recorded", expected)):
    if not isinstance(payload, dict) or "lean_version" not in payload:
        raise SystemExit(f"{role} Lean evidence has no version identity")
    match = pattern.fullmatch(payload["lean_version"])
    if match is None:
        raise SystemExit(f"{role} Lean evidence has a malformed version identity")
    observed = (match.group("version"), match.group("commit"), match.group("build"))
    if observed != portable:
        raise SystemExit(
            f"{role} Lean evidence has the wrong portable identity: {observed!r}"
        )
    del payload["lean_version"]
if actual != expected:
    raise SystemExit("platform-neutral Lean evidence projection differs")
PY
then
  echo "exact log-product SxPID2 PDF check: portable Lean evidence is stale or not reproducible" >&2
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
  echo "exact log-product SxPID2 PDF check: LaTeX build failed" >&2
  exit 1
fi

LOG="$BUILD_DIR/exact-log-product-sxpid2-assurance.log"
BUILT="$BUILD_DIR/exact-log-product-sxpid2-assurance.pdf"

if grep -E \
  '(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error' \
  "$LOG" >/dev/null; then
  grep -E \
    '(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error' \
    "$LOG" >&2
  echo "exact log-product SxPID2 PDF check: LaTeX log contains a rejected diagnostic" >&2
  exit 1
fi

if [[ "$MODE" == "--exact" ]]; then
  if ! cmp -s "$BUILT" "$COMMITTED"; then
    echo "exact log-product SxPID2 PDF check: committed PDF is stale or not reproducible" >&2
    exit 1
  fi
else
  pdftotext -layout "$BUILT" "$BUILD_DIR/built.txt"
  pdftotext -layout "$COMMITTED" "$BUILD_DIR/committed.txt"
  if ! cmp -s "$BUILD_DIR/built.txt" "$BUILD_DIR/committed.txt"; then
    echo "exact log-product SxPID2 PDF check: extracted text/layout changed across toolchains" >&2
    exit 1
  fi
  pdfinfo "$BUILT" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/built.info"
  pdfinfo "$COMMITTED" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/committed.info"
  if ! cmp -s "$BUILD_DIR/built.info" "$BUILD_DIR/committed.info"; then
    echo "exact log-product SxPID2 PDF check: page geometry changed across toolchains" >&2
    exit 1
  fi
  for pdf in "$BUILT" "$COMMITTED"; do
    if ! pdffonts "$pdf" | awk '
      NR > 2 { seen = 1; if ($(NF - 4) != "yes") bad = 1 }
      END { exit (!seen || bad) }
    '; then
      echo "exact log-product SxPID2 PDF check: PDF has a missing or non-embedded font" >&2
      exit 1
    fi
  done
fi

if command -v shasum >/dev/null 2>&1; then
  DIGEST="$(shasum -a 256 "$BUILT" | awk '{print $1}')"
else
  DIGEST="$(sha256sum "$BUILT" | awk '{print $1}')"
fi

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: exact log-product SxPID2 PDF is warning-free and same-toolchain reproducible ($DIGEST)"
else
  echo "OK: exact log-product SxPID2 PDF is warning-free and cross-toolchain structurally equivalent ($DIGEST)"
fi
