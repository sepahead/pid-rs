#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/l3pdffile-filespec-f-compat.tex"
COMPAT_SHA256=a8eb78a26f554117fd5ff9661e617e0348e8e69fce3f63e3ff3c1321b51aa36a

for command_name in awk cmp cp env grep kpsewhich mkdir mktemp pdflatex python3 rm shasum; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "l3pdffile file-specification compatibility self-test failed: missing command: $command_name" >&2
    exit 1
  fi
done
if [[ ! -f "$COMPAT" || -L "$COMPAT" ]]; then
  echo "l3pdffile file-specification compatibility self-test failed: source is absent or symbolic" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$COMPAT_SHA256" "$COMPAT" | shasum -a 256 --check --status; then
  echo "l3pdffile file-specification compatibility self-test failed: source digest changed" >&2
  exit 1
fi

PDFMANAGEMENT="$(kpsewhich pdfmanagement-testphase.ltx)"
if [[ -z "$PDFMANAGEMENT" || ! -f "$PDFMANAGEMENT" || -L "$PDFMANAGEMENT" ]]; then
  echo "l3pdffile file-specification compatibility self-test failed: bundle source is absent or symbolic" >&2
  exit 1
fi
if grep -Fq '\pdf_string_from_unicode:nnN {utf8/string}{#2}' "$PDFMANAGEMENT"; then
  NATIVE=1
  MODE=native-present
else
  NATIVE=0
  MODE=native-absent
fi

TMP_BASE="${TMPDIR:-/tmp}"
while [[ "$TMP_BASE" != "/" && "$TMP_BASE" == */ ]]; do
  TMP_BASE="${TMP_BASE%/}"
done
TEST_ROOT="$(mktemp -d "${TMP_BASE%/}/pid-rs-filespec-f-self-test.XXXXXX")"
cleanup() {
  case "$TEST_ROOT" in
    "${TMP_BASE%/}"/pid-rs-filespec-f-self-test.*)
      rm -rf -- "$TEST_ROOT"
      ;;
    *)
      echo "l3pdffile file-specification compatibility self-test cleanup refused unexpected path: $TEST_ROOT" >&2
      ;;
  esac
}
trap cleanup EXIT INT TERM
cp "$COMPAT" "$TEST_ROOT/l3pdffile-filespec-f-compat.tex"
mkdir "$TEST_ROOT/home" "$TEST_ROOT/installed" "$TEST_ROOT/without"

