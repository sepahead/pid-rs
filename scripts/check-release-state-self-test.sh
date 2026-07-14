#!/usr/bin/env bash
# Failure-injection tests for release-state and version-coherence checks. Every mutation occurs in
# a temporary repository populated from tracked working-tree files.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-release-state.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

while IFS= read -r -d '' path; do
  mkdir -p "$(dirname "$TMP/$path")"
  cp -p "$REPO_ROOT/$path" "$TMP/$path"
done < <(git -C "$REPO_ROOT" ls-files -z)

# This workflow can be untracked while its introduction and these checks are tested together.
if [[ -f "$REPO_ROOT/.github/workflows/review-release.yml" \
  && ! -f "$TMP/.github/workflows/review-release.yml" ]]; then
  mkdir -p "$TMP/.github/workflows"
  cp -p "$REPO_ROOT/.github/workflows/review-release.yml" \
    "$TMP/.github/workflows/review-release.yml"
fi

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

restore_head_file() {
  local path="$1"
  git -C "$TMP" show "HEAD:$path" >"$TMP/$path"
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
    print "> first public source-review prerelease. It provides the reviewed source, proposed-1.0 scope"
    print "> records, provenance, and checksums for reviewer feedback."
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
git -C "$TMP" add .
git -C "$TMP" commit -qm review-metadata

# An extracted review-source archive has no Git metadata. Both the public-state checker and the
# complete version/author checker must accept it anyway.
mv "$TMP/.git" "$TMP/.git.saved"
"$TMP/scripts/check-release-state.sh" review-source "v$version" >/dev/null
"$TMP/scripts/check-version-coherence.sh" review-source "v$version" >/dev/null
mv "$TMP/.git.saved" "$TMP/.git"

git -C "$TMP" tag -a "v$version" -m "pid-rs $version source-review prerelease"
"$TMP/scripts/check-release-state.sh" review-tagged "v$version" >/dev/null
"$TMP/scripts/check-version-coherence.sh" review-tagged "v$version" >/dev/null

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

git -C "$TMP" tag -d "v$version" >/dev/null
git -C "$TMP" tag "v$version"
expect_failure "review-tagged lightweight tag" \
  "$TMP/scripts/check-release-state.sh" review-tagged "v$version"
expect_failure "version checker review-tagged lightweight tag" \
  "$TMP/scripts/check-version-coherence.sh" review-tagged "v$version"
git -C "$TMP" tag -d "v$version" >/dev/null

review_commit="$(git -C "$TMP" rev-parse HEAD)"
misnamed_tag_object="$(
  printf 'object %s\ntype commit\ntag v0.9.1\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\nmisnamed review tag\n' \
    "$review_commit" \
    | git -C "$TMP" hash-object -t tag -w --stdin
)"
git -C "$TMP" update-ref "refs/tags/v$version" "$misnamed_tag_object"
expect_failure "review-tagged mismatched internal name" \
  "$TMP/scripts/check-release-state.sh" review-tagged "v$version"
expect_failure "version checker review-tagged mismatched internal name" \
  "$TMP/scripts/check-version-coherence.sh" review-tagged "v$version"
git -C "$TMP" tag -d "v$version" >/dev/null

inner_tag_object="$(
  printf 'object %s\ntype commit\ntag inner-review\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\ninner review tag\n' \
    "$review_commit" \
    | git -C "$TMP" hash-object -t tag -w --stdin
)"
nested_tag_object="$(
  printf 'object %s\ntype tag\ntag v%s\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\nnested review tag\n' \
    "$inner_tag_object" "$version" \
    | git -C "$TMP" hash-object -t tag -w --stdin
)"
git -C "$TMP" update-ref "refs/tags/v$version" "$nested_tag_object"
expect_failure "review-tagged nested annotated tag" \
  "$TMP/scripts/check-release-state.sh" review-tagged "v$version"
grep --fixed-strings "must directly annotate a commit, not 'tag'" "$TMP/output.log" >/dev/null
expect_failure "version checker review-tagged nested annotated tag" \
  "$TMP/scripts/check-version-coherence.sh" review-tagged "v$version"
grep --fixed-strings "must directly annotate a commit, not 'tag'" "$TMP/output.log" >/dev/null
git -C "$TMP" tag -d "v$version" >/dev/null

signed_tag_object="$(
  printf 'object %s\ntype commit\ntag v%s\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\nreview\n-----BEGIN PGP SIGNATURE-----\nnot-a-real-signature\n-----END PGP SIGNATURE-----\n' \
    "$review_commit" "$version" \
    | git -C "$TMP" hash-object -t tag -w --stdin
)"
git -C "$TMP" update-ref "refs/tags/v$version" "$signed_tag_object"
expect_failure "review-tagged signed annotated tag" \
  "$TMP/scripts/check-release-state.sh" review-tagged "v$version"
grep --fixed-strings "repository policy requires an unsigned annotated tag" \
  "$TMP/output.log" >/dev/null
