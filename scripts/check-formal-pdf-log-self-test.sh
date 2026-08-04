#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="${BASH_SOURCE[0]%/*}"
if [[ "$SCRIPT_DIRECTORY" == "${BASH_SOURCE[0]}" ]]; then
  SCRIPT_DIRECTORY="."
fi
ROOT="$(cd "$SCRIPT_DIRECTORY/.." && pwd -P)"
CHECKER="$ROOT/scripts/check-formal-pdf-log.sh"
TMP_ROOT="${TMPDIR:-/tmp}"
FIXTURE_ROOT="$(mktemp -d "$TMP_ROOT/pid-rs-formal-pdf-log-self-test.XXXXXX")"
trap 'rm -rf -- "$FIXTURE_ROOT"' EXIT

require_accept() {
  local name="$1"
  local line="$2"
  local log="$FIXTURE_ROOT/$name.log"
  local stdout="$FIXTURE_ROOT/$name.stdout"
  local stderr="$FIXTURE_ROOT/$name.stderr"
  printf '%s\n' "$line" >"$log"
  if ! bash "$CHECKER" "$log" >"$stdout" 2>"$stderr"; then
    echo "formal PDF log self-test: accepted control failed: $name" >&2
    return 1
  fi
  if [[ -s "$stdout" || -s "$stderr" ]]; then
    echo "formal PDF log self-test: accepted control emitted output: $name" >&2
    return 1
  fi
}

require_reject() {
  local name="$1"
  local line="$2"
  local log="$FIXTURE_ROOT/$name.log"
  local stdout="$FIXTURE_ROOT/$name.stdout"
  local stderr="$FIXTURE_ROOT/$name.stderr"
  local status
  printf '%s\n' "$line" >"$log"
  set +e
  bash "$CHECKER" "$log" >"$stdout" 2>"$stderr"
  status=$?
  set -e
  if [[ "$status" -ne 1 ]]; then
    echo "formal PDF log self-test: rejected mutation returned $status: $name" >&2
    return 1
  fi
  if [[ -s "$stdout" ]] || ! cmp -s "$log" "$stderr"; then
    echo "formal PDF log self-test: rejected mutation output drifted: $name" >&2
    return 1
  fi
}

require_intermediate_accept() {
  local name="$1"
  local line="$2"
  local log="$FIXTURE_ROOT/$name.log"
  local stdout="$FIXTURE_ROOT/$name.stdout"
  local stderr="$FIXTURE_ROOT/$name.stderr"
  printf '%s\n' "$line" >"$log"
  if ! bash "$CHECKER" --intermediate "$log" >"$stdout" 2>"$stderr"; then
    echo "formal PDF log self-test: intermediate convergence control failed: $name" >&2
    return 1
  fi
  if [[ -s "$stdout" || -s "$stderr" ]]; then
    echo "formal PDF log self-test: intermediate convergence control emitted output: $name" >&2
    return 1
  fi
}

require_intermediate_reject() {
  local name="$1"
  local line="$2"
  local log="$FIXTURE_ROOT/$name.log"
  local stdout="$FIXTURE_ROOT/$name.stdout"
  local stderr="$FIXTURE_ROOT/$name.stderr"
  local status
  printf '%s\n' "$line" >"$log"
  set +e
  bash "$CHECKER" --intermediate "$log" >"$stdout" 2>"$stderr"
  status=$?
  set -e
  if [[ "$status" -ne 1 || -s "$stdout" ]] || ! cmp -s "$log" "$stderr"; then
    echo "formal PDF log self-test: intermediate mutation did not fail closed: $name" >&2
    return 1
  fi
}

require_accept "clean-output" "Output written on paper.pdf (12 pages, 123456 bytes)."
require_accept "informational-message" "Package microtype Info: Character ignored."
require_accept "font-information" "LaTeX Font Info: Font shape declared on input line 7."
require_accept "engine-information" "LuaTeX Info: deterministic object stream enabled."

