#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/hgeneric-uri-contents-compat.tex"
COMPAT_SHA256=6294db9644cff4d7ded8e2a98415d72cb73fae4f3a55ad705607b39edc391ad5

for command_name in awk cmp cp env grep kpsewhich mkdir mktemp pdflatex python3 rm shasum; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "hgeneric URI-Contents compatibility self-test failed: missing command: $command_name" >&2
    exit 1
  fi
done
if [[ ! -f "$COMPAT" || -L "$COMPAT" ]]; then
  echo "hgeneric URI-Contents compatibility self-test failed: source is absent or symbolic" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$COMPAT_SHA256" "$COMPAT" | shasum -a 256 --check --status; then
  echo "hgeneric URI-Contents compatibility self-test failed: source digest changed" >&2
  exit 1
fi

HGENERIC="$(kpsewhich hgeneric-testphase.def)"
if [[ -z "$HGENERIC" || ! -f "$HGENERIC" || -L "$HGENERIC" ]]; then
  echo "hgeneric URI-Contents compatibility self-test failed: hgeneric source is absent or symbolic" >&2
  exit 1
fi
if grep -Fq '\tl_new:N\l__hyp_link_Contents_tl' "$HGENERIC"; then
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
TEST_ROOT="$(mktemp -d "${TMP_BASE%/}/pid-rs-hgeneric-uri-contents-self-test.XXXXXX")"
cleanup() {
  case "$TEST_ROOT" in
    "${TMP_BASE%/}"/pid-rs-hgeneric-uri-contents-self-test.*)
      rm -rf -- "$TEST_ROOT"
      ;;
    *)
      echo "hgeneric URI-Contents compatibility self-test cleanup refused unexpected path: $TEST_ROOT" >&2
      ;;
  esac
}
trap cleanup EXIT INT TERM
cp "$COMPAT" "$TEST_ROOT/hgeneric-uri-contents-compat.tex"
mkdir "$TEST_ROOT/home" "$TEST_ROOT/installed" "$TEST_ROOT/without" "$TEST_ROOT/forced-old" \
  "$TEST_ROOT/scheduled" "$TEST_ROOT/scheduled-without"

