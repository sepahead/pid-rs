#!/usr/bin/env bash
# Hostile controls for the exact-only blueprint PDF gate.
# Hostile mutations below intentionally pass single-quoted shell-source fragments as data.
# shellcheck disable=SC2016
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
CHECKER="$ROOT/scripts/check-pid-discovery-verification-blueprint-pdf.sh"
BUILDER="$ROOT/scripts/build-pid-discovery-verification-blueprint.sh"
CHECK_NAME="PID blueprint PDF check self-test"

for command_name in awk bash cmp cp grep mkdir mktemp mv python3 rm shasum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME: missing command: $command_name" >&2
    exit 2
  }
done
for path in \
    "$CHECKER" \
    "$BUILDER" \
    "$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf" \
    "$ROOT/audit/evidence/pid-discovery-verification-durability-blueprint-visual-receipt-2026-09-02.md"; do
  [[ -f "$path" && ! -L "$path" ]] || {
    echo "$CHECK_NAME: required production input is absent, non-regular, or symbolic: $path" >&2
    exit 2
  }
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
TEST_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-blueprint-pdf-self-test.XXXXXX")"
cleanup() {
  local status="$1"
  trap - EXIT INT TERM
  case "$TEST_ROOT" in
    "$TMP_BASE"/pid-rs-blueprint-pdf-self-test.*) rm -rf -- "$TEST_ROOT" ;;
    *) echo "$CHECK_NAME: refusing unexpected cleanup path: $TEST_ROOT" >&2; status=1 ;;
  esac
  exit "$status"
}
trap 'cleanup "$?"' EXIT
trap 'cleanup 130' INT
trap 'cleanup 143' TERM

PASS_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'ok %d - %s\n' "$PASS_COUNT" "$1"; }

replace_once() {
  local path="$1" before="$2" after="$3"
  python3 -I -S - "$path" "$before" "$after" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
before = sys.argv[2]
after = sys.argv[3]
text = path.read_text(encoding="utf-8")
if text.count(before) != 1:
    raise SystemExit(f"mutation anchor count is {text.count(before)}, expected one: {before!r}")
path.write_text(text.replace(before, after, 1), encoding="utf-8", newline="\n")
PY
}

reseal_fixture_input() {
  local fixture="$1" variable="$2" relative="$3"
  local checker="$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh"
  local old_digest new_digest
  old_digest="$(awk -F'"' -v prefix="$variable=" '$0 ~ ("^" prefix) {print $2}' "$checker")"
  new_digest="$(shasum -a 256 "$fixture/$relative" | awk '{print $1}')"
  if [[ ! "$old_digest" =~ ^[0-9a-f]{64}$ || ! "$new_digest" =~ ^[0-9a-f]{64}$ ]]; then
    echo "$CHECK_NAME: cannot reseal hostile fixture input: $variable" >&2
    exit 1
  fi
  replace_once "$checker" "$old_digest" "$new_digest"
}

make_fixture() {
  local fixture="$1"
  mkdir -p \
    "$fixture/scripts" \
    "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001" \
    "$fixture/audit/evidence" \
    "$fixture/audit/formal/latex/figures/pid-discovery-verification-and-durability-blueprint"
  cp "$CHECKER" "$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh"
  cp "$ROOT/scripts/check-pid-discovery-verification-blueprint-pdf-self-test.sh" "$fixture/scripts/"
  cp "$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md" "$fixture/"
  cp "$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf" "$fixture/"
  cp "$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf" "$fixture/expected-builder-output.pdf"
  cp "$ROOT/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md" "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/"
  cp "$ROOT/claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md" "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/"
  cp "$ROOT/claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md" "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/"
  cp "$ROOT/audit/evidence/worktree-and-branch-retirement-ledger-2026-09-01.json" "$fixture/audit/evidence/"
  cp "$ROOT/audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json" "$fixture/audit/evidence/"
  cp "$ROOT/audit/evidence/pid-discovery-verification-durability-blueprint-visual-receipt-2026-09-02.md" "$fixture/audit/evidence/"
  cp "$ROOT/audit/formal/latex/pid-discovery-verification-and-durability-blueprint-header.tex" "$fixture/audit/formal/latex/"
  cp "$ROOT/audit/formal/latex/pid-discovery-verification-and-durability-blueprint-filter.lua" "$fixture/audit/formal/latex/"
  cp "$ROOT/audit/formal/latex/figures/pid-discovery-verification-and-durability-blueprint/"*.svg "$fixture/audit/formal/latex/figures/pid-discovery-verification-and-durability-blueprint/"
  cat >"$fixture/scripts/build-pid-discovery-verification-blueprint.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
[[ "$#" -eq 1 ]] || exit 2
cp "$ROOT/expected-builder-output.pdf" "$1"
printf 'OK: fixture same-toolchain builder\n'
EOF
  chmod 0755 "$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh" "$fixture/scripts/build-pid-discovery-verification-blueprint.sh"
}

