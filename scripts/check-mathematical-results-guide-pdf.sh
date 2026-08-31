#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
BUILDER="$ROOT/scripts/build-mathematical-results-guide-pdf.sh"
COMMITTED="$ROOT/output/pdf/mathematical-results-guide.pdf"
MODE="${1:---exact}"
CHECK_NAME="Mathematical results guide PDF check"
PROSE_CHECK="$ROOT/scripts/check-mathematical-results-guide-prose.py"
PROSE_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-prose-self-test.py"
BUILDER_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-builder-self-test.sh"
TAGPDF_COMPAT_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-tagpdf-compat-self-test.sh"
URI_CONTENTS_COMPAT_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-uri-contents-compat-self-test.sh"
FILESPEC_COMPAT_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-filespec-compat-self-test.sh"
FIGURE_ASSET_CHECK="$ROOT/scripts/check-mathematical-results-guide-figure-assets.py"
FIGURE_ASSET_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-figure-assets-self-test.py"
OPEN_FONT_REGENERATOR="$ROOT/scripts/regenerate-mathematical-results-guide-open-font-figures.py"
OPEN_FONT_REGENERATOR_SELF_TEST="$ROOT/scripts/regenerate-mathematical-results-guide-open-font-figures-self-test.py"
ID_VARIANCE_CHECK="$ROOT/scripts/check-mathematical-results-guide-pdf-id-variance.py"
ID_VARIANCE_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-pdf-id-variance-self-test.py"
ID_VARIANCE_CHECK_SHA256=d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7
FONT_ROSTER_CHECK="$ROOT/scripts/check-mathematical-results-guide-font-roster.py"
FONT_ROSTER_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-font-roster-self-test.py"
TRAILER_ID_OBSERVATION_CHECK="$ROOT/scripts/check-mathematical-results-guide-trailer-id-observation.py"
TRAILER_ID_OBSERVATION_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-trailer-id-observation-self-test.py"
TRAILER_ID_OBSERVATION_CHECK_SHA256=e531d58620ff41275b741666a119a1245d5ec2a08fa943fc12a297d56317106f
TRAILER_ID_OBSERVATION_SELF_TEST_SHA256=9b1d0da3dffc87e9d46a4986b9c54c457c036ff0cd0a0966f08155aad7b5b65b
STRUCTURE_CHECK="$ROOT/scripts/check-mathematical-results-guide-pdf-structure-v2.py"
STRUCTURE_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-pdf-structure-v2-self-test.py"
HOSTED_RAW_CHECK="$ROOT/scripts/check-mathematical-results-guide-pdf-hosted-raw-profile-v2.py"
HOSTED_RAW_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-pdf-hosted-raw-profile-v2-self-test.py"
FONT_ALPHA_CHECK="$ROOT/scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence.py"
FONT_ALPHA_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence-self-test.py"
MODE_WIRING_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-pdf-mode-wiring-self-test.py"
RETAINED_HOSTED_RAW_FIXTURE="$ROOT/audit/evidence/mathematical-results-guide-pandoc-3.10.2-ubuntu-24.04-texlive-2023-hosted-raw-v2.pdf"
HOSTED_RAW_PROFILE_RECEIPT="$ROOT/audit/evidence/mathematical-results-guide-pandoc-3.10.2-hosted-raw-profile-v2.json"
RETAINED_FONT_ALPHA_FIXTURE="$ROOT/audit/evidence/mathematical-results-guide-pandoc-3.1.3-texlive-2023-font-alpha.pdf"
STRUCTURE_CHECK_SHA256=a70d3c78da7040774c5976f2316480501713eed1e9c865822e3024724a0ccf8d
STRUCTURE_SELF_TEST_SHA256=aa8fd64c627884d64b18c2e8cb2565c06678f2c5f55be182723541d026c56229
HOSTED_RAW_CHECK_SHA256=29837b202ad3e5afa59e10f0ef4848b876fb6ef2b6aa3a996f78d7aac2752fcc
HOSTED_RAW_SELF_TEST_SHA256=f24a3a3013ccf4f5964f947f26798ad00a01f47b7453a75ce9e29946d28f89f9
HOSTED_RAW_PROFILE_RECEIPT_SHA256=56e599a1f879418c8d2cce85f61b0a51cb1210f915462ff4aa6f0af8b2334be8
FONT_ALPHA_CHECK_SHA256=5a07012129960b8db96d77f292fa21a5ff67cdc79103bef23c0826bf00e2e997
FONT_ALPHA_SELF_TEST_SHA256=07f73bf9e2b027f5d50bcb3bd7c4ff5f8a7a4c1fb81f807af79387e3f962c5be
PANDOC_TEX_NORMALIZER="$ROOT/scripts/normalize-mathematical-results-guide-pandoc-tex.py"
PANDOC_TEX_NORMALIZER_SELF_TEST="$ROOT/scripts/normalize-mathematical-results-guide-pandoc-tex-self-test.py"
PANDOC_PORTABILITY_RECEIPT_CHECK="$ROOT/scripts/check-mathematical-results-guide-pandoc-portability-receipt.py"
PANDOC_PORTABILITY_RECEIPT_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-pandoc-portability-receipt-self-test.py"
PANDOC_PORTABILITY_RECEIPT_CHECK_SHA256=5e59e9fb997098656039db1a60c1e8694a451432618ac2ecd192b402e7a8c319
PANDOC_PORTABILITY_RECEIPT_SELF_TEST_SHA256=bdb53c0b8a20e48df73b22aeeabc223855c2ce797444808e6de495baf6ab2473
LEGACY_PANDOC_PORTABILITY_RECEIPT="$ROOT/audit/evidence/mathematical-results-guide-pandoc-3.1.3-portability-v1.json"
LEGACY_PANDOC_PORTABILITY_RECEIPT_SHA256=7ea2acf89c8a33f5666ab9798a594c24febdad609bd1b5e650b87d8a98ca4581
LEGACY_TRAILER_ID_OBSERVATION_RECEIPT="$ROOT/audit/evidence/mathematical-results-guide-old-toolchain-trailer-id-observation-v1.json"
LEGACY_TRAILER_ID_OBSERVATION_RECEIPT_SHA256=cd5602bb28dce0780c4bac5f70097e496d2afe9141a8210f249332b5e6d93596

HOSTED_PROFILE_ID=hosted-pandoc-3.10.2-ubuntu-24.04-raw-v2-bound
HOSTED_PANDOC_VERSION='pandoc 3.10.2'
HOSTED_PANDOC_SHA256=867c5fc83e6b18991d1880e040867d31d09a0d5e68b0bfae362d2fbc71cf25ce
HOSTED_RENDERER_VERSION='This is LuaHBTeX, Version 1.17.0 (TeX Live 2023/Debian)'
HOSTED_RENDERER_REALPATH=/usr/bin/luahbtex
HOSTED_RENDERER_SHA256=cc74da0d993e503321f9dd65b8cc5ddf103f2620c4bdbc41798841f253c46e02
HOSTED_TEXMFSYSVAR=/var/lib/texmf
HOSTED_FORMAT_PATH=/var/lib/texmf/web2c/luahbtex/lualatex.fmt

LEGACY_PROFILE_ID=legacy-pandoc-3.1.3-ubuntu-24.04-font-alpha
LEGACY_PANDOC_VERSION='pandoc 3.1.3'
LEGACY_PANDOC_REALPATH=/usr/bin/pandoc
LEGACY_PANDOC_SHA256=3dd273647f0265cb439f22976d5366a54b071a3783f6fec50838b47fb53d701b
LEGACY_RENDERER_VERSION='This is LuaHBTeX, Version 1.17.0 (TeX Live 2023/Debian)'
LEGACY_RENDERER_REALPATH=/usr/bin/luahbtex
LEGACY_RENDERER_SHA256=cc74da0d993e503321f9dd65b8cc5ddf103f2620c4bdbc41798841f253c46e02
LEGACY_TEXMFSYSVAR=/var/lib/texmf
LEGACY_FORMAT_PATH=/var/lib/texmf/web2c/luahbtex/lualatex.fmt
# The historical receipt did not capture the selected format bytes.  Empty
# constants deliberately make that producer tuple unsupported until a retained,
# reviewed legacy-format record can bind both fields.
LEGACY_FORMAT_BYTES=''
LEGACY_FORMAT_SHA256=''

