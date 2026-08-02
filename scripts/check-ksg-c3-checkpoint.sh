#!/usr/bin/env bash
set -euo pipefail

# Git applies the invoking process's umask when it materializes a checkout.
# The frozen exact-source runner rejects noncanonical source modes, so
# normalize before any historical clone is created.  mktemp still creates the
# private scratch directory with owner-only permissions.
umask 022

# Replay the immutable C3 phase evidence in both lifecycle representations. The
# phase self-test constructs committed hostile descendants, so its source must
# remain the exact parent-plus-overlay candidate rather than a clean checkpoint.

readonly C3_PARENT="8b792bc143fff2d84f2d8e7817d1de7850741223"
readonly C3_PARENT_TREE="8e247b9a6c46fd6266fe4fc02fbe9c3142268215"
readonly C3_CHECKPOINT="8fa6e992d9124229c7a175c4508bf10df336675a"
readonly C3_TREE="059dc980d4a86066c07687188a452cf2459899eb"
readonly C3_PRECOMMIT_STATUS_SIZE="2689"
readonly C3_PRECOMMIT_STATUS_SHA256="1e1dc75985155d2a1ae3caff43fa8b09767cddaebd58f087266c335819619a85"
readonly C3_DELTA_NAME_ONLY_SIZE="875"
readonly C3_DELTA_NAME_ONLY_SHA256="9de626b10a3c332c8075bf85e04a1fe8fa6aacee0289edbd347eed885117c950"
readonly C3_DELTA_NAME_STATUS_SIZE="913"
readonly C3_DELTA_NAME_STATUS_SHA256="c51242f983405aa569a4567a1f83618f46aefeafdb5d87975c2d4762e8e3057f"
readonly C3_CHECKER_SHA256="967e3c55b83006470be1e699fdabbe8f8358319dea563f8171870c1122c6591d"
readonly C3_SELF_TEST_SHA256="b2056cc7d215b32ffeabcb70d1831d72b47b5a7b2a05d41e042e2827baa67c48"
readonly FOLLOWUP_PARENT="$C3_CHECKPOINT"
readonly FOLLOWUP_CHECKPOINT="f6fde520b841c61b7752cdd053af59bda763d3d1"
readonly FOLLOWUP_TREE="1ce2d75081bf85d9a30da180539c162a2c5a5c86"
readonly FOLLOWUP_RUNNER_SHA256="194e7ef0463f5d447d2be59e9ab24f35efadd70739bcf4b9a40ed3734408dbdf"

if [[ "$#" -ne 0 ]]; then
  printf 'usage: %s\n' "$0" >&2
  exit 2
fi

