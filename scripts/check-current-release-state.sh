#!/usr/bin/env bash
# Select the release-state checker from explicit metadata and the current Git ref.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

version="$({
  awk '
    /^\[workspace\.package\][[:space:]]*$/ { in_section=1; next }
    /^\[/ { in_section=0 }
    in_section && /^[[:space:]]*version[[:space:]]*=/ {
      line=$0
      sub(/^[^"]*"/, "", line)
      sub(/".*/, "", line)
      print line
      exit
    }
  ' "$REPO_ROOT/Cargo.toml"
} || true)"
[[ "$version" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] || {
  echo "ERROR: cannot select release state without an exact workspace SemVer" >&2
  exit 1
}

review_marker='Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE.'
candidate_marker='Release status: CANDIDATE — not yet published.'
final_marker='Release status: FINAL REGISTRY RELEASE.'
readme="$REPO_ROOT/README.md"

state=""
matches=0
if grep -Fq "$candidate_marker" "$readme"; then state=candidate; ((matches += 1)); fi
if grep -Fq "$review_marker" "$readme"; then state=review; ((matches += 1)); fi
if grep -Fq "$final_marker" "$readme"; then state=final; ((matches += 1)); fi
if [[ "$matches" -ne 1 ]]; then
  echo "ERROR: README must contain exactly one recognized release-state marker" >&2
  exit 1
fi

tag="v$version"
tagged=false
repository_git_root=""
if [[ -z "${GITHUB_REF_TYPE:-}" ]]; then
  repository_git_root="$(git -C "$REPO_ROOT" rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ -n "$repository_git_root" ]]; then
    repository_git_root="$(cd "$repository_git_root" 2>/dev/null && pwd -P || true)"
  fi
fi
if [[ "${GITHUB_REF_TYPE:-}" == tag ]]; then
  [[ "${GITHUB_REF_NAME:-}" == "$tag" ]] || {
    echo "ERROR: tag event '${GITHUB_REF_NAME:-<missing>}' does not match workspace $tag" >&2
    exit 1
  }
  tagged=true
elif [[ -z "${GITHUB_REF_TYPE:-}" ]] \
  && [[ "$repository_git_root" == "$REPO_ROOT" ]] \
  && git -C "$REPO_ROOT" show-ref --verify --quiet "refs/tags/$tag" \
  && [[ "$(git -C "$REPO_ROOT" rev-parse "refs/tags/$tag^{commit}")" \
    == "$(git -C "$REPO_ROOT" rev-parse HEAD)" ]] \
  && [[ -z "$(git -C "$REPO_ROOT" status --porcelain=v2 --untracked-files=all)" ]]; then
  tagged=true
fi

case "$state:$tagged" in
  candidate:true)
    echo "ERROR: candidate metadata cannot be validated as a release tag" >&2
    exit 1
    ;;
  candidate:false)
    "$SCRIPT_DIR/check-version-coherence.sh"
    ;;
  review:true)
    "$SCRIPT_DIR/check-version-coherence.sh" review-tagged "$tag"
    ;;
  review:false)
    "$SCRIPT_DIR/check-version-coherence.sh" review-source "$tag"
    ;;
  final:true)
    "$SCRIPT_DIR/check-version-coherence.sh" "$tag"
    ;;
  final:false)
    "$SCRIPT_DIR/check-version-coherence.sh" final-source "$tag"
    ;;
esac