cat >"$TEST_ROOT/preamble.tex" <<'TEX'
\DocumentMetadata{lang=en-US,testphase=phase-II}
\documentclass{article}
\usepackage{hyperref}
TEX
cat >"$TEST_ROOT/body.tex" <<'TEX'
\begin{document}
\section{Target}\label{target}
\hyperref[target]{internal control}
\href{alpha-guide.pdf}{alpha PDF}
\href{folder/beta-guide.pdf\#page=2}{beta PDF}
\href{https://example.invalid/path}{URI control}
\end{document}
TEX

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/control.tex"
printf '%s\n' \
  '\input{compat-under-test.tex}' \
  '\input{body.tex}' >>"$TEST_ROOT/control.tex"

compile_control() {
  local source="$1" output_directory="$2"
  local run
  for run in first second; do
    (cd "$TEST_ROOT" && \
      env -i PATH="$PATH" HOME="$TEST_ROOT/home" TMPDIR="$TEST_ROOT" \
        LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH=1787875200 \
        pdflatex -interaction=nonstopmode -halt-on-error \
          -jobname=compat-control -output-directory="$output_directory" "$source") \
        >"$output_directory/$run.stdout" 2>&1 || {
          cat "$output_directory/$run.stdout" >&2
          echo "l3pdffile file-specification compatibility self-test failed: $source did not compile" >&2
          exit 1
        }
  done
}

cp "$COMPAT" "$TEST_ROOT/compat-under-test.tex"
compile_control "$TEST_ROOT/control.tex" "$TEST_ROOT/installed"
printf '%s\n' '% native no-op or old-route negative control' \
  >"$TEST_ROOT/compat-under-test.tex"
compile_control "$TEST_ROOT/control.tex" "$TEST_ROOT/without"

python3 -I -B - \
  "$TEST_ROOT/installed/compat-control.pdf" \
  "$TEST_ROOT/without/compat-control.pdf" \
  "$MODE" <<'PY'
import pathlib
import re
import sys

from pypdf import PdfReader
from pypdf.generic import (
    ArrayObject,
    ByteStringObject,
    DictionaryObject,
    IndirectObject,
    NameObject,
    TextStringObject,
)

expected_files = ["alpha-guide.pdf", "folder/beta-guide.pdf"]
expected_destinations = [(0, "/Fit"), "page=2"]
ID_PATTERN = re.compile(
    rb"/ID[ \t\r\n]*\[[ \t\r\n]*<([0-9A-F]{32})>[ \t\r\n]*"
    rb"<([0-9A-F]{32})>[ \t\r\n]*\]"
)
ID_NAME_PATTERN = re.compile(
    rb"/ID(?=$|[\x00\t\n\f\r ()<>\[\]{}/%])"
)


def original_bytes(value, label):
    raw = getattr(value, "original_bytes", None)
    if not isinstance(raw, bytes):
        raise SystemExit(f"{label}: PDF string lacks original bytes")
    return raw


def destination_value(value):
    if isinstance(value, ArrayObject):
        return (int(value[0]), str(value[1]))
    return str(value)


def dereference(value):
    while isinstance(value, IndirectObject):
        value = value.get_object()
    return value


def require_native_equal_outside_trailer_id(installed, without):
    def erase_unique_duplicated_id(path):
        data = path.read_bytes()
        name_matches = list(ID_NAME_PATTERN.finditer(data))
        if len(name_matches) != 1:
            raise SystemExit(
                f"{path.name}: raw file does not contain exactly one /ID name token"
            )
        matches = list(ID_PATTERN.finditer(data))
        if len(matches) != 1:
            raise SystemExit(f"{path.name}: expected exactly one strict trailer /ID token")
        match = matches[0]
        if match.start() != name_matches[0].start():
            raise SystemExit(f"{path.name}: strict /ID token does not own the sole raw /ID name")
        if match.group(1) != match.group(2):
            raise SystemExit(f"{path.name}: trailer /ID pair is not duplicated")
        typed = PdfReader(path, strict=True).trailer.raw_get("/ID")
        if not isinstance(typed, ArrayObject) or len(typed) != 2:
            raise SystemExit(f"{path.name}: typed trailer /ID is not a two-element array")
        if any(
            not isinstance(value, (TextStringObject, ByteStringObject))
            for value in typed
        ):
            raise SystemExit(f"{path.name}: typed trailer /ID elements are not PDF strings")
        typed_bytes = [getattr(value, "original_bytes", None) for value in typed]
        if (
            any(not isinstance(value, bytes) or len(value) != 16 for value in typed_bytes)
            or typed_bytes[0] != typed_bytes[1]
            or typed_bytes
            != [bytes.fromhex(match.group(1).decode("ascii"))] * 2
        ):
            raise SystemExit(f"{path.name}: typed trailer /ID does not match the raw token")
        normalized = bytearray(data)
        for group in (1, 2):
            start, end = match.span(group)
            normalized[start:end] = b"0" * (end - start)
        return bytes(normalized)

    if erase_unique_duplicated_id(installed) != erase_unique_duplicated_id(without):
        raise SystemExit(
            "native path changed bytes outside the exact duplicated trailer /ID payload"
        )


def exercise_id_parser(control):
    control_bytes = control.read_bytes()
    match = ID_PATTERN.search(control_bytes)
    if match is None:
        raise SystemExit("ID-parser control lacks the strict baseline token")

    def expect_rejection(label, payload, expected):
        hostile = control.with_name(f"id-hostile-{label}.pdf")
        hostile.write_bytes(payload)
        try:
            require_native_equal_outside_trailer_id(control, hostile)
        except SystemExit as error:
            if expected not in str(error):
                raise SystemExit(f"ID-parser {label} diagnostic changed: {error}") from error
        else:
            raise SystemExit(f"ID-parser {label} hostile passed")

    expect_rejection(
        "extra-name",
        control_bytes + b"\n0/ID ",
        "does not contain exactly one /ID name token",
    )
    if len(ID_NAME_PATTERN.findall(control_bytes + b"\n/Identity-H\n")) != 1:
        raise SystemExit("ID-parser mistook /Identity-H for an /ID name token")
    malformed = bytearray(control_bytes)
    malformed[match.start(1) - 1] = ord("(")
    expect_rejection(
        "malformed-token", bytes(malformed), "expected exactly one strict trailer /ID token"
    )
    nonduplicated = bytearray(control_bytes)
    second_start, _ = match.span(2)
    nonduplicated[second_start] = ord("0") if nonduplicated[second_start] != ord("0") else ord("1")
    expect_rejection(
        "nonduplicated", bytes(nonduplicated), "trailer /ID pair is not duplicated"
    )
    expect_rejection(
        "outside-payload",
        control_bytes + b"\n",
        "changed bytes outside the exact duplicated trailer /ID payload",
    )


def inspect(path, label, require_fixed):
    reader = PdfReader(path, strict=True)
    root = reader.trailer["/Root"]
    if not isinstance(root.raw_get("/StructTreeRoot"), IndirectObject):
        raise SystemExit(f"{label}: StructTreeRoot is absent or direct")
    files = []
    destinations = []
    internal = 0
    uris = []
    for page_number, page in enumerate(reader.pages, 1):
        for ordinal, reference in enumerate(page.get("/Annots", ArrayObject()), 1):
            annotation = reference.get_object()
            action = dereference(annotation.raw_get("/A")) if "/A" in annotation else None
            if not isinstance(action, DictionaryObject):
                continue
            kind = action.get("/S")
            if kind not in (NameObject("/GoToR"), NameObject("/GoTo"), NameObject("/URI")):
                continue
            if kind == NameObject("/GoToR"):
                if annotation.get("/StructParent") is not None or annotation.get("/Contents") is not None:
                    raise SystemExit(
                        f"{label}: page {page_number} GoToR unexpectedly has structure or Contents"
                    )
                filespec_reference = action.raw_get("/F")
                if not isinstance(filespec_reference, IndirectObject):
                    raise SystemExit(f"{label}: GoToR /F is not an indirect file specification")
                filespec = dereference(filespec_reference)
                portable = filespec.get("/F")
                unicode_name = filespec.get("/UF")
                target = str(portable)
                if str(unicode_name) != target:
                    raise SystemExit(f"{label}: /F and /UF decode to different targets")
                if require_fixed:
                    if original_bytes(portable, label) != target.encode("ascii"):
                        raise SystemExit(f"{label}: /F is not canonical ASCII")
                elif original_bytes(portable, label) != b"\xfe\xff" + target.encode("utf-16-be"):
                    raise SystemExit(f"{label}: old-route negative control no longer has UTF-16BE /F")
                if original_bytes(unicode_name, label) != b"\xfe\xff" + target.encode("utf-16-be"):
                    raise SystemExit(f"{label}: /UF is not the preserved UTF-16BE target")
                files.append(target)
                destinations.append(destination_value(action.get("/D")))
            elif kind == NameObject("/GoTo"):
                if not isinstance(annotation.get("/StructParent"), int):
                    raise SystemExit(f"{label}: internal GoTo lacks StructParent")
                internal += 1
            else:
                if not isinstance(annotation.get("/StructParent"), int):
                    raise SystemExit(f"{label}: URI lacks StructParent")
                uris.append(str(action.get("/URI")))
    if files != expected_files or destinations != expected_destinations:
        raise SystemExit(
            f"{label}: file targets or destinations changed: {files!r} {destinations!r}"
        )
    if internal != 1 or uris != ["https://example.invalid/path"]:
        raise SystemExit(f"{label}: control actions changed: GoTo={internal} URI={uris!r}")


installed_path = pathlib.Path(sys.argv[1])
without_path = pathlib.Path(sys.argv[2])
inspect(installed_path, "installed", True)
inspect(without_path, "without-compat", sys.argv[3] == "native-present")
exercise_id_parser(without_path)
if sys.argv[3] == "native-present":
    require_native_equal_outside_trailer_id(installed_path, without_path)
PY

if [[ "$NATIVE" -eq 1 ]]; then
  : # The strict parser above permits only the input-dependent duplicated trailer /ID payload.
else
  if cmp -s "$TEST_ROOT/installed/compat-control.pdf" "$TEST_ROOT/without/compat-control.pdf"; then
    echo "l3pdffile file-specification compatibility self-test failed: old-route control was inert" >&2
    exit 1
  fi
fi

compact_pidrs_diagnostic() {
  awk '
    !capture && /^! (Fatal )?Package pid-rs Error:/ {
      capture = 1
      sub(/^! (Fatal )?Package pid-rs Error:[[:space:]]*/, "")
      gsub(/[[:space:]]/, "")
      printf "%s", $0
      next
    }
    capture && /^\(pid-rs\)/ {
      sub(/^\(pid-rs\)[[:space:]]*/, "")
      gsub(/[[:space:]]/, "")
      printf "%s", $0
      next
    }
    capture { exit }
  '
}

if [[ "$(printf '%s\n' \
    '! Package pid-rs Error: split diag' \
    '(pid-rs) nostic text.' | compact_pidrs_diagnostic)" != "splitdiagnostictext." ]]; then
  echo "l3pdffile file-specification compatibility self-test failed: bounded diagnostic control changed" >&2
  exit 1
fi
if [[ "$(printf '%s\n' \
    '! Package pid-rs Error: wrong text' \
    'expected needle only outside the package block' | compact_pidrs_diagnostic)" == \
    *"expectedneedle"* ]]; then
  echo "l3pdffile file-specification compatibility self-test failed: diagnostic parser captured an unprefixed line" >&2
  exit 1
fi
if [[ "$(printf '%s\n' \
    '! Package pid-rs Error: wrong first block' \
    '! Package pid-rs Error: expected needle only in second block' | \
    compact_pidrs_diagnostic)" == *"expectedneedle"* ]]; then
  echo "l3pdffile file-specification compatibility self-test failed: diagnostic parser captured a second package block" >&2
  exit 1
fi

expect_fatal() {
  local name="$1" source="$2" message="$3"
  local output_directory="$TEST_ROOT/$name" normalized expected_compact
  mkdir "$output_directory"
  if (cd "$TEST_ROOT" && \
      env -i PATH="$PATH" HOME="$TEST_ROOT/home" TMPDIR="$TEST_ROOT" \
        LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH=1787875200 \
        pdflatex -interaction=nonstopmode -halt-on-error \
          -jobname=must-not-render -output-directory="$output_directory" "$source") \
        >"$output_directory/stdout" 2>&1; then
    echo "l3pdffile file-specification compatibility self-test failed: $name rendered" >&2
    exit 1
  fi
  if [[ -e "$output_directory/must-not-render.pdf" || -L "$output_directory/must-not-render.pdf" ]]; then
    echo "l3pdffile file-specification compatibility self-test failed: $name published a PDF" >&2
    exit 1
  fi
  normalized="$(compact_pidrs_diagnostic <"$output_directory/stdout")"
  expected_compact="$(awk -v value="$message" 'BEGIN { gsub(/[[:space:]]/, "", value); print value }')"
  if [[ "$normalized" != *"$expected_compact"* ]]; then
    cat "$output_directory/stdout" >&2
    echo "l3pdffile file-specification compatibility self-test failed: $name diagnostic changed" >&2
    exit 1
  fi
}

write_native_absent_fixture() {
  local destination="$1"
  cat >>"$destination" <<'TEX'
\ExplSyntaxOn
\cs_set_protected:Npn \__pdffile_filespec_write:nnn #1#2#3 { }
\cs_set_protected:Npn \__pdffile_filespec_write:nnN #1#2#3 { }
\cs_set_eq:NN \pdffile_filespec:nnn \__pdffile_filespec_write:nnn
\ExplSyntaxOff
TEX
}

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/newer-native-absent.tex"
write_native_absent_fixture "$TEST_ROOT/newer-native-absent.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@pdfmanagement-testphase.ltx\endcsname{2024-03-01 unexpected-newer}' \
  '\input{l3pdffile-filespec-f-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/newer-native-absent.tex"
expect_fatal \
  newer-native-absent \
  "$TEST_ROOT/newer-native-absent.tex" \
  'newer bundle lacks the reviewed native'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/older-native-present.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@pdfmanagement-testphase.ltx\endcsname{2023-12-09 unexpected-native}' \
  '\ExplSyntaxOn' \
  '\cs_set_protected:Npn \__pdffile_filespec_write:nnn #1#2#3 {\use_none:n {pdf_string_from_unicode:nnN utf8/string}}' \
  '\cs_set_protected:Npn \__pdffile_filespec_write:nnN #1#2#3 {\use_none:n {pdf_string_from_unicode:nnN utf8/string}}' \
  '\cs_set_eq:NN \pdffile_filespec:nnn \__pdffile_filespec_write:nnn' \
  '\ExplSyntaxOff' \
  '\input{l3pdffile-filespec-f-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/older-native-present.tex"
expect_fatal \
  older-native-present \
  "$TEST_ROOT/older-native-present.tex" \
  'unexpected older bundle has the native'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/mixed-state.tex"
printf '%s\n' \
  '\ExplSyntaxOn' \
  '\cs_set_protected:Npn \__pdffile_filespec_write:nnn #1#2#3 {\use_none:n {pdf_string_from_unicode:nnN utf8/string}}' \
  '\cs_set_protected:Npn \__pdffile_filespec_write:nnN #1#2#3 { }' \
  '\cs_set_eq:NN \pdffile_filespec:nnn \__pdffile_filespec_write:nnn' \
  '\ExplSyntaxOff' \
  '\input{l3pdffile-filespec-f-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/mixed-state.tex"
expect_fatal mixed-state "$TEST_ROOT/mixed-state.tex" 'mixed native file-specification writer state'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/ancient-fallback.tex"
write_native_absent_fixture "$TEST_ROOT/ancient-fallback.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@pdfmanagement-testphase.ltx\endcsname{2023-12-08 0.96c}' \
  '\input{l3pdffile-filespec-f-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/ancient-fallback.tex"
expect_fatal \
  ancient-fallback \
  "$TEST_ROOT/ancient-fallback.tex" \
  'bundle is older than the reviewed 0.96d fallback'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/wrong-version.tex"
write_native_absent_fixture "$TEST_ROOT/wrong-version.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@pdfmanagement-testphase.ltx\endcsname{2023-12-09 0.96c}' \
  '\input{l3pdffile-filespec-f-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/wrong-version.tex"
expect_fatal \
  wrong-version \
  "$TEST_ROOT/wrong-version.tex" \
  'bundle version is not the reviewed 0.96d fallback'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/version-suffix.tex"
write_native_absent_fixture "$TEST_ROOT/version-suffix.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@pdfmanagement-testphase.ltx\endcsname{2023-12-09 v0.96danger PDF management code (testphase)}' \
  '\input{l3pdffile-filespec-f-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/version-suffix.tex"
expect_fatal \
  version-suffix \
  "$TEST_ROOT/version-suffix.tex" \
  'bundle version is not the reviewed 0.96d fallback'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/duplicate.tex"
write_native_absent_fixture "$TEST_ROOT/duplicate.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@pdfmanagement-testphase.ltx\endcsname{2023-12-09 v0.96d PDF management code (testphase)}' \
  '\input{l3pdffile-filespec-f-compat.tex}' \
  '\input{l3pdffile-filespec-f-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/duplicate.tex"
expect_fatal duplicate "$TEST_ROOT/duplicate.tex" 'duplicate compatibility'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/missing-api.tex"
write_native_absent_fixture "$TEST_ROOT/missing-api.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@pdfmanagement-testphase.ltx\endcsname{2023-12-09 v0.96d PDF management code (testphase)}' \
  '\ExplSyntaxOn\cs_undefine:N \pdf_string_from_unicode:nnN\ExplSyntaxOff' \
  '\input{l3pdffile-filespec-f-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/missing-api.tex"
expect_fatal missing-api "$TEST_ROOT/missing-api.tex" 'PDF string conversion API is absent'

echo "l3pdffile file-specification compatibility self-test passed: mode=$MODE controls=3 hostiles=14."