git_isolated() {
  local replay_index=""
  if [[ "${1:-}" == "--replay-index" ]]; then
    if [[ "$#" -lt 3 ]]; then
      printf 'internal replay-index invocation is incomplete\n' >&2
      return 2
    fi
    replay_index="$2"
    shift 2
  fi
  local -a clean_environment=(
    -u GIT_DIR
    -u GIT_WORK_TREE
    -u GIT_COMMON_DIR
    -u GIT_INDEX_FILE
    -u GIT_OBJECT_DIRECTORY
    -u GIT_ALTERNATE_OBJECT_DIRECTORIES
    -u GIT_NAMESPACE
    -u GIT_CONFIG_COUNT
    -u GIT_CONFIG
    -u GIT_CONFIG_PARAMETERS
    -u GIT_CONFIG_GLOBAL
    -u GIT_CONFIG_SYSTEM
    -u GIT_CEILING_DIRECTORIES
    -u GIT_ATTR_NOSYSTEM
    -u GIT_ATTR_SOURCE
    -u GIT_DISCOVERY_ACROSS_FILESYSTEM
    -u GIT_EXEC_PATH
    -u GIT_GRAFT_FILE
    -u GIT_GLOB_PATHSPECS
    -u GIT_ICASE_PATHSPECS
    -u GIT_LITERAL_PATHSPECS
    -u GIT_NOGLOB_PATHSPECS
    -u GIT_NO_REPLACE_OBJECTS
    -u GIT_PREFIX
    -u GIT_QUARANTINE_PATH
    -u GIT_REFERENCE_BACKEND
    -u GIT_REPLACE_REF_BASE
    -u GIT_SHALLOW_FILE
    -u GIT_TEMPLATE_DIR
  )
  local index
  for ((index = 0; index < 256; index += 1)); do
    clean_environment+=(
      -u "GIT_CONFIG_KEY_${index}"
      -u "GIT_CONFIG_VALUE_${index}"
    )
  done
  local -a replay_environment=(
    GIT_ATTR_NOSYSTEM=1
    GIT_CONFIG_GLOBAL=/dev/null
    GIT_CONFIG_NOSYSTEM=1
    GIT_GRAFT_FILE=/dev/null
    GIT_LITERAL_PATHSPECS=1
    GIT_NO_LAZY_FETCH=1
    GIT_NO_REPLACE_OBJECTS=1
    GIT_OPTIONAL_LOCKS=0
    GIT_TERMINAL_PROMPT=0
  )
  if [[ -n "$replay_index" ]]; then
    replay_environment+=(GIT_INDEX_FILE="$replay_index")
  fi
  env "${clean_environment[@]}" \
    "${replay_environment[@]}" \
    git \
      -c advice.graftFileDeprecated=false \
      -c core.attributesFile=/dev/null \
      -c core.fsmonitor=false \
      -c core.hooksPath=/dev/null \
      -c core.untrackedCache=false \
      "$@"
}

sha256_file() {
  local path="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -- "$path" | awk '{print $1}'
  else
    shasum -a 256 -- "$path" | awk '{print $1}'
  fi
}

require_file_sha256() {
  local path="$1"
  local expected="$2"
  local actual
  actual="$(sha256_file "$path")"
  if [[ "$actual" != "$expected" ]]; then
    printf 'exact C3 file digest mismatch: %s\n' "$path" >&2
    exit 1
  fi
}

SCRIPT_DIRECTORY="$(
  CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P
)"
readonly SCRIPT_DIRECTORY
REPOSITORY_ROOT="$(git_isolated -C "$SCRIPT_DIRECTORY/.." rev-parse --show-toplevel)"
readonly REPOSITORY_ROOT
CANONICAL_ROOT="$(CDPATH='' cd -- "$REPOSITORY_ROOT" && pwd -P)"
readonly CANONICAL_ROOT
if [[ "$CANONICAL_ROOT/scripts" != "$SCRIPT_DIRECTORY" ]]; then
  printf 'wrapper path is outside the canonical repository root\n' >&2
  exit 1
fi
if [[ "$(git_isolated -C "$CANONICAL_ROOT" rev-parse --show-object-format=storage)" != "sha1" ]]; then
  printf 'C3 checkpoint replay requires a SHA-1 Git object repository\n' >&2
  exit 1
fi
if [[ "$(git_isolated -C "$CANONICAL_ROOT" rev-parse --is-shallow-repository)" != "false" ]]; then
  printf 'C3 checkpoint replay requires a non-shallow repository\n' >&2
  exit 1
fi
if ! git_isolated -C "$CANONICAL_ROOT" merge-base --is-ancestor \
  "$C3_CHECKPOINT" HEAD
then
  printf 'HEAD does not descend from the immutable C3 checkpoint\n' >&2
  exit 1
fi
if [[ "$(git_isolated -C "$CANONICAL_ROOT" rev-parse --verify "$C3_CHECKPOINT^")" != "$C3_PARENT" ]] ||
   [[ "$(git_isolated -C "$CANONICAL_ROOT" rev-parse --verify "$C3_CHECKPOINT^{tree}")" != "$C3_TREE" ]] ||
   [[ "$(git_isolated -C "$CANONICAL_ROOT" rev-parse --verify "$C3_PARENT^{tree}")" != "$C3_PARENT_TREE" ]]
