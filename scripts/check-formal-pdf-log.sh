#!/usr/bin/env bash
set -euo pipefail

MODE="final"
case "$#" in
  1)
    LOG="$1"
    ;;
  2)
    if [[ "$1" != "--intermediate" ]]; then
      echo "usage: $0 [--intermediate] LATEX_LOG" >&2
      exit 2
    fi
    MODE="intermediate"
    LOG="$2"
    ;;
  *)
    echo "usage: $0 [--intermediate] LATEX_LOG" >&2
    exit 2
    ;;
esac
if [[ ! -f "$LOG" || ! -r "$LOG" ]]; then
  echo "formal PDF log check: missing or unreadable LaTeX log: $LOG" >&2
  exit 2
fi

# This helper defines the strict final-pass policy. A caller may separately request the bounded
# intermediate-pass policy, which admits only named cross-reference convergence diagnostics while
# still rejecting box, font, package, engine, and fatal diagnostics. Wiring is explicit at each
# formal-PDF leaf; this helper does not claim repository-wide coverage by itself.
REJECTED_DIAGNOSTICS='(^|[[:space:]])(LaTeX Warning:|Package [^[:space:]]+ Warning:|Class [^[:space:]]+ Warning:|LaTeX Font Warning:|(pdfTeX|LuaTeX|LuaHBTeX) warning|xdvipdfmx:warning:|Missing character:|Overfull \\[hv]box|Underfull \\[hv]box|undefined references|undefined citations|multiply defined|Rerun to get (cross-references|outlines) right|Fatal error|Emergency stop|TeX capacity exceeded|Runaway argument|Undefined control sequence)|^! (LaTeX|Package [^[:space:]]+) Error:'
INTERMEDIATE_ALLOWED='LaTeX Warning: Reference .* undefined on input|LaTeX Warning: There were undefined references\.|LaTeX Warning: Label\(s\) may have changed\. Rerun to get cross-references right\.|Package rerunfilecheck Warning: File |\(rerunfilecheck\).*Rerun to get outlines right'

set +e
MATCHES="$(LC_ALL=C grep -E -- "$REJECTED_DIAGNOSTICS" "$LOG")"
GREP_STATUS=$?
set -e

case "$GREP_STATUS" in
  0)
    if [[ "$MODE" == "intermediate" ]]; then
      set +e
      DISALLOWED="$(printf '%s\n' "$MATCHES" | LC_ALL=C grep -Ev -- "$INTERMEDIATE_ALLOWED")"
      DISALLOWED_STATUS=$?
      set -e
      case "$DISALLOWED_STATUS" in
        0)
          printf '%s\n' "$DISALLOWED" >&2
          exit 1
          ;;
        1)
          exit 0
          ;;
        *)
          echo "formal PDF log check: grep could not classify intermediate diagnostics: $LOG" >&2
          exit 2
          ;;
      esac
    fi
    printf '%s\n' "$MATCHES" >&2
    exit 1
    ;;
  1)
    exit 0
    ;;
  *)
    echo "formal PDF log check: grep could not inspect LaTeX log: $LOG" >&2
    exit 2
    ;;
esac