if (( $# > 1 )) || [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi
command -v python3 >/dev/null 2>&1 || {
  echo "$CHECK_NAME: missing command: python3" >&2
  exit 2
}
for guide_gate in "$PROSE_CHECK" "$PROSE_SELF_TEST" "$BUILDER_SELF_TEST" \
    "$TAGPDF_COMPAT_SELF_TEST" "$URI_CONTENTS_COMPAT_SELF_TEST" \
    "$FILESPEC_COMPAT_SELF_TEST" "$FIGURE_ASSET_CHECK" "$FIGURE_ASSET_SELF_TEST" \
    "$OPEN_FONT_REGENERATOR" "$OPEN_FONT_REGENERATOR_SELF_TEST" \
    "$ID_VARIANCE_CHECK" "$ID_VARIANCE_SELF_TEST" \
    "$FONT_ROSTER_CHECK" "$FONT_ROSTER_SELF_TEST" \
    "$STRUCTURE_CHECK" "$STRUCTURE_SELF_TEST" \
    "$MODE_WIRING_SELF_TEST" \
    "$PANDOC_TEX_NORMALIZER" "$PANDOC_TEX_NORMALIZER_SELF_TEST"; do
  if [[ ! -f "$guide_gate" || -L "$guide_gate" ]]; then
    echo "$CHECK_NAME: guide gate absent, non-regular, or symbolic: $guide_gate" >&2
    exit 1
  fi
done
for command_name in awk bash cat cmp diff env find grep mktemp pdffonts pdfinfo pdftoppm \
    pdftotext python3 rm shasum sort wc; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME: missing command: $command_name" >&2
    exit 2
  }
done
python3 -I -B -c 'import pypdf' >/dev/null 2>&1 || {
  echo "$CHECK_NAME: missing Python package: pypdf" >&2
  exit 2
}
for path in \
    "$BUILDER" \
    "$ROOT/MATHEMATICAL_RESULTS_GUIDE.md" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/header.tex" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/filter.lua" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/hgeneric-uri-contents-compat.tex" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/l3pdffile-filespec-f-compat.tex" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/pandoc-templates-bsd-3-clause-3.1.3-and-3.10.2.txt" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/canonical-figure-pdfs.json" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/open-font-figure-regeneration-v1.json" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/font-licenses/source-sans-pro-ofl-1.1-tex-live-2024.txt" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/font-licenses/gust-font-license-1.0-tex-live-2024.txt" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/font-licenses/manifest-latin-modern-2.004-tex-live-2024.txt" \
    "$ROOT/THIRD_PARTY_NOTICES.md" \
    "$ROOT/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.svg" \
    "$ROOT/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.pdf" \
    "$ROOT/audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.svg" \
    "$ROOT/audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.pdf" \
    "$ROOT/audit/formal/latex/figures/mathematical-results-guide/common-radius-small-ball-bridge.svg" \
    "$ROOT/audit/formal/latex/figures/mathematical-results-guide/common-radius-small-ball-bridge.pdf" \
    "$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.svg" \
    "$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.pdf" \
    "$COMMITTED"; do
  if [[ ! -f "$path" || -L "$path" ]]; then
    echo "$CHECK_NAME: required input absent, non-regular, or symbolic: $path" >&2
    exit 1
  fi
done

require_gate_digest() {
  local gate_path="$1" expected="$2" label="$3" observed
  if ! observed="$(python3 -I -S -B - "$gate_path" <<'PY'
import hashlib
import os
import pathlib
import stat
import sys


def reject(message):
    raise SystemExit("stable gate digest rejected: " + message)


STABLE_FIELDS = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_nlink",
    "st_uid",
    "st_gid",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)


def same_identity(first, second):
    return all(getattr(first, field) == getattr(second, field) for field in STABLE_FIELDS)


def digest_stable_gate(path):
    try:
        path_before = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        reject(f"cannot inspect gate: {error}")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or nonblock is None:
        reject("platform lacks no-follow, nonblocking gate custody")
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as error:
        reject(f"cannot open gate without following links or blocking: {error}")
    digest = hashlib.sha256()
    try:
        opened = os.fstat(descriptor)
        if (
            resolved != path
            or stat.S_ISLNK(path_before.st_mode)
            or not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or opened.st_size <= 0
            or opened.st_size > 4 * 1024 * 1024
            or not same_identity(path_before, opened)
        ):
            reject("gate is noncanonical, non-regular, linked, empty, or oversized")
        captured = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            captured += len(chunk)
        descriptor_after = os.fstat(descriptor)
        path_after = path.lstat()
        resolved_after = path.resolve(strict=True)
    except OSError as error:
        reject(f"cannot read gate: {error}")
    finally:
        os.close(descriptor)
    if (
        captured != opened.st_size
        or resolved_after != resolved
        or not same_identity(opened, descriptor_after)
        or not same_identity(opened, path_after)
    ):
        reject("gate changed while hashed")
    return digest.hexdigest()


print(digest_stable_gate(pathlib.Path(sys.argv[1])))
PY
)"; then
    echo "$CHECK_NAME: $label could not be hashed under stable custody" >&2
    exit 1
  fi
  if [[ "$observed" != "$expected" ]]; then
    echo "$CHECK_NAME: $label digest changed: ${observed:-unavailable}" >&2
    exit 1
  fi
}
require_profile_input() {
  local profile_path="$1" label="$2"
  if [[ ! -f "$profile_path" || -L "$profile_path" ]]; then
    echo "$CHECK_NAME: selected $label absent, non-regular, or symbolic: $profile_path" >&2
    exit 1
  fi
}
require_gate_digest "$STRUCTURE_CHECK" "$STRUCTURE_CHECK_SHA256" "strict structure checker"
require_gate_digest "$STRUCTURE_SELF_TEST" "$STRUCTURE_SELF_TEST_SHA256" \
  "strict structure checker self-test"
require_gate_digest "$ID_VARIANCE_CHECK" "$ID_VARIANCE_CHECK_SHA256" \
  "strict trailer-ID variance checker"

python3 -I -S -B "$PANDOC_TEX_NORMALIZER_SELF_TEST"
python3 -O -I -S -B "$PANDOC_TEX_NORMALIZER_SELF_TEST"
bash --noprofile --norc "$BUILDER_SELF_TEST"
bash --noprofile --norc "$TAGPDF_COMPAT_SELF_TEST"
bash --noprofile --norc "$URI_CONTENTS_COMPAT_SELF_TEST"
bash --noprofile --norc "$FILESPEC_COMPAT_SELF_TEST"
python3 -I -B "$FIGURE_ASSET_CHECK"
python3 -O -I -B "$FIGURE_ASSET_CHECK"
python3 -I -B "$FIGURE_ASSET_SELF_TEST"
python3 -O -I -B "$FIGURE_ASSET_SELF_TEST"
python3 -I -B "$OPEN_FONT_REGENERATOR_SELF_TEST"
python3 -O -I -B "$OPEN_FONT_REGENERATOR_SELF_TEST"
python3 -I -B "$ID_VARIANCE_SELF_TEST"
python3 -O -I -B "$ID_VARIANCE_SELF_TEST"
python3 -I -S -B "$FONT_ROSTER_SELF_TEST"
python3 -O -I -S -B "$FONT_ROSTER_SELF_TEST"
python3 -I -B "$PROSE_CHECK"
python3 -O -I -B "$PROSE_CHECK"
python3 -I -B "$PROSE_SELF_TEST"
python3 -O -I -B "$PROSE_SELF_TEST"
python3 -I -B "$STRUCTURE_SELF_TEST" "$COMMITTED"
python3 -O -I -B "$STRUCTURE_SELF_TEST" "$COMMITTED"
require_gate_digest "$STRUCTURE_SELF_TEST" "$STRUCTURE_SELF_TEST_SHA256" \
  "strict structure checker self-test after execution"
python3 -I -B "$MODE_WIRING_SELF_TEST"
python3 -O -I -B "$MODE_WIRING_SELF_TEST"

HEADER="$ROOT/audit/formal/latex/mathematical-results-guide/header.tex"
for design_contract in \
    '\definecolor{PidNavy}{HTML}{2C3E50}' \
    '\definecolor{PidTeal}{HTML}{1F6968}' \
    '\definecolor{PidBronze}{HTML}{916400}' \
    '\definecolor{PidGold}{HTML}{DCA520}' \
    '\definecolor{PidPaper}{HTML}{F7F3E9}' \
    '{\Large\bfseries\color{PidNavy}}' \
    '{\large\bfseries\color{PidTeal}}'; do
  grep -Fq -- "$design_contract" "$HEADER" || {
    echo "$CHECK_NAME: source design contract absent: $design_contract" >&2
    exit 1
  }
done
if grep -Eq '\\fontsize\{(2[4-9]|[3-9][0-9])\}[^\n]*\\color\{PidTeal\}' "$HEADER"; then
  echo "$CHECK_NAME: PidTeal must not style a large title" >&2
  exit 1
fi

capture_cross_producer_tuple() {
  local capture_label="$1" tuple_output="$2"
  local pandoc_command lualatex_command kpsewhich_command
  pandoc_command="$(command -v pandoc)"
  lualatex_command="$(command -v lualatex)"
  kpsewhich_command="$(command -v kpsewhich)"
  if [[ -z "$pandoc_command" || -z "$lualatex_command" || -z "$kpsewhich_command" \
      || "$pandoc_command" == *$'\n'* || "$pandoc_command" == *$'\r'* \
      || "$lualatex_command" == *$'\n'* || "$lualatex_command" == *$'\r'* \
      || "$kpsewhich_command" == *$'\n'* || "$kpsewhich_command" == *$'\r'* ]]; then
    echo "$CHECK_NAME: $capture_label producer command selection is empty or multiline" >&2
    return 1
  fi
  if ! python3 -I -S -B - "$tuple_output" "$pandoc_command" \
      "$lualatex_command" "$kpsewhich_command" "$PATH" <<'PY'
import hashlib
import os
import pathlib
import selectors
import signal
import stat
import subprocess
import sys
import time


def reject(message):
    raise SystemExit("producer tuple rejected: " + message)


STABLE_FIELDS = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_nlink",
    "st_uid",
    "st_gid",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)


def same_identity(first, second):
    return all(getattr(first, field) == getattr(second, field) for field in STABLE_FIELDS)


def nonblocking_read_flags(label):
    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or nonblock is None:
        reject(f"platform lacks no-follow, nonblocking custody for {label}")
    return os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)


def terminate_probe(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=1.0)
    for stream in (process.stdout, process.stderr):
        if stream is not None:
            stream.close()


def run_probe(command, arguments, label, path_value, *, timeout_seconds=10.0, maximum=8192):
    if timeout_seconds <= 0 or maximum <= 0:
        reject(f"{label} probe bounds are invalid")
    try:
        process = subprocess.Popen(
            [command, *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={"PATH": path_value, "LC_ALL": "C", "LANG": "C"},
            start_new_session=True,
            close_fds=True,
        )
    except (OSError, ValueError) as error:
        reject(f"cannot start {label}: {error}")
    if process.stdout is None or process.stderr is None:
        terminate_probe(process)
        reject(f"{label} has no captured output pipes")
    selector = selectors.DefaultSelector()
    streams = (("stdout", process.stdout), ("stderr", process.stderr))
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    try:
        for stream_name, stream in streams:
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, stream_name)
        deadline = time.monotonic() + timeout_seconds
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                terminate_probe(process)
                reject(f"{label} exceeded its time bound")
            events = selector.select(remaining)
            if not events:
                terminate_probe(process)
                reject(f"{label} exceeded its time bound")
            for key, _ in events:
                stream_name = key.data
                try:
                    chunk = os.read(key.fileobj.fileno(), 65536)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffers[stream_name].extend(chunk)
                if len(buffers[stream_name]) > maximum:
                    terminate_probe(process)
                    reject(f"{label} exceeded its output bound")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            terminate_probe(process)
            reject(f"{label} exceeded its time bound")
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            terminate_probe(process)
            reject(f"{label} exceeded its time bound")
    finally:
        selector.close()
    process.stdout.close()
    process.stderr.close()
    if returncode != 0:
        reject(f"{label} exited with status {returncode}")
    if buffers["stderr"]:
        reject(f"{label} emitted stderr")
    return bytes(buffers["stdout"])