then
  printf 'immutable C3 parent, checkpoint, or tree relationship changed\n' >&2
  exit 1
fi
if ! git_isolated -C "$CANONICAL_ROOT" merge-base --is-ancestor \
  "$FOLLOWUP_CHECKPOINT" HEAD
then
  printf 'HEAD does not descend from the immutable C3 hosted follow-up\n' >&2
  exit 1
fi
if [[ "$(git_isolated -C "$CANONICAL_ROOT" rev-parse --verify "$FOLLOWUP_CHECKPOINT^")" != "$FOLLOWUP_PARENT" ]] ||
   [[ "$(git_isolated -C "$CANONICAL_ROOT" rev-parse --verify "$FOLLOWUP_CHECKPOINT^{tree}")" != "$FOLLOWUP_TREE" ]]
then
  printf 'immutable C3 hosted follow-up parent, checkpoint, or tree relationship changed\n' >&2
  exit 1
fi

readonly SCRATCH_PARENT="${RUNNER_TEMP:-${TMPDIR:-/tmp}}"
SCRATCH_ROOT="$(mktemp -d "$SCRATCH_PARENT/pid-rs-ksg-c3-checkpoint.XXXXXX")"
readonly SCRATCH_ROOT
case "$SCRATCH_ROOT" in
  "$SCRATCH_PARENT"/pid-rs-ksg-c3-checkpoint.*) ;;
  *)
    printf 'temporary replay path escaped its declared parent\n' >&2
    exit 1
    ;;
esac
cleanup() {
  chmod -R u+w -- "$SCRATCH_ROOT" 2>/dev/null || true
  rm -rf -- "$SCRATCH_ROOT"
}
trap cleanup EXIT HUP INT TERM

clone_without_checkout() {
  local destination="$1"
  git_isolated -c protocol.file.allow=always clone \
    --no-local --quiet --no-checkout -- "$CANONICAL_ROOT" "$destination"
}

readonly COMMITTED_ROOT="$SCRATCH_ROOT/committed"
clone_without_checkout "$COMMITTED_ROOT"
git_isolated -C "$COMMITTED_ROOT" checkout --quiet --detach "$C3_CHECKPOINT"
if [[ "$(git_isolated -C "$COMMITTED_ROOT" rev-parse --verify HEAD)" != "$C3_CHECKPOINT" ]] ||
   [[ "$(git_isolated -C "$COMMITTED_ROOT" rev-parse --verify 'HEAD^{tree}')" != "$C3_TREE" ]] ||
   [[ -n "$(git_isolated -C "$COMMITTED_ROOT" status --porcelain=v2 --untracked-files=all)" ]]
then
  printf 'clean committed C3 replay has the wrong HEAD, tree, or status\n' >&2
  exit 1
fi
require_file_sha256 \
  "$COMMITTED_ROOT/scripts/check-ksg-phase-isolation.py" \
  "$C3_CHECKER_SHA256"
require_file_sha256 \
  "$COMMITTED_ROOT/scripts/check-ksg-phase-isolation-self-test.py" \
  "$C3_SELF_TEST_SHA256"
(
  cd -- "$COMMITTED_ROOT"
  python3 -I -S scripts/check-ksg-phase-isolation.py \
    --expected-candidate-tree "$C3_TREE" \
    --checkpoint-commit "$C3_CHECKPOINT"
  python3 -I -S -O scripts/check-ksg-phase-isolation.py \
    --expected-candidate-tree "$C3_TREE" \
    --checkpoint-commit "$C3_CHECKPOINT"
)
if [[ "$(git_isolated -C "$COMMITTED_ROOT" rev-parse --verify HEAD)" != "$C3_CHECKPOINT" ]] ||
   [[ "$(git_isolated -C "$COMMITTED_ROOT" rev-parse --verify 'HEAD^{tree}')" != "$C3_TREE" ]] ||
   [[ -n "$(git_isolated -C "$COMMITTED_ROOT" status --porcelain=v2 --untracked-files=all)" ]]
