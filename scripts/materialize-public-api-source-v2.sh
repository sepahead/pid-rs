#!/usr/bin/env bash
# Materialize one literal Git source tree for public-API evidence generation.
set -euo pipefail

if [[ "$#" -ne 5 ]]; then
  echo "usage: $0 <repository-root> <source-commit> <source-tree> <destination> <python>" >&2
  exit 2
fi

REPO_ROOT="$1"
SOURCE_COMMIT="$2"
SOURCE_TREE="$3"
DESTINATION="$4"
PYTHON_EXECUTABLE="$5"
if [[ "$PYTHON_EXECUTABLE" != /* || ! -f "$PYTHON_EXECUTABLE" \
  || ! -x "$PYTHON_EXECUTABLE" ]]
then
  echo "public API source materialization requires an absolute executable Python path" >&2
  exit 2
fi
PYTHON_EXECUTABLE="$(
  cd "$(dirname "$PYTHON_EXECUTABLE")"
  printf '%s/%s\n' "$(pwd -P)" "$(basename "$PYTHON_EXECUTABLE")"
)"
if ! "$PYTHON_EXECUTABLE" -I -S -B -c '
import sys
raise SystemExit(
    0
    if sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize == 0
    else 1
)
'; then
  echo "public API source materialization requires Python 3.11+ -I -S -B without -O" >&2
  exit 2
fi
readonly PYTHON_EXECUTABLE
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-public-api-source.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

scrubbed_git() (
  unset \
    GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_ATTR_SOURCE GIT_CEILING_DIRECTORIES \
    GIT_COMMON_DIR GIT_CONFIG GIT_CONFIG_COUNT GIT_CONFIG_GLOBAL GIT_CONFIG_NOSYSTEM \
    GIT_CONFIG_PARAMETERS GIT_CONFIG_SYSTEM GIT_DIR GIT_DISCOVERY_ACROSS_FILESYSTEM \
    GIT_EXEC_PATH GIT_GLOB_PATHSPECS GIT_GRAFT_FILE GIT_ICASE_PATHSPECS GIT_INDEX_FILE \
    GIT_INDEX_VERSION GIT_INTERNAL_SUPER_PREFIX GIT_LITERAL_PATHSPECS GIT_NAMESPACE \
    GIT_NOGLOB_PATHSPECS GIT_NO_REPLACE_OBJECTS GIT_OBJECT_DIRECTORY GIT_PREFIX \
    GIT_QUARANTINE_PATH GIT_REFERENCE_BACKEND GIT_REPLACE_REF_BASE GIT_SHALLOW_FILE \
    GIT_SUPER_PREFIX GIT_TEMPLATE_DIR GIT_WORK_TREE
  local variable
  while IFS= read -r variable; do
    unset "$variable"
  done < <(compgen -A variable GIT_CONFIG_KEY_ || true)
  while IFS= read -r variable; do
    unset "$variable"
  done < <(compgen -A variable GIT_CONFIG_VALUE_ || true)
  export \
    GIT_ATTR_NOSYSTEM=1 \
    GIT_CONFIG_GLOBAL=/dev/null \
    GIT_CONFIG_NOSYSTEM=1 \
    GIT_GRAFT_FILE=/dev/null \
    GIT_LITERAL_PATHSPECS=1 \
    GIT_NO_LAZY_FETCH=1 \
    GIT_NO_REPLACE_OBJECTS=1 \
    GIT_OPTIONAL_LOCKS=0 \
    GIT_TERMINAL_PROMPT=0 \
    LC_ALL=C
  command git -c advice.graftFileDeprecated=false -c core.attributesFile=/dev/null "$@"
)

canonical_repo_root="$(cd "$REPO_ROOT" && pwd -P)"
reported_repo_root="$(scrubbed_git -C "$REPO_ROOT" rev-parse --show-toplevel)"
canonical_reported_root="$(cd "$reported_repo_root" && pwd -P)"
if [[ "$canonical_reported_root" != "$canonical_repo_root" ]]; then
  echo "public API Git worktree mismatch" >&2
  exit 1
fi

git_version="$(scrubbed_git --version)"
if [[ ! "$git_version" =~ ^git\ version\ ([0-9]+)\.([0-9]+) ]]; then
  echo "cannot parse Git version for public API source materialization: $git_version" >&2
  exit 1
fi
git_major="${BASH_REMATCH[1]}"
git_minor="${BASH_REMATCH[2]}"
if ((git_major < 2 || (git_major == 2 && git_minor < 45))); then
  echo "public API source materialization requires Git 2.45 or newer" >&2
  exit 1
fi

actual_source_tree="$(scrubbed_git -C "$REPO_ROOT" rev-parse "$SOURCE_COMMIT^{tree}")"
if [[ "$actual_source_tree" != "$SOURCE_TREE" ]]; then
  echo "public API source tree mismatch: expected $SOURCE_TREE, got $actual_source_tree" >&2
  exit 1
fi
source_object_format="$(scrubbed_git -C "$REPO_ROOT" rev-parse --show-object-format)"
if [[ "$source_object_format" != "sha1" && "$source_object_format" != "sha256" ]]; then
  echo "unsupported Git object format for public API source: $source_object_format" >&2
  exit 1
fi


# git-archive honors export attributes from both the source tree and untracked
# $GIT_DIR/info/attributes. Prove that neither source can omit or rewrite a retained source path.
scrubbed_git -C "$REPO_ROOT" ls-tree -r -t -z --name-only "$SOURCE_COMMIT" \
  >"$TMP/tracked-paths"
scrubbed_git -C "$REPO_ROOT" check-attr \
  --source "$SOURCE_COMMIT" --stdin -z export-ignore export-subst \
  <"$TMP/tracked-paths" >"$TMP/archive-attributes"
"$PYTHON_EXECUTABLE" -I -S -B - "$TMP/archive-attributes" <<'PY'
import sys as _bootstrap_sys

if not (
    _bootstrap_sys.version_info >= (3, 11)
    and _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.dont_write_bytecode
    and _bootstrap_sys.flags.optimize == 0
):
    raise SystemExit("public API materializer helper requires Python 3.11+ -I -S -B")
del _bootstrap_sys

from pathlib import Path
import sys

fields = Path(sys.argv[1]).read_bytes().split(b"\0")
if fields and fields[-1] == b"":
    fields.pop()
if len(fields) % 3:
    raise SystemExit("malformed Git archive-attribute output")
for path, attribute, value in zip(fields[0::3], fields[1::3], fields[2::3]):
    if value not in {b"unspecified", b"unset"}:
        rendered_path = path.decode("utf-8", errors="backslashreplace")
        rendered_attribute = attribute.decode("ascii", errors="backslashreplace")
        raise SystemExit(
            f"public API source materialization rejects {rendered_attribute} on {rendered_path}"
        )
PY
scrubbed_git -C "$REPO_ROOT" ls-tree -r -z "$SOURCE_COMMIT" \
  >"$TMP/source-tree-entries"
"$PYTHON_EXECUTABLE" -I -S -B - "$TMP/source-tree-entries" <<'PY'
import sys as _bootstrap_sys

if not (
    _bootstrap_sys.version_info >= (3, 11)
    and _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.dont_write_bytecode
    and _bootstrap_sys.flags.optimize == 0
):
    raise SystemExit("public API materializer helper requires Python 3.11+ -I -S -B")
del _bootstrap_sys

from pathlib import Path
import sys

records = Path(sys.argv[1]).read_bytes().split(b"\0")
if records and records[-1] == b"":
    records.pop()
for record in records:
    try:
        header, path = record.split(b"\t", 1)
        mode, kind, object_id = header.split(b" ", 2)
    except ValueError as error:
        raise SystemExit("malformed Git tree-entry output") from error
    rendered_path = path.decode("utf-8", errors="backslashreplace")
    components = path.split(b"/")
    if not path or path.startswith(b"/") or any(part in {b"", b".", b".."} for part in components):
        raise SystemExit(f"public API source materialization rejects unsafe path {rendered_path}")
    if mode == b"120000":
        raise SystemExit(
            "public API source materialization rejects tracked symbolic-link entry "
            f"{rendered_path}"
        )
    if mode == b"160000":
        raise SystemExit(
            "public API source materialization rejects Git submodule entry "
            f"{rendered_path}"
        )
    if mode not in {b"100644", b"100755"} or kind != b"blob":
        raise SystemExit(
            "public API source materialization rejects unsupported tree entry "
            f"{mode.decode('ascii', errors='backslashreplace')} {rendered_path}"
        )
    if not object_id or any(byte not in b"0123456789abcdef" for byte in object_id):
        raise SystemExit(f"malformed Git object ID for {rendered_path}")
PY

mkdir "$DESTINATION"
(
  unset TAR_OPTIONS TAR_READER_OPTIONS TAR_WRITER_OPTIONS
  scrubbed_git -C "$REPO_ROOT" archive --format=tar "$SOURCE_COMMIT" \
    | command tar -xf - -C "$DESTINATION"
)

# Compare the raw extracted bytes, paths, and executable modes directly with every source-tree
# entry. Computing blob IDs without Git avoids executing or applying committed clean/text filters.
# The complete path-set check catches archive omissions, substitutions, additions, and link races.
"$PYTHON_EXECUTABLE" -I -S -B - \
  "$TMP/source-tree-entries" "$DESTINATION" "$source_object_format" <<'PY'
import sys as _bootstrap_sys

if not (
    _bootstrap_sys.version_info >= (3, 11)
    and _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.dont_write_bytecode
    and _bootstrap_sys.flags.optimize == 0
):
    raise SystemExit("public API materializer helper requires Python 3.11+ -I -S -B")
del _bootstrap_sys

from pathlib import Path
import hashlib
import os
import stat
import sys

entry_path = Path(sys.argv[1])
root = os.fsencode(sys.argv[2])
object_format = sys.argv[3]

expected: dict[bytes, tuple[bytes, bytes]] = {}
expected_directories: set[bytes] = set()
records = entry_path.read_bytes().split(b"\0")
if records and records[-1] == b"":
    records.pop()
for record in records:
    header, path = record.split(b"\t", 1)
    mode, _kind, object_id = header.split(b" ", 2)
    if path in expected:
        raise SystemExit("duplicate Git tree path in public API source")
    expected[path] = (mode, object_id)
    components = path.split(b"/")
    for length in range(1, len(components)):
        expected_directories.add(b"/".join(components[:length]))

seen_files: set[bytes] = set()
seen_directories: set[bytes] = set()
for current, directories, files in os.walk(root, topdown=True, followlinks=False):
    for name in directories:
        full_path = os.path.join(current, name)
        relative = os.path.relpath(full_path, root)
        metadata = os.lstat(full_path)
        if not stat.S_ISDIR(metadata.st_mode):
            rendered = os.fsdecode(relative)
            raise SystemExit(f"materialized public API source contains a link or special entry: {rendered}")
        seen_directories.add(relative)
    for name in files:
        full_path = os.path.join(current, name)
        relative = os.path.relpath(full_path, root)
        metadata = os.lstat(full_path)
        if not stat.S_ISREG(metadata.st_mode):
            rendered = os.fsdecode(relative)
            raise SystemExit(f"materialized public API source contains a link or special entry: {rendered}")
        if relative not in expected:
            rendered = os.fsdecode(relative)
            raise SystemExit(f"materialized public API source contains an extra path: {rendered}")
        expected_mode, expected_object_id = expected[relative]
        actual_executable = bool(metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        expected_executable = expected_mode == b"100755"
        if actual_executable != expected_executable:
            rendered = os.fsdecode(relative)
            raise SystemExit(f"materialized public API source changed executable mode: {rendered}")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(full_path, flags)
        with os.fdopen(descriptor, "rb") as source:
            opened_metadata = os.fstat(source.fileno())
            if not stat.S_ISREG(opened_metadata.st_mode):
                rendered = os.fsdecode(relative)
                raise SystemExit(
                    f"materialized public API source changed while reading: {rendered}"
                )
            data = source.read()
        digest = hashlib.new(object_format)
        digest.update(b"blob " + str(len(data)).encode("ascii") + b"\0" + data)
        if digest.hexdigest().encode("ascii") != expected_object_id:
            rendered = os.fsdecode(relative)
            raise SystemExit(f"materialized public API source changed retained bytes: {rendered}")
        seen_files.add(relative)

missing_files = set(expected) - seen_files
extra_directories = seen_directories - expected_directories
missing_directories = expected_directories - seen_directories
if missing_files:
    rendered = os.fsdecode(sorted(missing_files)[0])
    raise SystemExit(f"materialized public API source omitted a path: {rendered}")
if extra_directories:
    rendered = os.fsdecode(sorted(extra_directories)[0])
    raise SystemExit(f"materialized public API source contains an extra directory: {rendered}")
if missing_directories:
    rendered = os.fsdecode(sorted(missing_directories)[0])
    raise SystemExit(f"materialized public API source omitted a directory: {rendered}")
PY
