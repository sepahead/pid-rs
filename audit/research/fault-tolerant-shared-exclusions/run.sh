#!/usr/bin/env bash
# Reproduce the fault-tolerance research checks of 26 September 2026.
#
# Usage: run.sh <uci-data-dir> <fresh-work-dir> [--with-lean]
#
# <uci-data-dir> holds datatraining.txt, datatest.txt and datatest2.txt from UCI Occupancy
# Detection; the experiment scripts verify their SHA-256 values. <fresh-work-dir> must not exist
# and must lie outside the repository checkout; the script writes nothing inside the checkout.
# It runs the theory checks, the pid-rs down-set cross-check, all three experiment versions and, with
# --with-lean, the Lean compile and axiom receipt. Each output is compared byte for byte with the
# retained copy in results/; a difference is reported and makes the exit status nonzero.
set -euo pipefail

usage() {
  echo "usage: $0 <uci-data-dir> <fresh-work-dir> [--with-lean]" >&2
  exit 2
}
[[ $# -ge 2 && $# -le 3 ]] || usage
data="$1"
requested_work="$2"
with_lean="${3:-}"
[[ -z "$with_lean" || "$with_lean" == "--with-lean" ]] || usage
[[ -d "$data" ]] || { echo "run.sh: data directory is absent: $data" >&2; exit 2; }

here="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo="$(git -C "$here" rev-parse --show-toplevel)"
repo="$(CDPATH='' cd -- "$repo" && pwd -P)"
if [[ -e "$requested_work" ]]; then
  echo "run.sh: work directory must not exist: $requested_work" >&2
  exit 2
fi
parent="$(dirname -- "$requested_work")"
[[ -d "$parent" ]] || { echo "run.sh: parent directory is absent: $parent" >&2; exit 2; }
work="$(CDPATH='' cd -- "$parent" && pwd -P)/$(basename -- "$requested_work")"
case "$work/" in
  "$repo"/*) echo "run.sh: work directory must lie outside the checkout: $work" >&2; exit 2 ;;
esac
mkdir -p "$work"

dump="$repo/audit/evidence/cross-implementation-reverification-2026-09-26/inputs/discrete_dump.json"
python3 "$here/python/theory_checks.py" >"$work/theory_checks.txt"
python3 "$here/python/check_threshold_down_sets.py" "$dump" >"$work/check_threshold_down_sets.txt"
python3 "$here/python/fault_tolerant_experiment_v2.py" "$data" >"$work/experiment-v2.json"
python3 "$here/python/fault_tolerant_experiment_v1.py" "$data" >"$work/experiment-v1.json"
python3 "$here/python/fault_tolerant_experiment_v3.py" "$data" >"$work/experiment-v3.json"
names=(theory_checks.txt check_threshold_down_sets.txt experiment-v1.json experiment-v2.json
  experiment-v3.json)
if [[ "$with_lean" == "--with-lean" ]]; then
  python3 "$here/python/check_lean.py" "$repo" >"$work/lean-axioms.txt"
  names+=(lean-axioms.txt)
fi

status=0
for name in "${names[@]}"; do
  if cmp -s "$work/$name" "$here/results/$name"; then
    echo "same: $name"
  else
    echo "DIFFERENT: $name" >&2
    status=1
  fi
done
echo "outputs in $work"
exit "$status"
