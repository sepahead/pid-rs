#!/usr/bin/env bash
# Mutation test: a public method added without touching lib.rs must change the compiled snapshot.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TOOLCHAIN="${PID_RS_PUBLIC_API_TOOLCHAIN:-nightly}"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-public-api-mutation.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

# Prevent a false-positive self-test caused by unrelated baseline drift.
"$SCRIPT_DIR/check-public-api-snapshots.sh"

mkdir "$TMP/repo"
tar --exclude './.git' --exclude './target' -cf - -C "$REPO_ROOT" . \
  | tar -xf - -C "$TMP/repo"
python3 - "$TMP/repo/crates/pid-core/src/report.rs" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
needle = "pub enum InformationUnit {\n    Nats,\n}\n"
addition = needle + "\nimpl InformationUnit {\n    pub fn unscoped_release_method(&self) {}\n}\n"
if source.count(needle) != 1:
    raise SystemExit("compiled API injection point changed")
path.write_text(source.replace(needle, addition), encoding="utf-8")
PY

generated="$TMP/mutated-api.txt"
(
  cd "$TMP/repo"
  CARGO_TARGET_DIR="$TMP/cargo-target" \
    cargo "+$TOOLCHAIN" public-api -p pid-core --no-default-features \
      -sss --color never >"$generated"
)

committed="$REPO_ROOT/audit/api/public-api/pid-core-default.txt"
if cmp -s "$committed" "$generated"; then
  echo "compiled public method mutation did not change the API snapshot" >&2
  exit 1
fi
if ! grep -F \
  "pub fn pid_core::stable::continuous::InformationUnit::unscoped_release_method(&self)" \
  "$generated" >/dev/null
then
  echo "compiled mutation changed the snapshot for an unexpected reason" >&2
  exit 1
fi

echo "OK: compiled public method mutation changed the frozen API snapshot"