def decode_probe(stdout, label, *, first_line=False):
    if not stdout or len(stdout) > 8192 or b"\0" in stdout or b"\r" in stdout:
        reject(f"{label} output is empty, oversized, or malformed")
    try:
        text = stdout.decode("utf-8")
    except UnicodeDecodeError:
        reject(f"{label} output is not UTF-8")
    lines = text.splitlines()
    if first_line:
        if not lines or not lines[0] or "\t" in lines[0] or "=" in lines[0]:
            reject(f"{label} first line is malformed")
        return lines[0]
    if len(lines) != 1 or not lines[0] or "\t" in lines[0] or "=" in lines[0]:
        reject(f"{label} output is not exactly one safe line")
    return lines[0]


def snapshot(path_text, label, *, direct, executable, maximum):
    if "\n" in path_text or "\r" in path_text or "\t" in path_text or "=" in path_text:
        reject(f"{label} path is malformed")
    path = pathlib.Path(path_text)
    if not path.is_absolute() or path.as_posix() != path_text:
        reject(f"{label} path is not canonical absolute POSIX syntax")
    try:
        command_before = path.lstat()
        resolved = path.resolve(strict=True)
        resolved_before = resolved.lstat()
    except (OSError, RuntimeError) as error:
        reject(f"{label} cannot be resolved: {error}")
    if direct and resolved != path:
        reject(f"{label} has a symbolic or noncanonical component")
    if executable and not os.access(resolved, os.X_OK):
        reject(f"{label} is not executable")
    flags = nonblocking_read_flags(label)
    try:
        descriptor = os.open(resolved, flags)
    except OSError as error:
        reject(f"{label} cannot be opened without following links or blocking: {error}")
    digest = hashlib.sha256()
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or not same_identity(resolved_before, opened)
        ):
            reject(f"{label} is not a singly linked regular file")
        if opened.st_size <= 0 or opened.st_size > maximum:
            reject(f"{label} size is outside its bound")
        captured = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            captured += len(chunk)
        descriptor_after = os.fstat(descriptor)
        resolved_after = resolved.lstat()
        command_after = path.lstat()
        resolved_again = path.resolve(strict=True)
    except OSError as error:
        reject(f"{label} could not be captured: {error}")
    finally:
        os.close(descriptor)
    if (
        captured != opened.st_size
        or resolved_again != resolved
        or not same_identity(opened, descriptor_after)
        or not same_identity(opened, resolved_after)
        or not same_identity(command_before, command_after)
    ):
        reject(f"{label} changed while captured")
    return resolved.as_posix(), opened, digest.hexdigest()


def require_same_snapshot(label, first, second):
    first_path, first_stat, first_digest = first
    second_path, second_stat, second_digest = second
    if (
        first_path != second_path
        or first_digest != second_digest
        or not same_identity(first_stat, second_stat)
    ):
        reject(f"{label} changed across its probe")


def same_object(first, second):
    return first.st_dev == second.st_dev and first.st_ino == second.st_ino


def private_parent(parent_stat):
    return (
        stat.S_ISDIR(parent_stat.st_mode)
        and parent_stat.st_uid == os.geteuid()
        and stat.S_IMODE(parent_stat.st_mode) & 0o077 == 0
    )


