#!/usr/bin/env bash
# (Consumer repo renamed pid_vla -> prisoma at its docset v10.4; this script tracks the new name.)
# Bump prisoma's `pid-rs` git submodule to a target pid-rs tag and refresh prisoma's
# root Cargo.lock so the path-deps (pid-core / pid-runlog) re-resolve to the new version.
#
# WHY an explicit fetch + checkout (and NOT `git submodule update --remote`):
# prisoma's `pid-rs` submodule history DIVERGED from canonical sepahead/pid-rs — the prior
# pin was not an ancestor of canonical `main`. `git submodule update --remote` resolves the
# branch tip recorded in .gitmodules and fast-forwards; with a diverged history that either
# fails or lands on the wrong commit. We instead verify the exact annotated tag object and peeled
# commit against canonical origin, fetch only that tag into a temporary ref, and check out its
# commit, which is unambiguous regardless of ancestry. (Ancestry to the submodule's recorded
# branch is intentionally irrelevant here.)
#
# This script does NOT commit or push. It stages the gitlink (`git add pid-rs`) and the
# refreshed Cargo.lock, then prints the gitlink change and a suggested commit for the
# maintainer to run by hand.
#
# Usage:
#   scripts/repin-pidrs.sh <tag> [prisoma-dir]
#
#   <tag>          A pid-rs tag to pin the submodule to, e.g. v0.9.0.
#   [prisoma-dir]  Path to the prisoma checkout. Defaults to the sibling `prisoma`
#                  directory next to this pid-rs checkout (resolved from this script's
#                  location), i.e. the standard sepahead-github sibling layout.
set -euo pipefail

# ---- argument validation -----------------------------------------------------------------
if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $(basename "$0") <tag> [prisoma-dir]" >&2
  exit 2
fi

TAG="$1"
if [[ ! "$TAG" =~ ^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]]; then
  echo "ERROR: <tag> must be an exact vMAJOR.MINOR.PATCH pid-rs tag (e.g. v0.9.0)." >&2
  exit 2
fi

# Resolve prisoma dir: explicit arg, else the sibling `prisoma` of this pid-rs checkout.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDRS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"          # the pid-rs checkout this script ships in
DEFAULT_VLA="$(cd "$PIDRS_ROOT/.." && pwd)/prisoma" # sibling under sepahead-github/

VLA="${2:-$DEFAULT_VLA}"
if [[ ! -d "$VLA" ]]; then
  echo "ERROR: prisoma directory not found: $VLA" >&2
  echo "       Pass the path explicitly: $(basename "$0") $TAG /path/to/prisoma" >&2
  exit 2
fi
VLA="$(cd "$VLA" && pwd)"

if ! git -C "$VLA" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: $VLA is not a git work tree." >&2
  exit 2
fi

SUB="$VLA/pid-rs"
# An initialized submodule has a `.git` *file* (gitdir pointer into .git/modules/...) or,
# in older layouts, a `.git` directory. `-e` covers both; bare `-d` would miss the file.
if [[ ! -e "$SUB/.git" ]]; then
  echo "ERROR: $SUB is not an initialized git submodule (.git missing)." >&2
  echo "       Run: git -C \"$VLA\" submodule update --init" >&2
  exit 2
fi
if ! git -C "$SUB" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: $SUB is not a usable git work tree." >&2
  echo "       Run: git -C \"$VLA\" submodule update --init" >&2
  exit 2
fi

CANONICAL_REMOTE="https://github.com/sepahead/pid-rs.git"
configured_remote="$(git -C "$SUB" config --get remote.origin.url || true)"
resolved_remote="$(git -C "$SUB" remote get-url origin 2>/dev/null || true)"
if [[ "$configured_remote" != "$CANONICAL_REMOTE" \
  || "$resolved_remote" != "$CANONICAL_REMOTE" ]]; then
  echo "ERROR: pid-rs submodule origin must be $CANONICAL_REMOTE" >&2
  echo "       configured origin: ${configured_remote:-<missing>}" >&2
  echo "       resolved origin: ${resolved_remote:-<missing>}" >&2
  exit 1
fi
gitmodules_remote="$(
  git -C "$VLA" config -f .gitmodules --get submodule.pid-rs.url 2>/dev/null || true
)"
if [[ "$gitmodules_remote" != "$CANONICAL_REMOTE" ]]; then
  echo "ERROR: .gitmodules submodule.pid-rs.url must be $CANONICAL_REMOTE" >&2
  echo "       configured URL: ${gitmodules_remote:-<missing>}" >&2
  exit 1
fi
head_gitmodules_remote="$(
  git -C "$VLA" config --blob HEAD:.gitmodules \
    --get submodule.pid-rs.url 2>/dev/null || true
)"
if [[ "$head_gitmodules_remote" != "$CANONICAL_REMOTE" ]]; then
  echo "ERROR: HEAD:.gitmodules submodule.pid-rs.url must be $CANONICAL_REMOTE" >&2
  echo "       committed URL: ${head_gitmodules_remote:-<missing>}" >&2
  exit 1
