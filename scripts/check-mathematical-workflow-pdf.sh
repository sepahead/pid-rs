#!/usr/bin/env bash
set -euo pipefail

PHASE="${PID_RS_WORKFLOW_PDF_PHASE:-capture}"
case "$PHASE" in
  capture)
    SCRIPT_DIRECTORY="${BASH_SOURCE[0]%/*}"
    if [[ "$SCRIPT_DIRECTORY" == "${BASH_SOURCE[0]}" ]]; then
      SCRIPT_DIRECTORY="."
    fi
    ROOT="$(cd "$SCRIPT_DIRECTORY/.." && pwd -P)"
    ;;
  verify)
    if [[ -z "${PID_RS_WORKFLOW_PDF_ROOT:-}" || -z "${PID_RS_WORKFLOW_PDF_BUILD_ROOT:-}" \
        || -z "${PID_RS_WORKFLOW_PDF_SAFE_PATH:-}" ]]; then
      echo "mathematical workflow PDF check: captured phase lacks its bootstrap custody" >&2
      exit 2
    fi
    ROOT="$PID_RS_WORKFLOW_PDF_ROOT"
    ;;
  *)
    echo "mathematical workflow PDF check: invalid internal phase" >&2
    exit 2
    ;;
esac
SOURCE="audit/formal/latex/mathematical-problem-solving-workflow.tex"
MARKDOWN="MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md"
COMMITTED="output/pdf/mathematical-problem-solving-workflow.pdf"
RENDERING_RECEIPT="output/pdf/mathematical-problem-solving-workflow.rendering-receipt.tsv"
VISUAL_RECEIPT="audit/evidence/mathematical-workflow-visual-receipt-2026-08-12.md"
SHARED_STYLE="audit/formal/latex/pid-rs-report-tables.sty"
PUBLICATION_STYLE="audit/formal/latex/pid-rs-workflow-publication.sty"
FIGURE_DIR="audit/formal/latex/figures/mathematical-workflow"
REPORT_STEM="mathematical-problem-solving-workflow"
ENTRY_WRAPPER_NAME="pid-rs-map-file-free-entry.tex"
SOURCE_DATE_EPOCH_VALUE="1785715200"
RENDER_DPI=120
EXPECTED_PAGES=64
EXPECTED_PYPDF_VERSION="6.14.2"
MODE="${1:---exact}"
CHECK_NAME="mathematical workflow PDF check"

FIGURE_STEMS=(
  "four-object-assurance-chain"
  "obligation-dag-minimal-cuts"
  "shared-oracle-correlated-routes"
  "invalidation-publication-state-machine"
)

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" && "$MODE" != "--refresh" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain|--refresh]" >&2
  exit 2
fi

commands=(
  python3
  awk
  bash
  basename
  cat
  chmod
  cmp
  cp
  env
  fc-cache
  find
  grep
  kpsewhich
  ln
  lualatex
  luaotfload-tool
  texlua
  mkdir
  mktemp
  mv
  pdffonts
  pdfinfo
  pdftoppm
  pdftotext
  ps
  rm
  rsvg-convert
  sed
  sleep
  xmllint
)

# The capture phase may start in an ordinary interactive environment, but it must not silently
# promote an executable from a repository, home directory, or temporary-directory PATH prefix into
# the trusted computing base.  These prefixes cover the system package managers used by the local
# Darwin replay and the pinned hosted Ubuntu replay.  They are an admission boundary, not an
# authenticity claim; exact executable bytes are recorded below for every accepted run.
trusted_executable_path() {
  case "$1" in
    /bin/* | /sbin/* | /usr/bin/* | /usr/sbin/* | /usr/local/* \
      | /opt/homebrew/* | /opt/hostedtoolcache/* | /opt/texlive/* | /Library/TeX/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

BOOTSTRAP_PYTHON="$(type -P python3 || true)"
if [[ -z "$BOOTSTRAP_PYTHON" ]]; then
  echo "$CHECK_NAME: missing command: python3" >&2
  exit 2
fi
if [[ "$BOOTSTRAP_PYTHON" != /* || ! -f "$BOOTSTRAP_PYTHON" || ! -x "$BOOTSTRAP_PYTHON" ]] \
    || ! trusted_executable_path "$BOOTSTRAP_PYTHON"; then
  echo "$CHECK_NAME: bootstrap python is outside the admitted executable roots: $BOOTSTRAP_PYTHON" >&2
  exit 2
fi
command_paths=()
safe_path_components=()
for command in "${commands[@]}"; do
  command_path="$(type -P "$command" || true)"
  if [[ -z "$command_path" ]]; then
    echo "$CHECK_NAME: missing command: $command" >&2
    exit 2
  fi
  if [[ "$command_path" != /* ]] || ! trusted_executable_path "$command_path"; then
    echo "$CHECK_NAME: command is outside the admitted executable roots: $command: $command_path" >&2
    exit 2
  fi
  command_search_path="$command_path"
  command_path="$("$BOOTSTRAP_PYTHON" -I -S -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$command_path")"
  if [[ ! -f "$command_path" || ! -x "$command_path" ]]; then
    echo "$CHECK_NAME: command does not resolve to a regular executable: $command" >&2
    exit 2
  fi
  if ! trusted_executable_path "$command_path"; then
    echo "$CHECK_NAME: resolved command escapes the admitted executable roots: $command: $command_path" >&2
    exit 2
  fi
  command_paths+=("$command_path")
  safe_path_components+=("${command_search_path%/*}")
done

SAFE_PATH=""
for path_component in "${safe_path_components[@]}"; do
  case ":$SAFE_PATH:" in
    *":$path_component:"*) ;;
    *)
      if [[ -n "$SAFE_PATH" ]]; then
        SAFE_PATH+=":"
      fi
      SAFE_PATH+="$path_component"
      ;;
  esac
done
if [[ "$PHASE" == "verify" && "$SAFE_PATH" != "$PID_RS_WORKFLOW_PDF_SAFE_PATH" ]]; then
  echo "$CHECK_NAME: captured executable search path drifted" >&2
  exit 2
fi
PATH="$SAFE_PATH"
export PATH
verify_command_resolution() {
  local command
  local command_index
  local observed_path
  local resolver="${command_paths[0]}"
  for command_index in "${!commands[@]}"; do
    command="${commands[$command_index]}"
    observed_path="$(type -P "$command" || true)"
    if [[ -z "$observed_path" ]]; then
      echo "$CHECK_NAME: captured command disappeared from the isolated search path: $command" >&2
      exit 2
    fi
    observed_path="$("$resolver" -I -S -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$observed_path")"
    if [[ "$observed_path" != "${command_paths[$command_index]}" ]]; then
      echo "$CHECK_NAME: isolated search path resolves different executable bytes: $command" >&2
      exit 2
    fi
  done
}

# COMMAND_RESOLUTION_INITIAL: bind commands before the lock/re-exec transition.
verify_command_resolution
BASH_EXECUTABLE="$(type -P bash)"
ENV_EXECUTABLE="$(type -P env)"
CLEAN_BASE_ENV=("PATH=$SAFE_PATH" "LC_ALL=C" "LANG=C" "TZ=UTC")

# Serialize every source capture, build, comparison, and refresh that cooperates with this
# publication pipeline.  The lock is outside the repository so acquiring it cannot perturb the
# captured root-directory metadata.  The inherited descriptor is revalidated after the clean-env
# phase transition below; an environment variable alone is never accepted as proof that the lock
# is held.  This is an advisory same-host writer lock, not protection from a privileged process or
# an uncooperative process that deliberately ignores it.
LOCK_CHECKER_DIRECTORY="${BASH_SOURCE[0]%/*}"
if [[ "$LOCK_CHECKER_DIRECTORY" == "${BASH_SOURCE[0]}" ]]; then
  LOCK_CHECKER_DIRECTORY="."
fi
LOCK_CHECKER="$(cd "$LOCK_CHECKER_DIRECTORY" && pwd -P)/${BASH_SOURCE[0]##*/}"
LOCK_BOOTSTRAP_PARENT=0
if [[ -z "${PID_RS_WORKFLOW_PDF_LOCK_FD+x}" \
    && -z "${PID_RS_WORKFLOW_PDF_LOCK_ROOT_SHA256+x}" ]]; then
  # The Python child acquires the descriptor and then replaces itself with a lock-bearing copy of
  # this script.  The original shell must terminate with that child's exact status; otherwise it
  # would continue without the inherited variables after the lock-bearing copy finishes.
  LOCK_BOOTSTRAP_PARENT=1
elif [[ -z "${PID_RS_WORKFLOW_PDF_LOCK_FD+x}" \
    || -z "${PID_RS_WORKFLOW_PDF_LOCK_ROOT_SHA256+x}" ]]; then
  echo "$CHECK_NAME: publication lock environment is only partially specified" >&2
  exit 2
fi
if python3 -I -S - \
  "$ROOT" \
  "$LOCK_CHECKER" \
  "$MODE" \
  "$BASH_EXECUTABLE" <<'PY'
from __future__ import annotations

import fcntl
import hashlib
import os
from pathlib import Path
import stat
import sys


def fail(detail: str) -> None:
    raise SystemExit(f"mathematical workflow PDF check: publication lock {detail}")


root = Path(sys.argv[1]).resolve(strict=True)
script = Path(sys.argv[2]).resolve(strict=True)
mode = sys.argv[3]
bash = str(Path(sys.argv[4]).resolve(strict=True))
lock_root = Path("/tmp").resolve(strict=True)
root_digest = hashlib.sha256(os.fsencode(str(root))).hexdigest()
lock_path = lock_root / f"pid-rs-mathematical-workflow-{os.getuid()}-{root_digest}.lock"


def validate_lock_file(descriptor: int) -> None:
    try:
        named = lock_path.lstat()
        opened = os.fstat(descriptor)
    except OSError as error:
        fail(f"cannot validate {lock_path}: {error}")
    if not stat.S_ISREG(named.st_mode) or not stat.S_ISREG(opened.st_mode):
        fail("path is not a regular file")
    if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
        fail("path and inherited descriptor identify different files")
    if named.st_nlink != 1 or opened.st_nlink != 1:
        fail("file is not single-link")
    if named.st_uid != os.getuid() or opened.st_uid != os.getuid():
        fail("file is not owned by the current user")
    if stat.S_IMODE(named.st_mode) != 0o600 or stat.S_IMODE(opened.st_mode) != 0o600:
        fail("file mode is not 0600")


has_descriptor = "PID_RS_WORKFLOW_PDF_LOCK_FD" in os.environ
has_root_digest = "PID_RS_WORKFLOW_PDF_LOCK_ROOT_SHA256" in os.environ
if has_descriptor or has_root_digest:
    if not has_descriptor or not has_root_digest:
        fail("environment is only partially specified")
    raw_descriptor = os.environ["PID_RS_WORKFLOW_PDF_LOCK_FD"]
    held_digest = os.environ["PID_RS_WORKFLOW_PDF_LOCK_ROOT_SHA256"]
    if not raw_descriptor.isdigit():
        fail("inherited descriptor is not a decimal integer")
    if held_digest != root_digest:
        fail("inherited repository-root digest differs")
    descriptor = int(raw_descriptor)
    validate_lock_file(descriptor)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fail("inherited descriptor does not own the exclusive lock")
    raise SystemExit(0)

descriptor = os.open(
    lock_path,
    os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
    0o600,
)
validate_lock_file(descriptor)
fcntl.flock(descriptor, fcntl.LOCK_EX)
validate_lock_file(descriptor)
os.set_inheritable(descriptor, True)
environment = os.environ.copy()
environment["PID_RS_WORKFLOW_PDF_LOCK_FD"] = str(descriptor)
environment["PID_RS_WORKFLOW_PDF_LOCK_ROOT_SHA256"] = root_digest
os.execve(
    bash,
    [bash, "--noprofile", "--norc", str(script), mode],
    environment,
)
PY
then
  LOCK_BOOTSTRAP_STATUS=0
else
  LOCK_BOOTSTRAP_STATUS=$?
fi
if [[ "$LOCK_BOOTSTRAP_STATUS" -ne 0 ]]; then
  exit "$LOCK_BOOTSTRAP_STATUS"
fi
if [[ "$LOCK_BOOTSTRAP_PARENT" -eq 1 ]]; then
  exit 0
fi

sha256_file() {
  python3 -I -S -c \
    'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' \
    "$1"
}

if ! python3 -I -S -c 'import sys, sysconfig; [sys.path.insert(0, p) for p in dict.fromkeys((sysconfig.get_path("purelib"), sysconfig.get_path("platlib"))) if p]; import pypdf; sys.exit(pypdf.__version__ != sys.argv[1])' \
    "$EXPECTED_PYPDF_VERSION" >/dev/null 2>&1; then
  echo "$CHECK_NAME: exact Python package pypdf==$EXPECTED_PYPDF_VERSION is required" >&2
  exit 2
fi