then
  printf 'committed C3 checker replay changed the clean checkpoint clone\n' >&2
  exit 1
fi
require_file_sha256 \
  "$COMMITTED_ROOT/scripts/check-ksg-phase-isolation.py" \
  "$C3_CHECKER_SHA256"
require_file_sha256 \
  "$COMMITTED_ROOT/scripts/check-ksg-phase-isolation-self-test.py" \
  "$C3_SELF_TEST_SHA256"

readonly PRECOMMIT_ROOT="$SCRATCH_ROOT/precommit"
clone_without_checkout "$PRECOMMIT_ROOT"
git_isolated -C "$PRECOMMIT_ROOT" checkout --quiet --detach "$C3_PARENT"
readonly DELTA_NAME_ONLY="$SCRATCH_ROOT/c3-delta-name-only.z"
readonly DELTA_NAME_STATUS="$SCRATCH_ROOT/c3-delta-name-status.z"
git_isolated -C "$PRECOMMIT_ROOT" diff-tree --no-commit-id --name-only \
  --no-renames -r -z "$C3_PARENT" "$C3_CHECKPOINT" >"$DELTA_NAME_ONLY"
git_isolated -C "$PRECOMMIT_ROOT" diff-tree --no-commit-id --name-status \
  --no-renames -r -z "$C3_PARENT" "$C3_CHECKPOINT" >"$DELTA_NAME_STATUS"
if [[ "$(tr -cd '\000' <"$DELTA_NAME_ONLY" | wc -c | tr -d '[:space:]')" != "19" ]] ||
   [[ "$(tr -cd '\000' <"$DELTA_NAME_STATUS" | wc -c | tr -d '[:space:]')" != "38" ]] ||
   [[ "$(wc -c <"$DELTA_NAME_ONLY" | tr -d '[:space:]')" != "$C3_DELTA_NAME_ONLY_SIZE" ]] ||
   [[ "$(sha256_file "$DELTA_NAME_ONLY")" != "$C3_DELTA_NAME_ONLY_SHA256" ]] ||
   [[ "$(wc -c <"$DELTA_NAME_STATUS" | tr -d '[:space:]')" != "$C3_DELTA_NAME_STATUS_SIZE" ]] ||
   [[ "$(sha256_file "$DELTA_NAME_STATUS")" != "$C3_DELTA_NAME_STATUS_SHA256" ]]
then
  printf 'C3 parent-to-checkpoint path inventory differs from the frozen delta\n' >&2
  exit 1
fi
git_isolated -C "$PRECOMMIT_ROOT" restore \
  --source="$C3_CHECKPOINT" --worktree \
  --pathspec-from-file="$DELTA_NAME_ONLY" --pathspec-file-nul
readonly STATUS_CAPTURE="$SCRATCH_ROOT/precommit-status-v2.z"
git_isolated -C "$PRECOMMIT_ROOT" status \
  --porcelain=v2 -z --untracked-files=all >"$STATUS_CAPTURE"
if [[ "$(wc -c <"$STATUS_CAPTURE" | tr -d '[:space:]')" != "$C3_PRECOMMIT_STATUS_SIZE" ]] ||
   [[ "$(sha256_file "$STATUS_CAPTURE")" != "$C3_PRECOMMIT_STATUS_SHA256" ]]
then
  printf 'reconstructed C3 precommit status differs from the frozen 19-path overlay\n' >&2
  exit 1
fi
if ! git_isolated -C "$PRECOMMIT_ROOT" diff --cached --quiet --exit-code; then
  printf 'reconstructed C3 precommit index differs from its exact parent\n' >&2
  exit 1
fi
readonly ALTERNATE_INDEX="$SCRATCH_ROOT/c3-precommit.index"
git_isolated --replay-index "$ALTERNATE_INDEX" -C "$PRECOMMIT_ROOT" \
  read-tree "$C3_PARENT"