fi
if [[ -n "$(git -C "$SUB" status --porcelain=v2 --untracked-files=all)" ]]; then
  echo "ERROR: pid-rs submodule has local changes; refusing to replace its checkout." >&2
  exit 1
fi
if [[ -n "$(git -C "$VLA" status --porcelain=v2 --untracked-files=all -- \
  .gitmodules pid-rs Cargo.lock)" ]]; then
  echo "ERROR: prisoma has existing .gitmodules/pid-rs/Cargo.lock changes; refusing to mix them." >&2
  exit 1
fi
gitlink_record="$(git -C "$VLA" ls-tree HEAD -- pid-rs)"
if [[ ! "$gitlink_record" =~ ^160000[[:space:]]commit[[:space:]][0-9a-f]{40}[[:space:]]pid-rs$ ]]; then
  echo "ERROR: prisoma HEAD does not record pid-rs as a root gitlink." >&2
  exit 1
fi
if ! command -v cargo >/dev/null 2>&1; then
  echo "ERROR: cargo not found on PATH; cannot refresh the root Cargo.lock." >&2
  exit 1
fi

echo "==> Re-pinning prisoma submodule pid-rs -> $TAG"
echo "    prisoma : $VLA"
echo "    submod  : $SUB"

# ---- record the before-state for the diff summary ----------------------------------------
BEFORE_SHA="$(git -C "$SUB" rev-parse HEAD)"

# ---- live tag verification + exact fetch (NEVER `git submodule update --remote`) ----------
echo "==> Verifying the exact annotated tag on canonical origin ..."
remote_tag_lines="$(
  git -C "$SUB" ls-remote origin "refs/tags/$TAG" "refs/tags/$TAG^{}"
)"
remote_tag_object="$(
  awk -v ref="refs/tags/$TAG" '$2 == ref { print $1 }' <<<"$remote_tag_lines"
)"
remote_peeled_commit="$(
  awk -v ref="refs/tags/$TAG^{}" '$2 == ref { print $1 }' <<<"$remote_tag_lines"
)"
if [[ ! "$remote_tag_object" =~ ^[0-9a-f]{40}$ \
  || ! "$remote_peeled_commit" =~ ^[0-9a-f]{40}$ \
  || "$remote_tag_object" == "$remote_peeled_commit" \
  || "$(wc -l <<<"$remote_tag_lines" | tr -d ' ')" != 2 ]]; then
  echo "ERROR: canonical origin does not expose one annotated tag '$TAG' and peeled commit." >&2
  exit 1
fi

TEMP_REF="refs/pid-rs-repin/$TAG"
cleanup_temp_ref() {
  git -C "$SUB" update-ref -d "$TEMP_REF" >/dev/null 2>&1 || true
}
trap cleanup_temp_ref EXIT
cleanup_temp_ref
git -C "$SUB" fetch --no-tags origin "refs/tags/$TAG:$TEMP_REF"

if [[ "$(git -C "$SUB" rev-parse "$TEMP_REF")" != "$remote_tag_object" \
  || "$(git -C "$SUB" cat-file -t "$TEMP_REF")" != tag \
  || "$(git -C "$SUB" rev-parse "$TEMP_REF^{commit}")" != "$remote_peeled_commit" ]]; then
  echo "ERROR: fetched tag identity differs from the live canonical remote projection." >&2
  exit 1
fi
tag_object="$(git -C "$SUB" cat-file tag "$TEMP_REF")"
embedded_object="$(awk '/^object / { sub(/^object /, ""); print; exit }' <<<"$tag_object")"
embedded_type="$(awk '/^type / { sub(/^type /, ""); print; exit }' <<<"$tag_object")"
embedded_name="$(awk '/^tag / { sub(/^tag /, ""); print; exit }' <<<"$tag_object")"
if [[ "$embedded_object" != "$remote_peeled_commit" \
  || "$embedded_type" != commit \
  || "$embedded_name" != "$TAG" ]]; then
  echo "ERROR: $TAG is not a direct annotated tag of its reported commit." >&2
  exit 1
fi
if grep -Eq -- \
  '-----BEGIN (PGP|SSH) SIGNATURE-----|-----BEGIN SIGNED MESSAGE-----' \
  <<<"$tag_object"; then
  echo "ERROR: $TAG is signed; pid-rs release tags must be annotated and unsigned." >&2
  exit 1