cat >"$TEST_ROOT/preamble.tex" <<'TEX'
\DocumentMetadata{
  lang=en-US,
  pdfstandard=ua-2,
  testphase={phase-III,title,table,math,firstaid}
}
\documentclass{article}
\usepackage{etoolbox}
\usepackage{hyperref}
TEX
cat >"$TEST_ROOT/body.tex" <<'TEX'
\begin{document}
\section{Target}\label{target}
\hyperref[target]{internal reference}
\ExplSyntaxOn
\tl_new:N \l__pidrs_uri_dictionary_before_tl
\tl_new:N \l__pidrs_uri_dictionary_after_tl
\tl_set:Nx \l__pidrs_uri_dictionary_before_tl { \pdfannot_dict_use:n { link/URI } }
\ExplSyntaxOff
\href{../../method-catalog.json}{method catalog}
\href{https://example.invalid/path?q=alpha}{external control}
\ExplSyntaxOn
\tl_set:Nx \l__pidrs_uri_dictionary_after_tl { \pdfannot_dict_use:n { link/URI } }
\tl_if_eq:NNF \l__pidrs_uri_dictionary_before_tl \l__pidrs_uri_dictionary_after_tl
  { \GenericError{}{URI annotation dictionary leaked across hyper@linkurl}{}{} }
\ExplSyntaxOff
\end{document}
TEX

cp "$TEST_ROOT/body.tex" "$TEST_ROOT/installed-body.tex"
cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/control.tex"
printf '%s\n' \
  '\input{compat-under-test.tex}' \
  '\input{installed-body.tex}' >>"$TEST_ROOT/control.tex"

write_native_removal() {
  local destination="$1"
  if [[ "$NATIVE" -eq 1 ]]; then
    cat >>"$destination" <<'TEX'
\makeatletter
\ExplSyntaxOn
\patchcmd \hyper@linkurl
  {
    \socket_use:nn { hyp/link/URI/Contents } {#2}
    \pdfannot_dict_put:nne
      { link/URI }
      { Contents }
      { \l__hyp_link_Contents_tl }
  }
  { }
  { }
  { \GenericError{}{native URI-Contents block not found}{}{} }
\cs_undefine:N \l__hyp_link_Contents_tl
\ExplSyntaxOff
\makeatother
TEX
  fi
}

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/forced-old.tex"
write_native_removal "$TEST_ROOT/forced-old.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@hgeneric-testphase.def\endcsname{2023-12-09 v0.96d generic Hyperref driver for the LaTeX PDF management testphase bundle}' \
  '\input{hgeneric-uri-contents-compat.tex}' \
  '\input{installed-body.tex}' >>"$TEST_ROOT/forced-old.tex"

cat >"$TEST_ROOT/scheduled.tex" <<'TEX'
\DocumentMetadata{
  lang=en-US,
  pdfstandard=ua-2,
  testphase={phase-III,title,table,math,firstaid}
}
\documentclass{article}
\AtBeginDocument{\input{scheduled-compat-under-test.tex}}
\usepackage{etoolbox}
\usepackage{hyperref}
\begin{document}
\href{../../method-catalog.json}{method catalog first-token control}
\section{Target}\label{scheduled-target}
\hyperref[scheduled-target]{internal reference}
\href{https://example.invalid/path?q=alpha}{external control}
\end{document}
TEX

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
          echo "hgeneric URI-Contents compatibility self-test failed: $source did not compile" >&2
          exit 1
        }
  done
}

cp "$COMPAT" "$TEST_ROOT/compat-under-test.tex"
compile_control "$TEST_ROOT/control.tex" "$TEST_ROOT/installed"
printf '%s\n' '% native no-op or old-route negative control' \
  >"$TEST_ROOT/compat-under-test.tex"
compile_control "$TEST_ROOT/control.tex" "$TEST_ROOT/without"
compile_control "$TEST_ROOT/forced-old.tex" "$TEST_ROOT/forced-old"
cp "$COMPAT" "$TEST_ROOT/scheduled-compat-under-test.tex"
compile_control "$TEST_ROOT/scheduled.tex" "$TEST_ROOT/scheduled"
printf '%s\n' '% native no-op or old-route negative control' \
  >"$TEST_ROOT/scheduled-compat-under-test.tex"
compile_control "$TEST_ROOT/scheduled.tex" "$TEST_ROOT/scheduled-without"

python3 -I -B - \
  "$TEST_ROOT/installed/compat-control.pdf" \
  "$TEST_ROOT/forced-old/compat-control.pdf" \
  "$TEST_ROOT/without/compat-control.pdf" \
  "$MODE" \
  "$TEST_ROOT/scheduled/compat-control.pdf" \
  "$TEST_ROOT/scheduled-without/compat-control.pdf" <<'PY'
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

expected_uris = ["../../method-catalog.json", "https://example.invalid/path?q=alpha"]
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
        raise SystemExit(f"{label}: text string lacks original bytes")
    return raw


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
    uris = []
    gotos = []
    action_kinds = []
    for page_number, page in enumerate(reader.pages, 1):
        annotations = page.get("/Annots", ArrayObject())
        for ordinal, reference in enumerate(annotations, 1):
            annotation = reference.get_object()
            action = annotation.get("/A")
            if not isinstance(action, DictionaryObject):
                continue
            kind = action.get("/S")
            if kind not in (NameObject("/URI"), NameObject("/GoTo")):
                continue
            action_kinds.append(str(kind))
            if not isinstance(annotation.get("/StructParent"), int):
                raise SystemExit(f"{label}: page {page_number} annotation {ordinal} lacks StructParent")
            contents = annotation.get("/Contents")
            if kind == NameObject("/URI"):
                target = str(action.get("/URI"))
                uris.append(target)
                if require_fixed:
                    expected = b"\xfe\xff" + target.encode("utf-16-be")
                    if str(contents) != target or original_bytes(contents, label) != expected:
                        raise SystemExit(f"{label}: URI Contents is not the canonical UTF-16BE target")
                elif original_bytes(contents, label) != b"url":
                    raise SystemExit(f"{label}: old-route negative control no longer reproduces (url)")
            else:
                gotos.append(
                    (str(action.get("/D")), str(contents), original_bytes(contents, label))
                )
    if uris != expected_uris or len(gotos) != 1:
        raise SystemExit(f"{label}: action counts or URI targets changed: URIs={uris!r} GoTo={gotos!r}")
    return gotos, action_kinds


installed_path = pathlib.Path(sys.argv[1])
forced_old_path = pathlib.Path(sys.argv[2])
without_path = pathlib.Path(sys.argv[3])
scheduled_path = pathlib.Path(sys.argv[5])
scheduled_without_path = pathlib.Path(sys.argv[6])
installed_gotos, _ = inspect(installed_path, "installed", True)
forced_old_gotos, _ = inspect(forced_old_path, "forced-old", True)
without_gotos, _ = inspect(
    without_path, "without-compat", sys.argv[4] == "native-present"
)
scheduled_gotos, scheduled_kinds = inspect(scheduled_path, "scheduled", True)
scheduled_without_gotos, _ = inspect(
    scheduled_without_path,
    "scheduled-without",
    sys.argv[4] == "native-present",
)
if installed_gotos != without_gotos:
    raise SystemExit("installed: compatibility source changed internal GoTo semantics or bytes")
if forced_old_gotos != without_gotos:
    raise SystemExit("forced-old: URI fallback changed internal GoTo semantics or bytes")
if (
    scheduled_gotos != scheduled_without_gotos
    or not scheduled_kinds
    or scheduled_kinds[0] != "/URI"
):
    raise SystemExit(
        "scheduled: production-order shim changed GoTo or did not fix the first-token URI"
    )
exercise_id_parser(without_path)
if sys.argv[4] == "native-present":
    require_native_equal_outside_trailer_id(installed_path, without_path)
    require_native_equal_outside_trailer_id(scheduled_path, scheduled_without_path)
PY

if [[ "$NATIVE" -eq 1 ]]; then
  : # The strict parser above permits only the input-dependent duplicated trailer /ID payload.
else
  if cmp -s "$TEST_ROOT/installed/compat-control.pdf" "$TEST_ROOT/without/compat-control.pdf"; then
    echo "hgeneric URI-Contents compatibility self-test failed: old-route control was inert" >&2
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
  echo "hgeneric URI-Contents compatibility self-test failed: bounded diagnostic control changed" >&2
  exit 1
fi
if [[ "$(printf '%s\n' \
    '! Package pid-rs Error: wrong text' \
    'expected needle only outside the package block' | compact_pidrs_diagnostic)" == \
    *"expectedneedle"* ]]; then
  echo "hgeneric URI-Contents compatibility self-test failed: diagnostic parser captured an unprefixed line" >&2
  exit 1
fi
if [[ "$(printf '%s\n' \
    '! Package pid-rs Error: wrong first block' \
    '! Package pid-rs Error: expected needle only in second block' | \
    compact_pidrs_diagnostic)" == *"expectedneedle"* ]]; then
  echo "hgeneric URI-Contents compatibility self-test failed: diagnostic parser captured a second package block" >&2
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
    echo "hgeneric URI-Contents compatibility self-test failed: $name rendered" >&2
    exit 1
  fi
  if [[ -e "$output_directory/must-not-render.pdf" \
      || -L "$output_directory/must-not-render.pdf" ]]; then
    echo "hgeneric URI-Contents compatibility self-test failed: $name published a PDF" >&2
    exit 1
  fi
  normalized="$(compact_pidrs_diagnostic <"$output_directory/stdout")"
  expected_compact="$(awk -v value="$message" 'BEGIN { gsub(/[[:space:]]/, "", value); print value }')"
  if [[ "$normalized" != *"$expected_compact"* ]]; then
    cat "$output_directory/stdout" >&2
    echo "hgeneric URI-Contents compatibility self-test failed: $name diagnostic changed" >&2
    exit 1
  fi
}

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/newer-native-absent.tex"
write_native_removal "$TEST_ROOT/newer-native-absent.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@hgeneric-testphase.def\endcsname{2024-03-01 unexpected-newer}' \
  '\input{hgeneric-uri-contents-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/newer-native-absent.tex"