def publish_tuple(output, payload):
    if (
        not output.is_absolute()
        or output.as_posix() != sys.argv[1]
        or output.name in ("", ".", "..")
    ):
        reject("tuple output is not a canonical absolute leaf path")
    parent = output.parent
    try:
        parent_before = parent.lstat()
        parent_resolved = parent.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        reject(f"cannot inspect tuple output parent: {error}")
    directory = getattr(os, "O_DIRECTORY", None)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if directory is None or nofollow is None:
        reject("platform lacks no-follow directory custody for tuple publication")
    if parent_resolved != parent or not private_parent(parent_before):
        reject("tuple output parent is noncanonical or not private to this identity")
    parent_flags = (
        os.O_RDONLY | directory | nofollow | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        parent_descriptor = os.open(parent, parent_flags)
    except OSError as error:
        reject(f"cannot open tuple output parent without following links: {error}")
    descriptor = None
    created_stat = None
    published = False
    try:
        parent_opened = os.fstat(parent_descriptor)
        parent_path_opened = parent.lstat()
        if (
            not private_parent(parent_opened)
            or not same_object(parent_before, parent_opened)
            or not same_object(parent_opened, parent_path_opened)
            or parent.resolve(strict=True) != parent_resolved
        ):
            reject("tuple output parent changed while it was opened")
        try:
            os.stat(output.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            pass
        except OSError as error:
            reject(f"cannot inspect fresh tuple output leaf: {error}")
        else:
            reject("tuple output leaf already exists")
        leaf_flags = (
            os.O_RDWR
            | os.O_CREAT
            | os.O_EXCL
            | nofollow
            | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            descriptor = os.open(
                output.name,
                leaf_flags,
                0o600,
                dir_fd=parent_descriptor,
            )
        except (OSError, TypeError) as error:
            reject(f"cannot create tuple output through held parent: {error}")
        created_stat = os.fstat(descriptor)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                reject("tuple output write made no progress")
            view = view[written:]
        os.fsync(descriptor)
        os.lseek(descriptor, 0, os.SEEK_SET)
        chunks = []
        remaining = len(payload) + 1
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        reread = b"".join(chunks)
        output_stat = os.fstat(descriptor)
        output_path_stat = os.stat(
            output.name, dir_fd=parent_descriptor, follow_symlinks=False
        )
        parent_after = os.fstat(parent_descriptor)
        parent_path_after = parent.lstat()
        output_absolute_after = output.lstat()
        if (
            parent.resolve(strict=True) != parent_resolved
            or not private_parent(parent_after)
            or not same_object(parent_opened, parent_after)
            or not same_object(parent_after, parent_path_after)
            or not same_object(output_stat, output_path_stat)
            or not same_object(output_stat, output_absolute_after)
            or not stat.S_ISREG(output_stat.st_mode)
            or output_stat.st_nlink != 1
            or output_stat.st_uid != os.geteuid()
            or stat.S_IMODE(output_stat.st_mode) != 0o600
            or output_stat.st_size != len(payload)
            or reread != payload
        ):
            reject("tuple output or its parent changed while it was published")
        published = True
    except (OSError, RuntimeError) as error:
        reject(f"cannot publish tuple output: {error}")
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if not published and created_stat is not None:
            try:
                rollback_stat = os.stat(
                    output.name,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            except OSError:
                pass
            else:
                if same_object(created_stat, rollback_stat):
                    try:
                        os.unlink(output.name, dir_fd=parent_descriptor)
                    except OSError:
                        pass
        os.close(parent_descriptor)


output = pathlib.Path(sys.argv[1])
pandoc_real, pandoc_stat, pandoc_sha = snapshot(
    sys.argv[2], "Pandoc", direct=True, executable=True, maximum=512 * 1024 * 1024
)
lualatex_real, lualatex_stat, lualatex_sha = snapshot(
    sys.argv[3], "LuaLaTeX", direct=False, executable=True, maximum=64 * 1024 * 1024
)
kpsewhich_real, kpsewhich_stat, kpsewhich_sha = snapshot(
    sys.argv[4], "kpsewhich", direct=True, executable=True, maximum=64 * 1024 * 1024
)
probe_path = sys.argv[5]
pandoc_version = decode_probe(
    run_probe(pandoc_real, ("--version",), "Pandoc version", probe_path),
    "Pandoc version",
    first_line=True,
)
renderer_version = decode_probe(
    run_probe(lualatex_real, ("--version",), "LuaLaTeX version", probe_path),
    "LuaLaTeX version",
    first_line=True,
)
texmfsysvar = decode_probe(
    run_probe(
        kpsewhich_real,
        ("-var-value=TEXMFSYSVAR",),
        "kpsewhich TEXMFSYSVAR",
        probe_path,
    ),
    "kpsewhich TEXMFSYSVAR",
)
format_path_text = decode_probe(
    run_probe(
        kpsewhich_real,
        (
            "--engine=luahbtex",
            "--progname=lualatex",
            "--must-exist",
            "--format=fmt",
            "lualatex.fmt",
        ),
        "kpsewhich LuaLaTeX format",
        probe_path,
    ),
    "kpsewhich LuaLaTeX format",
)
require_same_snapshot(
    "Pandoc",
    (pandoc_real, pandoc_stat, pandoc_sha),
    snapshot(
        sys.argv[2],
        "Pandoc",
        direct=True,
        executable=True,
        maximum=512 * 1024 * 1024,
    ),
)
require_same_snapshot(
    "LuaLaTeX",
    (lualatex_real, lualatex_stat, lualatex_sha),
    snapshot(
        sys.argv[3],
        "LuaLaTeX",
        direct=False,
        executable=True,
        maximum=64 * 1024 * 1024,
    ),
)
require_same_snapshot(
    "kpsewhich",
    (kpsewhich_real, kpsewhich_stat, kpsewhich_sha),
    snapshot(
        sys.argv[4],
        "kpsewhich",
        direct=True,
        executable=True,
        maximum=64 * 1024 * 1024,
    ),
)
format_path = pathlib.Path(format_path_text)
expected_format_path = pathlib.Path(texmfsysvar) / "web2c/luahbtex/lualatex.fmt"
if format_path != expected_format_path:
    reject("selected format is not the exact TEXMFSYSVAR LuaHBTeX leaf")
format_real, format_stat, format_sha = snapshot(
    format_path_text,
    "LuaLaTeX format",
    direct=True,
    executable=False,
    maximum=128 * 1024 * 1024,
)
format_mode = stat.S_IMODE(format_stat.st_mode)
if (
    format_mode & (stat.S_IWGRP | stat.S_IWOTH)
    or (format_stat.st_uid == os.geteuid() and format_mode & stat.S_IWUSR)
    or os.access(format_real, os.W_OK)
):
    reject("LuaLaTeX format is writable by the invoking identity or a broad class")
require_same_snapshot(
    "LuaLaTeX format",
    (format_real, format_stat, format_sha),
    snapshot(
        format_path_text,
        "LuaLaTeX format",
        direct=True,
        executable=False,
        maximum=128 * 1024 * 1024,
    ),
)
records = (
    ("pandoc_command", sys.argv[2]),
    ("pandoc_realpath", pandoc_real),
    ("pandoc_version", pandoc_version),
    ("pandoc_bytes", str(pandoc_stat.st_size)),
    ("pandoc_sha256", pandoc_sha),
    ("lualatex_command", sys.argv[3]),
    ("renderer_realpath", lualatex_real),
    ("renderer_version", renderer_version),
    ("renderer_bytes", str(lualatex_stat.st_size)),
    ("renderer_sha256", lualatex_sha),
    ("kpsewhich_command", sys.argv[4]),
    ("kpsewhich_realpath", kpsewhich_real),
    ("kpsewhich_bytes", str(kpsewhich_stat.st_size)),
    ("kpsewhich_sha256", kpsewhich_sha),
    ("texmfsysvar", texmfsysvar),
    ("format_path", format_real),
    ("format_kind", "regular"),
    ("format_mode", format(format_mode, "04o")),
    ("format_nlink", str(format_stat.st_nlink)),
    ("format_uid", str(format_stat.st_uid)),
    ("format_gid", str(format_stat.st_gid)),
    ("format_writable", "no"),
    ("format_bytes", str(format_stat.st_size)),
    ("format_sha256", format_sha),
)
payload = "".join(f"{key}\t{value}\n" for key, value in records).encode("utf-8")
publish_tuple(output, payload)
PY
  then
    echo "$CHECK_NAME: $capture_label producer tuple could not be captured" >&2
    return 1
  fi
}

select_cross_profile_from_tuple() {
  python3 -I -S -B - "$1" \
    "$HOSTED_PROFILE_ID" "$HOSTED_PANDOC_VERSION" "$HOSTED_PANDOC_SHA256" \
    "$HOSTED_RENDERER_REALPATH" "$HOSTED_RENDERER_VERSION" \
    "$HOSTED_RENDERER_SHA256" "$HOSTED_TEXMFSYSVAR" "$HOSTED_FORMAT_PATH" \
    "$LEGACY_PROFILE_ID" "$LEGACY_PANDOC_VERSION" "$LEGACY_PANDOC_REALPATH" \
    "$LEGACY_PANDOC_SHA256" "$LEGACY_RENDERER_REALPATH" \
    "$LEGACY_RENDERER_VERSION" "$LEGACY_RENDERER_SHA256" \
    "$LEGACY_TEXMFSYSVAR" "$LEGACY_FORMAT_PATH" "$LEGACY_FORMAT_BYTES" \
    "$LEGACY_FORMAT_SHA256" <<'PY'
import base64
import os
import pathlib
import re
import stat
import sys


def reject(message):
    raise SystemExit("producer profile rejected: " + message)


STABLE_FIELDS = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_nlink",
    "st_uid",
    "st_gid",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)


def same_identity(first, second):
    return all(getattr(first, field) == getattr(second, field) for field in STABLE_FIELDS)


def read_stable_tuple(tuple_path):
    try:
        path_before = tuple_path.lstat()
        resolved = tuple_path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        reject(f"cannot inspect tuple: {error}")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or nonblock is None:
        reject("platform lacks no-follow, nonblocking tuple custody")
    try:
        descriptor = os.open(
            tuple_path,
            os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as error:
        reject(f"cannot open tuple without following links or blocking: {error}")
    try:
        opened = os.fstat(descriptor)
        if (
            resolved != tuple_path
            or stat.S_ISLNK(path_before.st_mode)
            or not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or opened.st_size <= 0
            or opened.st_size > 16384
            or not same_identity(path_before, opened)
        ):
            reject("tuple is noncanonical, non-regular, linked, empty, or oversized")
        chunks = []
        remaining = 16385
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        descriptor_after = os.fstat(descriptor)
        path_after = tuple_path.lstat()
        resolved_after = tuple_path.resolve(strict=True)
    except OSError as error:
        reject(f"cannot read tuple: {error}")
    finally:
        os.close(descriptor)
    if (
        resolved_after != resolved
        or not same_identity(opened, descriptor_after)
        or not same_identity(opened, path_after)
        or len(raw) != opened.st_size
    ):
        reject("tuple changed while selected")
    return raw, opened


tuple_path = pathlib.Path(sys.argv[1])
raw, before = read_stable_tuple(tuple_path)
if len(raw) != before.st_size or not raw.endswith(b"\n") or b"\0" in raw or b"\r" in raw:
    reject("tuple byte framing is malformed")
try:
    lines = raw.decode("utf-8").splitlines()
except UnicodeDecodeError:
    reject("tuple is not UTF-8")
expected_keys = (
    "pandoc_command",
    "pandoc_realpath",
    "pandoc_version",
    "pandoc_bytes",
    "pandoc_sha256",
    "lualatex_command",
    "renderer_realpath",
    "renderer_version",
    "renderer_bytes",
    "renderer_sha256",
    "kpsewhich_command",
    "kpsewhich_realpath",
    "kpsewhich_bytes",
    "kpsewhich_sha256",
    "texmfsysvar",
    "format_path",
    "format_kind",
    "format_mode",
    "format_nlink",
    "format_uid",
    "format_gid",
    "format_writable",
    "format_bytes",
    "format_sha256",
)
records = {}
if len(lines) != len(expected_keys):
    reject(f"tuple has {len(lines)} rows; expected {len(expected_keys)}")
for index, (line, expected_key) in enumerate(zip(lines, expected_keys, strict=True), 1):
    if line.count("\t") != 1:
        reject(f"tuple row {index} is not one key/value pair")
    key, value = line.split("\t", 1)
    if key != expected_key or not value or key in records or "=" in value:
        reject(f"tuple row {index} has a wrong, duplicate, or unsafe field")
    records[key] = value

for key in (
    "pandoc_bytes",
    "renderer_bytes",
    "kpsewhich_bytes",
    "format_nlink",
    "format_uid",
    "format_gid",
    "format_bytes",
):
    if re.fullmatch(r"0|[1-9][0-9]*", records[key]) is None:
        reject(f"{key} is not a canonical nonnegative integer")
for key in ("pandoc_bytes", "renderer_bytes", "kpsewhich_bytes", "format_bytes"):
    if int(records[key]) <= 0:
        reject(f"{key} is not positive")
for key in (
    "pandoc_sha256",
    "renderer_sha256",
    "kpsewhich_sha256",
    "format_sha256",
):
    if re.fullmatch(r"[0-9a-f]{64}", records[key]) is None:
        reject(f"{key} is not canonical SHA-256")
if re.fullmatch(r"[0-7]{4}", records["format_mode"]) is None:
    reject("format_mode is not four-digit octal")
format_mode = int(records["format_mode"], 8)
format_uid = int(records["format_uid"])
format_secure = (
    records["format_kind"] == "regular"
    and records["format_nlink"] == "1"
    and records["format_writable"] == "no"
    and (format_mode & 0o022) == 0
    and not (format_uid == os.geteuid() and (format_mode & 0o200))
)

hosted = {
    "profile": sys.argv[2],
    "pandoc_version": sys.argv[3],
    "pandoc_sha256": sys.argv[4],
    "renderer_realpath": sys.argv[5],
    "renderer_version": sys.argv[6],
    "renderer_sha256": sys.argv[7],
    "texmfsysvar": sys.argv[8],
    "format_path": sys.argv[9],
}
legacy = {
    "profile": sys.argv[10],
    "pandoc_version": sys.argv[11],
    "pandoc_realpath": sys.argv[12],
    "pandoc_sha256": sys.argv[13],
    "renderer_realpath": sys.argv[14],
    "renderer_version": sys.argv[15],
    "renderer_sha256": sys.argv[16],
    "texmfsysvar": sys.argv[17],
    "format_path": sys.argv[18],
    "format_bytes": sys.argv[19],
    "format_sha256": sys.argv[20],
}
matches = []
if (
    # Current hosted format bytes vary after package-level format regeneration.
    # They are therefore run evidence, not profile-shopping selectors.  The
    # selected route is safe only because its checker separately binds the
    # complete candidate to one retained raw fixture (apart from strict IDs).
    hosted["profile"]
    and records["pandoc_command"] == records["pandoc_realpath"]
    and records["pandoc_version"] == hosted["pandoc_version"]
    and records["pandoc_sha256"] == hosted["pandoc_sha256"]
    and records["lualatex_command"] == "/usr/bin/lualatex"
    and records["renderer_realpath"] == hosted["renderer_realpath"]
    and records["renderer_version"] == hosted["renderer_version"]
    and records["renderer_sha256"] == hosted["renderer_sha256"]
    and records["kpsewhich_command"] == "/usr/bin/kpsewhich"
    and records["kpsewhich_realpath"] == "/usr/bin/kpsewhich"
    and records["texmfsysvar"] == hosted["texmfsysvar"]
    and records["format_path"] == hosted["format_path"]
    and format_secure
):
    matches.append(hosted["profile"])
if (
    legacy["profile"]
    and legacy["format_bytes"]
    and legacy["format_sha256"]
    and records["pandoc_command"] == legacy["pandoc_realpath"]
    and records["pandoc_realpath"] == legacy["pandoc_realpath"]
    and records["pandoc_version"] == legacy["pandoc_version"]
    and records["pandoc_sha256"] == legacy["pandoc_sha256"]
    and records["lualatex_command"] == "/usr/bin/lualatex"
    and records["renderer_realpath"] == legacy["renderer_realpath"]
    and records["renderer_version"] == legacy["renderer_version"]
    and records["renderer_sha256"] == legacy["renderer_sha256"]
    and records["kpsewhich_command"] == "/usr/bin/kpsewhich"
    and records["kpsewhich_realpath"] == "/usr/bin/kpsewhich"
    and records["texmfsysvar"] == legacy["texmfsysvar"]
    and records["format_path"] == legacy["format_path"]
    and records["format_bytes"] == legacy["format_bytes"]
    and records["format_sha256"] == legacy["format_sha256"]
    and format_secure
):
    matches.append(legacy["profile"])
if len(matches) != 1 or not matches[0]:
    reject(f"tuple matched {len(matches)} supported profiles")
print(f"{matches[0]}\t{base64.b64encode(raw).decode('ascii')}")
PY
}

TMP_BASE="$(CDPATH='' cd -- "${TMPDIR:-/tmp}" && pwd -P)"
if [[ "$TMP_BASE" == "/" ]]; then
  echo "$CHECK_NAME: temporary root must not be filesystem /" >&2
  exit 1
fi
BUILD_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-mathematical-results-guide-check.XXXXXX")"
cleanup() {
  case "$BUILD_ROOT" in
    "$TMP_BASE"/pid-rs-mathematical-results-guide-check.*) rm -rf -- "$BUILD_ROOT" ;;
    *) echo "$CHECK_NAME: refusing unexpected cleanup path: $BUILD_ROOT" >&2 ;;
  esac
}
trap cleanup EXIT INT TERM

BUILT="$BUILD_ROOT/built.pdf"
CROSS_PROFILE=''
PRODUCER_TUPLE_BEFORE="$BUILD_ROOT/producer-before.tsv"
PRODUCER_TUPLE_AFTER="$BUILD_ROOT/producer-after.tsv"
# CROSS_PROFILE_SELECTION_BEGIN
if [[ "$MODE" == "--cross-toolchain" ]]; then
  capture_cross_producer_tuple before "$PRODUCER_TUPLE_BEFORE"
  CROSS_SELECTION="$(select_cross_profile_from_tuple "$PRODUCER_TUPLE_BEFORE")"
  IFS=$'\t' read -r CROSS_PROFILE CROSS_TUPLE_BASE64 CROSS_EXTRA \
    <<<"$CROSS_SELECTION"
  if [[ -z "$CROSS_PROFILE" || "$CROSS_PROFILE" == *$'\n'* || "$CROSS_PROFILE" == *$'\r'* \
      || -z "$CROSS_TUPLE_BASE64" \
      || ! "$CROSS_TUPLE_BASE64" =~ ^[A-Za-z0-9+/]+={0,2}$ || -n "$CROSS_EXTRA" ]]; then
    echo "$CHECK_NAME: cross-toolchain producer evidence is malformed" >&2
    exit 1
  fi
  case "$CROSS_PROFILE" in
    "$HOSTED_PROFILE_ID")
      require_profile_input "$HOSTED_RAW_CHECK" "hosted raw-profile checker"
      require_profile_input "$HOSTED_RAW_SELF_TEST" "hosted raw-profile checker self-test"
      require_profile_input "$RETAINED_HOSTED_RAW_FIXTURE" "hosted raw-profile fixture"
      require_profile_input "$HOSTED_RAW_PROFILE_RECEIPT" "hosted raw-profile provenance receipt"
      require_gate_digest "$HOSTED_RAW_CHECK" "$HOSTED_RAW_CHECK_SHA256" \
        "hosted raw-profile checker"
      require_gate_digest "$HOSTED_RAW_SELF_TEST" "$HOSTED_RAW_SELF_TEST_SHA256" \
        "hosted raw-profile checker self-test"
      require_gate_digest "$HOSTED_RAW_PROFILE_RECEIPT" \
        "$HOSTED_RAW_PROFILE_RECEIPT_SHA256" "hosted raw-profile provenance receipt"
      python3 -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source hosted
      python3 -O -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source hosted
      python3 -I -B "$HOSTED_RAW_SELF_TEST" "$RETAINED_HOSTED_RAW_FIXTURE"
      python3 -O -I -B "$HOSTED_RAW_SELF_TEST" "$RETAINED_HOSTED_RAW_FIXTURE"
      require_gate_digest "$HOSTED_RAW_CHECK" "$HOSTED_RAW_CHECK_SHA256" \
        "hosted raw-profile checker after selected execution"
      require_gate_digest "$HOSTED_RAW_SELF_TEST" "$HOSTED_RAW_SELF_TEST_SHA256" \
        "hosted raw-profile checker self-test after selected execution"
      require_gate_digest "$HOSTED_RAW_PROFILE_RECEIPT" \
        "$HOSTED_RAW_PROFILE_RECEIPT_SHA256" \
        "hosted raw-profile provenance receipt after selected execution"
      ;;
    "$LEGACY_PROFILE_ID")
      require_profile_input "$FONT_ALPHA_CHECK" "typed font-alpha comparator"
      require_profile_input "$FONT_ALPHA_SELF_TEST" "typed font-alpha comparator self-test"
      require_profile_input "$RETAINED_FONT_ALPHA_FIXTURE" "legacy font-alpha fixture"
      require_profile_input "$PANDOC_PORTABILITY_RECEIPT_CHECK" \
        "historical Pandoc portability receipt checker"
      require_profile_input "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST" \
        "historical Pandoc portability receipt checker self-test"
      require_profile_input "$LEGACY_PANDOC_PORTABILITY_RECEIPT" \
        "historical Pandoc portability receipt"
      require_profile_input "$TRAILER_ID_OBSERVATION_CHECK" \
        "historical trailer-ID observation checker"
      require_profile_input "$TRAILER_ID_OBSERVATION_SELF_TEST" \
        "historical trailer-ID observation checker self-test"
      require_profile_input "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT" \
        "historical trailer-ID observation receipt"
      require_gate_digest "$FONT_ALPHA_CHECK" "$FONT_ALPHA_CHECK_SHA256" \
        "typed font-alpha comparator"
      require_gate_digest "$FONT_ALPHA_SELF_TEST" "$FONT_ALPHA_SELF_TEST_SHA256" \
        "typed font-alpha comparator self-test"
      require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_CHECK" \
        "$PANDOC_PORTABILITY_RECEIPT_CHECK_SHA256" \
        "historical Pandoc portability receipt checker"
      require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST" \
        "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST_SHA256" \
        "historical Pandoc portability receipt checker self-test"
      require_gate_digest "$LEGACY_PANDOC_PORTABILITY_RECEIPT" \
        "$LEGACY_PANDOC_PORTABILITY_RECEIPT_SHA256" \
        "historical Pandoc portability receipt"
      require_gate_digest "$TRAILER_ID_OBSERVATION_CHECK" \
        "$TRAILER_ID_OBSERVATION_CHECK_SHA256" \
        "historical trailer-ID observation checker"
      require_gate_digest "$TRAILER_ID_OBSERVATION_SELF_TEST" \
        "$TRAILER_ID_OBSERVATION_SELF_TEST_SHA256" \
        "historical trailer-ID observation checker self-test"
      require_gate_digest "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT" \
        "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT_SHA256" \
        "historical trailer-ID observation receipt"
      python3 -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source legacy
      python3 -O -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source legacy
      python3 -I -B "$PANDOC_PORTABILITY_RECEIPT_CHECK"
      python3 -O -I -B "$PANDOC_PORTABILITY_RECEIPT_CHECK"
      python3 -I -B "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST"
      python3 -O -I -B "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST"
      python3 -I -B "$TRAILER_ID_OBSERVATION_CHECK"
      python3 -O -I -B "$TRAILER_ID_OBSERVATION_CHECK"
      python3 -I -B "$TRAILER_ID_OBSERVATION_SELF_TEST"
      python3 -O -I -B "$TRAILER_ID_OBSERVATION_SELF_TEST"
      python3 -I -B "$FONT_ALPHA_SELF_TEST" "$COMMITTED" \
        "$RETAINED_FONT_ALPHA_FIXTURE"
      python3 -O -I -B "$FONT_ALPHA_SELF_TEST" "$COMMITTED" \
        "$RETAINED_FONT_ALPHA_FIXTURE"
      require_gate_digest "$FONT_ALPHA_CHECK" "$FONT_ALPHA_CHECK_SHA256" \
        "typed font-alpha comparator after selected execution"
      require_gate_digest "$FONT_ALPHA_SELF_TEST" "$FONT_ALPHA_SELF_TEST_SHA256" \
        "typed font-alpha comparator self-test after selected execution"
      require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_CHECK" \
        "$PANDOC_PORTABILITY_RECEIPT_CHECK_SHA256" \
        "historical Pandoc portability receipt checker after selected execution"
      require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST" \
        "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST_SHA256" \
        "historical Pandoc portability receipt checker self-test after selected execution"
      require_gate_digest "$LEGACY_PANDOC_PORTABILITY_RECEIPT" \
        "$LEGACY_PANDOC_PORTABILITY_RECEIPT_SHA256" \
        "historical Pandoc portability receipt after selected execution"
      require_gate_digest "$TRAILER_ID_OBSERVATION_CHECK" \
        "$TRAILER_ID_OBSERVATION_CHECK_SHA256" \
        "historical trailer-ID observation checker after selected execution"
      require_gate_digest "$TRAILER_ID_OBSERVATION_SELF_TEST" \
        "$TRAILER_ID_OBSERVATION_SELF_TEST_SHA256" \
        "historical trailer-ID observation checker self-test after selected execution"
      require_gate_digest "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT" \
        "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT_SHA256" \
        "historical trailer-ID observation receipt after selected execution"
      ;;
    *)
      echo "$CHECK_NAME: internal unsupported cross-toolchain profile: $CROSS_PROFILE" >&2
      exit 1
      ;;
  esac