git_isolated --replay-index "$ALTERNATE_INDEX" -C "$PRECOMMIT_ROOT" \
  add --pathspec-from-file="$DELTA_NAME_ONLY" --pathspec-file-nul
if [[ "$(git_isolated --replay-index "$ALTERNATE_INDEX" -C "$PRECOMMIT_ROOT" write-tree)" != "$C3_TREE" ]]; then
  printf 'alternate-index reconstruction differs from the exact C3 tree\n' >&2
  exit 1
fi
if [[ ! -f "$ALTERNATE_INDEX" || -L "$ALTERNATE_INDEX" ]] ||
   [[ "$(python3 -I -S -c 'import os, sys; print(os.lstat(sys.argv[1]).st_nlink)' "$ALTERNATE_INDEX")" != "1" ]] ||
   [[ "$(git_isolated -C "$PRECOMMIT_ROOT" write-tree)" != "$C3_PARENT_TREE" ]]
then
  printf 'alternate or real C3 reconstruction index lost exact custody\n' >&2
  exit 1
fi
ALTERNATE_INDEX_SHA256="$(sha256_file "$ALTERNATE_INDEX")"
readonly ALTERNATE_INDEX_SHA256
require_file_sha256 \
  "$PRECOMMIT_ROOT/scripts/check-ksg-phase-isolation.py" \
  "$C3_CHECKER_SHA256"
require_file_sha256 \
  "$PRECOMMIT_ROOT/scripts/check-ksg-phase-isolation-self-test.py" \
  "$C3_SELF_TEST_SHA256"
(
  cd -- "$PRECOMMIT_ROOT"
  python3 -I -S scripts/check-ksg-phase-isolation.py \
    --expected-candidate-tree "$C3_TREE" \
    --checkpoint-commit "$C3_CHECKPOINT"
  python3 -I -S -O scripts/check-ksg-phase-isolation.py \
    --expected-candidate-tree "$C3_TREE" \
    --checkpoint-commit "$C3_CHECKPOINT"
  python3 -I -S scripts/check-ksg-phase-isolation-self-test.py
  python3 -I -S -O scripts/check-ksg-phase-isolation-self-test.py
  python3 -I -S scripts/check-ksg-phase-isolation.py \
    --expected-candidate-tree "$C3_TREE" \
    --checkpoint-commit "$C3_CHECKPOINT"
  python3 -I -S -O scripts/check-ksg-phase-isolation.py \
    --expected-candidate-tree "$C3_TREE" \
    --checkpoint-commit "$C3_CHECKPOINT"
)

git_isolated -C "$PRECOMMIT_ROOT" status \
  --porcelain=v2 -z --untracked-files=all >"$STATUS_CAPTURE"
if [[ "$(wc -c <"$STATUS_CAPTURE" | tr -d '[:space:]')" != "$C3_PRECOMMIT_STATUS_SIZE" ]] ||
   [[ "$(sha256_file "$STATUS_CAPTURE")" != "$C3_PRECOMMIT_STATUS_SHA256" ]]
then
  printf 'C3 phase self-tests did not restore the frozen precommit overlay\n' >&2
  exit 1
fi
if [[ "$(git_isolated -C "$PRECOMMIT_ROOT" rev-parse --verify HEAD)" != "$C3_PARENT" ]] ||
   [[ "$(git_isolated -C "$PRECOMMIT_ROOT" write-tree)" != "$C3_PARENT_TREE" ]] ||
   [[ "$(git_isolated --replay-index "$ALTERNATE_INDEX" -C "$PRECOMMIT_ROOT" write-tree)" != "$C3_TREE" ]] ||
   [[ "$(sha256_file "$ALTERNATE_INDEX")" != "$ALTERNATE_INDEX_SHA256" ]]
then
  printf 'C3 phase self-tests changed the precommit HEAD or either index\n' >&2
  exit 1
