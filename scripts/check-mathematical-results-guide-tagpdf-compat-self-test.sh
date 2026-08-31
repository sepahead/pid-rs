#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
COMPAT_SHA256=6b638ef882260e54ad619b1ec9bfa775e7e8ecce04b24932ba41ca0e55e91f17

for command_name in cat cp dirname env grep kpsewhich mkdir mktemp pdflatex python3 rm shasum; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "tagpdf OpenAction compatibility self-test failed: missing command: $command_name" >&2
    exit 1
  fi
done
if [[ ! -f "$COMPAT" || -L "$COMPAT" ]]; then
  echo "tagpdf OpenAction compatibility self-test failed: compatibility source is absent or symbolic" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$COMPAT_SHA256" "$COMPAT" | shasum -a 256 --check --status; then
  echo "tagpdf OpenAction compatibility self-test failed: compatibility source digest changed" >&2
  exit 1
fi

TAGPDF_STY="$(kpsewhich tagpdf.sty)"
if [[ -z "$TAGPDF_STY" || ! -f "$TAGPDF_STY" || -L "$TAGPDF_STY" ]]; then
  echo "tagpdf OpenAction compatibility self-test failed: tagpdf source is absent or symbolic" >&2
  exit 1
fi

TMP_BASE="${TMPDIR:-/tmp}"
while [[ "$TMP_BASE" != "/" && "$TMP_BASE" == */ ]]; do
  TMP_BASE="${TMP_BASE%/}"
done
TEST_ROOT="$(mktemp -d "${TMP_BASE%/}/pid-rs-tagpdf-openaction-compat-self-test.XXXXXX")"
cleanup() {
  case "$TEST_ROOT" in
    "${TMP_BASE%/}"/pid-rs-tagpdf-openaction-compat-self-test.*)
      rm -rf -- "$TEST_ROOT"
      ;;
    *)
      echo "tagpdf OpenAction compatibility self-test cleanup refused unexpected path: $TEST_ROOT" >&2
      ;;
  esac
}
trap cleanup EXIT INT TERM
cp "$COMPAT" "$TEST_ROOT/tagpdf-openaction-compat.tex"
mkdir "$TEST_ROOT/home"

if grep -Fq '\__tag_tree_update_openaction:' "$TAGPDF_STY"; then
  MODE=forced-v0.98w
  cat >"$TEST_ROOT/control.tex" <<'TEX'
\DocumentMetadata{
  lang=en-US,
  pdfstandard=ua-2,
  testphase={phase-III,title,table,math,firstaid}
}
\documentclass{article}
\usepackage{hyperref}
\hypersetup{pdfstartview=Fit}
\ExplSyntaxOn
% Remove the entire native tagpdf last-page chunk before undefining its called
% function, then restore only the pre-OpenAction MarkInfo/StructTreeRoot work.
\hook_gremove_code:nn { shipout/lastpage } { tagpdf }
\hook_gput_code:nnn { shipout/lastpage } { tagpdf }
  {
    \bool_if:NT \g__tag_active_tree_bool
      {
        \pdfmanagement_add:nnn { Catalog / MarkInfo } { Marked } { true }
        \pdfmanagement_add:nne
          { Catalog }
          { StructTreeRoot }
          { \pdf_object_ref:n { __tag/struct/0 } }
      }
  }
\cs_undefine:N \__tag_tree_update_openaction:
\ExplSyntaxOff
\expandafter\def\csname ver@tagpdf.sty\endcsname{2024/02/22 v0.98w}
\input{tagpdf-openaction-compat.tex}
\begin{document}
Forced tagpdf v0.98w compatibility control.
\end{document}
TEX
else
  MODE=native-function-absent
  cat >"$TEST_ROOT/control.tex" <<'TEX'
\DocumentMetadata{
  lang=en-US,
  pdfstandard=ua-2,
  testphase={phase-III,title,table,math,firstaid}
}
\documentclass{article}
\usepackage{hyperref}
\hypersetup{pdfstartview=Fit}
\input{tagpdf-openaction-compat.tex}
\begin{document}
Native-function-absent tagpdf compatibility control.
\end{document}
TEX
fi

cat >"$TEST_ROOT/newer-without-native.tex" <<'TEX'
\DocumentMetadata{
  lang=en-US,
  pdfstandard=ua-2,
  testphase={phase-III,title,table,math,firstaid}
}
\documentclass{article}
\usepackage{hyperref}
\ExplSyntaxOn
\cs_if_exist:NT \__tag_tree_update_openaction:
  {
    \hook_gremove_code:nn { shipout/lastpage } { tagpdf }
    \cs_undefine:N \__tag_tree_update_openaction:
  }
