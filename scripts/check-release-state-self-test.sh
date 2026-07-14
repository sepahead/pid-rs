#!/usr/bin/env bash
# Failure-injection tests for check-release-state.sh. All mutations occur in a temporary Git repo.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-release-state.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/scripts"
cp "$SCRIPT_DIR/check-release-state.sh" "$TMP/scripts/"
cp "$REPO_ROOT/Cargo.toml" "$REPO_ROOT/CITATION.cff" "$REPO_ROOT/CHANGELOG.md" \
  "$REPO_ROOT/README.md" "$REPO_ROOT/RELEASE_NOTES.md" "$TMP/"

git -C "$TMP" init -q
git -C "$TMP" config user.name "Release State Self-Test"
git -C "$TMP" config user.email "release-state-self-test.invalid"
git -C "$TMP" add .
git -C "$TMP" commit -qm candidate

expect_failure() {
  local label="$1"
  shift
  if "$@" >"$TMP/output.log" 2>&1; then
    echo "ERROR: $label unexpectedly passed" >&2
    return 1
  fi
}

"$TMP/scripts/check-release-state.sh" candidate >/dev/null

printf '\ndate-released: "2026-07-14"\n' >>"$TMP/CITATION.cff"
expect_failure "candidate date-released injection" \
  "$TMP/scripts/check-release-state.sh" candidate
sed -i.bak '/^date-released:/d' "$TMP/CITATION.cff"
rm "$TMP/CITATION.cff.bak"

printf '\nThe stable libraries are distributed through crates.io.\n' >>"$TMP/README.md"
expect_failure "candidate present-tense registry claim" \
  "$TMP/scripts/check-release-state.sh" candidate
sed -i.bak '/are distributed through crates.io/d' "$TMP/README.md"
rm "$TMP/README.md.bak"

sed -i.bak 's/## \[1.0.0\] - Unreleased/## [1.0.0] - 2026-07-14/' "$TMP/CHANGELOG.md"
sed -i.bak '/Release status: CANDIDATE — not yet published\./d' "$TMP/README.md"
sed -i.bak 's/## Forthcoming registry installation (not yet available)/## Installation/' "$TMP/README.md"
sed -i.bak '/Release status: \*\*DRAFT — not yet published\*\*\./d' "$TMP/RELEASE_NOTES.md"
printf '\ndate-released: "2026-07-13"\n' >>"$TMP/CITATION.cff"
rm -f "$TMP"/*.bak
git -C "$TMP" add .
git -C "$TMP" commit -qm mismatched-tagged-metadata
git -C "$TMP" tag -a v1.0.0 -m v1.0.0
expect_failure "tagged CFF/changelog date mismatch" \
  "$TMP/scripts/check-release-state.sh" tagged v1.0.0

echo "OK: release-state failure injections were rejected"