fi
# CROSS_PROFILE_SELECTION_END
PID_RS_PDF_TMPDIR="$BUILD_ROOT" bash --noprofile --norc "$BUILDER" "$MODE" "$BUILT" \
  >"$BUILD_ROOT/build.stdout" 2>"$BUILD_ROOT/build.stderr" || {
    cat "$BUILD_ROOT/build.stdout" "$BUILD_ROOT/build.stderr" >&2
    exit 1
  }
if [[ "$MODE" == "--cross-toolchain" ]]; then
  capture_cross_producer_tuple after "$PRODUCER_TUPLE_AFTER"
  CROSS_SELECTION_AFTER="$(select_cross_profile_from_tuple "$PRODUCER_TUPLE_AFTER")"
  IFS=$'\t' read -r CROSS_PROFILE_AFTER CROSS_TUPLE_BASE64_AFTER \
    CROSS_EXTRA_AFTER <<<"$CROSS_SELECTION_AFTER"
  if [[ "$CROSS_PROFILE_AFTER" != "$CROSS_PROFILE" \
      || "$CROSS_TUPLE_BASE64_AFTER" != "$CROSS_TUPLE_BASE64" \
      || -n "$CROSS_EXTRA_AFTER" ]]; then
    echo "$CHECK_NAME: cross-toolchain producer tuple changed during the build" >&2
    exit 1
  fi
