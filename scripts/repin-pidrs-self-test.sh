#!/usr/bin/env bash
# Failure-injection tests for the downstream pid-rs submodule repin helper.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPIN="$SCRIPT_DIR/repin-pidrs.sh"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-repin.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
REAL_GIT="$(command -v git)"

git init -q -b main "$TMP/pid-origin"
git -C "$TMP/pid-origin" config user.name "Repin Self Test"
git -C "$TMP/pid-origin" config user.email "repin-self-test.invalid"
printf '[workspace]\n[workspace.package]\nversion = "0.8.0"\n' \
  >"$TMP/pid-origin/Cargo.toml"
git -C "$TMP/pid-origin" add Cargo.toml
git -C "$TMP/pid-origin" commit -qm v0.8.0
BASE_SHA="$(git -C "$TMP/pid-origin" rev-parse HEAD)"
sed -i.bak 's/0\.8\.0/0.9.0/' "$TMP/pid-origin/Cargo.toml"
rm "$TMP/pid-origin/Cargo.toml.bak"
git -C "$TMP/pid-origin" add Cargo.toml
git -C "$TMP/pid-origin" commit -qm v0.9.0
git -C "$TMP/pid-origin" tag -a v0.9.0 -m v0.9.0
TARGET_SHA="$(git -C "$TMP/pid-origin" rev-parse 'v0.9.0^{commit}')"
git -C "$TMP/pid-origin" tag -a v0.9.1 -m mismatched-version
git -C "$TMP/pid-origin" tag v0.9.2
TAG_OBJECT="$(git -C "$TMP/pid-origin" rev-parse 'v0.9.0^{tag}')"
NESTED_TAG_OBJECT="$(
  printf 'object %s\ntype tag\ntag v0.9.3\ntagger Repin Self Test <repin-self-test.invalid> 0 +0000\n\nindirect\n' \
    "$TAG_OBJECT" | git -C "$TMP/pid-origin" hash-object -t tag -w --stdin
)"
git -C "$TMP/pid-origin" update-ref refs/tags/v0.9.3 "$NESTED_TAG_OBJECT"
MISNAMED_TAG_OBJECT="$(
  printf 'object %s\ntype commit\ntag v0.9.99\ntagger Repin Self Test <repin-self-test.invalid> 0 +0000\n\nmisnamed\n' \
    "$TARGET_SHA" | git -C "$TMP/pid-origin" hash-object -t tag -w --stdin
)"
git -C "$TMP/pid-origin" update-ref refs/tags/v0.9.4 "$MISNAMED_TAG_OBJECT"
SIGNED_TAG_OBJECT="$(
  printf 'object %s\ntype commit\ntag v0.9.5\ntagger Repin Self Test <repin-self-test.invalid> 0 +0000\n\nsigned\n-----BEGIN PGP SIGNATURE-----\nnot-a-real-signature\n-----END PGP SIGNATURE-----\n' \
    "$TARGET_SHA" | git -C "$TMP/pid-origin" hash-object -t tag -w --stdin
)"
git -C "$TMP/pid-origin" update-ref refs/tags/v0.9.5 "$SIGNED_TAG_OBJECT"

make_prisoma() {
  local name="$1"
  local committed_url="${2:-https://github.com/sepahead/pid-rs.git}"
  local root="$TMP/$name"
  git init -q -b main "$root"
  git -C "$root" config user.name "Repin Self Test"
  git -C "$root" config user.email "repin-self-test.invalid"
  printf '[workspace]\nresolver = "2"\n' >"$root/Cargo.toml"
  : >"$root/Cargo.lock"
  git -C "$root" -c protocol.file.allow=always submodule add -q \
    "$TMP/pid-origin" pid-rs
  git -C "$root/pid-rs" checkout -q "$BASE_SHA"
  git -C "$root" config -f .gitmodules submodule.pid-rs.url "$committed_url"
  git -C "$root/pid-rs" remote set-url origin \
    https://github.com/sepahead/pid-rs.git
  git -C "$root" add Cargo.toml Cargo.lock .gitmodules pid-rs
  git -C "$root" commit -qm initial
}

mkdir -p "$TMP/bin"
cat >"$TMP/bin/git" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
args=("$@")
transport=false
for arg in "${args[@]}"; do
  if [[ "$arg" == ls-remote || "$arg" == fetch ]]; then transport=true; fi
done
if [[ "$transport" == true ]]; then
  for index in "${!args[@]}"; do
    if [[ "${args[$index]}" == origin ]]; then
      args[$index]="$PIDRS_TEST_ORIGIN"
    fi
  done
fi
exec "$REAL_GIT" "${args[@]}"
EOF
cat >"$TMP/bin/cargo" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
[[ "${1:-}" == update || "${1:-}" == check ]]
if [[ "${REPIN_TEST_STALE_LOCK:-}" == 1 ]]; then
  exit 0