\ExplSyntaxOff
\expandafter\def\csname ver@tagpdf.sty\endcsname{2024/02/23 unexpected-newer}
\input{tagpdf-openaction-compat.tex}
\begin{document}
This document must not render.
\end{document}
TEX
if env -i PATH="$PATH" HOME="$TEST_ROOT/home" TMPDIR="$TEST_ROOT" \
    LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH=1787875200 \
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$TEST_ROOT" \
      "$TEST_ROOT/newer-without-native.tex" >"$TEST_ROOT/newer-without-native.stdout" 2>&1
then
  echo "tagpdf OpenAction compatibility self-test failed: newer native-absent package rendered" >&2
  exit 1
fi
if [[ -e "$TEST_ROOT/newer-without-native.pdf" || -L "$TEST_ROOT/newer-without-native.pdf" ]]; then
  echo "tagpdf OpenAction compatibility self-test failed: newer native-absent fatal published a PDF" >&2
  exit 1
fi
if ! grep -Fq 'newer tagpdf lacks the reviewed native' "$TEST_ROOT/newer-without-native.stdout"; then
  cat "$TEST_ROOT/newer-without-native.stdout" >&2
  echo "tagpdf OpenAction compatibility self-test failed: newer native-absent fatal changed" >&2
  exit 1
fi

for run in first second; do
  if ! env -i PATH="$PATH" HOME="$TEST_ROOT/home" TMPDIR="$TEST_ROOT" \
      LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH=1787875200 \
      pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$TEST_ROOT" \
        "$TEST_ROOT/control.tex" >"$TEST_ROOT/$run.log" 2>&1
  then
    cat "$TEST_ROOT/$run.log" >&2
    echo "tagpdf OpenAction compatibility self-test failed: $run TeX run failed" >&2
    exit 1
  fi
done

python3 -I -B - "$TEST_ROOT/control.pdf" "$MODE" <<'PY'
import pathlib
import sys

from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject

pdf_path = pathlib.Path(sys.argv[1])
mode = sys.argv[2]
reader = PdfReader(pdf_path, strict=True)
root = reader.trailer["/Root"]
action = root.raw_get("/OpenAction")
if not isinstance(action, DictionaryObject):
    raise SystemExit(f"{mode}: OpenAction is not a direct dictionary")
if action.get("/S") != NameObject("/GoTo"):
    raise SystemExit(f"{mode}: OpenAction /S is not /GoTo")

destination = action.raw_get("/D")
if not isinstance(destination, ArrayObject) or len(destination) != 2:
    raise SystemExit(f"{mode}: OpenAction /D is not a two-element array")
page_ref = reader.pages[0].indirect_reference
if destination[0] != page_ref or destination[1] != NameObject("/Fit"):
    raise SystemExit(f"{mode}: OpenAction /D does not target page one with /Fit")

structure_destination = action.raw_get("/SD")
if not isinstance(structure_destination, ArrayObject) or len(structure_destination) != 2:
    raise SystemExit(f"{mode}: OpenAction /SD is not a two-element array")
struct_root = root.raw_get("/StructTreeRoot")
if not isinstance(struct_root, IndirectObject):
    raise SystemExit(f"{mode}: StructTreeRoot is not indirect")
root_k = struct_root.get_object().raw_get("/K")
if isinstance(root_k, ArrayObject):
    if not root_k:
        raise SystemExit(f"{mode}: StructTreeRoot/K is empty")
    document_ref = root_k[0]
else:
    document_ref = root_k
if not isinstance(document_ref, IndirectObject):
    raise SystemExit(f"{mode}: StructTreeRoot/K document target is not indirect")
if document_ref.get_object().get("/S") != NameObject("/Document"):
    raise SystemExit(f"{mode}: StructTreeRoot/K target is not the Document structure")
if structure_destination[0] != document_ref or structure_destination[1] != NameObject("/Fit"):
    raise SystemExit(f"{mode}: OpenAction /SD does not target StructTreeRoot/K[0] with /Fit")

print(
    "tagpdf OpenAction compatibility self-test passed: "
    f"mode={mode} pages={len(reader.pages)} "
    f"page_object={page_ref.idnum} structure_object={document_ref.idnum} "
    "newer_native_absent_fatal=2024-02-23"
)
PY
