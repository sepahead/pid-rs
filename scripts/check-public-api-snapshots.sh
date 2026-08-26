#!/usr/bin/env bash
# Rebuild every pid-core feature-profile API and compare it byte-for-byte with the frozen scope.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TOOLCHAIN="${PID_RS_PUBLIC_API_TOOLCHAIN:-nightly-2026-06-16}"
EXPECTED_RUSTC="rustc 1.98.0-nightly (01dfd7924 2026-06-15)"
EXPECTED_TOOL="cargo-public-api 0.52.0"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-public-api.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

if ! API_PYTHON_EXECUTABLE="$(type -P python3)" \
  || [[ "$API_PYTHON_EXECUTABLE" != /* || ! -f "$API_PYTHON_EXECUTABLE" \
    || ! -x "$API_PYTHON_EXECUTABLE" ]]
then
  echo "public API evidence requires an absolute executable python3 route" >&2
  exit 2
fi
API_PYTHON_EXECUTABLE="$(
  cd "$(dirname "$API_PYTHON_EXECUTABLE")"
  printf '%s/%s\n' "$(pwd -P)" "$(basename "$API_PYTHON_EXECUTABLE")"
)"
if ! "$API_PYTHON_EXECUTABLE" -I -S -B -c '
import sys
raise SystemExit(
    0
    if sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize == 0
    else 1
)
'; then
  echo "public API evidence requires Python 3.11+ -I -S -B without -O" >&2
  exit 2
fi
readonly API_PYTHON_EXECUTABLE

if ! API_RUSTUP_EXECUTABLE="$(type -P rustup)" \
  || [[ "$API_RUSTUP_EXECUTABLE" != /* || ! -f "$API_RUSTUP_EXECUTABLE" \
    || ! -x "$API_RUSTUP_EXECUTABLE" ]]
then
  echo "public API evidence requires an absolute executable rustup route" >&2
  exit 2
fi
API_RUSTUP_PROXY_DIR="$(
  cd "$(dirname "$API_RUSTUP_EXECUTABLE")"
  pwd -P
)"
API_RUSTUP_EXECUTABLE="$API_RUSTUP_PROXY_DIR/$(basename "$API_RUSTUP_EXECUTABLE")"
for executable_name in rustup cargo cargo-public-api; do
  executable_path="$API_RUSTUP_PROXY_DIR/$executable_name"
  if [[ ! -f "$executable_path" || ! -x "$executable_path" ]]; then
    echo "rustup proxy directory lacks executable $executable_name" >&2
    exit 2
  fi
done
API_TOOL_PATH="$API_RUSTUP_PROXY_DIR:${PATH:?PATH is required to locate the pinned tools}"
readonly API_RUSTUP_EXECUTABLE API_RUSTUP_PROXY_DIR API_TOOL_PATH

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
    "PATH=$API_TOOL_PATH" \
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
  command "$API_PYTHON_EXECUTABLE" -I -S -B "$@"
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

proxy_cargo_version="$("$API_RUSTUP_PROXY_DIR/cargo" "+$TOOLCHAIN" --version)"
rustup_cargo_version="$("$API_RUSTUP_EXECUTABLE" run "$TOOLCHAIN" cargo --version)"
if [[ "$proxy_cargo_version" != "$rustup_cargo_version" ]]; then
  echo "rustup Cargo proxy and pinned rustup-run Cargo versions disagree" >&2
  exit 1
fi

actual_rustc="$("$API_RUSTUP_EXECUTABLE" run "$TOOLCHAIN" rustc --version)"
if [[ "$actual_rustc" != "$EXPECTED_RUSTC" ]]; then
  echo "public API toolchain mismatch: expected '$EXPECTED_RUSTC', got '$actual_rustc'" >&2
  exit 1
fi

actual_tool="$(
  cd "$REPO_ROOT"
  run_public_api "$TMP/cargo-target-tool-version" \
    "$API_RUSTUP_EXECUTABLE" run "$TOOLCHAIN" cargo public-api --version
)"
if [[ "$actual_tool" != "$EXPECTED_TOOL" ]]; then
  echo "public API tool mismatch: expected '$EXPECTED_TOOL', got '$actual_tool'" >&2
  exit 1
fi

rustdoc_target="$(isolated_python - "$REPO_ROOT/release-scope-1.0.json" <<'PY'
import json
from pathlib import Path
import sys

print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["api_snapshot_source"]["rustdoc_target_triple"])
PY
)"
target_libdir="$("$API_RUSTUP_EXECUTABLE" run "$TOOLCHAIN" rustc --print target-libdir --target "$rustdoc_target")"
if [[ ! -d "$target_libdir" ]]; then
  echo "public API rustdoc target is not installed: $rustdoc_target" >&2
  exit 1
fi

isolated_python - "$REPO_ROOT/release-scope-1.0.json" >"$TMP/profiles.tsv" <<'PY'
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

isolated_python - "$REPO_ROOT/release-scope-1.0.json" <<'PY'
import json
from pathlib import Path
import sys

scope = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
profiles = scope["feature_profiles"]
by_id = {profile["id"]: profile for profile in profiles}
if len(profiles) != 10 or len({item["public_api_snapshot"] for item in profiles}) != 9:
    raise SystemExit("public API evidence requires ten logical profiles and nine physical snapshots")
all_features = by_id["pid-core-all-features"]
experimental_all = by_id["pid-core-experimental-all"]
if (
    not all_features["all_features"]
    or all_features["requested_features"]
    or all_features["generation_arguments"][-1:] != ["--all-features"]
    or experimental_all["all_features"]
    or experimental_all["requested_features"] != ["experimental-all"]
    or experimental_all["generation_arguments"][-2:]
    != ["--features", "experimental-all"]
):
    raise SystemExit("all-features and experimental-all activation semantics were conflated")
if (
    all_features["public_api_snapshot"] != experimental_all["public_api_snapshot"]
    or all_features["public_api_snapshot_sha256"]
    != experimental_all["public_api_snapshot_sha256"]
):
    raise SystemExit("the two activation routes no longer bind one shared exact snapshot")
PY

source_commit="$(isolated_python - "$REPO_ROOT/release-scope-1.0.json" <<'PY'
import json
from pathlib import Path
import sys

print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["api_snapshot_source"]["commit_sha"])
PY
)"
source_tree="$(isolated_python - "$REPO_ROOT/release-scope-1.0.json" <<'PY'
import json
from pathlib import Path
import sys

print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["api_snapshot_source"]["tree_sha"])
PY
)"
"$SCRIPT_DIR/materialize-public-api-source-v2.sh" \
  "$REPO_ROOT" "$source_commit" "$source_tree" "$TMP/snapshot-source" \
  "$API_PYTHON_EXECUTABLE"
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
      "$API_RUSTUP_EXECUTABLE" run "$TOOLCHAIN" cargo metadata --locked --format-version 1 >/dev/null
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
      "$API_RUSTUP_EXECUTABLE" run "$TOOLCHAIN" cargo public-api
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
  if ! cmp -s \
    "$TMP/$label-pid-core-all-features.txt" \
    "$TMP/$label-pid-core-experimental-all.txt"
  then
    echo "public API activation drift: --all-features differs from experimental-all ($label)" >&2
    diff -u \
      "$TMP/$label-pid-core-experimental-all.txt" \
      "$TMP/$label-pid-core-all-features.txt" | sed -n '1,240p' >&2 || true
    exit 1
  fi
  echo "OK: all-features and experimental-all are byte-identical but independently generated ($label)"
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