require_safe_path() {
  local candidate="$1"
  local label="$2"
  if [[ ! "$candidate" =~ ^/[A-Za-z0-9._/-]+$ || "$candidate" == *//* ]]; then
    echo "$CHECK_NAME: $label is unsafe for Kpathsea/XML list syntax: $candidate" >&2
    exit 2
  fi
}

require_safe_path "$ROOT" "repository root"
if [[ "$(cd "$ROOT" && pwd -P)" != "$ROOT" ]]; then
  echo "$CHECK_NAME: repository root is not canonical" >&2
  exit 2
fi
# COMMAND_RESOLUTION_PRE_MANIFEST: bind search results immediately before phase custody capture.
verify_command_resolution
if [[ "$PHASE" == "capture" ]]; then
  TMP_ROOT_RAW="${TMPDIR:-/tmp}"
  if [[ ! -d "$TMP_ROOT_RAW" ]]; then
    echo "$CHECK_NAME: temporary root is not a directory" >&2
    exit 2
  fi
  # Kpathsea assigns recursive-search meaning to a double slash. macOS TMPDIR normally ends in a
  # slash, so canonicalize before composing any TEXMF path; otherwise a hostile sibling symlink can
  # turn an apparently isolated build into an ambient filesystem crawl.
  TMP_ROOT="$(cd "$TMP_ROOT_RAW" && pwd -P)"
  require_safe_path "$TMP_ROOT" "temporary root"
  BUILD_ROOT="$(mktemp -d "$TMP_ROOT/pid-rs-mathematical-workflow-pdf.XXXXXX")"
  BUILD_ROOT="$(cd "$BUILD_ROOT" && pwd -P)"
else
  BUILD_ROOT="$(cd "$PID_RS_WORKFLOW_PDF_BUILD_ROOT" && pwd -P)"
  if [[ "$BUILD_ROOT" != "$PID_RS_WORKFLOW_PDF_BUILD_ROOT" ]]; then
    echo "$CHECK_NAME: captured build-root identity drifted" >&2
    exit 2
  fi
fi
require_safe_path "$BUILD_ROOT" "canonical build root"
cleanup_build_root() {
  local status=$?
  local build_parent="${BUILD_ROOT%/*}"
  trap - EXIT
  if [[ -n "${BUILD_ROOT:-}" \
      && "$BUILD_ROOT" == "$build_parent"/pid-rs-mathematical-workflow-pdf.* \
      && "$BUILD_ROOT" != "$build_parent" ]]; then
    # The captured source tree is deliberately mode 0555/0444.  On platforms whose rm refuses to
    # descend through a non-writable directory (including Darwin), first restore owner write
    # permission on this already-canonicalized, exact temporary root.  A preparation failure is a
    # gate failure even if a later best-effort removal happens to succeed.
    local cleanup_failed=0
    if ! chmod -R u+w "$BUILD_ROOT"; then
      echo "$CHECK_NAME: failed to make the exact temporary build root removable: $BUILD_ROOT" >&2
      cleanup_failed=1
    fi
    if ! rm -rf -- "$BUILD_ROOT"; then
      echo "$CHECK_NAME: failed to remove the exact temporary build root: $BUILD_ROOT" >&2
      cleanup_failed=1
    fi
    if [[ "$cleanup_failed" -ne 0 && "$status" -eq 0 ]]; then
      status=2
    fi
  else
    echo "$CHECK_NAME: refusing ambiguous temporary-build cleanup: ${BUILD_ROOT:-unset}" >&2
    if [[ "$status" -eq 0 ]]; then
      status=2
    fi
  fi
  exit "$status"
}
trap cleanup_build_root EXIT

capture_executable_manifest() {
  local output="$1"
  python3 -I -S - "$output" "${#commands[@]}" "${commands[@]}" "${command_paths[@]}" <<'PY'
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shlex
import stat
import sys


def fail(detail: str) -> None:
    raise SystemExit(f"mathematical workflow PDF check: executable capture {detail}")


def fingerprint(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


output = Path(sys.argv[1])
count = int(sys.argv[2])
names = sys.argv[3 : 3 + count]
paths = sys.argv[3 + count :]
if len(names) != count or len(paths) != count or len(set(names)) != count:
    fail("received an invalid command inventory")
rows = ["schema\tpid-rs-formal-pdf-executable-manifest-v1\n"]
captured_paths = {Path(raw_path).resolve() for raw_path in paths}
path_by_name = dict(zip(names, paths, strict=True))
shebangs: list[tuple[str, Path, bytes]] = []
for name, raw_path in zip(names, paths, strict=True):
    path = Path(raw_path)
    before_name = path.lstat()
    if not stat.S_ISREG(before_name.st_mode):
        fail(f"path is not a regular non-symlink file: {name}: {path}")
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        before = os.fstat(descriptor)
        if (before.st_dev, before.st_ino) != (before_name.st_dev, before_name.st_ino):
            fail(f"path changed during open: {name}: {path}")
        if before.st_size > 512 * 1024 * 1024:
            fail(f"file exceeds the 512 MiB executable-capture bound: {name}: {path}")
        digest = hashlib.sha256()
        byte_count = 0
        prefix = bytearray()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            if len(prefix) < 4097:
                prefix.extend(chunk[: 4097 - len(prefix)])
            digest.update(chunk)
            byte_count += len(chunk)
        after = os.fstat(descriptor)
        if fingerprint(before) != fingerprint(after) or byte_count != before.st_size:
            fail(f"file changed during capture: {name}: {path}")
    finally:
        os.close(descriptor)
    if prefix.startswith(b"#!"):
        newline = prefix.find(b"\n")
        if newline < 0:
            if byte_count > len(prefix):
                fail(f"shebang exceeds the 4096-byte parser bound: {name}: {path}")
            shebang = bytes(prefix)
        else:
            if newline > 4096:
                fail(f"shebang exceeds the 4096-byte parser bound: {name}: {path}")
            shebang = bytes(prefix[:newline])
        shebangs.append((name, path, shebang))
    rows.append(f"{name}\t{path}\t{byte_count}\t{digest.hexdigest()}\n")


def require_captured_path(raw: str, label: str) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute():
        fail(f"{label} is not an absolute interpreter path: {raw!r}")
    resolved = candidate.resolve()
    if resolved not in captured_paths:
        fail(f"{label} interpreter bytes are absent from the executable manifest: {resolved}")
    return resolved


for name, path, shebang in shebangs:
    try:
        fields = shlex.split(shebang[2:].decode("utf-8"), posix=True)
    except (UnicodeDecodeError, ValueError) as error:
        fail(f"cannot parse shebang for {name}: {path}: {error}")
    if not fields:
        fail(f"shebang names no interpreter: {name}: {path}")
    interpreter = require_captured_path(fields[0], f"shebang for {name}")
    if interpreter.name == "env":
        if len(fields) != 2 or fields[1].startswith("-") or "=" in fields[1]:
            fail(f"env shebang has an unsupported argument form: {name}: {path}")
        delegated = fields[1]
        if "/" in delegated:
            require_captured_path(delegated, f"delegated shebang for {name}")
        elif delegated not in path_by_name:
            fail(
                f"delegated shebang interpreter is absent from the executable manifest: "
                f"{name}: {delegated}"
            )
    elif len(fields) < 1:
        fail(f"direct shebang is malformed: {name}: {path}")
output.write_text("".join(rows), encoding="utf-8", newline="\n")
PY
}

capture_pypdf_manifest() {
  local output="$1"
  python3 -I -S - "$output" "$EXPECTED_PYPDF_VERSION" <<'PY'
from __future__ import annotations

import hashlib
import importlib.metadata
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import sysconfig


def fail(detail: str) -> None:
    raise SystemExit(f"mathematical workflow PDF check: pypdf capture {detail}")


def fingerprint(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


output = Path(sys.argv[1])
expected_version = sys.argv[2]
package_roots = tuple(
    Path(raw).resolve()
    for raw in dict.fromkeys((sysconfig.get_path("purelib"), sysconfig.get_path("platlib")))
    if raw
)
for root in package_roots:
    sys.path.insert(0, str(root))
distribution = importlib.metadata.distribution("pypdf")
if distribution.version != expected_version:
    fail(f"version differs: {distribution.version!r}")
files = distribution.files
if not files:
    fail("distribution exposes no installed-file inventory")
rows = [f"schema\tpid-rs-python-distribution-manifest-v1\npypdf\t{expected_version}\n"]
aggregate = 0
seen: set[str] = set()
for package_path in sorted(files, key=lambda value: str(value)):
    relative = PurePosixPath(str(package_path).replace(os.sep, "/"))
    if relative.is_absolute() or not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        fail(f"contains a noncanonical distribution path: {str(package_path)!r}")
    canonical = relative.as_posix()
    if canonical in seen:
        fail(f"contains a duplicate distribution path: {canonical!r}")
    seen.add(canonical)
    path = Path(distribution.locate_file(package_path)).resolve()
    if not any(path == root or root in path.parents for root in package_roots):
        fail(f"installed path escapes the declared Python package roots: {path}")
    before_name = path.lstat()
    if not stat.S_ISREG(before_name.st_mode) or stat.S_ISLNK(before_name.st_mode):
        fail(f"installed path is not a regular non-symlink file: {path}")
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        before = os.fstat(descriptor)
        if (before.st_dev, before.st_ino) != (before_name.st_dev, before_name.st_ino):
            fail(f"installed path changed during open: {path}")
        digest = hashlib.sha256()
        byte_count = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            byte_count += len(chunk)
        after = os.fstat(descriptor)
        if fingerprint(before) != fingerprint(after) or byte_count != before.st_size:
            fail(f"installed path changed during capture: {path}")
    finally:
        os.close(descriptor)
    aggregate += byte_count
    if aggregate > 64 * 1024 * 1024:
        fail("distribution closure exceeds the 64 MiB aggregate bound")
    rows.append(f"{canonical}\t{path}\t{byte_count}\t{digest.hexdigest()}\n")
output.write_text("".join(rows), encoding="utf-8", newline="\n")
PY
}

if [[ "$PHASE" == "capture" ]]; then
  capture_executable_manifest "$BUILD_ROOT/executables.before.tsv"
  capture_pypdf_manifest "$BUILD_ROOT/pypdf.before.tsv"
else
  capture_executable_manifest "$BUILD_ROOT/executables.verify.tsv"
  if ! cmp -s "$BUILD_ROOT/executables.before.tsv" "$BUILD_ROOT/executables.verify.tsv"; then
    echo "$CHECK_NAME: executable identities changed between capture and verification" >&2
    exit 1
  fi
  capture_pypdf_manifest "$BUILD_ROOT/pypdf.verify.tsv"
  if ! cmp -s "$BUILD_ROOT/pypdf.before.tsv" "$BUILD_ROOT/pypdf.verify.tsv"; then
    echo "$CHECK_NAME: pypdf installed-file identities changed between capture and verification" >&2
    exit 1
  fi
fi

SNAPSHOT_ROOT="$BUILD_ROOT/source-snapshot"
if [[ "$PHASE" == "capture" ]]; then
  mkdir -p "$SNAPSHOT_ROOT" "$BUILD_ROOT/tmp"
elif [[ ! -d "$SNAPSHOT_ROOT" || ! -f "$BUILD_ROOT/root-inputs.before.tsv" \
    || ! -f "$BUILD_ROOT/snapshot-inputs.tsv" ]]; then
  echo "$CHECK_NAME: captured phase lacks its read-only source snapshot" >&2
  exit 2
fi

manifest_paths=(
  "scripts/check-mathematical-workflow-pdf.sh"
  "scripts/check-mathematical-workflow-pdf-self-test.sh"
  "scripts/sync-mathematical-workflow-tex.py"
  "scripts/check-citation-edge-countermodel.py"
  "scripts/check-citation-edge-countermodel-self-test.py"
  "audit/evidence/x-thread-citation-edge-application.json"
  "audit/evidence/x-thread-citation-source-manifest.json"
  "$SOURCE"
  "$MARKDOWN"
  "$SHARED_STYLE"
  "$PUBLICATION_STYLE"
  "audit/formal/requirements-pdf.txt"
  "scripts/check-formal-pdf-log.sh"
  "scripts/check-formal-pdf-log-self-test.sh"
  "scripts/compare-formal-pdf-renders.py"
  "scripts/compare-formal-pdf-renders-self-test.py"
  "scripts/sync-mathematical-workflow-tex-self-test.py"
)
if [[ "$MODE" != "--refresh" ]]; then
  # Refresh is the bootstrap/update operation for the report PDF, its rendering receipt, and the
  # four SVG-derived figure PDFs.  The independent visual receipt is rebound only after a human or
  # agent actually inspects the refreshed pages.  Treating stale or absent output bytes as source
  # inputs made a clean refresh impossible and falsely enlarged the build dependency closure.
  # Exact and cross-toolchain modes still capture the report, rendering, and visual records.
  manifest_paths+=("$COMMITTED" "$RENDERING_RECEIPT" "$VISUAL_RECEIPT")
fi
for stem in "${FIGURE_STEMS[@]}"; do
  manifest_paths+=("$FIGURE_DIR/$stem.svg")
  if [[ "$MODE" != "--refresh" ]]; then
    manifest_paths+=("$FIGURE_DIR/$stem.pdf")
  fi
done

capture_manifest() {
  local base="$1"
  local output="$2"
  local snapshot_destination="$3"
  python3 -I -S - \
    "$base" \
    "$output" \
    "$snapshot_destination" \
    "$FIGURE_DIR" \
    "${#FIGURE_STEMS[@]}" \
    "${FIGURE_STEMS[@]}" \
    "${manifest_paths[@]}" <<'PY'
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from pathlib import PurePosixPath
import stat
import sys


def fail(detail: str) -> None:
    print(f"mathematical workflow PDF check: source capture {detail}", file=sys.stderr)
    raise SystemExit(1)


def flags(*names: str) -> int:
    value = 0
    for name in names:
        value |= getattr(os, name, 0)
    return value


def fingerprint(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def split_relative(raw: str) -> tuple[str, ...]:
    path = PurePosixPath(raw)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        fail(f"noncanonical relative path: {raw!r}")
    canonical = path.as_posix()
    if canonical != raw:
        fail(f"noncanonical path spelling: {raw!r}")
    return path.parts


def read_regular_beneath(root_fd: int, raw: str) -> bytes:
    parts = split_relative(raw)
    parent_fd = os.dup(root_fd)
    directory_fds = [parent_fd]
    opened: list[tuple[int, int, str, tuple[int, ...]]] = []
    try:
        for component in parts[:-1]:
            before = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            if not stat.S_ISDIR(before.st_mode):
                fail(f"path component is not a real directory: {raw!r}: {component!r}")
            child_fd = os.open(
                component,
                flags("O_RDONLY", "O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC"),
                dir_fd=parent_fd,
            )
            child_stat = os.fstat(child_fd)
            if (before.st_dev, before.st_ino) != (child_stat.st_dev, child_stat.st_ino):
                fail(f"directory component changed during open: {raw!r}: {component!r}")
            opened.append((parent_fd, child_fd, component, fingerprint(child_stat)))
            parent_fd = child_fd
            directory_fds.append(child_fd)

        leaf = parts[-1]
        before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            fail(f"input is not a regular non-symlink file: {raw!r}")
        leaf_fd = os.open(
            leaf,
            flags("O_RDONLY", "O_NOFOLLOW", "O_NONBLOCK", "O_CLOEXEC"),
            dir_fd=parent_fd,
        )
        try:
            opened_leaf = os.fstat(leaf_fd)
            if (before.st_dev, before.st_ino) != (opened_leaf.st_dev, opened_leaf.st_ino):
                fail(f"input changed during open: {raw!r}")
            if not stat.S_ISREG(opened_leaf.st_mode) or opened_leaf.st_nlink != 1:
                fail(f"input is not a single-link regular file: {raw!r}")
            if opened_leaf.st_size > 32 * 1024 * 1024:
                fail(f"input exceeds the 32 MiB per-file capture bound: {raw!r}")
            chunks: list[bytes] = []
            remaining = opened_leaf.st_size
            while remaining:
                chunk = os.read(leaf_fd, min(remaining, 1024 * 1024))
                if not chunk:
                    fail(f"input truncated during capture: {raw!r}")
                chunks.append(chunk)
                remaining -= len(chunk)
            if os.read(leaf_fd, 1):
                fail(f"input grew during capture: {raw!r}")
            after_leaf = os.fstat(leaf_fd)
            after_name = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
            if fingerprint(opened_leaf) != fingerprint(after_leaf) or (
                after_name.st_dev,
                after_name.st_ino,
            ) != (opened_leaf.st_dev, opened_leaf.st_ino):
                fail(f"input identity or metadata changed during capture: {raw!r}")
            data = b"".join(chunks)
            if len(data) != opened_leaf.st_size:
                fail(f"input size changed during capture: {raw!r}")
        finally:
            os.close(leaf_fd)

        for ancestor_fd, child_fd, component, expected in reversed(opened):
            current = os.stat(component, dir_fd=ancestor_fd, follow_symlinks=False)
            if fingerprint(current) != expected:
                fail(f"directory component changed during capture: {raw!r}: {component!r}")
        return data
    except OSError as error:
        fail(f"cannot capture {raw!r}: {error}")
    finally:
        for directory_fd in reversed(directory_fds):
            try:
                os.close(directory_fd)
            except OSError:
                pass


base = Path(sys.argv[1])
output = Path(sys.argv[2])
snapshot_raw = sys.argv[3]
figure_directory_raw = sys.argv[4]
stem_count = int(sys.argv[5])
stems = sys.argv[6 : 6 + stem_count]
manifest_raw = sys.argv[6 + stem_count :]
if len(manifest_raw) != len(set(manifest_raw)):
    fail("manifest contains duplicate paths")
required_figure_names = {f"{stem}.svg" for stem in stems}
allowed_figure_names = {
    f"{stem}.{suffix}" for stem in stems for suffix in ("pdf", "svg")
}
figure_pdf_paths = {f"{figure_directory_raw}/{stem}.pdf" for stem in stems}
pdf_inventory_is_input = figure_pdf_paths <= set(manifest_raw)
root_fd = os.open(base, flags("O_RDONLY", "O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC"))
root_before = fingerprint(os.fstat(root_fd))
rows: list[str] = []
aggregate = 0
try:
    figure_parts = split_relative(figure_directory_raw)
    figure_fd = os.dup(root_fd)
    try:
        for component in figure_parts:
            child_fd = os.open(
                component,
                flags("O_RDONLY", "O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC"),
                dir_fd=figure_fd,
            )
            os.close(figure_fd)
            figure_fd = child_fd
        actual_names = set(os.listdir(figure_fd))
        missing_names = required_figure_names - actual_names
        extra_names = actual_names - allowed_figure_names
        missing_input_pdfs = (
            allowed_figure_names - actual_names if pdf_inventory_is_input else set()
        )
        if missing_names or extra_names or missing_input_pdfs:
            fail(
                "figure directory inventory differs; "
                f"missing={sorted(missing_names | missing_input_pdfs)!r}; "
                f"extra={sorted(extra_names)!r}"
            )
        for name in actual_names:
            entry = os.stat(name, dir_fd=figure_fd, follow_symlinks=False)
            if not stat.S_ISREG(entry.st_mode) or entry.st_nlink != 1:
                fail(f"figure inventory entry is not a single-link regular file: {name!r}")
    finally:
        os.close(figure_fd)

    snapshot = Path(snapshot_raw) if snapshot_raw else None
    for relative_raw in manifest_raw:
        data = read_regular_beneath(root_fd, relative_raw)
        aggregate += len(data)
        if aggregate > 64 * 1024 * 1024:
            fail("manifest exceeds the 64 MiB aggregate capture bound")
        rows.append(f"{relative_raw}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}\n")
        if snapshot is not None:
            destination = snapshot / PurePosixPath(relative_raw)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(data)
finally:
    if fingerprint(os.fstat(root_fd)) != root_before:
        fail("capture root directory metadata changed during manifest construction")
    os.close(root_fd)
output.write_text("".join(rows), encoding="utf-8", newline="\n")
PY
}

verify_snapshot_readonly() {
  python3 -I -S - "$SNAPSHOT_ROOT" "${manifest_paths[@]}" <<'PY'
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import stat
import sys


def fail(detail: str) -> None:
    raise SystemExit(f"mathematical workflow PDF check: read-only snapshot {detail}")


root = Path(sys.argv[1])
expected_files = set(sys.argv[2:])
expected_directories = {"."}
for raw in expected_files:
    path = PurePosixPath(raw)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        fail(f"received a noncanonical manifest path: {raw!r}")
    for index in range(1, len(path.parts)):
        expected_directories.add(PurePosixPath(*path.parts[:index]).as_posix())

actual_files: set[str] = set()
actual_directories = {"."}
root_status = root.lstat()
if not stat.S_ISDIR(root_status.st_mode) or stat.S_IMODE(root_status.st_mode) != 0o555:
    fail("root is not a mode-0555 real directory")
for current_raw, directory_names, file_names in os.walk(root, topdown=True, followlinks=False):
    current = Path(current_raw)
    for name in sorted(directory_names):
        path = current / name
        status = path.lstat()
        relative = path.relative_to(root).as_posix()
        if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
            fail(f"contains a non-directory path component: {relative!r}")
        if stat.S_IMODE(status.st_mode) != 0o555:
            fail(f"directory mode drifted from 0555: {relative!r}")
        actual_directories.add(relative)
    for name in sorted(file_names):
        path = current / name
        status = path.lstat()
        relative = path.relative_to(root).as_posix()
        if not stat.S_ISREG(status.st_mode) or stat.S_ISLNK(status.st_mode):
            fail(f"contains a non-regular file: {relative!r}")
        if status.st_nlink != 1 or stat.S_IMODE(status.st_mode) != 0o444:
            fail(f"file is not a single-link mode-0444 regular file: {relative!r}")
        actual_files.add(relative)
if actual_files != expected_files:
    fail(
        "file inventory drifted; "
        f"missing={sorted(expected_files - actual_files)!r}; "
        f"extra={sorted(actual_files - expected_files)!r}"
    )
if actual_directories != expected_directories:
    fail(
        "directory inventory drifted; "
        f"missing={sorted(expected_directories - actual_directories)!r}; "
        f"extra={sorted(actual_directories - expected_directories)!r}"
    )
PY
}

if [[ "$PHASE" == "capture" ]]; then
  capture_manifest "$ROOT" "$BUILD_ROOT/root-inputs.before.tsv" "$SNAPSHOT_ROOT"
  capture_manifest "$SNAPSHOT_ROOT" "$BUILD_ROOT/snapshot-inputs.tsv" ""
  if ! cmp -s "$BUILD_ROOT/root-inputs.before.tsv" "$BUILD_ROOT/snapshot-inputs.tsv"; then
    echo "$CHECK_NAME: source snapshot differs from the initial repository inputs" >&2
    exit 1
  fi
  python3 -I -S - "$SNAPSHOT_ROOT" <<'PY'
from pathlib import Path
import stat
import sys


root = Path(sys.argv[1])
entries = sorted(root.rglob("*"), key=lambda path: len(path.parts), reverse=True)
for path in entries:
    status = path.lstat()
    if stat.S_ISLNK(status.st_mode):
        raise SystemExit(f"mathematical workflow PDF check: snapshot unexpectedly contains symlink: {path}")
    if stat.S_ISREG(status.st_mode):
        path.chmod(0o444)
    elif stat.S_ISDIR(status.st_mode):
        path.chmod(0o555)
    else:
        raise SystemExit(f"mathematical workflow PDF check: snapshot contains unsupported object: {path}")
root.chmod(0o555)
PY
  verify_snapshot_readonly
  mkdir -p "$BUILD_ROOT/bootstrap-home"
  exec "$ENV_EXECUTABLE" -i \
    "${CLEAN_BASE_ENV[@]}" \
    "HOME=$BUILD_ROOT/bootstrap-home" \
    "TMPDIR=$BUILD_ROOT/tmp" \
    "PYTHONDONTWRITEBYTECODE=1" \
    "SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH_VALUE" \
    "PID_RS_WORKFLOW_PDF_PHASE=verify" \
    "PID_RS_WORKFLOW_PDF_ROOT=$ROOT" \
    "PID_RS_WORKFLOW_PDF_BUILD_ROOT=$BUILD_ROOT" \
    "PID_RS_WORKFLOW_PDF_SAFE_PATH=$SAFE_PATH" \
    "PID_RS_WORKFLOW_PDF_LOCK_FD=$PID_RS_WORKFLOW_PDF_LOCK_FD" \
    "PID_RS_WORKFLOW_PDF_LOCK_ROOT_SHA256=$PID_RS_WORKFLOW_PDF_LOCK_ROOT_SHA256" \
    "$BASH_EXECUTABLE" --noprofile --norc \
    "$SNAPSHOT_ROOT/scripts/check-mathematical-workflow-pdf.sh" "$MODE"
fi

expected_checker="$SNAPSHOT_ROOT/scripts/check-mathematical-workflow-pdf.sh"
actual_checker_directory="${BASH_SOURCE[0]%/*}"
actual_checker="$(cd "$actual_checker_directory" && pwd -P)/${BASH_SOURCE[0]##*/}"
if [[ "$actual_checker" != "$expected_checker" ]]; then
  echo "$CHECK_NAME: verification phase is not executing the captured checker bytes" >&2
  exit 2
fi
if ! cmp -s "$BUILD_ROOT/root-inputs.before.tsv" "$BUILD_ROOT/snapshot-inputs.tsv"; then
  echo "$CHECK_NAME: captured source manifest lost its initial equality" >&2
  exit 1
fi
verify_snapshot_readonly

python3 -I -S - \
  "$SNAPSHOT_ROOT/$SOURCE" \
  "$SNAPSHOT_ROOT/$MARKDOWN" \
  "$SNAPSHOT_ROOT/$PUBLICATION_STYLE" \
  "${FIGURE_STEMS[@]}" <<'PY'
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys


def fail(detail: str) -> None:
    print(f"mathematical workflow PDF check: {detail}", file=sys.stderr)
    raise SystemExit(1)


source_path = Path(sys.argv[1])
markdown_path = Path(sys.argv[2])
style_path = Path(sys.argv[3])
figure_stems = sys.argv[4:]
source_bytes = source_path.read_bytes()
markdown_bytes = markdown_path.read_bytes()
style_bytes = style_path.read_bytes()
for label, data in (
    ("TeX", source_bytes),
    ("canonical Markdown", markdown_bytes),
    ("publication style", style_bytes),
):
    if b"\r" in data:
        fail(f"{label} contains a carriage return")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"{label} is not UTF-8: {error}")

source = source_bytes.decode("utf-8")
markdown = markdown_bytes.decode("utf-8")
style = style_bytes.decode("utf-8")
# An HTML comment opener can hide arbitrary later prose and is therefore forbidden.  A bare
# closing-token spelling is not sufficient evidence of concealment: the retained finite-group
# counterexample deliberately contains the labelled arrow ``--id-->``.  Rejecting every ``-->``
# suffix would make the accepted source contract internally unsatisfiable.
if "<!--" in markdown:
    fail("canonical Markdown contains an HTML comment opener")
begin_marker = "\\begin{markdown}\n"
end_marker = "\\end{markdown}"
if source.count(begin_marker) != 1 or source.count(end_marker) != 1:
    fail("TeX source must contain exactly one canonical Markdown enclosure")
begin = source.index(begin_marker) + len(begin_marker)
end = source.index(end_marker, begin)
embedded = source[begin:end]
if embedded.encode("utf-8") != markdown_bytes:
    fail("embedded canonical Markdown differs byte-for-byte from the root source")
source_suffix = source[end + len(end_marker) :]
if source_suffix != "\n\n\\end{document}\n":
    fail("TeX source has bytes outside the exact reviewed post-Markdown suffix")

for forbidden in ("private_CV", "final_generic", "/Users/", "file://"):
    if forbidden in source or forbidden in style:
        fail(f"publication source has a forbidden external/private dependency: {forbidden}")

required_source_markers = (
    r"\usepackage{fontspec}",
    r"\usepackage{unicode-math}",
    r"\setmathfont{latinmodern-math.otf}",
    r"\usepackage{pid-rs-report-tables}",
    r"\usepackage{pid-rs-workflow-publication}",
    r"\pdfvariable minorversion=7",
    r"\pdfextension catalog { /Lang (en) }",
    r"\par\Needspace{8\baselineskip}%",
    r"\def\PidWorkflowPortableParagraphTitleOne{Discovery, verification, and communication methods}",
    r"\def\PidWorkflowPortableParagraphTitleTwo{Mathematical method reconstructed from the paper}",
    r"\newcommand{\PidWorkflowForcedPageParagraph}",
    r"\newcommand{\PidWorkflowReportParagraph}",
    r"headingFour = {\PidWorkflowReportParagraph{#1}}",
    r"\begin{longtable}",
    r"\begin{minipage}{\linewidth}",
)
for marker in required_source_markers:
    if source.count(marker) != 1:
        fail(f"required TeX publication marker must occur once: {marker}")
if r"\Needspace{0.26\textheight}" in source:
    fail("legacy all-heading 26-percent page guard remains present")
portable_paragraph_boundary = (
    "\\ifx\\PidWorkflowCurrentParagraphTitle\\PidWorkflowPortableParagraphTitleOne\n"
    "    \\endgroup\n"
    "    \\PidWorkflowForcedPageParagraph{#1}%\n"
    "  \\else\n"
    "    \\ifx\\PidWorkflowCurrentParagraphTitle\\PidWorkflowPortableParagraphTitleTwo\n"
    "      \\endgroup\n"
    "      \\PidWorkflowForcedPageParagraph{#1}%\n"
    "    \\else\n"
    "      \\endgroup\n"
    "      \\PidWorkflowParagraph{#1}%\n"
    "    \\fi\n"
    "  \\fi"
)
if source.count(portable_paragraph_boundary) != 1:
    fail("exact-title workflow paragraph page-boundary guards must occur once")
forced_page_paragraph = (
    "\\newcommand{\\PidWorkflowForcedPageParagraph}[1]{%\n"
    "  \\clearpage\n"
    "  % Needspace is redundant at a forced page. Replace titlesec's page-top before-skip with fixed,\n"
    "  % non-discardable placement, while preserving the real paragraph command and its after-heading\n"
    "  % state for the body that follows this macro.\n"
    "  \\titlespacing*{\\paragraph}{0pt}{0pt}{3pt}%\n"
    "  \\vspace*{9pt}%\n"
    "  \\paragraph{#1}%\n"
    "  \\titlespacing*{\\paragraph}{0pt}{0.82em}{0.28em}%\n"
    "  \\ignorespaces\n"
    "}"
)
if source.count(forced_page_paragraph) != 1:
    fail("forced-page workflow paragraph spacing contract must occur once")

# Equation numbers in the typeset-only primer are an explicit, monotone sequence.  Auto-numbered
# display environments can silently collide with those manual tags (as happened when the worked
# two-source inversion used an unstarred align environment), leaving algebraically correct prose
# with ambiguous cross-references in the publication artifact.
primer = source[: source.index(begin_marker)]
primer_body_start_marker = "\\clearpage\n\n"
if source.count(primer_body_start_marker) != 1:
    fail("typeset-only primer body boundary drifted")
primer_body = source[
    source.index(primer_body_start_marker) + len(primer_body_start_marker) :
    source.index(begin_marker)
]
bare_primer_headings = re.findall(
    r"\\(?:section|subsection|subsubsection|paragraph)\{",
    primer_body,
)
if bare_primer_headings:
    fail(f"typeset-only primer contains bare heading commands: {bare_primer_headings!r}")
typed_heading_counts = {
    r"\PidWorkflowSection{": 3,
    r"\PidWorkflowSubsection{": 15,
    r"\PidWorkflowSubsubsection{": 1,
    r"\PidWorkflowParagraph{": 1,
}
for typed_heading, expected_count in typed_heading_counts.items():
    observed_count = source.count(typed_heading)
    if observed_count != expected_count:
        fail(
            "typed heading invocation count drifted: "
            f"{typed_heading}: expected {expected_count}, observed {observed_count}"
        )
auto_numbered_environments = re.findall(
    r"\\begin\{(align|alignat|equation|eqnarray|flalign|gather|multline|subequations|xalignat|xxalignat)\}",
    primer,
)
if auto_numbered_environments:
    fail(
        "typeset-only primer contains auto-numbered display environments: "
        f"{auto_numbered_environments!r}"
    )
primer_equation_tags = re.findall(r"\\tag(\*)?\{([^{}]*)\}", primer)
expected_primer_equation_tags = [("", str(number)) for number in range(1, 13)]
if primer_equation_tags != expected_primer_equation_tags:
    fail(
        "typeset-only primer equation-tag sequence drifted: "
        f"{primer_equation_tags!r}"
    )

required_style_markers = (
    r"\definecolor{PidCvLapis}{HTML}{1F3F60}",
    r"\definecolor{PidCvInk}{HTML}{2C3E50}",
    r"\definecolor{PidCvTurquoise}{HTML}{1F6968}",
    r"\definecolor{PidCvMineral}{HTML}{D2E0E2}",
    r"\definecolor{PidCvIvory}{HTML}{F7F3E9}",
    r"\definecolor{PidCvBronze}{HTML}{B28218}",
    r"\definecolor{PidCvMuted}{HTML}{596A73}",
    r"\setmainfont[",
    r"\setsansfont[",
    r"\pagecolor{PidCvIvory}",
    r"\newcommand{\PidWorkflowRosette}",
    r"\newcommand{\PidWorkflowSectionRail}",
    r"\newcommand{\PidWorkflowSection}",
    r"\newcommand{\PidWorkflowSubsection}",
    r"\newcommand{\PidWorkflowSubsubsection}",
    r"\newcommand{\PidWorkflowParagraph}",
)
for marker in required_style_markers:
    if style.count(marker) != 1:
        fail(f"required project-local visual marker must occur once: {marker}")

figure_refs = re.findall(
    r"\\PidWorkflowFigure\s*\{([a-z0-9-]+)\}",
    source,
)
if figure_refs != figure_stems:
    fail(f"TeX figure order/inventory drifted: {figure_refs!r}")
for stem in figure_stems:
    if source.count(stem) != 1:
        fail(f"figure stem must occur in exactly one typed figure invocation: {stem}")

direct_source_literals = (
    "The assurance path therefore contains three distinct transitions, each with its own obligation:",
    "The assurance chain has four distinct objects and three separately justified assurance transitions.",
    "An AND/OR directed acyclic graph has frozen admissible universe U = {A1, A2, B1, C}, route A = {A1, A2, C}, and route B = {B1, C}.",
    "The complete inclusion-minimal cut family is {C}, {A1, B1}, and {A2, B1}; the common goal and synthetic route aggregators are excluded from the admissible cut universe.",
    "AND prerequisites, OR routes, and the complete three-cut family in the frozen example.",
)
for literal in direct_source_literals:
    if source.count(literal) != 1:
        fail(f"required TeX assurance-boundary wording must occur once: {literal}")


def top_level_markdown_prose(text: str) -> str:
    """Return prose outside fenced/quoted/indented code contexts.

    Required scientific assertions must be visible assertions, not strings parked in examples or
    quotations.  This is intentionally a narrow context recognizer rather than a complete Markdown
    renderer; the exact Markdown digest closes the remaining syntax boundary.
    """

    visible: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        fence = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence_character is not None:
            closing = re.match(
                rf"^ {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*$",
                line,
            )
            if closing is not None:
                fence_character = None
                fence_length = 0
            visible.append("")
            continue
        if fence is not None:
            fence_token = fence.group(1)
            fence_character = fence_token[0]
            fence_length = len(fence_token)
            visible.append("")
            continue
        if re.match(r"^ {0,3}>", line) or line.startswith("\t") or re.match(r"^ {4}\S", line):
            visible.append("")
            continue
        visible.append(line)
    if fence_character is not None:
        fail("canonical Markdown contains an unclosed fenced-code block")
    return "\n".join(visible)


semantic_markdown = top_level_markdown_prose(markdown)
semantic_patterns = (
    r"at every observable checkpoint\s+before a possible context boundary",
    r"redacted canonical projection plus immutable locators\s+and an identity of the permitted projection",
    r"PID and process-group ID only when the tool exposes\s+them or they are reliably observed, otherwise explicit `unavailable`",
    r"mere success status of a tool call is not evidence of\s+scientific progress",
    r"at least three consecutive goal turns,\s+counting the original user-triggered turn",
    r"previously blocked goal resumes, begin a fresh\s+three-turn blocked audit",
    r"Orient every dependency-bearing edge from prerequisite to dependent",
    r"inclusion-minimal",
    r"Equation \(27\) is therefore false",
)
for pattern in semantic_patterns:
    if re.search(pattern, semantic_markdown) is None:
        fail(f"canonical semantic correction is absent: {pattern}")
if markdown.count("Named source arrow (domain -> codomain):") != 1:
    fail("canonical fenced counterexample arrow label is absent or duplicated")

semantic_literals = (
    "13b95999f060c0be2142089cfb8b17b75e9231c3c1f3fa0980445ff1b35f0b3b",
    "64b900d5fae6fe22f2ae1b8e3b712d20055194a6c81cf343a2455e5898ac7dd6",
    "Intended closure/falsification routes",
    "Initial accepted-result evidence",
    "Current accepted-result evidence",
    "Initialized as an empty list rendered as the literal text “no accepted evidence”",
    "at least five genuinely failure-diverse applicable audit families",
    "Within the finite MGW/shared-exclusions construction used here",
    "A route that merely failed is not a counterexample",
    "Per-cell or per-obligation witnesses do not imply one joint witness",
    "OpenAI-hosted proof-process walkthroughs: process controls only",
    "both were supplied from the same OpenAI CDN source family",
    "order of conditioning, fitting, mixing or averaging, nonlinear transforms, and Möbius inversion",
    "one compatible joint version or witness when simultaneity is required",
    "one total error budget smaller than every strict claimed margin",
    "the construction-native local or target-outcome-specific information object, any cumulative-event semantics and Möbius convention it actually uses",
    "the construction-native local or target-outcome-specific information object and decomposition convention; for MGW",
    "admissible state/event identifications and incidental overlaps",
    "neighboring non-target method or estimand that it must reject",
    "Formatting or serialization changes therefore still require artifact replay",
    "logical alternativity alone does not make them dependency-disjoint",
    "A raw digest of an enumerable seed or target is not hiding",
    "known soundness advisories against the exact version",
    "frozen admissible vertex universe",
    "split that lens into typed subrows",
    "underflow/subnormals",
    "noninjective target coarse-graining as an estimand-changing map",
    "Completion predicate and adjudicator",
    "Completeness is a disposition, not an evidence class",
    "arXiv:2002.03356v5",
    "arXiv:2311.06373v3",
    "arXiv:2106.12393v2",
    "arXiv:1004.2515v1",
    "arXiv:cond-mat/0305641v1",
    "PhysRevE.83.019903",
    "arXiv:2504.15779v1",
    "arXiv:2409.13506v1",
    "arXiv:2508.05530v2",
    "arXiv:2604.03869v2",
    "experimental::isx_heuristics",
    "project-defined target-free $\\mathrm{Red}^{\\circ}$/$\\mathrm{Vul}^{\\circ}$ ratios",
    "A semidecision search that may run forever in the no-violator case",
    "physical PDF page 5 prints $dt\\,ds_1\\,ds_1$",
    "complete right-hand side must be divided by $\\ln 2$",
    "_compute_n_T(T,eps)",
    "That code is correlated with the defining-paper route",
)
normalized_markdown = " ".join(semantic_markdown.split())
for literal in semantic_literals:
    if " ".join(literal.split()) not in normalized_markdown:
        fail(f"canonical semantic literal is absent: {literal}")

# The publication renderer deliberately allows character-level breaks inside short code tokens.
# Its sequence splitter removes interword spaces, however, so whitespace-bearing inline-code spans
# would silently change visible text.  Require such prose to use ordinary quoted text or a fenced
# verbatim block instead of accepting a semantically lossy PDF rendering.
for line_number, line in enumerate(markdown.splitlines(), start=1):
    for code_span in re.finditer(r"(?<!`)`([^`\n]+)`(?!`)", line):
        if any(character.isspace() for character in code_span.group(1)):
            fail(
                "whitespace-bearing inline code is incompatible with the publication renderer "
                f"at canonical Markdown line {line_number}"
            )

# Markdown 2.23 and Markdown 3.4 agree on this ordered-list argument when its six display
# delimiters and the first continuation after each display use four spaces. Three spaces at those
# nine parser boundaries can terminate the list on the hosted TeX toolchain, silently outdent the
# proof, and merge later numbered items while leaving navigation identities intact. Freeze the
# minimum portable source structure instead of broadly reindenting the mathematics or weakening
# the cross-toolchain raster comparison.
portable_list_start = "3. Use the new rank--trace inequality:"
portable_list_end = "\n\nTheorem E gives the corresponding"
if markdown.count(portable_list_start) != 1 or markdown.count(portable_list_end) != 1:
    fail("portable ordered-list argument boundary drifted")
portable_start_offset = markdown.index(portable_list_start)
portable_end_offset = markdown.index(portable_list_end, portable_start_offset)
portable_block = markdown[portable_start_offset:portable_end_offset]
if portable_block.count("\n4. ") != 1 or portable_block.count("\n5. ") != 1:
    fail("portable ordered-list item inventory drifted")
if portable_block.count("\n    $$") != 6:
    fail("portable ordered-list display delimiter inventory drifted")
portable_post_display_markers = {
    "rank-trace proof": "\n    $$\n\n    The proof separates",
    "transfer conjunction": "\n    $$\n\n    and\n\n    $$",
    "prime-side continuation": "\n    $$\n\n    On the prime side",
}
for label, marker in portable_post_display_markers.items():
    if portable_block.count(marker) != 1:
        fail(
            "portable ordered-list post-display continuation marker must occur once: "
            f"{label}"
        )

for forbidden in (
    "empirical-law plug-in estimand",
    "Are every claimed Rust",
    "For each new theorem, use at least three applicable audit families",
    "One-source self-redundancy reduces to mutual information",
    "both are OpenAI-produced collections",
    "the cumulative event semantics, informative/misinformative split, and Möbius convention",
    "- the pointwise informative, misinformative, and net terms;",
):
    if forbidden in markdown:
        fail(f"superseded semantic wording remains: {forbidden}")

# TeX is programmable enough to bypass any finite lexical rule (for example through \csname or a
# redefined wrapper). The rules above provide branch-specific diagnostics; these exact reviewed
# byte bindings close the residual framing/style parser boundary. Updating either digest is an
# explicit custody transition, not a claim that the bytes are semantically correct by hashing.
markdown_digest = hashlib.sha256(markdown_bytes).hexdigest()
if markdown_digest != "c55e6fa63ba9f72477e1bb8e4153e99d80e77ef69fc858e49976ee0c154335a7":
    fail(f"canonical Markdown exact-byte custody drifted: {markdown_digest}")
primer_digest = hashlib.sha256(primer.encode("utf-8")).hexdigest()
if primer_digest != "a86e39c1a5602866c496c93259b8c0da6ac21b8cfe3736bbc5f4d02dc4f31dab":
    fail(f"typeset-only primer exact-byte custody drifted: {primer_digest}")
style_digest = hashlib.sha256(style_bytes).hexdigest()
if style_digest != "73eac73ac0cd028ced43020c0935ac59dd65ecd0b26cf7b67155de2fe2a8343e":
    fail(f"workflow publication style exact-byte custody drifted: {style_digest}")
PY

if [[ "$MODE" != "--refresh" ]]; then
  python3 -I -S - \
    "$SNAPSHOT_ROOT/$VISUAL_RECEIPT" \
    "$SNAPSHOT_ROOT/$COMMITTED" \
    "$SNAPSHOT_ROOT/$RENDERING_RECEIPT" \
    "$EXPECTED_PAGES" \
    "$RENDER_DPI" <<'PY'
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys


def fail(detail: str) -> None:
    print(f"mathematical workflow PDF check: visual receipt {detail}", file=sys.stderr)
    raise SystemExit(1)


receipt_path = Path(sys.argv[1])
pdf_path = Path(sys.argv[2])
rendering_receipt_path = Path(sys.argv[3])
expected_pages = int(sys.argv[4])
expected_dpi = int(sys.argv[5])
raw = receipt_path.read_bytes()
if not raw.endswith(b"\n") or b"\r" in raw:
    fail("does not have canonical LF termination")
try:
    text = raw.decode("utf-8")
except UnicodeDecodeError as error:
    fail(f"is not UTF-8: {error}")
if any(forbidden in text for forbidden in ("/private/", "/Users/", "file://")):
    fail("contains a private or host-local path")
lines = text.splitlines()
if any(
    token in text
    for token in ("<!--", "-->", "```", "~~~")
) or any(
    line.startswith((">", "\t", "    "))
    for line in lines
):
    fail("contains forbidden Markdown concealment or non-top-level content")
if not lines or lines[0] != "# Mathematical workflow PDF visual-review receipt":
    fail("does not begin with the canonical visible title")
if len(lines) < 3 or lines[1] != "":
    fail("does not separate the canonical title from its field block")
if any(line.startswith("#") for line in lines[1:]):
    fail("contains an unexpected additional heading")

field_order = (
    "schema",
    "subject",
    "pdf_sha256",
    "rendering_receipt",
    "rendering_receipt_sha256",
    "pages",
    "dpi",
    "color_pages_reviewed",
    "grayscale_pages_reviewed",
    "original_resolution_spot_checks",
    "figure_pages_reviewed",
    "status",
    "review_date_utc",
    "reviewer_kind",
)
field_values: dict[str, str] = {}
for offset, name in enumerate(field_order, start=2):
    if offset >= len(lines):
        fail(f"is truncated before canonical {name} field")
    match = re.fullmatch(rf"{re.escape(name)}: `([^`]+)`", lines[offset])
    if match is None:
        fail(f"canonical field order or syntax drifted at {name}")
    field_values[name] = match.group(1)
field_block_end = 2 + len(field_order)
if field_block_end >= len(lines) or lines[field_block_end] != "":
    fail("does not terminate the canonical field block with one blank line")


def field(name: str) -> str:
    matches = re.findall(rf"^{re.escape(name)}: `([^`]+)`$", text, re.MULTILINE)
    if len(matches) != 1 or name not in field_values:
        fail(f"must contain exactly one canonical {name} field")
    return field_values[name]


expected_fields = {
    "schema": "pid-rs/mathematical-workflow-visual-review/v1",
    "subject": "output/pdf/mathematical-problem-solving-workflow.pdf",
    "pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
    "rendering_receipt": "output/pdf/mathematical-problem-solving-workflow.rendering-receipt.tsv",
    "rendering_receipt_sha256": hashlib.sha256(rendering_receipt_path.read_bytes()).hexdigest(),
    "pages": str(expected_pages),
    "dpi": str(expected_dpi),
    "color_pages_reviewed": f"1-{expected_pages}",
    "grayscale_pages_reviewed": f"1-{expected_pages}",
    "original_resolution_spot_checks": f"1-{expected_pages}",
    "figure_pages_reviewed": "3,4,9,10",
    "status": "passed",
    "review_date_utc": "2026-08-12",
    "reviewer_kind": "agent-visual-inspection",
}
for name, expected in expected_fields.items():
    observed = field(name)
    if observed != expected:
        fail(f"field {name} differs: {observed!r}")

required_statements = (
    f"All {expected_pages} color pages and all {expected_pages} grayscale pages were viewed in page order.",
    "No blank, clipped, overlapping, misordered, or visibly corrupt page was observed.",
    "Every workflow figure was reviewed at original resolution in both color and grayscale.",
    "The root agent completed the page-by-page visual inspection; no dependency-disjoint second-review credit is claimed.",
    "This receipt records a bounded page-by-page agent visual inspection; it is not a proof of mathematical correctness, accessibility conformance, or semantic completeness.",
)
paragraphs = [
    " ".join(line.strip() for line in paragraph.splitlines())
    for paragraph in text.split("\n\n")
    if paragraph.strip()
]
for statement in required_statements:
    if paragraphs.count(statement) != 1:
        fail(f"required top-level review paragraph is absent or duplicated: {statement}")
expected_paragraphs = [
    "# Mathematical workflow PDF visual-review receipt",
    " ".join(lines[2:field_block_end]),
    *required_statements,
]
if paragraphs != expected_paragraphs:
    fail("paragraph inventory differs from the closed schema")
PY
fi

python3 -I -S - "$SNAPSHOT_ROOT/$FIGURE_DIR" "${FIGURE_STEMS[@]}" <<'PY'
from __future__ import annotations

import hashlib
from itertools import combinations
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


def fail(detail: str) -> None:
    print(f"mathematical workflow PDF check: {detail}", file=sys.stderr)
    raise SystemExit(1)


figure_dir = Path(sys.argv[1])
stems = sys.argv[2:]
expected_geometry = {
    "four-object-assurance-chain": ("160mm", "64mm", "0 0 1600 640"),
    "obligation-dag-minimal-cuts": ("160mm", "78mm", "0 0 1600 780"),
    "shared-oracle-correlated-routes": ("160mm", "76mm", "0 0 1600 760"),
    "invalidation-publication-state-machine": ("160mm", "84mm", "0 0 1600 840"),
}
expected_svg_sha256 = {
    "four-object-assurance-chain": "64955c76d881c9bfe4ee3fade1961064acebf5b21c20ba75be826824b0dcdc25",
    "obligation-dag-minimal-cuts": "d3c5bbade2238e1d5023f7637ac7714ce79baa3bf0f2a20cdfab28ce14bf6a0c",
    "shared-oracle-correlated-routes": "44b55e8cc1dbe7c357bb223fface53488761ed97c6ecc8fc133e9be2c23e4987",
    "invalidation-publication-state-machine": "9ac971262d90e71197e6b421a167ea0b91f1c3ce1c921944824b533e5e85dc59",
}
allowed_palette = {
    "#1F3F60",
    "#2C3E50",
    "#1F6968",
    "#D2E0E2",
    "#F7F3E9",
    "#B28218",
    "#596A73",
}
svg_namespace = "{http://www.w3.org/2000/svg}"
for stem in stems:
    path = figure_dir / f"{stem}.svg"
    try:
        raw_bytes = path.read_bytes()
        raw = raw_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        fail(f"cannot read {path.name} as UTF-8: {error}")
    if b"\r" in raw_bytes:
        fail(f"{path.name} contains a carriage return")
    declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    if not raw.startswith(declaration):
        fail(f"{path.name} lacks the exact XML declaration")
    body = raw[len(declaration) :]
    if re.search(r"<!DOCTYPE|<!ENTITY", body, re.IGNORECASE):
        fail(f"{path.name} contains a DOCTYPE or entity declaration")
    if "<?" in body:
        fail(f"{path.name} contains a processing instruction")
    resource_scan = body.replace('xmlns="http://www.w3.org/2000/svg"', "", 1)
    if re.search(
        r"@import|@font-face|expression\s*\(|(?:https?|file|data):",
        resource_scan,
        re.IGNORECASE,
    ):
        fail(f"{path.name} contains a forbidden external or executable CSS/resource form")
    for match in re.finditer(r"url\s*\(([^)]*)\)", body, re.IGNORECASE):
        if re.fullmatch(r"\s*#[A-Za-z_][A-Za-z0-9_.:-]*\s*", match.group(1)) is None:
            fail(f"{path.name} contains a non-local URL reference")
    if re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden|(?:^|[;\s])opacity\s*:\s*0(?:\D|$))", body, re.IGNORECASE):
        fail(f"{path.name} contains hidden content")
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        fail(f"cannot parse {path.name}: {error}")
    if root.tag != f"{svg_namespace}svg":
        fail(f"{path.name} does not have an SVG root element")
    width, height, view_box = expected_geometry[stem]
    if (
        root.get("width") != width
        or root.get("height") != height
        or root.get("viewBox") != view_box
    ):
        fail(f"{path.name} geometry differs from the declared figure contract")
    if root.get("role") != "img" or root.get("{http://www.w3.org/XML/1998/namespace}lang") != "en":
        fail(f"{path.name} lacks its image role or English-language declaration")
    titles = root.findall(f"{svg_namespace}title")
    descriptions = root.findall(f"{svg_namespace}desc")
    if len(titles) != 1 or len(descriptions) != 1:
        fail(f"{path.name} must contain exactly one direct title and description")
    title_id = titles[0].get("id")
    description_id = descriptions[0].get("id")
    if not title_id or not description_id:
        fail(f"{path.name} title/description must have identifiers")
    if root.get("aria-labelledby", "").split() != [title_id, description_id]:
        fail(f"{path.name} source-SVG title/description binding must name title then description")

    identifiers: list[str] = []
    text_nodes: list[str] = []
    paint_properties = {
        "color",
        "fill",
        "flood-color",
        "lighting-color",
        "stop-color",
        "stroke",
    }

    def validate_paint(value: str) -> None:
        if value in {"none", "currentColor"}:
            return
        if value.upper() in allowed_palette:
            return
        if re.fullmatch(r"url\(#[A-Za-z_][A-Za-z0-9_.:-]*\)", value):
            return
        fail(f"{path.name} uses an unsupported paint declaration: {value!r}")

    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name in {"foreignObject", "image", "script"}:
            fail(f"{path.name} contains forbidden embedded content: {local_name}")
        identifier = element.get("id")
        if identifier is not None:
            identifiers.append(identifier)
        if local_name == "text":
            rendered_text = "".join(element.itertext()).strip()
            if rendered_text:
                text_nodes.append(rendered_text)
        for attribute, value in element.attrib.items():
            attribute_name = attribute.rsplit("}", 1)[-1]
            normalized_value = value.strip().casefold()
            if attribute_name.lower().startswith("on") or attribute_name == "base":
                fail(f"{path.name} contains an event handler or XML base")
            if (
                (attribute_name == "display" and normalized_value == "none")
                or (
                    attribute_name == "visibility"
                    and normalized_value in {"hidden", "collapse"}
                )
                or (
                    attribute_name in {"opacity", "fill-opacity", "stroke-opacity"}
                    and re.fullmatch(
                        r"[+-]?(?:0+(?:\.0*)?|\.0+)(?:e[+-]?\d+)?",
                        normalized_value,
                    )
                )
                or (
                    local_name == "text"
                    and attribute_name == "font-size"
                    and re.fullmatch(r"[+-]?(?:0+(?:\.0*)?|\.0+)(?:[a-z%]+)?", normalized_value)
                )
            ):
                fail(f"{path.name} contains hidden content")
            if attribute_name == "href" and not value.startswith("#"):
                fail(f"{path.name} contains a non-local href")
            if attribute_name in paint_properties:
                validate_paint(value)
            if attribute_name == "style":
                for property_name, property_value in re.findall(
                    r"([A-Za-z-]+)\s*:\s*([^;{}]+)", value
                ):
                    if property_name.lower() in paint_properties:
                        validate_paint(property_value.strip())
        if local_name == "style":
            css = "".join(element.itertext())
            for property_name, property_value in re.findall(
                r"([A-Za-z-]+)\s*:\s*([^;{}]+)", css
            ):
                if property_name.lower() in paint_properties:
                    validate_paint(property_value.strip())
    if len(identifiers) != len(set(identifiers)):
        fail(f"{path.name} contains duplicate XML identifiers")
    colors = {value.upper() for value in re.findall(r"#[0-9A-Fa-f]{6}", raw)}
    if not colors or not colors.issubset(allowed_palette):
        fail(f"{path.name} uses a color outside the exact project palette: {sorted(colors)}")
    if "Source Sans Pro" not in raw or "Latin Modern Roman" not in raw:
        fail(f"{path.name} does not declare the report heading/body font architecture")
    if stem == "obligation-dag-minimal-cuts":
        node_pattern = re.compile(r"[A-Z][A-Z0-9]*")

        def parse_set(raw_value: str | None, label: str) -> frozenset[str]:
            if raw_value is None or not raw_value:
                fail(f"{path.name} lacks {label} metadata")
            values = raw_value.split(",")
            if (
                any(node_pattern.fullmatch(value) is None for value in values)
                or len(values) != len(set(values))
            ):
                fail(f"{path.name} has noncanonical {label} metadata")
            return frozenset(values)

        universe = parse_set(root.get("data-admissible-universe"), "admissible-universe")
        routes = (
            parse_set(root.get("data-route-a"), "route-a"),
            parse_set(root.get("data-route-b"), "route-b"),
        )
        raw_cuts = root.get("data-minimal-cuts")
        if raw_cuts is None or not raw_cuts:
            fail(f"{path.name} lacks minimal-cut metadata")
        declared_cuts = tuple(
            parse_set(raw_cut, f"minimal-cut-{index}")
            for index, raw_cut in enumerate(raw_cuts.split(";"), start=1)
        )
        if universe != frozenset({"A1", "A2", "B1", "C"}):
            fail(f"{path.name} admissible universe drifted")
        if routes != (
            frozenset({"A1", "A2", "C"}),
            frozenset({"B1", "C"}),
        ):
            fail(f"{path.name} route family drifted")
        if any(not route or not route <= universe for route in routes):
            fail(f"{path.name} route family escapes the admissible universe")
        if len(declared_cuts) != len(set(declared_cuts)):
            fail(f"{path.name} repeats a declared minimal cut")

        hitting_sets: set[frozenset[str]] = set()
        ordered_universe = sorted(universe)
        for size in range(1, len(ordered_universe) + 1):
            for members in combinations(ordered_universe, size):
                candidate = frozenset(members)
                if all(candidate & route for route in routes):
                    hitting_sets.add(candidate)
        minimal_hitting_sets = {
            candidate
            for candidate in hitting_sets
            if not any(proper < candidate for proper in hitting_sets)
        }
        if set(declared_cuts) != minimal_hitting_sets:
            fail(
                f"{path.name} declared cuts are not the complete minimal transversal family: "
                f"declared={declared_cuts!r}, computed={sorted(map(sorted, minimal_hitting_sets))!r}"
            )

        description_text = " ".join("".join(descriptions[0].itertext()).split())
        description_literals = (
            "frozen admissible universe U = {A1, A2, B1, C}",
            "route A = {A1, A2, C} and route B = {B1, C}",
            "complete inclusion-minimal cut family is {C}, {A1, B1}, and {A2, B1}",
        )
        for literal in description_literals:
            if literal not in description_text:
                fail(f"{path.name} description lacks cut semantics: {literal!r}")

def parse_css_properties(body: str, label: str) -> dict[str, str]:
    properties: dict[str, str] = {}
    for declaration in body.split(";"):
        declaration = declaration.strip()
        if not declaration:
            continue
        if ":" not in declaration:
            fail(f"{label} contains a malformed CSS declaration")
        name, value = declaration.split(":", 1)
        name = name.strip().casefold()
        value = value.strip()
        if not re.fullmatch(r"[a-z-]+", name) or not value or name in properties:
            fail(f"{label} contains a duplicate or noncanonical CSS property")
        properties[name] = value
    return properties


def strict_visible_text(root: ET.Element, path: Path) -> str:
    view_box_values = root.get("viewBox", "").split()
    if len(view_box_values) != 4:
        fail(f"{path.name} has a malformed viewBox")
    try:
        view_x, view_y, view_width, view_height = map(float, view_box_values)
    except ValueError:
        fail(f"{path.name} has a nonnumeric viewBox")
    if view_width <= 0 or view_height <= 0:
        fail(f"{path.name} has a nonpositive viewBox")

    class_properties: dict[str, dict[str, str]] = {}
    for style_element in root.iter(f"{svg_namespace}style"):
        css = "".join(style_element.itertext())
        if "/*" in css or "*/" in css or "@" in css:
            fail(f"{path.name} stylesheet contains comments or at-rules")
        matches = list(re.finditer(r"\.([A-Za-z_][A-Za-z0-9_-]*)\s*\{([^{}]*)\}", css))
        residue = re.sub(r"\.([A-Za-z_][A-Za-z0-9_-]*)\s*\{[^{}]*\}", "", css)
        if residue.strip():
            fail(f"{path.name} stylesheet contains a noncanonical selector")
        for match in matches:
            class_name = match.group(1)
            if class_name in class_properties:
                fail(f"{path.name} repeats CSS class {class_name!r}")
            class_properties[class_name] = parse_css_properties(
                match.group(2),
                f"{path.name} CSS class {class_name!r}",
            )
    if not class_properties:
        fail(f"{path.name} has no canonical text-style classes")

    parent = {child: element for element in root.iter() for child in element}
    validated_text: list[str] = []
    hidden_properties = {"clip-path", "filter", "mask"}
    zero_pattern = re.compile(r"[+-]?(?:0+(?:\.0*)?|\.0+)(?:e[+-]?\d+)?", re.IGNORECASE)
    number_pattern = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?", re.IGNORECASE)

    for element in root.iter(f"{svg_namespace}text"):
        text_value = "".join(element.itertext()).strip()
        if not text_value:
            continue
        chain: list[ET.Element] = []
        current: ET.Element | None = element
        while current is not None:
            chain.append(current)
            current = parent.get(current)
        chain.reverse()

        translate_x = 0.0
        translate_y = 0.0
        for ancestor in chain:
            local_name = ancestor.tag.rsplit("}", 1)[-1]
            if local_name in {"clipPath", "defs", "desc", "marker", "mask", "metadata", "pattern", "symbol", "title"}:
                fail(f"{path.name} contains text in a nonrendered container")
            properties = {
                key.rsplit("}", 1)[-1].casefold(): value.strip()
                for key, value in ancestor.attrib.items()
            }
            class_value = properties.get("class")
            if class_value:
                class_names = class_value.split()
                if len(class_names) != 1 or class_names[0] not in class_properties:
                    fail(f"{path.name} text ancestry uses a noncanonical CSS class")
                properties.update(class_properties[class_names[0]])
            if "style" in properties:
                properties.update(
                    parse_css_properties(
                        properties["style"],
                        f"{path.name} inline style",
                    )
                )
            if properties.get("display", "").casefold() == "none" or properties.get(
                "visibility", ""
            ).casefold() in {"hidden", "collapse"}:
                fail(f"{path.name} contains required text hidden by display/visibility")
            for opacity_name in ("opacity", "fill-opacity"):
                opacity = properties.get(opacity_name)
                if opacity is not None and zero_pattern.fullmatch(opacity.strip()):
                    fail(f"{path.name} contains required text hidden by {opacity_name}")
            for property_name in hidden_properties:
                if properties.get(property_name, "").casefold() not in {"", "none"}:
                    fail(f"{path.name} contains clipped, filtered, or masked text")
            if properties.get("fill", "").casefold() == "none":
                fail(f"{path.name} contains text with a none fill")
            transform = properties.get("transform")
            if transform:
                translate = re.fullmatch(
                    rf"translate\(\s*({number_pattern.pattern})(?:[ ,]+({number_pattern.pattern}))?\s*\)",
                    transform,
                    re.IGNORECASE,
                )
                rotation = re.fullmatch(
                    rf"rotate\(\s*({number_pattern.pattern})[ ,]+({number_pattern.pattern})[ ,]+({number_pattern.pattern})\s*\)",
                    transform,
                    re.IGNORECASE,
                )
                if translate is not None and ancestor is not element:
                    translate_x += float(translate.group(1))
                    translate_y += float(translate.group(2) or 0.0)
                elif rotation is not None and ancestor is element:
                    # Current vertical badges rotate about their own declared anchor.  This leaves
                    # the anchor invariant and admits no arbitrary matrix/off-canvas transform.
                    pass
                else:
                    fail(f"{path.name} text uses an unsupported transform: {transform!r}")

        class_value = element.get("class", "")
        if len(class_value.split()) != 1 or class_value not in class_properties:
            fail(f"{path.name} text lacks one canonical style class")
        text_style = class_properties[class_value]
        fill = text_style.get("fill", "")
        if fill.casefold() == "none" or fill.upper() not in allowed_palette:
            fail(f"{path.name} text class lacks a visible palette fill")
        font_size_raw = text_style.get("font-size", "").removesuffix("px")
        if number_pattern.fullmatch(font_size_raw) is None or float(font_size_raw) <= 0:
            fail(f"{path.name} text class has a nonpositive font size")
        x_raw = element.get("x", "")
        y_raw = element.get("y", "")
        if number_pattern.fullmatch(x_raw) is None or number_pattern.fullmatch(y_raw) is None:
            fail(f"{path.name} text lacks one finite numeric anchor")
        x = float(x_raw) + translate_x
        y = float(y_raw) + translate_y
        if not (view_x <= x <= view_x + view_width and view_y <= y <= view_y + view_height):
            fail(f"{path.name} text anchor lies outside the viewBox")
        rotation = element.get("transform")
        if rotation:
            match = re.fullmatch(
                rf"rotate\(\s*({number_pattern.pattern})[ ,]+({number_pattern.pattern})[ ,]+({number_pattern.pattern})\s*\)",
                rotation,
                re.IGNORECASE,
            )
            if match is None or abs(float(match.group(2)) - float(x_raw)) > 1e-9 or abs(
                float(match.group(3)) - float(y_raw)
            ) > 1e-9:
                fail(f"{path.name} rotated text does not preserve its declared anchor")
        validated_text.append(text_value)
    if not validated_text:
        fail(f"{path.name} contains no validated visible text")
    return " ".join(validated_text)


required_figure_language = {
    "four-object-assurance-chain": (
        "target correspondence",
        "implementation refinement",
        "consumer qualification",
    ),
    "obligation-dag-minimal-cuts": (
        "A or B accepted",
        "Frozen U = {A1, A2, B1, C}",
        "Routes: A = {A1, A2, C}; B = {B1, C}",
        "All inclusion-minimal cuts: {C}; {A1, B1}; {A2, B1}",
    ),
    "shared-oracle-correlated-routes": (
        "Candidate separate route",
        "Separate formulation",
        "Distinct verifier",
        "Independence audit",
        "OPEN",
    ),
    "invalidation-publication-state-machine": (
        "Nodes unreachable from this change are not invalidated by it",
        "their prior state remains separately governed",
    ),
}
for stem in stems:
    path = figure_dir / f"{stem}.svg"
    root = ET.parse(path).getroot()
    visible_text = strict_visible_text(root, path)
    raw_bytes = path.read_bytes()
    raw = raw_bytes.decode("utf-8")
    for literal in required_figure_language[stem]:
        if literal not in visible_text:
            fail(f"{path.name} lacks corrected visible semantic text: {literal!r}")
    for forbidden in (
        "Independent model",
        "Convergent evidence",
        "Unreachable upstream nodes remain valid",
        "Cut 2: {route A, route B}",
        "Cut 2: node set {A1, B1}",
        ">define<",
        ">execute<",
        ">justify<",
    ):
        if forbidden in raw:
            fail(f"{path.name} retains superseded implication language: {forbidden!r}")
    observed_svg_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    if observed_svg_sha256 != expected_svg_sha256[stem]:
        fail(
            f"{path.name} differs from its exact visually reviewed source bytes: "
            f"{observed_svg_sha256}"
        )
PY

python3 -I -S "$SNAPSHOT_ROOT/scripts/check-citation-edge-countermodel.py" >/dev/null
python3 -I -S "$SNAPSHOT_ROOT/scripts/check-citation-edge-countermodel-self-test.py" >/dev/null
python3 -I -S "$SNAPSHOT_ROOT/scripts/sync-mathematical-workflow-tex-self-test.py" \
  >/dev/null 2>&1
python3 -O -I -S "$SNAPSHOT_ROOT/scripts/sync-mathematical-workflow-tex-self-test.py" \
  >/dev/null 2>&1
python3 -I -S "$SNAPSHOT_ROOT/scripts/compare-formal-pdf-renders-self-test.py" \
  >/dev/null 2>&1
python3 -O -I -S "$SNAPSHOT_ROOT/scripts/compare-formal-pdf-renders-self-test.py" \
  >/dev/null 2>&1
bash "$SNAPSHOT_ROOT/scripts/check-formal-pdf-log-self-test.sh" >/dev/null
if [[ "$MODE" != "--refresh" ]]; then
  # The checker self-test contains accepted controls bound to the committed PDF, rendering
  # receipt, and independent visual receipt.  Refresh is the operation that creates/replaces the
  # first two and deliberately invalidates the third, so its accepted controls are necessarily
  # circular during bootstrap.  Exact/cross modes always run the full hostile suite.
  bash "$SNAPSHOT_ROOT/scripts/check-mathematical-workflow-pdf-self-test.sh" >/dev/null
fi

PDF_BUILD_HOME="$BUILD_ROOT/home"
PDF_XDG_CONFIG="$BUILD_ROOT/xdg-config"
PDF_XDG_CACHE="$BUILD_ROOT/xdg-cache"
PDF_TEXMF_HOME="$BUILD_ROOT/texmf-home"
PDF_TEXMF_CONFIG="$BUILD_ROOT/texmf-config"
PDF_TEXMF_VAR="$BUILD_ROOT/texmf-var"
PDF_TEXMF_CACHE="$BUILD_ROOT/texmf-cache"
FONT_ROOT="$BUILD_ROOT/report-fonts"
FORMAT_ROOT="$BUILD_ROOT/report-format"
FORMAT_PATH="$FORMAT_ROOT/lualatex.fmt"
EMPTY_FONT_ROOT="$BUILD_ROOT/empty-fonts"
FONT_CACHE="$BUILD_ROOT/font-cache"
FONT_CONFIG="$BUILD_ROOT/fontconfig.conf"
mkdir -p \
  "$PDF_BUILD_HOME" \
  "$PDF_XDG_CONFIG" \
  "$PDF_XDG_CACHE" \
  "$PDF_TEXMF_HOME" \
  "$PDF_TEXMF_CONFIG" \
  "$PDF_TEXMF_VAR" \
  "$PDF_TEXMF_CACHE" \
  "$FONT_ROOT" \
  "$FORMAT_ROOT" \
  "$EMPTY_FONT_ROOT" \
  "$FONT_CACHE"
mkdir -p "$PDF_XDG_CONFIG/luaotfload"
cat >"$PDF_XDG_CONFIG/luaotfload/luaotfload.conf" <<'EOF'
[db]
  update-live = false
  scan-local = false
  max-fonts = 64
  location-precedence = texmf
EOF
TEX_ENVIRONMENT=(
  "HOME=$PDF_BUILD_HOME"
  "XDG_CONFIG_HOME=$PDF_XDG_CONFIG"
  "XDG_CACHE_HOME=$PDF_XDG_CACHE"
  "TEXMFHOME=$PDF_TEXMF_HOME"
  "TEXMFCONFIG=$PDF_TEXMF_CONFIG"
  "TEXMFVAR=$PDF_TEXMF_VAR"
  "TEXMFCACHE=$PDF_TEXMF_CACHE"
  "LUATEX_CACHEDIR=$PDF_TEXMF_CACHE"
)
font_files=(
  "SourceSansPro-Regular.otf"
  "SourceSansPro-RegularIt.otf"
  "SourceSansPro-Semibold.otf"
  "SourceSansPro-SemiboldIt.otf"
  "SourceSansPro-Bold.otf"
  "SourceSansPro-BoldIt.otf"
  "lmroman10-regular.otf"
  "lmroman10-italic.otf"
  "lmroman10-bold.otf"
  "lmroman10-bolditalic.otf"
  "lmmono10-regular.otf"
  "lmmono10-italic.otf"
  "lmmonolt10-bold.otf"
  "lmmonolt10-boldoblique.otf"
  "latinmodern-math.otf"
)

capture_font_exact() {
  python3 -I -S - "$1" "$2" "$3" "$4" "$5" <<'PY'
from __future__ import annotations

import os
from pathlib import Path
import stat
import sys


def fail(detail: str) -> None:
    raise SystemExit(f"mathematical workflow PDF check: font source {detail}")


font_name, query_result, texmf_dist_raw, texmf_debian_raw, destination_root_raw = sys.argv[1:]
allowed_relative_paths = {
    "SourceSansPro-Regular.otf": "fonts/opentype/adobe/sourcesanspro/SourceSansPro-Regular.otf",
    "SourceSansPro-RegularIt.otf": "fonts/opentype/adobe/sourcesanspro/SourceSansPro-RegularIt.otf",
    "SourceSansPro-Semibold.otf": "fonts/opentype/adobe/sourcesanspro/SourceSansPro-Semibold.otf",
    "SourceSansPro-SemiboldIt.otf": "fonts/opentype/adobe/sourcesanspro/SourceSansPro-SemiboldIt.otf",
    "SourceSansPro-Bold.otf": "fonts/opentype/adobe/sourcesanspro/SourceSansPro-Bold.otf",
    "SourceSansPro-BoldIt.otf": "fonts/opentype/adobe/sourcesanspro/SourceSansPro-BoldIt.otf",
    "lmroman10-regular.otf": "fonts/opentype/public/lm/lmroman10-regular.otf",
    "lmroman10-italic.otf": "fonts/opentype/public/lm/lmroman10-italic.otf",
    "lmroman10-bold.otf": "fonts/opentype/public/lm/lmroman10-bold.otf",
    "lmroman10-bolditalic.otf": "fonts/opentype/public/lm/lmroman10-bolditalic.otf",
    "lmmono10-regular.otf": "fonts/opentype/public/lm/lmmono10-regular.otf",
    "lmmono10-italic.otf": "fonts/opentype/public/lm/lmmono10-italic.otf",
    "lmmonolt10-bold.otf": "fonts/opentype/public/lm/lmmonolt10-bold.otf",
    "lmmonolt10-boldoblique.otf": "fonts/opentype/public/lm/lmmonolt10-boldoblique.otf",
    "latinmodern-math.otf": "fonts/opentype/public/lm-math/latinmodern-math.otf",
}
relative_path = allowed_relative_paths.get(font_name)
if relative_path is None:
    fail(f"inventory contains an unrecognized filename: {font_name!r}")
if not query_result:
    fail(f"query is empty for {font_name}")
if "\n" in query_result or "\r" in query_result or not query_result.startswith("/"):
    fail(f"query is not one absolute LF-free path for {font_name}")

texmf_dist = Path(texmf_dist_raw)
texmf_debian = Path(texmf_debian_raw) if texmf_debian_raw else None
allowed_paths = [texmf_dist / relative_path]
# Debian and Ubuntu deliberately split the Latin Modern OpenType payload out of TEXMFDIST into
# TEXMFDEBIAN.  Source Sans Pro remains a TeX Live distribution file and is not admitted from the
# Debian overlay.  This is an exact two-layout portability rule, not an ambient font search.
if texmf_debian is not None and (
    font_name.startswith("lm") or font_name == "latinmodern-math.otf"
):
    allowed_paths.append(texmf_debian / relative_path)

source = Path(query_result)
if str(source) != query_result:
    fail(f"query is not canonically spelled for {font_name}: {query_result}")
if source not in allowed_paths:
    fail(f"query escapes the admitted exact TeX roots for {font_name}: {source}")
selected_root = next(root for root in (texmf_dist, texmf_debian) if root is not None and source == root / relative_path)
relative = Path(relative_path)
destination_root = Path(destination_root_raw)

required_open_flags = ("O_CLOEXEC", "O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
missing_open_flags = [name for name in required_open_flags if not hasattr(os, name)]
if missing_open_flags:
    fail(f"platform lacks required no-follow descriptor flags: {missing_open_flags}")
directory_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW
file_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
stable_fields = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_nlink",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)


def identity(status: os.stat_result) -> tuple[int, ...]:
    return tuple(getattr(status, field) for field in stable_fields)


def open_directory_chain(path: Path) -> tuple[int, tuple[tuple[int, int, int], ...]]:
    if not path.is_absolute() or str(path) != path.as_posix():
        fail(f"admitted root is not an exact absolute POSIX path: {path}")
    descriptor = os.open("/", directory_flags)
    identities = []
    try:
        root_status = os.fstat(descriptor)
        identities.append((root_status.st_dev, root_status.st_ino, root_status.st_mode))
        for component in path.parts[1:]:
            try:
                child = os.open(component, directory_flags, dir_fd=descriptor)
            except OSError as error:
                fail(f"cannot open direct directory component {component!r} in {path}: {error}")
            os.close(descriptor)
            descriptor = child
            child_status = os.fstat(descriptor)
            identities.append((child_status.st_dev, child_status.st_ino, child_status.st_mode))
        return descriptor, tuple(identities)
    except BaseException:
        os.close(descriptor)
        raise


def open_source_beneath(
    root_descriptor: int,
    relative_path_value: Path,
) -> tuple[int, int, os.stat_result, tuple[tuple[int, int, int], ...]]:
    if relative_path_value.is_absolute() or any(
        component in ("", ".", "..") for component in relative_path_value.parts
    ):
        fail(f"internal font path is not canonical: {relative_path_value}")
    directory_descriptor = os.dup(root_descriptor)
    directory_identities = []
    try:
        for component in relative_path_value.parts[:-1]:
            try:
                child = os.open(component, directory_flags, dir_fd=directory_descriptor)
            except OSError as error:
                fail(
                    f"cannot open direct font-directory component {component!r} "
                    f"for {font_name}: {error}"
                )
            os.close(directory_descriptor)
            directory_descriptor = child
            child_status = os.fstat(directory_descriptor)
            directory_identities.append(
                (child_status.st_dev, child_status.st_ino, child_status.st_mode)
            )
        leaf = relative_path_value.parts[-1]
        try:
            before_name = os.stat(leaf, dir_fd=directory_descriptor, follow_symlinks=False)
            if not stat.S_ISREG(before_name.st_mode):
                fail(f"is not a direct regular file for {font_name}: {source}")
            source_descriptor = os.open(leaf, file_flags, dir_fd=directory_descriptor)
        except OSError as error:
            fail(f"cannot open direct regular font file for {font_name}: {error}")
        opened = os.fstat(source_descriptor)
        if not stat.S_ISREG(before_name.st_mode) or not stat.S_ISREG(opened.st_mode):
            os.close(source_descriptor)
            fail(f"is not a direct regular file for {font_name}: {source}")
        if (before_name.st_dev, before_name.st_ino) != (opened.st_dev, opened.st_ino):
            os.close(source_descriptor)
            fail(f"changed during descriptor open for {font_name}: {source}")
        return directory_descriptor, source_descriptor, before_name, tuple(directory_identities)
    except BaseException:
        os.close(directory_descriptor)
        raise


root_descriptor, root_chain_before = open_directory_chain(selected_root)
parent_descriptor = -1
source_descriptor = -1
try:
    parent_descriptor, source_descriptor, before_name, relative_chain_before = open_source_beneath(
        root_descriptor, relative
    )
    before = os.fstat(source_descriptor)
    if before.st_size < 1 or before.st_size > 64 * 1024 * 1024:
        fail(f"size is outside the 1..67108864-byte bound for {font_name}: {before.st_size}")
    data = bytearray()
    while True:
        chunk = os.read(source_descriptor, min(1024 * 1024, before.st_size + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > before.st_size:
            fail(f"grew beyond its captured size for {font_name}")
    after = os.fstat(source_descriptor)
    after_name = os.stat(relative.parts[-1], dir_fd=parent_descriptor, follow_symlinks=False)
    if identity(before_name) != identity(before) or identity(before) != identity(after):
        fail(f"changed during descriptor capture for {font_name}: {source}")
    if identity(after_name) != identity(after):
        fail(f"namespace changed during descriptor capture for {font_name}: {source}")
    if len(data) != before.st_size:
        fail(f"size changed during descriptor capture for {font_name}: {source}")
finally:
    if source_descriptor >= 0:
        os.close(source_descriptor)
    if parent_descriptor >= 0:
        os.close(parent_descriptor)
    os.close(root_descriptor)

# Rewalk the complete absolute and relative directory chains after reading.  This catches a rename
# or replacement of any path component during capture while all source reads themselves remain
# anchored beneath no-follow descriptors.
root_descriptor, root_chain_after = open_directory_chain(selected_root)
parent_descriptor = -1
source_descriptor = -1
try:
    parent_descriptor, source_descriptor, final_name, relative_chain_after = open_source_beneath(
        root_descriptor, relative
    )
    final_status = os.fstat(source_descriptor)
    if (
        root_chain_before != root_chain_after
        or relative_chain_before != relative_chain_after
        or identity(final_name) != identity(before)
        or identity(final_status) != identity(before)
    ):
        fail(f"path changed across descriptor capture for {font_name}: {source}")
finally:
    if source_descriptor >= 0:
        os.close(source_descriptor)
    if parent_descriptor >= 0:
        os.close(parent_descriptor)
    os.close(root_descriptor)

destination_root_descriptor, destination_chain_before = open_directory_chain(destination_root)
destination_descriptor = -1
try:
    destination_descriptor = os.open(
        font_name,
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | os.O_CLOEXEC
        | os.O_NOFOLLOW
        | os.O_NONBLOCK,
        0o600,
        dir_fd=destination_root_descriptor,
    )
    destination_before = os.fstat(destination_descriptor)
    if not stat.S_ISREG(destination_before.st_mode):
        fail(f"destination is not a direct regular file for {font_name}")
    if destination_before.st_nlink != 1 or destination_before.st_size != 0:
        fail(f"destination is not a new single-link empty file for {font_name}")
    offset = 0
    while offset < len(data):
        written = os.write(destination_descriptor, data[offset:])
        if written <= 0:
            fail(f"destination write made no progress for {font_name}")
        offset += written
    destination_after = os.fstat(destination_descriptor)
    destination_name = os.stat(
        font_name, dir_fd=destination_root_descriptor, follow_symlinks=False
    )
    if identity(destination_before)[:4] != identity(destination_after)[:4]:
        fail(f"destination identity changed during write for {font_name}")
    if destination_after.st_nlink != 1:
        fail(f"destination gained another link during write for {font_name}")
    if identity(destination_name) != identity(destination_after):
        fail(f"destination namespace changed during write for {font_name}")
    if destination_after.st_size != len(data):
        fail(f"destination size changed during write for {font_name}")
finally:
    if destination_descriptor >= 0:
        os.close(destination_descriptor)
    os.close(destination_root_descriptor)

destination_root_descriptor, destination_chain_after = open_directory_chain(destination_root)
try:
    destination_final = os.stat(
        font_name, dir_fd=destination_root_descriptor, follow_symlinks=False
    )
    if destination_chain_before != destination_chain_after:
        fail(f"destination path changed across write for {font_name}")
    if identity(destination_final) != identity(destination_after):
        fail(f"destination file changed across write for {font_name}")
finally:
    os.close(destination_root_descriptor)
PY
}

capture_format_exact() {
  python3 -I -S - "$1" "$2" "$3" <<'PY'
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import sys


def fail(detail: str) -> None:
    raise SystemExit(f"mathematical workflow PDF check: format source {detail}")


query_result, texmf_sysvar_raw, destination_root_raw = sys.argv[1:]
format_name = "lualatex.fmt"
relative = Path("web2c/luahbtex") / format_name
if not query_result:
    fail("query is empty")
if "\n" in query_result or "\r" in query_result or not query_result.startswith("/"):
    fail("query is not one absolute LF-free path")

texmf_sysvar = Path(texmf_sysvar_raw)
source = Path(query_result)
destination_root = Path(destination_root_raw)
if str(source) != query_result:
    fail(f"query is not canonically spelled: {query_result}")
if source != texmf_sysvar / relative:
    fail(f"query escapes the one admitted generated-format leaf: {source}")

required_open_flags = ("O_CLOEXEC", "O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
missing_open_flags = [name for name in required_open_flags if not hasattr(os, name)]
if missing_open_flags:
    fail(f"platform lacks required no-follow descriptor flags: {missing_open_flags}")
directory_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW
source_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
stable_fields = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_nlink",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)


def identity(status: os.stat_result) -> tuple[int, ...]:
    return tuple(getattr(status, field) for field in stable_fields)


def open_directory_chain(path: Path) -> tuple[int, tuple[tuple[int, int, int], ...]]:
    if not path.is_absolute() or str(path) != path.as_posix():
        fail(f"admitted root is not an exact absolute POSIX path: {path}")
    descriptor = os.open("/", directory_flags)
    identities = []
    try:
        root_status = os.fstat(descriptor)
        identities.append((root_status.st_dev, root_status.st_ino, root_status.st_mode))
        for component in path.parts[1:]:
            try:
                child = os.open(component, directory_flags, dir_fd=descriptor)
            except OSError as error:
                fail(f"cannot open direct directory component {component!r} in {path}: {error}")
            os.close(descriptor)
            descriptor = child
            child_status = os.fstat(descriptor)
            identities.append((child_status.st_dev, child_status.st_ino, child_status.st_mode))
        return descriptor, tuple(identities)
    except BaseException:
        os.close(descriptor)
        raise


def open_source_beneath(
    root_descriptor: int,
) -> tuple[int, int, os.stat_result, tuple[tuple[int, int, int], ...]]:
    directory_descriptor = os.dup(root_descriptor)
    directory_identities = []
    try:
        for component in relative.parts[:-1]:
            try:
                child = os.open(component, directory_flags, dir_fd=directory_descriptor)
            except OSError as error:
                fail(f"cannot open direct format-directory component {component!r}: {error}")
            os.close(directory_descriptor)
            directory_descriptor = child
            child_status = os.fstat(directory_descriptor)
            directory_identities.append(
                (child_status.st_dev, child_status.st_ino, child_status.st_mode)
            )
        leaf = relative.parts[-1]
        try:
            before_name = os.stat(leaf, dir_fd=directory_descriptor, follow_symlinks=False)
            if not stat.S_ISREG(before_name.st_mode):
                fail(f"is not a direct regular file: {source}")
            source_descriptor = os.open(leaf, source_flags, dir_fd=directory_descriptor)
        except OSError as error:
            fail(f"cannot open direct regular format file: {error}")
        opened = os.fstat(source_descriptor)
        if not stat.S_ISREG(opened.st_mode):
            os.close(source_descriptor)
            fail(f"is not a direct regular file: {source}")
        if (before_name.st_dev, before_name.st_ino) != (opened.st_dev, opened.st_ino):
            os.close(source_descriptor)
            fail(f"changed during descriptor open: {source}")
        return directory_descriptor, source_descriptor, before_name, tuple(directory_identities)
    except BaseException:
        os.close(directory_descriptor)
        raise


root_descriptor, root_chain_before = open_directory_chain(texmf_sysvar)
parent_descriptor = -1
source_descriptor = -1
try:
    parent_descriptor, source_descriptor, before_name, relative_chain_before = open_source_beneath(
        root_descriptor
    )
    before = os.fstat(source_descriptor)
    if before.st_size < 1 or before.st_size > 64 * 1024 * 1024:
        fail(f"size is outside the 1..67108864-byte bound: {before.st_size}")
    data = bytearray()
    while len(data) < before.st_size:
        chunk = os.read(source_descriptor, min(1024 * 1024, before.st_size - len(data)))
        if not chunk:
            fail("truncated during descriptor capture")
        data.extend(chunk)
    if os.read(source_descriptor, 1):
        fail("grew beyond its captured size")
    after = os.fstat(source_descriptor)
    after_name = os.stat(relative.parts[-1], dir_fd=parent_descriptor, follow_symlinks=False)
    if identity(before_name) != identity(before) or identity(before) != identity(after):
        fail(f"changed during descriptor capture: {source}")
    if identity(after_name) != identity(after):
        fail(f"namespace changed during descriptor capture: {source}")
finally:
    if source_descriptor >= 0:
        os.close(source_descriptor)
    if parent_descriptor >= 0:
        os.close(parent_descriptor)
    os.close(root_descriptor)

# Rewalk the absolute and relative source path after reading so a component rename cannot silently
# retarget the leaf while the actual read remains anchored beneath no-follow descriptors.
root_descriptor, root_chain_after = open_directory_chain(texmf_sysvar)
parent_descriptor = -1
source_descriptor = -1
try:
    parent_descriptor, source_descriptor, final_name, relative_chain_after = open_source_beneath(
        root_descriptor
    )
    final_status = os.fstat(source_descriptor)
    if (
        root_chain_before != root_chain_after
        or relative_chain_before != relative_chain_after
        or identity(final_name) != identity(before)
        or identity(final_status) != identity(before)
    ):
        fail(f"path changed across descriptor capture: {source}")
finally:
    if source_descriptor >= 0:
        os.close(source_descriptor)
    if parent_descriptor >= 0:
        os.close(parent_descriptor)
    os.close(root_descriptor)

destination_root_descriptor, destination_chain_before = open_directory_chain(destination_root)
destination_descriptor = -1
try:
    try:
        destination_descriptor = os.open(
            format_name,
            os.O_RDWR
            | os.O_CREAT
            | os.O_EXCL
            | os.O_CLOEXEC
            | os.O_NOFOLLOW
            | os.O_NONBLOCK,
            0o600,
            dir_fd=destination_root_descriptor,
        )
    except OSError as error:
        fail(f"cannot create the exclusive private format leaf: {error}")
    destination_before = os.fstat(destination_descriptor)
    if not stat.S_ISREG(destination_before.st_mode):
        fail("destination is not a direct regular file")
    if destination_before.st_nlink != 1 or destination_before.st_size != 0:
        fail("destination is not a new single-link empty file")
    view = memoryview(data)
    while view:
        written = os.write(destination_descriptor, view)
        if written <= 0:
            fail("destination write made no progress")
        view = view[written:]
    os.fsync(destination_descriptor)
    os.fchmod(destination_descriptor, 0o444)
    os.fsync(destination_descriptor)
    destination_after = os.fstat(destination_descriptor)
    destination_name = os.stat(
        format_name, dir_fd=destination_root_descriptor, follow_symlinks=False
    )
    if (destination_before.st_dev, destination_before.st_ino) != (
        destination_after.st_dev,
        destination_after.st_ino,
    ):
        fail("destination identity changed during write")
    if destination_after.st_nlink != 1 or destination_after.st_size != len(data):
        fail("destination link count or size changed during write")
    if identity(destination_name) != identity(destination_after):
        fail("destination namespace changed during write")
    if stat.S_IMODE(destination_after.st_mode) != 0o444:
        fail("destination did not become mode 0444")
    os.lseek(destination_descriptor, 0, os.SEEK_SET)
    observed = bytearray()
    while len(observed) < len(data):
        block = os.read(destination_descriptor, min(1024 * 1024, len(data) - len(observed)))
        if not block:
            fail("destination truncated during descriptor replay")
        observed.extend(block)
    if os.read(destination_descriptor, 1) or observed != data:
        fail("destination differs from the captured source bytes")
finally:
    if destination_descriptor >= 0:
        os.close(destination_descriptor)
    os.close(destination_root_descriptor)

destination_root_descriptor, destination_chain_after = open_directory_chain(destination_root)
try:
    destination_final = os.stat(
        format_name, dir_fd=destination_root_descriptor, follow_symlinks=False
    )
    if destination_chain_before != destination_chain_after:
        fail("destination path changed across write")
    if identity(destination_final) != identity(destination_after):
        fail("destination file changed across write")
finally:
    os.close(destination_root_descriptor)

print(f"{len(data)}\t{hashlib.sha256(data).hexdigest()}")
PY
}

verify_captured_format_exact() {
  python3 -I -S - "$1" "$2" "$3" <<'PY'
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import sys


path = Path(sys.argv[1])
expected_size_raw = sys.argv[2]
expected_sha256 = sys.argv[3]
if not path.is_absolute() or str(path) != path.as_posix() or path.name != "lualatex.fmt":
    raise SystemExit(
        "mathematical workflow PDF check: captured format path is not the exact absolute leaf"
    )
if not expected_size_raw.isdigit() or int(expected_size_raw) < 1:
    raise SystemExit("mathematical workflow PDF check: captured format size receipt is invalid")
expected_size = int(expected_size_raw)
if len(expected_sha256) != 64 or any(character not in "0123456789abcdef" for character in expected_sha256):
    raise SystemExit("mathematical workflow PDF check: captured format digest receipt is invalid")
for required_flag in ("O_CLOEXEC", "O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK"):
    if not hasattr(os, required_flag):
        raise SystemExit(
            f"mathematical workflow PDF check: captured format verification lacks {required_flag}"
        )
directory_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW
file_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
root_name = path.parent.lstat()
root_descriptor = os.open(path.parent, directory_flags)
descriptor = -1
try:
    root_before = os.fstat(root_descriptor)
    if not stat.S_ISDIR(root_before.st_mode) or stat.S_IMODE(root_before.st_mode) != 0o555:
        raise SystemExit(
            "mathematical workflow PDF check: captured format root is not a mode-0555 directory"
        )
    if (root_name.st_dev, root_name.st_ino, root_name.st_mode) != (
        root_before.st_dev,
        root_before.st_ino,
        root_before.st_mode,
    ):
        raise SystemExit(
            "mathematical workflow PDF check: captured format root descriptor/path identity differs"
        )
    if os.listdir(root_descriptor) != [path.name]:
        raise SystemExit(
            "mathematical workflow PDF check: captured format root inventory is not exact"
        )
    before_name = os.stat(path.name, dir_fd=root_descriptor, follow_symlinks=False)
    try:
        descriptor = os.open(path.name, file_flags, dir_fd=root_descriptor)
    except OSError as error:
        raise SystemExit(
            f"mathematical workflow PDF check: captured format descriptor open failed: {error}"
        )
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise SystemExit(
            "mathematical workflow PDF check: captured format is not a single-link regular file"
        )
    if stat.S_IMODE(before.st_mode) != 0o444 or before.st_size != expected_size:
        raise SystemExit(
            "mathematical workflow PDF check: captured format mode or size receipt drifted"
        )
    if (before_name.st_dev, before_name.st_ino, before_name.st_size, before_name.st_mode) != (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mode,
    ):
        raise SystemExit(
            "mathematical workflow PDF check: captured format descriptor/path identity differs"
        )
    digest = hashlib.sha256()
    remaining = expected_size
    while remaining:
        block = os.read(descriptor, min(remaining, 1024 * 1024))
        if not block:
            raise SystemExit("mathematical workflow PDF check: captured format truncated")
        digest.update(block)
        remaining -= len(block)
    if os.read(descriptor, 1):
        raise SystemExit("mathematical workflow PDF check: captured format grew")
    after = os.fstat(descriptor)
finally:
    if descriptor >= 0:
        os.close(descriptor)
    os.close(root_descriptor)
root_after_name = path.parent.lstat()
root_descriptor = os.open(path.parent, directory_flags)
try:
    root_after = os.fstat(root_descriptor)
    if os.listdir(root_descriptor) != [path.name]:
        raise SystemExit(
            "mathematical workflow PDF check: captured format root inventory changed"
        )
    after_name = os.stat(path.name, dir_fd=root_descriptor, follow_symlinks=False)
finally:
    os.close(root_descriptor)
stable_fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
if tuple(getattr(before, field) for field in stable_fields) != tuple(
    getattr(after, field) for field in stable_fields
) or tuple(getattr(after, field) for field in stable_fields) != tuple(
    getattr(after_name, field) for field in stable_fields
):
    raise SystemExit("mathematical workflow PDF check: captured format changed during verification")
if (root_before.st_dev, root_before.st_ino, root_before.st_mode) != (
    root_after.st_dev,
    root_after.st_ino,
    root_after.st_mode,
) or (root_after_name.st_dev, root_after_name.st_ino, root_after_name.st_mode) != (
    root_after.st_dev,
    root_after.st_ino,
    root_after.st_mode,
):
    raise SystemExit("mathematical workflow PDF check: captured format root changed")
if digest.hexdigest() != expected_sha256:
    raise SystemExit("mathematical workflow PDF check: captured format digest receipt drifted")
PY
}

adjudicate_texmfdebian_query() {
  local query_status="$1"
  local query_output="$2"
  if [[ "$query_status" -eq 0 && -n "$query_output" ]]; then
    printf '%s' "$query_output"
  elif [[ "$query_status" -eq 1 && -z "$query_output" ]]; then
    # Upstream TeX Live has no Debian overlay variable.  Kpathsea writes a blank line and returns
    # status 1; Bash command substitution removes the trailing LF before this function sees it.
    return 0
  else
    echo "mathematical workflow PDF check: Debian TeX overlay query failed unexpectedly" >&2
    return 2
  fi
}
# TEXMFDEBIAN_QUERY_END

TEXMFDIST_ROOT="$(env -i \
  "${CLEAN_BASE_ENV[@]}" \
  "HOME=$PDF_BUILD_HOME" \
  "XDG_CONFIG_HOME=$PDF_XDG_CONFIG" \
  "XDG_CACHE_HOME=$PDF_XDG_CACHE" \
  kpsewhich -var-value=TEXMFDIST)"
TEXMFROOT_ROOT="$(env -i \
  "${CLEAN_BASE_ENV[@]}" \
  "HOME=$PDF_BUILD_HOME" \
  "XDG_CONFIG_HOME=$PDF_XDG_CONFIG" \
  "XDG_CACHE_HOME=$PDF_XDG_CACHE" \
  kpsewhich -var-value=TEXMFROOT)"
TEXMFSYSVAR_ROOT="$(env -i \
  "${CLEAN_BASE_ENV[@]}" \
  "HOME=$PDF_BUILD_HOME" \
  "XDG_CONFIG_HOME=$PDF_XDG_CONFIG" \
  "XDG_CACHE_HOME=$PDF_XDG_CACHE" \
  kpsewhich -var-value=TEXMFSYSVAR)"
TEXMFDEBIAN_ROOT=""
# Upstream TeX Live does not define the Debian packaging overlay: Kpathsea returns status 1 and a
# blank line, which command substitution normalizes to an empty captured value.  Debian-family
# installations define the variable and must return its exact root after the same normalization.
if texmf_debian_query="$(env -i \
  "${CLEAN_BASE_ENV[@]}" \
  "HOME=$PDF_BUILD_HOME" \
  "XDG_CONFIG_HOME=$PDF_XDG_CONFIG" \
  "XDG_CACHE_HOME=$PDF_XDG_CACHE" \
  kpsewhich -var-value=TEXMFDEBIAN)"; then
  texmf_debian_query_status=0
else
  texmf_debian_query_status=$?
fi
if ! TEXMFDEBIAN_ROOT="$(adjudicate_texmfdebian_query \
  "$texmf_debian_query_status" "$texmf_debian_query")"; then
  exit 2
fi
if [[ -z "$TEXMFDIST_ROOT" || ! -d "$TEXMFDIST_ROOT" \
    || -z "$TEXMFROOT_ROOT" || ! -d "$TEXMFROOT_ROOT" \
    || -z "$TEXMFSYSVAR_ROOT" || ! -d "$TEXMFSYSVAR_ROOT" ]]; then
  echo "$CHECK_NAME: TeX Live distribution root is unavailable" >&2
  exit 2
fi
TEXMFDIST_ROOT="$(cd "$TEXMFDIST_ROOT" && pwd -P)"
TEXMFROOT_ROOT="$(cd "$TEXMFROOT_ROOT" && pwd -P)"
TEXMFSYSVAR_ROOT="$(cd "$TEXMFSYSVAR_ROOT" && pwd -P)"
require_safe_path "$TEXMFDIST_ROOT" "TeX distribution root"
require_safe_path "$TEXMFROOT_ROOT" "TeX installation root"
require_safe_path "$TEXMFSYSVAR_ROOT" "TeX generated-state root"
if [[ "$TEXMFDIST_ROOT" != "$TEXMFROOT_ROOT"/* ]]; then
  echo "$CHECK_NAME: TeX distribution root escapes the declared TeX installation root" >&2
  exit 2
fi
if [[ -n "$TEXMFDEBIAN_ROOT" ]]; then
  if [[ "$TEXMFDEBIAN_ROOT" != "/usr/share/texmf" || ! -d "$TEXMFDEBIAN_ROOT" ]]; then
    echo "$CHECK_NAME: unsupported Debian TeX overlay root: $TEXMFDEBIAN_ROOT" >&2
    exit 2
  fi
  TEXMFDEBIAN_ROOT="$(cd "$TEXMFDEBIAN_ROOT" && pwd -P)"
  require_safe_path "$TEXMFDEBIAN_ROOT" "Debian TeX overlay root"
  if [[ "$TEXMFDEBIAN_ROOT" != "/usr/share/texmf" ]]; then
    echo "$CHECK_NAME: Debian TeX overlay root is not canonical" >&2
    exit 2
  fi
fi
if ! FORMAT_QUERY="$(env -i \
  "${CLEAN_BASE_ENV[@]}" \
  "${TEX_ENVIRONMENT[@]}" \
  kpsewhich \
    --engine=luahbtex \
    --progname=lualatex \
    --must-exist \
    --format=fmt \
    lualatex.fmt)"; then
  echo "$CHECK_NAME: required LuaLaTeX format is unavailable" >&2
  exit 2
fi
if ! FORMAT_CAPTURE="$(capture_format_exact \
  "$FORMAT_QUERY" "$TEXMFSYSVAR_ROOT" "$FORMAT_ROOT")"; then
  exit 2
fi
IFS=$'\t' read -r FORMAT_BYTES FORMAT_SHA256 <<<"$FORMAT_CAPTURE"
if [[ ! "$FORMAT_BYTES" =~ ^[1-9][0-9]*$ \
    || ! "$FORMAT_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
  echo "$CHECK_NAME: captured LuaLaTeX format receipt is malformed" >&2
  exit 2
fi
readonly FORMAT_BYTES FORMAT_SHA256
chmod 0555 "$FORMAT_ROOT"
if ! verify_captured_format_exact \
  "$FORMAT_PATH" "$FORMAT_BYTES" "$FORMAT_SHA256"; then
  exit 2
fi
TEX_ENVIRONMENT+=("TEXFORMATS=$FORMAT_ROOT")
if ! PRIVATE_FORMAT_SEARCH_PATH="$(env -i \
  "${CLEAN_BASE_ENV[@]}" \
  "${TEX_ENVIRONMENT[@]}" \
  kpsewhich \
    --engine=luahbtex \
    --progname=lualatex \
    --show-path=fmt)"; then
  echo "$CHECK_NAME: private LuaLaTeX format search-path query failed" >&2
  exit 2
fi
if ! PRIVATE_FORMAT_QUERY="$(env -i \
  "${CLEAN_BASE_ENV[@]}" \
  "${TEX_ENVIRONMENT[@]}" \
  kpsewhich \
    --engine=luahbtex \
    --progname=lualatex \
    --must-exist \
    --format=fmt \
    lualatex.fmt)"; then
  echo "$CHECK_NAME: private LuaLaTeX format lookup failed" >&2
  exit 2
fi
if [[ "$PRIVATE_FORMAT_SEARCH_PATH" != "$FORMAT_ROOT" \
    || "$PRIVATE_FORMAT_QUERY" != "$FORMAT_PATH" ]]; then
  echo "$CHECK_NAME: private LuaLaTeX format lookup escaped its exact snapshot" >&2
  exit 1
fi
for font in "${font_files[@]}"; do
  if ! font_query="$(env -i \
    "${CLEAN_BASE_ENV[@]}" \
    "${TEX_ENVIRONMENT[@]}" \
    kpsewhich --must-exist "$font")"; then
    echo "$CHECK_NAME: required TeX font is unavailable: $font" >&2
    exit 2
  fi
  if ! capture_font_exact \
    "$font" "$font_query" "$TEXMFDIST_ROOT" "$TEXMFDEBIAN_ROOT" "$FONT_ROOT"; then
    exit 2
  fi
done
cat >"$FONT_CONFIG" <<EOF
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>$FONT_ROOT</dir>
  <cachedir>$FONT_CACHE</cachedir>
  <config></config>
</fontconfig>
EOF
env -i \
  "${CLEAN_BASE_ENV[@]}" \
  "${TEX_ENVIRONMENT[@]}" \
  "FONTCONFIG_FILE=$FONT_CONFIG" \
  "FONTCONFIG_PATH=$BUILD_ROOT" \
  fc-cache -f >/dev/null

RENDER_ENVIRONMENT=(
  "${TEX_ENVIRONMENT[@]}"
  "FONTCONFIG_FILE=$FONT_CONFIG"
  "FONTCONFIG_PATH=$BUILD_ROOT"
  "PANGOCAIRO_BACKEND=fc"
  "OSFONTDIR=$FONT_ROOT"
  "OPENTYPEFONTS=$FONT_ROOT"
  "TTFONTS=$EMPTY_FONT_ROOT"
  "T1FONTS=$EMPTY_FONT_ROOT"
  "AFMFONTS=$EMPTY_FONT_ROOT"
  "SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH_VALUE"
  "TZ=UTC"
)

decorate_figure_pdf() {
  local raw_pdf="$1"
  local output_pdf="$2"
  local title="$3"
  local source_svg="$4"
  python3 -I -S - "$raw_pdf" "$output_pdf" "$title" "$source_svg" <<'PY'
import hashlib
from pathlib import Path
import sys
import sysconfig

for package_root in dict.fromkeys((sysconfig.get_path("purelib"), sysconfig.get_path("platlib"))):
    if package_root:
        sys.path.insert(0, package_root)

from pypdf import PdfWriter
from pypdf.generic import BooleanObject, DictionaryObject, NameObject, TextStringObject


raw = Path(sys.argv[1])
output = Path(sys.argv[2])
title = sys.argv[3]
source_svg = Path(sys.argv[4])
source_svg_sha256 = hashlib.sha256(source_svg.read_bytes()).hexdigest()
writer = PdfWriter(clone_from=raw)
writer.pdf_header = "%PDF-1.7"
writer.root_object[NameObject("/Lang")] = TextStringObject("en")
writer.root_object[NameObject("/ViewerPreferences")] = DictionaryObject(
    {NameObject("/DisplayDocTitle"): BooleanObject(True)}
)
writer.add_metadata(
    {
        "/Title": title,
        "/Subject": "Mathematical problem-solving workflow assurance diagram",
        "/Keywords": "pid-rs, mathematical workflow, assurance, evidence",
        "/Author": "pid-rs contributors",
        "/Creator": "pid-rs deterministic SVG derivative pipeline",
        "/Producer": "pid-rs deterministic SVG derivative pipeline",
        "/CreationDate": "D:20260803000000Z",
        "/ModDate": "D:20260803000000Z",
        "/PidRsSourceSvgSHA256": source_svg_sha256,
    }
)
with output.open("wb") as stream:
    writer.write(stream)
PY
}

figure_title() {
  case "$1" in
    four-object-assurance-chain)
      printf '%s\n' 'Four-object assurance chain'
      ;;
    obligation-dag-minimal-cuts)
      printf '%s\n' 'AND OR obligation DAG with inclusion-minimal cuts'
      ;;
    shared-oracle-correlated-routes)
      printf '%s\n' 'Correlated routes through a shared oracle'
      ;;
    invalidation-publication-state-machine)
      printf '%s\n' 'Dependency invalidation and publication state machine'
      ;;
    *)
      echo "$CHECK_NAME: internal figure-title inventory error: $1" >&2
      return 2
      ;;
  esac
}

figure_height_mm() {
  case "$1" in
    four-object-assurance-chain) printf '%s\n' 64 ;;
    obligation-dag-minimal-cuts) printf '%s\n' 78 ;;
    shared-oracle-correlated-routes) printf '%s\n' 76 ;;
    invalidation-publication-state-machine) printf '%s\n' 84 ;;
    *) return 2 ;;
  esac
}

figure_sentinel() {
  case "$1" in
    four-object-assurance-chain) printf '%s\n' 'Keep the scientific objects distinct' ;;
    obligation-dag-minimal-cuts) printf '%s\n' 'Accepted routes, AND prerequisites' ;;
    shared-oracle-correlated-routes) printf '%s\n' 'Five routes may still be one route semantically' ;;
    invalidation-publication-state-machine) printf '%s\n' 'Prerequisites point toward dependents; invalidation follows the arrows' ;;
    *) return 2 ;;
  esac
}

validate_font_table() {
  local pdf="$1"
  local label="$2"
  if ! LC_ALL=C pdffonts "$pdf" | awk '
    NR > 2 {
      seen = 1
      if ($(NF - 4) != "yes" || $(NF - 3) != "yes" || $(NF - 2) != "yes") bad = 1
    }
    END { exit (!seen || bad) }
  '; then
    echo "$CHECK_NAME: $label lacks an embedded, subset, Unicode-mapped font" >&2
    exit 1
  fi
}

validate_figure_pdf() {
  local pdf="$1"
  local stem="$2"
  local label="$3"
  local title="$4"
  local height_mm="$5"
  local source_svg="$6"
  local info="$BUILD_ROOT/$label.info"
  LC_ALL=C pdfinfo "$pdf" >"$info"
  for predicate in \
    '^Pages:[[:space:]]+1$' \
    '^Encrypted:[[:space:]]+no$' \
    '^Tagged:[[:space:]]+no$' \
    '^Form:[[:space:]]+none$' \
    '^JavaScript:[[:space:]]+no$' \
    '^PDF version:[[:space:]]+1\.7$'; do
    if ! grep -Eq "$predicate" "$info"; then
      echo "$CHECK_NAME: $label violates figure PDF predicate: $predicate" >&2
      exit 1
    fi
  done
  validate_font_table "$pdf" "$label"
  if ! LC_ALL=C pdffonts "$pdf" | grep -F 'SourceSansPro' >/dev/null \
    || ! LC_ALL=C pdffonts "$pdf" | grep -F 'LMRoman' >/dev/null; then
    echo "$CHECK_NAME: $label does not embed both Source Sans and Latin Modern Roman" >&2
    exit 1
  fi
  python3 -I -S - "$pdf" "$title" "$height_mm" "$source_svg" <<'PY'
import hashlib
from pathlib import Path
import sys
import sysconfig

for package_root in dict.fromkeys((sysconfig.get_path("purelib"), sysconfig.get_path("platlib"))):
    if package_root:
        sys.path.insert(0, package_root)

from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject


def fail(detail: str) -> None:
    print(f"mathematical workflow PDF check: figure PDF {detail}", file=sys.stderr)
    raise SystemExit(1)


def resolve(value):
    return value.get_object() if isinstance(value, IndirectObject) else value


path = Path(sys.argv[1])
expected_title = sys.argv[2]
height_mm = float(sys.argv[3])
source_svg_sha256 = hashlib.sha256(Path(sys.argv[4]).read_bytes()).hexdigest()
reader = PdfReader(path, strict=True)
root = resolve(reader.trailer["/Root"])
if reader.pdf_header != "%PDF-1.7":
    fail("header is not PDF 1.7")
if str(root.get("/Lang")) != "en":
    fail("catalog /Lang is not en")
if root.get("/StructTreeRoot") is not None or bool(resolve(root.get("/MarkInfo", {})).get("/Marked", False)):
    fail("claims tagged structure without a reviewed tag tree")
if root.get("/AcroForm") is not None:
    fail("contains an AcroForm")
for forbidden_key in ("/OpenAction", "/AA", "/AF", "/Collection"):
    if root.get(forbidden_key) is not None:
        fail(f"catalog contains forbidden active/associated content: {forbidden_key}")
if root.get("/Dests") is not None:
    fail("catalog contains a competing legacy /Dests dictionary")
names = resolve(root.get("/Names", {}))
unexpected_name_trees = set(names) - {"/Dests"}
if unexpected_name_trees:
    fail(f"catalog contains an unapproved name tree: {sorted(map(str, unexpected_name_trees))}")
metadata = reader.metadata
expected_metadata = {
    "/Title": expected_title,
    "/Subject": "Mathematical problem-solving workflow assurance diagram",
    "/Keywords": "pid-rs, mathematical workflow, assurance, evidence",
    "/Author": "pid-rs contributors",
    "/Creator": "pid-rs deterministic SVG derivative pipeline",
    "/Producer": "pid-rs deterministic SVG derivative pipeline",
    "/CreationDate": "D:20260803000000Z",
    "/ModDate": "D:20260803000000Z",
    "/PidRsSourceSvgSHA256": source_svg_sha256,
}
for key, expected in expected_metadata.items():
    if metadata.get(key) != expected:
        fail(f"metadata {key} differs: {metadata.get(key)!r}")
if len(reader.pages) != 1:
    fail("is not exactly one page")
page = reader.pages[0]
media_coordinates = tuple(map(float, page.mediabox))
if len(media_coordinates) != 4:
    fail("MediaBox is malformed")
x_min, y_min, x_max, y_max = media_coordinates
width = x_max - x_min
height = y_max - y_min
if abs(width - 160 * 72 / 25.4) > 0.02 or abs(height - height_mm * 72 / 25.4) > 0.02:
    fail(f"geometry differs: {width} x {height}")
if abs(x_min) > 1e-9 or abs(y_min) > 1e-9:
    fail("MediaBox origin differs from zero")
if (page.get("/Rotate") or 0) != 0:
    fail("page is rotated")
for box_name, box in (
    ("CropBox", page.cropbox),
    ("BleedBox", page.bleedbox),
    ("TrimBox", page.trimbox),
    ("ArtBox", page.artbox),
):
    if tuple(map(float, box)) != media_coordinates:
        fail(f"{box_name} differs from MediaBox")
try:
    user_unit = float(page.get("/UserUnit", 1))
except (TypeError, ValueError):
    fail("UserUnit is malformed")
if user_unit != 1.0:
    fail("UserUnit differs from 1")
if page.get("/Annots"):
    fail("contains unexpected annotations or URL actions")

forbidden_keys = {
    "/A",
    "/AA",
    "/AF",
    "/Collection",
    "/EF",
    "/EmbeddedFiles",
    "/JavaScript",
    "/JS",
    "/OpenAction",
    "/RichMediaContent",
    "/RichMediaSettings",
    "/XFA",
}
forbidden_subtypes = {
    "/3D",
    "/FileAttachment",
    "/Movie",
    "/RichMedia",
    "/Screen",
    "/Sound",
}
seen_indirect: set[tuple[int, int]] = set()
seen_direct: set[int] = set()


def walk(value, location: str) -> None:
    if isinstance(value, IndirectObject):
        identity = (value.idnum, value.generation)
        if identity in seen_indirect:
            return
        seen_indirect.add(identity)
        value = value.get_object()
    else:
        identity = id(value)
        if identity in seen_direct:
            return
        seen_direct.add(identity)
    if isinstance(value, DictionaryObject):
        object_type = str(value.get("/Type"))
        subtype = str(value.get("/Subtype"))
        if object_type in {"/Action", "/Filespec"} or subtype in forbidden_subtypes:
            fail(f"contains an active or file-specification object at {location}")
        present = forbidden_keys.intersection(map(str, value.keys()))
        if present:
            fail(f"contains forbidden active keys at {location}: {sorted(present)!r}")
        for key, child in value.items():
            walk(child, f"{location}/{key}")
    elif isinstance(value, (ArrayObject, list, tuple)):
        for index, child in enumerate(value):
            walk(child, f"{location}[{index}]")


walk(reader.trailer["/Root"], "catalog")
PY
}

render_pdf_page_set() {
  local pdf="$1"
  local output_directory="$2"
  local label="$3"
  local mode="$4"
  local -a mode_arguments=(-png)
  if [[ "$mode" == "gray" ]]; then
    mode_arguments+=(-gray)
  elif [[ "$mode" != "color" ]]; then
    echo "$CHECK_NAME: internal Poppler render mode error: $mode" >&2
    exit 2
  fi
  mkdir -p "$output_directory"
  if ! env -i \
    "${CLEAN_BASE_ENV[@]}" \
    "HOME=$BUILD_ROOT/pdf-tools-home" \
    "TMPDIR=$BUILD_ROOT/tmp" \
    pdftoppm "${mode_arguments[@]}" -r "$RENDER_DPI" \
      "$pdf" "$output_directory/page" \
      >"$BUILD_ROOT/$label.stdout" 2>"$BUILD_ROOT/$label.stderr"; then
    cat "$BUILD_ROOT/$label.stdout" "$BUILD_ROOT/$label.stderr" >&2
    echo "$CHECK_NAME: Poppler rendering failed: $label" >&2
    exit 1
  fi
  for diagnostic in "$BUILD_ROOT/$label.stdout" "$BUILD_ROOT/$label.stderr"; do
    if [[ -s "$diagnostic" ]]; then
      cat "$diagnostic" >&2
      echo "$CHECK_NAME: Poppler emitted a rendering diagnostic: $label" >&2
      exit 1
    fi
  done
}

compare_render_sets() {
  local left_directory="$1"
  local right_directory="$2"
  local pages="$3"
  local label="$4"
  local receipt="$5"
  python3 -I -S "$SNAPSHOT_ROOT/scripts/compare-formal-pdf-renders.py" \
    --left-dir "$left_directory" \
    --right-dir "$right_directory" \
    --pages "$pages" \
    --label "$label" \
    --receipt "$receipt" \
    --large-delta 24 \
    --max-mean-abs 0.20 \
    --max-changed-fraction 0.01 \
    --max-large-fraction 0.001
}

PAIR_ROOT="$BUILD_ROOT/figure-pairs"
REPORT_FIGURE_DIR="$BUILD_ROOT/report-figures"
mkdir -p "$PAIR_ROOT" "$REPORT_FIGURE_DIR" "$BUILD_ROOT/pdf-tools-home"
for stem in "${FIGURE_STEMS[@]}"; do
  svg="$SNAPSHOT_ROOT/$FIGURE_DIR/$stem.svg"
  committed_figure="$SNAPSHOT_ROOT/$FIGURE_DIR/$stem.pdf"
  raw_a="$PAIR_ROOT/$stem.a.raw.pdf"
  raw_b="$PAIR_ROOT/$stem.b.raw.pdf"
  regenerated_a="$PAIR_ROOT/$stem.a.pdf"
  regenerated_b="$PAIR_ROOT/$stem.b.pdf"
  title="$(figure_title "$stem")"
  height_mm="$(figure_height_mm "$stem")"

  xmllint --nonet --noout "$svg"
  env -i "${CLEAN_BASE_ENV[@]}" "${RENDER_ENVIRONMENT[@]}" \
    rsvg-convert --format=pdf --keep-aspect-ratio --output="$raw_a" "$svg"
  env -i "${CLEAN_BASE_ENV[@]}" "${RENDER_ENVIRONMENT[@]}" \
    rsvg-convert --format=pdf --keep-aspect-ratio --output="$raw_b" "$svg"
  decorate_figure_pdf "$raw_a" "$regenerated_a" "$title" "$svg"
  decorate_figure_pdf "$raw_b" "$regenerated_b" "$title" "$svg"
  if ! cmp -s "$regenerated_a" "$regenerated_b"; then
    echo "$CHECK_NAME: two SVG derivative builds are not byte-identical: $stem" >&2
    exit 1
  fi

  validate_figure_pdf \
    "$regenerated_a" "$stem" "$stem-generated" "$title" "$height_mm" "$svg"
  if [[ "$MODE" != "--refresh" ]]; then
    validate_figure_pdf \
      "$committed_figure" "$stem" "$stem-committed" "$title" "$height_mm" "$svg"
  fi
  pdftotext "$regenerated_a" "$PAIR_ROOT/$stem.generated.txt"
  sentinel="$(figure_sentinel "$stem")"
  if [[ "$MODE" != "--refresh" ]]; then
    pdftotext "$committed_figure" "$PAIR_ROOT/$stem.committed.txt"
  fi
  figure_text_paths=("$PAIR_ROOT/$stem.generated.txt")
  if [[ "$MODE" != "--refresh" ]]; then
    figure_text_paths+=("$PAIR_ROOT/$stem.committed.txt")
  fi
  for text_path in "${figure_text_paths[@]}"; do
    if ! grep -F -- "$sentinel" "$text_path" >/dev/null; then
      echo "$CHECK_NAME: figure text sentinel is absent: $stem" >&2
      exit 1
    fi
  done

  if [[ "$MODE" == "--cross-toolchain" ]]; then
    generated_color="$PAIR_ROOT/$stem.generated.color"
    committed_color="$PAIR_ROOT/$stem.committed.color"
    generated_gray="$PAIR_ROOT/$stem.generated.gray"
    committed_gray="$PAIR_ROOT/$stem.committed.gray"
    render_pdf_page_set "$regenerated_a" "$generated_color" "$stem-generated-color" color
    render_pdf_page_set "$committed_figure" "$committed_color" "$stem-committed-color" color
    render_pdf_page_set "$regenerated_a" "$generated_gray" "$stem-generated-gray" gray
    render_pdf_page_set "$committed_figure" "$committed_gray" "$stem-committed-gray" gray
    compare_render_sets \
      "$generated_color" "$committed_color" 1 "$stem-color" \
      "$PAIR_ROOT/$stem.color-comparison.tsv"
    compare_render_sets \
      "$generated_gray" "$committed_gray" 1 "$stem-gray" \
      "$PAIR_ROOT/$stem.gray-comparison.tsv"
  fi

  if [[ "$MODE" == "--exact" ]]; then
    if ! cmp -s "$regenerated_a" "$committed_figure"; then
      echo "$CHECK_NAME: committed PDF derivative is stale for SVG: $stem" >&2
      exit 1
    fi
  elif [[ "$MODE" == "--cross-toolchain" ]]; then
    if ! cmp -s "$PAIR_ROOT/$stem.generated.txt" "$PAIR_ROOT/$stem.committed.txt"; then
      echo "$CHECK_NAME: SVG/PDF figure text changed across toolchains: $stem" >&2
      exit 1
    fi
    grep -E '^(Pages|Page size|PDF version):' "$BUILD_ROOT/$stem-generated.info" \
      >"$PAIR_ROOT/$stem.generated.structure"
    grep -E '^(Pages|Page size|PDF version):' "$BUILD_ROOT/$stem-committed.info" \
      >"$PAIR_ROOT/$stem.committed.structure"
    if ! cmp -s "$PAIR_ROOT/$stem.generated.structure" "$PAIR_ROOT/$stem.committed.structure"; then
      echo "$CHECK_NAME: SVG/PDF figure structure changed across toolchains: $stem" >&2
      exit 1
    fi
  fi
  cp "$regenerated_a" "$REPORT_FIGURE_DIR/$stem.pdf"
done
chmod 0444 "$REPORT_FIGURE_DIR"/*.pdf
chmod 0555 "$REPORT_FIGURE_DIR"

build_report() {
  local run_name="$1"
  local run_dir="$BUILD_ROOT/$run_name"
  local run_home="$run_dir/home"
  local run_xdg_config="$run_dir/xdg-config"
  local run_xdg_cache="$run_dir/xdg-cache"
  local run_texmf_home="$run_dir/texmf-home"
  local run_texmf_config="$run_dir/texmf-config"
  local run_texmf_cache="$run_dir/texmf-cache"
  local run_texmf_var="$run_dir/texmf-var"
  local run_font_cache="$run_dir/font-cache"
  local run_font_config="$run_dir/fontconfig.conf"
  local run_empty_fonts="$run_dir/empty-fonts"
  local run_tmp="$run_dir/tmp"
  local pass_dir="$run_dir/passes"
  local entry_wrapper="$run_dir/$ENTRY_WRAPPER_NAME"
  local pass_number=1
  local previous_state=""
  local current_state=""
  local converged=0
  local run_format_search_path=""
  local run_format_query=""
  mkdir -p \
    "$run_dir" \
    "$run_home" \
    "$run_xdg_config/luaotfload" \
    "$run_xdg_cache" \
    "$run_texmf_home" \
    "$run_texmf_config" \
    "$run_texmf_cache" \
    "$run_texmf_var" \
    "$run_font_cache" \
    "$run_empty_fonts" \
    "$run_tmp" \
    "$pass_dir"
  python3 -I -S - "$entry_wrapper" "$SNAPSHOT_ROOT/$SOURCE" <<'PY'
from __future__ import annotations

import os
from pathlib import Path
import stat
import sys


def fail(detail: str) -> None:
    print(f"mathematical workflow PDF check: entry-wrapper capture {detail}", file=sys.stderr)
    raise SystemExit(1)


path = Path(sys.argv[1])
source_path = sys.argv[2]
if not path.is_absolute() or not source_path.startswith("/"):
    fail("received a non-absolute path")
if any(character in source_path for character in "{}\r\n"):
    fail("received a source path unsafe for a braced TeX input")

# The first explicit wrapper operation disables LuaTeX's default pdfTeX map after the selected format
# has loaded.  Format initialization and any engine-supplied pre-wrapper token source are outside
# this ordering claim.  The operation-specific callback rejects every later nonempty map-file
# lookup that reaches find_map_file on the tested TeX primitive or pdf.mapfile() routes before the
# engine reads a map file, independent of requested spelling.  LuaTeX 1.18
# defines start_file category 2 as a font-map coupling font names to resources.  That callback is
# deliberately only defense in depth, not operation-specific evidence.
wrapper = (
    "\\pdfextension mapfile {}\n"
    "\\directlua{\n"
    "  local pid_rs_error = error\n"
    "  local pid_rs_pairs = pairs\n"
    "  local pid_rs_tostring = tostring\n"
    '  local pid_rs_existing_find_map = luatexbase.callback_descriptions("find_map_file")\n'
    "  local pid_rs_prior_map_callback_count = 0\n"
    "  for _ in pid_rs_pairs(pid_rs_existing_find_map) do\n"
    "    pid_rs_prior_map_callback_count = pid_rs_prior_map_callback_count + 1\n"
    "  end\n"
    "  if pid_rs_prior_map_callback_count ~= 0 then\n"
    "    pid_rs_error(\n"
    '      "PID-RS-UNEXPECTED-PRIOR-MAP-CALLBACKS:"\n'
    "        .. pid_rs_tostring(pid_rs_prior_map_callback_count), 0)\n"
    "  end\n"
    "  local function pid_rs_deny_map_file(name)\n"
    '    pid_rs_error("PID-RS-MAP-FILE-DENIED:" .. pid_rs_tostring(name), 0)\n'
    "  end\n"
    "  local function pid_rs_deny_category_two_font_map_event(category, filename)\n"
    "    if category == 2 then\n"
    "      pid_rs_error(\n"
    '        "PID-RS-CATEGORY-TWO-FONT-MAP-EVENT-DENIED:"\n'
    "          .. pid_rs_tostring(filename), 0)\n"
    "    end\n"
    "  end\n"
    "  luatexbase.add_to_callback(\n"
    '    "find_map_file", pid_rs_deny_map_file,\n'
    '    "pid-rs deny font-map lookup")\n'
    "  luatexbase.add_to_callback(\n"
    '    "start_file", pid_rs_deny_category_two_font_map_event,\n'
    '    "pid-rs deny category-2 font-map events")\n'
    "}\n"
    "\\typeout{PID-RS-DEFAULT-PDFTEX-MAP=disabled-before-source}\n"
    f"\\input{{{source_path}}}\n"
).encode("utf-8")

for required_flag in ("O_NOFOLLOW", "O_CLOEXEC"):
    if not hasattr(os, required_flag):
        fail(f"platform lacks required {required_flag}")
flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
descriptor = os.open(path, flags, 0o600)
try:
    view = memoryview(wrapper)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            fail("write made no progress")
        view = view[written:]
    os.fsync(descriptor)
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        fail("destination is not a single-link regular file")
    os.lseek(descriptor, 0, os.SEEK_SET)
    observed = bytearray()
    while len(observed) < len(wrapper):
        block = os.read(descriptor, len(wrapper) - len(observed))
        if not block:
            fail("destination truncated during descriptor replay")
        observed.extend(block)
    if os.read(descriptor, 1) or bytes(observed) != wrapper:
        fail("destination differs from the exact constructed bytes")
    os.fchmod(descriptor, 0o444)
    after = os.fstat(descriptor)
    if not stat.S_ISREG(after.st_mode) or after.st_nlink != 1:
        fail("destination stopped being a single-link regular file")
    stable_fields = ("st_dev", "st_ino", "st_size")
    if tuple(getattr(before, field) for field in stable_fields) != tuple(
        getattr(after, field) for field in stable_fields
    ):
        fail("destination identity changed during capture")
    leaf = path.lstat()
    leaf_fields = ("st_dev", "st_ino", "st_size", "st_nlink")
    if tuple(getattr(leaf, field) for field in leaf_fields) != tuple(
        getattr(after, field) for field in leaf_fields
    ) or stat.S_IMODE(leaf.st_mode) != stat.S_IMODE(after.st_mode):
        fail("destination path identity differs from its descriptor")
    if stat.S_IMODE(after.st_mode) != 0o444 or len(wrapper) != after.st_size:
        fail("destination did not retain its exact captured read-only bytes")
finally:
    os.close(descriptor)
PY
  cat >"$run_xdg_config/luaotfload/luaotfload.conf" <<'EOF'
[db]
  update-live = false
  scan-local = false
  max-fonts = 64
  location-precedence = texmf
EOF
  cat >"$run_font_config" <<EOF
<?xml version="1.0"?>
<fontconfig>
  <dir>$FONT_ROOT</dir>
  <cachedir>$run_font_cache</cachedir>
  <config></config>
</fontconfig>
EOF
  local run_environment=(
    "HOME=$run_home"
    "TMPDIR=$run_tmp"
    "XDG_CONFIG_HOME=$run_xdg_config"
    "XDG_CACHE_HOME=$run_xdg_cache"
    "TEXMFHOME=$run_texmf_home"
    "TEXMFCONFIG=$run_texmf_config"
    "TEXMFVAR=$run_texmf_var"
    "TEXMFCACHE=$run_texmf_cache"
    "LUATEX_CACHEDIR=$run_texmf_cache"
    "TEXFORMATS=$FORMAT_ROOT"
    "FONTCONFIG_FILE=$run_font_config"
    "FONTCONFIG_PATH=$run_dir"
    "PANGOCAIRO_BACKEND=fc"
    "OSFONTDIR=$FONT_ROOT"
    "OPENTYPEFONTS=$FONT_ROOT"
    "TTFONTS=$run_empty_fonts"
    "T1FONTS=$run_empty_fonts"
    "AFMFONTS=$run_empty_fonts"
    "SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH_VALUE"
  )
  if ! run_format_search_path="$(env -i \
    "${CLEAN_BASE_ENV[@]}" \
    "${run_environment[@]}" \
    kpsewhich \
      --engine=luahbtex \
      --progname=lualatex \
      --show-path=fmt)"; then
    echo "$CHECK_NAME: private LuaLaTeX format search-path query failed in $run_name" >&2
    exit 2
  fi
  if ! run_format_query="$(env -i \
    "${CLEAN_BASE_ENV[@]}" \
    "${run_environment[@]}" \
    kpsewhich \
      --engine=luahbtex \
      --progname=lualatex \
      --must-exist \
      --format=fmt \
      lualatex.fmt)"; then
    echo "$CHECK_NAME: private LuaLaTeX format lookup failed in $run_name" >&2
    exit 2
  fi
  if [[ "$run_format_search_path" != "$FORMAT_ROOT" \
      || "$run_format_query" != "$FORMAT_PATH" ]]; then
    echo "$CHECK_NAME: private LuaLaTeX format lookup escaped its exact snapshot" >&2
    exit 1
  fi
  env -i "${CLEAN_BASE_ENV[@]}" "${run_environment[@]}" fc-cache -f >/dev/null
  if ! (
    cd "$run_dir"
    env -i \
      "${CLEAN_BASE_ENV[@]}" \
      "${run_environment[@]}" \
      luaotfload-tool \
        --update \
        --force \
        --prefer-texmf \
        --max-fonts=64 \
        -vv \
        --log=stdout
  ) >"$run_dir/luaotfload-tool.stdout" 2>&1; then
    cat "$run_dir/luaotfload-tool.stdout" >&2
    echo "$CHECK_NAME: bounded font database build failed in $run_name" >&2
    exit 1
  fi
  if ! grep -F -- 'Fonts in the database: 15' "$run_dir/luaotfload-tool.stdout" >/dev/null \
      || grep -F -- 'Scanning system fonts' "$run_dir/luaotfload-tool.stdout" >/dev/null; then
    cat "$run_dir/luaotfload-tool.stdout" >&2
    echo "$CHECK_NAME: bounded font database inventory drifted in $run_name" >&2
    exit 1
  fi
  while [[ "$pass_number" -le 6 ]]; do
    if ! verify_captured_format_exact \
      "$FORMAT_PATH" "$FORMAT_BYTES" "$FORMAT_SHA256"; then
      exit 1
    fi
    if ! (
      cd "$run_dir"
      env -i \
        "${CLEAN_BASE_ENV[@]}" \
        "${run_environment[@]}" \
        "TEXINPUTS=$SNAPSHOT_ROOT/audit/formal/latex:$REPORT_FIGURE_DIR:" \
        lualatex \
          -no-shell-escape \
          -recorder \
          -interaction=nonstopmode \
          -halt-on-error \
          -jobname="$REPORT_STEM" \
          -output-directory="$run_dir" \
          "$entry_wrapper"
    ) >"$pass_dir/pass-$pass_number.stdout" 2>&1; then
      cat "$pass_dir/pass-$pass_number.stdout" >&2
      echo "$CHECK_NAME: LuaLaTeX pass $pass_number failed in $run_name" >&2
      exit 1
    fi
    for artifact in "$REPORT_STEM.pdf" "$REPORT_STEM.log" "$REPORT_STEM.fls"; do
      if [[ ! -s "$run_dir/$artifact" ]]; then
        echo "$CHECK_NAME: $run_name pass $pass_number did not produce nonempty $artifact" >&2
        exit 1
      fi
    done
    cp "$run_dir/$REPORT_STEM.log" "$pass_dir/pass-$pass_number.log"
    cp "$run_dir/$REPORT_STEM.fls" "$pass_dir/pass-$pass_number.fls"
    if ! bash "$SNAPSHOT_ROOT/scripts/check-formal-pdf-log.sh" --intermediate \
        "$pass_dir/pass-$pass_number.log"; then
      echo "$CHECK_NAME: LaTeX pass $pass_number contains a non-convergence diagnostic in $run_name" >&2
      exit 1
    fi
    if ! grep -F -- 'This is LuaHBTeX' "$pass_dir/pass-$pass_number.log" >/dev/null \
        || ! grep -F -- 'PID-RS-SHELL-ESCAPE=disabled' \
          "$pass_dir/pass-$pass_number.log" >/dev/null; then
      echo "$CHECK_NAME: $run_name pass $pass_number lacks its engine/shell-escape sentinel" >&2
      exit 1
    fi
    if [[ "$(grep -Fxc -- 'PID-RS-DEFAULT-PDFTEX-MAP=disabled-before-source' \
        "$pass_dir/pass-$pass_number.log")" -ne 1 ]]; then
      echo "$CHECK_NAME: $run_name pass $pass_number lacks one exact pre-source map sentinel" >&2
      exit 1
    fi
    current_state="$(python3 -I -S - "$run_dir" "$REPORT_STEM" <<'PY'
from pathlib import Path
import hashlib
import sys


root = Path(sys.argv[1])
stem = sys.argv[2]
paths = [
    root / f"{stem}.aux",
    root / f"{stem}.markdown.in",
    root / f"{stem}.out",
    root / f"{stem}.pdf",
    root / f"{stem}.toc",
]
paths.extend(sorted((root / f"_markdown_{stem}").glob("*")))
digest = hashlib.sha256()
for path in paths:
    if not path.is_file():
        raise SystemExit(f"missing convergence artifact: {path}")
    relative = path.relative_to(root).as_posix().encode("utf-8")
    data = path.read_bytes()
    digest.update(len(relative).to_bytes(8, "big"))
    digest.update(relative)
    digest.update(len(data).to_bytes(8, "big"))
    digest.update(data)
print(digest.hexdigest())
PY
)"
    if [[ "$pass_number" -ge 2 && "$current_state" == "$previous_state" ]] \
        && bash "$SNAPSHOT_ROOT/scripts/check-formal-pdf-log.sh" \
          "$pass_dir/pass-$pass_number.log" \
          >"$pass_dir/pass-$pass_number.final-check.stdout" \
          2>"$pass_dir/pass-$pass_number.final-check.stderr"; then
      if [[ -s "$pass_dir/pass-$pass_number.final-check.stdout" \
          || -s "$pass_dir/pass-$pass_number.final-check.stderr" ]]; then
        echo "$CHECK_NAME: final log checker emitted output in $run_name" >&2
        exit 1
      fi
      converged=1
      break
    fi
    previous_state="$current_state"
    pass_number=$((pass_number + 1))
  done
  if [[ "$converged" -ne 1 ]]; then
    echo "$CHECK_NAME: $run_name did not reach warning-free bounded fixed-point convergence" >&2
    exit 1
  fi
  printf '%s\n' "$pass_number" >"$run_dir/pass-count.txt"
}

build_report "build-a"
build_report "build-b"
if ! verify_captured_format_exact \
  "$FORMAT_PATH" "$FORMAT_BYTES" "$FORMAT_SHA256"; then
  exit 1
fi

BUILT_A="$BUILD_ROOT/build-a/$REPORT_STEM.pdf"
BUILT_B="$BUILD_ROOT/build-b/$REPORT_STEM.pdf"
if ! cmp -s "$BUILD_ROOT/build-a/pass-count.txt" "$BUILD_ROOT/build-b/pass-count.txt"; then
  echo "$CHECK_NAME: isolated builds reached fixed-point convergence on different passes" >&2
  exit 1
fi
if ! cmp -s "$BUILT_A" "$BUILT_B"; then
  echo "$CHECK_NAME: two isolated same-toolchain builds are not byte-identical" >&2
  exit 1
fi

python3 -I -S - \
  "$BUILD_ROOT/build-a" \
  "$BUILD_ROOT/build-b" \
  "$ROOT" \
  "$SNAPSHOT_ROOT" \
  "$TEXMFROOT_ROOT" \
  "$FONT_ROOT" \
  "$FORMAT_PATH" \
  "$FORMAT_BYTES" \
  "$FORMAT_SHA256" \
  "$SNAPSHOT_ROOT/$SOURCE" \
  "$SNAPSHOT_ROOT/$SHARED_STYLE" \
  "$SNAPSHOT_ROOT/$PUBLICATION_STYLE" \
  "$REPORT_FIGURE_DIR" \
  "$BUILD_ROOT/fls-closures" \
  "$ENTRY_WRAPPER_NAME" \
  "${FIGURE_STEMS[@]}" <<'PY'
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import sys


def fail(detail: str) -> None:
    print(f"mathematical workflow PDF check: {detail}", file=sys.stderr)
    raise SystemExit(1)


run_directories = [Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()]
repository_root = Path(sys.argv[3]).resolve()
snapshot_root = Path(sys.argv[4]).resolve()
texmf_root = Path(sys.argv[5]).resolve()
font_root = Path(sys.argv[6]).resolve()
format_path = Path(sys.argv[7]).resolve()
format_bytes_raw = sys.argv[8]
format_sha256 = sys.argv[9]
source_path = Path(sys.argv[10]).resolve()
shared_style = Path(sys.argv[11]).resolve()
publication_style = Path(sys.argv[12]).resolve()
figure_dir = Path(sys.argv[13]).resolve()
closure_root = Path(sys.argv[14])
entry_wrapper_name = sys.argv[15]
stems = sys.argv[16:]
if not format_bytes_raw.isdigit() or int(format_bytes_raw) < 1:
    fail("captured format size receipt is invalid")
format_bytes = int(format_bytes_raw)
if len(format_sha256) != 64 or any(
    character not in "0123456789abcdef" for character in format_sha256
):
    fail("captured format digest receipt is invalid")
if format_path.name != "lualatex.fmt":
    fail("captured format path is not the exact expected leaf")
closure_root.mkdir(parents=True, exist_ok=False)


def beneath(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def is_forbidden_tex_map_path(path: Path) -> bool:
    """Recognize only recorder input paths that are unambiguously map-shaped."""
    if path.name.casefold().endswith(".map"):
        return True
    folded_parts = tuple(part.casefold() for part in path.parts)
    return any(
        folded_parts[index : index + 2] == ("fonts", "map")
        for index in range(len(folded_parts) - 1)
    )


def capture_regular(path: Path) -> tuple[int, str]:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            fail(f"FLS input is not a regular file: {path}")
        if before.st_size > 64 * 1024 * 1024:
            fail(f"FLS input exceeds the per-file capture bound: {path}")
        digest = hashlib.sha256()
        remaining = before.st_size
        while remaining:
            block = os.read(descriptor, min(remaining, 1024 * 1024))
            if not block:
                fail(f"FLS input truncated during capture: {path}")
            digest.update(block)
            remaining -= len(block)
        if os.read(descriptor, 1):
            fail(f"FLS input grew during capture: {path}")
        after = os.fstat(descriptor)
        fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
        if tuple(getattr(before, name) for name in fields) != tuple(
            getattr(after, name) for name in fields
        ):
            fail(f"FLS input changed during capture: {path}")
        return before.st_size, digest.hexdigest()
    finally:
        os.close(descriptor)


external_identities: dict[Path, tuple[int, str]] = {}
for run_dir in run_directories:
    pass_count_raw = (run_dir / "pass-count.txt").read_text(encoding="ascii").strip()
    if not pass_count_raw.isdigit() or not 2 <= int(pass_count_raw) <= 6:
        fail(f"{run_dir.name} has an invalid bounded pass count")
    pass_count = int(pass_count_raw)
    pass_dir = run_dir / "passes"
    expected_fls = {pass_dir / f"pass-{number}.fls" for number in range(1, pass_count + 1)}
    observed_fls = set(pass_dir.glob("pass-*.fls"))
    if observed_fls != expected_fls:
        fail(f"{run_dir.name} preserved FLS inventory drifted")
    for pass_number in range(1, pass_count + 1):
        fls_path = pass_dir / f"pass-{pass_number}.fls"
        lines = fls_path.read_text(encoding="utf-8").splitlines()
        working_directories = [line[4:] for line in lines if line.startswith("PWD ")]
        if working_directories != [str(run_dir)]:
            fail(f"{run_dir.name} pass {pass_number} recorded an unexpected working directory")
        inputs = [line[6:] for line in lines if line.startswith("INPUT ")]
        outputs = [line[7:] for line in lines if line.startswith("OUTPUT ")]
        raw_input_paths = [
            Path(raw) if Path(raw).is_absolute() else run_dir / raw for raw in inputs
        ]
        raw_format_inputs = {
            path for path in raw_input_paths if path.name.casefold().endswith(".fmt")
        }
        if raw_format_inputs != {format_path}:
            fail(
                f"{run_dir.name} pass {pass_number} recorded a format outside its exact raw path"
            )
        for path in raw_input_paths:
            if is_forbidden_tex_map_path(path):
                fail(
                    f"{run_dir.name} pass {pass_number} loaded a forbidden raw "
                    f"TeX map-path input: {path}"
                )
        resolved_inputs = {path.resolve() for path in raw_input_paths}
        resolved_format_inputs = {
            path for path in resolved_inputs if path.name.casefold().endswith(".fmt")
        }
        if resolved_format_inputs != {format_path}:
            fail(
                f"{run_dir.name} pass {pass_number} loaded a format outside its exact resolved path"
            )
        for path in resolved_inputs:
            if is_forbidden_tex_map_path(path):
                fail(
                    f"{run_dir.name} pass {pass_number} loaded a forbidden resolved "
                    f"TeX map-path input: {path}"
                )
        expected_entry_wrapper = (run_dir / entry_wrapper_name).resolve()
        expected_inputs = {
            source_path,
            shared_style,
            publication_style,
            expected_entry_wrapper,
            format_path,
        }
        expected_inputs.update((figure_dir / f"{stem}.pdf").resolve() for stem in stems)
        missing = expected_inputs - resolved_inputs
        if missing:
            fail(
                f"{run_dir.name} pass {pass_number} omitted snapshotted inputs: "
                f"{sorted(map(str, missing))}"
            )
        matching_wrappers = {
            path for path in resolved_inputs if path.name == entry_wrapper_name
        }
        if matching_wrappers != {expected_entry_wrapper}:
            fail(
                f"{run_dir.name} pass {pass_number} loaded the entry wrapper from an "
                "undeclared path"
            )
        for stem in stems:
            matching = {path for path in resolved_inputs if path.name == f"{stem}.pdf"}
            expected = {(figure_dir / f"{stem}.pdf").resolve()}
            if matching != expected:
                fail(f"{run_dir.name} pass {pass_number} loaded figure from an undeclared path: {stem}")
            if any(path.name == f"{stem}.svg" for path in resolved_inputs):
                fail(f"{run_dir.name} pass {pass_number} loaded SVG instead of its exact PDF: {stem}")
        for path in resolved_inputs:
            if beneath(path, repository_root):
                fail(f"{run_dir.name} pass {pass_number} bypassed the source snapshot: {path}")
            if path == format_path:
                continue
            if not any(
                beneath(path, allowed)
                for allowed in (
                    snapshot_root,
                    run_dir,
                    texmf_root,
                    font_root,
                    figure_dir,
                )
            ):
                fail(f"{run_dir.name} pass {pass_number} loaded an ambient input: {path}")
        resolved_outputs = {
            (Path(raw) if Path(raw).is_absolute() else run_dir / raw).resolve()
            for raw in outputs
        }
        escaped_outputs = [path for path in resolved_outputs if not beneath(path, run_dir)]
        if escaped_outputs:
            fail(f"{run_dir.name} pass {pass_number} wrote outside its run root: {escaped_outputs[0]}")
        expected_pdf = (run_dir / "mathematical-problem-solving-workflow.pdf").resolve()
        if expected_pdf not in resolved_outputs:
            fail(f"{run_dir.name} pass {pass_number} did not record the report PDF output")

        closure_rows = ["schema\tpid-rs-workflow-fls-input-closure-v1\n"]
        aggregate_size = 0
        for path in sorted(resolved_inputs, key=str):
            size, digest = capture_regular(path)
            if path == format_path and (size, digest) != (format_bytes, format_sha256):
                fail(
                    f"{run_dir.name} pass {pass_number} captured format receipt drifted"
                )
            aggregate_size += size
            if aggregate_size > 256 * 1024 * 1024:
                fail(f"{run_dir.name} pass {pass_number} FLS closure exceeds 256 MiB")
            if not beneath(path, run_dir):
                identity = (size, digest)
                if path in external_identities and external_identities[path] != identity:
                    fail(f"external FLS input changed between retained passes: {path}")
                external_identities[path] = identity
            closure_rows.append(f"{path}\t{size}\t{digest}\n")
        (closure_root / f"{run_dir.name}-pass-{pass_number}.tsv").write_text(
            "".join(closure_rows), encoding="utf-8", newline="\n"
        )
PY

pdftotext -layout "$BUILT_A" "$BUILD_ROOT/built.txt"
required_text=(
  'Mathematical Problem-Solving Workflow'
  'Keep the scientific objects distinct'
  'Accepted routes, AND prerequisites, and all minimal cuts'
  'All inclusion-minimal cuts: {C}; {A1, B1}; {A2, B1}'
  'Five routes may still be one route semantically'
  'Prerequisites point toward dependents; invalidation follows the arrows'
  'normative_prompt:'
  'PID/PGID or explicit unavailable'
  'three-turn blocked audit'
  'Orient every dependency-bearing edge from prerequisite to dependent'
  'Lenses 1–10: scientific object and inference contract'
  'Lenses 11–20: evidence, custody, implementation, and release contract'
  'Named source arrow (domain -> codomain):'
  '0 -> 0 -> C2 --id--> C2 -> 0'
  'G=A+E'
  'Ahat=P+Q'
  '0.672500703679...'
  'M1-M9-incomplete=>abstain'
)
for sentinel in "${required_text[@]}"; do
  if ! grep -F -- "$sentinel" "$BUILD_ROOT/built.txt" >/dev/null; then
    echo "$CHECK_NAME: rendered-text sentinel is absent: $sentinel" >&2
    exit 1
  fi
done
if grep -F -- '??' "$BUILD_ROOT/built.txt" >/dev/null; then
  echo "$CHECK_NAME: rendered text contains an unresolved reference marker" >&2
  exit 1
fi
REPLACEMENT_CHARACTER="$(printf '\357\277\275')"
if grep -F -- "$REPLACEMENT_CHARACTER" "$BUILD_ROOT/built.txt" >/dev/null; then
  echo "$CHECK_NAME: rendered text contains a Unicode replacement character" >&2
  exit 1
fi
python3 -I -S - "$BUILD_ROOT/built.txt" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
if "\N{INVERTED QUESTION MARK}" in text or "\N{INVERTED EXCLAMATION MARK}" in text:
    raise SystemExit("mathematical workflow PDF check: rendered code contains an inverted angle-bracket glyph")

normalized = " ".join(text.split())
for expected in (
    "rendered as the literal text “no accepted evidence”",
    "Python with optimization enabled (the -O option)",
    "the three-component vector (functional/mechanism, epistemic/dependency, institutional/custody)",
    "the displayed Z/2 exact-sequence witness above as the minimal human-readable regression",
):
    if expected not in normalized:
        raise SystemExit(
            "mathematical workflow PDF check: rendered text loses required interword semantics: "
            + expected
        )
PY

validate_report_pdf() {
  local pdf="$1"
  local label="$2"
  local info="$BUILD_ROOT/$label.info"
  LC_ALL=C pdfinfo "$pdf" >"$info"
  for predicate in \
    "^Pages:[[:space:]]+$EXPECTED_PAGES$" \
    '^Page size:[[:space:]]+595\.276 x 841\.89 pts \(A4\)$' \
    '^Page rot:[[:space:]]+0$' \
    '^Encrypted:[[:space:]]+no$' \
    '^Tagged:[[:space:]]+no$' \
    '^Form:[[:space:]]+none$' \
    '^JavaScript:[[:space:]]+no$' \
    '^PDF version:[[:space:]]+1\.7$'; do
    if ! grep -Eq "$predicate" "$info"; then
      echo "$CHECK_NAME: $label violates report PDF predicate: $predicate" >&2
      grep -E \
        '^(Pages|Page size|Page rot|Encrypted|Tagged|Form|JavaScript|PDF version):' \
        "$info" >&2 || true
      exit 1
    fi
  done
  validate_font_table "$pdf" "$label"
  python3 -I -S - \
    "$pdf" \
    "$SNAPSHOT_ROOT/$MARKDOWN" \
    "$EXPECTED_PAGES" \
    "$MODE" \
    "$BUILD_ROOT/$label.navigation.tsv" <<'PY'
from collections import Counter
import hashlib
from pathlib import Path
import re
import sys
import sysconfig
import unicodedata

for package_root in dict.fromkeys((sysconfig.get_path("purelib"), sysconfig.get_path("platlib"))):
    if package_root:
        sys.path.insert(0, package_root)

from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NullObject, TextStringObject

APPROVED_UNAUTHENTICATED_HTTP_URIS = {
    "http://www.bdim.eu/item?id=RLIN_2000_9_11_3_183_0&fmt=pdf",
}


def fail(detail: str) -> None:
    print(f"mathematical workflow PDF check: report PDF {detail}", file=sys.stderr)
    raise SystemExit(1)


def resolve(value):
    return value.get_object() if isinstance(value, IndirectObject) else value


def validate_action(action, location: str) -> tuple[str, object]:
    action = resolve(action)
    if not isinstance(action, DictionaryObject):
        fail(f"{location} action is not a dictionary")
    if action.get("/Next") is not None:
        fail(f"{location} action contains a chained /Next action")
    action_type = str(action.get("/S"))
    if action_type == "/URI":
        uri = str(action.get("/URI"))
        # One reviewed predecessor was obtainable only from an unauthenticated HTTP transport.
        # Admit that exact, visibly disclosed URI while retaining the default HTTPS-only policy.
        if not uri.startswith("https://") and uri not in APPROVED_UNAUTHENTICATED_HTTP_URIS:
            fail(f"{location} has an unapproved non-HTTPS URI action: {uri}")
        return "URI", uri
    elif action_type == "/GoTo":
        destination = action.get("/D")
        if destination is None:
            fail(f"{location} internal GoTo action lacks a destination")
        return "GoTo", destination
    else:
        fail(f"{location} has a forbidden action type: {action_type}")


pdf_path = Path(sys.argv[1])
markdown_path = Path(sys.argv[2])
expected_pages = int(sys.argv[3])
validation_mode = sys.argv[4]
navigation_manifest_path = Path(sys.argv[5])
if validation_mode not in {"--exact", "--cross-toolchain", "--refresh"}:
    fail(f"received an invalid validation mode: {validation_mode!r}")
reader = PdfReader(pdf_path, strict=True)
root = resolve(reader.trailer["/Root"])
if reader.pdf_header != "%PDF-1.7":
    fail("header is not PDF 1.7")
if str(root.get("/Lang")) != "en":
    fail("catalog /Lang is not en")
mark_info = resolve(root.get("/MarkInfo", DictionaryObject()))
if bool(mark_info.get("/Marked", False)) or root.get("/StructTreeRoot") is not None:
    fail("claims tagged structure although this publication is explicitly untagged")
if root.get("/AcroForm") is not None:
    fail("contains an AcroForm")
for forbidden_key in ("/OpenAction", "/AA", "/AF", "/Collection"):
    if root.get(forbidden_key) is not None:
        fail(f"catalog contains forbidden active/associated content: {forbidden_key}")
if root.get("/Dests") is not None:
    fail("catalog contains a competing legacy /Dests dictionary")
names = resolve(root.get("/Names", DictionaryObject()))
unexpected_name_trees = set(names) - {"/Dests"}
if unexpected_name_trees:
    fail(f"catalog contains an unapproved name tree: {sorted(map(str, unexpected_name_trees))}")
metadata = reader.metadata
expected_metadata = {
    "/Title": "Mathematical Problem-Solving Workflow for pid-rs",
    "/Subject": "Claim discipline, adversarial proof development, certificates, and layered assurance",
    "/Keywords": "partial information decomposition, proof workflow, formal verification, certified numerics, adversarial audit",
    "/Author": "pid-rs contributors",
    "/Creator": "pid-rs deterministic publication pipeline",
    "/Producer": "LuaLaTeX",
}
for key, expected in expected_metadata.items():
    if metadata.get(key) != expected:
        fail(f"metadata {key} differs: {metadata.get(key)!r}")

if len(reader.pages) != expected_pages:
    fail(f"page count differs: {len(reader.pages)}")
page_text_normalized = [
    "".join(
        character
        for character in unicodedata.normalize("NFKC", page.extract_text() or "").casefold()
        if character.isalnum()
    )
    for page in reader.pages
]


def normalized_heading(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKC", value).casefold()
        if character.isalnum()
    )


outline_rows: list[tuple[int, str, int]] = []


def walk_outline(items, depth: int = 0) -> None:
    for item in items:
        if isinstance(item, list):
            walk_outline(item, depth + 1)
            continue
        title = str(getattr(item, "title", ""))
        page_index = reader.get_destination_page_number(item)
        if not title or page_index is None or not 0 <= page_index < expected_pages:
            fail(f"outline item has an invalid title or destination: {title!r}, {page_index!r}")
        title_without_number = re.sub(r"^\s*\d+(?:\.\d+)*\s+", "", title)
        normalized_title = normalized_heading(title_without_number)
        if not normalized_title or normalized_title not in page_text_normalized[page_index]:
            fail(
                "outline destination page does not contain its heading: "
                f"{title!r} -> page {page_index + 1}"
            )
        outline_rows.append((depth, title, page_index))


walk_outline(reader.outline)
if len(outline_rows) != 74:
    fail(f"outline item inventory drifted: {len(outline_rows)}")
outline_manifest = "".join(
    f"{depth}\t{title}\t{page_index + 1}\n"
    for depth, title, page_index in outline_rows
).encode("utf-8")
outline_manifest_digest = hashlib.sha256(outline_manifest).hexdigest()
if outline_manifest_digest != "ba9955ea747694eab4a11985fa43f180fafada843813492aa97ea9216e46fd7d":
    fail(f"outline title/depth/target manifest drifted: {outline_manifest_digest}")
if len(reader.named_destinations) != 185:
    fail(f"named-destination inventory drifted: {len(reader.named_destinations)}")

raw_destination_root = names.get("/Dests")
if raw_destination_root is None:
    fail("catalog lacks its raw destination name tree")
seen_name_tree_indirect: set[tuple[int, int]] = set()
seen_name_tree_direct: set[int] = set()
name_tree_node_count = 0


def raw_destination_name(value, location: str) -> str:
    value = resolve(value)
    if not isinstance(value, TextStringObject):
        fail(f"raw destination name is not a text string at {location}")
    name = str(value)
    if re.fullmatch(r"[!-~]+", name) is None:
        fail(f"raw destination name is outside the admitted ASCII spelling at {location}")
    return name


def walk_destination_name_tree(value, location: str, depth: int = 0):
    global name_tree_node_count
    if depth > 32:
        fail("raw destination name tree exceeds depth 32")
    if isinstance(value, IndirectObject):
        identity = (value.idnum, value.generation)
        if identity in seen_name_tree_indirect:
            fail(f"raw destination name tree contains a cycle or shared node at {location}")
        seen_name_tree_indirect.add(identity)
        value = value.get_object()
    else:
        identity = id(value)
        if identity in seen_name_tree_direct:
            fail(f"raw destination name tree contains a cycle or shared node at {location}")
        seen_name_tree_direct.add(identity)
    name_tree_node_count += 1
    if name_tree_node_count > 1024:
        fail("raw destination name tree exceeds 1024 nodes")
    if not isinstance(value, DictionaryObject):
        fail(f"raw destination name-tree node is not a dictionary at {location}")
    keys = set(map(str, value.keys()))
    has_names = "/Names" in keys
    has_kids = "/Kids" in keys
    if has_names == has_kids or keys != ({"/Names", "/Limits"} if has_names else {"/Kids", "/Limits"}):
        fail(f"raw destination name-tree node has a noncanonical shape at {location}: {sorted(keys)}")
    limits = resolve(value.get("/Limits"))
    if not isinstance(limits, ArrayObject) or len(limits) != 2:
        fail(f"raw destination name-tree limits are malformed at {location}")
    if has_names:
        pairs = resolve(value.get("/Names"))
        if not isinstance(pairs, ArrayObject) or not pairs or len(pairs) % 2:
            fail(f"raw destination name-tree leaf pairs are malformed at {location}")
        entries = [
            (raw_destination_name(pairs[index], f"{location}/Names[{index}]"), pairs[index + 1])
            for index in range(0, len(pairs), 2)
        ]
        leaf_names = [name for name, _destination in entries]
        if any(left >= right for left, right in zip(leaf_names, leaf_names[1:])):
            fail(f"raw destination name-tree keys are not strictly increasing at {location}")
    else:
        kids = resolve(value.get("/Kids"))
        if not isinstance(kids, ArrayObject) or not kids:
            fail(f"raw destination name-tree kids are malformed at {location}")
        entries = []
        child_ranges: list[tuple[str, str]] = []
        for index, child in enumerate(kids):
            child_first, child_last, child_entries = walk_destination_name_tree(
                child,
                f"{location}/Kids[{index}]",
                depth + 1,
            )
            child_ranges.append((child_first, child_last))
            entries.extend(child_entries)
        if any(
            left_last >= right_first
            for (_left_first, left_last), (right_first, _right_last)
            in zip(child_ranges, child_ranges[1:])
        ):
            fail(f"raw destination name-tree child ranges overlap or are unordered at {location}")
    first_name = entries[0][0]
    last_name = entries[-1][0]
    observed_limits = (
        raw_destination_name(limits[0], f"{location}/Limits[0]"),
        raw_destination_name(limits[1], f"{location}/Limits[1]"),
    )
    if observed_limits != (first_name, last_name):
        fail(f"raw destination name-tree limits drifted at {location}: {observed_limits!r}")
    return first_name, last_name, entries


_raw_first, _raw_last, raw_destination_entries = walk_destination_name_tree(
    raw_destination_root,
    "catalog/Names/Dests",
)
raw_destination_names = [name for name, _destination in raw_destination_entries]
logical_destination_names = sorted(map(str, reader.named_destinations))
if len(raw_destination_names) != 185 or raw_destination_names != logical_destination_names:
    fail("raw destination name-tree inventory differs from the logical destination inventory")


def destination_scalar(value) -> str:
    return "null" if value is None or isinstance(value, NullObject) else str(value)


named_destination_route_rows: list[str] = []
named_destination_rows: list[str] = []
for destination_name, destination in sorted(reader.named_destinations.items()):
    page_index = reader.get_destination_page_number(destination)
    if page_index is None or not 0 <= page_index < expected_pages:
        fail(f"named destination has an invalid page: {destination_name!r}: {page_index!r}")
    if str(destination.typ) != "/XYZ":
        fail(f"named destination is not an XYZ target: {destination_name!r}")
    if (
        destination.left is None
        or destination.top is None
        or isinstance(destination.left, NullObject)
        or isinstance(destination.top, NullObject)
    ):
        fail(f"named destination lacks explicit coordinates: {destination_name!r}")
    left = float(destination.left)
    top = float(destination.top)
    page = reader.pages[page_index]
    if not 0 <= left <= float(page.mediabox.width) or not 0 <= top <= float(page.mediabox.height):
        fail(f"named destination lies outside its page: {destination_name!r}")
    if not all(
        value is None or isinstance(value, NullObject)
        for value in (destination.right, destination.bottom, destination.zoom)
    ):
        fail(f"named destination has an unexpected XYZ extent or zoom: {destination_name!r}")
    if destination_name.startswith("page."):
        page_suffix = destination_name.removeprefix("page.")
        if not page_suffix.isdigit() or int(page_suffix) != page_index + 1:
            fail(f"physical-page destination is misbound: {destination_name!r}")
    named_destination_route_rows.append(
        f"{destination_name}\t{page_index + 1}\t{destination.typ}\n"
    )
    named_destination_rows.append(
        "\t".join(
            (
                destination_name,
                str(page_index + 1),
                str(destination.typ),
                destination_scalar(destination.left),
                destination_scalar(destination.top),
                destination_scalar(destination.right),
                destination_scalar(destination.bottom),
                destination_scalar(destination.zoom),
            )
        )
        + "\n"
    )
named_destination_route_digest = hashlib.sha256(
    "".join(named_destination_route_rows).encode("utf-8")
).hexdigest()
if named_destination_route_digest != "412fdd7fbd6e55e661336d1c4f9b6dfa3179ea1347ae02b04705a39415cf6fea":
    fail(f"named-destination name/page/type manifest drifted: {named_destination_route_digest}")
if validation_mode in {"--exact", "--refresh"}:
    named_destination_digest = hashlib.sha256(
        "".join(named_destination_rows).encode("utf-8")
    ).hexdigest()
    if named_destination_digest != "c3be5be42104ffab51a48d23dbdf80f5659616da99130795e383cd15dd186d5f":
        fail(f"exact named-destination manifest drifted: {named_destination_digest}")
outline_pages = {
    normalized_heading(re.sub(r"^\s*\d+(?:\.\d+)*\s+", "", title)): page_index
    for _depth, title, page_index in outline_rows
}
section_two = normalized_heading("Typed assurance and rigorous evidence aggregation")
section_two_status = normalized_heading("Status of this supplement")
if outline_pages.get(section_two) != outline_pages.get(section_two_status):
    fail("section 2 heading is orphaned from its first subsection")
observed_uris: Counter[str] = Counter()
observed_goto_destinations: list[tuple[str, object]] = []
annotation_rows: list[str] = []
forbidden_annotation_subtypes = {
    "/3D",
    "/FileAttachment",
    "/Movie",
    "/RichMedia",
    "/Screen",
    "/Sound",
}
for page_number, page in enumerate(reader.pages, start=1):
    media_coordinates = tuple(map(float, page.mediabox))
    if len(media_coordinates) != 4:
        fail(f"page {page_number} has a malformed MediaBox")
    media_x_min, media_y_min, media_x_max, media_y_max = media_coordinates
    width = media_x_max - media_x_min
    height = media_y_max - media_y_min
    if abs(width - 595.276) > 0.02 or abs(height - 841.89) > 0.02:
        fail(f"page {page_number} is not exact A4 geometry: {width} x {height}")
    if abs(media_x_min) > 1e-9 or abs(media_y_min) > 1e-9:
        fail(f"page {page_number} MediaBox origin differs from zero")
    if (page.get("/Rotate") or 0) != 0:
        fail(f"page {page_number} is rotated")
    for box_name, box in (
        ("CropBox", page.cropbox),
        ("BleedBox", page.bleedbox),
        ("TrimBox", page.trimbox),
        ("ArtBox", page.artbox),
    ):
        if tuple(map(float, box)) != media_coordinates:
            fail(f"page {page_number} {box_name} differs from its MediaBox")
    try:
        user_unit = float(page.get("/UserUnit", 1))
    except (TypeError, ValueError):
        fail(f"page {page_number} has a malformed UserUnit")
    if not user_unit == 1.0:
        fail(f"page {page_number} UserUnit differs from 1")
    if len((page.extract_text() or "").strip()) < 20:
        fail(f"page {page_number} has implausibly little extractable text")
    if page.get("/AA") is not None or page.get("/AF") is not None:
        fail(f"page {page_number} has additional actions or associated files")
    annots = resolve(page.get("/Annots", ArrayObject()))
    for annotation_number, annotation_ref in enumerate(annots, start=1):
        annotation = resolve(annotation_ref)
        subtype = str(annotation.get("/Subtype"))
        if subtype in forbidden_annotation_subtypes or subtype != "/Link":
            fail(f"page {page_number} has a forbidden annotation subtype: {subtype}")
        if annotation.get("/AA") is not None:
            fail(f"page {page_number} annotation has additional actions")
        if annotation.get("/QuadPoints") is not None:
            fail(f"page {page_number} link has unreviewed QuadPoints geometry")
        try:
            annotation_flags = int(annotation.get("/F", 0))
        except (TypeError, ValueError):
            fail(f"page {page_number} link has malformed annotation flags")
        if annotation_flags != 0:
            fail(f"page {page_number} link has noncanonical annotation flags: {annotation_flags}")
        for forbidden_key in ("/AF", "/FS", "/RichMediaContent", "/RichMediaSettings"):
            if annotation.get(forbidden_key) is not None:
                fail(f"page {page_number} link contains forbidden content: {forbidden_key}")
        action = annotation.get("/A")
        destination = annotation.get("/Dest")
        if action is not None and destination is not None:
            fail(f"page {page_number} link has both an action and a direct destination")
        if action is not None:
            action_kind, action_target = validate_action(action, f"page {page_number} link")
            if action_kind == "URI":
                observed_uris[str(action_target)] += 1
            else:
                observed_goto_destinations.append(
                    (f"page {page_number} link", action_target)
                )
        elif destination is None:
            fail(f"page {page_number} link has neither an action nor a destination")
        else:
            action_kind, action_target = "GoTo", destination
            observed_goto_destinations.append((f"page {page_number} direct link", destination))
        rectangle = resolve(annotation.get("/Rect", ArrayObject()))
        if not isinstance(rectangle, ArrayObject) or len(rectangle) != 4:
            fail(f"page {page_number} link has a malformed rectangle")
        x_min, y_min, x_max, y_max = map(float, rectangle)
        if not (
            0 <= x_min <= x_max <= width
            and 0 <= y_min <= y_max <= height
        ):
            fail(f"page {page_number} link rectangle lies outside its page")
        if x_max - x_min < 1.0 or y_max - y_min < 1.0:
            fail(f"page {page_number} link rectangle has a zero or sub-point extent")
        annotation_rows.append(
            "\t".join(
                (
                    "annotation",
                    str(page_number),
                    str(annotation_number),
                    action_kind,
                    str(resolve(action_target)),
                    *(format(value, ".12g") for value in (x_min, y_min, x_max, y_max)),
                    str(annotation_flags),
                )
            )
            + "\n"
        )

seen_indirect: set[tuple[int, int, bool]] = set()
seen_direct: set[tuple[int, bool]] = set()
forbidden_dictionary_keys = {
    "/AA",
    "/AF",
    "/Collection",
    "/EF",
    "/EmbeddedFiles",
    "/JavaScript",
    "/JS",
    "/OpenAction",
    "/PresSteps",
    "/RichMediaContent",
    "/RichMediaSettings",
    "/XFA",
}
standard_action_types = {
    "/GoTo",
    "/GoTo3DView",
    "/GoToE",
    "/GoToR",
    "/Hide",
    "/ImportData",
    "/JavaScript",
    "/Launch",
    "/Movie",
    "/Named",
    "/Rendition",
    "/ResetForm",
    "/SetOCGState",
    "/Sound",
    "/SubmitForm",
    "/Thread",
    "/Trans",
    "/URI",
}


def walk_reachable(value, location: str, authorized_action: bool = False) -> None:
    if isinstance(value, IndirectObject):
        identity = (value.idnum, value.generation, authorized_action)
        if identity in seen_indirect:
            return
        seen_indirect.add(identity)
        value = value.get_object()
    else:
        identity = (id(value), authorized_action)
        if identity in seen_direct:
            return
        seen_direct.add(identity)
    if isinstance(value, DictionaryObject):
        object_type = str(value.get("/Type"))
        subtype = str(value.get("/Subtype"))
        action_type = str(value.get("/S"))
        declares_action = object_type == "/Action" or action_type in standard_action_types
        if declares_action and not authorized_action:
            fail(f"reachable object contains an action outside an authorized /A edge at {location}")
        if object_type == "/Filespec" or subtype in forbidden_annotation_subtypes:
            fail(f"reachable object contains a file specification or active subtype at {location}")
        present = forbidden_dictionary_keys.intersection(map(str, value.keys()))
        if present:
            fail(f"reachable object contains forbidden active keys at {location}: {sorted(present)}")
        for key, child in value.items():
            if str(key) == "/A":
                validate_action(child, f"reachable {location}/A")
                walk_reachable(child, f"{location}/{key}", authorized_action=True)
            else:
                walk_reachable(child, f"{location}/{key}")
    elif isinstance(value, (ArrayObject, list, tuple)):
        for index, child in enumerate(value):
            walk_reachable(child, f"{location}[{index}]")


walk_reachable(reader.trailer["/Root"], "catalog")

named_destination_names = set(reader.named_destinations)
for location, raw_destination in observed_goto_destinations:
    destination = resolve(raw_destination)
    if not isinstance(destination, str):
        fail(f"{location} uses a non-named internal destination")
    if destination not in named_destination_names:
        fail(f"{location} refers to an absent named destination: {destination!r}")

markdown = markdown_path.read_text(encoding="utf-8")
expected_uris: Counter[str] = Counter(re.findall(r"\]\((https?://[^)]+)\)", markdown))
# Hyperref emits one link annotation per line fragment, so a single source link can legitimately
# produce multiple same-URI rectangles when its label wraps. For each URI value, require the
# rendered-fragment count to be no smaller than its source-occurrence count, and forbid every URI
# absent from the source. This aggregate comparison does not pair repeated identical source links
# one-to-one. Exact fragment multiplicity, page/order, rectangles, and flags remain bound by the
# navigation manifest below.
missing_occurrences = sorted((expected_uris - observed_uris).items())
unknown_uris = sorted(set(observed_uris) - set(expected_uris))
if missing_occurrences or unknown_uris:
    fail(
        "URL annotation/source binding differs; "
        f"missing_source_occurrences={missing_occurrences!r}, "
        f"unknown_rendered_uris={unknown_uris!r}"
    )

navigation_rows = ["schema\tpid-rs-workflow-navigation-manifest-v1\n"]
for depth, title, page_index in outline_rows:
    if "\t" in title or "\n" in title:
        fail("outline title is not TSV-safe")
    navigation_rows.append(f"outline\t{depth}\t{page_index + 1}\t{title}\n")
for row in named_destination_rows:
    navigation_rows.append("destination\t" + row)
navigation_rows.extend(annotation_rows)
navigation_manifest_path.write_text(
    "".join(navigation_rows),
    encoding="utf-8",
    newline="\n",
)
PY
}

validate_report_pdf "$BUILT_A" "built-a"
validate_report_pdf "$BUILT_B" "built-b"
if [[ "$MODE" != "--refresh" ]]; then
  validate_report_pdf "$SNAPSHOT_ROOT/$COMMITTED" "committed"
fi
if ! cmp -s "$BUILD_ROOT/built-a.navigation.tsv" "$BUILD_ROOT/built-b.navigation.tsv"; then
  echo "$CHECK_NAME: two isolated builds have different navigation manifests" >&2
  exit 1
fi
if [[ "$MODE" == "--exact" ]]; then
  if ! cmp -s "$BUILD_ROOT/built-a.navigation.tsv" "$BUILD_ROOT/committed.navigation.tsv"; then
    echo "$CHECK_NAME: committed navigation manifest is stale" >&2
    exit 1
  fi
elif [[ "$MODE" == "--cross-toolchain" ]]; then
  python3 -I -S - \
    "$BUILD_ROOT/built-a.navigation.tsv" \
    "$BUILD_ROOT/committed.navigation.tsv" <<'PY'
from pathlib import Path
import sys


def fail(detail: str) -> None:
    raise SystemExit(f"mathematical workflow PDF check: cross-toolchain navigation {detail}")


def read(path: Path) -> list[list[str]]:
    raw = path.read_bytes()
    if not raw.endswith(b"\n") or b"\r" in raw:
        fail(f"manifest is not canonical LF text: {path}")
    rows = [line.split("\t") for line in raw.decode("utf-8").splitlines()]
    if not rows or rows[0] != ["schema", "pid-rs-workflow-navigation-manifest-v1"]:
        fail(f"manifest schema differs: {path}")
    return rows[1:]


left_rows = read(Path(sys.argv[1]))
right_rows = read(Path(sys.argv[2]))
if len(left_rows) != len(right_rows):
    fail(f"row count differs: {len(left_rows)} != {len(right_rows)}")
coordinate_tolerance_points = 2.0
for row_number, (left, right) in enumerate(zip(left_rows, right_rows, strict=True), start=2):
    if not left or not right or left[0] != right[0]:
        fail(f"row kind differs at row {row_number}")
    kind = left[0]
    if kind == "outline":
        if left != right:
            fail(f"outline route differs at row {row_number}")
        continue
    if kind == "destination":
        if len(left) != 9 or len(right) != 9 or left[:4] != right[:4]:
            fail(f"destination identity differs at row {row_number}")
        coordinate_pairs = zip(
            ("left", "top", "right", "bottom", "zoom"),
            left[4:],
            right[4:],
            strict=True,
        )
        identity = f"destination {left[1]!r}"
    elif kind == "annotation":
        if (
            len(left) != 10
            or len(right) != 10
            or left[:5] != right[:5]
            or left[9] != right[9]
        ):
            fail(f"annotation page/order/target/flags differ at row {row_number}")
        coordinate_pairs = zip(
            ("left", "bottom", "right", "top"),
            left[5:9],
            right[5:9],
            strict=True,
        )
        identity = f"annotation page={left[1]} order={left[2]} target={left[3]!r}"
    else:
        fail(f"unknown row kind at row {row_number}: {kind!r}")
    for field, left_raw, right_raw in coordinate_pairs:
        if left_raw == "null" or right_raw == "null":
            if left_raw != right_raw:
                fail(
                    f"null coordinate status differs at row {row_number} "
                    f"({identity}, field={field}, built={left_raw!r}, "
                    f"committed={right_raw!r})"
                )
            continue
        try:
            delta = abs(float(left_raw) - float(right_raw))
        except ValueError:
            fail(f"coordinate is not numeric at row {row_number}")
        if delta > coordinate_tolerance_points:
            fail(
                f"coordinate moved by {delta:.6g} points at row {row_number} "
                f"({identity}, field={field}, built={left_raw}, "
                f"committed={right_raw}); "
                f"limit is {coordinate_tolerance_points:.6g}"
            )
PY
fi

COLOR_RENDER="$BUILD_ROOT/render-built-color"
GRAY_RENDER="$BUILD_ROOT/render-built-gray"
COMMITTED_COLOR_RENDER="$BUILD_ROOT/render-committed-color"
COMMITTED_GRAY_RENDER="$BUILD_ROOT/render-committed-gray"
render_pdf_page_set "$BUILT_A" "$COLOR_RENDER" "report-built-color" color
render_pdf_page_set "$BUILT_A" "$GRAY_RENDER" "report-built-gray" gray
if [[ "$MODE" == "--cross-toolchain" ]]; then
  render_pdf_page_set \
    "$SNAPSHOT_ROOT/$COMMITTED" "$COMMITTED_COLOR_RENDER" "report-committed-color" color
  render_pdf_page_set \
    "$SNAPSHOT_ROOT/$COMMITTED" "$COMMITTED_GRAY_RENDER" "report-committed-gray" gray
  compare_render_sets \
    "$COLOR_RENDER" "$COMMITTED_COLOR_RENDER" "$EXPECTED_PAGES" "report-color" \
    "$BUILD_ROOT/report-color-comparison.tsv"
  compare_render_sets \
    "$GRAY_RENDER" "$COMMITTED_GRAY_RENDER" "$EXPECTED_PAGES" "report-gray" \
    "$BUILD_ROOT/report-gray-comparison.tsv"
fi

GENERATED_RECEIPT="$BUILD_ROOT/$REPORT_STEM.rendering-receipt.tsv"
python3 -I -S - \
  "$BUILT_A" \
  "$COLOR_RENDER" \
  "$GRAY_RENDER" \
  "$GENERATED_RECEIPT" \
  "$EXPECTED_PAGES" \
  "$RENDER_DPI" <<'PY'
from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import sys
import zlib


def fail(detail: str) -> None:
    print(f"mathematical workflow PDF check: rendering receipt {detail}", file=sys.stderr)
    raise SystemExit(1)


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def inspect_png(path: Path, expected_mode: str) -> tuple[int, int, int, int, int, int]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        fail(f"{path.name} is not a PNG")
    offset = 8
    idat = bytearray()
    width = height = bit_depth = color_type = interlace = None
    while offset < len(data):
        if offset + 12 > len(data):
            fail(f"{path.name} has a truncated chunk")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        if len(payload) != length:
            fail(f"{path.name} has a truncated payload")
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break
        offset += 12 + length
    if None in (width, height, bit_depth, color_type, interlace):
        fail(f"{path.name} lacks IHDR")
    if bit_depth != 8 or interlace != 0:
        fail(f"{path.name} is not non-interlaced 8-bit PNG")
    channels_by_type = {0: 1, 2: 3}
    channels = channels_by_type.get(color_type)
    if channels is None:
        fail(f"{path.name} has unsupported color type {color_type}")
    if expected_mode == "color" and color_type != 2:
        fail(f"{path.name} is not an opaque RGB rendering")
    if expected_mode == "gray" and color_type not in {0, 2}:
        fail(f"{path.name} has an unsupported grayscale-render container type")
    if (width, height) != (993, 1404):
        fail(f"{path.name} dimensions differ from A4 at the declared 120 DPI")
    stride = width * channels
    raw = zlib.decompress(bytes(idat))
    if len(raw) != height * (stride + 1):
        fail(f"{path.name} has an unexpected decoded byte count")
    previous = bytearray(stride)
    minimum = 255
    maximum = 0
    dark_pixels = 0
    chromatic_pixels = 0
    cursor = 0
    for _ in range(height):
        filter_type = raw[cursor]
        scan = raw[cursor + 1 : cursor + 1 + stride]
        cursor += stride + 1
        reconstructed = bytearray(stride)
        for index, value in enumerate(scan):
            left = reconstructed[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 0:
                predicted = 0
            elif filter_type == 1:
                predicted = left
            elif filter_type == 2:
                predicted = up
            elif filter_type == 3:
                predicted = (left + up) // 2
            elif filter_type == 4:
                predicted = paeth(left, up, upper_left)
            else:
                fail(f"{path.name} uses unsupported PNG filter {filter_type}")
            reconstructed[index] = (value + predicted) & 0xFF
        for index in range(0, stride, channels):
            if color_type == 2:
                red, green, blue = reconstructed[index : index + 3]
                if max(red, green, blue) - min(red, green, blue) > 2:
                    chromatic_pixels += 1
                if expected_mode == "gray" and not (red == green == blue):
                    fail(f"{path.name} grayscale rendering contains unequal RGB channels")
                luminance = (299 * red + 587 * green + 114 * blue) // 1000
            else:
                luminance = reconstructed[index]
            minimum = min(minimum, luminance)
            maximum = max(maximum, luminance)
            if luminance < 230:
                dark_pixels += 1
        previous = reconstructed
    if maximum - minimum < 30 or dark_pixels < 500:
        fail(f"{path.name} appears blank or has insufficient contrast")
    if expected_mode == "color" and chromatic_pixels < 500:
        fail(f"{path.name} color rendering contains insufficient chroma")
    if expected_mode == "gray" and chromatic_pixels != 0:
        fail(f"{path.name} grayscale rendering retained chroma")
    return width, height, minimum, maximum, dark_pixels, chromatic_pixels


pdf_path = Path(sys.argv[1])
color_dir = Path(sys.argv[2])
gray_dir = Path(sys.argv[3])
receipt_path = Path(sys.argv[4])
expected_pages = int(sys.argv[5])
dpi = int(sys.argv[6])
color_paths = sorted(color_dir.glob("page-*.png"))
gray_paths = sorted(gray_dir.glob("page-*.png"))
if len(color_paths) != expected_pages or len(gray_paths) != expected_pages:
    fail(
        f"expected {expected_pages} color and grayscale pages, "
        f"found {len(color_paths)} and {len(gray_paths)}"
    )

rows = [
    "schema\tpid-rs-formal-rendering-receipt-v2\n",
    f"pdf_sha256\t{hashlib.sha256(pdf_path.read_bytes()).hexdigest()}\n",
    f"pages\t{expected_pages}\n",
    f"dpi\t{dpi}\n",
    "mode\tpage\twidth\theight\tbytes\tsha256\tmin_luma\tmax_luma\tdark_pixels\tchromatic_pixels\n",
]
dimensions: dict[int, tuple[int, int]] = {}
for mode, paths in (("color", color_paths), ("gray", gray_paths)):
    for page_number, path in enumerate(paths, start=1):
        width, height, minimum, maximum, dark_pixels, chromatic_pixels = inspect_png(path, mode)
        if page_number in dimensions and dimensions[page_number] != (width, height):
            fail(f"page {page_number} color/grayscale dimensions differ")
        dimensions[page_number] = (width, height)
        data = path.read_bytes()
        rows.append(
            f"{mode}\t{page_number}\t{width}\t{height}\t{len(data)}\t"
            f"{hashlib.sha256(data).hexdigest()}\t{minimum}\t{maximum}\t{dark_pixels}\t"
            f"{chromatic_pixels}\n"
        )
receipt_path.write_text("".join(rows), encoding="utf-8", newline="\n")
PY

validate_rendering_receipt_pair() {
  local committed_receipt="$1"
  local committed_pdf="$2"
  local generated_receipt="$3"
  local generated_pdf="$4"
  local pages="$5"
  local dpi="$6"
  local validation_mode="$7"
  python3 -I -S - \
    "$committed_receipt" \
    "$committed_pdf" \
    "$generated_receipt" \
    "$generated_pdf" \
    "$pages" \
    "$dpi" \
    "$validation_mode" <<'PY'
import hashlib
from pathlib import Path
import re
import sys


expected_pages = int(sys.argv[5])
expected_dpi = int(sys.argv[6])
mode = sys.argv[7]
sha_pattern = re.compile(r"[0-9a-f]{64}")


def fail(label: str, detail: str) -> None:
    raise SystemExit(f"mathematical workflow PDF check: {label} rendering receipt {detail}")


def canonical_uint(raw: str, label: str, field: str) -> int:
    if not raw.isdigit() or str(int(raw)) != raw:
        fail(label, f"has a noncanonical {field}")
    return int(raw)


def validate(receipt_path: Path, pdf_path: Path, label: str) -> None:
    raw = receipt_path.read_bytes()
    if not raw.endswith(b"\n") or b"\r" in raw:
        fail(label, "does not have canonical LF termination")
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        fail(label, f"is not UTF-8: {error}")
    if len(lines) != 5 + 2 * expected_pages:
        fail(label, "row count drifted")
    if lines[0] != "schema\tpid-rs-formal-rendering-receipt-v2":
        fail(label, "schema drifted")
    expected_pdf_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    if lines[1] != f"pdf_sha256\t{expected_pdf_hash}":
        fail(label, "PDF digest binding drifted")
    if lines[2] != f"pages\t{expected_pages}" or lines[3] != f"dpi\t{expected_dpi}":
        fail(label, "page/DPI binding drifted")
    header = "mode\tpage\twidth\theight\tbytes\tsha256\tmin_luma\tmax_luma\tdark_pixels\tchromatic_pixels"
    if lines[4] != header:
        fail(label, "header drifted")
    expected_order = [
        (mode, page)
        for mode in ("color", "gray")
        for page in range(1, expected_pages + 1)
    ]
    dimensions: dict[int, tuple[int, int]] = {}
    for expected_pair, raw_row in zip(expected_order, lines[5:], strict=True):
        row = raw_row.split("\t")
        if len(row) != 10:
            fail(label, "row shape drifted")
        mode, page_raw, width_raw, height_raw, bytes_raw, digest, min_raw, max_raw, dark_raw, chroma_raw = row
        page = canonical_uint(page_raw, label, "page")
        if (mode, page) != expected_pair:
            fail(label, "page order/inventory drifted")
        width = canonical_uint(width_raw, label, "width")
        height = canonical_uint(height_raw, label, "height")
        byte_count = canonical_uint(bytes_raw, label, "byte count")
        minimum = canonical_uint(min_raw, label, "minimum luminance")
        maximum = canonical_uint(max_raw, label, "maximum luminance")
        dark_pixels = canonical_uint(dark_raw, label, "dark-pixel count")
        chromatic_pixels = canonical_uint(chroma_raw, label, "chromatic-pixel count")
        if (width, height) != (993, 1404):
            fail(label, f"page {page} dimensions drifted")
        if not 1024 <= byte_count <= 20 * 1024 * 1024:
            fail(label, f"page {page} PNG byte count is implausible")
        if sha_pattern.fullmatch(digest) is None:
            fail(label, f"page {page} PNG digest is noncanonical")
        pixels = width * height
        if not 0 <= minimum <= maximum <= 255 or maximum - minimum < 30:
            fail(label, f"page {page} luminance bounds are invalid")
        if not 500 <= dark_pixels <= pixels:
            fail(label, f"page {page} dark-pixel count is invalid")
        if mode == "color":
            if not 500 <= chromatic_pixels <= pixels:
                fail(label, f"page {page} color chroma count is invalid")
        elif chromatic_pixels != 0:
            fail(label, f"page {page} grayscale chroma count is nonzero")
        if page in dimensions and dimensions[page] != (width, height):
            fail(label, f"page {page} color/grayscale dimensions disagree")
        dimensions[page] = (width, height)


if mode != "--refresh":
    validate(Path(sys.argv[1]), Path(sys.argv[2]), "committed")
validate(Path(sys.argv[3]), Path(sys.argv[4]), "generated")
PY
}

validate_rendering_receipt_pair \
  "$SNAPSHOT_ROOT/$RENDERING_RECEIPT" \
  "$SNAPSHOT_ROOT/$COMMITTED" \
  "$GENERATED_RECEIPT" \
  "$BUILT_A" \
  "$EXPECTED_PAGES" \
  "$RENDER_DPI" \
  "$MODE"

if [[ "$MODE" == "--exact" ]]; then
  if ! cmp -s "$BUILT_A" "$SNAPSHOT_ROOT/$COMMITTED"; then
    echo "$CHECK_NAME: committed report PDF is stale or not reproducible" >&2
    exit 1
  fi
  if ! cmp -s "$GENERATED_RECEIPT" "$SNAPSHOT_ROOT/$RENDERING_RECEIPT"; then
    echo "$CHECK_NAME: committed color/grayscale rendering receipt is stale" >&2
    exit 1
  fi
elif [[ "$MODE" == "--cross-toolchain" ]]; then
  pdftotext -layout "$SNAPSHOT_ROOT/$COMMITTED" "$BUILD_ROOT/committed.txt"
  if ! cmp -s "$BUILD_ROOT/built.txt" "$BUILD_ROOT/committed.txt"; then
    echo "$CHECK_NAME: extracted report text/layout changed across toolchains" >&2
    exit 1
  fi
  grep -E '^(Pages|Page size|PDF version):' "$BUILD_ROOT/built-a.info" \
    >"$BUILD_ROOT/built.structure"
  grep -E '^(Pages|Page size|PDF version):' "$BUILD_ROOT/committed.info" \
    >"$BUILD_ROOT/committed.structure"
  if ! cmp -s "$BUILD_ROOT/built.structure" "$BUILD_ROOT/committed.structure"; then
    echo "$CHECK_NAME: report page structure changed across toolchains" >&2
    exit 1
  fi
fi

capture_manifest "$SNAPSHOT_ROOT" "$BUILD_ROOT/snapshot-inputs.after.tsv" ""
if ! cmp -s "$BUILD_ROOT/snapshot-inputs.tsv" "$BUILD_ROOT/snapshot-inputs.after.tsv"; then
  echo "$CHECK_NAME: captured read-only source snapshot changed while its consumers were running" >&2
  exit 1
fi
verify_snapshot_readonly

capture_manifest "$ROOT" "$BUILD_ROOT/root-inputs.after.tsv" ""
if ! cmp -s "$BUILD_ROOT/root-inputs.before.tsv" "$BUILD_ROOT/root-inputs.after.tsv"; then
  echo "$CHECK_NAME: report input changed while isolated checks were running" >&2
  exit 1
fi

# COMMAND_RESOLUTION_POST_VALIDATION: reject persistent PATH/symlink drift before final custody and optional refresh.
verify_command_resolution
capture_executable_manifest "$BUILD_ROOT/executables.after.tsv"
if ! cmp -s "$BUILD_ROOT/executables.before.tsv" "$BUILD_ROOT/executables.after.tsv"; then
  echo "$CHECK_NAME: admitted executable bytes changed while isolated checks were running" >&2
  exit 1
fi
capture_pypdf_manifest "$BUILD_ROOT/pypdf.after.tsv"
if ! cmp -s "$BUILD_ROOT/pypdf.before.tsv" "$BUILD_ROOT/pypdf.after.tsv"; then
  echo "$CHECK_NAME: admitted pypdf bytes changed while isolated checks were running" >&2
  exit 1
fi

if [[ "$MODE" == "--refresh" ]]; then
  refresh_sources=("$BUILT_A" "$GENERATED_RECEIPT")
  refresh_destinations=("$COMMITTED" "$RENDERING_RECEIPT")
  for stem in "${FIGURE_STEMS[@]}"; do
    refresh_sources+=("$REPORT_FIGURE_DIR/$stem.pdf")
    refresh_destinations+=("$FIGURE_DIR/$stem.pdf")
  done
  python3 -I -S - \
    "$ROOT" \
    "$BUILD_ROOT/root-inputs.before.tsv" \
    "${#refresh_sources[@]}" \
    "${refresh_sources[@]}" \
    "${refresh_destinations[@]}" <<'PY'
from __future__ import annotations

import ctypes
import ctypes.util
import hashlib
import os
from pathlib import Path
import platform
import stat
import sys


def fail(detail: str) -> None:
    raise SystemExit(f"mathematical workflow PDF check: refresh {detail}")


READ_FLAGS = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
DIRECTORY_FLAGS = READ_FLAGS | getattr(os, "O_DIRECTORY", 0)


def read_descriptor_stably(descriptor: int, opening_stat: os.stat_result, label: str) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            break
        chunks.append(chunk)
    closing_stat = os.fstat(descriptor)
    stable_fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
    if any(getattr(opening_stat, field) != getattr(closing_stat, field) for field in stable_fields):
        fail(f"{label} changed while being read")
    data = b"".join(chunks)
    if len(data) != opening_stat.st_size:
        fail(f"{label} byte count changed while being read")
    return data


def read_stable_source(path: Path) -> bytes:
    path_stat = path.lstat()
    if not stat.S_ISREG(path_stat.st_mode) or path_stat.st_nlink != 1:
        fail(f"source is not a single-link regular file: {path}")
    descriptor = os.open(path, READ_FLAGS)
    try:
        opening_stat = os.fstat(descriptor)
        identity_fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(path_stat, field) != getattr(opening_stat, field) for field in identity_fields):
            fail(f"source identity changed before descriptor capture: {path}")
        return read_descriptor_stably(descriptor, opening_stat, f"source {path}")
    finally:
        os.close(descriptor)


def open_directory_beneath(root_descriptor: int, parts: tuple[str, ...], label: str) -> int:
    descriptor = os.dup(root_descriptor)
    try:
        for part in parts:
            next_descriptor = os.open(part, DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        fail(f"destination parent is not a stable real directory: {label}")


# Directory link counts are not an identity field: on APFS they can change when this writer creates
# ordinary staging entries in the directory.  Bind the object, kind/permissions, and ownership;
# mutable directory timestamps and link counts are deliberately excluded from the stable identity.
DIRECTORY_IDENTITY_FIELDS = ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid")


def directory_identity(status: os.stat_result) -> tuple[int, ...]:
    return tuple(getattr(status, field) for field in DIRECTORY_IDENTITY_FIELDS)


def open_live_root(
    root_path: Path,
    expected_identity: tuple[int, ...],
    phase: str,
) -> int:
    try:
        path_stat = root_path.lstat()
        if not stat.S_ISDIR(path_stat.st_mode):
            fail(f"repository-root binding changed during {phase}")
        descriptor = os.open(root_path, DIRECTORY_FLAGS)
    except (FileNotFoundError, NotADirectoryError, OSError):
        fail(f"repository-root binding changed during {phase}")
    descriptor_stat = os.fstat(descriptor)
    if (
        directory_identity(path_stat) != directory_identity(descriptor_stat)
        or directory_identity(descriptor_stat) != expected_identity
    ):
        os.close(descriptor)
        fail(f"repository-root binding changed during {phase}")
    return descriptor


def open_live_parent(
    root_path: Path,
    root_identity: tuple[int, ...],
    item: dict[str, object],
    phase: str,
) -> int:
    live_root_descriptor = open_live_root(root_path, root_identity, phase)
    try:
        live_parent_descriptor = open_directory_beneath(
            live_root_descriptor,
            tuple(item["parent_parts"]),
            str(item["relative"]),
        )
    finally:
        os.close(live_root_descriptor)
    if directory_identity(os.fstat(live_parent_descriptor)) != item["parent_identity"]:
        os.close(live_parent_descriptor)
        fail(f"destination parent binding changed during {phase}: {item['relative']}")
    return live_parent_descriptor


def read_regular_at(
    directory_descriptor: int,
    name: str,
    label: str,
) -> tuple[bytes, int, tuple[int, int]]:
    path_stat = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
    if not stat.S_ISREG(path_stat.st_mode) or path_stat.st_nlink != 1:
        fail(f"{label} is not a single-link regular file")
    descriptor = os.open(name, READ_FLAGS, dir_fd=directory_descriptor)
    try:
        opening_stat = os.fstat(descriptor)
        if (path_stat.st_dev, path_stat.st_ino, path_stat.st_mode, path_stat.st_nlink) != (
            opening_stat.st_dev,
            opening_stat.st_ino,
            opening_stat.st_mode,
            opening_stat.st_nlink,
        ):
            fail(f"{label} identity changed before descriptor capture")
        return (
            read_descriptor_stably(descriptor, opening_stat, label),
            stat.S_IMODE(opening_stat.st_mode),
            (opening_stat.st_dev, opening_stat.st_ino),
        )
    finally:
        os.close(descriptor)


def node_identity_at(directory_descriptor: int, name: str) -> tuple[int, int]:
    value = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
    return value.st_dev, value.st_ino


def create_staged_file(directory_descriptor: int, prefix: str, data: bytes, mode: int) -> str:
    for _attempt in range(128):
        candidate = f".{prefix}.{os.urandom(16).hex()}"
        try:
            descriptor = os.open(
                candidate,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=directory_descriptor,
            )
        except FileExistsError:
            continue
        try:
            view = memoryview(data)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    fail(f"failed to write staged file {candidate}")
                view = view[written:]
            os.fchmod(descriptor, mode)
            os.fsync(descriptor)
        except BaseException:
            os.close(descriptor)
            try:
                os.unlink(candidate, dir_fd=directory_descriptor)
            except FileNotFoundError:
                pass
            raise
        os.close(descriptor)
        return candidate
    fail(f"could not allocate a unique staged filename for {prefix}")


def atomic_rename_at(
    directory_descriptor: int,
    source: str,
    destination: str,
    *,
    exchange: bool,
) -> None:
    """Use a no-overwrite rename or an atomic exchange on Darwin/Linux."""

    system = platform.system()
    library = ctypes.CDLL(ctypes.util.find_library("c") or None, use_errno=True)
    if system == "Darwin":
        function = library.renameatx_np
        flag = 0x00000002 if exchange else 0x00000004  # RENAME_SWAP / RENAME_EXCL
    elif system == "Linux":
        function = library.renameat2
        flag = 0x00000002 if exchange else 0x00000001  # EXCHANGE / NOREPLACE
    else:
        fail(f"atomic rename primitives are unsupported on {system}")
    function.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    function.restype = ctypes.c_int
    result = function(
        directory_descriptor,
        os.fsencode(source),
        directory_descriptor,
        os.fsencode(destination),
        flag,
    )
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number), f"{source} -> {destination}")


root = Path(sys.argv[1]).resolve(strict=True)
expected_source_manifest_path = Path(sys.argv[2])
source_count = int(sys.argv[3])
sources = [Path(raw) for raw in sys.argv[4 : 4 + source_count]]
relatives = [Path(raw) for raw in sys.argv[4 + source_count :]]
if source_count != 6 or len(sources) != source_count or len(relatives) != source_count:
    fail("requires one report PDF, one rendering receipt, and four figure PDFs")
source_data = [read_stable_source(source) for source in sources]
expected_receipt_binding = (
    f"pdf_sha256\t{hashlib.sha256(source_data[0]).hexdigest()}\n".encode("ascii")
)
if sum(line == expected_receipt_binding for line in source_data[1].splitlines(keepends=True)) != 1:
    fail("rendering receipt does not uniquely bind the staged PDF")

root_descriptor = os.open(root, DIRECTORY_FLAGS)
root_identity = directory_identity(os.fstat(root_descriptor))
staged: list[dict[str, object]] = []
replaced: list[dict[str, object]] = []


def parse_expected_source_manifest(path: Path) -> dict[str, tuple[int, str]]:
    raw = read_stable_source(path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail("expected source manifest is not UTF-8")
    if not text.endswith("\n") or "\r" in text:
        fail("expected source manifest is not canonical LF text")
    rows: dict[str, tuple[int, str]] = {}
    for line in text.splitlines():
        fields = line.split("\t")
        if len(fields) != 3 or fields[0] in rows:
            fail("expected source manifest contains a malformed or duplicate row")
        raw_size = fields[1]
        digest = fields[2]
        if (
            not raw_size.isdigit()
            or (len(raw_size) > 1 and raw_size.startswith("0"))
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            fail("expected source manifest contains a noncanonical size or digest")
        relative = Path(fields[0])
        if relative.is_absolute() or any(
            part in ("", ".", "..") for part in relative.parts
        ):
            fail(f"expected source manifest path is unsafe: {fields[0]!r}")
        if relative.as_posix() != fields[0]:
            fail(f"expected source manifest path is noncanonical: {fields[0]!r}")
        rows[fields[0]] = (int(raw_size), digest)
    if not rows:
        fail("expected source manifest is empty")
    return rows


expected_source_manifest = parse_expected_source_manifest(
    expected_source_manifest_path
)
destination_strings = {relative.as_posix() for relative in relatives}
overlap = destination_strings.intersection(expected_source_manifest)
if overlap:
    fail(f"generated destination is incorrectly classified as a source input: {sorted(overlap)!r}")


def verify_nonoutput_source_manifest(phase: str) -> None:
    observed: dict[str, tuple[int, str]] = {}
    for raw_relative, expected in expected_source_manifest.items():
        relative = Path(raw_relative)
        parent_descriptor = open_directory_beneath(
            root_descriptor,
            tuple(relative.parent.parts),
            raw_relative,
        )
        try:
            data, _mode, _node = read_regular_at(
                parent_descriptor,
                relative.name,
                f"non-output source during {phase}: {raw_relative}",
            )
        finally:
            os.close(parent_descriptor)
        observed[raw_relative] = (len(data), hashlib.sha256(data).hexdigest())
        if observed[raw_relative] != expected:
            fail(f"non-output source changed during {phase}: {raw_relative}")
    if observed != expected_source_manifest:
        fail(f"non-output source inventory changed during {phase}")


figure_destination_relatives = relatives[2:]
figure_parent_parts = {tuple(relative.parent.parts) for relative in figure_destination_relatives}
if len(figure_parent_parts) != 1:
    fail("figure destination parents are inconsistent")
figure_parent = figure_destination_relatives[0].parent
figure_source_names = {
    Path(raw).name
    for raw in expected_source_manifest
    if Path(raw).parent == figure_parent and Path(raw).suffix == ".svg"
}
if len(figure_source_names) != 4:
    fail("expected source manifest does not bind four figure SVGs")
expected_final_figure_names = figure_source_names | {
    relative.name for relative in figure_destination_relatives
}


def verify_final_figure_inventory() -> None:
    parent_descriptor = open_directory_beneath(
        root_descriptor,
        tuple(figure_parent.parts),
        str(figure_parent),
    )
    try:
        actual = set(os.listdir(parent_descriptor))
        recovery_items = [
            item
            for item in staged
            if item["relative"].parent == figure_parent
            and item["install_kind"] == "exchange"
            and item["new_temporary"] is not None
        ]
        recovery_names = {str(item["new_temporary"]) for item in recovery_items}
        if len(recovery_names) != len(recovery_items):
            fail("writer-owned figure recovery-name inventory is not unique")
        expected_during_transaction = expected_final_figure_names | recovery_names
        if actual != expected_during_transaction:
            fail(
                "final figure inventory differs; "
                f"missing={sorted(expected_during_transaction - actual)!r}; "
                f"extra={sorted(actual - expected_during_transaction)!r}"
            )
        for name in sorted(expected_final_figure_names):
            read_regular_at(
                parent_descriptor,
                name,
                f"final figure inventory entry {name}",
            )
        for item in recovery_items:
            recovery_record = read_regular_at(
                parent_descriptor,
                str(item["new_temporary"]),
                f"writer-owned displaced figure {item['relative']}",
            )
            if recovery_record != item["rollback_record"]:
                fail(f"writer-owned displaced figure readback differs: {item['relative']}")
    finally:
        os.close(parent_descriptor)


verify_nonoutput_source_manifest("pre-install verification")


def assert_all_live_bindings(phase: str) -> None:
    live_root_descriptor = open_live_root(root, root_identity, phase)
    os.close(live_root_descriptor)
    for staged_item in staged:
        live_parent_descriptor = open_live_parent(
            root,
            root_identity,
            staged_item,
            phase,
        )
        os.close(live_parent_descriptor)


def rollback_replaced(replacement_error: BaseException) -> None:
    rollback_errors: list[str] = []
    for item in reversed(replaced):
        parent_descriptor = int(item["parent_descriptor"])
        destination_name = str(item["destination_name"])
        # An exchange item holds the displaced pre-install node at its temporary name.  Keep that
        # recovery node on every exceptional path unless a verified reverse exchange completes;
        # otherwise a type-changing concurrent write could make read_regular_at fail and the outer
        # cleanup would destroy the only retained original.
        if item["install_kind"] == "exchange":
            item["preserve_temporary"] = True
        try:
            current_data, current_mode, current_node = read_regular_at(
                parent_descriptor,
                destination_name,
                f"rollback candidate destination {item['relative']}",
            )
            if (
                current_data != item["new_data"]
                or current_mode != 0o644
                or current_node != item["new_node"]
            ):
                item["preserve_temporary"] = True
                raise RuntimeError(
                    "installed path changed; refusing to overwrite a concurrent writer"
                )
            if item["install_kind"] == "absent":
                os.unlink(destination_name, dir_fd=parent_descriptor)
            elif item["install_kind"] == "exchange":
                new_temporary = item["new_temporary"]
                if new_temporary is None:
                    raise RuntimeError("displaced destination path is absent")
                rollback_record = item["rollback_record"]
                if rollback_record is None:
                    rollback_record = read_regular_at(
                        parent_descriptor,
                        str(new_temporary),
                        f"rollback displaced destination {item['relative']}",
                    )
                atomic_rename_at(
                    parent_descriptor,
                    str(new_temporary),
                    destination_name,
                    exchange=True,
                )
                restored = read_regular_at(
                    parent_descriptor,
                    destination_name,
                    f"rolled-back destination {item['relative']}",
                )
                if restored != rollback_record:
                    raise RuntimeError("rollback readback differs")
                item["preserve_temporary"] = False
            else:
                raise RuntimeError("rollback encountered an unknown install kind")
            os.fsync(parent_descriptor)
        except BaseException as rollback_error:
            recovery = ""
            if item["preserve_temporary"] and item["new_temporary"] is not None:
                recovery_path = item["relative"].parent / str(item["new_temporary"])
                recovery = f"; displaced recovery node retained at {recovery_path}"
            rollback_errors.append(f"{item['relative']}: {rollback_error}{recovery}")
    if rollback_errors:
        fail(
            "replacement failed and rollback was incomplete: "
            + "; ".join(rollback_errors)
            + f"; replacement error: {replacement_error}"
        )


try:
    for data, relative in zip(source_data, relatives, strict=True):
        assert_all_live_bindings(f"before staging {relative}")
        if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
            fail(f"destination is unsafe: {relative}")
        parent_parts = tuple(relative.parent.parts)
        parent_descriptor = open_directory_beneath(
            root_descriptor,
            parent_parts,
            str(relative),
        )
        destination_name = relative.name
        item: dict[str, object] = {
            "relative": relative,
            "parent_parts": parent_parts,
            "parent_descriptor": parent_descriptor,
            "parent_identity": directory_identity(os.fstat(parent_descriptor)),
            "destination_name": destination_name,
            "new_temporary": None,
            "new_data": data,
            "new_node": None,
            "original": None,
            "rollback_record": None,
            "install_kind": None,
            "preserve_temporary": False,
        }
        staged.append(item)
        try:
            original_data, original_mode, original_node = read_regular_at(
                parent_descriptor,
                destination_name,
                f"destination {relative}",
            )
            original: tuple[bytes, int, tuple[int, int]] | None = (
                original_data,
                original_mode,
                original_node,
            )
        except FileNotFoundError:
            original = None
        item["original"] = original
        item["new_temporary"] = create_staged_file(
            parent_descriptor,
            f"{destination_name}.refresh-new",
            data,
            0o644,
        )
        _staged_data, _staged_mode, staged_node = read_regular_at(
            parent_descriptor,
            str(item["new_temporary"]),
            f"staged destination {relative}",
        )
        if _staged_data != data or _staged_mode != 0o644:
            fail(f"staged destination readback differs: {relative}")
        item["new_node"] = staged_node
        assert_all_live_bindings(f"after staging {relative}")

    try:
        for item in staged:
            assert_all_live_bindings(f"before replacing {item['relative']}")
            parent_descriptor = int(item["parent_descriptor"])
            new_temporary = str(item["new_temporary"])
            destination_name = str(item["destination_name"])
            original = item["original"]
            if original is None:
                atomic_rename_at(
                    parent_descriptor,
                    new_temporary,
                    destination_name,
                    exchange=False,
                )
                item["new_temporary"] = None
                item["install_kind"] = "absent"
                replaced.append(item)
            else:
                atomic_rename_at(
                    parent_descriptor,
                    new_temporary,
                    destination_name,
                    exchange=True,
                )
                item["install_kind"] = "exchange"
                replaced.append(item)
                displaced_node = node_identity_at(parent_descriptor, new_temporary)
                displaced_error: BaseException | None = None
                try:
                    displaced = read_regular_at(
                        parent_descriptor,
                        new_temporary,
                        f"atomically displaced destination {item['relative']}",
                    )
                except BaseException as error:
                    displaced = None
                    displaced_error = error
                if displaced_error is not None or displaced != original:
                    # The exchange has already moved the concurrently observed node to the random
                    # staging name.  Restore that exact node immediately without requiring it to
                    # be a regular file: a symlink, hard link, or otherwise changed inode is the
                    # very evidence that the final compare-and-swap premise failed.  Leaving this
                    # item in the generic rollback list would make restoration depend on parsing
                    # the hostile node and could then discard it during cleanup.
                    try:
                        atomic_rename_at(
                            parent_descriptor,
                            new_temporary,
                            destination_name,
                            exchange=True,
                        )
                        os.fsync(parent_descriptor)
                        if node_identity_at(parent_descriptor, destination_name) != displaced_node:
                            raise RuntimeError("restored destination node identity differs")
                    except BaseException as restore_error:
                        item["preserve_temporary"] = True
                        raise RuntimeError(
                            "destination changed in the final compare-and-swap window and "
                            f"immediate restoration failed: {item['relative']}: {restore_error}"
                        ) from displaced_error
                    if not replaced or replaced[-1] is not item:
                        raise RuntimeError("replacement rollback order drifted")
                    replaced.pop()
                    item["install_kind"] = None
                    item["rollback_record"] = None
                    raise RuntimeError(
                        f"destination changed in the final compare-and-swap window: {item['relative']}"
                    ) from displaced_error
                item["rollback_record"] = displaced
            os.fsync(parent_descriptor)
            installed_data, installed_mode, installed_node = read_regular_at(
                parent_descriptor,
                destination_name,
                f"installed destination {item['relative']}",
            )
            if (
                installed_data != item["new_data"]
                or installed_mode != 0o644
                or installed_node != item["new_node"]
            ):
                fail(f"installed destination readback differs: {item['relative']}")
            live_parent_descriptor = open_live_parent(
                root,
                root_identity,
                item,
                f"after replacing {item['relative']}",
            )
            try:
                live_data, live_mode, live_node = read_regular_at(
                    live_parent_descriptor,
                    destination_name,
                    f"live installed destination {item['relative']}",
                )
            finally:
                os.close(live_parent_descriptor)
            if (
                live_data != item["new_data"]
                or live_mode != 0o644
                or live_node != item["new_node"]
            ):
                fail(f"live installed destination readback differs: {item['relative']}")
            assert_all_live_bindings(f"after readback {item['relative']}")
    except BaseException as replacement_error:
        rollback_replaced(replacement_error)
        raise
    try:
        assert_all_live_bindings("final pair verification")
        live_pair: list[bytes] = []
        for item in staged:
            live_parent_descriptor = open_live_parent(
                root,
                root_identity,
                item,
                "final pair verification",
            )
            try:
                installed_data, installed_mode, installed_node = read_regular_at(
                    live_parent_descriptor,
                    str(item["destination_name"]),
                    f"final live destination {item['relative']}",
                )
            finally:
                os.close(live_parent_descriptor)
            if (
                installed_data != item["new_data"]
                or installed_mode != 0o644
                or installed_node != item["new_node"]
            ):
                fail(f"final live destination readback differs: {item['relative']}")
            live_pair.append(installed_data)
        final_receipt_binding = (
            f"pdf_sha256\t{hashlib.sha256(live_pair[0]).hexdigest()}\n".encode("ascii")
        )
        if sum(
            line == final_receipt_binding
            for line in live_pair[1].splitlines(keepends=True)
        ) != 1:
            fail("final live rendering receipt does not uniquely bind the installed PDF")
        verify_nonoutput_source_manifest("post-install verification")
        verify_final_figure_inventory()
    except BaseException as final_verification_error:
        rollback_replaced(final_verification_error)
        raise
finally:
    for item in staged:
        parent_descriptor = int(item["parent_descriptor"])
        temporary = item["new_temporary"]
        if temporary is not None and not item["preserve_temporary"]:
            try:
                os.unlink(str(temporary), dir_fd=parent_descriptor)
                os.fsync(parent_descriptor)
            except FileNotFoundError:
                pass
        os.close(parent_descriptor)
    os.close(root_descriptor)
PY
  capture_manifest "$ROOT" "$BUILD_ROOT/root-inputs.post-refresh.tsv" ""
  python3 -I -S - \
    "$BUILD_ROOT/root-inputs.before.tsv" \
    "$BUILD_ROOT/root-inputs.post-refresh.tsv" \
    "$ROOT" \
    "$BUILT_A" \
    "$GENERATED_RECEIPT" \
    "$REPORT_FIGURE_DIR" \
    "$COMMITTED" \
    "$RENDERING_RECEIPT" \
    "$FIGURE_DIR" \
    "${FIGURE_STEMS[@]}" <<'PY'
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from pathlib import PurePosixPath
import stat
import sys


def fail(detail: str) -> None:
    raise SystemExit(f"mathematical workflow PDF check: post-refresh source custody {detail}")


def parse(path: Path) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) != 3 or fields[0] in rows:
            fail(f"manifest row is malformed or duplicated: {path}")
        rows[fields[0]] = (fields[1], fields[2])
    return rows


before = parse(Path(sys.argv[1]))
after = parse(Path(sys.argv[2]))
if before != after:
    changed = sorted(
        path
        for path in before.keys() | after.keys()
        if before.get(path) != after.get(path)
    )
    fail(f"non-output input changed during installation: {changed[:1]!r}")

root = Path(sys.argv[3]).resolve(strict=True)
report_source = Path(sys.argv[4])
receipt_source = Path(sys.argv[5])
generated_directory = Path(sys.argv[6])
report_destination = sys.argv[7]
receipt_destination = sys.argv[8]
figure_destination_directory = sys.argv[9]
stems = sys.argv[10:]


def fingerprint(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def read_descriptor(descriptor: int, opening: os.stat_result, label: str) -> bytes:
    if not stat.S_ISREG(opening.st_mode) or opening.st_nlink != 1:
        fail(f"{label} is not a single-link regular file")
    if opening.st_size > 32 * 1024 * 1024:
        fail(f"{label} exceeds the 32 MiB verification bound")
    chunks: list[bytes] = []
    remaining = opening.st_size
    while remaining:
        chunk = os.read(descriptor, min(remaining, 1024 * 1024))
        if not chunk:
            fail(f"{label} truncated during verification")
        chunks.append(chunk)
        remaining -= len(chunk)
    if os.read(descriptor, 1):
        fail(f"{label} grew during verification")
    if fingerprint(os.fstat(descriptor)) != fingerprint(opening):
        fail(f"{label} changed during verification")
    return b"".join(chunks)


def read_source(path: Path, label: str) -> bytes:
    named = path.lstat()
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        opened = os.fstat(descriptor)
        if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
            fail(f"{label} changed during open")
        data = read_descriptor(descriptor, opened, label)
        final = path.lstat()
        if fingerprint(final) != fingerprint(opened):
            fail(f"{label} path changed during verification")
        return data
    finally:
        os.close(descriptor)


def split_relative(raw: str) -> tuple[str, ...]:
    relative = PurePosixPath(raw)
    if (
        relative.is_absolute()
        or not relative.parts
        or relative.as_posix() != raw
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        fail(f"destination path is noncanonical: {raw!r}")
    return relative.parts


def read_destination(root_descriptor: int, raw: str) -> bytes:
    parts = split_relative(raw)
    descriptors = [os.dup(root_descriptor)]
    try:
        for part in parts[:-1]:
            descriptor = os.open(
                part,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=descriptors[-1],
            )
            descriptors.append(descriptor)
        named = os.stat(parts[-1], dir_fd=descriptors[-1], follow_symlinks=False)
        descriptor = os.open(
            parts[-1],
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=descriptors[-1],
        )
        try:
            opened = os.fstat(descriptor)
            if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
                fail(f"installed destination changed during open: {raw}")
            data = read_descriptor(descriptor, opened, f"installed destination {raw}")
            final = os.stat(parts[-1], dir_fd=descriptors[-1], follow_symlinks=False)
            if fingerprint(final) != fingerprint(opened):
                fail(f"installed destination path changed during verification: {raw}")
            return data
        finally:
            os.close(descriptor)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def list_destination_directory(root_descriptor: int, raw: str) -> set[str]:
    parts = split_relative(raw)
    descriptors = [os.dup(root_descriptor)]
    try:
        for part in parts:
            named = os.stat(part, dir_fd=descriptors[-1], follow_symlinks=False)
            descriptor = os.open(
                part,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=descriptors[-1],
            )
            opened = os.fstat(descriptor)
            if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
                os.close(descriptor)
                fail(f"installed directory changed during open: {raw}")
            descriptors.append(descriptor)
        opening = os.fstat(descriptors[-1])
        names = set(os.listdir(descriptors[-1]))
        if fingerprint(os.fstat(descriptors[-1])) != fingerprint(opening):
            fail(f"installed directory changed during inventory read: {raw}")
        return names
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


pairs = [
    (report_source, report_destination),
    (receipt_source, receipt_destination),
]
pairs.extend(
    (generated_directory / f"{stem}.pdf", f"{figure_destination_directory}/{stem}.pdf")
    for stem in stems
)
root_descriptor = os.open(
    root,
    os.O_RDONLY
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_CLOEXEC", 0),
)
installed_bytes: dict[str, bytes] = {}
try:
    for source, destination in pairs:
        expected = read_source(source, f"generated source {source.name}")
        observed = read_destination(root_descriptor, destination)
        if observed != expected:
            fail(f"installed bytes differ from generated source: {destination}")
        installed_bytes[destination] = observed
    if len(stems) != 4 or len(set(stems)) != 4:
        fail("figure-stem inventory is not exactly four unique names")
    expected_figure_names = {
        f"{stem}.{suffix}"
        for stem in stems
        for suffix in ("svg", "pdf")
    }
    observed_figure_names = list_destination_directory(
        root_descriptor,
        figure_destination_directory,
    )
    if observed_figure_names != expected_figure_names:
        fail(
            "post-cleanup figure inventory differs; "
            f"missing={sorted(expected_figure_names - observed_figure_names)!r}; "
            f"extra={sorted(observed_figure_names - expected_figure_names)!r}"
        )
    for name in sorted(expected_figure_names):
        read_destination(root_descriptor, f"{figure_destination_directory}/{name}")
finally:
    os.close(root_descriptor)

installed_report = installed_bytes[report_destination]
installed_receipt = installed_bytes[receipt_destination]
binding = f"pdf_sha256\t{hashlib.sha256(installed_report).hexdigest()}\n"
try:
    receipt_text = installed_receipt.decode("utf-8")
except UnicodeDecodeError:
    fail("installed rendering receipt is not UTF-8")
if receipt_text.splitlines(keepends=True).count(binding) != 1:
    fail("installed rendering receipt lost its unique report-PDF binding")
PY
fi

DIGEST="$(sha256_file "$BUILT_A")"
RECEIPT_DIGEST="$(sha256_file "$GENERATED_RECEIPT")"
EXECUTABLE_MANIFEST_DIGEST="$(sha256_file "$BUILD_ROOT/executables.before.tsv")"
PYPDF_MANIFEST_DIGEST="$(sha256_file "$BUILD_ROOT/pypdf.before.tsv")"
if [[ "$MODE" == "--exact" ]]; then
  echo "OK: workflow PDF, four SVG/PDF pairs, two isolated report builds, and $EXPECTED_PAGES-page dual-render receipt are exact ($DIGEST; receipt $RECEIPT_DIGEST; executable manifest $EXECUTABLE_MANIFEST_DIGEST; pypdf manifest $PYPDF_MANIFEST_DIGEST; format source $FORMAT_QUERY; format snapshot $FORMAT_BYTES bytes sha256 $FORMAT_SHA256)"
elif [[ "$MODE" == "--cross-toolchain" ]]; then
  echo "OK: workflow PDF and four SVG/PDF pairs preserve text, structure, and bounded same-renderer color/grayscale pixels across toolchains; $EXPECTED_PAGES report pages rendered ($DIGEST; receipt $RECEIPT_DIGEST; executable manifest $EXECUTABLE_MANIFEST_DIGEST; pypdf manifest $PYPDF_MANIFEST_DIGEST; format source $FORMAT_QUERY; format snapshot $FORMAT_BYTES bytes sha256 $FORMAT_SHA256)"
else
  echo "UPDATED: the workflow PDF, rendering receipt, and four source-bound figure PDFs were individually atomically renamed and read back after two isolated $EXPECTED_PAGES-page builds ($DIGEST; receipt $RECEIPT_DIGEST; format source $FORMAT_QUERY; format snapshot $FORMAT_BYTES bytes sha256 $FORMAT_SHA256); ordinary failure rolls back completed replacements whose installed nodes remain unchanged, while a detected concurrent replacement is preserved and makes the transition fail with retained recovery state; a crash between the six renames can leave a fail-closed mismatch; the visual-review receipt must now be independently rebound before --exact can pass"
fi
