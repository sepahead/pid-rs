#!/usr/bin/env bash
# Failure-injection tests for release-state and version-coherence checks. Every mutation occurs in
# a temporary repository populated from the current non-ignored working-tree files.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-release-state.XXXXXX")"
EXTERNAL_TMP="$TMP.external"
mkdir -p "$EXTERNAL_TMP" "$TMP/fixture-home"
trap 'rm -rf "$TMP" "$EXTERNAL_TMP"' EXIT

isolated_git() (
  local root="$1"
  shift
  command env -i \
    "GIT_ATTR_NOSYSTEM=1" \
    "GIT_CONFIG_GLOBAL=/dev/null" \
    "GIT_CONFIG_NOSYSTEM=1" \
    "GIT_CONFIG_SYSTEM=/dev/null" \
    "GIT_GRAFT_FILE=/dev/null" \
    "GIT_LITERAL_PATHSPECS=1" \
    "GIT_NO_LAZY_FETCH=1" \
    "GIT_NO_REPLACE_OBJECTS=1" \
    "GIT_OPTIONAL_LOCKS=0" \
    "GIT_TERMINAL_PROMPT=0" \
    "HOME=$TMP/fixture-home" \
    "LANG=C" \
    "LC_ALL=C" \
    "PATH=${PATH:?PATH is required to locate Git}" \
    "TMPDIR=$EXTERNAL_TMP" \
    git \
      -c advice.graftFileDeprecated=false \
      -c commit.gpgsign=false \
      -c core.attributesFile=/dev/null \
      -c core.fsmonitor=false \
      -c core.hooksPath=/dev/null \
      -c core.untrackedCache=false \
      -c tag.gpgsign=false \
      -C "$root" "$@"
)

fixture_git() {
  isolated_git "$TMP" "$@"
}

create_tracked_source_fixture() {
  local phase="$1"
  local destination="$2"
  local archive="$EXTERNAL_TMP/$phase.tar"

  if [[ -e "$destination" || -L "$destination" ]]; then
    echo "ERROR: $phase source-fixture destination already exists: $destination" >&2
    return 1
  fi
  mkdir -p "$destination"
  if ! fixture_git archive --format=tar HEAD >"$archive"; then
    echo "ERROR: $phase could not serialize the committed fixture tree" >&2
    return 1
  fi
  if ! tar -xf "$archive" -C "$destination"; then
    echo "ERROR: $phase could not extract the committed fixture tree" >&2
    return 1
  fi
  if [[ -e "$destination/.git" || -L "$destination/.git" ]]; then
    echo "ERROR: $phase extracted source fixture unexpectedly contains .git metadata" >&2
    return 1
  fi
}

while IFS= read -r -d '' path; do
  if [[ ! -e "$REPO_ROOT/$path" && ! -L "$REPO_ROOT/$path" ]]; then
    continue
  fi
  mkdir -p "$(dirname "$TMP/$path")"
  cp -pP "$REPO_ROOT/$path" "$TMP/$path"
done < <(isolated_git "$REPO_ROOT" ls-files -z --cached --others --exclude-standard)

# This workflow can be untracked while its introduction and these checks are tested together.
if [[ -f "$REPO_ROOT/.github/workflows/review-release.yml" \
  && ! -f "$TMP/.github/workflows/review-release.yml" ]]; then
  mkdir -p "$TMP/.github/workflows"
  cp -p "$REPO_ROOT/.github/workflows/review-release.yml" \
    "$TMP/.github/workflows/review-release.yml"
fi
if [[ -f "$REPO_ROOT/scripts/check-current-release-state.sh" \
  && ! -f "$TMP/scripts/check-current-release-state.sh" ]]; then
  cp -p "$REPO_ROOT/scripts/check-current-release-state.sh" \
    "$TMP/scripts/check-current-release-state.sh"
fi

# Once the repository reaches review-source state, reconstruct the immediately preceding candidate
# metadata in the temporary tree. This keeps the state-machine test repeatable before and after the
# one-way public metadata transition without depending on Git history.
if grep -Fq 'Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE.' "$TMP/README.md"; then
  awk '
    /^> \*\*Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE/ {
      print "> **Release status: CANDIDATE — not yet published.** This source tree is preparing `0.9.0` as the"
      print "> first public review release. The intended `v0.9.0` GitHub prerelease is source-only: it will"
      print "> provide source offered for review, proposed-1.0 scope records, release provenance, and checksums"
      print "> feedback. It will not include crates, wheels, binaries, SBOMs, or docs.rs documentation."
      in_status=1
      next
    }
    in_status && /^$/ { in_status=0; print; next }
    in_status { next }
    { print }
  ' "$TMP/README.md" >"$TMP/README.md.next"
  mv "$TMP/README.md.next" "$TMP/README.md"
  sed -i.bak \
    's/Version 0\.9\.0 is not published to crates\.io or PyPI/Version 0.9.0 is not being published to crates.io or PyPI/' \
    "$TMP/README.md"

  sed -i.bak \
    's/^\*\*Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE\.\*\*$/Release status: **DRAFT — not yet published**./' \
    "$TMP/RELEASE_NOTES.md"
  sed -i.bak 's/^pid-rs 0\.9\.0 is the first public/pid-rs 0.9.0 will be the first public/' \
    "$TMP/RELEASE_NOTES.md"
  sed -i.bak 's/^The 0\.9\.0 release is/The intended 0.9.0 release is/' \
    "$TMP/RELEASE_NOTES.md"
  sed -i.bak 's/^The release tag is/The intended release tag is/' "$TMP/RELEASE_NOTES.md"
  sed -i.bak 's/GitHub release immutability/When published, GitHub release immutability/' \
    "$TMP/RELEASE_NOTES.md"

  awk '
    /^Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE\.$/ {
      print "Release status: **CANDIDATE.** No `v0.9.0` tag or GitHub prerelease is claimed by this source tree."
      print "The metadata remains deliberately undated and the changelog entry remains unreleased until the"
      print "source-review prerelease is intentionally created."
      in_status=1
      next
    }
    in_status && /^$/ { in_status=0; print; next }
    in_status { next }
    { print }
  ' "$TMP/RELEASE_REPRODUCTION.md" >"$TMP/RELEASE_REPRODUCTION.md.next"
  mv "$TMP/RELEASE_REPRODUCTION.md.next" "$TMP/RELEASE_REPRODUCTION.md"

  awk '
    /^pid-rs 0\.9 is the published GitHub-only source-review prerelease/ {
      print "pid-rs 0.9 is the candidate public review release for a proposed 1.0 API. If published, it will"
      print "deliberately narrow the default scientific surface, but no 1.x software/API compatibility promise"
      print "starts until feedback is resolved and 1.0 is released. It does not promote default-off research"
      print "estimators to validated population measures."
      in_status=1
      next
    }
    in_status && /^$/ { in_status=0; print; next }
    in_status { next }
    { print }
  ' "$TMP/MIGRATION.md" >"$TMP/MIGRATION.md.next"
  mv "$TMP/MIGRATION.md.next" "$TMP/MIGRATION.md"

  awk '
    /^The published 0\.9 GitHub-only source-review prerelease presents/ {
      print "The 0.9 candidate will publish these proposed 1.0 limitations for reviewer feedback if the review"
      print "release proceeds. They are not an assertion that 1.0 has shipped or that 1.x compatibility has"
      print "begun. A green test suite establishes implemented software behavior on its covered cases; it does"
      print "not prove that a statistical estimator is valid for an arbitrary dataset."
      in_status=1
      next
    }
    in_status && /^$/ { in_status=0; print; next }
    in_status { next }
    { print }
  ' "$TMP/KNOWN_LIMITATIONS.md" >"$TMP/KNOWN_LIMITATIONS.md.next"
  mv "$TMP/KNOWN_LIMITATIONS.md.next" "$TMP/KNOWN_LIMITATIONS.md"

  sed -i.bak \
    's/^The published 0\.9 source-review prerelease is a GitHub-only source prerelease containing the tagged/The intended 0.9 publication is instead a GitHub-only source prerelease containing the tagged/' \
    "$TMP/RELEASE_AUDIT.md"
  sed -i.bak \
    "s/^| Latest 0\\.x source-review prerelease (\`v0.9.0\`) |/| Latest 0.x source-review prerelease |/" \
    "$TMP/SECURITY.md"
  sed -i.bak \
    "/^| Latest 0\.x source-review prerelease |/i\\