fi
require_file_sha256 \
  "$PRECOMMIT_ROOT/scripts/check-ksg-phase-isolation.py" \
  "$C3_CHECKER_SHA256"
require_file_sha256 \
  "$PRECOMMIT_ROOT/scripts/check-ksg-phase-isolation-self-test.py" \
  "$C3_SELF_TEST_SHA256"

printf '%s\n' \
  "OK: immutable C3 checkpoint replay; committed=2/2; precommit=2/2; hostile=normal+optimized; parent=$C3_PARENT; checkpoint=$C3_CHECKPOINT; tree=$C3_TREE. No arithmetic, estimator, PID, statistical, remote, authenticity, or follow-up-tree claim is implied."

# The direct-child follow-up gate is intentionally valid only at its exact
# implementation commit.  Replay those frozen bytes in a third no-local clone;
# never relax its topology rule to accept the current descendant.
readonly FOLLOWUP_ROOT="$SCRATCH_ROOT/followup"
clone_without_checkout "$FOLLOWUP_ROOT"
git_isolated -C "$FOLLOWUP_ROOT" checkout --quiet --detach "$FOLLOWUP_CHECKPOINT"
require_followup_clone_state() {
  if [[ "$(git_isolated -C "$FOLLOWUP_ROOT" rev-parse --verify HEAD)" != "$FOLLOWUP_CHECKPOINT" ]] ||
     [[ "$(git_isolated -C "$FOLLOWUP_ROOT" rev-parse --verify 'HEAD^{tree}')" != "$FOLLOWUP_TREE" ]] ||
     [[ -n "$(git_isolated -C "$FOLLOWUP_ROOT" status --porcelain=v2 --untracked-files=all --ignored=matching)" ]]
  then
    printf 'clean hosted-follow-up replay has the wrong HEAD, tree, or status\n' >&2
    exit 1
  fi
  if [[ -e "$FOLLOWUP_ROOT/.git/objects/info/alternates" ||
        -L "$FOLLOWUP_ROOT/.git/objects/info/alternates" ||
        -e "$FOLLOWUP_ROOT/.git/info/grafts" ||
        -L "$FOLLOWUP_ROOT/.git/info/grafts" ||
        -e "$FOLLOWUP_ROOT/.git/shallow" ||
        -L "$FOLLOWUP_ROOT/.git/shallow" ]] ||
     [[ -n "$(git_isolated -C "$FOLLOWUP_ROOT" for-each-ref --format='%(refname)' refs/replace)" ]]
  then
    printf 'clean hosted-follow-up replay retained alternate, graft, shallow, or replacement routing\n' >&2
    exit 1
  fi
}
require_followup_clone_state
require_file_sha256 \
  "$FOLLOWUP_ROOT/scripts/check-c3-hosted-followup.sh" \
  "$FOLLOWUP_RUNNER_SHA256"
(
  cd -- "$FOLLOWUP_ROOT"
  scripts/check-c3-hosted-followup.sh normal self-test \
    --compare-runner-modes \
    --expected-candidate-tree "$FOLLOWUP_TREE" \
    --checkpoint-commit "$FOLLOWUP_CHECKPOINT"
  scripts/check-c3-hosted-followup.sh normal checker \
    --expected-candidate-tree "$FOLLOWUP_TREE" \
    --checkpoint-commit "$FOLLOWUP_CHECKPOINT"
)
require_followup_clone_state
require_file_sha256 \
  "$FOLLOWUP_ROOT/scripts/check-c3-hosted-followup.sh" \
  "$FOLLOWUP_RUNNER_SHA256"

printf '%s\n' \
  "OK: immutable C3 hosted-follow-up replay; parent=$FOLLOWUP_PARENT; checkpoint=$FOLLOWUP_CHECKPOINT; tree=$FOLLOWUP_TREE; modes=normal+optimized. This does not adjudicate the current descendant or imply hosted, scientific, authenticity, or security-clean success."