expect_success() {
  local fixture="$1"
  if ! TMPDIR="$TEST_ROOT/" bash --noprofile --norc "$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh" >"$fixture/out" 2>"$fixture/err"; then
    cat "$fixture/out" "$fixture/err" >&2
    echo "$CHECK_NAME: exact fixture was rejected" >&2
    exit 1
  fi
  grep -Fq 'exact committed-byte relation passed' "$fixture/out" || {
    cat "$fixture/out" >&2
    echo "$CHECK_NAME: exact fixture success contract changed" >&2
    exit 1
  }
}

expect_failure() {
  local fixture="$1" needle="$2"
  if TMPDIR="$TEST_ROOT/" bash --noprofile --norc "$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh" >"$fixture/out" 2>"$fixture/err"; then
    echo "$CHECK_NAME: hostile fixture was accepted" >&2
    exit 1
  fi
  grep -Fq "$needle" "$fixture/err" || {
    cat "$fixture/out" "$fixture/err" >&2
    echo "$CHECK_NAME: hostile fixture failed for a noncausal reason" >&2
    exit 1
  }
}

make_pdf_pair_mutant() {
  local fixture="$1" mode="$2"
  python3 -I - "$fixture" "$mode" <<'PY'
from pathlib import Path
import os
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, NumberObject, TextStringObject


fixture = Path(sys.argv[1])
mode = sys.argv[2]


def mutate(path: Path) -> None:
    if mode == "pdf-version":
        data = path.read_bytes()
        if data.count(b"%PDF-1.7") != 1:
            raise SystemExit("PDF-version mutation target drifted")
        temporary = path.with_suffix(path.suffix + ".mutant")
        temporary.write_bytes(data.replace(b"%PDF-1.7", b"%PDF-1.6", 1))
        os.replace(temporary, path)
        return

    reader = PdfReader(path, strict=True)
    writer = PdfWriter(clone_from=reader)
    writer.pdf_header = reader.pdf_header
    changed = False

    if mode == "page-count":
        writer.remove_page(len(writer.pages) - 1)
        changed = True
    elif mode == "metadata-author":
        writer.add_metadata({"/Author": "unbound author"})
        changed = True
    elif mode == "page-aa-file-uri":
        writer.pages[0][NameObject("/AA")] = DictionaryObject(
            {
                NameObject("/O"): DictionaryObject(
                    {
                        NameObject("/S"): NameObject("/URI"),
                        NameObject("/URI"): TextStringObject("file:///tmp/blocked"),
                    }
                )
            }
        )
        changed = True
    elif mode == "catalog-aa":
        writer.root_object[NameObject("/AA")] = DictionaryObject(
            {
                NameObject("/WC"): DictionaryObject(
                    {
                        NameObject("/S"): NameObject("/ResetForm"),
                    }
                )
            }
        )
        changed = True
    elif mode == "catalog-open-action-named":
        action_reference = writer.root_object.get("/OpenAction")
        action = action_reference.get_object() if action_reference is not None else None
        if not isinstance(action, DictionaryObject):
            raise SystemExit("catalog OpenAction mutation target drifted")
        action[NameObject("/S")] = NameObject("/Named")
        action[NameObject("/N")] = NameObject("/Print")
        action.pop(NameObject("/D"), None)
        changed = True
    elif mode == "nonannotation-uri":
        writer.root_object[NameObject("/HostileUriCarrier")] = DictionaryObject(
            {
                NameObject("/URI"): TextStringObject(
                    "https://github.com/sepahead/pid-rs"
                )
            }
        )
        changed = True
    elif mode == "nonannotation-action":
        writer.root_object[NameObject("/HostileActionCarrier")] = DictionaryObject(
            {
                NameObject("/S"): NameObject("/ResetForm"),
            }
        )
        changed = True
    else:
        for page in writer.pages:
            for annotation_reference in page.get("/Annots", []):
                annotation = annotation_reference.get_object()
                action_reference = annotation.get("/A")
                action = action_reference.get_object() if action_reference is not None else None
                if not isinstance(action, DictionaryObject) or str(action.get("/S")) != "/URI":
                    continue
                if mode == "relative-uri":
                    action[NameObject("/URI")] = TextStringObject(
                        "audit/evidence/worktree-and-branch-preservation-2026-08-27.md"
                    )
                elif mode == "unknown-https":
                    action[NameObject("/URI")] = TextStringObject(
                        "https://example.invalid/undeclared-blueprint-source"
                    )
                elif mode == "javascript":
                    action[NameObject("/S")] = NameObject("/JavaScript")
                    action[NameObject("/JS")] = TextStringObject("app.alert('blocked')")
                    action.pop(NameObject("/URI"), None)
                elif mode == "launch":
                    action[NameObject("/S")] = NameObject("/Launch")
                    action[NameObject("/F")] = TextStringObject("blocked.bin")
                    action.pop(NameObject("/URI"), None)
                elif mode == "named":
                    action[NameObject("/S")] = NameObject("/Named")
                    action[NameObject("/N")] = NameObject("/Print")
                    action.pop(NameObject("/URI"), None)
                elif mode == "hide":
                    action[NameObject("/S")] = NameObject("/Hide")
                    action[NameObject("/T")] = TextStringObject("blocked")
                    action.pop(NameObject("/URI"), None)
                elif mode == "reset-form":
                    action[NameObject("/S")] = NameObject("/ResetForm")
                    action.pop(NameObject("/URI"), None)
                elif mode == "additional-action":
                    annotation[NameObject("/AA")] = DictionaryObject(
                        {
                            NameObject("/E"): DictionaryObject(
                                {
                                    NameObject("/S"): NameObject("/JavaScript"),
                                    NameObject("/JS"): TextStringObject("blocked"),
                                }
                            )
                        }
                    )
                elif mode == "hidden-flag":
                    annotation[NameObject("/F")] = NumberObject(2)
                elif mode == "filespec":
                    annotation[NameObject("/FS")] = DictionaryObject(
                        {
                            NameObject("/Type"): NameObject("/Filespec"),
                            NameObject("/F"): TextStringObject("blocked.bin"),
                        }
                    )
                else:
                    raise SystemExit(f"unknown PDF mutation mode: {mode}")
                changed = True
                break
            if changed:
                break
    if not changed:
        raise SystemExit(f"PDF mutation target drifted: {mode}")
    temporary = path.with_suffix(path.suffix + ".mutant")
    with temporary.open("wb") as stream:
        writer.write(stream)
    os.replace(temporary, path)


for name in (
    "PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf",
    "expected-builder-output.pdf",
):
    mutate(fixture / name)
PY
  reseal_fixture_visual_receipt_pdf "$fixture"
}