fi
if [[ -s "$BUILD_ROOT/build.stderr" ]]; then
  cat "$BUILD_ROOT/build.stderr" >&2
  echo "$CHECK_NAME: builder emitted stderr" >&2
  exit 1
fi
if [[ "$MODE" == "--cross-toolchain" ]]; then
  cat "$BUILD_ROOT/build.stdout"
fi

validate_pdf() {
  local label="$1" pdf="$2" structure_relation="$3"
  local info="$BUILD_ROOT/$label.info" fonts="$BUILD_ROOT/$label.fonts"
  local font_roster="$BUILD_ROOT/$label.font-roster"
  local optimized_font_roster="$BUILD_ROOT/$label.font-roster-optimized"
  local text="$BUILD_ROOT/$label.txt"
  local observed_urls="$BUILD_ROOT/$label.observed-urls"
  local observed_navigation="$BUILD_ROOT/$label.observed-navigation"
  local optimized_urls="$BUILD_ROOT/$label.optimized-urls"
  local optimized_navigation="$BUILD_ROOT/$label.optimized-navigation"
  local expected_urls="$BUILD_ROOT/$label.expected-urls"
  LC_ALL=C pdfinfo "$pdf" >"$info" 2>"$BUILD_ROOT/$label.info.stderr"
  LC_ALL=C pdffonts "$pdf" >"$fonts" 2>"$BUILD_ROOT/$label.fonts.stderr"
  LC_ALL=C pdftotext -layout "$pdf" "$text" 2>"$BUILD_ROOT/$label.text.stderr"
  local parser_stderr
  for parser_stderr in "$BUILD_ROOT/$label.info.stderr" "$BUILD_ROOT/$label.fonts.stderr" \
      "$BUILD_ROOT/$label.text.stderr"; do
    if [[ -s "$parser_stderr" ]]; then
      cat "$parser_stderr" >&2
      echo "$CHECK_NAME: $label caused PDF parser diagnostics" >&2
      exit 1
    fi
  done
  if ! python3 -I -S -B "$FONT_ROSTER_CHECK" "$fonts" >"$font_roster" \
      2>"$BUILD_ROOT/$label.font-roster.stderr"; then
    cat "$BUILD_ROOT/$label.font-roster.stderr" >&2
    echo "$CHECK_NAME: $label violates the final open-font roster contract" >&2
    exit 1
  fi
  if [[ -s "$BUILD_ROOT/$label.font-roster.stderr" ]]; then
    cat "$BUILD_ROOT/$label.font-roster.stderr" >&2
    echo "$CHECK_NAME: $label font-roster validator emitted stderr" >&2
    exit 1
  fi
  if ! python3 -O -I -S -B "$FONT_ROSTER_CHECK" "$fonts" >"$optimized_font_roster" \
      2>"$BUILD_ROOT/$label.font-roster-optimized.stderr"; then
    cat "$BUILD_ROOT/$label.font-roster-optimized.stderr" >&2
    echo "$CHECK_NAME: optimized Python rejected the $label final font roster" >&2
    exit 1
  fi
  if [[ -s "$BUILD_ROOT/$label.font-roster-optimized.stderr" ]]; then
    cat "$BUILD_ROOT/$label.font-roster-optimized.stderr" >&2
    echo "$CHECK_NAME: optimized $label font-roster validator emitted stderr" >&2
    exit 1
  fi
  if ! cmp -s "$font_roster" "$optimized_font_roster"; then
    echo "$CHECK_NAME: $label font roster differs under optimized Python" >&2
    exit 1
  fi
  local pages
  pages="$(awk '/^Pages:/ {print $2}' "$info")"
  if [[ ! "$pages" =~ ^[0-9]+$ || "$pages" -lt 14 || "$pages" -gt 60 ]]; then
    echo "$CHECK_NAME: $label has implausible page count: ${pages:-missing}" >&2
    exit 1
  fi
  grep -Eq '^Page size:[[:space:]]+595\.[0-9]+ x 841\.[0-9]+ pts \(A4\)$' "$info" || {
    echo "$CHECK_NAME: $label is not A4" >&2
    exit 1
  }
  grep -Eq '^Tagged:[[:space:]]+yes$' "$info" || {
    echo "$CHECK_NAME: $label lacks a PDF structure tree" >&2
    exit 1
  }
  grep -Eq '^Suspects:[[:space:]]+no$' "$info" || {
    echo "$CHECK_NAME: $label is structurally suspect" >&2
    exit 1
  }
  grep -Eq '^Form:[[:space:]]+none$' "$info" || {
    echo "$CHECK_NAME: $label contains an interactive form" >&2
    exit 1
  }
  grep -Eq '^JavaScript:[[:space:]]+no$' "$info" || {
    echo "$CHECK_NAME: $label contains JavaScript" >&2
    exit 1
  }
  grep -Eq '^Encrypted:[[:space:]]+no$' "$info" || {
    echo "$CHECK_NAME: $label is encrypted" >&2
    exit 1
  }
  grep -Eq '^Page rot:[[:space:]]+0$' "$info" || {
    echo "$CHECK_NAME: $label has a rotated page" >&2
    exit 1
  }
  grep -Eq '^PDF version:[[:space:]]+1[.]7$' "$info" || {
    echo "$CHECK_NAME: $label is not PDF 1.7" >&2
    exit 1
  }
  for sentinel in \
      'Non-authoritative guide' \
      'Five distinct lanes' \
      'Five lanes. No silent transfer.' \
      'Three different counts for three different objects' \
      'Nine result families' \
      'Four evidence questions' \
      'Fixed finite-alphabet plug-in convergence' \
      'Support-change-tolerant averaged-Sx continuity' \
      'Dependency-color concentration' \
      'Exact two-source categorical-Sx assurance' \
      '20,348' \
      '2,197,584' \
      'Represented-binary64 and quantizer assurance' \
      'repository/publication integration remains NO-GO' \
      'A proved population-level transfer' \
      'repository-derived conditional lemma, catalogued as project-defined' \
      'common-geodesic-radius event ratio converges to an expression with the algebraic form of' \
      "Ehrlich et al.'s bivariate analytic formula." \
      'manifold small-ball lemma. It is not a new PID functional' \
      'population lemma [R] and boundary' \
      'Require the laws to admit the following density' \
      'essentially bounded on a neighbourhood' \
      'both density sums in the following ratio are strictly positive.' \
      'The proof needs only the two displayed' \
      'overlap conditions. Local essential boundedness is a' \
      'convenient sufficient condition, not a necessary one.' \
      'discarded overlap terms are' \
      'retained union scales' \
      'Why the displayed smooth marginals do not suffice' \
      'Riemannian arclength is Lebesgue measure' \
      'parameter Clayton form at a fixed parameter' \
      'used here as an ordinary copula, with no' \
      'survival-time semantics. This form is equivalent' \
      'Clayton (1978) for the original survival-association model' \
      "normalization despite the density's corner singularity" \
      'the full density is' \
      'one-source, target, and target-source density versions continuous' \
      'positive-measure open sets in every neighbourhood.' \
      'pair density is essentially unbounded' \
      'near the origin because' \
      'FIRST-ORDER OVERLAP TEST' \
      'conditional limit + boundary test' \
      'does not prove that pair local boundedness is necessary.' \
      'some replacement condition must control the overlap.' \
      'Gauge and dimension boundary' \
      'both branch-one coefficients are' \
      'positive, branch one dominates.' \
      'If either coefficient vanishes, continuity alone does not determine which' \
      'branch dominates or its replacement rate.' \
      'Equal numeric source radii are therefore a gauge choice.' \
      'They do not supply this manifold-domain theorem.' \
      'The lemma proves no adaptive-kNN consistency' \
      'expectation interchange, PID-atom property' \
      'a generic metric-kNN theorem does not transfer.' \
      'These workflows preserve evidence'; do
    grep -Fiq -- "$sentinel" "$text" || {
      echo "$CHECK_NAME: $label lacks rendered sentinel: $sentinel" >&2
      exit 1
    }
  done
  if grep -Fiq -- 'project-derived' "$text"; then
    echo "$CHECK_NAME: $label uses the nonexistent project-derived provenance class" >&2
    exit 1
  fi
  if grep -Fq $'\357\277\275' "$text"; then
    echo "$CHECK_NAME: $label contains a Unicode replacement character" >&2
    exit 1
  fi
  local raw_fragment
  for raw_fragment in '$$' '\\log' '\\mathcal' '\\left' '\\right' '\\sum' '\\cdot' \
      '\\alpha' '\\forall' '\\exists' '\\operatorname'; do
    if grep -Fq -- "$raw_fragment" "$text"; then
      echo "$CHECK_NAME: $label exposes raw TeX in visible text: $raw_fragment" >&2
      exit 1
    fi
  done
  if grep -Eq '^[[:space:]]*[0-9]+([.][0-9]+)?[[:space:]]+[0-9]+([.][0-9]+)*[.][[:space:]]' "$text"; then
    echo "$CHECK_NAME: $label contains a doubly numbered section heading" >&2
    exit 1
  fi

  python3 -I -S -B - "$text" <<'PY'
import pathlib
import sys

pages = [" ".join(page.split()) for page in pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").split("\f")]

def require_same_page(label, first, second):
    if not any(first in page and second in page for page in pages):
        raise SystemExit(f"pagination contract failed for {label}")

contracts = [
    ("foundational opening", "Foundational semantic audit", "Scope and formula"),
    ("plug-in opening", "Fixed finite-alphabet plug-in convergence", "Assumptions/result"),
    ("continuity opening", "Support-change-tolerant averaged-Sx continuity", "The result fixes three objects"),
    ("continuity-to-sampling transition", "The result applies when rare cells enter/leave", "Sampling and exact finite-table assurance"),
    ("sampling section opening", "Sampling and exact finite-table assurance", "Dependency-color concentration"),
    ("dependency opening", "Dependency-color concentration", "Complete rows"),
    ("two-source opening", "Exact two-source categorical-Sx assurance", "Exactly two finite categorical sources"),
    ("SxPID3 opening", "SxPID3 source-marginal factorization", "The factorization assumes"),
    ("binary64 opening", "Represented-binary64 and quantizer assurance", "Every finite binary64 number"),
    ("KSG opening", "KSG positive-integer harmonic arithmetic", "Revision 4 is active"),
    ("Wibral roadmap opening", "Wibral-line roadmap for high dimension", "This roadmap uses"),
    ("small-ball theorem opening", "A proved population-level transfer", "repository-derived conditional lemma, catalogued as project-defined"),
    ("small-ball pointwise assumptions", "Require the laws to admit the following density", "both density sums in the following ratio are strictly positive."),
    ("Clayton provenance boundary", "parameter Clayton form at a fixed parameter", "reparameterization of Clayton's 1978"),
    ("Clayton density construction", "ordinary copula, with no survival-time semantics.", "normalization despite the density's corner singularity"),
    ("gauge and PID boundary", "Gauge and dimension boundary", "expectation interchange, PID-atom property"),
    ("semantic figure", "Five lanes. No silent transfer.", "No equality"),
    ("evidence figure", "Nine result families", "NO PROOF TRANSFER BY PROXIMITY"),
    ("crosswalk figure", "Three different counts for three different objects", "Retaining all six views"),
]
for contract in contracts:
    require_same_page(*contract)
PY

  local -a structure_command optimized_structure_command
  require_gate_digest "$STRUCTURE_CHECK" "$STRUCTURE_CHECK_SHA256" "strict structure checker"
  require_gate_digest "$ID_VARIANCE_CHECK" "$ID_VARIANCE_CHECK_SHA256" \
    "strict trailer-ID variance checker"
  if [[ "$structure_relation" == "hosted-raw-and-strict" ]]; then
    require_gate_digest "$HOSTED_RAW_CHECK" "$HOSTED_RAW_CHECK_SHA256" \
      "hosted raw-profile checker"
  elif [[ "$structure_relation" == "legacy-typed-font-alpha-from-committed" ]]; then
    require_gate_digest "$FONT_ALPHA_CHECK" "$FONT_ALPHA_CHECK_SHA256" \
      "typed font-alpha comparator"
  fi
  case "$structure_relation" in
    strict)
      structure_command=(python3 -I -B "$STRUCTURE_CHECK" "$pdf" \
        "$observed_urls" "$observed_navigation")
      optimized_structure_command=(python3 -O -I -B "$STRUCTURE_CHECK" "$pdf" \
        "$optimized_urls" "$optimized_navigation")
      ;;
    hosted-raw-and-strict)
      structure_command=(python3 -I -B "$HOSTED_RAW_CHECK" \
        "$RETAINED_HOSTED_RAW_FIXTURE" "$pdf" \
        "$observed_urls" "$observed_navigation")
      optimized_structure_command=(python3 -O -I -B "$HOSTED_RAW_CHECK" \
        "$RETAINED_HOSTED_RAW_FIXTURE" "$pdf" \
        "$optimized_urls" "$optimized_navigation")
      ;;
    legacy-typed-font-alpha-from-committed)
      structure_command=(python3 -I -B "$FONT_ALPHA_CHECK" "$COMMITTED" "$pdf" \
        "$RETAINED_FONT_ALPHA_FIXTURE" \
        "$observed_urls" "$observed_navigation")
      optimized_structure_command=(python3 -O -I -B "$FONT_ALPHA_CHECK" "$COMMITTED" "$pdf" \
        "$RETAINED_FONT_ALPHA_FIXTURE" \
        "$optimized_urls" "$optimized_navigation")
      ;;
    *)
      echo "$CHECK_NAME: internal unknown structure relation: $structure_relation" >&2
      exit 1
      ;;
  esac
  if ! "${structure_command[@]}" \
      >"$BUILD_ROOT/$label.structure.stdout" 2>"$BUILD_ROOT/$label.structure.stderr"; then
    cat "$BUILD_ROOT/$label.structure.stdout" "$BUILD_ROOT/$label.structure.stderr" >&2
    exit 1
  fi
  if ! "${optimized_structure_command[@]}" \
      >"$BUILD_ROOT/$label.structure-optimized.stdout" \
      2>"$BUILD_ROOT/$label.structure-optimized.stderr"; then
    cat "$BUILD_ROOT/$label.structure-optimized.stdout" \
      "$BUILD_ROOT/$label.structure-optimized.stderr" >&2
    exit 1
  fi
  for structure_stderr in "$BUILD_ROOT/$label.structure.stderr" \
      "$BUILD_ROOT/$label.structure-optimized.stderr"; do
    if [[ -s "$structure_stderr" ]]; then
      cat "$structure_stderr" >&2
      echo "$CHECK_NAME: $label structure validator emitted stderr" >&2
      exit 1
    fi
  done
  if ! cmp -s "$observed_urls" "$optimized_urls" \
      || ! cmp -s "$observed_navigation" "$optimized_navigation"; then
    echo "$CHECK_NAME: $label structure result differs under optimized Python" >&2
    exit 1
  fi
  if ! cmp -s "$BUILD_ROOT/$label.structure.stdout" \
      "$BUILD_ROOT/$label.structure-optimized.stdout"; then
    echo "$CHECK_NAME: $label structure diagnostics differ under optimized Python" >&2
    diff -u "$BUILD_ROOT/$label.structure.stdout" \
      "$BUILD_ROOT/$label.structure-optimized.stdout" >&2 || true
    exit 1
  fi
  require_gate_digest "$STRUCTURE_CHECK" "$STRUCTURE_CHECK_SHA256" "strict structure checker"
  require_gate_digest "$ID_VARIANCE_CHECK" "$ID_VARIANCE_CHECK_SHA256" \
    "strict trailer-ID variance checker"
  if [[ "$structure_relation" == "hosted-raw-and-strict" ]]; then
    require_gate_digest "$HOSTED_RAW_CHECK" "$HOSTED_RAW_CHECK_SHA256" \
      "hosted raw-profile checker"
  elif [[ "$structure_relation" == "legacy-typed-font-alpha-from-committed" ]]; then
    require_gate_digest "$FONT_ALPHA_CHECK" "$FONT_ALPHA_CHECK_SHA256" \
      "typed font-alpha comparator"
  fi
  cat >"$expected_urls" <<'EOF'
