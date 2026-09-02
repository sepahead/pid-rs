#!/usr/bin/env bash
# Verify only the canonical, same-toolchain blueprint publication relation.
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
BUILDER="$ROOT/scripts/build-pid-discovery-verification-blueprint.sh"
SOURCE="$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md"
COMMITTED="$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf"
HEADER="$ROOT/audit/formal/latex/pid-discovery-verification-and-durability-blueprint-header.tex"
FILTER="$ROOT/audit/formal/latex/pid-discovery-verification-and-durability-blueprint-filter.lua"
FIGURE_DIRECTORY="$ROOT/audit/formal/latex/figures/pid-discovery-verification-and-durability-blueprint"
SELF_TEST="$ROOT/scripts/check-pid-discovery-verification-blueprint-pdf-self-test.sh"
DECISION_V2="$ROOT/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md"
EVIDENCE_ADJUDICATION_INDEX="$ROOT/claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md"
CONVENTIONS="$ROOT/claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md"
PRIMARY_RETIREMENT_LEDGER="$ROOT/audit/evidence/worktree-and-branch-retirement-ledger-2026-09-01.json"
SIBLING_RETIREMENT_LEDGER="$ROOT/audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json"
VISUAL_RECEIPT="$ROOT/audit/evidence/pid-discovery-verification-durability-blueprint-visual-receipt-2026-09-02.md"
DECISION_V2_SHA256="f5bfef2afa6237661e031d416497e17f2aad01b17de61f15e9aba1a6e9ff6c59"
EVIDENCE_ADJUDICATION_INDEX_SHA256="0410df9f4163d2ccd2e4bb993fed9fd3d1598fae13bd3bc58cf30784966bbab4"
CONVENTIONS_SHA256="2d14bea9d6f0a2d07493ddaf7d89a130f4ad62680319cb9efba465590c2250c7"
PRIMARY_RETIREMENT_LEDGER_SHA256="29c6d6e0b2fe4b51b154e88be950db32ad214f64a67041c1ad215e756c8270bf"
SIBLING_RETIREMENT_LEDGER_SHA256="25b226abce58071ffa383753528300b7b2ef7203c47b07bb5f9a1b3b02e08420"
VISUAL_RECEIPT_SHA256="01e2e8b39aa27fd69f733ad1ee6c01f2de8f6e4e7b2e4e1c7e568ea47957d120"
VISUAL_RECEIPT_PDF_SHA256="18d034deb7f131e8e93170f4dd064980ab9f40cbdda208b512dbf68a58af3a0a"
CHECK_NAME="PID discovery/verification/durability blueprint PDF check"
MODE="${1:---exact}"
EXPECTED_PAGES=29
EXPECTED_PYPDF_VERSION="6.15.0"

