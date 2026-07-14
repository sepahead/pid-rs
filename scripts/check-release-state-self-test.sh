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
version="$(awk '
  /^\[workspace\.package\]$/ { in_section=1; next }
  /^\[/ { in_section=0 }
  in_section && /^version = / {
    line=$0
    sub(/^[^"]*"/, "", line)
    sub(/".*/, "", line)
    print line
    exit
  }
' "$TMP/Cargo.toml")"

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

sed -i.bak "s/## \[$version\] - Unreleased/## [$version] - 2026-07-14/" "$TMP/CHANGELOG.md"
sed -i.bak \
  "s#\[$version\]: https://github.com/sepahead/pid-rs/compare/v0.4.0...HEAD#[$version]: https://github.com/sepahead/pid-rs/compare/v0.4.0...v$version#" \
  "$TMP/CHANGELOG.md"
sed -i.bak '/Release status: CANDIDATE — not yet published\./d' "$TMP/README.md"
sed -i.bak 's/## Forthcoming registry installation (not yet available)/## Installation/' "$TMP/README.md"
sed -i.bak '/Release status: \*\*DRAFT — not yet published\*\*\./d' "$TMP/RELEASE_NOTES.md"
printf '\ndate-released: "2026-07-14"\n' >>"$TMP/CITATION.cff"
rm -f "$TMP"/*.bak
git -C "$TMP" add .
git -C "$TMP" commit -qm finalized-metadata

# An extracted release archive has no Git metadata. Final-source mode must nevertheless validate
# the exact finalized files and encoded release version.
mv "$TMP/.git" "$TMP/.git.saved"
"$TMP/scripts/check-release-state.sh" final-source "v$version" >/dev/null
mv "$TMP/.git.saved" "$TMP/.git"

git -C "$TMP" tag -a "v$version" -m "v$version"
"$TMP/scripts/check-release-state.sh" tagged "v$version" >/dev/null

# Inject one date mismatch into the otherwise valid final state. Both the archive and annotated-tag
# paths must reject that same isolated metadata defect.
sed -i.bak 's/date-released: "2026-07-14"/date-released: "2026-07-13"/' "$TMP/CITATION.cff"
rm "$TMP/CITATION.cff.bak"
expect_failure "final-source CFF/changelog date mismatch" \
  "$TMP/scripts/check-release-state.sh" final-source "v$version"
grep --fixed-strings "final-source CFF date '2026-07-13' != CHANGELOG date '2026-07-14'" \
  "$TMP/output.log" >/dev/null

git -C "$TMP" tag -d "v$version" >/dev/null
git -C "$TMP" add CITATION.cff
git -C "$TMP" commit -qm mismatched-tagged-metadata
git -C "$TMP" tag -a "v$version" -m "v$version"
expect_failure "tagged CFF/changelog date mismatch" \
  "$TMP/scripts/check-release-state.sh" tagged "v$version"
grep --fixed-strings "tagged CFF date '2026-07-13' != CHANGELOG date '2026-07-14'" \
  "$TMP/output.log" >/dev/null

echo "OK: candidate, final-source, and tagged states passed; failure injections were rejected"
