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

run_public_api() (
  local target_dir="$1"
  shift
  command env -i \
    "ALL_PROXY=${ALL_PROXY-}" \
    "CARGO_HOME=$TMP/cargo-home" \
    "CARGO_TARGET_DIR=$target_dir" \
    "HOME=${HOME:?HOME is required to locate rustup toolchains}" \
    "HTTPS_PROXY=${HTTPS_PROXY-}" \
    "HTTP_PROXY=${HTTP_PROXY-}" \
    "LANG=C" \
    "LC_ALL=C" \
    "NO_PROXY=${NO_PROXY-}" \
    "PATH=${PATH:?PATH is required to locate the pinned tools}" \
    "RUSTUP_HOME=${RUSTUP_HOME:-$HOME/.rustup}" \
    "TMPDIR=$TMP" \
    "TZ=UTC" \
    "all_proxy=${all_proxy-}" \
    "http_proxy=${http_proxy-}" \
    "https_proxy=${https_proxy-}" \
    "no_proxy=${no_proxy-}" \
    "$@"
)

isolated_python() (
  local variable
  while IFS= read -r variable; do
    unset "$variable"
  done < <(compgen -A variable PYTHON || true)
  export PYTHONNOUSERSITE=1
  command python3 "$@"
)

reject_ancestor_cargo_configs() {
  local current
  local cargo_config
  current="$(cd "$1" && pwd -P)"
  while true; do
    for cargo_config in "$current/.cargo/config" "$current/.cargo/config.toml"; do
      if [[ -e "$cargo_config" || -L "$cargo_config" ]]; then
        echo "public API evidence rejects Cargo config in source ancestry: $cargo_config" >&2
        exit 1
      fi
    done
    if [[ "$current" == "/" ]]; then
      break
    fi
    current="$(dirname "$current")"
  done
}

# Validate the source identity, profile paths, feature closure, and canonical scope before using
# any of its values in shell commands.
isolated_python "$SCRIPT_DIR/check-release-scope.py" --print-markdown >/dev/null
reject_ancestor_cargo_configs "$REPO_ROOT"
mkdir "$TMP/cargo-home"

actual_rustc="$(rustup run "$TOOLCHAIN" rustc --version)"
if [[ "$actual_rustc" != "$EXPECTED_RUSTC" ]]; then
  echo "public API toolchain mismatch: expected '$EXPECTED_RUSTC', got '$actual_rustc'" >&2
  exit 1
fi

actual_tool="$(
  cd "$REPO_ROOT"
  run_public_api "$TMP/cargo-target-tool-version" \
    cargo "+$TOOLCHAIN" public-api --version
)"
if [[ "$actual_tool" != "$EXPECTED_TOOL" ]]; then
  echo "public API tool mismatch: expected '$EXPECTED_TOOL', got '$actual_tool'" >&2
  exit 1
fi

rustdoc_target="$(isolated_python -I - "$REPO_ROOT/release-scope-1.0.json" <<'PY'
import json
from pathlib import Path
import sys

print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["api_snapshot_source"]["rustdoc_target_triple"])
PY
)"
target_libdir="$(rustup run "$TOOLCHAIN" rustc --print target-libdir --target "$rustdoc_target")"
if [[ ! -d "$target_libdir" ]]; then
  echo "public API rustdoc target is not installed: $rustdoc_target" >&2
  exit 1
fi

isolated_python -I - "$REPO_ROOT/release-scope-1.0.json" >"$TMP/profiles.tsv" <<'PY'
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

source_commit="$(isolated_python -I - "$REPO_ROOT/release-scope-1.0.json" <<'PY'
import json
from pathlib import Path
import sys

print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["api_snapshot_source"]["commit_sha"])
PY
)"
source_tree="$(isolated_python -I - "$REPO_ROOT/release-scope-1.0.json" <<'PY'
import json
from pathlib import Path
import sys

print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["api_snapshot_source"]["tree_sha"])
PY
)"
"$SCRIPT_DIR/materialize-public-api-source.sh" \
  "$REPO_ROOT" "$source_commit" "$source_tree" "$TMP/snapshot-source"
reject_ancestor_cargo_configs "$TMP/snapshot-source"

prepare_tree() {
  local tree_root="$1"
  local label="$2"
  local lock_snapshot="$TMP/$label-Cargo.lock"
  local lock_path="$tree_root/Cargo.lock"
  reject_ancestor_cargo_configs "$tree_root"
  if [[ ! -f "$lock_path" || -L "$lock_path" ]]; then
    echo "public API evidence requires a regular Cargo.lock: $lock_path" >&2
    exit 1
  fi
  cp "$lock_path" "$lock_snapshot"
  (
    cd "$tree_root"
    run_public_api "$TMP/cargo-target-$label-lock-preflight" \
      cargo "+$TOOLCHAIN" metadata --locked --format-version 1 >/dev/null
  )
  if ! cmp -s "$lock_snapshot" "$lock_path"; then
    echo "public API evidence observed Cargo.lock mutation during locked preflight: $label" >&2
    exit 1
  fi
}

check_tree() {
  local tree_root="$1"
  local label="$2"
  local lock_snapshot="$TMP/$label-Cargo.lock"
  local lock_path="$tree_root/Cargo.lock"
  while IFS=$'\t' read -r profile all_features features relative_snapshot; do
    local generated="$TMP/$label-$profile.txt"
    local committed="$REPO_ROOT/$relative_snapshot"
    local command=(
      cargo "+$TOOLCHAIN" public-api
      --package pid-core
      --no-default-features
      --target "$rustdoc_target"
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
      run_public_api "$TMP/cargo-target-$label-$profile" "${command[@]}"
    ) >"$generated"
    if ! cmp -s "$lock_snapshot" "$lock_path"; then
      echo "public API evidence observed Cargo.lock mutation: $profile ($label)" >&2
      exit 1
    fi
    if ! cmp -s "$committed" "$generated"; then
      echo "public API snapshot drift: $profile ($label)" >&2
      diff -u "$committed" "$generated" | sed -n '1,240p' >&2 || true
      exit 1
    fi
    echo "OK: $profile ($label)"
  done <"$TMP/profiles.tsv"
}

# Reject configuration and dependency-resolution problems for both inputs before any expensive
# declaration build. The checkout under review is checked first so local drift fails immediately.
prepare_tree "$REPO_ROOT" "working-tree"
prepare_tree "$TMP/snapshot-source" "snapshot-source"

# The first pass proves that the committed signatures really came from the exact historical
# source recorded in the machine scope. The second independently rejects drift in the checkout
# under review.
check_tree "$TMP/snapshot-source" "snapshot-source"
check_tree "$REPO_ROOT" "working-tree"