reseal_fixture_visual_receipt_pdf() {
  local fixture="$1"
  local checker="$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh"
  local receipt="$fixture/audit/evidence/pid-discovery-verification-durability-blueprint-visual-receipt-2026-09-02.md"
  local old_digest new_digest
  old_digest="$(awk -F'"' '/^VISUAL_RECEIPT_PDF_SHA256=/ {print $2}' "$checker")"
  new_digest="$(shasum -a 256 "$fixture/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf" | awk '{print $1}')"
  if [[ ! "$old_digest" =~ ^[0-9a-f]{64}$ || ! "$new_digest" =~ ^[0-9a-f]{64}$ ]]; then
    echo "$CHECK_NAME: cannot reseal hostile fixture visual-receipt PDF binding" >&2
    exit 1
  fi
  replace_once "$checker" \
    "VISUAL_RECEIPT_PDF_SHA256=\"$old_digest\"" \
    "VISUAL_RECEIPT_PDF_SHA256=\"$new_digest\""
  replace_once "$receipt" \
    "pdf_sha256: \`$old_digest\`" \
    "pdf_sha256: \`$new_digest\`"
  reseal_fixture_input "$fixture" VISUAL_RECEIPT_SHA256 \
    "audit/evidence/pid-discovery-verification-durability-blueprint-visual-receipt-2026-09-02.md"
}

run_resealed_decision_mutation() {
  local slug="$1" label="$2" before="$3" after="$4" needle="$5"
  local fixture="$TEST_ROOT/$slug"
  make_fixture "$fixture"
  replace_once \
    "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md" \
    "$before" \
    "$after"
  reseal_fixture_input "$fixture" DECISION_V2_SHA256 \
    "claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md"
  expect_failure "$fixture" "$needle"
  pass "$label"
}

expect_cross_status() {
  local fixture="$1" expected="$2"
  local observed
  if TMPDIR="$TEST_ROOT/" bash --noprofile --norc \
      "$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh" \
      --cross-toolchain >"$fixture/cross.out" 2>"$fixture/cross.err"; then
    observed=0
  else
    observed=$?
  fi
  if [[ "$observed" -ne "$expected" ]]; then
    cat "$fixture/cross.out" "$fixture/cross.err" >&2
    echo "$CHECK_NAME: cross refusal returned $observed, expected $expected" >&2
    return 1
  fi
  grep -Fq 'no reviewed cross-toolchain equivalence relation or producer profile exists' \
    "$fixture/cross.err" || {
      cat "$fixture/cross.err" >&2
      echo "$CHECK_NAME: cross refusal diagnostic changed" >&2
      return 1
    }
}