expect_failure "version checker review-tagged signed annotated tag" \
  "$TMP/scripts/check-version-coherence.sh" review-tagged "v$version"
grep --fixed-strings "repository policy requires an unsigned annotated tag" \
  "$TMP/output.log" >/dev/null
git -C "$TMP" tag -d "v$version" >/dev/null
git -C "$TMP" tag -a "v$version" -m "pid-rs $version source-review prerelease"

# Preserve the v1-only final-source/tagged paths. A synthetic 1.0 transition updates locked package
# metadata and replaces every review-only lifecycle marker with a final-registry state.
git -C "$TMP" tag -d "v$version" >/dev/null
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
git -C "$TMP" add .
git -C "$TMP" commit -qm final-registry-metadata

mv "$TMP/.git" "$TMP/.git.saved"
"$TMP/scripts/check-release-state.sh" final-source "v$final_version" >/dev/null
"$TMP/scripts/check-version-coherence.sh" final-source "v$final_version" >/dev/null
mv "$TMP/.git.saved" "$TMP/.git"

git -C "$TMP" tag -a "v$final_version" -m "v$final_version"
"$TMP/scripts/check-release-state.sh" tagged "v$final_version" >/dev/null
"$TMP/scripts/check-version-coherence.sh" "v$final_version" >/dev/null

final_commit="$(git -C "$TMP" rev-parse HEAD)"
final_inner_tag_object="$(
  printf 'object %s\ntype commit\ntag inner-final\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\ninner final tag\n' \
    "$final_commit" \
    | git -C "$TMP" hash-object -t tag -w --stdin
)"
final_nested_tag_object="$(
  printf 'object %s\ntype tag\ntag v%s\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\nnested final tag\n' \
    "$final_inner_tag_object" "$final_version" \
    | git -C "$TMP" hash-object -t tag -w --stdin
)"
git -C "$TMP" update-ref "refs/tags/v$final_version" "$final_nested_tag_object"
expect_failure "tagged nested annotated tag" \
  "$TMP/scripts/check-release-state.sh" tagged "v$final_version"
expect_failure "version checker tagged nested annotated tag" \
  "$TMP/scripts/check-version-coherence.sh" "v$final_version"
git -C "$TMP" tag -d "v$final_version" >/dev/null

final_misnamed_tag_object="$(
  printf 'object %s\ntype commit\ntag v1.0.1\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\nmisnamed final tag\n' \
    "$final_commit" \
    | git -C "$TMP" hash-object -t tag -w --stdin
)"
git -C "$TMP" update-ref "refs/tags/v$final_version" "$final_misnamed_tag_object"
expect_failure "tagged mismatched internal name" \
  "$TMP/scripts/check-release-state.sh" tagged "v$final_version"
expect_failure "version checker tagged mismatched internal name" \
  "$TMP/scripts/check-version-coherence.sh" "v$final_version"
git -C "$TMP" tag -d "v$final_version" >/dev/null

final_signed_tag_object="$(
  printf 'object %s\ntype commit\ntag v%s\ntagger Release State Self-Test <release-state-self-test.invalid> 0 +0000\n\nfinal\n-----BEGIN PGP SIGNATURE-----\nnot-a-real-signature\n-----END PGP SIGNATURE-----\n' \
    "$final_commit" "$final_version" \
    | git -C "$TMP" hash-object -t tag -w --stdin
)"
git -C "$TMP" update-ref "refs/tags/v$final_version" "$final_signed_tag_object"
expect_failure "tagged signed annotated tag" \
  "$TMP/scripts/check-release-state.sh" tagged "v$final_version"
expect_failure "version checker tagged signed annotated tag" \
  "$TMP/scripts/check-version-coherence.sh" "v$final_version"
git -C "$TMP" tag -d "v$final_version" >/dev/null
git -C "$TMP" tag -a "v$final_version" -m "v$final_version"

sed -i.bak 's/date-released: "2026-07-14"/date-released: "2026-07-13"/' \
  "$TMP/CITATION.cff"
rm "$TMP/CITATION.cff.bak"
expect_failure "final-source CFF/changelog date mismatch" \
  "$TMP/scripts/check-release-state.sh" final-source "v$final_version"
grep --fixed-strings \
  "final-source CFF date '2026-07-13' != CHANGELOG date '2026-07-14'" \
  "$TMP/output.log" >/dev/null

git -C "$TMP" tag -d "v$final_version" >/dev/null
git -C "$TMP" add CITATION.cff
git -C "$TMP" commit -qm mismatched-tagged-metadata
git -C "$TMP" tag -a "v$final_version" -m "v$final_version"
expect_failure "tagged CFF/changelog date mismatch" \
  "$TMP/scripts/check-release-state.sh" tagged "v$final_version"
grep --fixed-strings \
  "tagged CFF date '2026-07-13' != CHANGELOG date '2026-07-14'" \
  "$TMP/output.log" >/dev/null

echo "OK: candidate, review-source, review-tagged, final-source, and tagged states passed; all failure injections were rejected"
