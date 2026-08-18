#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
MODE="${1:---cross-toolchain}"
GATE="scripts/check-ksg-m1a-composite-v6-pdf-portability.sh"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

for command in bash chmod cp mkdir mktemp python3 rg; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "composite publication PDF v6 adjudication self-test: missing command: $command" >&2
    exit 2
  }
done

cd "$ROOT"
[[ -f "$GATE" && ! -L "$GATE" ]] || {
  echo "composite publication PDF v6 adjudication self-test: gate is absent or unsafe" >&2
  exit 1
}
bash -n "$GATE"

source_text="$(<"$GATE")"
required_source_literals=(
  'The publication relation is keyed, never Cartesian.'
  'report Form is not exact-bound to its committed TeX figure'
  'same-lane byte-different figure Cartesian pairing'
  'Cartesian report/figure pairing'
  '(PdfReader(BytesIO(clipped_bytes.getvalue()), strict=True), "clipping")'
  '(PdfReader(BytesIO(offpage_bytes.getvalue()), strict=True), "off-page")'
  '(matrix, "Form matrix")'
  '(resources, "Form resources")'
  '(action, "catalog action")'
  'fail(f"{label} hostile control was accepted")'
  "normalization-only \$mode visibility hostile was accepted"
  'byte-different report positive'
  'byte-different figure positive'
  '--max-mean-abs 0.20'
  '--max-changed-fraction 0.01'
  '--max-large-fraction 0.001'
  'bounded same-renderer'
)
for literal in "${required_source_literals[@]}"; do
  [[ "$source_text" == *"$literal"* ]] || {
    echo "composite publication PDF v6 adjudication self-test: gate lost policy literal: $literal" >&2
    exit 1
  }
done

# The live positive runs the actual object, text, geometry, font, color, gray,
# byte-different-equivalence, keyed-relation, and hostile controls.  Exact mode
# additionally replays both immutable exact publication gates.
"$GATE" "$MODE" >/dev/null

TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-publication-v6-self-test.XXXXXX")"
trap 'rm -rf -- "$TEST_ROOT"' EXIT

# A source-level mutation that revokes the keyed relation must be visible to the
# policy sentinel even if every PDF fixture on this host is exact.  The live gate
# above separately executes the wrong-lane report/figure pairing as a causal hostile.
mkdir -p "$TEST_ROOT/scripts"
cp "$GATE" "$TEST_ROOT/$GATE"
python3 -I -S - "$TEST_ROOT/$GATE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "The publication relation is keyed, never Cartesian."
new = "The publication relation may be Cartesian."
if text.count(old) != 1:
    raise SystemExit("self-test could not locate the keyed relation")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
PY
mutated="$(<"$TEST_ROOT/$GATE")"
if [[ "$mutated" != *'The publication relation may be Cartesian.'* ]]; then
  echo "composite publication PDF v6 adjudication self-test: relation mutation was not installed" >&2
  exit 1
fi
if [[ "$mutated" == "$source_text" ]]; then
  echo "composite publication PDF v6 adjudication self-test: relation mutation was inert" >&2
  exit 1
fi
if [[ "$mutated" == *'The publication relation is keyed, never Cartesian.'* ]]; then
  echo "composite publication PDF v6 adjudication self-test: policy sentinel accepted the relation mutation" >&2
  exit 1
fi

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: composite publication PDF v6 exact/cross semantics, positive serialization fixtures, five object hostiles, normalization-only raster hostile, and anti-Cartesian sentinel passed"
else
  echo "OK: composite publication PDF v6 cross semantics, positive serialization fixtures, five object hostiles, normalization-only raster hostile, and anti-Cartesian sentinel passed"
fi
