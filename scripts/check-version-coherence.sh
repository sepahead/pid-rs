#!/usr/bin/env bash
# check-version-coherence.sh — assert this repo's release version is coherent
# across every place it is recorded, and optionally that an exact local release
# tag points at a tree whose required version metadata matches the tag name.
#
# READ-ONLY: this script never writes to the repo, runs no builds, and performs
# no network calls. It only reads tracked files and (for the optional tag check)
# the local git object database.
#
# What "coherent" means here:
#   - the Cargo workspace package version (Cargo.toml [workspace.package].version,
#     falling back to [package].version for a single-crate repo)
#   - the npm package.json "version" (where a package.json is present)
#   - the CITATION.cff "version"
#   must all be byte-equal. A release that bumps one but forgets another is the
#   classic stale-metadata footgun this guard exists to catch.
#
# With an optional <tag> argument it instead checks the tagged tree and asserts:
#   - the argument is exactly `vMAJOR.MINOR.PATCH`,
#   - the exact local `refs/tags/<tag>` exists and peels to a commit, and
#   - that commit's required Cargo.toml and CITATION.cff versions (plus an npm
#     package.json version when present) equal the tag's version.
#
# Usage:
#   scripts/check-version-coherence.sh [tag]
#
# Exit codes: 0 = coherent; 1 = mismatch / missing required file; 2 = bad usage.

set -euo pipefail

usage() {
  cat <<'EOF'
check-version-coherence.sh — assert release-version coherence (read-only).

Usage:
  check-version-coherence.sh [tag]

  tag   Optional. An exact release tag (e.g. v0.2.8). When given, the script
        verifies refs/tags/<tag>, then reads version metadata from that tagged
        tree rather than from the current working tree.

With no tag, the script only asserts internal coherence in the working tree.

Exit codes: 0 = coherent; 1 = mismatch / missing required file; 2 = bad usage.
EOF
}

TAG=""
for arg in "$@"; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
    -*)        echo "ERROR: unknown option '$arg'" >&2; echo >&2; usage >&2; exit 2 ;;
    *)
      if [[ -n "$TAG" ]]; then
        echo "ERROR: too many arguments" >&2; echo >&2; usage >&2; exit 2
      fi
      TAG="$arg" ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- version extractors (read-only; first match wins) -----------------------