validate_checker_contract() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
lines = text.splitlines()
required_lines = (
    'require_sha256 "$DECISION_V2" "$DECISION_V2_SHA256" "decision-v2 current-evidence"',
    'require_sha256 "$PRIMARY_RETIREMENT_LEDGER" "$PRIMARY_RETIREMENT_LEDGER_SHA256" \\',
    'require_sha256 "$SIBLING_RETIREMENT_LEDGER" "$SIBLING_RETIREMENT_LEDGER_SHA256" \\',
    'require_sha256 "$VISUAL_RECEIPT" "$VISUAL_RECEIPT_SHA256" \\',
    'require_sha256 "$COMMITTED" "$VISUAL_RECEIPT_PDF_SHA256" \\',
    '  "pdf_sha256: \\`$VISUAL_RECEIPT_PDF_SHA256\\`" \\',
    'require_unique_line "$VISUAL_RECEIPT" "color_120_dpi_pages_reviewed: \\`1-29\\`" \\',
    'require_unique_line "$VISUAL_RECEIPT" "grayscale_120_dpi_pages_reviewed: \\`1-29\\`" \\',
    '  "spot_300_dpi_pages_reviewed: \\`1,3,13-16,21-29\\`" \\',
    'require_unique_line "$VISUAL_RECEIPT" "lens_count: \\`20\\`" \\',
    'require_unique_line "$VISUAL_RECEIPT" "status: \\`passed\\`" \\',
    'validate_catalog_open_action(catalog_open_action, "catalog /OpenAction")',
    '    for forbidden_key in ("/AA", "/AF", "/A", "/OpenAction", "/PresSteps", "/Trans"):',
    '        authorized_link_owners.update(',
    'collect_outline_siblings(outline_first, outlines_ref, "outline")',
    '        if declares_action:',
    '        if value.get("/URI") is not None and not (',
    '            fail(f"non-annotation URI appears at {location}")',
    '                if owner_identity in authorized_link_owners:',
    '                elif owner_identity in authorized_outline_owners:',
    '    "/JavaScript", "/Launch", "/Movie", "/Named", "/Rendition", "/ResetForm",',
    'require_unique_line "$DECISION_V2" \'**Disposition: proposed/open.**\' \\',
    '    \'claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#the-complete-18-node-carrier\' \\',
    '    \'audit/evidence/worktree-and-branch-retirement-ledger-2026-09-01.json\' \\',
    '    \'audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json\' \\',
    '    \'audit/evidence/post-publication-custody-2026-09-02.md\' \\',
    '    \'audit/evidence/post-publication-custody-2026-09-02.json\'; do',
    '  if [[ "$pages" != "$EXPECTED_PAGES" ]]; then',
    '  if ! grep -Eq \'^Page size:[[:space:]]+595\\.[0-9]+ x 841\\.[0-9]+ pts \\(A4\\)$\' "$info"; then',
    '  if ! grep -Eq \'^PDF version:[[:space:]]+1\\.7$\' "$info"; then',
    '      \'^Tagged:[[:space:]]+no$\' \\',
    "      'Author:          pid-rs contributors' \\",
    '      \'Dated 1 September 2026 adversarial publication closure\' \\',
    '      \'PASS identifies current-byte evidence\' \\',
    '      \'seventy typed rows in total\' \\',
    '      \'Twenty mandatory core lenses\' \\',
    '      \'Fifty additional artifact-specific hostile lenses\' \\',
    '      \'D1 remains open\' \\',
    '      \'bounded corpus and optional shards\' \\',
    '      \'remote-ref, ancestry, hosted-run, and recovery-drill checks pass\' \\',
    '  if ! python3 -I - "$pdf" "$SOURCE" "$EXPECTED_PYPDF_VERSION" "$label" <<\'PY\'',
    'expected_pdf_date = "D:20260902000000Z"',
    '    fail("deterministic creation/modification chronology metadata drifted")',
    '  pdftoppm -f 1 -l "$pages" -r 120 -png "$pdf" "$render_prefix" >/dev/null 2>&1',
    '  pdftoppm -f 1 -l "$pages" -r 120 -gray -png "$pdf" "$gray_render_prefix" >/dev/null 2>&1',
    'validate_pdf rebuilt "$BUILT"',
    'validate_pdf committed "$COMMITTED"',
    'if ! cmp -s "$BUILT" "$COMMITTED"; then',
)
for line in required_lines:
    if lines.count(line) != 1:
        raise SystemExit(f"checker contract line drifted: {line!r}")
cross_block = '''if [[ "$MODE" == "--cross-toolchain" ]]; then
  echo "$CHECK_NAME: no reviewed cross-toolchain equivalence relation or producer profile exists; no cross-toolchain acceptance is issued" >&2
  exit 2
fi
'''
if text.count(cross_block) != 1:
    raise SystemExit("checker cross-toolchain refusal block drifted")
metadata_block = '''  for metadata in \\
      '^Tagged:[[:space:]]+no$' \\
      '^Form:[[:space:]]+none$' \\
      '^JavaScript:[[:space:]]+no$' \\
      '^Encrypted:[[:space:]]+no$'; do
'''
if text.count(metadata_block) != 1:
    raise SystemExit("checker PDF metadata block drifted")
font_predicate = 'if ($(NF - 4) != "yes" || $(NF - 2) != "yes") bad = 1'
if text.count(font_predicate) != 1:
    raise SystemExit("checker embedded-font predicate drifted")