| Current candidate before \`v0.9.0\` | ✅ |" "$TMP/SECURITY.md"

  sed -i.bak '/^date-released:/d' "$TMP/CITATION.cff"
  sed -i.bak 's/## \[0\.9\.0\] - 2026-07-14/## [0.9.0] - Unreleased/' \
    "$TMP/CHANGELOG.md"
  sed -i.bak \
    's#\[Unreleased\]: https://github.com/sepahead/pid-rs/compare/v0\.9\.0\.\.\.HEAD#[Unreleased]: https://github.com/sepahead/pid-rs/compare/ad489f5bf5e15c164c599d069a6bee0f338c0e48...HEAD#' \
    "$TMP/CHANGELOG.md"
  sed -i.bak \
    's#\[0\.9\.0\]: https://github.com/sepahead/pid-rs/compare/ad489f5bf5e15c164c599d069a6bee0f338c0e48\.\.\.v0\.9\.0#[0.9.0]: https://github.com/sepahead/pid-rs/compare/ad489f5bf5e15c164c599d069a6bee0f338c0e48...HEAD#' \
    "$TMP/CHANGELOG.md"
  rm -f "$TMP"/*.bak
fi

fixture_git init -q
fixture_git config user.name "Release State Self-Test"
fixture_git config user.email "release-state-self-test.invalid"
printf '/output.log\n' >>"$TMP/.git/info/exclude"
fixture_git add .
fixture_git commit -q --no-gpg-sign --no-verify -m candidate
candidate_commit="$(fixture_git rev-parse HEAD)"
if fixture_git cat-file -p "$candidate_commit" | grep -q '^gpgsig '; then
  echo "release-state fixture commit was unexpectedly signed" >&2
  exit 1
fi

expect_failure() {
  local label="$1"
  shift
  if "$@" >"$TMP/output.log" 2>&1; then
    echo "ERROR: $label unexpectedly passed" >&2
    return 1
  fi
}

expect_success() {
  local label="$1"
  shift
  if ! "$@" >"$TMP/output.log" 2>&1; then
    echo "ERROR: $label failed" >&2
    sed 's/^/  | /' "$TMP/output.log" >&2
    return 1
  fi
}

run_selector_at() {
  local root="$1"
  GITHUB_REF_TYPE='' GITHUB_REF_NAME='' "$root/scripts/check-current-release-state.sh"
}

run_local_selector() {
  run_selector_at "$TMP"
}

restore_head_file() {
  local path="$1"
  fixture_git show "HEAD:$path" >"$TMP/$path"
}

remove_review_job_line() {
  local job_id="$1"
  local needle="$2"
  local workflow="$TMP/.github/workflows/review-release.yml"
  awk -v header="  $job_id:" -v needle="$needle" '
    $0 == header { in_job=1 }
    in_job && $0 != header && $0 ~ /^  [[:alnum:]_-]+:[[:space:]]*$/ { in_job=0 }
    in_job && index($0, needle) { next }
    { print }
  ' "$workflow" >"$workflow.next"
  mv "$workflow.next" "$workflow"
}

rewrite_locked_package_version() {
  local package="$1"
  local replacement="$2"
  awk -v package="$package" -v replacement="$replacement" '
    /^\[\[package\]\]$/ { in_package=0 }
    $0 == "name = \"" package "\"" { in_package=1 }
    in_package && /^version = "/ {
      print "version = \"" replacement "\""
      in_package=0
      next
    }
    { print }
  ' "$TMP/Cargo.lock" >"$TMP/Cargo.lock.next"
  mv "$TMP/Cargo.lock.next" "$TMP/Cargo.lock"
}

"$TMP/scripts/check-release-state.sh" candidate >/dev/null
"$TMP/scripts/check-version-coherence.sh" >/dev/null
run_local_selector >/dev/null
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
[[ "$version" == 0.9.0 ]] || {
  echo "ERROR: review self-test requires exact workspace version 0.9.0; found '$version'" >&2
  exit 1
}

fixture_git tag "v$version"
expect_failure "selector rejects tagged candidate metadata" \
  run_local_selector
fixture_git tag -d "v$version" >/dev/null

printf '\ndate-released: "2026-07-14"\n' >>"$TMP/CITATION.cff"
expect_failure "candidate date-released injection" \
  "$TMP/scripts/check-release-state.sh" candidate
restore_head_file CITATION.cff

printf '\nThe stable libraries are distributed through crates.io.\n' >>"$TMP/README.md"
expect_failure "candidate present-tense registry claim" \
  "$TMP/scripts/check-release-state.sh" candidate
restore_head_file README.md

# Finalize every lifecycle document for the GitHub-only source-review state while deliberately
# retaining all registry non-publication and pre-1.0 compatibility non-promise text.
awk '
  /^> \*\*Release status: CANDIDATE/ {
    print "> **Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE.** Version `0.9.0` is the"
    print "> first public source-review prerelease. It provides the exact source offered for review, proposed-1.0 scope"
    print "> records, release provenance, and checksums for reviewer feedback. `Source review` names the"
    print "> prerelease\047s purpose, not a completed review. The later 186-row tag-file inventory records every"
    print "> file as `UNASSIGNED` and `INVENTORIED_NOT_REVIEWED`. It is identity/coverage metadata only, not"
    print "> evidence of completed line, model, human, formal, or scientific review. Model review is advisory"
    print "> and is not independent human or institutional review. The immutable `v0.9.0` tag preserves its"
    print "> original wording; this correction does not rewrite tag history."
    in_status=1
    next
  }
  in_status && /^$/ { in_status=0; print; next }
  in_status { next }
  { print }
' "$TMP/README.md" >"$TMP/README.md.next"
mv "$TMP/README.md.next" "$TMP/README.md"
sed -i.bak \
  's/^Release status: \*\*DRAFT — not yet published\*\*\./**Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE.**/' \
  "$TMP/RELEASE_NOTES.md"
sed -i.bak 's/^pid-rs 0\.9\.0 will be the first public/pid-rs 0.9.0 is the first public/' \
  "$TMP/RELEASE_NOTES.md"
sed -i.bak 's/^The intended 0\.9\.0 release is/The 0.9.0 release is/' \
  "$TMP/RELEASE_NOTES.md"
sed -i.bak 's/^The intended release tag is/The release tag is/' "$TMP/RELEASE_NOTES.md"
sed -i.bak 's/When published, GitHub release/GitHub release/' "$TMP/RELEASE_NOTES.md"
awk '
  /^Release status: \*\*CANDIDATE\.\*\*/ {
    print "Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE."
    print "The v0.9.0 GitHub source-review prerelease is published for reviewer feedback."
    in_status=1
    next
  }
  in_status && /^$/ { in_status=0; print; next }
  in_status { next }
  { print }
' "$TMP/RELEASE_REPRODUCTION.md" >"$TMP/RELEASE_REPRODUCTION.md.next"
mv "$TMP/RELEASE_REPRODUCTION.md.next" "$TMP/RELEASE_REPRODUCTION.md"
awk '
  /^pid-rs 0\.9 is the candidate public review release/ {
    print "pid-rs 0.9 is the published GitHub-only source-review prerelease for a proposed 1.0 API."
    print "It narrows the default scientific surface without starting a 1.x compatibility promise."
    in_status=1
    next
  }
  in_status && /^$/ { in_status=0; print; next }
  in_status { next }
  { print }
' "$TMP/MIGRATION.md" >"$TMP/MIGRATION.md.next"
mv "$TMP/MIGRATION.md.next" "$TMP/MIGRATION.md"
awk '
  /^The 0\.9 candidate will publish/ {
    print "The published 0.9 GitHub-only source-review prerelease presents these proposed 1.0 limitations for reviewer feedback."
    print "They are not an assertion that 1.0 has shipped or that 1.x compatibility has begun."
    in_status=1
    next
  }
  in_status && /^$/ { in_status=0; print; next }
  in_status { next }
  { print }
' "$TMP/KNOWN_LIMITATIONS.md" >"$TMP/KNOWN_LIMITATIONS.md.next"
mv "$TMP/KNOWN_LIMITATIONS.md.next" "$TMP/KNOWN_LIMITATIONS.md"
sed -i.bak \
  's/^The intended 0\.9 publication is instead a GitHub-only source prerelease containing the tagged/The published 0.9 source-review prerelease is a GitHub-only source prerelease containing the tagged/' \
  "$TMP/RELEASE_AUDIT.md"
sed -i.bak "/^| Current candidate before \`v0\\.9\\.0\` |/d" "$TMP/SECURITY.md"
sed -i.bak \
  "s/^| Latest 0\\.x source-review prerelease |/| Latest 0.x source-review prerelease (\`v0.9.0\`) |/" \
  "$TMP/SECURITY.md"
sed -i.bak "s/## \[$version\] - Unreleased/## [$version] - 2026-07-14/" \
  "$TMP/CHANGELOG.md"
sed -i.bak \
  "s#\[$version\]: https://github.com/sepahead/pid-rs/compare/ad489f5bf5e15c164c599d069a6bee0f338c0e48...HEAD#[$version]: https://github.com/sepahead/pid-rs/compare/ad489f5bf5e15c164c599d069a6bee0f338c0e48...v$version#" \
  "$TMP/CHANGELOG.md"
printf '\ndate-released: "2026-07-14"\n' >>"$TMP/CITATION.cff"
rm -f "$TMP"/*.bak
fixture_git add .
fixture_git commit -q --no-gpg-sign --no-verify -m review-metadata
cp "$TMP/README.md" "$EXTERNAL_TMP/README.corrected.md"
cp "$TMP/RELEASE_NOTES.md" "$EXTERNAL_TMP/RELEASE_NOTES.corrected.md"

# An extracted review-source archive has no Git metadata. Build it from the exact committed fixture
# bytes without disturbing the live fixture repository: later tag-inference tests must continue to
# exercise that repository, not a moved-out/moved-back approximation.
review_source_fixture="$EXTERNAL_TMP/review-source"
create_tracked_source_fixture review-source "$review_source_fixture"
expect_success "review-source archive: release-state checker" \
  "$review_source_fixture/scripts/check-release-state.sh" review-source "v$version"
expect_success "review-source archive: version-coherence checker" \
  "$review_source_fixture/scripts/check-version-coherence.sh" review-source "v$version"
expect_success "review-source archive: automatic selector" \
  run_selector_at "$review_source_fixture"

# A source archive can be unpacked below an unrelated Git repository. Make that ancestor maximally
# misleading: it is clean, ignores the extracted child, and has the exact release tag at its HEAD.
# The child selector must still choose source mode rather than inheriting the ancestor's tag state.
hostile_parent="$EXTERNAL_TMP/unrelated-parent"
hostile_review_source="$hostile_parent/extracted-review-source"
mkdir -p "$hostile_parent"
isolated_git "$hostile_parent" init -q
isolated_git "$hostile_parent" config user.name "Unrelated Parent"
isolated_git "$hostile_parent" config user.email "unrelated-parent.invalid"
printf '/extracted-review-source/\n' >"$hostile_parent/.gitignore"
isolated_git "$hostile_parent" add .gitignore
isolated_git "$hostile_parent" commit -q --no-gpg-sign --no-verify -m unrelated-parent
isolated_git "$hostile_parent" tag -a "v$version" -m "unrelated v$version"
create_tracked_source_fixture hostile-review-source "$hostile_review_source"
discovered_parent="$(isolated_git "$hostile_review_source" rev-parse --show-toplevel)"
hostile_parent_physical="$(cd "$hostile_parent" && pwd -P)"
[[ "$discovered_parent" == "$hostile_parent_physical" ]] || {
  echo "ERROR: hostile-review-source did not discover the intended unrelated ancestor Git root" >&2
  exit 1
}
[[ -z "$(isolated_git "$hostile_review_source" status --porcelain=v2 --untracked-files=all)" ]] || {
  echo "ERROR: hostile-review-source unrelated ancestor fixture is not clean" >&2
  exit 1
}
expect_success "hostile-review-source archive: release-state checker" \
  "$hostile_review_source/scripts/check-release-state.sh" review-source "v$version"
expect_success "hostile-review-source archive: version-coherence checker" \
  "$hostile_review_source/scripts/check-version-coherence.sh" review-source "v$version"
expect_success "hostile-review-source archive: selector ignores unrelated ancestor Git" \
  run_selector_at "$hostile_review_source"

fixture_git tag "v$version"
expect_failure "selector rejects lightweight review tag" \
  run_local_selector
fixture_git tag -d "v$version" >/dev/null

# Reconstruct the immutable publication wording in a distinct tagged commit. Current source mode
# must use the corrected evidence labels, while tag mode verifies the historical bytes without
# promoting them into completed-review credit.
awk '
  /^> \*\*Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE/ {
    print "> **Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE.** Version `0.9.0` is the first public"
    print "> source-review prerelease. It provides the exact reviewed source, proposed-1.0 scope records,"
    print "> review provenance, and checksums for reviewer feedback. It contains no registry packages,"
    print "> wheels, binaries, SBOMs, or docs.rs publication."
    in_status=1
    next
  }
  in_status && /^$/ { in_status=0; print; next }
  in_status { next }
  { print }
' "$TMP/README.md" >"$TMP/README.md.next"
mv "$TMP/README.md.next" "$TMP/README.md"
awk '
  /^The 0\.9\.0 release is a GitHub \*\*prerelease for source review\*\*\./ {
    print "The 0.9.0 release is a GitHub **prerelease for source review**. Its downloadable payload is"
    print "limited to the reviewed source archive, the human- and machine-readable proposed-1.0 scope records,"
    print "`REVIEW_RELEASE_PROVENANCE.txt`, and SHA-256/SHA-512 checksum manifests. GitHub\047s automatically"
    print "generated source archives remain available as usual."
    in_boundary=1
    next
  }
  in_boundary && /^$/ { in_boundary=0; print; next }
  in_boundary { next }
  { print }
' "$TMP/RELEASE_NOTES.md" >"$TMP/RELEASE_NOTES.md.next"
mv "$TMP/RELEASE_NOTES.md.next" "$TMP/RELEASE_NOTES.md"
fixture_git add README.md RELEASE_NOTES.md
fixture_git commit -q --no-gpg-sign --no-verify -m historical-review-wording
historical_review_commit="$(fixture_git rev-parse HEAD)"
fixture_git tag -a "v$version" -m "pid-rs $version source-review prerelease" \
  "$historical_review_commit"
"$TMP/scripts/check-release-state.sh" review-tagged "v$version" >/dev/null
"$TMP/scripts/check-version-coherence.sh" review-tagged "v$version" >/dev/null
run_local_selector >/dev/null

sed -i.bak \
  '/Distribution is GitHub-only: crates\.io and PyPI are not published for this 0\.9\.0 review prerelease\./d' \
  "$TMP/README.md"
rm "$TMP/README.md.bak"
expect_failure "dirty worktree cannot infer clean review tag" \
  run_local_selector
grep --fixed-strings \
  "README.md does not contain required release text: Distribution is GitHub-only" \
  "$TMP/output.log" >/dev/null
restore_head_file README.md

cp "$EXTERNAL_TMP/README.corrected.md" "$TMP/README.md"
cp "$EXTERNAL_TMP/RELEASE_NOTES.corrected.md" "$TMP/RELEASE_NOTES.md"
fixture_git add README.md RELEASE_NOTES.md
fixture_git commit -q --no-gpg-sign --no-verify -m review-truth-correction
"$TMP/scripts/check-release-state.sh" review-source "v$version" >/dev/null
"$TMP/scripts/check-version-coherence.sh" review-source "v$version" >/dev/null
run_local_selector >/dev/null

cp "$TMP/README.md" "$EXTERNAL_TMP/README.md"
rm "$TMP/README.md"
ln -s "$EXTERNAL_TMP/README.md" "$TMP/README.md"
expect_failure "review-source rejects symlinked release metadata" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
grep --fixed-strings "required source file must not be a symlink: README.md" \
  "$TMP/output.log" >/dev/null
expect_failure "version checker rejects symlinked release metadata" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings "required source file must not be a symlink: README.md" \
  "$TMP/output.log" >/dev/null
rm "$TMP/README.md"
restore_head_file README.md

# The current source gate distinguishes an offer/inventory from completed review and binds every
# evidence-class disclosure independently.
sed -i.bak 's/exact source offered for review/exact source available for review/' "$TMP/README.md"
rm "$TMP/README.md.bak"
expect_failure "review-source source-offer boundary removal" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
restore_head_file README.md

sed -i.bak 's/not a completed review/not a finished review/' "$TMP/RELEASE_NOTES.md"
rm "$TMP/RELEASE_NOTES.md.bak"
expect_failure "review-source purpose boundary removal" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
restore_head_file RELEASE_NOTES.md

sed -i.bak 's/`UNASSIGNED` and `INVENTORIED_NOT_REVIEWED`/`ASSIGNED` and `REVIEWED`/' \
  "$TMP/README.md"
rm "$TMP/README.md.bak"
expect_failure "review-source inventory-state boundary removal" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
restore_head_file README.md

sed -i.bak 's/identity\/coverage metadata/inventory\/coverage metadata/' \
  "$TMP/RELEASE_NOTES.md"
rm "$TMP/RELEASE_NOTES.md.bak"
expect_failure "review-source evidence-class boundary removal" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
restore_head_file RELEASE_NOTES.md

sed -i.bak 's/not independent human or institutional review/not separate human or institutional review/' \
  "$TMP/README.md"
rm "$TMP/README.md.bak"
expect_failure "review-source model-independence boundary removal" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
restore_head_file README.md

sed -i.bak 's/does not rewrite tag history/does not alter tag history/' "$TMP/RELEASE_NOTES.md"
rm "$TMP/RELEASE_NOTES.md.bak"
expect_failure "review-source history-preservation boundary removal" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
restore_head_file RELEASE_NOTES.md

sed -i.bak 's/exact source offered for review/exact reviewed source/' "$TMP/README.md"
rm "$TMP/README.md.bak"
expect_failure "review-source rejects reviewed-source promotion despite disclaimer" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
grep --fixed-strings "README promotes source-offer or inventory evidence" "$TMP/output.log" >/dev/null
restore_head_file README.md

sed -i.bak 's/exact source offered for review/exact reviewed source/' \
  "$TMP/RELEASE_NOTES.md"
rm "$TMP/RELEASE_NOTES.md.bak"
expect_failure "review-source rejects reviewed-archive promotion despite disclaimer" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
grep --fixed-strings "release notes promote source-offer or inventory evidence" \
  "$TMP/output.log" >/dev/null
restore_head_file RELEASE_NOTES.md

sed -i.bak 's/release provenance/review provenance/' "$TMP/README.md"
rm "$TMP/README.md.bak"
expect_failure "review-source rejects review-provenance promotion" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
grep --fixed-strings "README promotes source-offer or inventory evidence" "$TMP/output.log" >/dev/null
restore_head_file README.md

printf '\n' >>"$TMP/audit/evidence/FILE_REVIEW_LEDGER.csv"
expect_failure "review-source rejects tag-file inventory byte mutation" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
grep --fixed-strings "tag-file inventory bytes differ from the protected baseline" \
  "$TMP/output.log" >/dev/null
restore_head_file audit/evidence/FILE_REVIEW_LEDGER.csv

cp "$TMP/audit/evidence/FILE_REVIEW_LEDGER.csv" "$EXTERNAL_TMP/FILE_REVIEW_LEDGER.csv"
rm "$TMP/audit/evidence/FILE_REVIEW_LEDGER.csv"
ln -s "$EXTERNAL_TMP/FILE_REVIEW_LEDGER.csv" "$TMP/audit/evidence/FILE_REVIEW_LEDGER.csv"
expect_failure "review-source rejects symlinked tag-file inventory" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
grep --fixed-strings "tag-file inventory must be a regular non-symlink file" \
  "$TMP/output.log" >/dev/null
rm "$TMP/audit/evidence/FILE_REVIEW_LEDGER.csv"
restore_head_file audit/evidence/FILE_REVIEW_LEDGER.csv

# Every defining review-release claim is fail-closed.
sed -i.bak 's/date-released: "2026-07-14"/date-released: "2026-07-13"/' \
  "$TMP/CITATION.cff"
rm "$TMP/CITATION.cff.bak"
expect_failure "review-source CFF/changelog date mismatch" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
grep --fixed-strings \
  "review-source CFF date '2026-07-13' != CHANGELOG date '2026-07-14'" \
  "$TMP/output.log" >/dev/null
restore_head_file CITATION.cff

sed -i.bak 's/date-released: "2026-07-14"/date-released: "2026-02-30"/' \
  "$TMP/CITATION.cff"
sed -i.bak 's/## \[0.9.0\] - 2026-07-14/## [0.9.0] - 2026-02-30/' \
  "$TMP/CHANGELOG.md"
rm "$TMP/CITATION.cff.bak" "$TMP/CHANGELOG.md.bak"
expect_failure "review-source invalid calendar date" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
grep --fixed-strings "needs a valid ISO release date; found '2026-02-30'" \
  "$TMP/output.log" >/dev/null
restore_head_file CITATION.cff
restore_head_file CHANGELOG.md

sed -i.bak '/Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE\./d' \
  "$TMP/README.md"
rm "$TMP/README.md.bak"
expect_failure "review-source exact status removal" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
expect_failure "version checker review-source exact status removal" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
restore_head_file README.md

for job_id in verify-review-tag build-review-assets publish-review-prerelease; do
  for guard in \
    'github.actor == github.repository_owner &&' \
    'github.triggering_actor == github.repository_owner'; do
    remove_review_job_line "$job_id" "$guard"
    expect_failure "review-source $job_id owner authorization removal" \
      "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
    grep --fixed-strings \
      "review-release $job_id job does not contain required release text: $guard" \
      "$TMP/output.log" >/dev/null
    restore_head_file .github/workflows/review-release.yml
  done
done

sed -i.bak '/echo "qualified_ci_run_attempt=\$CI_RUN_ATTEMPT"/d' \
  "$TMP/.github/workflows/review-release.yml"
rm "$TMP/.github/workflows/review-release.yml.bak"
expect_failure "review-source exact CI attempt provenance removal" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings \
  'does not contain required release text: echo "qualified_ci_run_attempt=$CI_RUN_ATTEMPT"' \
  "$TMP/output.log" >/dev/null
restore_head_file .github/workflows/review-release.yml

sed -i.bak '/echo "immutability_preflight=\$IMMUTABILITY_PREFLIGHT"/d' \
  "$TMP/.github/workflows/review-release.yml"
rm "$TMP/.github/workflows/review-release.yml.bak"
expect_failure "review-source immutability acknowledgement provenance removal" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings \
  'does not contain required release text: echo "immutability_preflight=$IMMUTABILITY_PREFLIGHT"' \
  "$TMP/output.log" >/dev/null
restore_head_file .github/workflows/review-release.yml

sed -i.bak '/artifact-ids: \${{ needs\.build-review-assets\.outputs\.review_artifact_id }}/d' \
  "$TMP/.github/workflows/review-release.yml"
rm "$TMP/.github/workflows/review-release.yml.bak"
expect_failure "review-source exact Actions artifact selection removal" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings \
  'artifact-ids: ${{ needs.build-review-assets.outputs.review_artifact_id }}' \
  "$TMP/output.log" >/dev/null
restore_head_file .github/workflows/review-release.yml

remove_review_job_line build-review-assets \
  'name: review-release-assets-${{ inputs.tag }}-attempt-${{ github.run_attempt }}'
expect_failure "review-source attempt-qualified Actions artifact name removal" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings \
  'name: review-release-assets-${{ inputs.tag }}-attempt-${{ github.run_attempt }}' \
  "$TMP/output.log" >/dev/null
restore_head_file .github/workflows/review-release.yml

remove_review_job_line publish-review-prerelease 'and .body == $body'
expect_failure "review-source exact release body validation removal" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings "must contain 'and .body == \$body' exactly 5 times; found 0" \
  "$TMP/output.log" >/dev/null
restore_head_file .github/workflows/review-release.yml

remove_review_job_line publish-review-prerelease \
  'git ls-remote origin "$tag_ref" "$peeled_ref"'
expect_failure "review-source publication-boundary remote tag recheck removal" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings \
  "must contain 'git ls-remote origin \"\$tag_ref\" \"\$peeled_ref\"' exactly 4 times; found 0" \
  "$TMP/output.log" >/dev/null
restore_head_file .github/workflows/review-release.yml

remove_review_job_line publish-review-prerelease \
  'trap cleanup_mutable_review_release EXIT'
expect_failure "review-source mutable-release cleanup trap removal" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings \
  'does not contain required release text: trap cleanup_mutable_review_release EXIT' \
  "$TMP/output.log" >/dev/null
restore_head_file .github/workflows/review-release.yml

for immutable_existing_predicate in \
  '.tag_name == $tag' \
  'and .target_commitish == $commit' \
  'and .draft == false' \
  'and .immutable == true'
do
  remove_review_job_line publish-review-prerelease "$immutable_existing_predicate"
  expect_failure "review-source immutable-existing predicate removal: $immutable_existing_predicate" \
    "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
  grep --fixed-strings \
    "review-release immutable-existing-release preflight does not contain required release text" \
    "$TMP/output.log" >/dev/null
  restore_head_file .github/workflows/review-release.yml
done

for retry_lineage_predicate in \
  'ALREADY_PUBLISHED: ${{ steps.preflight.outputs.already_published }}' \
  'if [[ "$ALREADY_PUBLISHED" == true ]]' \
  'test "$(wc -l < "$published_provenance")" -eq 28' \
  'if (count != 1)' \
  'test "$original_workflow_attempt" -lt "$GITHUB_RUN_ATTEMPT"' \
  'require_provenance_value workflow_run_id "$GITHUB_RUN_ID"' \
  'require_provenance_value dispatch_actor "$GITHUB_REPOSITORY_OWNER"' \
  'require_provenance_value triggering_actor "$GITHUB_REPOSITORY_OWNER"' \
  'require_provenance_value repository_owner "$GITHUB_REPOSITORY_OWNER"' \
  'actions/runs/$GITHUB_RUN_ID/attempts/$original_workflow_attempt"' \
  '(.id | tostring) == $workflow_run_id' \
  '(.run_attempt | tostring) == $workflow_attempt' \
  'and .event == "workflow_dispatch"' \
  'and .head_sha == $workflow_commit' \
  '.path == ".github/workflows/review-release.yml"' \
  'and .actor.login == $workflow_owner' \
  'and .triggering_actor.login == $workflow_owner' \
  'and .repository.full_name == $workflow_repository' \
  'original_jobs="$(gh api --paginate --slurp' \
  'actions/runs/$GITHUB_RUN_ID/attempts/$original_workflow_attempt/jobs?per_page=100"' \
  '[.[]?.jobs[]? | select(.name == "Publish immutable source-review prerelease")]' \
  'test "$(jq length <<<"$publishing_jobs")" -eq 1' \
  'and (.[0].run_id | tostring) == $workflow_run_id' \
  'and .[0].head_sha == $workflow_commit' \
  'and .[0].workflow_name == "Source review prerelease"' \
  '([.[0].steps[] | select(.name == $name)] | length) == 1' \
  '[0].conclusion == "success"' \
  'actions/runs/$original_ci_run_id/attempts/$original_ci_run_attempt"' \
  '(.id | tostring) == $ci_run_id' \
  '(.run_attempt | tostring) == $ci_attempt' \
  'and .event == "push"' \
  'and .head_branch == $ci_tag' \
  'and .head_sha == $ci_commit' \
  '.path == ".github/workflows/ci.yml"' \
  'and .repository.full_name == $ci_repository' \
  'and .conclusion == "success"' \
  'and ([.[].name] | sort) == ([' \
  'cmp SHA256SUMS "$RUNNER_TEMP/published-SHA256SUMS"' \
  'cmp SHA512SUMS "$RUNNER_TEMP/published-SHA512SUMS"' \
  'cmp release/RELEASE_SCOPE_1_0.md' \
  'cmp release/release-scope-1.0.json' \
  'cmp "release/$source_archive"' \
  'for published_asset in downloaded-after-publication/*'
do
  remove_review_job_line publish-review-prerelease "$retry_lineage_predicate"
  expect_failure "review-source immutable retry lineage removal: $retry_lineage_predicate" \
    "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
  grep --fixed-strings \
    "review-release immutable retry verifier does not contain required release text" \
    "$TMP/output.log" >/dev/null
  restore_head_file .github/workflows/review-release.yml
done

for retry_publication_step in \
  '"Reconfirm owner authorization"' \
  '"Preflight the exact tag and review assets"' \
  '"Revalidate the exact tag before creating the draft"' \
  '"Create the draft source-review prerelease"' \
  '"Byte-verify the draft asset set"' \
  '"Publish as a prerelease without changing latest"'
do
  remove_review_job_line publish-review-prerelease "$retry_publication_step"
  expect_failure "review-source immutable retry publication-step removal: $retry_publication_step" \
    "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
  grep --fixed-strings \
    "review-release immutable retry publication-step lineage does not contain required release text" \
    "$TMP/output.log" >/dev/null
  restore_head_file .github/workflows/review-release.yml
done

awk '
  { print }
  /Release was previously observed immutable; refusing mutation or deletion/ {
    print "            gh api --method DELETE repos/example/release"
  }
' "$TMP/.github/workflows/review-release.yml" \
  > "$TMP/.github/workflows/review-release.yml.next"
mv "$TMP/.github/workflows/review-release.yml.next" \
  "$TMP/.github/workflows/review-release.yml"
expect_failure "review-source immutable retry verifier rejects release deletion" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings \
  "review-release immutable retry verifier must not delete a release already observed immutable" \
  "$TMP/output.log" >/dev/null
restore_head_file .github/workflows/review-release.yml

remove_review_job_line build-review-assets 'echo "registry_publication=none"'
expect_failure "review-source missing registry provenance key" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings \
  "must contain 'echo \"registry_publication=none\"' exactly 1 times; found 0" \
  "$TMP/output.log" >/dev/null
restore_head_file .github/workflows/review-release.yml

awk '
  { print }
  /echo "registry_publication=none"/ { print }
' "$TMP/.github/workflows/review-release.yml" \
  > "$TMP/.github/workflows/review-release.yml.next"
mv "$TMP/.github/workflows/review-release.yml.next" \
  "$TMP/.github/workflows/review-release.yml"
expect_failure "review-source duplicate registry provenance key" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings \
  "must contain 'echo \"registry_publication=none\"' exactly 1 times; found 2" \
  "$TMP/output.log" >/dev/null
restore_head_file .github/workflows/review-release.yml

sed -i.bak '/echo "repository_owner=\$GITHUB_REPOSITORY_OWNER"/d' \
  "$TMP/.github/workflows/review-release.yml"
rm "$TMP/.github/workflows/review-release.yml.bak"
expect_failure "review-source owner provenance removal" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings \
  'does not contain required release text: echo "repository_owner=$GITHUB_REPOSITORY_OWNER"' \
  "$TMP/output.log" >/dev/null
restore_head_file .github/workflows/review-release.yml

for job_id in verify-review-tag build-review-assets publish-review-prerelease; do
  for guard in \
    'test "$GITHUB_ACTOR" = "$GITHUB_REPOSITORY_OWNER"' \
    'test "$GITHUB_TRIGGERING_ACTOR" = "$GITHUB_REPOSITORY_OWNER"'; do
    remove_review_job_line "$job_id" "$guard"
    expect_failure "review-source $job_id owner shell guard removal" \
      "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
    grep --fixed-strings \
      "review-release $job_id job does not contain required release text: $guard" \
      "$TMP/output.log" >/dev/null
    restore_head_file .github/workflows/review-release.yml
  done
done

sed -i.bak \
  '/Distribution is GitHub-only: crates\.io and PyPI are not published for this 0\.9\.0 review prerelease\./d' \
  "$TMP/README.md"
rm "$TMP/README.md.bak"
expect_failure "review-source registry non-publication removal" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
expect_failure "version checker review-source registry non-publication removal" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
restore_head_file README.md

sed -i.bak \
  '/This 0\.9\.0 review prerelease makes no 1\.x compatibility promise\./d' \
  "$TMP/RELEASE_NOTES.md"
rm "$TMP/RELEASE_NOTES.md.bak"
expect_failure "review-source 1.x non-promise removal" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
expect_failure "version checker review-source 1.x non-promise removal" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
restore_head_file RELEASE_NOTES.md

expect_failure "review-source rejects leading-zero release reference" \
  "$TMP/scripts/check-release-state.sh" review-source v00.9.0
grep --fixed-strings "release reference must match vMAJOR.MINOR.PATCH" \
  "$TMP/output.log" >/dev/null
expect_failure "version checker rejects leading-zero release reference" \
  "$TMP/scripts/check-version-coherence.sh" review-source v00.9.0
grep --fixed-strings "release reference must match vMAJOR.MINOR.PATCH" \
  "$TMP/output.log" >/dev/null

sed -i.bak 's/version = "0.9.0"/version = "00.9.0"/' "$TMP/Cargo.toml"
rm "$TMP/Cargo.toml.bak"
expect_failure "review-source rejects leading-zero workspace version" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
grep --fixed-strings "Cargo.toml workspace version is not exact SemVer: '00.9.0'" \
  "$TMP/output.log" >/dev/null
expect_failure "version checker rejects leading-zero workspace version" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings "Cargo.toml workspace version is not exact SemVer: '00.9.0'" \
  "$TMP/output.log" >/dev/null
restore_head_file Cargo.toml

printf '\ndoi: "10.5281/zenodo.1234567"\n' >>"$TMP/CITATION.cff"
expect_failure "review-source software DOI injection" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
grep --fixed-strings "declares a top-level software DOI" "$TMP/output.log" >/dev/null
expect_failure "version checker review-source software DOI injection" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings "must not declare a top-level software DOI" "$TMP/output.log" >/dev/null
restore_head_file CITATION.cff

printf '\nrepository-artifact: "https://zenodo.org/records/1234567"\n' \
  >>"$TMP/CITATION.cff"
expect_failure "review-source Zenodo injection" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
grep --fixed-strings "declares a top-level Zenodo identifier" "$TMP/output.log" >/dev/null
expect_failure "version checker review-source Zenodo injection" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings "must not declare a top-level Zenodo identifier" "$TMP/output.log" >/dev/null
restore_head_file CITATION.cff

sed -i.bak 's/version = "0.9.0"/version = "0.9.1"/' "$TMP/Cargo.toml"
rm "$TMP/Cargo.toml.bak"
expect_failure "review-source non-0.9.0 version injection" \
  "$TMP/scripts/check-release-state.sh" review-source "v$version"
grep --fixed-strings "reserved for exact version '0.9.0'" "$TMP/output.log" >/dev/null
expect_failure "version checker review-source non-0.9.0 version injection" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings "review-source is reserved for exact version '0.9.0'" \
  "$TMP/output.log" >/dev/null
restore_head_file Cargo.toml

# Sole authorship is checked independently across Cargo, CFF, and Python package metadata.
sed -i.bak \
  's/authors = \["Sepehr Mahmoudian"\]/authors = ["Sepehr Mahmoudian", "Second Author"]/' \
  "$TMP/Cargo.toml"
rm "$TMP/Cargo.toml.bak"
expect_failure "review-source second Cargo author injection" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings "Cargo author" "$TMP/output.log" >/dev/null
restore_head_file Cargo.toml

awk '
  /^repository-code:/ {
    print "  - family-names: Author"
    print "    given-names: Second"
  }
  { print }
' "$TMP/CITATION.cff" >"$TMP/CITATION.cff.next"
mv "$TMP/CITATION.cff.next" "$TMP/CITATION.cff"
expect_failure "review-source second CFF author injection" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings "exactly one top-level author; found '2'" "$TMP/output.log" >/dev/null
restore_head_file CITATION.cff

sed -i.bak \
  's/authors = \[{ name = "Sepehr Mahmoudian" }\]/authors = [{ name = "Sepehr Mahmoudian" }, { name = "Second Author" }]/' \
  "$TMP/crates/pid-python/pyproject.toml"
rm "$TMP/crates/pid-python/pyproject.toml.bak"
expect_failure "review-source second Python author injection" \
  "$TMP/scripts/check-version-coherence.sh" review-source "v$version"
grep --fixed-strings "must name exactly one author" "$TMP/output.log" >/dev/null
restore_head_file crates/pid-python/pyproject.toml

# Review-tagged accepts only the exact ref, directly annotated with the same internal name, and
# containing no PGP, SSH, or X.509/CMS signature armor.
expect_failure "review-tagged missing exact tag" \
  "$TMP/scripts/check-release-state.sh" review-tagged v0.9.1

fixture_git tag -d "v$version" >/dev/null
fixture_git tag "v$version"
expect_failure "review-tagged lightweight tag" \
  "$TMP/scripts/check-release-state.sh" review-tagged "v$version"
expect_failure "version checker review-tagged lightweight tag" \
  "$TMP/scripts/check-version-coherence.sh" review-tagged "v$version"
fixture_git tag -d "v$version" >/dev/null

review_regular_commit="$(fixture_git rev-parse HEAD)"
rm "$TMP/README.md"
ln -s RELEASE_NOTES.md "$TMP/README.md"
fixture_git add README.md
fixture_git commit -q --no-gpg-sign --no-verify -m symlinked-review-metadata
fixture_git tag -a "v$version" -m "pid-rs $version symlink rejection"
expect_failure "review-tagged rejects symlinked release metadata" \
  "$TMP/scripts/check-release-state.sh" review-tagged "v$version"
grep --fixed-strings "required tagged file must be a regular blob: README.md" \
  "$TMP/output.log" >/dev/null
expect_failure "version checker rejects symlinked tagged release metadata" \
  "$TMP/scripts/check-version-coherence.sh" review-tagged "v$version"
grep --fixed-strings "required tagged file must be a regular blob: README.md" \
  "$TMP/output.log" >/dev/null
fixture_git tag -d "v$version" >/dev/null
fixture_git checkout -q "$review_regular_commit" -- README.md
fixture_git add README.md
fixture_git commit -q --no-gpg-sign --no-verify -m restore-regular-review-metadata

review_commit="$(fixture_git rev-parse HEAD)"
misnamed_tag_object="$(
  printf 'object %s\ntype commit\ntag v0.9.1\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\nmisnamed review tag\n' \
    "$review_commit" \
    | fixture_git hash-object -t tag -w --stdin
)"
fixture_git update-ref "refs/tags/v$version" "$misnamed_tag_object"
expect_failure "review-tagged mismatched internal name" \
  "$TMP/scripts/check-release-state.sh" review-tagged "v$version"
expect_failure "version checker review-tagged mismatched internal name" \
  "$TMP/scripts/check-version-coherence.sh" review-tagged "v$version"
fixture_git tag -d "v$version" >/dev/null

inner_tag_object="$(
  printf 'object %s\ntype commit\ntag inner-review\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\ninner review tag\n' \
    "$review_commit" \
    | fixture_git hash-object -t tag -w --stdin
)"
nested_tag_object="$(
  printf 'object %s\ntype tag\ntag v%s\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\nnested review tag\n' \
    "$inner_tag_object" "$version" \
    | fixture_git hash-object -t tag -w --stdin
)"
fixture_git update-ref "refs/tags/v$version" "$nested_tag_object"
expect_failure "review-tagged nested annotated tag" \
  "$TMP/scripts/check-release-state.sh" review-tagged "v$version"
grep --fixed-strings "must directly annotate a commit, not 'tag'" "$TMP/output.log" >/dev/null
expect_failure "version checker review-tagged nested annotated tag" \
  "$TMP/scripts/check-version-coherence.sh" review-tagged "v$version"
grep --fixed-strings "must directly annotate a commit, not 'tag'" "$TMP/output.log" >/dev/null
fixture_git tag -d "v$version" >/dev/null

signed_tag_object="$(
  printf 'object %s\ntype commit\ntag v%s\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\nreview\n-----BEGIN PGP SIGNATURE-----\nnot-a-real-signature\n-----END PGP SIGNATURE-----\n' \
    "$review_commit" "$version" \
    | fixture_git hash-object -t tag -w --stdin
)"
fixture_git update-ref "refs/tags/v$version" "$signed_tag_object"
expect_failure "review-tagged signed annotated tag" \
  "$TMP/scripts/check-release-state.sh" review-tagged "v$version"
grep --fixed-strings "repository policy requires an unsigned annotated tag" \
  "$TMP/output.log" >/dev/null
expect_failure "version checker review-tagged signed annotated tag" \
  "$TMP/scripts/check-version-coherence.sh" review-tagged "v$version"
grep --fixed-strings "repository policy requires an unsigned annotated tag" \
  "$TMP/output.log" >/dev/null
fixture_git tag -d "v$version" >/dev/null
fixture_git tag -a "v$version" -m "pid-rs $version source-review prerelease"

# Preserve the v1-only final-source/tagged paths. A synthetic 1.0 transition updates locked package
# metadata and replaces every review-only lifecycle marker with a final-registry state.
fixture_git tag -d "v$version" >/dev/null
final_version="1.0.0"
sed -i.bak 's/^version = "0\.9\.0"$/version = "1.0.0"/' "$TMP/Cargo.toml"
sed -i.bak 's/version = "0\.9\.0", path/version = "1.0.0", path/' "$TMP/Cargo.toml"
sed -i.bak 's/version = "0\.9\.0", path/version = "1.0.0", path/' \
  "$TMP/crates/pid-python/Cargo.toml"
sed -i.bak 's/^version: "0\.9\.0"$/version: "1.0.0"/' "$TMP/CITATION.cff"
for package in pid-core pid-runlog pid-python; do
  rewrite_locked_package_version "$package" "$final_version"
done

awk '
  /^> \*\*Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE/ {
    print "> **Release status: FINAL REGISTRY RELEASE.** Version `1.0.0` is the qualified stable release."
    in_status=1
    next
  }
  in_status && /^$/ { in_status=0; print; next }
  in_status { next }
  { print }
' "$TMP/README.md" >"$TMP/README.md.next"
mv "$TMP/README.md.next" "$TMP/README.md"
sed -i.bak \
  '/Distribution is GitHub-only: crates\.io and PyPI are not published for this 0\.9\.0 review prerelease\./d' \
  "$TMP/README.md"
sed -i.bak \
  '/This 0\.9\.0 review prerelease makes no 1\.x compatibility promise\./d' "$TMP/README.md"
sed -i.bak 's/^# pid-rs 0\.9\.0$/# pid-rs 1.0.0/' "$TMP/RELEASE_NOTES.md"
sed -i.bak \
  's/^\*\*Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE\.\*\*/**Release status: FINAL REGISTRY RELEASE.**/' \
  "$TMP/RELEASE_NOTES.md"
sed -i.bak \
  '/Distribution is GitHub-only: crates\.io and PyPI are not published for this 0\.9\.0 review prerelease\./d' \
  "$TMP/RELEASE_NOTES.md"
sed -i.bak \
  '/This 0\.9\.0 review prerelease makes no 1\.x compatibility promise\./d' \
  "$TMP/RELEASE_NOTES.md"
sed -i.bak \
  's/^Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE\.$/Release status: FINAL REGISTRY RELEASE./' \
  "$TMP/RELEASE_REPRODUCTION.md"
sed -i.bak '/^The v0\.9\.0 GitHub source-review prerelease is published/d' \
  "$TMP/RELEASE_REPRODUCTION.md"
sed -i.bak \
  's/^pid-rs 0\.9 is the published GitHub-only source-review prerelease for a proposed 1\.0 API\.$/pid-rs version 1.0.0 is the qualified stable registry release./' \
  "$TMP/MIGRATION.md"
sed -i.bak \
  's/^The published 0\.9 GitHub-only source-review prerelease presents these proposed 1\.0 limitations for reviewer feedback\.$/The pid-rs 1.0.0 limitations apply to the qualified stable registry release./' \
  "$TMP/KNOWN_LIMITATIONS.md"
sed -i.bak \
  "s/^| Latest 0\\.x source-review prerelease (\`v0.9.0\`) |/| Latest 1.x release |/" \
  "$TMP/SECURITY.md"
sed -i.bak \
  's/^The published 0\.9 source-review prerelease is a GitHub-only source prerelease containing/The qualified pid-rs 1.0.0 release contains/' \
  "$TMP/RELEASE_AUDIT.md"
printf '\n## [%s] - 2026-07-14\n\nQualified stable registry release.\n' \
  "$final_version" >>"$TMP/CHANGELOG.md"
printf '\n[%s]: https://github.com/sepahead/pid-rs/compare/ad489f5bf5e15c164c599d069a6bee0f338c0e48...v%s\n' \
  "$final_version" "$final_version" >>"$TMP/CHANGELOG.md"
printf '\nQualified registry references: pid-core@%s and pid-core-rs==%s.\n' \
  "$final_version" "$final_version" >>"$TMP/README.md"
printf '\nFinal release reference: v%s.\n' "$final_version" \
  >>"$TMP/RELEASE_REPRODUCTION.md"
printf '\nFinal release reference: v%s.\n' "$final_version" >>"$TMP/scripts/README.md"
rm -f "$TMP"/*.bak "$TMP/crates/pid-python"/*.bak
fixture_git add .
fixture_git commit -q --no-gpg-sign --no-verify -m final-registry-metadata

final_source_fixture="$EXTERNAL_TMP/final-source"
create_tracked_source_fixture final-source "$final_source_fixture"
expect_success "final-source archive: release-state checker" \
  "$final_source_fixture/scripts/check-release-state.sh" final-source "v$final_version"
expect_success "final-source archive: version-coherence checker" \
  "$final_source_fixture/scripts/check-version-coherence.sh" final-source "v$final_version"
expect_success "final-source archive: automatic selector" \
  run_selector_at "$final_source_fixture"

fixture_git tag -a "v$final_version" -m "v$final_version"
"$TMP/scripts/check-release-state.sh" tagged "v$final_version" >/dev/null
"$TMP/scripts/check-version-coherence.sh" "v$final_version" >/dev/null
run_local_selector >/dev/null

final_commit="$(fixture_git rev-parse HEAD)"
final_inner_tag_object="$(
  printf 'object %s\ntype commit\ntag inner-final\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\ninner final tag\n' \
    "$final_commit" \
    | fixture_git hash-object -t tag -w --stdin
)"
final_nested_tag_object="$(
  printf 'object %s\ntype tag\ntag v%s\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\nnested final tag\n' \
    "$final_inner_tag_object" "$final_version" \
    | fixture_git hash-object -t tag -w --stdin
)"
fixture_git update-ref "refs/tags/v$final_version" "$final_nested_tag_object"
expect_failure "tagged nested annotated tag" \
  "$TMP/scripts/check-release-state.sh" tagged "v$final_version"
expect_failure "version checker tagged nested annotated tag" \
  "$TMP/scripts/check-version-coherence.sh" "v$final_version"
fixture_git tag -d "v$final_version" >/dev/null

final_misnamed_tag_object="$(
  printf 'object %s\ntype commit\ntag v1.0.1\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\nmisnamed final tag\n' \
    "$final_commit" \
    | fixture_git hash-object -t tag -w --stdin
)"
fixture_git update-ref "refs/tags/v$final_version" "$final_misnamed_tag_object"
expect_failure "tagged mismatched internal name" \
  "$TMP/scripts/check-release-state.sh" tagged "v$final_version"
expect_failure "version checker tagged mismatched internal name" \
  "$TMP/scripts/check-version-coherence.sh" "v$final_version"
fixture_git tag -d "v$final_version" >/dev/null

final_signed_tag_object="$(
  printf 'object %s\ntype commit\ntag v%s\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\nfinal\n-----BEGIN PGP SIGNATURE-----\nnot-a-real-signature\n-----END PGP SIGNATURE-----\n' \
    "$final_commit" "$final_version" \
    | fixture_git hash-object -t tag -w --stdin
)"
fixture_git update-ref "refs/tags/v$final_version" "$final_signed_tag_object"
expect_failure "tagged signed annotated tag" \
  "$TMP/scripts/check-release-state.sh" tagged "v$final_version"
expect_failure "version checker tagged signed annotated tag" \
  "$TMP/scripts/check-version-coherence.sh" "v$final_version"
fixture_git tag -d "v$final_version" >/dev/null
fixture_git tag -a "v$final_version" -m "v$final_version"

sed -i.bak 's/date-released: "2026-07-14"/date-released: "2026-02-30"/' \
  "$TMP/CITATION.cff"
sed -i.bak 's/## \[1.0.0\] - 2026-07-14/## [1.0.0] - 2026-02-30/' \
  "$TMP/CHANGELOG.md"
rm "$TMP/CITATION.cff.bak" "$TMP/CHANGELOG.md.bak"
expect_failure "final-source invalid calendar date" \
  "$TMP/scripts/check-release-state.sh" final-source "v$final_version"
grep --fixed-strings "needs an ISO release date; found '2026-02-30'" \
  "$TMP/output.log" >/dev/null
restore_head_file CITATION.cff
restore_head_file CHANGELOG.md

sed -i.bak 's/date-released: "2026-07-14"/date-released: "2026-07-13"/' \
  "$TMP/CITATION.cff"
rm "$TMP/CITATION.cff.bak"
expect_failure "final-source CFF/changelog date mismatch" \
  "$TMP/scripts/check-release-state.sh" final-source "v$final_version"
grep --fixed-strings \
  "final-source CFF date '2026-07-13' != CHANGELOG date '2026-07-14'" \
  "$TMP/output.log" >/dev/null

fixture_git tag -d "v$final_version" >/dev/null
fixture_git add CITATION.cff
fixture_git commit -q --no-gpg-sign --no-verify -m mismatched-tagged-metadata
fixture_git tag -a "v$final_version" -m "v$final_version"
expect_failure "tagged CFF/changelog date mismatch" \
  "$TMP/scripts/check-release-state.sh" tagged "v$final_version"
grep --fixed-strings \
  "tagged CFF date '2026-07-13' != CHANGELOG date '2026-07-14'" \
  "$TMP/output.log" >/dev/null

echo "OK: candidate, review-source, review-tagged, final-source, and tagged states passed; all failure injections were rejected"
