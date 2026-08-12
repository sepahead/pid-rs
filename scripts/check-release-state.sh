#!/usr/bin/env bash
# Check that public metadata describes a candidate tree, a GitHub-only review prerelease, a
# finalized source archive, or an annotated release tag.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/check-release-state.sh candidate
  scripts/check-release-state.sh review-source vMAJOR.MINOR.PATCH
  scripts/check-release-state.sh review-tagged vMAJOR.MINOR.PATCH
  scripts/check-release-state.sh final-source vMAJOR.MINOR.PATCH
  scripts/check-release-state.sh tagged vMAJOR.MINOR.PATCH

Candidate mode rejects a release date, an existing final tag, present-tense registry claims, and
unqualified downstream compatibility claims. Review-source validates a dated, GitHub-only 0.9.0
source-review prerelease in an extracted source tree without requiring a `.git` directory;
review-tagged applies the same checks to the exact annotated, unsigned tag. Final-source validates
final registry-release metadata in an extracted source tree. Tagged mode applies the same final
metadata checks to the annotated tag tree and additionally verifies the tag object.
EOF
}

case "$#:$1" in
  1:candidate)
    MODE=candidate
    TAG=""
    ;;
  2:review-source)
    MODE=review-source
    TAG="$2"
    ;;
  2:review-tagged)
    MODE=review-tagged
    TAG="$2"
    ;;
  2:final-source)
    MODE=final-source
    TAG="$2"
    ;;
  2:tagged)
    MODE=tagged
    TAG="$2"
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROBLEMS=()
REVIEW_VERSION="0.9.0"
REVIEW_STATUS_MARKER="Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE."
REVIEW_REGISTRY_MARKER="Distribution is GitHub-only: crates.io and PyPI are not published for this 0.9.0 review prerelease."
REVIEW_COMPATIBILITY_MARKER="This 0.9.0 review prerelease makes no 1.x compatibility promise."
REVIEW_DENIAL_MARKER=$'No `v0.9.0` tag or GitHub prerelease is claimed'
PRE_REVIEW_BASELINE="ad489f5bf5e15c164c599d069a6bee0f338c0e48"
FINAL_STATUS_MARKER="Release status: FINAL REGISTRY RELEASE."
REVIEW_LEDGER_PATH="audit/evidence/FILE_REVIEW_LEDGER.csv"
REVIEW_LEDGER_SHA256="54c055943937fca2b0b382118e788b90ad4cbe94a0f57ac71d39de46c72f5778"
REVIEW_SOURCE_OFFER_MARKER="exact source offered for review"
REVIEW_PURPOSE_MARKER="not a completed review."
REVIEW_INVENTORY_MARKER='`UNASSIGNED` and `INVENTORIED_NOT_REVIEWED`'
REVIEW_CLASS_MARKER="identity/coverage metadata"
REVIEW_MODEL_MARKER="not independent human or institutional review"
REVIEW_HISTORY_MARKER="does not rewrite tag history"

