#!/usr/bin/env bash
# Method catalog: validation.sxpid3-source-marginal-bounded-audit
set -euo pipefail
unset BASH_ENV ENV

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
BUILDER="$ROOT/scripts/build-sxpid3-source-marginal-audit-pdf.sh"
PDF_CHECK="$ROOT/scripts/check-sxpid3-source-marginal-audit-pdf.sh"
ID_VARIANCE_CHECK="$ROOT/scripts/check-mathematical-results-guide-pdf-id-variance.py"
CANONICAL_PDF="$ROOT/output/pdf/sxpid3-source-marginal-and-bounded-audit.pdf"
CHECK_NAME="SxPID3 source-marginal audit builder self-test"

for command_name in bash cat chmod cmp cp env find grep ln mkdir mkfifo mktemp python3 rm rmdir shasum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME failed: missing command: $command_name" >&2
    exit 2
  }
done
for required_path in "$BUILDER" "$PDF_CHECK" "$ID_VARIANCE_CHECK" "$CANONICAL_PDF"; do
  if [[ ! -f "$required_path" || -L "$required_path" ]]; then
    echo "$CHECK_NAME failed: required source is absent, non-regular, or symbolic: $required_path" >&2
    exit 1
  fi
done
REAL_CP="$(command -v cp)"
REAL_CMP="$(command -v cmp)"
REAL_MKTEMP="$(command -v mktemp)"
REAL_PYTHON="$(command -v python3)"
REAL_BASH="${BASH:-}"
if [[ "$REAL_BASH" != /* || ! -f "$REAL_BASH" || -L "$REAL_BASH" || ! -x "$REAL_BASH" ]]; then
  echo "$CHECK_NAME failed: current Bash executable is not a direct executable file" >&2
  exit 2
fi

capture_directory_identity() {
  "$REAL_PYTHON" -I -S -B - "$1" <<'PY'
import os
import stat
import sys

try:
    metadata = os.lstat(sys.argv[1])
except OSError:
    raise SystemExit(1)
if metadata.st_uid != os.geteuid() or not stat.S_ISDIR(metadata.st_mode):
    raise SystemExit(1)
print(f"{metadata.st_dev}:{metadata.st_ino}")
PY
}

directory_has_identity() {
  local observed
  observed="$(capture_directory_identity "$1")" || return 1
  [[ "$observed" == "$2" ]]
}

TEST_TMP_INPUT="${TMPDIR:-/tmp}"
if ! TEST_TMP_BASE="$(CDPATH='' cd -- "$TEST_TMP_INPUT" && pwd -P)"; then
  echo "$CHECK_NAME failed: cannot canonicalize temporary root: $TEST_TMP_INPUT" >&2
  exit 2
fi
if [[ "$TEST_TMP_BASE" == "/" ]]; then
  echo "$CHECK_NAME failed: refusing filesystem root as temporary root" >&2
  exit 2
fi
TEST_ROOT_LEXICAL="$(mktemp -d "$TEST_TMP_BASE/pid-rs-sxpid3-audit-builder-self-test.XXXXXX")"
if [[ ! -d "$TEST_ROOT_LEXICAL" || -L "$TEST_ROOT_LEXICAL" ]] \
    || ! TEST_ROOT="$(CDPATH='' cd -- "$TEST_ROOT_LEXICAL" && pwd -P)"; then
  echo "$CHECK_NAME failed: mktemp did not create a direct directory" >&2
  exit 2
fi
TEST_ROOT_NAME="${TEST_ROOT##*/}"
if [[ "$TEST_ROOT_LEXICAL" != "$TEST_ROOT" \
    || "$TEST_ROOT" != "$TEST_TMP_BASE/$TEST_ROOT_NAME" \
    || ! "$TEST_ROOT_NAME" =~ ^pid-rs-sxpid3-audit-builder-self-test\.[[:alnum:]]+$ ]]; then
  echo "$CHECK_NAME failed: mktemp returned an unexpected test directory" >&2
  exit 2
fi
if ! TEST_ROOT_ID="$(capture_directory_identity "$TEST_ROOT")"; then
  echo "$CHECK_NAME failed: mktemp test directory lacks fresh-object custody" >&2
  exit 2
fi
cleanup() {
  local status=$?
  if [[ "$TEST_ROOT" == "$TEST_TMP_BASE/$TEST_ROOT_NAME" \
      && "$TEST_ROOT_NAME" =~ ^pid-rs-sxpid3-audit-builder-self-test\.[[:alnum:]]+$ \
      && -d "$TEST_ROOT" && ! -L "$TEST_ROOT" ]] \
      && directory_has_identity "$TEST_ROOT" "$TEST_ROOT_ID"; then
    rm -rf -- "$TEST_ROOT"
  elif [[ -e "$TEST_ROOT" || -L "$TEST_ROOT" ]]; then
    echo "$CHECK_NAME failed: refusing unexpected cleanup path: $TEST_ROOT" >&2
    status=1
  fi
  return "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

FIXTURE_REPO="$TEST_ROOT/repository"
FIXTURE_SCRIPT="$FIXTURE_REPO/scripts/build-sxpid3-source-marginal-audit-pdf.sh"
FIXTURE_FIGURES="$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit"
FIXTURE_LATEX="$FIXTURE_REPO/audit/formal/latex/sxpid3-source-marginal-and-bounded-audit"
OUTPUT_DIRECTORY="$TEST_ROOT/output"
BUILD_TMP="$TEST_ROOT/build-tmp"
FAKE_BIN="$TEST_ROOT/fake-bin"
FAKE_FONTS="$TEST_ROOT/fonts"
LOG_DIRECTORY="$TEST_ROOT/logs"
LAUNCH_HOME="$TEST_ROOT/launch-home"
mkdir -p "$FIXTURE_REPO/scripts" "$FIXTURE_FIGURES" "$FIXTURE_LATEX" \
  "$OUTPUT_DIRECTORY" "$BUILD_TMP" "$FAKE_BIN" "$FAKE_FONTS" "$LOG_DIRECTORY" "$LAUNCH_HOME"

cp "$BUILDER" "$FIXTURE_SCRIPT"
cp "$ID_VARIANCE_CHECK" \
  "$FIXTURE_REPO/scripts/check-mathematical-results-guide-pdf-id-variance.py"
cp "$ROOT/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md" \
  "$FIXTURE_REPO/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md"
cp "$ROOT/audit/formal/latex/sxpid3-source-marginal-and-bounded-audit/header.tex" \
  "$FIXTURE_LATEX/header.tex"
cp "$ROOT/audit/formal/latex/sxpid3-source-marginal-and-bounded-audit/filter.lua" \
  "$FIXTURE_LATEX/filter.lua"
for figure in audit-coordinate-crosswalk.svg audit-coordinate-crosswalk.pdf \
    source-cylinder-factorization.svg source-cylinder-factorization.pdf; do
  cp "$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/$figure" \
    "$FIXTURE_FIGURES/$figure"
done
SOURCE_BASELINE="$TEST_ROOT/source-baseline.md"
cp "$FIXTURE_REPO/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md" "$SOURCE_BASELINE"
CHECKER_BASELINE="$TEST_ROOT/checker-baseline.py"
cp "$FIXTURE_REPO/scripts/check-mathematical-results-guide-pdf-id-variance.py" \
  "$CHECKER_BASELINE"

CROSS_FIRST="$TEST_ROOT/cross-first.pdf"
CROSS_SECOND="$TEST_ROOT/cross-second.pdf"
CROSS_OUTSIDE="$TEST_ROOT/cross-second-outside-id.pdf"
cp "$CANONICAL_PDF" "$CROSS_FIRST"
"$REAL_PYTHON" -I -B - "$CROSS_FIRST" "$CROSS_SECOND" "$CROSS_OUTSIDE" <<'PY'
from __future__ import annotations

import pathlib
import re
import sys

source = pathlib.Path(sys.argv[1]).read_bytes()
match = re.search(
    rb"/ID[ \t\r\n]*\[[ \t\r\n]*<([0-9A-Fa-f]{32})>[ \t\r\n]*"
    rb"<([0-9A-Fa-f]{32})>[ \t\r\n]*\]",
    source,
)
if match is None or match.group(1).lower() != match.group(2).lower():
    raise SystemExit("canonical SxPID3 fixture lacks one duplicated strict trailer ID")
replacement = b"0123456789ABCDEF0123456789ABCDEF"
if match.group(1).upper() == replacement:
    replacement = b"FEDCBA9876543210FEDCBA9876543210"
varied = bytearray(source)
for group in (1, 2):
    varied[match.start(group) : match.end(group)] = replacement
pathlib.Path(sys.argv[2]).write_bytes(varied)
outside = bytearray(varied)
if not outside.startswith(b"%PDF-1."):
    raise SystemExit("canonical SxPID3 fixture has an unexpected PDF header")
outside[7] = ord("6") if outside[7] != ord("6") else ord("7")
pathlib.Path(sys.argv[3]).write_bytes(outside)
PY
"$REAL_PYTHON" -I -B "$ID_VARIANCE_CHECK" "$CROSS_FIRST" "$CROSS_SECOND" >/dev/null

for font in lmroman10-regular.otf lmsans10-regular.otf lmmonolt10-regular.otf \
    latinmodern-math.otf; do
  printf '%s\n' "fixture font $font" >"$FAKE_FONTS/$font"
done

cat >"$FAKE_BIN/kpsewhich" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s/%s\n' "${PID_RS_FIXTURE_FONTS:?}" "$1"
EOF
cat >"$FAKE_BIN/cp" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
"${PID_RS_REAL_CP:?}" "$@"
destination="${!#}"
case "$destination" in
  */.sxpid3-audit.pdf.*)
    if [[ -n "${PID_RS_MUTATE_PUBLICATION_COPY:-}" ]]; then
      printf '%s\n' 'hostile publication-copy mutation' >>"$destination"
    fi
    ;;
esac
EOF
cat >"$FAKE_BIN/cmp" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
fixture_root=""
for argument in "$@"; do
  case "$argument" in
    */build-tmp/*/first/build/*.pdf | */build-tmp/*/second/build/*.pdf)
      fixture_root="${argument%%/build-tmp/*}"
      ;;
  esac
done
if [[ -n "$fixture_root" && -f "$fixture_root/cmp-error.enabled" ]]; then
  exit 2
fi
exec "${PID_RS_REAL_CMP:?}" "$@"
EOF
cat >"$FAKE_BIN/fc-cache" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exit 0
EOF
cat >"$FAKE_BIN/mktemp" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
template="${!#}"
if [[ -n "${PID_RS_FIXTURE_MKTEMP_ESCAPE:-}" && "$1" == "-d" ]]; then
  escaped="${PID_RS_FIXTURE_ROOT:?}/mktemp-escaped-directory"
  mkdir "$escaped"
  printf '%s\n' "$escaped"
  exit 0
fi
if [[ -n "${PID_RS_FIXTURE_MKTEMP_PUBLICATION_ALIAS_SOURCE:-}" && "$1" != "-d" ]]; then
  alias_path="${template%XXXXXX}HARD01"
  ln "${PID_RS_FIXTURE_MKTEMP_PUBLICATION_ALIAS_SOURCE:?}" "$alias_path"
  printf '%s\n' "$alias_path"
  exit 0
fi
case "$template" in
  *X) ;;
  *)
    echo "fixture mktemp rejected a template without terminal X placeholders: $template" >&2
    exit 91
    ;;
esac
exec "${PID_RS_REAL_MKTEMP:?}" "$@"
EOF
cat >"$FAKE_BIN/pandoc" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
output=""
for argument in "$@"; do
  case "$argument" in
    --output=*) output="${argument#--output=}" ;;
  esac
done
[[ -n "$output" ]]
printf '%s\n' '\documentclass{article}' '\begin{document}' 'fixture' '\end{document}' >"$output"
fixture_root="${output%%/build-tmp/*}"
if [[ "$fixture_root" != "$output" && -f "$fixture_root/pandoc-failure.enabled" ]]; then
  echo "fixture forced Pandoc failure after writing usable-looking TeX" >&2
  exit 94
fi
EOF
cat >"$FAKE_BIN/lualatex" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
output_directory=""
job_name=""
for argument in "$@"; do
  case "$argument" in
    --output-directory=*) output_directory="${argument#--output-directory=}" ;;
    --jobname=*) job_name="${argument#--jobname=}" ;;
  esac
done
[[ -n "$output_directory" && -n "$job_name" ]]
fixture_root="${output_directory%%/build-tmp/*}"
if [[ "$fixture_root" != "$output_directory" && -f "$fixture_root/cross-variance.enabled" ]]; then
  case "$output_directory" in
    */first/build) /bin/cp "$fixture_root/cross-first.pdf" "$output_directory/$job_name.pdf" ;;
    */second/build)
      if [[ -f "$fixture_root/outside-id-drift.enabled" ]]; then
        /bin/cp "$fixture_root/cross-second-outside-id.pdf" "$output_directory/$job_name.pdf"
      else
        /bin/cp "$fixture_root/cross-second.pdf" "$output_directory/$job_name.pdf"
      fi
      ;;
    *) echo "fixture cannot classify repeated-build output path" >&2; exit 92 ;;
  esac