cargo_version_from_stream() {
  awk '
    /^\[workspace\.package\]/ { sec="wp"; next }
    /^\[package\]/            { sec="pkg"; next }
    /^\[/                     { sec="" ; next }
    (sec=="wp" || sec=="pkg") && /^[[:space:]]*version[[:space:]]*=/ {
      line=$0
      sub(/^[^=]*=[[:space:]]*/, "", line)
      gsub(/["\x27]/, "", line)        # strip both " and single quote
      sub(/[[:space:]].*$/, "", line)  # drop trailing comment/space
      print line
      exit
    }
  '
}

npm_version_from_stream() {
  awk -F'"' '/^[[:space:]]*"version"[[:space:]]*:/ { print $4; exit }'
}

cff_version_from_stream() {
  awk '
    /^version[[:space:]]*:/ {
      line=$0
      sub(/^version[[:space:]]*:[[:space:]]*/, "", line)
      gsub(/["\x27]/, "", line)
      sub(/[[:space:]]*#.*$/, "", line)
      sub(/[[:space:]]+$/, "", line)
      print line
      exit
    }
  '
}

# Cargo: prefer the workspace package version, else a single-crate [package].
# We look in the repo-root Cargo.toml first, then src-tauri/Cargo.toml (Tauri
# apps keep the crate manifest there).
cargo_version() {
  local f
  for f in "$REPO_ROOT/Cargo.toml" "$REPO_ROOT/src-tauri/Cargo.toml"; do
    [[ -f "$f" ]] || continue
    cargo_version_from_stream <"$f"
    return
  done
}

# npm: package.json "version": "x.y.z"
npm_version() {
  local f="$REPO_ROOT/package.json"
  [[ -f "$f" ]] || return
  npm_version_from_stream <"$f"
}

# CITATION.cff: a top-level `version:` key. Values may be quoted or bare.
cff_version() {
  local f="$REPO_ROOT/CITATION.cff"
  [[ -f "$f" ]] || return
  cff_version_from_stream <"$f"
}

# Tag mode intentionally does not inspect the working tree. This permits a
# maintainer to validate an older release tag while preparing a later release,
# and prevents dirty/uncommitted metadata from standing in for tagged content.
if [[ -n "$TAG" ]]; then
  echo "Version coherence (repo: $REPO_ROOT)"
  echo

  if [[ ! "$TAG" =~ ^v([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    echo "ERROR: tag must match exactly vMAJOR.MINOR.PATCH; got '$TAG'" >&2
    exit 1
  fi
  TAG_VER="${BASH_REMATCH[1]}"

  if ! git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: not inside a git work tree; cannot check tag '$TAG'" >&2
    exit 1
  fi

  TAG_REF="refs/tags/$TAG"
  if ! git -C "$REPO_ROOT" show-ref --verify --quiet "$TAG_REF"; then
    echo "ERROR: exact local tag '$TAG_REF' does not exist" >&2
    exit 1
  fi
  if ! PEELED_COMMIT="$(git -C "$REPO_ROOT" rev-parse --verify "${TAG_REF}^{commit}" 2>/dev/null)"; then
    echo "ERROR: exact local tag '$TAG_REF' does not peel to a commit" >&2
    exit 1
  fi

  tagged_problems=()
  TAG_CARGO_VER=""
  TAG_CFF_VER=""
  TAG_NPM_VER=""

  if TAG_CARGO_TOML="$(git -C "$REPO_ROOT" show "${PEELED_COMMIT}:Cargo.toml" 2>/dev/null)"; then
    TAG_CARGO_VER="$(cargo_version_from_stream <<<"$TAG_CARGO_TOML" || true)"
    if [[ -z "$TAG_CARGO_VER" ]]; then
      tagged_problems+=("tagged Cargo.toml has no [workspace.package] or [package] version")
    fi
  else
    tagged_problems+=("tagged tree is missing required Cargo.toml")
  fi

  if TAG_CITATION="$(git -C "$REPO_ROOT" show "${PEELED_COMMIT}:CITATION.cff" 2>/dev/null)"; then
    TAG_CFF_VER="$(cff_version_from_stream <<<"$TAG_CITATION" || true)"
    if [[ -z "$TAG_CFF_VER" ]]; then
      tagged_problems+=("tagged CITATION.cff has no top-level version")
    fi
  else
    tagged_problems+=("tagged tree is missing required CITATION.cff")
  fi

  if git -C "$REPO_ROOT" cat-file -e "${PEELED_COMMIT}:package.json" 2>/dev/null; then
    if TAG_PACKAGE_JSON="$(git -C "$REPO_ROOT" show "${PEELED_COMMIT}:package.json" 2>/dev/null)"; then
      TAG_NPM_VER="$(npm_version_from_stream <<<"$TAG_PACKAGE_JSON" || true)"
      if [[ -z "$TAG_NPM_VER" ]]; then
        tagged_problems+=("tagged package.json has no version")
      fi
    else
      tagged_problems+=("could not read tagged package.json")
    fi
  fi

  printf '  %-22s %s\n' "tag" "$TAG"
  printf '  %-22s %s\n' "peeled commit" "$PEELED_COMMIT"
  printf '  %-22s %s\n' "Cargo (tagged tree)" "${TAG_CARGO_VER:-<missing>}"
  printf '  %-22s %s\n' "CITATION.cff" "${TAG_CFF_VER:-<missing>}"
  if [[ -n "$TAG_NPM_VER" ]]; then
    printf '  %-22s %s\n' "npm (package.json)" "$TAG_NPM_VER"
  fi
  echo

  [[ -z "$TAG_CARGO_VER" || "$TAG_CARGO_VER" == "$TAG_VER" ]] \
    || tagged_problems+=("tag '$TAG' encodes '$TAG_VER' but tagged Cargo.toml records '$TAG_CARGO_VER'")
  [[ -z "$TAG_CFF_VER" || "$TAG_CFF_VER" == "$TAG_VER" ]] \
    || tagged_problems+=("tag '$TAG' encodes '$TAG_VER' but tagged CITATION.cff records '$TAG_CFF_VER'")
  [[ -z "$TAG_NPM_VER" || "$TAG_NPM_VER" == "$TAG_VER" ]] \
    || tagged_problems+=("tag '$TAG' encodes '$TAG_VER' but tagged package.json records '$TAG_NPM_VER'")

  if [[ "${#tagged_problems[@]}" -ne 0 ]]; then
    echo "MISMATCH:" >&2
    for problem in "${tagged_problems[@]}"; do
      echo "  - $problem" >&2
    done
    exit 1
  fi

  echo "OK: required versions in '$TAG_REF' are coherent at '$TAG_VER'"
  exit 0
fi

CARGO_VER="$(cargo_version || true)"
NPM_VER="$(npm_version || true)"
CFF_VER="$(cff_version || true)"

echo "Version coherence (repo: $REPO_ROOT)"
echo
printf '  %-22s %s\n' "Cargo (workspace/pkg)" "${CARGO_VER:-<not present>}"
printf '  %-22s %s\n' "npm (package.json)"     "${NPM_VER:-<not present>}"
printf '  %-22s %s\n' "CITATION.cff"           "${CFF_VER:-<not present>}"
echo

problems=()

if [[ ! -f "$REPO_ROOT/Cargo.toml" || -z "$CARGO_VER" ]]; then
  problems+=("required root Cargo.toml is missing or has no workspace/package version")
fi
if [[ ! -f "$REPO_ROOT/CITATION.cff" || -z "$CFF_VER" ]]; then
  problems+=("required CITATION.cff is missing or has no top-level version")
fi

# Cargo.toml and CITATION.cff are required sources of truth in pid-rs; package.json remains
# optional. Every present source must agree.
present_labels=()
present_values=()
[[ -n "$CARGO_VER" ]] && { present_labels+=("Cargo"); present_values+=("$CARGO_VER"); }
[[ -n "$NPM_VER"   ]] && { present_labels+=("npm");   present_values+=("$NPM_VER"); }
[[ -n "$CFF_VER"   ]] && { present_labels+=("CITATION.cff"); present_values+=("$CFF_VER"); }

if [[ "${#present_values[@]}" -eq 0 ]]; then
  echo "ERROR: no version source found (no Cargo.toml / package.json / CITATION.cff version)" >&2
  exit 1
fi

CANON="${present_values[0]}"
for i in "${!present_values[@]}"; do
  if [[ "${present_values[$i]}" != "$CANON" ]]; then
    problems+=("${present_labels[$i]} version '${present_values[$i]}' != '${CANON}' (${present_labels[0]})")
  fi
done

if [[ "${#problems[@]}" -ne 0 ]]; then
  echo "MISMATCH:" >&2
  for p in "${problems[@]}"; do
    echo "  - $p" >&2
  done
  exit 1
fi

echo "OK: versions coherent at '$CANON'"
