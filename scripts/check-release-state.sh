#!/usr/bin/env bash
# Check that public metadata describes either a candidate tree or an annotated release tag.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/check-release-state.sh candidate
  scripts/check-release-state.sh tagged vMAJOR.MINOR.PATCH

Candidate mode rejects a release date, an existing final tag, present-tense registry claims, and
unqualified downstream compatibility claims. Tagged mode reads metadata from the annotated tag
and requires one coherent final version/date with candidate wording removed.
EOF
}

case "$#:$1" in
  1:candidate)
    MODE=candidate
    TAG=""
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

load_worktree_file() {
  local path="$1"
  [[ -f "$REPO_ROOT/$path" ]] || {
    PROBLEMS+=("missing required file $path")
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

if [[ "$MODE" == tagged ]]; then
  if [[ ! "$TAG" =~ ^v([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    echo "ERROR: tag must match vMAJOR.MINOR.PATCH; got '$TAG'" >&2
    exit 1
  fi
  TAG_VERSION="${BASH_REMATCH[1]}"
  TAG_REF="refs/tags/$TAG"
  git -C "$REPO_ROOT" show-ref --verify --quiet "$TAG_REF" || {
    echo "ERROR: missing exact tag $TAG_REF" >&2
    exit 1
  }
  [[ "$(git -C "$REPO_ROOT" cat-file -t "$TAG_REF")" == tag ]] || {
    echo "ERROR: $TAG_REF is not an annotated tag" >&2
    exit 1
  }
  TAG_COMMIT="$(git -C "$REPO_ROOT" rev-parse --verify "$TAG_REF^{commit}")"
  cargo_text="$(load_tag_file Cargo.toml)"
  cff_text="$(load_tag_file CITATION.cff)"
  changelog_text="$(load_tag_file CHANGELOG.md)"
  readme_text="$(load_tag_file README.md)"
  release_notes_text="$(load_tag_file RELEASE_NOTES.md)"
else
  cargo_text="$(load_worktree_file Cargo.toml)"
  cff_text="$(load_worktree_file CITATION.cff)"
  changelog_text="$(load_worktree_file CHANGELOG.md)"
  readme_text="$(load_worktree_file README.md)"
  release_notes_text="$(load_worktree_file RELEASE_NOTES.md)"
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
[[ "$cff_version" == "$version" ]] \
  || PROBLEMS+=("CITATION.cff version '$cff_version' != Cargo version '$version'")

if [[ "$MODE" == candidate ]]; then
  [[ -z "$cff_date" ]] \
    || PROBLEMS+=("candidate CITATION.cff must omit date-released; found '$cff_date'")
  [[ "$changelog_suffix" == Unreleased ]] \
    || PROBLEMS+=("candidate CHANGELOG entry must be '## [$version] - Unreleased'")
  [[ "$readme_text" == *"Release status: CANDIDATE — not yet published."* ]] \
    || PROBLEMS+=("candidate README lacks the exact candidate status marker")
  [[ "$readme_text" == *"Forthcoming registry installation (not yet available)"* ]] \
    || PROBLEMS+=("candidate README lacks qualified forthcoming installation wording")
  [[ "$readme_text" != *"are distributed through crates.io"* ]] \
    || PROBLEMS+=("candidate README makes an unqualified present-tense crates.io claim")
  [[ "$release_notes_text" == *"Release status: **DRAFT — not yet published**."* ]] \
    || PROBLEMS+=("candidate release notes lack the exact draft status marker")
  [[ "$readme_text" == *"is **not claimed** by this"* ]] \
    || PROBLEMS+=("candidate README does not mark downstream compatibility not claimed")
  if git -C "$REPO_ROOT" show-ref --verify --quiet "refs/tags/v$version"; then
    PROBLEMS+=("candidate mode found existing final tag refs/tags/v$version")
  fi
else
  [[ "$version" == "$TAG_VERSION" ]] \
    || PROBLEMS+=("tag '$TAG' encodes '$TAG_VERSION' but tree version is '$version'")
  [[ "$cff_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] \
    || PROBLEMS+=("tagged CITATION.cff needs an ISO release date; found '$cff_date'")
  [[ -n "$cff_date" && "$changelog_suffix" == "$cff_date" ]] \
    || PROBLEMS+=("tagged CFF date '$cff_date' != CHANGELOG date '$changelog_suffix'")
  [[ "$readme_text" != *"Release status: CANDIDATE"* ]] \
    || PROBLEMS+=("tagged README still claims candidate status")
  [[ "$readme_text" != *"not yet available"* ]] \
    || PROBLEMS+=("tagged README still says registry installation is unavailable")
  [[ "$release_notes_text" != *"Release status: **DRAFT"* ]] \
    || PROBLEMS+=("tagged release notes still claim draft status")
  [[ "$changelog_text" == *"[1.0.0]: https://github.com/sepahead/pid-rs/compare/v0.4.0...v1.0.0"* ]] \
    || PROBLEMS+=("tagged CHANGELOG lacks immutable v0.4.0...v1.0.0 comparison link")
fi

echo "Release state: $MODE"
printf '  %-20s %s\n' version "${version:-<missing>}"
if [[ "$MODE" == tagged ]]; then
  printf '  %-20s %s\n' tag "$TAG"
  printf '  %-20s %s\n' "peeled commit" "$TAG_COMMIT"
  printf '  %-20s %s\n' "release date" "${cff_date:-<missing>}"
fi

if ((${#PROBLEMS[@]})); then
  echo "MISMATCH:" >&2
  printf '  - %s\n' "${PROBLEMS[@]}" >&2
  exit 1
fi

echo "OK: public metadata truthfully matches the $MODE state"