if [[ "$#" -gt 1 || ( "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ) ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi
if [[ "$MODE" == "--cross-toolchain" ]]; then
  echo "$CHECK_NAME: no reviewed cross-toolchain equivalence relation or producer profile exists; no cross-toolchain acceptance is issued" >&2
  exit 2
fi

for command_name in awk bash cmp find grep mktemp pdffonts pdfinfo pdftoppm pdftotext \
    python3 rm shasum wc; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME: missing command: $command_name" >&2
    exit 2
  }
done

required_inputs=(
  "$BUILDER"
  "$SOURCE"
  "$COMMITTED"
  "$HEADER"
  "$FILTER"
  "$SELF_TEST"
  "$DECISION_V2"
  "$EVIDENCE_ADJUDICATION_INDEX"
  "$CONVENTIONS"
  "$PRIMARY_RETIREMENT_LEDGER"
  "$SIBLING_RETIREMENT_LEDGER"
  "$VISUAL_RECEIPT"
  "$FIGURE_DIRECTORY/semantic-transfer-firewall-source-card.svg"
  "$FIGURE_DIRECTORY/semantic-transfer-firewall-pid-card.svg"
  "$FIGURE_DIRECTORY/durable-promotion-state-machine-stages.svg"
  "$FIGURE_DIRECTORY/durable-promotion-state-machine-storage.svg"
)
for required_input in "${required_inputs[@]}"; do
  if [[ ! -f "$required_input" || -L "$required_input" ]]; then
    echo "$CHECK_NAME: required input is absent, non-regular, or symbolic: $required_input" >&2
    exit 1
  fi
done

require_sha256() {
  local path="$1" expected="$2" label="$3"
  local observed
  observed="$(shasum -a 256 "$path" | awk '{print $1}')"
  if [[ "$observed" != "$expected" ]]; then
    echo "$CHECK_NAME: $label identity drifted: expected $expected, observed $observed" >&2
    exit 1
  fi
}

require_unique_line() {
  local path="$1" literal="$2" label="$3"
  local count
  count="$(grep -Fxc -- "$literal" "$path" || true)"
  if [[ "$count" != "1" ]]; then
    echo "$CHECK_NAME: $label drifted; expected one exact line, observed $count" >&2
    exit 1
  fi
}

require_unique_fragment() {
  local path="$1" literal="$2" label="$3"
  local count
  count="$(grep -Fc -- "$literal" "$path" || true)"
  if [[ "$count" != "1" ]]; then
    echo "$CHECK_NAME: $label drifted; expected one exact fragment, observed $count" >&2
    exit 1
  fi
}

require_sha256 "$DECISION_V2" "$DECISION_V2_SHA256" "decision-v2 current-evidence"
require_sha256 "$EVIDENCE_ADJUDICATION_INDEX" "$EVIDENCE_ADJUDICATION_INDEX_SHA256" \
  "evidence-adjudication index"
require_sha256 "$CONVENTIONS" "$CONVENTIONS_SHA256" "frozen SxPID3 conventions"
require_sha256 "$PRIMARY_RETIREMENT_LEDGER" "$PRIMARY_RETIREMENT_LEDGER_SHA256" \
  "primary retirement ledger"
require_sha256 "$SIBLING_RETIREMENT_LEDGER" "$SIBLING_RETIREMENT_LEDGER_SHA256" \
  "sibling-registry retirement ledger"
require_sha256 "$VISUAL_RECEIPT" "$VISUAL_RECEIPT_SHA256" \
  "blueprint visual-review receipt"
require_sha256 "$COMMITTED" "$VISUAL_RECEIPT_PDF_SHA256" \
  "visual-review receipt subject PDF"

require_unique_line "$VISUAL_RECEIPT" \
  "schema: \`pid-rs/pid-discovery-verification-durability-blueprint-visual-review/v1\`" \
  "visual-review receipt schema"
require_unique_line "$VISUAL_RECEIPT" \
  "subject: \`PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf\`" \
  "visual-review receipt subject"
require_unique_line "$VISUAL_RECEIPT" \
  "pdf_sha256: \`$VISUAL_RECEIPT_PDF_SHA256\`" \
  "visual-review receipt PDF binding"
require_unique_line "$VISUAL_RECEIPT" "pages: \`29\`" \
  "visual-review receipt page scope"
require_unique_line "$VISUAL_RECEIPT" "color_120_dpi_pages_rendered: \`1-29\`" \
  "visual-review receipt color render scope"
require_unique_line "$VISUAL_RECEIPT" "color_120_dpi_pages_reviewed: \`1-29\`" \
  "visual-review receipt color review scope"
require_unique_line "$VISUAL_RECEIPT" "grayscale_120_dpi_pages_rendered: \`1-29\`" \
  "visual-review receipt grayscale render scope"
require_unique_line "$VISUAL_RECEIPT" "grayscale_120_dpi_pages_reviewed: \`1-29\`" \
  "visual-review receipt grayscale review scope"
require_unique_line "$VISUAL_RECEIPT" \
  "spot_300_dpi_pages_reviewed: \`1,3,13-16,21-29\`" \
  "visual-review receipt high-resolution spot scope"
require_unique_line "$VISUAL_RECEIPT" \
  "delta_reference_pdf_sha256: \`51a5d399cdcddbdf0ae4aea13a0d5726b79c8e81b417f845e0968b7e310e3d27\`" \
  "visual-review receipt predecessor binding"
require_unique_line "$VISUAL_RECEIPT" "delta_reference_pages: \`28\`" \
  "visual-review receipt predecessor page scope"
require_unique_line "$VISUAL_RECEIPT" "delta_120_dpi_raster_identical_pages: \`none\`" \
  "visual-review receipt unchanged-page boundary"
require_unique_line "$VISUAL_RECEIPT" \
  "delta_120_dpi_changed_or_added_pages_reviewed: \`1-29\`" \
  "visual-review receipt delta-review scope"
require_unique_line "$VISUAL_RECEIPT" "lens_count: \`20\`" \
  "visual-review receipt lens count"
require_unique_line "$VISUAL_RECEIPT" "status: \`passed\`" \
  "visual-review receipt disposition"

require_unique_line "$DECISION_V2" '**Disposition: proposed/open.**' \
  "decision-v2 disposition boundary"
require_unique_line "$DECISION_V2" \
  '**Complete target-implication evidence label: no accepted end-to-end evidence.**' \
  "decision-v2 complete-target boundary"
require_unique_fragment "$DECISION_V2" \
  'Neither result closes the prospective certificate implication.' \
  "decision-v2 scoped-result boundary"
require_unique_fragment "$DECISION_V2" \
  '| A: source and combinatorial semantics | Partial |' \
  "decision-v2 Program A status"
require_unique_fragment "$DECISION_V2" \
  '| B: dual formal semantics | Partial at the generic algebra layer |' \
  "decision-v2 Program B status"
require_unique_fragment "$DECISION_V2" \
  '| C: certified numerics | Bounded exact sign/zero partial result |' \
  "decision-v2 Program C status"
require_unique_fragment "$DECISION_V2" \
  '| D: compiled Rust refinement | Lexical routing observation only |' \
  "decision-v2 Program D status"
require_unique_fragment "$DECISION_V2" \
  '| E: replay, provenance, and adjudication | Source-bound local receipt and partial mutation evidence |' \
  "decision-v2 Program E status"
require_unique_fragment "$DECISION_V2" \
  '- 108 PID atoms, lattice nodes, or independent degrees of freedom;' \
  "decision-v2 108-expression taxonomy"
require_unique_fragment "$DECISION_V2" \
  '- the 166-position SxPID4 lattice;' \
  "decision-v2 four-source boundary"
require_unique_line "$EVIDENCE_ADJUDICATION_INDEX" \
  '| 1 | 2 | [claim-v1.md](claim-v1.md) | [decision-v2.md](decision-v2.md) | [evidence-matrix-v2.md](evidence-matrix-v2.md) | Current proposed/open decision; two scoped sub-results receive credit, but Programs A--E remain open |' \
  "evidence-adjudication current pointer/status boundary"
require_unique_fragment "$SOURCE" \
  'Decision record 2 keeps the complete target **proposed/open**;' \
  "blueprint current-decision summary"
require_unique_fragment "$SOURCE" \
  'None closes an end-to-end implication, and this report does not close the claim.' \
  "blueprint Program A--E status summary"

for required_link in \
    'claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md' \
    'claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md' \
    'claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#the-complete-18-node-carrier' \
    'audit/evidence/worktree-and-branch-preservation-2026-08-27.md' \
    'audit/evidence/worktree-and-branch-retirement-ledger-2026-09-01.json' \
    'audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json' \
    'audit/evidence/post-publication-custody-2026-09-02.md' \
    'audit/evidence/post-publication-custody-2026-09-02.json'; do
  if ! grep -Fq "]($required_link)" "$SOURCE"; then
    echo "$CHECK_NAME: source lacks required current-evidence link: $required_link" >&2
    exit 1
  fi
done

TMP_BASE_INPUT="${TMPDIR:-/tmp}"
if ! TMP_BASE="$(CDPATH='' cd -- "$TMP_BASE_INPUT" && pwd -P)"; then
  echo "$CHECK_NAME: cannot canonicalize temporary root: $TMP_BASE_INPUT" >&2
  exit 2
fi
if [[ "$TMP_BASE" == "/" ]]; then
  echo "$CHECK_NAME: refusing filesystem root as temporary root" >&2
  exit 2
fi
BUILD_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-blueprint-pdf-check.XXXXXX")"
cleanup() {
  local status="$1"
  trap - EXIT INT TERM
  case "$BUILD_ROOT" in
    "$TMP_BASE"/pid-rs-blueprint-pdf-check.*) rm -rf -- "$BUILD_ROOT" ;;
    *)
      echo "$CHECK_NAME: refusing unexpected cleanup path: $BUILD_ROOT" >&2
      status=1
      ;;
  esac
  exit "$status"
}
trap 'cleanup "$?"' EXIT
trap 'cleanup 130' INT
trap 'cleanup 143' TERM

