#!/usr/bin/env bash
# Reproduce the cross-implementation re-verification checks of 26 September 2026.
#
# Usage: run.sh <commit> <fresh-work-dir> [--with-test-suite]
#
# The script exports <commit> with `git archive` into <fresh-work-dir>/src, copies the two
# evidence generators into that export only, and runs them with a private Cargo target
# directory. It then runs the Python checks, the checker self-test, the SMT obligation check
# (which needs Z3 4.16.0 on PATH) and the archived binary64 diagnostic. <fresh-work-dir> must not exist and must lie outside the repository checkout; the
# script writes nothing inside the checkout. Outputs go to <fresh-work-dir>/out. Each output is
# compared byte for byte with the retained copy in this evidence directory; a difference is
# reported and makes the exit status nonzero.
set -euo pipefail

usage() {
  echo "usage: $0 <commit> <fresh-work-dir> [--with-test-suite]" >&2
  exit 2
}
[[ $# -ge 2 && $# -le 3 ]] || usage
commit="$1"
requested_work="$2"
with_tests="${3:-}"
[[ -z "$with_tests" || "$with_tests" == "--with-test-suite" ]] || usage

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
full_commit="$(git -C "$repo" rev-parse --verify "$commit^{commit}")"

mkdir -p "$work/src" "$work/out"
export CARGO_TARGET_DIR="$work/target"
timing="$work/out/timing.txt"
start_all="$(date +%s)"
stamp() {
  printf '%s %s s\n' "$1" "$(( $(date +%s) - $2 ))" >>"$timing"
}
printf 'commit %s\n' "$full_commit" >"$timing"

git -C "$repo" archive "$full_commit" | tar -x -C "$work/src"
cp "$here/rust/audit_dump_discrete.rs" "$here/rust/audit_dump_continuous.rs" \
  "$work/src/crates/pid-core/examples/"

step="$(date +%s)"
(
  cd "$work/src"
  cargo run --locked --release -q -p pid-core --example audit_dump_discrete \
    >"$work/out/discrete_dump.json"
  cargo run --locked --release -q -p pid-core --all-features --example audit_dump_continuous \
    >"$work/out/continuous_dump.json"
)
stamp "build-and-generate" "$step"

step="$(date +%s)"
python3 "$here/python/check_discrete.py" "$work/out/discrete_dump.json" \
  >"$work/out/check_discrete.txt"
stamp "check_discrete" "$step"
step="$(date +%s)"
python3 "$here/python/check_continuous.py" "$work/out/continuous_dump.json" \
  >"$work/out/check_continuous.txt"
stamp "check_continuous" "$step"
step="$(date +%s)"
python3 "$here/python/check_one_lambda.py" >"$work/out/check_one_lambda.txt"
stamp "check_one_lambda" "$step"
step="$(date +%s)"
python3 "$here/python/check_percentile_index.py" >"$work/out/check_percentile_index.txt"
stamp "check_percentile_index" "$step"
step="$(date +%s)"
python3 "$here/python/checker_self_test.py" "$work/out/discrete_dump.json" \
  "$work/out/continuous_dump.json" >"$work/out/checker_self_test.txt"
stamp "checker_self_test" "$step"
step="$(date +%s)"
python3 "$here/python/check_smt_obligations.py" "$work/src" >"$work/out/check_smt_obligations.txt"
stamp "check_smt_obligations" "$step"
step="$(date +%s)"
python3 "$here/python/archive/diagnose_one_lambda_binary64_v1.py" \
  >"$work/out/diagnose_one_lambda_binary64_v1.txt"
stamp "diagnose_one_lambda_binary64_v1" "$step"

if [[ "$with_tests" == "--with-test-suite" ]]; then
  step="$(date +%s)"
  (
    cd "$work/src"
    cargo test --locked --release -p pid-core --all-features >"$work/out/test_suite.raw.log" 2>&1
  )
  # Replace the machine-specific work path so the log can be retained.
  sed "s#$work#<work>#g" "$work/out/test_suite.raw.log" >"$work/out/test_suite.log"
  rm -f -- "$work/out/test_suite.raw.log"
  grep -E '^test result:' "$work/out/test_suite.log" \
    | awk '{p += $4; f += $6; i += $8} END {printf "passed=%d failed=%d ignored=%d\n", p, f, i}' \
    >"$work/out/test_suite_summary.txt"
  stamp "test-suite" "$step"
fi
stamp "total" "$start_all"

# Compare the deterministic outputs with the retained copies.
status=0
compare() {
  if cmp -s "$1" "$2"; then
    echo "same: $(basename -- "$1")"
  else
    echo "DIFFERENT: $(basename -- "$1") versus ${2#"$here"/}" >&2
    status=1
  fi
}
compare "$work/out/discrete_dump.json" "$here/inputs/discrete_dump.json"
compare "$work/out/continuous_dump.json" "$here/inputs/continuous_dump.json"
for name in check_discrete check_continuous check_one_lambda check_percentile_index \
    checker_self_test check_smt_obligations; do
  compare "$work/out/$name.txt" "$here/results/$name.txt"
done
compare "$work/out/diagnose_one_lambda_binary64_v1.txt" \
  "$here/results/archive/diagnose_one_lambda_binary64_v1.txt"

(cd "$work/out" && shasum -a 256 ./*.json ./*.txt) >"$work/out/SHA256SUMS"
echo "outputs in $work/out"
exit "$status"