for raster_count in (
    'if [[ "$rendered_count" != "$pages" ]]; then',
    'if [[ "$gray_rendered_count" != "$pages" ]]; then',
):
    if text.count(raster_count) != 1:
        raise SystemExit(f"checker all-page raster-count predicate drifted: {raster_count!r}")
ordered = (
    'require_sha256 "$DECISION_V2"',
    'require_sha256 "$VISUAL_RECEIPT"',
    'require_unique_line "$VISUAL_RECEIPT"',
    'for required_link in',
    'validate_pdf() {',
    'validate_pdf rebuilt "$BUILT"',
    'validate_pdf committed "$COMMITTED"',
    'if ! cmp -s "$BUILT" "$COMMITTED"; then',
)
positions = [text.index(item) for item in ordered]
if positions != sorted(positions):
    raise SystemExit("checker evidence/build/validation order drifted")
PY
}

run_contract_mutation() {
  local label="$1" before="$2" after="$3"
  local mutant="$TEST_ROOT/checker-contract-$PASS_COUNT.sh"
  cp "$CHECKER" "$mutant"
  replace_once "$mutant" "$before" "$after"
  if validate_checker_contract "$mutant" \
      >"$TEST_ROOT/checker-contract-$PASS_COUNT.out" \
      2>"$TEST_ROOT/checker-contract-$PASS_COUNT.err"; then
    echo "$CHECK_NAME: checker contract mutation was accepted: $label" >&2
    exit 1
  fi
  pass "$label"
}

fixture="$TEST_ROOT/positive"
make_fixture "$fixture"
expect_success "$fixture"
pass "exact fixture accepts matching committed bytes with a trailing-slash temporary root"

validate_checker_contract "$CHECKER"
pass "production checker retains the load-bearing exact/status/PDF validation contract"

expect_cross_status "$fixture" 2
pass "cross-toolchain mode refuses with exact status 2 and no invented profile"

run_contract_mutation "page-count weakening is rejected" \
  '"$pages" != "$EXPECTED_PAGES"' '"$pages" -lt 1'
run_contract_mutation "A4 predicate drift is rejected" \
  '\(A4\)$' '\(Letter\)$'
run_contract_mutation "PDF-version predicate drift is rejected" \
  "'^PDF version:[[:space:]]+1\\.7$'" "'^PDF version:[[:space:]]+1\\.6$'"
run_contract_mutation "metadata predicate drift is rejected" \
  "'^Encrypted:[[:space:]]+no$'" "'^Encrypted:[[:space:]]+yes$'"
run_contract_mutation "embedded-font predicate drift is rejected" \
  '$(NF - 4) != "yes"' '$(NF - 4) != "no"'
run_contract_mutation "current-closure sentinel removal is rejected" \
  "'Dated 1 September 2026 adversarial publication closure'" \
  "'Current publication closure omitted'"
run_contract_mutation "all-page raster command drift is rejected" \
  'pdftoppm -f 1 -l "$pages" -r 120 -png' 'pdftoppm -f 1 -l 1 -r 120 -png'
run_contract_mutation "all-page grayscale command drift is rejected" \
  'pdftoppm -f 1 -l "$pages" -r 120 -gray -png' \
  'pdftoppm -f 1 -l 1 -r 120 -gray -png'
run_contract_mutation "all-page raster count weakening is rejected" \
  '"$rendered_count" != "$pages"' '"$rendered_count" -lt 1'
run_contract_mutation "all-page grayscale count weakening is rejected" \
  '"$gray_rendered_count" != "$pages"' '"$gray_rendered_count" -lt 1'
run_contract_mutation "navigation/action audit bypass is rejected" \
  'if ! python3 -I - "$pdf" "$SOURCE" "$EXPECTED_PYPDF_VERSION" "$label"' \
  'if ! true # navigation/action audit omitted'
run_contract_mutation "rebuilt-PDF validation bypass is rejected" \
  'validate_pdf rebuilt "$BUILT"' '# validate rebuilt omitted'
run_contract_mutation "committed-PDF validation bypass is rejected" \
  'validate_pdf committed "$COMMITTED"' '# validate committed omitted'
run_contract_mutation "committed-byte comparison inversion is rejected" \
  'if ! cmp -s "$BUILT" "$COMMITTED"; then' \
  'if cmp -s "$BUILT" "$COMMITTED"; then'
run_contract_mutation "decision freshness invocation removal is rejected" \
  'require_sha256 "$DECISION_V2" "$DECISION_V2_SHA256" "decision-v2 current-evidence"' \
  '# decision freshness omitted'
run_contract_mutation "visual-receipt identity invocation removal is rejected" \
  "require_sha256 \"\$VISUAL_RECEIPT\" \"\$VISUAL_RECEIPT_SHA256\" \\" \
  "# visual-receipt identity omitted \\"
run_contract_mutation "visual-receipt subject-PDF binding removal is rejected" \
  "require_sha256 \"\$COMMITTED\" \"\$VISUAL_RECEIPT_PDF_SHA256\" \\" \
  "# visual-receipt subject-PDF binding omitted \\"