fi
tag_version="${TAG#v}"
workspace_manifest="$(git -C "$SUB" show "$remote_peeled_commit:Cargo.toml")" || {
  echo "ERROR: $TAG does not contain a root Cargo.toml." >&2
  exit 1
}
workspace_version="$(awk '
  /^\[workspace\.package\][[:space:]]*$/ { in_section=1; next }
  /^\[/ { in_section=0 }
  in_section && /^[[:space:]]*version[[:space:]]*=/ {
    line=$0
    sub(/^[^"]*"/, "", line)
    sub(/".*/, "", line)
    print line
    exit
  }
' <<<"$workspace_manifest")"
if [[ "$workspace_version" != "$tag_version" ]]; then
  echo "ERROR: $TAG points to workspace version '${workspace_version:-<missing>}'." >&2
  exit 1
fi

echo "==> Checking out $TAG in the submodule ..."
# Detached checkout onto the tag. Explicit checkout is intentional: ancestry to the
# submodule's recorded branch is irrelevant here (the histories diverged). --detach keeps
# us on a detached HEAD (no stray local branch) exactly as a submodule pin expects.
git -C "$SUB" checkout --detach "$remote_peeled_commit"

AFTER_SHA="$(git -C "$SUB" rev-parse HEAD)"
if [[ "$AFTER_SHA" != "$remote_peeled_commit" ]]; then
  echo "ERROR: checked-out commit differs from the verified remote tag." >&2
  exit 1
fi

if [[ "$BEFORE_SHA" == "$AFTER_SHA" ]]; then
  echo "    Note: submodule was already at $TAG ($AFTER_SHA); gitlink unchanged."
fi

# ---- stage the gitlink -------------------------------------------------------------------
# Pathspec is relative to $VLA (pid-rs lives at the prisoma repo root). A no-op when the
# gitlink is unchanged; safe regardless.
echo "==> Staging the gitlink change in prisoma ..."
git -C "$VLA" add -- pid-rs

# ---- refresh prisoma's ROOT Cargo.lock ---------------------------------------------------
# pid-core / pid-runlog are path-deps from the submodule, so their entries in prisoma's root
# Cargo.lock follow the submodule's source. Re-resolve by updating just those packages.
# Do NOT use `cargo check --locked` as the refresh path: after a version bump the lock is
# intentionally stale, so --locked would (correctly) refuse to update it. Fall back to a
# plain `cargo check`, which rewrites the lock. cargo stderr is left visible so a genuine
# failure (network/registry/manifest) is diagnosable rather than silently swallowed.
# Note: prisoma's root workspace excludes `crates/ncp-observer`, so this does not pull in
# NCP/Zenoh; `cargo update` does not compile anything, and the `cargo check` fallback only
# touches the default members.
echo "==> Refreshing prisoma root Cargo.lock (pid-core / pid-runlog) ..."
if ! cargo update --manifest-path "$VLA/Cargo.toml" -p pid-core -p pid-runlog; then
  echo "    cargo update -p pid-core -p pid-runlog did not apply cleanly; falling back to cargo check."
  cargo check --manifest-path "$VLA/Cargo.toml"
fi

# `cargo update` can exit successfully without touching the intended packages (for example after
# a consumer workspace topology change). Verify the lock actually records exactly one copy of each
# path package at the release-tag version before staging or reporting success.
locked_package_versions() {
  local package="$1"
  awk -v package="$package" '
    /^\[\[package\]\]$/ { name=""; next }
    /^name = "/ {
      name=$0
      sub(/^name = "/, "", name)
      sub(/"$/, "", name)
      next
    }
    name == package && /^version = "/ {
      version=$0
      sub(/^version = "/, "", version)
      sub(/"$/, "", version)
      print version
    }
  ' "$VLA/Cargo.lock"
}
for package in pid-core pid-runlog; do
  locked_versions="$(locked_package_versions "$package")"
  if [[ "$locked_versions" != "$tag_version" ]]; then
    rendered_versions="${locked_versions//$'\n'/, }"
    echo "ERROR: Cargo.lock must contain exactly one $package $tag_version entry; found ${rendered_versions:-<none>}." >&2
    exit 1
  fi
done

# Stage the lock only if cargo actually touched it.
if ! git -C "$VLA" diff --quiet -- Cargo.lock; then
  git -C "$VLA" add -- Cargo.lock
  echo "    Cargo.lock updated and staged."
else
  echo "    Cargo.lock unchanged (pid-core/pid-runlog version may be identical)."
fi

# ---- summary -----------------------------------------------------------------------------
echo
echo "==> Gitlink change (prisoma/pid-rs):"
echo "    $BEFORE_SHA -> $AFTER_SHA  ($TAG)"
echo
echo "==> Staged changes in prisoma:"
git -C "$VLA" diff --cached --stat -- pid-rs Cargo.lock | sed 's/^/    /' || true
echo
echo "==> Nothing has been committed or pushed. Suggested commit (run by hand):"
echo
echo "    git -C \"$VLA\" commit -m \"chore: re-pin pid-rs submodule to $TAG\""
echo
echo "Done."