require_reject "latex-warning" "LaTeX Warning: Reference undefined on input line 7."
require_reject "package-warning" "Package hyperref Warning: Token not allowed in a PDF string."
require_reject "class-warning" "Class article Warning: Unsupported class option on input line 1."
require_reject "font-warning" "LaTeX Font Warning: Font shape unavailable on input line 9."
require_reject "pdftex-warning" "pdfTeX warning (dest): name{section.1} has been referenced but does not exist"
require_reject "luatex-warning" "LuaTeX warning (file missing.pdf): PDF inclusion: required page does not exist"
require_reject "xdvipdfmx-warning" "xdvipdfmx:warning: Unparsed material at end of special ignored."
require_reject "missing-character" "Missing character: There is no U+2212 in font LatinModernRoman!"
require_reject "overfull-hbox" 'Overfull \hbox (2.0pt too wide) in paragraph at lines 1--2'
require_reject "underfull-hbox" 'Underfull \hbox (badness 10000) in paragraph at lines 1--2'
require_reject "overfull-vbox" 'Overfull \vbox (33.7033pt too high) has occurred while \output is active []'
require_reject "underfull-vbox" 'Underfull \vbox (badness 10000) has occurred while \output is active []'
require_reject "undefined-references" "There were undefined references."
require_reject "undefined-citations" "There were undefined citations."
require_reject "multiply-defined" "There were multiply defined labels."
require_reject "rerun-outlines" "Rerun to get outlines right"
require_reject "latex-error" "! LaTeX Error: File missing.sty not found."
require_reject "package-error" "! Package graphicx Error: Unknown graphics extension."
require_reject "emergency-stop" "! Emergency stop."
require_reject "runaway-argument" "Runaway argument?"
require_reject "undefined-control" "! Undefined control sequence."
require_reject "fatal-error" "Fatal error occurred, no output PDF file produced!"

require_intermediate_accept \
  "intermediate-reference" \
  "LaTeX Warning: Reference \`sec:one' on page 1 undefined on input line 7."
require_intermediate_accept \
  "intermediate-undefined-summary" \
  "LaTeX Warning: There were undefined references."
require_intermediate_accept \
  "intermediate-cross-reference-rerun" \
  "LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right."
require_intermediate_accept \
  "intermediate-outline-file" \
  "Package rerunfilecheck Warning: File \`paper.out' has changed."
require_intermediate_accept \
  "intermediate-outline-rerun" \
  "(rerunfilecheck)                Rerun to get outlines right"
require_intermediate_reject \
  "intermediate-package-warning" \
  "Package hyperref Warning: Token not allowed in a PDF string."
require_intermediate_reject \
  "intermediate-overfull" \
  'Overfull \hbox (2.0pt too wide) in paragraph at lines 1--2'

set +e
bash "$CHECKER" "$FIXTURE_ROOT/absent.log" >"$FIXTURE_ROOT/missing.stdout" \
  2>"$FIXTURE_ROOT/missing.stderr"
MISSING_STATUS=$?
bash "$CHECKER" >"$FIXTURE_ROOT/usage.stdout" 2>"$FIXTURE_ROOT/usage.stderr"
USAGE_STATUS=$?
set -e
if [[ "$MISSING_STATUS" -ne 2 ]] \
  || ! grep -F -- "missing or unreadable LaTeX log" "$FIXTURE_ROOT/missing.stderr" >/dev/null \
  || [[ -s "$FIXTURE_ROOT/missing.stdout" ]]; then
  echo "formal PDF log self-test: missing-log control did not fail closed" >&2
  exit 1
fi
if [[ "$USAGE_STATUS" -ne 2 ]] \
  || ! grep -F -- "usage:" "$FIXTURE_ROOT/usage.stderr" >/dev/null \
  || [[ -s "$FIXTURE_ROOT/usage.stdout" ]]; then
  echo "formal PDF log self-test: usage control did not fail closed" >&2
  exit 1
fi

echo "OK: 24 formal-PDF log mutations fail closed; nine clean/convergence and two interface controls pass"