workspace_version() {
  awk '
    /^\[workspace\.package\][[:space:]]*$/ { in_section=1; next }
    /^\[/ { in_section=0 }
    in_section && /^[[:space:]]*version[[:space:]]*=/ {
      line=$0
      sub(/^[^=]*=[[:space:]]*"/, "", line)
      sub(/".*/, "", line)
      print line
      exit
    }
  ' <<<"$1"
}

cff_value() {
  local key="$1"
  awk -v key="$key" '$0 ~ "^" key "[[:space:]]*:" {
    line=$0
    sub(/^[^:]*:[[:space:]]*/, "", line)
    gsub(/["\x27]/, "", line)
    sub(/[[:space:]]*#.*/, "", line)
    sub(/[[:space:]]+$/, "", line)
    print line
    exit
  }' <<<"$2"
}

is_iso_calendar_date() {
  local value="$1"
  [[ "$value" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || return 1
  awk -F- '
    {
      year=$1 + 0
      month=$2 + 0
      day=$3 + 0
      days[1]=31; days[2]=28; days[3]=31; days[4]=30
      days[5]=31; days[6]=30; days[7]=31; days[8]=31
      days[9]=30; days[10]=31; days[11]=30; days[12]=31
      if (year % 400 == 0 || (year % 4 == 0 && year % 100 != 0)) days[2]=29
      exit(month >= 1 && month <= 12 && day >= 1 && day <= days[month] ? 0 : 1)
    }
  ' <<<"$value"
}

sha256_file() {
  local path="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -- "$path" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 -- "$path" | awk '{print $1}'
  else
    return 127
  fi
}

cff_has_top_level_software_doi() {
  awk '
    /^[[:alnum:]_-]+[[:space:]]*:/ {
      key=$0
      sub(/[[:space:]]*:.*/, "", key)
      in_identifiers=(key == "identifiers")
      if (key == "doi") found=1
      next
    }
    in_identifiers {
      lower=tolower($0)
      if (lower ~ /^[[:space:]]+(-[[:space:]]*)?type[[:space:]]*:[[:space:]]*["\x27]?doi(["\x27[:space:]#]|$)/) {
        found=1
      }
    }
    END { exit(found ? 0 : 1) }
  ' <<<"$1"
}

cff_has_top_level_zenodo_identifier() {
  awk '
    /^[[:alnum:]_-]+[[:space:]]*:/ {
      key=$0
      sub(/[[:space:]]*:.*/, "", key)
      value=tolower($0)
      sub(/^[^:]*:/, "", value)
      in_identifiers=(key == "identifiers")
      if (key ~ /^(doi|repository|repository-artifact|repository-code|url)$/ && value ~ /zenodo/) {
        found=1
      }
      next
    }
    in_identifiers && tolower($0) ~ /zenodo/ { found=1 }
    END { exit(found ? 0 : 1) }
  ' <<<"$1"
}

load_worktree_file() {
  local path="$1"
  [[ -f "$REPO_ROOT/$path" ]] || {
    PROBLEMS+=("missing required file $path")
    return 0
  }
  [[ ! -L "$REPO_ROOT/$path" ]] || {
    PROBLEMS+=("required source file must not be a symlink: $path")
    return 0
  }
  command cat -- "$REPO_ROOT/$path"
}

load_tag_file() {
  local path="$1"
  git -C "$REPO_ROOT" show "$TAG_COMMIT:$path" 2>/dev/null || {
    PROBLEMS+=("annotated tag tree is missing $path")
    return 0
  }
}

if [[ "$MODE" != candidate ]]; then
  if [[ ! "$TAG" =~ ^v((0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*))$ ]]; then
    echo "ERROR: release reference must match vMAJOR.MINOR.PATCH; got '$TAG'" >&2
    exit 1
  fi
  TAG_VERSION="${BASH_REMATCH[1]}"
fi

if [[ "$MODE" == tagged || "$MODE" == review-tagged ]]; then
  TAG_REF="refs/tags/$TAG"
  git -C "$REPO_ROOT" show-ref --verify --quiet "$TAG_REF" || {
    echo "ERROR: missing exact tag $TAG_REF" >&2
    exit 1
  }
  [[ "$(git -C "$REPO_ROOT" cat-file -t "$TAG_REF")" == tag ]] || {
    echo "ERROR: $TAG_REF is not an annotated tag" >&2
    exit 1
  }
  tag_object="$(git -C "$REPO_ROOT" cat-file tag "$TAG_REF")"
  embedded_object_type="$(awk '/^type / { sub(/^type /, ""); print; exit }' <<<"$tag_object")"
  [[ "$embedded_object_type" == commit ]] || {
    echo "ERROR: $TAG_REF must directly annotate a commit, not '$embedded_object_type'" >&2
    exit 1
  }
  embedded_tag="$(awk '/^tag / { sub(/^tag /, ""); print; exit }' <<<"$tag_object")"
  [[ "$embedded_tag" == "$TAG" ]] || {
    echo "ERROR: $TAG_REF points to an annotated tag object named '$embedded_tag', not '$TAG'" >&2
    exit 1
  }
  if grep -Eq -- '-----BEGIN (PGP|SSH) SIGNATURE-----|-----BEGIN SIGNED MESSAGE-----' \
    <<<"$tag_object"; then
    echo "ERROR: $TAG_REF is signed; repository policy requires an unsigned annotated tag" >&2
    exit 1
  fi
  TAG_COMMIT="$(git -C "$REPO_ROOT" rev-parse --verify "$TAG_REF^{commit}")"
  for required_tag_file in \
    Cargo.toml CITATION.cff CHANGELOG.md README.md RELEASE_NOTES.md RELEASE_REPRODUCTION.md
  do
    tree_entry="$(git -C "$REPO_ROOT" ls-tree "$TAG_COMMIT" -- "$required_tag_file")"
    read -r tree_mode tree_type _tree_object _tree_path <<<"$tree_entry"
    if [[ "$tree_type" != blob \
      || ("$tree_mode" != 100644 && "$tree_mode" != 100755) ]]; then
      PROBLEMS+=("required tagged file must be a regular blob: $required_tag_file")
    fi
  done
  cargo_text="$(load_tag_file Cargo.toml)"
  cff_text="$(load_tag_file CITATION.cff)"
  changelog_text="$(load_tag_file CHANGELOG.md)"
  readme_text="$(load_tag_file README.md)"
  release_notes_text="$(load_tag_file RELEASE_NOTES.md)"
  reproduction_text="$(load_tag_file RELEASE_REPRODUCTION.md)"
else
  for required_source_file in \
    Cargo.toml CITATION.cff CHANGELOG.md README.md RELEASE_NOTES.md RELEASE_REPRODUCTION.md
  do
    [[ -f "$REPO_ROOT/$required_source_file" ]] \
      || PROBLEMS+=("missing required file $required_source_file")
    [[ ! -L "$REPO_ROOT/$required_source_file" ]] \
      || PROBLEMS+=("required source file must not be a symlink: $required_source_file")
  done
  cargo_text="$(load_worktree_file Cargo.toml)"
  cff_text="$(load_worktree_file CITATION.cff)"
  changelog_text="$(load_worktree_file CHANGELOG.md)"
  readme_text="$(load_worktree_file README.md)"
  release_notes_text="$(load_worktree_file RELEASE_NOTES.md)"
  reproduction_text="$(load_worktree_file RELEASE_REPRODUCTION.md)"
fi

version="$(workspace_version "$cargo_text")"
cff_version="$(cff_value version "$cff_text")"
cff_date="$(cff_value date-released "$cff_text")"
changelog_suffix="$(awk -v version="$version" '
  index($0, "## [" version "] - ") == 1 {
    sub("^## \\[" version "\\] - ", "")
    print
    exit
  }
' <<<"$changelog_text")"

[[ -n "$version" ]] || PROBLEMS+=("Cargo.toml has no workspace version")
[[ "$version" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] \
  || PROBLEMS+=("Cargo.toml workspace version is not exact SemVer: '$version'")
[[ "$cff_version" == "$version" ]] \
  || PROBLEMS+=("CITATION.cff version '$cff_version' != Cargo version '$version'")

if [[ "$MODE" == candidate ]]; then
  [[ -z "$cff_date" ]] \
    || PROBLEMS+=("candidate CITATION.cff must omit date-released; found '$cff_date'")
  [[ "$changelog_suffix" == Unreleased ]] \
    || PROBLEMS+=("candidate CHANGELOG entry must be '## [$version] - Unreleased'")
  [[ "$readme_text" == *"Release status: CANDIDATE — not yet published."* ]] \
    || PROBLEMS+=("candidate README lacks the exact candidate status marker")
  [[ "$readme_text" == *"## Source use and registry status"* ]] \
    || PROBLEMS+=("candidate README lacks the source-use and registry-status section")
  [[ "$readme_text" == *"Version $version is not being published to crates.io or PyPI"* ]] \
    || PROBLEMS+=("candidate README does not explicitly withhold crates.io and PyPI publication")
  [[ "$readme_text" != *"are distributed through crates.io"* ]] \
    || PROBLEMS+=("candidate README makes an unqualified present-tense crates.io claim")
  [[ "$release_notes_text" == *"Release status: **DRAFT — not yet published**."* ]] \
    || PROBLEMS+=("candidate release notes lack the exact draft status marker")
  [[ "$reproduction_text" == *"Release status: **CANDIDATE.**"* ]] \
    || PROBLEMS+=("candidate reproduction guide lacks the exact candidate status marker")
  [[ "$readme_text" == *"is **not claimed** by this"* ]] \
    || PROBLEMS+=("candidate README does not mark downstream compatibility not claimed")
  if git -C "$REPO_ROOT" show-ref --verify --quiet "refs/tags/v$version"; then
    PROBLEMS+=("candidate mode found existing final tag refs/tags/v$version")
  fi
elif [[ "$MODE" == review-source || "$MODE" == review-tagged ]]; then
  if [[ "$MODE" == review-tagged ]]; then
    review_label=review-tagged
    reference_label=tag
  else
    review_label=review-source
    reference_label="review release reference"
  fi
  [[ "$version" == "$TAG_VERSION" ]] \
    || PROBLEMS+=("$reference_label '$TAG' encodes '$TAG_VERSION' but tree version is '$version'")
  [[ "$version" == "$REVIEW_VERSION" ]] \
    || PROBLEMS+=("$review_label is reserved for exact version '$REVIEW_VERSION'; found '$version'")
  is_iso_calendar_date "$cff_date" \
    || PROBLEMS+=("$review_label CITATION.cff needs a valid ISO release date; found '$cff_date'")
  [[ -n "$cff_date" && "$changelog_suffix" == "$cff_date" ]] \
    || PROBLEMS+=("$review_label CFF date '$cff_date' != CHANGELOG date '$changelog_suffix'")
  [[ "$readme_text" == *"$REVIEW_STATUS_MARKER"* ]] \
    || PROBLEMS+=("$review_label README lacks the exact review-prerelease status marker")
  [[ "$release_notes_text" == *"$REVIEW_STATUS_MARKER"* ]] \
    || PROBLEMS+=("$review_label release notes lack the exact review-prerelease status marker")
  [[ "$reproduction_text" == *"$REVIEW_STATUS_MARKER"* ]] \
    || PROBLEMS+=("$review_label reproduction guide lacks the exact review-prerelease status marker")
  [[ "$readme_text" != *"Release status: CANDIDATE"* ]] \
    || PROBLEMS+=("$review_label README still claims candidate status")
  [[ "$release_notes_text" != *"Release status: **DRAFT"* ]] \
    || PROBLEMS+=("$review_label release notes still claim draft status")
  [[ "$reproduction_text" != *"Release status: **CANDIDATE.**"* ]] \
    || PROBLEMS+=("$review_label reproduction guide still claims candidate status")
  [[ "$reproduction_text" != *"$REVIEW_DENIAL_MARKER"* ]] \
    || PROBLEMS+=("$review_label reproduction guide still denies the published tag and prerelease")
  [[ "$readme_text" == *"$REVIEW_REGISTRY_MARKER"* ]] \
    || PROBLEMS+=("$review_label README lacks the exact GitHub-only registry non-publication marker")
  [[ "$release_notes_text" == *"$REVIEW_REGISTRY_MARKER"* ]] \
    || PROBLEMS+=("$review_label release notes lack the exact GitHub-only registry non-publication marker")
  [[ "$readme_text" == *"$REVIEW_COMPATIBILITY_MARKER"* ]] \
    || PROBLEMS+=("$review_label README lacks the exact 1.x compatibility non-promise")
  [[ "$release_notes_text" == *"$REVIEW_COMPATIBILITY_MARKER"* ]] \
    || PROBLEMS+=("$review_label release notes lack the exact 1.x compatibility non-promise")
  [[ "$readme_text" != *"are distributed through crates.io"* ]] \
    || PROBLEMS+=("$review_label README makes an unqualified present-tense crates.io claim")
  if cff_has_top_level_software_doi "$cff_text"; then
    PROBLEMS+=("$review_label CITATION.cff declares a top-level software DOI")
  fi
  if cff_has_top_level_zenodo_identifier "$cff_text"; then
    PROBLEMS+=("$review_label CITATION.cff declares a top-level Zenodo identifier")
  fi
  [[ "$changelog_text" == *"[$version]: https://github.com/sepahead/pid-rs/compare/$PRE_REVIEW_BASELINE...v$version"* ]] \
    || PROBLEMS+=("$review_label CHANGELOG lacks its immutable pre-review-commit comparison link")
  if [[ "$MODE" == review-source ]]; then
    for source_truth_marker in \
      "$REVIEW_SOURCE_OFFER_MARKER" \
      "$REVIEW_PURPOSE_MARKER" \
      "$REVIEW_INVENTORY_MARKER" \
      "$REVIEW_CLASS_MARKER" \
      "$REVIEW_MODEL_MARKER" \
      "$REVIEW_HISTORY_MARKER"
    do
      [[ "$readme_text" == *"$source_truth_marker"* ]] \
        || PROBLEMS+=("review-source README lacks review-evidence boundary: $source_truth_marker")
      [[ "$release_notes_text" == *"$source_truth_marker"* ]] \
        || PROBLEMS+=("review-source release notes lack review-evidence boundary: $source_truth_marker")
    done
    if grep -Eiq -- '(^|[^[:alnum:]_])(reviewed|audited|certified)[[:space:]]+source([^[:alnum:]_]|$)|review provenance' \
      <<<"$readme_text"; then
      PROBLEMS+=("review-source README promotes source-offer or inventory evidence into completed review")
    fi
    if grep -Eiq -- '(^|[^[:alnum:]_])(reviewed|audited|certified)[[:space:]]+source([^[:alnum:]_]|$)|review provenance' \
      <<<"$release_notes_text"; then
      PROBLEMS+=("review-source release notes promote source-offer or inventory evidence into completed review")
    fi
    ledger="$REPO_ROOT/$REVIEW_LEDGER_PATH"
    if [[ ! -f "$ledger" || -L "$ledger" ]]; then
      PROBLEMS+=("review-source tag-file inventory must be a regular non-symlink file: $REVIEW_LEDGER_PATH")
    else
      ledger_sha256="$(sha256_file "$ledger" 2>/dev/null || true)"
      [[ -n "$ledger_sha256" ]] \
        || PROBLEMS+=("review-source needs sha256sum or shasum to verify the tag-file inventory")
      [[ "$ledger_sha256" == "$REVIEW_LEDGER_SHA256" ]] \
        || PROBLEMS+=("review-source tag-file inventory bytes differ from the protected baseline")
    fi
  else
    # These are exact historical publication bytes, not an endorsement of their old review label.
    [[ "$readme_text" == *"It provides the exact reviewed source"* ]] \
      || PROBLEMS+=("review-tagged README differs from the immutable historical review wording")
    [[ "$release_notes_text" == *"limited to the reviewed source archive"* ]] \
      || PROBLEMS+=("review-tagged release notes differ from the immutable historical review wording")
  fi
else
  if [[ "$MODE" == tagged ]]; then
    final_label=tagged
    reference_label=tag
  else
    final_label=final-source
    reference_label="release reference"
  fi
  [[ "$version" == "$TAG_VERSION" ]] \
    || PROBLEMS+=("$reference_label '$TAG' encodes '$TAG_VERSION' but tree version is '$version'")
  [[ "$TAG_VERSION" =~ ^[1-9][0-9]*\. ]] \
    || PROBLEMS+=("$final_label is reserved for version 1.0.0 or later; found '$TAG_VERSION'")
  is_iso_calendar_date "$cff_date" \
    || PROBLEMS+=("$final_label CITATION.cff needs an ISO release date; found '$cff_date'")
  [[ -n "$cff_date" && "$changelog_suffix" == "$cff_date" ]] \
    || PROBLEMS+=("$final_label CFF date '$cff_date' != CHANGELOG date '$changelog_suffix'")
  [[ "$readme_text" != *"Release status: CANDIDATE"* ]] \
    || PROBLEMS+=("$final_label README still claims candidate status")
  [[ "$readme_text" != *"not yet available"* ]] \
    || PROBLEMS+=("$final_label README still says registry installation is unavailable")
  [[ "$release_notes_text" != *"Release status: **DRAFT"* ]] \
    || PROBLEMS+=("$final_label release notes still claim draft status")
  [[ "$changelog_text" == *"[$version]: https://github.com/sepahead/pid-rs/compare/$PRE_REVIEW_BASELINE...v$version"* ]] \
    || PROBLEMS+=("$final_label CHANGELOG lacks its immutable pre-review-commit comparison link")
  [[ "$readme_text" == *"$FINAL_STATUS_MARKER"* ]] \
    || PROBLEMS+=("$final_label README lacks the exact final-release status marker")
  [[ "$release_notes_text" == *"$FINAL_STATUS_MARKER"* ]] \
    || PROBLEMS+=("$final_label release notes lack the exact final-release status marker")
  [[ "$reproduction_text" == *"$FINAL_STATUS_MARKER"* ]] \
    || PROBLEMS+=("$final_label reproduction guide lacks the exact final-release status marker")
  for review_only_marker in \
    "$REVIEW_STATUS_MARKER" "$REVIEW_REGISTRY_MARKER" "$REVIEW_COMPATIBILITY_MARKER"; do
    [[ "$readme_text" != *"$review_only_marker"* ]] \
      || PROBLEMS+=("$final_label README retains review-only text: $review_only_marker")
    [[ "$release_notes_text" != *"$review_only_marker"* ]] \
      || PROBLEMS+=("$final_label release notes retain review-only text: $review_only_marker")
  done
fi

echo "Release state: $MODE"
printf '  %-20s %s\n' version "${version:-<missing>}"
if [[ "$MODE" == tagged || "$MODE" == review-tagged ]]; then
  printf '  %-20s %s\n' tag "$TAG"
  printf '  %-20s %s\n' "peeled commit" "$TAG_COMMIT"
  printf '  %-20s %s\n' "release date" "${cff_date:-<missing>}"
elif [[ "$MODE" == final-source || "$MODE" == review-source ]]; then
  printf '  %-20s %s\n' "release reference" "$TAG"
  printf '  %-20s %s\n' "release date" "${cff_date:-<missing>}"
fi

if ((${#PROBLEMS[@]})); then
  echo "MISMATCH:" >&2
  printf '  - %s\n' "${PROBLEMS[@]}" >&2
  exit 1
fi

if [[ "$MODE" == review-tagged ]]; then
  echo "OK: immutable historical v0.9.0 metadata matches its publication record; no completed review is inferred"
else
  echo "OK: public metadata truthfully matches the $MODE state"
fi