expect_fatal \
  newer-native-absent \
  "$TEST_ROOT/newer-native-absent.tex" \
  'newer hgeneric lacks the reviewed native'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/ambiguous-v096y-policy.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@hgeneric-testphase.def\endcsname{2026-01-23 v0.96y}' \
  '\input{hgeneric-uri-contents-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/ambiguous-v096y-policy.tex"
expect_fatal \
  ambiguous-v096y-policy \
  "$TEST_ROOT/ambiguous-v096y-policy.tex" \
  'hgeneric is in or after the ambiguous v0.96y policy family'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/older-native-present.tex"
if [[ "$NATIVE" -eq 0 ]]; then
  printf '%s\n' '\ExplSyntaxOn\tl_new:N \l__hyp_link_Contents_tl\ExplSyntaxOff' \
    >>"$TEST_ROOT/older-native-present.tex"
fi
printf '%s\n' \
  '\expandafter\def\csname ver@hgeneric-testphase.def\endcsname{2023-12-09 unexpected-native}' \
  '\input{hgeneric-uri-contents-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/older-native-present.tex"
expect_fatal \
  older-native-present \
  "$TEST_ROOT/older-native-present.tex" \
  'unexpected older hgeneric has the native'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/ancient-fallback.tex"
write_native_removal "$TEST_ROOT/ancient-fallback.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@hgeneric-testphase.def\endcsname{2023-12-08 v0.96c}' \
  '\input{hgeneric-uri-contents-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/ancient-fallback.tex"
expect_fatal \
  ancient-fallback \
  "$TEST_ROOT/ancient-fallback.tex" \
  'hgeneric is older than the reviewed v0.96d fallback'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/version-suffix.tex"
write_native_removal "$TEST_ROOT/version-suffix.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@hgeneric-testphase.def\endcsname{2023-12-09 v0.96danger generic Hyperref driver for the LaTeX PDF management testphase bundle}' \
  '\input{hgeneric-uri-contents-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/version-suffix.tex"
expect_fatal \
  version-suffix \
  "$TEST_ROOT/version-suffix.tex" \
  'hgeneric version is not the reviewed v0.96d fallback'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/missing-insertion-point.tex"
write_native_removal "$TEST_ROOT/missing-insertion-point.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@hgeneric-testphase.def\endcsname{2023-12-09 v0.96d generic Hyperref driver for the LaTeX PDF management testphase bundle}' \
  '\makeatletter\long\def\hyper@linkurl#1#2{#1}\makeatother' \
  '\input{hgeneric-uri-contents-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/missing-insertion-point.tex"
expect_fatal \
  missing-insertion-point \
  "$TEST_ROOT/missing-insertion-point.tex" \
  'reviewed v0.96d URI-link insertion point is absent'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/duplicate.tex"
write_native_removal "$TEST_ROOT/duplicate.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@hgeneric-testphase.def\endcsname{2023-12-09 v0.96d generic Hyperref driver for the LaTeX PDF management testphase bundle}' \
  '\input{hgeneric-uri-contents-compat.tex}' \
  '\input{hgeneric-uri-contents-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/duplicate.tex"
expect_fatal duplicate "$TEST_ROOT/duplicate.tex" 'duplicate compatibility'

cp "$TEST_ROOT/preamble.tex" "$TEST_ROOT/missing-api.tex"
write_native_removal "$TEST_ROOT/missing-api.tex"
printf '%s\n' \
  '\expandafter\def\csname ver@hgeneric-testphase.def\endcsname{2023-12-09 v0.96d generic Hyperref driver for the LaTeX PDF management testphase bundle}' \
  '\ExplSyntaxOn\cs_undefine:N \__hyp_text_pdfstring:eoN\ExplSyntaxOff' \
  '\input{hgeneric-uri-contents-compat.tex}' \
  '\begin{document}must not render\end{document}' \
  >>"$TEST_ROOT/missing-api.tex"
expect_fatal missing-api "$TEST_ROOT/missing-api.tex" 'hgeneric PDF-string API is absent'

echo "hgeneric URI-Contents compatibility self-test passed: mode=$MODE controls=6 hostiles=14."