else
  printf '%s\n' '%PDF-1.5' 'bounded fixture bytes' >"$output_directory/$job_name.pdf"
fi
printf '%s\n' 'clean fixture log' >"$output_directory/$job_name.log"
if [[ "$fixture_root" != "$output_directory" && -f "$fixture_root/lualatex-failure.enabled" ]]; then
  echo "fixture forced LuaLaTeX failure after writing stale-looking outputs" >&2
  exit 93
fi
EOF
cat >"$FAKE_BIN/python3" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
fixture_root="${PID_RS_FIXTURE_ROOT:?}"
if [[ -f "$fixture_root/checker-error.enabled" ]]; then
  is_variance_checker=0
  is_projection=1
  for argument in "$@"; do
    case "$argument" in
      */check-mathematical-results-guide-pdf-id-variance.py) is_variance_checker=1 ;;
      --validate-inputs) is_projection=0 ;;
    esac
  done
  if [[ "$is_variance_checker" -eq 1 && "$is_projection" -eq 1 ]]; then
    echo "fixture forced trailer-ID checker failure" >&2
    exit 86
  fi
fi
exec "${PID_RS_REAL_PYTHON:?}" "$@"
EOF
cat >"$FAKE_BIN/pdfinfo" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' 'Pages:           18' 'Page size:       595.276 x 841.89 pts (A4)' 'Tagged:          yes'
EOF
cat >"$FAKE_BIN/pdffonts" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' \
  'name                                 type              encoding         emb sub uni object ID' \
  '------------------------------------ ----------------- ---------------- --- --- --- ---------' \
  'AAAAAA+LMRoman10-Regular             CID Type 0C       Identity-H       yes yes yes      1  0'
