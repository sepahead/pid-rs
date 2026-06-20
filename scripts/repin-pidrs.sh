#!/usr/bin/env bash
# Bump pid_vla's `pid-rs` git submodule to a target pid-rs tag and refresh pid_vla's
# root Cargo.lock so the path-deps (pid-core / pid-runlog) re-resolve to the new version.
#
# WHY an explicit fetch + checkout (and NOT `git submodule update --remote`):
# pid_vla's `pid-rs` submodule history DIVERGED from canonical sepahead/pid-rs — the prior
# pin was not an ancestor of canonical `main`. `git submodule update --remote` resolves the
# branch tip recorded in .gitmodules and fast-forwards; with a diverged history that either
# fails or lands on the wrong commit. We instead fetch tags with --force and check out the
# requested tag by name, which is unambiguous regardless of ancestry. (Ancestry to the
# submodule's recorded branch is intentionally irrelevant here.)
#
# This script does NOT commit or push. It stages the gitlink (`git add pid-rs`) and the
# refreshed Cargo.lock, then prints the gitlink change and a suggested commit for the
# maintainer to run by hand.
#
# Usage:
#   scripts/repin-pidrs.sh <tag> [pid_vla-dir]
#
#   <tag>          A pid-rs tag to pin the submodule to, e.g. v0.2.0.
#   [pid_vla-dir]  Path to the pid_vla checkout. Defaults to the sibling `pid_vla`
#                  directory next to this pid-rs checkout (resolved from this script's
#                  location), i.e. the standard sepahead-github sibling layout.
set -euo pipefail

# ---- argument validation -----------------------------------------------------------------
if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $(basename "$0") <tag> [pid_vla-dir]" >&2
  exit 2
fi

TAG="$1"
if [[ -z "$TAG" ]]; then
  echo "ERROR: <tag> must be a non-empty pid-rs tag (e.g. v0.2.0)." >&2
  exit 2
fi

# Resolve pid_vla dir: explicit arg, else the sibling `pid_vla` of this pid-rs checkout.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDRS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"          # the pid-rs checkout this script ships in
DEFAULT_VLA="$(cd "$PIDRS_ROOT/.." && pwd)/pid_vla" # sibling under sepahead-github/

VLA="${2:-$DEFAULT_VLA}"
if [[ ! -d "$VLA" ]]; then
  echo "ERROR: pid_vla directory not found: $VLA" >&2
  echo "       Pass the path explicitly: $(basename "$0") $TAG /path/to/pid_vla" >&2
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

echo "==> Re-pinning pid_vla submodule pid-rs -> $TAG"
echo "    pid_vla : $VLA"
echo "    submod  : $SUB"

# ---- record the before-state for the diff summary ----------------------------------------
BEFORE_SHA="$(git -C "$SUB" rev-parse HEAD)"

# ---- explicit fetch + checkout (NEVER `git submodule update --remote`) --------------------
echo "==> Fetching tags from origin (--force) in the submodule ..."
git -C "$SUB" fetch origin --tags --force

# Verify the tag exists before we try to check it out, for a clear error.
if ! git -C "$SUB" rev-parse --verify --quiet "refs/tags/$TAG^{commit}" >/dev/null; then
  echo "ERROR: tag '$TAG' not found in submodule remote after fetch." >&2
  echo "       remote: $(git -C "$SUB" remote get-url origin 2>/dev/null || echo '<unknown>')" >&2
  echo "       Available tags:" >&2
  git -C "$SUB" tag -l 2>/dev/null | sed 's/^/         /' >&2 || true
  exit 1
fi

echo "==> Checking out $TAG in the submodule ..."
# Detached checkout onto the tag. Explicit checkout is intentional: ancestry to the
# submodule's recorded branch is irrelevant here (the histories diverged). --detach keeps
# us on a detached HEAD (no stray local branch) exactly as a submodule pin expects.
git -C "$SUB" checkout --detach "refs/tags/$TAG"

AFTER_SHA="$(git -C "$SUB" rev-parse HEAD)"

if [[ "$BEFORE_SHA" == "$AFTER_SHA" ]]; then
  echo "    Note: submodule was already at $TAG ($AFTER_SHA); gitlink unchanged."
fi

# ---- stage the gitlink -------------------------------------------------------------------
# Pathspec is relative to $VLA (pid-rs lives at the pid_vla repo root). A no-op when the
# gitlink is unchanged; safe regardless.
echo "==> Staging the gitlink change in pid_vla ..."
git -C "$VLA" add -- pid-rs

# ---- refresh pid_vla's ROOT Cargo.lock ---------------------------------------------------
# pid-core / pid-runlog are path-deps from the submodule, so their entries in pid_vla's root
# Cargo.lock follow the submodule's source. Re-resolve by updating just those packages.
# Do NOT use `cargo check --locked` as the refresh path: after a version bump the lock is
# intentionally stale, so --locked would (correctly) refuse to update it. Fall back to a
# plain `cargo check`, which rewrites the lock. cargo stderr is left visible so a genuine
# failure (network/registry/manifest) is diagnosable rather than silently swallowed.
# Note: pid_vla's root workspace excludes `crates/ncp-observer`, so this does not pull in
# NCP/Zenoh; `cargo update` does not compile anything, and the `cargo check` fallback only
# touches the default members.
echo "==> Refreshing pid_vla root Cargo.lock (pid-core / pid-runlog) ..."
if command -v cargo >/dev/null 2>&1; then
  if ! cargo update --manifest-path "$VLA/Cargo.toml" -p pid-core -p pid-runlog; then
    echo "    cargo update -p pid-core -p pid-runlog did not apply cleanly; falling back to cargo check."
    cargo check --manifest-path "$VLA/Cargo.toml"
  fi
  # Stage the lock only if cargo actually touched it.
  if ! git -C "$VLA" diff --quiet -- Cargo.lock; then
    git -C "$VLA" add -- Cargo.lock
    echo "    Cargo.lock updated and staged."
  else
    echo "    Cargo.lock unchanged (pid-core/pid-runlog version may be identical)."
  fi
else
  echo "WARNING: cargo not found on PATH; skipped Cargo.lock refresh." >&2
  echo "         Run manually in $VLA: cargo update -p pid-core -p pid-runlog" >&2
fi

# ---- summary -----------------------------------------------------------------------------
echo
echo "==> Gitlink change (pid_vla/pid-rs):"
echo "    $BEFORE_SHA -> $AFTER_SHA  ($TAG)"
echo
echo "==> Staged changes in pid_vla:"
git -C "$VLA" diff --cached --stat -- pid-rs Cargo.lock | sed 's/^/    /' || true
echo
echo "==> Nothing has been committed or pushed. Suggested commit (run by hand):"
echo
echo "    git -C \"$VLA\" commit -m \"chore: re-pin pid-rs submodule to $TAG\""
echo
echo "Done."