https://arxiv.org/abs/1004.2515
https://arxiv.org/abs/2106.12393v2
https://arxiv.org/html/2311.06373v3
https://dlmf.nist.gov/5.4.E14
https://doi.org/10.1002/rsa.20008
https://doi.org/10.1007/978-0-387-47322-2
https://doi.org/10.1007/BF00531932
https://doi.org/10.1080/01621459.1963.10500830
https://doi.org/10.1093/biomet/65.1.141
https://doi.org/10.1098/rspa.2021.0110
https://doi.org/10.1103/58bg-5n9s
https://doi.org/10.1103/PhysRevE.103.032149
https://doi.org/10.1103/PhysRevE.110.014115
https://doi.org/10.1103/PhysRevE.69.066138
https://doi.org/10.3390/e16042161
https://github.com/sepahead/pid-rs/blob/main/DEPENDENCY_COLORED_SXPID_CONCENTRATION.md
https://github.com/sepahead/pid-rs/blob/main/FINITE_ALPHABET_PLUGIN_CONVERGENCE.md
https://github.com/sepahead/pid-rs/blob/main/FORMAL_TOOL_ADOPTION_AUDIT.md
https://github.com/sepahead/pid-rs/blob/main/FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md
https://github.com/sepahead/pid-rs/blob/main/KNOWN_LIMITATIONS.md
https://github.com/sepahead/pid-rs/blob/main/MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md
https://github.com/sepahead/pid-rs/blob/main/METHODS.md
https://github.com/sepahead/pid-rs/blob/main/METHODS_SUMMARY.md
https://github.com/sepahead/pid-rs/blob/main/NUMERICAL_ASSURANCE.md
https://github.com/sepahead/pid-rs/blob/main/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md
https://github.com/sepahead/pid-rs/blob/main/PID_MATHEMATICAL_AUDIT_PROTOCOL.md
https://github.com/sepahead/pid-rs/blob/main/PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md
https://github.com/sepahead/pid-rs/blob/main/SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md
https://github.com/sepahead/pid-rs/blob/main/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md
https://github.com/sepahead/pid-rs/blob/main/audit/evidence/ksg-rev4-m1a-composite-v12-boundary-2026-08-23.md
https://github.com/sepahead/pid-rs/blob/main/audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md
https://github.com/sepahead/pid-rs/blob/main/audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md
https://github.com/sepahead/pid-rs/blob/main/claims/KSG-INTEGER-HARMONIC-001/claim-v4.md
https://github.com/sepahead/pid-rs/blob/main/claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md
https://github.com/sepahead/pid-rs/blob/main/claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md
https://github.com/sepahead/pid-rs/blob/main/claims/KSG-INTEGER-HARMONIC-001/revision-index.md
https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md
https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md
https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision.md
https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md
https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID3-001/revision-index.md
https://github.com/sepahead/pid-rs/blob/main/claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md
https://github.com/sepahead/pid-rs/blob/main/method-catalog.json
https://github.com/sepahead/pid-rs/blob/main/output/pdf/dependency-colored-sxpid-concentration.pdf
https://github.com/sepahead/pid-rs/blob/main/output/pdf/exact-log-product-sxpid2-assurance.pdf
https://github.com/sepahead/pid-rs/blob/main/output/pdf/finite-alphabet-plugin-convergence.pdf
https://github.com/sepahead/pid-rs/blob/main/output/pdf/foundational-shared-exclusions-pid-audit.pdf
https://github.com/sepahead/pid-rs/blob/main/output/pdf/mathematical-problem-solving-workflow.pdf
https://github.com/sepahead/pid-rs/blob/main/output/pdf/numerical-assurance.pdf
https://github.com/sepahead/pid-rs/blob/main/output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf
https://github.com/sepahead/pid-rs/blob/main/output/pdf/sxpid3-source-marginal-and-bounded-audit.pdf
https://github.com/sepahead/pid-rs/blob/main/output/pdf/two-source-sxpid-count-atom-bridge.pdf
https://papers.nips.cc/paper_files/paper/2004/hash/74934548253bcab8490ebd74afed7031-Abstract.html
https://proceedings.mlr.press/v38/gao15.html
https://proceedings.mlr.press/v80/nickel18a.html
https://shiftleft.com/mirrors/www.hpl.hp.com/techreports/2003/HPL-2003-97R1.pdf
EOF
  if ! cmp -s "$expected_urls" "$observed_urls"; then
    echo "$CHECK_NAME: $label hyperlink target set changed" >&2
    diff -u "$expected_urls" "$observed_urls" >&2 || true
    exit 1
  fi
}