BUILT="$BUILD_ROOT/rebuilt.pdf"
if ! TMPDIR="$BUILD_ROOT" bash --noprofile --norc "$BUILDER" "$BUILT" \
    >"$BUILD_ROOT/builder.stdout" 2>"$BUILD_ROOT/builder.stderr"; then
  cat "$BUILD_ROOT/builder.stdout" "$BUILD_ROOT/builder.stderr" >&2
  echo "$CHECK_NAME: builder failed" >&2
  exit 1
fi
if [[ -s "$BUILD_ROOT/builder.stderr" ]]; then
  cat "$BUILD_ROOT/builder.stderr" >&2
  echo "$CHECK_NAME: builder emitted stderr" >&2
  exit 1
fi

validate_pdf() {
  local label="$1" pdf="$2"
  local info="$BUILD_ROOT/$label.pdfinfo"
  local fonts="$BUILD_ROOT/$label.pdffonts"
  local text="$BUILD_ROOT/$label.txt"
  local render_prefix="$BUILD_ROOT/$label-page"
  local gray_render_prefix="$BUILD_ROOT/$label-gray-page"

  LC_ALL=C pdfinfo "$pdf" >"$info"
  LC_ALL=C pdffonts "$pdf" >"$fonts"
  LC_ALL=C pdftotext -layout "$pdf" "$text"
  local pages
  pages="$(awk '/^Pages:/ {print $2}' "$info")"
  if [[ "$pages" != "$EXPECTED_PAGES" ]]; then
    echo "$CHECK_NAME: $label page count differs: ${pages:-missing}; expected $EXPECTED_PAGES" >&2
    exit 1
  fi
  if ! grep -Eq '^Page size:[[:space:]]+595\.[0-9]+ x 841\.[0-9]+ pts \(A4\)$' "$info"; then
    echo "$CHECK_NAME: $label is not A4" >&2
    exit 1
  fi
  if ! grep -Eq '^PDF version:[[:space:]]+1\.7$' "$info"; then
    echo "$CHECK_NAME: $label is not PDF 1.7" >&2
    exit 1
  fi
  for metadata_line in \
      'Author:          pid-rs contributors' \
      'Subject:         Proposed PID discovery, verification, and durable-promotion architecture' \
      'Keywords:        partial information decomposition, SxPID3, formal verification, durable research workflow'; do
    if ! grep -Fqx "$metadata_line" "$info"; then
      echo "$CHECK_NAME: $label descriptive metadata drifted: $metadata_line" >&2
      exit 1
    fi
  done
  for metadata in \
      '^Tagged:[[:space:]]+no$' \
      '^Form:[[:space:]]+none$' \
      '^JavaScript:[[:space:]]+no$' \
      '^Encrypted:[[:space:]]+no$'; do
    if ! grep -Eq "$metadata" "$info"; then
      echo "$CHECK_NAME: $label PDF metadata omitted: $metadata" >&2
      exit 1
    fi
  done
  if ! awk '
    NR <= 2 { next }
    NF == 0 { next }
    { seen = 1; if ($(NF - 4) != "yes" || $(NF - 2) != "yes") bad = 1 }
    END { exit (!seen || bad) }
  ' "$fonts"; then
    echo "$CHECK_NAME: $label has a nonembedded or non-Unicode-mapped font" >&2
    exit 1
  fi
  for sentinel in \
      'PrimeGapsLib observations are dated 19 August 2026' \
      'Decision record 2 keeps the complete target' \
      '108 keyed scalar audit expressions' \
      'Dated 1 September 2026 adversarial publication closure' \
      'PASS identifies current-byte evidence' \
      'seventy typed rows in total' \
      'Twenty mandatory core lenses' \
      'Fifty additional artifact-specific hostile lenses' \
      'Ten materially distinct routes' \
      'D1 remains open' \
      'bounded corpus and optional shards' \
      'Semantic transfer firewall, part 1' \
      'Semantic transfer firewall, part 2' \
      'Durable promotion state machine, part 1' \
      'Durable promotion state machine, part 2' \
      'remote-ref, ancestry, hosted-run, and recovery-drill checks pass' \
      'There is no accepted cross-toolchain equivalence relation' \
      'Source-anchored claim register'; do
    if ! grep -Fq "$sentinel" "$text"; then
      echo "$CHECK_NAME: $label lacks rendered sentinel: $sentinel" >&2
      exit 1
    fi
  done
  if grep -Fq $'\357\277\275' "$text"; then
    echo "$CHECK_NAME: $label contains a Unicode replacement character" >&2
    exit 1
  fi
  if grep -Eq '\\begin\{|\\end\{|\.pdf\.pdf|[0-9]+\.[0-9]+\.[0-9]+\.' "$text"; then
    echo "$CHECK_NAME: $label exposes raw TeX, a doubled PDF suffix, or a doubly numbered heading" >&2
    exit 1
  fi
  if ! python3 -I - "$pdf" "$SOURCE" "$EXPECTED_PYPDF_VERSION" "$label" <<'PY'
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import sys

import pypdf
from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject


pdf_path = Path(sys.argv[1])
source_path = Path(sys.argv[2])
expected_pypdf_version = sys.argv[3]
label = sys.argv[4]


def fail(detail: str) -> None:
    raise SystemExit(f"{label} PDF navigation/action check failed: {detail}")


if pypdf.__version__ != expected_pypdf_version:
    fail(
        f"pypdf version differs: {pypdf.__version__}; "
        f"expected {expected_pypdf_version}"
    )

markdown = source_path.read_text(encoding="utf-8")
github_navigation_links = {
    "claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md":
        "https://github.com/sepahead/pid-rs/blob/main/claims/"
        "SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md",
    "claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md":
        "https://github.com/sepahead/pid-rs/blob/main/claims/"
        "SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md",
    "claims/SX-CERTIFIED-AVERAGED-PID3-001/revision-index.md":
        "https://github.com/sepahead/pid-rs/blob/main/claims/"
        "SX-CERTIFIED-AVERAGED-PID3-001/revision-index.md",
    "claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#the-complete-18-node-carrier":
        "https://github.com/sepahead/pid-rs/blob/main/claims/"
        "SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#the-complete-18-node-carrier",
    "audit/evidence/worktree-and-branch-preservation-2026-08-27.md":
        "https://github.com/sepahead/pid-rs/blob/main/audit/evidence/"
        "worktree-and-branch-preservation-2026-08-27.md",
    "audit/evidence/worktree-and-branch-retirement-ledger-2026-09-01.json":
        "https://github.com/sepahead/pid-rs/blob/main/audit/evidence/"
        "worktree-and-branch-retirement-ledger-2026-09-01.json",
    "audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json":
        "https://github.com/sepahead/pid-rs/blob/main/audit/evidence/"
        "sibling-registry-retirement-ledger-2026-09-01.json",
    "audit/evidence/post-publication-custody-2026-09-02.md":
        "https://github.com/sepahead/pid-rs/blob/main/audit/evidence/"
        "post-publication-custody-2026-09-02.md",
    "audit/evidence/post-publication-custody-2026-09-02.json":
        "https://github.com/sepahead/pid-rs/blob/main/audit/evidence/"
        "post-publication-custody-2026-09-02.json",
}
expected_uris: Counter[str] = Counter()
for target in re.findall(r"\]\(([^)]+)\)", markdown):
    if target.startswith(("http://", "https://")):
        if not target.startswith("https://"):
            fail(f"canonical source contains a non-HTTPS link: {target}")
        expected_uris[target] += 1
    elif target in github_navigation_links:
        expected_uris[github_navigation_links[target]] += 1

try:
    reader = PdfReader(pdf_path, strict=True)
except Exception as error:
    fail(f"cannot parse strictly: {error}")

metadata = reader.metadata
expected_pdf_date = "D:20260902000000Z"
if metadata is None or metadata.get("/CreationDate") != expected_pdf_date or metadata.get("/ModDate") != expected_pdf_date:
    fail("deterministic creation/modification chronology metadata drifted")


def resolve(value):
    return value.get_object() if isinstance(value, IndirectObject) else value


def object_identity(value) -> tuple[object, ...]:
    if isinstance(value, IndirectObject):
        return ("indirect", value.idnum, value.generation)
    return ("direct", id(value))


root_ref = reader.trailer.raw_get("/Root")
root = resolve(root_ref)
if not isinstance(root, DictionaryObject):
    fail("catalog is not a dictionary")
catalog_owner_identities = {object_identity(root_ref), object_identity(root)}
for forbidden_key in ("/AA", "/AF", "/Collection", "/AcroForm"):
    if root.get(forbidden_key) is not None:
        fail(f"catalog contains forbidden active/associated content: {forbidden_key}")
if root.get("/Dests") is not None:
    fail("catalog contains a competing legacy /Dests dictionary")
names = resolve(root.get("/Names", DictionaryObject()))
if not isinstance(names, DictionaryObject):
    fail("catalog /Names is not a dictionary")
unexpected_name_trees = set(map(str, names.keys())) - {"/Dests"}
if unexpected_name_trees:
    fail(f"catalog contains an unapproved name tree: {sorted(unexpected_name_trees)}")


def validate_catalog_open_action(action_value, location: str) -> None:
    action = resolve(action_value)
    if not isinstance(action, DictionaryObject):
        fail(f"{location} is not an action dictionary")
    if set(map(str, action.keys())) != {"/S", "/D"}:
        fail(f"{location} has unexpected keys: {sorted(map(str, action.keys()))}")
    if str(action.get("/S")) != "/GoTo":
        fail(f"{location} is not the intended catalog /GoTo action")
    destination = resolve(action.get("/D"))
    if not isinstance(destination, ArrayObject) or len(destination) != 2:
        fail(f"{location} destination is not the intended first-page /Fit array")
    page_ref, fit = destination
    first_page_ref = reader.pages[0].indirect_reference
    if (
        not isinstance(page_ref, IndirectObject)
        or first_page_ref is None
        or page_ref.idnum != first_page_ref.idnum
        or page_ref.generation != first_page_ref.generation
        or str(fit) != "/Fit"
    ):
        fail(f"{location} destination differs from the intended first-page /Fit view")


catalog_open_action = root.get("/OpenAction")
if catalog_open_action is None:
    fail("catalog lacks the intended first-page /Fit OpenAction")
validate_catalog_open_action(catalog_open_action, "catalog /OpenAction")


named_destination_names = set(reader.named_destinations)


def validate_named_goto_action(action_value, location: str) -> str:
    action = resolve(action_value)
    if not isinstance(action, DictionaryObject):
        fail(f"{location} lacks one action dictionary")
    if set(map(str, action.keys())) != {"/S", "/D"}:
        fail(f"{location} GoTo action has unexpected keys")
    if str(action.get("/S")) != "/GoTo":
        fail(f"{location} has forbidden action: {action.get('/S')}")
    destination = resolve(action.get("/D"))
    if not isinstance(destination, str) or destination not in named_destination_names:
        fail(f"{location} has an absent or non-named /GoTo destination")
    return destination


def validate_link_action(action_value, location: str) -> tuple[str, object]:
    action = resolve(action_value)
    if not isinstance(action, DictionaryObject):
        fail(f"{location} lacks one action dictionary")
    if action.get("/Next") is not None:
        fail(f"{location} action contains a chained /Next action")
    action_kind = str(action.get("/S"))
    if action_kind == "/URI":
        if set(map(str, action.keys())) != {"/Type", "/S", "/URI"}:
            fail(f"{location} URI action has unexpected keys")
        if str(action.get("/Type")) != "/Action":
            fail(f"{location} URI action lacks the canonical /Action type")
        uri = str(action.get("/URI", ""))
        if not uri.startswith("https://"):
            fail(f"{location} has a non-HTTPS URI: {uri}")
        if uri not in expected_uris:
            fail(f"{location} has an undeclared URI: {uri}")
        return "URI", uri
    if action_kind == "/GoTo":
        return "GoTo", validate_named_goto_action(action, location)
    fail(f"{location} has forbidden action: {action_kind}")


def same_indirect_reference(left, right) -> bool:
    return (
        isinstance(left, IndirectObject)
        and isinstance(right, IndirectObject)
        and left.idnum == right.idnum
        and left.generation == right.generation
    )


authorized_outline_owners: set[tuple[object, ...]] = set()
seen_outline_items: set[tuple[object, ...]] = set()


def collect_outline_siblings(first_ref, expected_parent_ref, location: str) -> None:
    current_ref = first_ref
    sibling_chain: set[tuple[object, ...]] = set()
    ordinal = 0
    while current_ref is not None:
        ordinal += 1
        current_identity = object_identity(current_ref)
        if current_identity in sibling_chain or current_identity in seen_outline_items:
            fail(f"{location} contains a cyclic or multiply owned outline item")
        sibling_chain.add(current_identity)
        seen_outline_items.add(current_identity)
        current = resolve(current_ref)
        if not isinstance(current, DictionaryObject):
            fail(f"{location} item {ordinal} is not a dictionary")
        if not same_indirect_reference(current.get("/Parent"), expected_parent_ref):
            fail(f"{location} item {ordinal} has an unexpected parent")
        if not str(current.get("/Title", "")).strip():
            fail(f"{location} item {ordinal} lacks a title")
        if current.get("/Dest") is not None:
            fail(f"{location} item {ordinal} uses an unbound direct destination")
        action = current.get("/A")
        validate_named_goto_action(action, f"{location} item {ordinal}")
        authorized_outline_owners.update(
            {current_identity, object_identity(current)}
        )
        child = current.get("/First")
        if child is not None:
            collect_outline_siblings(child, current_ref, f"{location} item {ordinal} children")
        current_ref = current.get("/Next")


outlines_ref = root.get("/Outlines")
outlines = resolve(outlines_ref)
if not isinstance(outlines_ref, IndirectObject) or not isinstance(outlines, DictionaryObject):
    fail("catalog /Outlines is absent or not an indirect dictionary")
outline_first = outlines.get("/First")
if outline_first is None:
    fail("catalog /Outlines lacks its first item")
collect_outline_siblings(outline_first, outlines_ref, "outline")


observed_uris: Counter[str] = Counter()
authorized_link_owners: set[tuple[object, ...]] = set()
for page_number, page in enumerate(reader.pages, start=1):
    for forbidden_key in ("/AA", "/AF", "/A", "/OpenAction", "/PresSteps", "/Trans"):
        if page.get(forbidden_key) is not None:
            fail(f"page {page_number} contains forbidden active content: {forbidden_key}")
    annotations = resolve(page.get("/Annots", ArrayObject()))
    if not isinstance(annotations, ArrayObject):
        fail(f"page {page_number} /Annots is not an array")
    for annotation_number, annotation_ref in enumerate(annotations, start=1):
        annotation = resolve(annotation_ref)
        if not isinstance(annotation, DictionaryObject):
            fail(f"page {page_number} annotation {annotation_number} is not a dictionary")
        if str(annotation.get("/Subtype")) != "/Link":
            fail(
                f"page {page_number} annotation {annotation_number} has forbidden subtype: "
                f"{annotation.get('/Subtype')}"
            )
        authorized_link_owners.update(
            {object_identity(annotation_ref), object_identity(annotation)}
        )
        if annotation.get("/AA") is not None:
            fail(f"page {page_number} annotation {annotation_number} has additional actions")
        if annotation.get("/Dest") is not None:
            fail(f"page {page_number} annotation {annotation_number} uses an unbound /Dest route")
        for forbidden_key in ("/AF", "/FS", "/RichMediaContent", "/RichMediaSettings"):
            if annotation.get(forbidden_key) is not None:
                if forbidden_key == "/FS":
                    fail(
                        "embedded or external file specification appears at "
                        f"page {page_number} annotation {annotation_number}"
                    )
                fail(
                    f"page {page_number} annotation {annotation_number} contains forbidden "
                    f"content: {forbidden_key}"
                )
        try:
            flags = int(annotation.get("/F", 0))
        except Exception:
            fail(f"page {page_number} annotation {annotation_number} has malformed flags")
        if flags != 0:
            fail(
                f"page {page_number} annotation {annotation_number} has noncanonical flags: "
                f"{flags}"
            )
        action_kind, action_target = validate_link_action(
            annotation.get("/A"), f"page {page_number} annotation {annotation_number}"
        )
        if action_kind == "URI":
            observed_uris[str(action_target)] += 1

if set(observed_uris) != set(expected_uris):
    fail(
        "rendered/source URI inventories differ: "
        f"missing={sorted(set(expected_uris) - set(observed_uris))}, "
        f"unexpected={sorted(set(observed_uris) - set(expected_uris))}"
    )
for uri, source_count in expected_uris.items():
    if observed_uris[uri] < source_count:
        fail(
            f"rendered URI occurrence count is too small for {uri}: "
            f"{observed_uris[uri]} < {source_count}"
        )

forbidden_annotation_subtypes = {
    "/3D", "/FileAttachment", "/Movie", "/RichMedia", "/Screen", "/Sound",
}
forbidden_dictionary_keys = {
    "/AA", "/AF", "/Collection", "/EF", "/EmbeddedFiles", "/JavaScript", "/JS",
    "/PresSteps", "/RichMediaContent", "/RichMediaSettings", "/XFA",
}
standard_action_types = {
    "/GoTo", "/GoTo3DView", "/GoToE", "/GoToR", "/Hide", "/ImportData",
    "/JavaScript", "/Launch", "/Movie", "/Named", "/Rendition", "/ResetForm",
    "/RichMediaExecute", "/SetOCGState", "/Sound", "/SubmitForm", "/Thread",
    "/Trans", "/URI",
}
seen_indirect: set[tuple[int, int, str | None]] = set()
seen_direct: set[tuple[int, str | None]] = set()


def walk(value, location: str, authorized_action: str | None = None) -> None:
    owner_identity = object_identity(value)
    if isinstance(value, IndirectObject):
        identity = (value.idnum, value.generation, authorized_action)
        if identity in seen_indirect:
            return
        seen_indirect.add(identity)
        try:
            value = value.get_object()
        except Exception as error:
            fail(f"cannot resolve object at {location}: {error}")
    elif isinstance(value, (DictionaryObject, ArrayObject)):
        identity = (id(value), authorized_action)
        if identity in seen_direct:
            return
        seen_direct.add(identity)
    if isinstance(value, DictionaryObject):
        object_type = str(value.get("/Type"))
        subtype = str(value.get("/Subtype"))
        action_kind = str(value.get("/S"))
        declares_action = object_type == "/Action" or action_kind in standard_action_types
        if declares_action:
            if authorized_action == "catalog-open":
                validate_catalog_open_action(value, location)
            elif authorized_action == "link":
                validate_link_action(value, location)
            elif authorized_action == "outline":
                validate_named_goto_action(value, location)
            else:
                fail(f"reachable object contains an action outside an authorized edge at {location}")
        if object_type == "/Filespec" or subtype in forbidden_annotation_subtypes:
            fail(f"embedded or external file specification appears at {location}")
        present = forbidden_dictionary_keys.intersection(map(str, value.keys()))
        if present:
            fail(f"forbidden active/embedded keys appear at {location}: {sorted(present)}")
        if value.get("/URI") is not None and not (
            authorized_action == "link" and action_kind == "/URI"
        ):
            fail(f"non-annotation URI appears at {location}")
        for key, child in value.items():
            key_name = str(key)
            child_location = f"{location}/{key_name}"
            if key_name == "/OpenAction":
                if owner_identity not in catalog_owner_identities:
                    fail(f"OpenAction appears outside the catalog at {child_location}")
                validate_catalog_open_action(child, child_location)
                walk(child, child_location, authorized_action="catalog-open")
            elif key_name == "/A":
                if owner_identity in authorized_link_owners:
                    validate_link_action(child, child_location)
                    walk(child, child_location, authorized_action="link")
                elif owner_identity in authorized_outline_owners:
                    validate_named_goto_action(child, child_location)
                    walk(child, child_location, authorized_action="outline")
                else:
                    fail(
                        "action edge appears outside a declared link annotation or outline item "
                        f"at {child_location}"
                    )
            else:
                walk(child, child_location)
    elif isinstance(value, ArrayObject):
        for index, child in enumerate(value):
            walk(child, f"{location}[{index}]")


walk(reader.trailer, "trailer")
PY
  then
    exit 1
  fi
  pdftoppm -f 1 -l "$pages" -r 120 -png "$pdf" "$render_prefix" >/dev/null 2>&1
  pdftoppm -f 1 -l "$pages" -r 120 -gray -png "$pdf" "$gray_render_prefix" >/dev/null 2>&1
  local rendered_count
  rendered_count="$(find "$BUILD_ROOT" -maxdepth 1 -type f -name "$label-page-*.png" -size +0c | wc -l | awk '{print $1}')"
  if [[ "$rendered_count" != "$pages" ]]; then
    echo "$CHECK_NAME: $label did not render every nonempty color page" >&2
    exit 1
  fi
  local gray_rendered_count
  gray_rendered_count="$(find "$BUILD_ROOT" -maxdepth 1 -type f -name "$label-gray-page-*.png" -size +0c | wc -l | awk '{print $1}')"
  if [[ "$gray_rendered_count" != "$pages" ]]; then
    echo "$CHECK_NAME: $label did not render every nonempty grayscale page" >&2
    exit 1
  fi
}

validate_pdf rebuilt "$BUILT"
validate_pdf committed "$COMMITTED"

if ! cmp -s "$BUILT" "$COMMITTED"; then
  echo "$CHECK_NAME: committed PDF is stale or not same-toolchain reproducible" >&2
  exit 1
fi

printf 'OK: %s exact committed-byte relation passed (sha256=%s)\n' \
  "$CHECK_NAME" "$(shasum -a 256 "$COMMITTED" | awk '{print $1}')"
