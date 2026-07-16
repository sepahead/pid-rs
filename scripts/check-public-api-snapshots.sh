#!/usr/bin/env bash
# Rebuild every pid-core feature-profile API and compare it byte-for-byte with the frozen scope.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TOOLCHAIN="${PID_RS_PUBLIC_API_TOOLCHAIN:-nightly}"
EXPECTED_RUSTC="rustc 1.98.0-nightly (01dfd7924 2026-06-15)"
EXPECTED_TOOL="cargo-public-api 0.52.0"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-public-api.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

# Validate the source identity, profile paths, feature closure, and canonical scope before using
# any of its values in shell commands.
python3 "$SCRIPT_DIR/check-release-scope.py" --print-markdown >/dev/null

actual_rustc="$(rustup run "$TOOLCHAIN" rustc --version)"
if [[ "$actual_rustc" != "$EXPECTED_RUSTC" ]]; then
  echo "public API toolchain mismatch: expected '$EXPECTED_RUSTC', got '$actual_rustc'" >&2
  exit 1
fi

actual_tool="$(cargo "+$TOOLCHAIN" public-api --version)"
if [[ "$actual_tool" != "$EXPECTED_TOOL" ]]; then
  echo "public API tool mismatch: expected '$EXPECTED_TOOL', got '$actual_tool'" >&2
  exit 1
fi

python3 - "$REPO_ROOT/release-scope-1.0.json" >"$TMP/profiles.tsv" <<'PY'
import json
from pathlib import Path
import sys

scope = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for profile in scope["feature_profiles"]:
    print(
        profile["id"],
        "1" if profile["all_features"] else "0",
        ",".join(profile["requested_features"]) or "-",
        profile["public_api_snapshot"],
        sep="\t",
    )
PY

source_commit="$(python3 - "$REPO_ROOT/release-scope-1.0.json" <<'PY'
import json
from pathlib import Path
import sys

print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["api_snapshot_source"]["commit_sha"])
PY
)"
mkdir "$TMP/snapshot-source"
git -C "$REPO_ROOT" archive "$source_commit" | tar -xf - -C "$TMP/snapshot-source"

check_tree() {
  local tree_root="$1"
  local label="$2"
  while IFS=$'\t' read -r profile all_features features relative_snapshot; do
    local generated="$TMP/$label-$profile.txt"
    local committed="$REPO_ROOT/$relative_snapshot"
    local command=(
      cargo "+$TOOLCHAIN" public-api
      --package pid-core
      --no-default-features
      -sss
      --color never
    )
    if [[ "$all_features" == "1" ]]; then
      command+=(--all-features)
    elif [[ "$features" != "-" ]]; then
      command+=(--features "$features")
    fi
    (
      cd "$tree_root"
      # Isolate every source tree and feature profile. cargo-public-api consumes/removes rustdoc
      # JSON, and Cargo fingerprints are not an evidence boundary between same-version source
      # trees; sharing a target can therefore mask or fabricate a snapshot comparison.
      CARGO_TARGET_DIR="$TMP/cargo-target-$label-$profile" "${command[@]}"
    ) >"$generated"
    if ! cmp -s "$committed" "$generated"; then
      echo "public API snapshot drift: $profile ($label)" >&2
      diff -u "$committed" "$generated" | sed -n '1,240p' >&2 || true
      exit 1
    fi
    echo "OK: $profile ($label)"
  done <"$TMP/profiles.tsv"
}

# The first pass proves that the committed signatures really came from the exact historical
# source recorded in the machine scope. The second independently rejects drift in the checkout
# under review.
check_tree "$TMP/snapshot-source" "snapshot-source"
check_tree "$REPO_ROOT" "working-tree"