validate_pdf committed "$COMMITTED" strict
case "$MODE:$CROSS_PROFILE" in
  --exact:)
    validate_pdf built "$BUILT" strict
    ;;
  --cross-toolchain:"$HOSTED_PROFILE_ID")
    # The hosted checker raw-binds its current-format fixture before strict validation.
    validate_pdf built "$BUILT" hosted-raw-and-strict
    ;;
  --cross-toolchain:"$LEGACY_PROFILE_ID")
    # The legacy checker raw-binds both references before its typed font-key proof.
    validate_pdf built "$BUILT" legacy-typed-font-alpha-from-committed
    ;;
  *)
    echo "$CHECK_NAME: mode/profile dispatch is empty, unknown, or inconsistent" >&2
    exit 1
    ;;
esac

if ! cmp -s "$BUILD_ROOT/built.font-roster" "$BUILD_ROOT/committed.font-roster"; then
  echo "$CHECK_NAME: normalized font roster differs between built and committed PDFs" >&2
  diff -u "$BUILD_ROOT/committed.font-roster" "$BUILD_ROOT/built.font-roster" >&2 || true
  exit 1
fi

if [[ "$MODE" == "--exact" ]]; then
  cmp -s "$BUILT" "$COMMITTED" || {
    echo "$CHECK_NAME: committed PDF is stale or not same-toolchain reproducible" >&2
    exit 1
  }
else
  cmp -s "$BUILD_ROOT/built.txt" "$BUILD_ROOT/committed.txt" || {
    echo "$CHECK_NAME: extracted text changed across toolchains" >&2
    exit 1
  }
  grep -E '^(Pages|Page size):' "$BUILD_ROOT/built.info" >"$BUILD_ROOT/built.geometry"
  grep -E '^(Pages|Page size):' "$BUILD_ROOT/committed.info" >"$BUILD_ROOT/committed.geometry"
  cmp -s "$BUILD_ROOT/built.geometry" "$BUILD_ROOT/committed.geometry" || {
    echo "$CHECK_NAME: geometry changed across toolchains" >&2
    exit 1
  }
fi

if ! cmp -s "$BUILD_ROOT/built.observed-urls" "$BUILD_ROOT/committed.observed-urls"; then
  echo "$CHECK_NAME: hyperlink target set differs between built and committed projections" >&2
  diff -u "$BUILD_ROOT/built.observed-urls" "$BUILD_ROOT/committed.observed-urls" >&2 || true
  exit 1
fi
if ! cmp -s "$BUILD_ROOT/built.observed-navigation" \
    "$BUILD_ROOT/committed.observed-navigation"; then
  echo "$CHECK_NAME: navigation structure differs between built and committed projections" >&2
  diff -u "$BUILD_ROOT/built.observed-navigation" \
    "$BUILD_ROOT/committed.observed-navigation" >&2 || true
  exit 1
fi
if [[ "$(wc -l <"$BUILD_ROOT/committed.observed-urls" | tr -d ' ')" != "56" ]]; then
  echo "$CHECK_NAME: hyperlink target count changed" >&2
  exit 1
fi
if [[ "$(wc -l <"$BUILD_ROOT/committed.observed-navigation" | tr -d ' ')" != "217" ]]; then
  echo "$CHECK_NAME: navigation-record count changed" >&2
  exit 1
fi
while IFS= read -r target; do
  case "$target" in
    https://github.com/sepahead/pid-rs/blob/main/*)
      local_target="${target#https://github.com/sepahead/pid-rs/blob/main/}"
      if [[ ! -f "$ROOT/$local_target" || -L "$ROOT/$local_target" ]]; then
        echo "$CHECK_NAME: repository hyperlink target is absent or symbolic: $local_target" >&2
        exit 1
      fi
      ;;
    http://*|https://*) ;;
    *)
      echo "$CHECK_NAME: unexpected hyperlink domain: $target" >&2
      exit 1
      ;;
  esac
done <"$BUILD_ROOT/committed.observed-urls"

require_gate_digest "$STRUCTURE_CHECK" "$STRUCTURE_CHECK_SHA256" "strict structure checker"
require_gate_digest "$ID_VARIANCE_CHECK" "$ID_VARIANCE_CHECK_SHA256" \
  "strict trailer-ID variance checker"
case "$MODE:$CROSS_PROFILE" in
  --exact:) ;;
  --cross-toolchain:"$HOSTED_PROFILE_ID")
    require_gate_digest "$HOSTED_RAW_CHECK" "$HOSTED_RAW_CHECK_SHA256" \
      "hosted raw-profile checker"
    require_gate_digest "$HOSTED_RAW_SELF_TEST" "$HOSTED_RAW_SELF_TEST_SHA256" \
      "hosted raw-profile checker self-test"
    require_gate_digest "$HOSTED_RAW_PROFILE_RECEIPT" \
      "$HOSTED_RAW_PROFILE_RECEIPT_SHA256" "hosted raw-profile provenance receipt"
    ;;
  --cross-toolchain:"$LEGACY_PROFILE_ID")
    require_gate_digest "$FONT_ALPHA_CHECK" "$FONT_ALPHA_CHECK_SHA256" \
      "typed font-alpha comparator"
    require_gate_digest "$FONT_ALPHA_SELF_TEST" "$FONT_ALPHA_SELF_TEST_SHA256" \
      "typed font-alpha comparator self-test"
    require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_CHECK" \
      "$PANDOC_PORTABILITY_RECEIPT_CHECK_SHA256" \
      "historical Pandoc portability receipt checker"
    require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST" \
      "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST_SHA256" \
      "historical Pandoc portability receipt checker self-test"
    require_gate_digest "$LEGACY_PANDOC_PORTABILITY_RECEIPT" \
      "$LEGACY_PANDOC_PORTABILITY_RECEIPT_SHA256" \
      "historical Pandoc portability receipt"
    require_gate_digest "$TRAILER_ID_OBSERVATION_CHECK" \
      "$TRAILER_ID_OBSERVATION_CHECK_SHA256" \
      "historical trailer-ID observation checker"
    require_gate_digest "$TRAILER_ID_OBSERVATION_SELF_TEST" \
      "$TRAILER_ID_OBSERVATION_SELF_TEST_SHA256" \
      "historical trailer-ID observation checker self-test"
    require_gate_digest "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT" \
      "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT_SHA256" \
      "historical trailer-ID observation receipt"
    ;;
  *)
    echo "$CHECK_NAME: final mode/profile digest dispatch is inconsistent" >&2
    exit 1
    ;;
esac

RENDER_PREFIX="$BUILD_ROOT/render/page"
mkdir -p "$(dirname "$RENDER_PREFIX")"
PAGES="$(awk '/^Pages:/ {print $2}' "$BUILD_ROOT/committed.info")"
pdftoppm -f 1 -l "$PAGES" -r 72 -png "$COMMITTED" "$RENDER_PREFIX" \
  >"$BUILD_ROOT/render.stdout" 2>"$BUILD_ROOT/render.stderr" || {
  cat "$BUILD_ROOT/render.stdout" "$BUILD_ROOT/render.stderr" >&2
  echo "$CHECK_NAME: Poppler could not render all pages" >&2
  exit 1
}
if [[ -s "$BUILD_ROOT/render.stderr" ]]; then
  cat "$BUILD_ROOT/render.stderr" >&2
  echo "$CHECK_NAME: Poppler rendering emitted stderr" >&2
  exit 1
fi
RENDERED="$(find "$BUILD_ROOT/render" -type f -name 'page-*.png' | wc -l | tr -d ' ')"
if [[ "$RENDERED" != "$PAGES" ]]; then
  echo "$CHECK_NAME: rendered page count $RENDERED does not equal PDF page count $PAGES" >&2
  exit 1
fi

echo "OK: $CHECK_NAME passed ($(shasum -a 256 "$BUILT" | awk '{print $1}'))"