run_contract_mutation "visual-receipt review-scope weakening is rejected" \
  'color_120_dpi_pages_reviewed: \`1-29\`' \
  'color_120_dpi_pages_reviewed: \`1-1\`'
run_contract_mutation "visual-receipt disposition weakening is rejected" \
  'status: \`passed\`' \
  'status: \`not-reviewed\`'
run_contract_mutation "catalog OpenAction validation removal is rejected" \
  'validate_catalog_open_action(catalog_open_action, "catalog /OpenAction")' \
  '# catalog OpenAction validation omitted'
run_contract_mutation "page active-content predicate weakening is rejected" \
  'for forbidden_key in ("/AA", "/AF", "/A", "/OpenAction", "/PresSteps", "/Trans"):' \
  'for forbidden_key in ("/AF", "/A", "/OpenAction", "/PresSteps", "/Trans"):'
run_contract_mutation "deep unauthorized-action predicate weakening is rejected" \
  'if declares_action:' \
  'if False and declares_action:'
run_contract_mutation "non-annotation URI predicate weakening is rejected" \
  'if value.get("/URI") is not None and not (' \
  'if False and value.get("/URI") is not None and not ('
run_contract_mutation "link-owner predicate weakening is rejected" \
  'if owner_identity in authorized_link_owners:' \
  'if True or owner_identity in authorized_link_owners:'
run_contract_mutation "outline-owner predicate weakening is rejected" \
  'elif owner_identity in authorized_outline_owners:' \
  'elif True or owner_identity in authorized_outline_owners:'
run_contract_mutation "retirement-ledger link binding removal is rejected" \
  "    'audit/evidence/worktree-and-branch-retirement-ledger-2026-09-01.json' \\" \
  "    'audit/evidence/worktree-and-branch-retirement-ledger-omitted.json' \\"
run_contract_mutation "sibling-ledger link binding removal is rejected" \
  "    'audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json' \\" \
  "    'audit/evidence/sibling-registry-retirement-ledger-omitted.json' \\"
run_contract_mutation "cross refusal status weakening is rejected" \
  $'no cross-toolchain acceptance is issued" >&2\n  exit 2' \
  $'no cross-toolchain acceptance is issued" >&2\n  exit 1'

fixture="$TEST_ROOT/stale"
make_fixture "$fixture"
printf '\n%% stale trailing byte\n' >>"$fixture/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf"
reseal_fixture_visual_receipt_pdf "$fixture"
expect_failure "$fixture" "committed PDF is stale or not same-toolchain reproducible"
pass "committed-byte drift rejects"

fixture="$TEST_ROOT/missing-builder"
make_fixture "$fixture"
rm -f -- "$fixture/scripts/build-pid-discovery-verification-blueprint.sh"
expect_failure "$fixture" "required input is absent, non-regular, or symbolic"
pass "missing builder rejects before publication comparison"

fixture="$TEST_ROOT/decision-identity"
make_fixture "$fixture"
printf '\nidentity mutation\n' \
  >>"$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md"
expect_failure "$fixture" "decision-v2 current-evidence identity drifted"
pass "unresealed decision-v2 byte drift rejects"

fixture="$TEST_ROOT/decision-disposition-resealed"
make_fixture "$fixture"
replace_once \
  "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md" \
  '**Disposition: proposed/open.**' \
  '**Disposition: accepted.**'
reseal_fixture_input "$fixture" DECISION_V2_SHA256 \
  "claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md"
expect_failure "$fixture" "decision-v2 disposition boundary drifted"
pass "coordinated decision digest reseal cannot promote the disposition"

run_resealed_decision_mutation \
  "complete-target-resealed" \
  "coordinated decision digest reseal cannot invent complete target evidence" \
  '**Complete target-implication evidence label: no accepted end-to-end evidence.**' \
  '**Complete target-implication evidence label: accepted end-to-end evidence.**' \
  "decision-v2 complete-target boundary drifted"

run_resealed_decision_mutation \
  "scoped-results-resealed" \
  "coordinated decision digest reseal cannot turn scoped results into closure" \
  'Neither result closes the prospective certificate implication.' \
  'Together the results close the prospective certificate implication.' \
  "decision-v2 scoped-result boundary drifted"

run_resealed_decision_mutation \
  "program-a-resealed" \
  "coordinated decision digest reseal cannot upgrade Program A" \
  '| A: source and combinatorial semantics | Partial |' \
  '| A: source and combinatorial semantics | Complete |' \
  "decision-v2 Program A status drifted"

run_resealed_decision_mutation \
  "program-b-resealed" \
  "coordinated decision digest reseal cannot upgrade Program B" \
  '| B: dual formal semantics | Partial at the generic algebra layer |' \
  '| B: dual formal semantics | Complete |' \
  "decision-v2 Program B status drifted"

run_resealed_decision_mutation \
  "program-c-resealed" \
  "coordinated decision digest reseal cannot upgrade Program C" \
  '| C: certified numerics | Bounded exact sign/zero partial result |' \
  '| C: certified numerics | Complete accepted result |' \
  "decision-v2 Program C status drifted"