fi
args=("$@")
manifest=""
for index in "${!args[@]}"; do
  if [[ "${args[$index]}" == --manifest-path ]]; then
    next=$((index + 1))
    manifest="${args[$next]}"
  fi
done
[[ -n "$manifest" ]]
root="$(cd "$(dirname "$manifest")" && pwd)"
version="$(awk '
  /^\[workspace\.package\]$/ { in_section=1; next }
  /^\[/ { in_section=0 }
  in_section && /^version = "/ {
    line=$0
    sub(/^[^"]*"/, "", line)
    sub(/".*/, "", line)
    print line
    exit
  }
' "$root/pid-rs/Cargo.toml")"
printf 'version = 4\n\n[[package]]\nname = "pid-core"\nversion = "%s"\n\n[[package]]\nname = "pid-runlog"\nversion = "%s"\n' \
  "$version" "$version" >"$root/Cargo.lock"
EOF
chmod +x "$TMP/bin/git" "$TMP/bin/cargo"
export REAL_GIT PIDRS_TEST_ORIGIN="$TMP/pid-origin" PATH="$TMP/bin:$PATH"

expect_failure() {
  local label="$1"
  shift
  if "$@" >"$TMP/output.log" 2>&1; then
    echo "ERROR: $label unexpectedly passed" >&2
    exit 1
  fi
}

make_prisoma happy
"$REPIN" v0.9.0 "$TMP/happy" >/dev/null
[[ "$(git -C "$TMP/happy/pid-rs" rev-parse HEAD)" == "$TARGET_SHA" ]]
[[ "$(git -C "$TMP/happy" ls-files -s pid-rs | awk '{ print $2 }')" == "$TARGET_SHA" ]]
if git -C "$TMP/happy/pid-rs" show-ref --verify --quiet refs/pid-rs-repin/v0.9.0; then
  echo "ERROR: temporary repin ref survived successful cleanup" >&2
  exit 1
fi

make_prisoma rewritten
git -C "$TMP/rewritten/pid-rs" config \
  "url.file://$TMP/pid-origin.insteadOf" \
  https://github.com/sepahead/pid-rs.git
expect_failure "url.*.insteadOf substitution" \
  "$REPIN" v0.9.0 "$TMP/rewritten"
grep -F "resolved origin:" "$TMP/output.log" >/dev/null

make_prisoma dirty-gitmodules
printf '\n# local edit\n' >>"$TMP/dirty-gitmodules/.gitmodules"
expect_failure "dirty .gitmodules" \
  "$REPIN" v0.9.0 "$TMP/dirty-gitmodules"

make_prisoma bad-head https://example.invalid/substituted.git
git -C "$TMP/bad-head" config -f .gitmodules submodule.pid-rs.url \
  https://github.com/sepahead/pid-rs.git
expect_failure "noncanonical committed .gitmodules" \
  "$REPIN" v0.9.0 "$TMP/bad-head"
grep -F "HEAD:.gitmodules" "$TMP/output.log" >/dev/null

make_prisoma wrong-version
expect_failure "tag/workspace version mismatch" \
  "$REPIN" v0.9.1 "$TMP/wrong-version"
grep -F "points to workspace version '0.9.0'" "$TMP/output.log" >/dev/null
[[ "$(git -C "$TMP/wrong-version/pid-rs" rev-parse HEAD)" == "$BASE_SHA" ]]

make_prisoma lightweight
expect_failure "lightweight release tag" \
  "$REPIN" v0.9.2 "$TMP/lightweight"
grep -F "does not expose one annotated tag" "$TMP/output.log" >/dev/null

make_prisoma nested
expect_failure "indirect annotated release tag" \
  "$REPIN" v0.9.3 "$TMP/nested"
grep -F "is not a direct annotated tag" "$TMP/output.log" >/dev/null

make_prisoma misnamed
expect_failure "mismatched internal tag name" \
  "$REPIN" v0.9.4 "$TMP/misnamed"
grep -F "is not a direct annotated tag" "$TMP/output.log" >/dev/null

make_prisoma signed
expect_failure "signed annotated release tag" \
  "$REPIN" v0.9.5 "$TMP/signed"
grep -F "release tags must be annotated and unsigned" "$TMP/output.log" >/dev/null

make_prisoma stale-lock
expect_failure "successful cargo command leaves stale lock" \
  env REPIN_TEST_STALE_LOCK=1 "$REPIN" v0.9.0 "$TMP/stale-lock"
grep -F "Cargo.lock must contain exactly one pid-core 0.9.0 entry" \
  "$TMP/output.log" >/dev/null

echo "OK: repin canonical-remote, clean-state, direct-tag, version, and lock failure injections passed"