EOF
cat >"$FAKE_BIN/pdftotext" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
output="${!#}"
printf '%s\n' \
  'Paper event semantics' \
  'fresh owner-controlled HTTPS' \
  'separate exact compatibility edge' \
  '18/108/166 crosswalk' \
  '20,348 tables' \
  '2,197,584' \
  'complete certificate' \
  'compatibility-literal rejections' \
  'exact type, shape, and value' \
  'disposable-checkout integrity failure' \
  'Explicit nonclaims and negative results' >"$output"
if [[ -n "${PID_RS_MUTATE_SOURCE:-}" ]]; then
  printf '%s\n' 'hostile source mutation' >>"$PID_RS_MUTATE_SOURCE"
fi
if [[ -n "${PID_RS_MUTATE_OUTPUT:-}" ]]; then
  ln "$PID_RS_MUTATE_ALIAS_SOURCE" "$PID_RS_MUTATE_OUTPUT"
fi
if [[ -n "${PID_RS_MUTATE_STAGED_CHECKER:-}" || -n "${PID_RS_MUTATE_BUILT_OUTPUT:-}" ]]; then
  for argument in "$@"; do
    case "$argument" in
      */first/build/*.pdf)
        build_root="${argument%%/first/build/*}"
        if [[ -n "${PID_RS_MUTATE_STAGED_CHECKER:-}" ]]; then
          printf '%s\n' '# hostile staged-checker mutation' \
            >>"$build_root/second/repository/scripts/check-mathematical-results-guide-pdf-id-variance.py"
        fi
        if [[ -n "${PID_RS_MUTATE_BUILT_OUTPUT:-}" ]]; then
          printf '%s\n' 'hostile repeated-build output mutation' >>"$argument"
        fi
        ;;
    esac
  done
fi
EOF
chmod 755 "$FAKE_BIN"/*

TEST_PATH="$FAKE_BIN:${REAL_PYTHON%/*}:/usr/bin:/bin:/usr/sbin:/sbin"
CONTROLS=0
HOSTILES=0
STATIC_GUARDS=0

# The search string is a deliberate literal source guard.
# shellcheck disable=SC2016
grep -Fq '"$BUILDER" "$MODE" "$BUILT"' "$PDF_CHECK" || {
  echo "$CHECK_NAME failed: PDF gate no longer passes its mode into the Sx builder" >&2
  exit 1
}
STATIC_GUARDS=$((STATIC_GUARDS + 1))
# The search string is a deliberate literal source guard.
# shellcheck disable=SC2016
grep -Fq 'cmp -s "$BUILD_ROOT/built.txt" "$BUILD_ROOT/committed.txt"' "$PDF_CHECK" || {
  echo "$CHECK_NAME failed: PDF gate no longer raw-compares cross-toolchain text" >&2
  exit 1
}
STATIC_GUARDS=$((STATIC_GUARDS + 1))
if grep -Fq 'pdf-id-variance' "$PDF_CHECK"; then
  echo "$CHECK_NAME failed: PDF gate may not apply the repeated-build ID projection to the committed comparison" >&2
  exit 1
fi
STATIC_GUARDS=$((STATIC_GUARDS + 1))
if grep -Fq 'font-alpha-equivalence' "$PDF_CHECK" \
    || grep -Fq 'font-alpha-equivalence' "$BUILDER"; then
  echo "$CHECK_NAME failed: guide-only font alpha-equivalence leaked into the SxPID3 build or PDF gate" >&2
  exit 1
fi
STATIC_GUARDS=$((STATIC_GUARDS + 1))
clean_boundary_count="$(grep -Fc '/usr/bin/env -i PATH="$PATH"' "$PDF_CHECK" || true)"
if [[ "$clean_boundary_count" -ne 2 ]]; then
  echo "$CHECK_NAME failed: PDF gate must clean the environment for both nested Bash launches" >&2
  exit 1
fi
STATIC_GUARDS=$((STATIC_GUARDS + 1))

run_builder() {
  local output="$1" stdout="$2" stderr="$3"
  shift 3
  /usr/bin/env -i PATH="$TEST_PATH" HOME="$LAUNCH_HOME" TMPDIR="$TEST_ROOT" \
    PID_RS_FIXTURE_ROOT="$TEST_ROOT" \
    PID_RS_FIXTURE_FONTS="$FAKE_FONTS" \
    PID_RS_PDF_TMPDIR="$BUILD_TMP" PID_RS_REAL_CP="$REAL_CP" \
    PID_RS_REAL_CMP="$REAL_CMP" PID_RS_REAL_MKTEMP="$REAL_MKTEMP" \
    PID_RS_REAL_PYTHON="$REAL_PYTHON" "$@" BASH_ENV=/dev/null ENV=/dev/null \
    "$REAL_BASH" --noprofile --norc "$FIXTURE_SCRIPT" "$output" >"$stdout" 2>"$stderr"
}

run_builder_mode() {
  local mode="$1" output="$2" stdout="$3" stderr="$4"
  shift 4
  /usr/bin/env -i PATH="$TEST_PATH" HOME="$LAUNCH_HOME" TMPDIR="$TEST_ROOT" \
    PID_RS_FIXTURE_ROOT="$TEST_ROOT" \
    PID_RS_FIXTURE_FONTS="$FAKE_FONTS" \
    PID_RS_PDF_TMPDIR="$BUILD_TMP" PID_RS_REAL_CP="$REAL_CP" \
    PID_RS_REAL_CMP="$REAL_CMP" PID_RS_REAL_MKTEMP="$REAL_MKTEMP" \
    PID_RS_REAL_PYTHON="$REAL_PYTHON" "$@" BASH_ENV=/dev/null ENV=/dev/null \
    "$REAL_BASH" --noprofile --norc "$FIXTURE_SCRIPT" "$mode" "$output" >"$stdout" 2>"$stderr"
}

run_builder_single_argument() {
  local argument="$1" stdout="$2" stderr="$3"
  /usr/bin/env -i PATH="$TEST_PATH" HOME="$LAUNCH_HOME" TMPDIR="$TEST_ROOT" \
    PID_RS_FIXTURE_ROOT="$TEST_ROOT" \
    PID_RS_FIXTURE_FONTS="$FAKE_FONTS" \
    PID_RS_PDF_TMPDIR="$BUILD_TMP" PID_RS_REAL_CP="$REAL_CP" \
    PID_RS_REAL_CMP="$REAL_CMP" PID_RS_REAL_MKTEMP="$REAL_MKTEMP" \
    PID_RS_REAL_PYTHON="$REAL_PYTHON" BASH_ENV=/dev/null ENV=/dev/null \
    "$REAL_BASH" --noprofile --norc "$FIXTURE_SCRIPT" "$argument" >"$stdout" 2>"$stderr"
}

require_no_temporary_residue() {
  local label="$1" residue build_residue
  residue="$(find "$OUTPUT_DIRECTORY" -maxdepth 1 -name '.sxpid3-audit.pdf.*' -print -quit)"
  if [[ -n "$residue" ]]; then
    echo "$CHECK_NAME failed: temporary publication residue after $label: $residue" >&2
    exit 1
  fi
  build_residue="$(find "$BUILD_TMP" -maxdepth 1 -name 'pid-rs-sxpid3-audit-pdf.*' -print -quit)"
  if [[ -n "$build_residue" ]]; then
    echo "$CHECK_NAME failed: temporary build-root residue after $label: $build_residue" >&2
    exit 1
  fi
}

require_success() {
  local label="$1" output="$2"
  local stdout="$LOG_DIRECTORY/$label.stdout" stderr="$LOG_DIRECTORY/$label.stderr"
  shift 2
  if ! run_builder "$output" "$stdout" "$stderr" "$@"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME failed: accepted control failed: $label" >&2
    exit 1
  fi
  if [[ -s "$stderr" || ! -f "$output" || -L "$output" ]]; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME failed: accepted control did not publish one direct regular file: $label" >&2
    exit 1
  fi
  grep -Fq 'OK: built' "$stdout" || {
    echo "$CHECK_NAME failed: accepted control lacks success record: $label" >&2
    exit 1
  }
  require_no_temporary_residue "$label"
  CONTROLS=$((CONTROLS + 1))
}

require_failure() {
  local label="$1" expected="$2" output="$3"
  local stdout="$LOG_DIRECTORY/$label.stdout" stderr="$LOG_DIRECTORY/$label.stderr"
  shift 3
  if run_builder "$output" "$stdout" "$stderr" "$@"; then
    echo "$CHECK_NAME failed: hostile case passed: $label" >&2
    exit 1
  fi
  if ! grep -Fq -- "$expected" "$stderr"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME failed: hostile case had the wrong diagnostic: $label" >&2
    exit 1
  fi
  require_no_temporary_residue "$label"
  HOSTILES=$((HOSTILES + 1))
}

require_success_mode() {
  local mode="$1" label="$2" output="$3"
  local stdout="$LOG_DIRECTORY/$label.stdout" stderr="$LOG_DIRECTORY/$label.stderr"
  shift 3
  if ! run_builder_mode "$mode" "$output" "$stdout" "$stderr" "$@"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME failed: accepted mode control failed: $label" >&2
    exit 1
  fi
  if [[ -s "$stderr" || ! -f "$output" || -L "$output" ]]; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME failed: accepted mode control did not publish one direct regular file: $label" >&2
    exit 1
  fi
  grep -Fq 'OK: built' "$stdout" || {
    echo "$CHECK_NAME failed: accepted mode control lacks success record: $label" >&2
    exit 1
  }
  require_no_temporary_residue "$label"
  CONTROLS=$((CONTROLS + 1))
}

require_failure_mode() {
  local mode="$1" label="$2" expected="$3" output="$4"
  local stdout="$LOG_DIRECTORY/$label.stdout" stderr="$LOG_DIRECTORY/$label.stderr"
  shift 4
  if run_builder_mode "$mode" "$output" "$stdout" "$stderr" "$@"; then
    echo "$CHECK_NAME failed: hostile mode case passed: $label" >&2
    exit 1
  fi
  if ! grep -Fq -- "$expected" "$stderr"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME failed: hostile mode case had the wrong diagnostic: $label" >&2
    exit 1
  fi
  require_no_temporary_residue "$label"
  HOSTILES=$((HOSTILES + 1))
}

ABSENT_OUTPUT="$OUTPUT_DIRECTORY/accepted-absent.pdf"
require_success accepted-absent "$ABSENT_OUTPUT"
printf '%s\n' 'stale regular output' >"$OUTPUT_DIRECTORY/accepted-existing.pdf"
require_success accepted-existing "$OUTPUT_DIRECTORY/accepted-existing.pdf"
require_success_mode --exact explicit-exact "$OUTPUT_DIRECTORY/accepted-explicit-exact.pdf"
require_success_mode --cross-toolchain cross-equal "$OUTPUT_DIRECTORY/accepted-cross-equal.pdf"
BASH_ENV_MARKER="$TEST_ROOT/bash-env-was-sourced"
BASH_ENV_PAYLOAD="$TEST_ROOT/hostile-bash-env.sh"
printf ': >%q\n' "$BASH_ENV_MARKER" >"$BASH_ENV_PAYLOAD"
require_success isolated-nested-bash-env "$OUTPUT_DIRECTORY/accepted-isolated-bash-env.pdf" \
  env BASH_ENV="$BASH_ENV_PAYLOAD" ENV="$BASH_ENV_PAYLOAD"
if [[ -e "$BASH_ENV_MARKER" || -L "$BASH_ENV_MARKER" ]]; then
  echo "$CHECK_NAME failed: nested Bash sourced the hostile BASH_ENV payload" >&2
  exit 1
fi
EXPORTED_FUNCTION_MARKER="$TEST_ROOT/exported-function-was-invoked"
PID_RS_EXPORTED_FUNCTION_MARKER="$EXPORTED_FUNCTION_MARKER"
export PID_RS_EXPORTED_FUNCTION_MARKER
mktemp() {
  : >"$PID_RS_EXPORTED_FUNCTION_MARKER"
  return 97
}
export -f mktemp
require_success isolated-exported-function \
  "$OUTPUT_DIRECTORY/accepted-isolated-exported-function.pdf"
unset -f mktemp
unset PID_RS_EXPORTED_FUNCTION_MARKER
if [[ -e "$EXPORTED_FUNCTION_MARKER" || -L "$EXPORTED_FUNCTION_MARKER" ]]; then
  echo "$CHECK_NAME failed: nested Bash imported an exported function" >&2
  exit 1
fi
require_success trailing-slash-temp "$OUTPUT_DIRECTORY/accepted-trailing-temp.pdf" \
  env PID_RS_PDF_TMPDIR="$BUILD_TMP/"
ln -s "$BUILD_TMP" "$TEST_ROOT/build-tmp-link"
require_success symbolic-temp-root "$OUTPUT_DIRECTORY/accepted-symbolic-temp.pdf" \
  env PID_RS_PDF_TMPDIR="$TEST_ROOT/build-tmp-link"

require_failure absent-temp-root 'cannot canonicalize temporary root' \
  "$OUTPUT_DIRECTORY/absent-temp-root.pdf" \
  env PID_RS_PDF_TMPDIR="$TEST_ROOT/absent-build-tmp"
require_failure root-temp-root 'refusing filesystem root as temporary root' \
  "$OUTPUT_DIRECTORY/root-temp-root.pdf" env PID_RS_PDF_TMPDIR=/
require_failure escaped-mktemp-build-root 'mktemp returned an unexpected build directory' \
  "$OUTPUT_DIRECTORY/escaped-mktemp-build-root.pdf" \
  env PID_RS_FIXTURE_MKTEMP_ESCAPE=1
if [[ ! -d "$TEST_ROOT/mktemp-escaped-directory" \
    || -L "$TEST_ROOT/mktemp-escaped-directory" ]]; then
  echo "$CHECK_NAME failed: escaped-mktemp fixture did not retain its refused directory" >&2
  exit 1
fi
rmdir "$TEST_ROOT/mktemp-escaped-directory"

PUBLICATION_ALIAS_VICTIM="$TEST_ROOT/publication-alias-victim"
printf '%s\n' 'must remain unchanged' >"$PUBLICATION_ALIAS_VICTIM"
PUBLICATION_ALIAS_VICTIM_DIGEST="$(shasum -a 256 "$PUBLICATION_ALIAS_VICTIM")"
PUBLICATION_ALIAS_PATH="$OUTPUT_DIRECTORY/.sxpid3-audit.pdf.HARD01"
publication_alias_stdout="$LOG_DIRECTORY/publication-temp-hardlink.stdout"
publication_alias_stderr="$LOG_DIRECTORY/publication-temp-hardlink.stderr"
publication_alias_output="$OUTPUT_DIRECTORY/publication-temp-hardlink-output.pdf"
if run_builder "$publication_alias_output" "$publication_alias_stdout" \
    "$publication_alias_stderr" env \
    PID_RS_FIXTURE_MKTEMP_PUBLICATION_ALIAS_SOURCE="$PUBLICATION_ALIAS_VICTIM"; then
  echo "$CHECK_NAME failed: publication-temporary hard-link fixture passed" >&2
  exit 1
fi
grep -Fq 'publication temporary is not a fresh owned single-link file' \
  "$publication_alias_stderr" || {
    cat "$publication_alias_stdout" "$publication_alias_stderr" >&2
    echo "$CHECK_NAME failed: publication-temporary hard-link fixture had the wrong diagnostic" >&2
    exit 1
  }
if [[ ! -f "$PUBLICATION_ALIAS_PATH" || -L "$PUBLICATION_ALIAS_PATH" \
    || ! "$PUBLICATION_ALIAS_PATH" -ef "$PUBLICATION_ALIAS_VICTIM" ]]; then
  echo "$CHECK_NAME failed: refused publication hard link was not retained for adjudication" >&2
  exit 1
fi
if [[ "$(shasum -a 256 "$PUBLICATION_ALIAS_VICTIM")" \
    != "$PUBLICATION_ALIAS_VICTIM_DIGEST" ]]; then
  echo "$CHECK_NAME failed: publication-temporary hard link changed its victim" >&2
  exit 1
fi
if [[ -e "$publication_alias_output" || -L "$publication_alias_output" ]]; then
  echo "$CHECK_NAME failed: publication-temporary hard-link fixture published an output" >&2
  exit 1
fi
rm -f -- "$PUBLICATION_ALIAS_PATH"
require_no_temporary_residue publication-temp-hardlink
HOSTILES=$((HOSTILES + 1))

missing_cross_stdout="$LOG_DIRECTORY/cross-missing-output.stdout"
missing_cross_stderr="$LOG_DIRECTORY/cross-missing-output.stderr"
if run_builder_single_argument --cross-toolchain "$missing_cross_stdout" "$missing_cross_stderr"; then
  echo "$CHECK_NAME failed: cross mode without a scratch output passed" >&2
  exit 1
fi
grep -Fq 'requires an explicit scratch output distinct from the canonical PDF' \
  "$missing_cross_stderr" || {
    cat "$missing_cross_stdout" "$missing_cross_stderr" >&2
    echo "$CHECK_NAME failed: cross mode without output had the wrong diagnostic" >&2
    exit 1
  }
HOSTILES=$((HOSTILES + 1))

CANONICAL_FIXTURE_OUTPUT="$FIXTURE_REPO/output/pdf/sxpid3-source-marginal-and-bounded-audit.pdf"
require_failure_mode --cross-toolchain cross-canonical-output \
  'requires an explicit scratch output distinct from the canonical PDF' \
  "$CANONICAL_FIXTURE_OUTPUT"
mkdir -p "${CANONICAL_FIXTURE_OUTPUT%/*}"
cp "$CROSS_FIRST" "$CANONICAL_FIXTURE_OUTPUT"
CANONICAL_ALIAS="$OUTPUT_DIRECTORY/cross-canonical-hardlink.pdf"
ln "$CANONICAL_FIXTURE_OUTPUT" "$CANONICAL_ALIAS"
require_failure_mode --cross-toolchain cross-canonical-hardlink \
  'cross-toolchain output aliases the canonical PDF' "$CANONICAL_ALIAS"
rm -f -- "$CANONICAL_ALIAS"

require_failure_mode --invalid invalid-mode 'usage:' "$OUTPUT_DIRECTORY/invalid-mode.pdf"

: >"$TEST_ROOT/cross-variance.enabled"
require_failure_mode --exact exact-rejects-id-variance 'repeated builds differ' \
  "$OUTPUT_DIRECTORY/exact-id-variance.pdf"
require_success_mode --cross-toolchain cross-accepts-id-variance \
  "$OUTPUT_DIRECTORY/cross-id-variance.pdf"

: >"$TEST_ROOT/outside-id-drift.enabled"
require_failure_mode --cross-toolchain cross-rejects-outside-id-drift \
  'differ beyond the strict trailer-ID projection' \
  "$OUTPUT_DIRECTORY/cross-outside-id-drift.pdf"
rm -f -- "$TEST_ROOT/outside-id-drift.enabled"

: >"$TEST_ROOT/checker-error.enabled"
require_failure_mode --cross-toolchain cross-checker-error-is-fatal \
  'differ beyond the strict trailer-ID projection' \
  "$OUTPUT_DIRECTORY/cross-checker-error.pdf"
rm -f -- "$TEST_ROOT/checker-error.enabled"

: >"$TEST_ROOT/cmp-error.enabled"
require_failure_mode --cross-toolchain cross-cmp-error-is-fatal \
  'repeated-build cmp had operational status 2' \
  "$OUTPUT_DIRECTORY/cross-cmp-error.pdf"
rm -f -- "$TEST_ROOT/cmp-error.enabled" "$TEST_ROOT/cross-variance.enabled"

printf '%s\n' '# hostile checker mutation' \
  >>"$FIXTURE_REPO/scripts/check-mathematical-results-guide-pdf-id-variance.py"
require_failure checker-digest-mutation 'trailer-ID variance checker digest changed' \
  "$OUTPUT_DIRECTORY/checker-digest-mutation.pdf"
cp "$CHECKER_BASELINE" \
  "$FIXTURE_REPO/scripts/check-mathematical-results-guide-pdf-id-variance.py"

: >"$TEST_ROOT/pandoc-failure.enabled"
require_failure pandoc-failure-with-usable-output 'Pandoc conversion failed' \
  "$OUTPUT_DIRECTORY/pandoc-failure.pdf"
rm -f -- "$TEST_ROOT/pandoc-failure.enabled"

: >"$TEST_ROOT/lualatex-failure.enabled"
require_failure lualatex-failure-with-stale-outputs 'LuaLaTeX pass 1 failed' \
  "$OUTPUT_DIRECTORY/lualatex-failure.pdf"
rm -f -- "$TEST_ROOT/lualatex-failure.enabled"

require_failure relative-output 'output must be a canonical absolute path' 'relative.pdf'
require_failure noncanonical-output 'symbolic or noncanonical component' \
  "$OUTPUT_DIRECTORY/./noncanonical.pdf"
require_failure missing-parent 'output parent is absent or not a directory' \
  "$OUTPUT_DIRECTORY/missing/result.pdf"
require_failure wrong-suffix 'output path must name a .pdf file' "$OUTPUT_DIRECTORY/result.txt"
require_failure root-parent 'filesystem root is not an admissible output parent' '/pid-rs-sxpid3-test.pdf'

mkdir "$OUTPUT_DIRECTORY/nonregular-directory.pdf"
require_failure directory-output 'existing output is not a regular file' \
  "$OUTPUT_DIRECTORY/nonregular-directory.pdf"
mkfifo "$OUTPUT_DIRECTORY/nonregular-fifo.pdf"
require_failure fifo-output 'existing output is not a regular file' \
  "$OUTPUT_DIRECTORY/nonregular-fifo.pdf"

ln -s "$FIXTURE_FIGURES/source-cylinder-factorization.pdf" \
  "$OUTPUT_DIRECTORY/symbolic-output.pdf"
require_failure symbolic-output 'output must not be symbolic' "$OUTPUT_DIRECTORY/symbolic-output.pdf"

ln -s "$OUTPUT_DIRECTORY" "$TEST_ROOT/output-link"
require_failure symbolic-parent 'symbolic or noncanonical component' \
  "$TEST_ROOT/output-link/symbolic-parent.pdf"

required_sources=(
  "$FIXTURE_REPO/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md"
  "$FIXTURE_LATEX/header.tex"
  "$FIXTURE_LATEX/filter.lua"
  "$FIXTURE_FIGURES/audit-coordinate-crosswalk.svg"
  "$FIXTURE_FIGURES/audit-coordinate-crosswalk.pdf"
  "$FIXTURE_FIGURES/source-cylinder-factorization.svg"
  "$FIXTURE_FIGURES/source-cylinder-factorization.pdf"
  "$FIXTURE_REPO/scripts/check-mathematical-results-guide-pdf-id-variance.py"
)
alias_index=0
for required_source in "${required_sources[@]}"; do
  alias_index=$((alias_index + 1))
  alias_output="$OUTPUT_DIRECTORY/hardlink-alias-$alias_index.pdf"
  ln "$required_source" "$alias_output"
  require_failure "hardlink-alias-$alias_index" 'output aliases required source' "$alias_output"
  rm -f -- "$alias_output"
done
require_failure exact-source-path 'output aliases required source' \
  "$FIXTURE_FIGURES/source-cylinder-factorization.pdf"

MUTATED_OUTPUT="$OUTPUT_DIRECTORY/mutated-source.pdf"
require_failure source-byte-mutation 'a required source changed during the build' "$MUTATED_OUTPUT" \
  env PID_RS_MUTATE_SOURCE="$FIXTURE_REPO/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md"
if [[ -e "$MUTATED_OUTPUT" || -L "$MUTATED_OUTPUT" ]]; then
  echo "$CHECK_NAME failed: source mutation published an output" >&2
  exit 1
fi
cp "$SOURCE_BASELINE" "$FIXTURE_REPO/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md"

STAGED_CHECKER_MUTATION_OUTPUT="$OUTPUT_DIRECTORY/mutated-staged-checker.pdf"
require_failure staged-checker-byte-mutation 'trailer-ID variance checker digest changed' \
  "$STAGED_CHECKER_MUTATION_OUTPUT" env PID_RS_MUTATE_STAGED_CHECKER=1
if [[ -e "$STAGED_CHECKER_MUTATION_OUTPUT" || -L "$STAGED_CHECKER_MUTATION_OUTPUT" ]]; then
  echo "$CHECK_NAME failed: staged-checker mutation published an output" >&2
  exit 1
fi

BUILT_OUTPUT_MUTATION_OUTPUT="$OUTPUT_DIRECTORY/mutated-repeated-build-output.pdf"
require_failure repeated-build-output-mutation 'repeated-build output changed after comparison' \
  "$BUILT_OUTPUT_MUTATION_OUTPUT" env PID_RS_MUTATE_BUILT_OUTPUT=1
if [[ -e "$BUILT_OUTPUT_MUTATION_OUTPUT" || -L "$BUILT_OUTPUT_MUTATION_OUTPUT" ]]; then
  echo "$CHECK_NAME failed: repeated-build output mutation published an output" >&2
  exit 1
fi

APPEARING_OUTPUT="$OUTPUT_DIRECTORY/appearing-alias.pdf"
require_failure output-alias-mutation 'output aliases required source' "$APPEARING_OUTPUT" \
  env PID_RS_MUTATE_OUTPUT="$APPEARING_OUTPUT" \
    PID_RS_MUTATE_ALIAS_SOURCE="$FIXTURE_FIGURES/source-cylinder-factorization.pdf"
if [[ ! "$APPEARING_OUTPUT" -ef "$FIXTURE_FIGURES/source-cylinder-factorization.pdf" ]]; then
  echo "$CHECK_NAME failed: output-alias mutation did not install its hostile alias" >&2
  exit 1
fi
rm -f -- "$APPEARING_OUTPUT"

COPY_MUTATION_OUTPUT="$OUTPUT_DIRECTORY/publication-copy-mutation.pdf"
require_failure publication-copy-mutation \
  'publication copy differs from the validated first build' "$COPY_MUTATION_OUTPUT" \
  env PID_RS_MUTATE_PUBLICATION_COPY=1
if [[ -e "$COPY_MUTATION_OUTPUT" || -L "$COPY_MUTATION_OUTPUT" ]]; then
  echo "$CHECK_NAME failed: publication-copy mutation published an output" >&2
  exit 1
fi

if ! cmp -s "$SOURCE_BASELINE" "$FIXTURE_REPO/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md"; then
  echo "$CHECK_NAME failed: fixture source was not restored" >&2
  exit 1
fi

echo "OK: $CHECK_NAME (controls=$CONTROLS; hostile_cases=$HOSTILES; required_source_aliases=$alias_index; static_guards=$STATIC_GUARDS)"