run_resealed_decision_mutation \
  "program-d-resealed" \
  "coordinated decision digest reseal cannot upgrade Program D" \
  '| D: compiled Rust refinement | Lexical routing observation only |' \
  '| D: compiled Rust refinement | Complete compiled refinement |' \
  "decision-v2 Program D status drifted"

run_resealed_decision_mutation \
  "program-e-resealed" \
  "coordinated decision digest reseal cannot upgrade Program E" \
  '| E: replay, provenance, and adjudication | Source-bound local receipt and partial mutation evidence |' \
  '| E: replay, provenance, and adjudication | Complete external replay and adjudication |' \
  "decision-v2 Program E status drifted"

run_resealed_decision_mutation \
  "taxonomy-108-resealed" \
  "coordinated decision digest reseal cannot relabel 108 expressions as atoms" \
  '- 108 PID atoms, lattice nodes, or independent degrees of freedom;' \
  '- 108 scalar expressions, all of which are PID atoms;' \
  "decision-v2 108-expression taxonomy drifted"

run_resealed_decision_mutation \
  "taxonomy-166-resealed" \
  "coordinated decision digest reseal cannot import the SxPID4 carrier" \
  '- the 166-position SxPID4 lattice;' \
  '- inclusion of the 166-position SxPID4 lattice;' \
  "decision-v2 four-source boundary drifted"

fixture="$TEST_ROOT/current-index-resealed"
make_fixture "$fixture"
replace_once \
  "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md" \
  'Current proposed/open decision; two scoped sub-results receive credit, but Programs A--E remain open' \
  'Current accepted decision; all Programs A--E are closed'
reseal_fixture_input "$fixture" EVIDENCE_ADJUDICATION_INDEX_SHA256 \
  "claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md"
expect_failure "$fixture" "evidence-adjudication current pointer/status boundary drifted"
pass "coordinated index digest reseal cannot change the current status"

fixture="$TEST_ROOT/conventions-identity"
make_fixture "$fixture"
printf '\nidentity mutation\n' \
  >>"$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md"
expect_failure "$fixture" "frozen SxPID3 conventions identity drifted"
pass "frozen conventions byte drift rejects"

fixture="$TEST_ROOT/missing-conventions-link"
make_fixture "$fixture"
replace_once \
  "$fixture/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md" \
  'claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#the-complete-18-node-carrier' \
  'claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#omitted'
expect_failure "$fixture" "source lacks required current-evidence link"
pass "missing complete-registry link rejects"

fixture="$TEST_ROOT/visual-receipt-identity"
make_fixture "$fixture"
printf '\nidentity mutation\n' \
  >>"$fixture/audit/evidence/pid-discovery-verification-durability-blueprint-visual-receipt-2026-09-02.md"
expect_failure "$fixture" "blueprint visual-review receipt identity drifted"
pass "unresealed blueprint visual-review receipt byte drift rejects"

fixture="$TEST_ROOT/visual-receipt-scope-resealed"
make_fixture "$fixture"
replace_once \
  "$fixture/audit/evidence/pid-discovery-verification-durability-blueprint-visual-receipt-2026-09-02.md" \
  'color_120_dpi_pages_reviewed: `1-29`' \
  'color_120_dpi_pages_reviewed: `1-1`'
reseal_fixture_input "$fixture" VISUAL_RECEIPT_SHA256 \
  "audit/evidence/pid-discovery-verification-durability-blueprint-visual-receipt-2026-09-02.md"
expect_failure "$fixture" "visual-review receipt color review scope drifted"
pass "coordinated visual-receipt digest reseal cannot weaken the reviewed page scope"

fixture="$TEST_ROOT/visual-receipt-status-resealed"
make_fixture "$fixture"
replace_once \
  "$fixture/audit/evidence/pid-discovery-verification-durability-blueprint-visual-receipt-2026-09-02.md" \
  'status: `passed`' \
  'status: `not-reviewed`'
reseal_fixture_input "$fixture" VISUAL_RECEIPT_SHA256 \
  "audit/evidence/pid-discovery-verification-durability-blueprint-visual-receipt-2026-09-02.md"
expect_failure "$fixture" "visual-review receipt disposition drifted"
pass "coordinated visual-receipt digest reseal cannot substitute an unreviewed disposition"

fixture="$TEST_ROOT/sibling-ledger-identity"
make_fixture "$fixture"
printf '\n' >>"$fixture/audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json"
expect_failure "$fixture" "sibling-registry retirement ledger identity drifted"
pass "unresealed sibling-registry ledger byte drift rejects"

fixture="$TEST_ROOT/missing-sibling-ledger-link"
make_fixture "$fixture"
replace_once \
  "$fixture/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md" \
  '[sibling-registry retirement ledger](audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json)' \
  '[sibling-registry retirement ledger](audit/evidence/sibling-registry-retirement-ledger-omitted.json)'
replace_once \
  "$fixture/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md" \
  '[machine-readable sibling-registry ledger](audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json)' \
  '[machine-readable sibling-registry ledger](audit/evidence/sibling-registry-retirement-ledger-omitted.json)'
expect_failure "$fixture" "source lacks required current-evidence link"
pass "missing sibling-registry ledger link rejects"

fixture="$TEST_ROOT/missing-svg"
make_fixture "$fixture"
rm -f -- \
  "$fixture/audit/formal/latex/figures/pid-discovery-verification-and-durability-blueprint/semantic-transfer-firewall-source-card.svg"
expect_failure "$fixture" "required input is absent, non-regular, or symbolic"
pass "missing declared SVG source rejects"

fixture="$TEST_ROOT/pdf-version"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" pdf-version
expect_failure "$fixture" "rebuilt is not PDF 1.7"
pass "coordinated PDF-version drift rejects"

fixture="$TEST_ROOT/page-count"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" page-count
expect_failure "$fixture" "rebuilt page count differs: 28; expected 29"
pass "coordinated page-count drift rejects"

fixture="$TEST_ROOT/relative-uri"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" relative-uri
expect_failure "$fixture" "has a non-HTTPS URI"
pass "relative PDF URI rejects even when builder and committed bytes agree"

fixture="$TEST_ROOT/unknown-https"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" unknown-https
expect_failure "$fixture" "has an undeclared URI"
pass "undeclared HTTPS PDF URI rejects"

fixture="$TEST_ROOT/page-aa-file-uri"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" page-aa-file-uri
expect_failure "$fixture" "page 1 contains forbidden active content: /AA"
pass "page additional-action dictionary rejects even when it carries a file URI"

fixture="$TEST_ROOT/catalog-aa"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" catalog-aa
expect_failure "$fixture" "catalog contains forbidden active/associated content: /AA"
pass "catalog additional-action dictionary rejects"

fixture="$TEST_ROOT/catalog-open-action-named"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" catalog-open-action-named
expect_failure "$fixture" "catalog /OpenAction has unexpected keys"
pass "catalog OpenAction rejects a Named action in place of the intended first-page GoTo"

fixture="$TEST_ROOT/metadata-author"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" metadata-author
expect_failure "$fixture" "descriptive metadata drifted"
pass "coordinated descriptive-metadata drift rejects"

fixture="$TEST_ROOT/javascript"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" javascript
expect_failure "$fixture" "has forbidden action: /JavaScript"
pass "JavaScript PDF action rejects"

fixture="$TEST_ROOT/launch"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" launch
expect_failure "$fixture" "has forbidden action: /Launch"
pass "launch PDF action rejects"

fixture="$TEST_ROOT/named"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" named
expect_failure "$fixture" "has forbidden action: /Named"
pass "Named link action rejects"

fixture="$TEST_ROOT/hide"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" hide
expect_failure "$fixture" "has forbidden action: /Hide"
pass "Hide link action rejects"

fixture="$TEST_ROOT/reset-form"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" reset-form
expect_failure "$fixture" "has forbidden action: /ResetForm"
pass "ResetForm link action rejects"

fixture="$TEST_ROOT/additional-action"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" additional-action
expect_failure "$fixture" "has additional actions"
pass "annotation additional-action dictionary rejects"

fixture="$TEST_ROOT/hidden-flag"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" hidden-flag
expect_failure "$fixture" "has noncanonical flags: 2"
pass "hidden annotation flag rejects"

fixture="$TEST_ROOT/filespec"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" filespec
expect_failure "$fixture" "embedded or external file specification"
pass "embedded or external file specification rejects"

fixture="$TEST_ROOT/nonannotation-uri"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" nonannotation-uri
expect_failure "$fixture" "non-annotation URI appears"
pass "non-annotation URI carrier rejects"

fixture="$TEST_ROOT/nonannotation-action"
make_fixture "$fixture"
make_pdf_pair_mutant "$fixture" nonannotation-action
expect_failure "$fixture" "action outside an authorized edge"
pass "undeclared non-annotation action carrier rejects"

actual_output="$TEST_ROOT/actual-trailing-slash.pdf"
TMPDIR="$TEST_ROOT/" bash --noprofile --norc "$BUILDER" "$actual_output" >"$TEST_ROOT/actual.out" 2>"$TEST_ROOT/actual.err" || {
  cat "$TEST_ROOT/actual.out" "$TEST_ROOT/actual.err" >&2
  echo "$CHECK_NAME: production builder rejected a trailing-slash temporary root" >&2
  exit 1
}
[[ -s "$actual_output" && ! -L "$actual_output" ]] || {
  echo "$CHECK_NAME: production builder did not create its trailing-slash regression artifact" >&2
  exit 1
}
pass "production builder canonicalizes a trailing-slash temporary root"

printf 'OK: %s passed %d checks\n' "$CHECK_NAME" "$PASS_COUNT"
