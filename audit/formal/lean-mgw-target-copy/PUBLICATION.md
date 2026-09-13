# Publication record for the finite target-copy MGW note

The [standalone note](../../evidence/finite-target-copy-mgw-synergy.md) derives
finite categorical identities for the shared-exclusions PID of Makkeh,
Gutknecht, and Wibral (MGW). This revision explains the target-copy model's
provenance, compares named PID definitions on the copy benchmark, and separates
signed MGW synergy from additional Shannon information. Its eleven local Lean
targets are unchanged. Scientific priority for the repository derivations has
not been established.

## Current source and PDF

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| [Markdown](../../evidence/finite-target-copy-mgw-synergy.md) | 33,464 | `63c6adeb1f9078213e323ba895057e0e949315df45bd33d46ae6fb9e69714671` |
| [13-page A4 PDF](../../../output/pdf/finite-target-copy-mgw-synergy.pdf) | 182,631 | `b22f6b079cdbc28af184d2f88fe9a71a4e689e37804017decc15dd06e46f7a58` |

The [SVG](../latex/figures/mgw-target-copy/event-union.svg) is unchanged, with
SHA-256 `280d19e9b63659ebe9aeaba74e09d11476be729a784c612f0a69679e05d3a22c`.
Its two source-law grids distinguish the source-match OR event from the anchor
cell. The formula below them shows why the positive target-event and full-key
masses cancel. The complete joint source law determines target-copy synergy;
the union mass alone is insufficient.

The note distinguishes this categorical construction from Williams–Beer
`I_min`, Harder–Salge–Polani redundancy, BROJA unique information, and Ehrlich
and coauthors' continuous shared exclusions. The comparison concerns their
definitions and stated axioms. It is not an estimator-accuracy ranking.
The practical discussion compares synergy with conditional mutual information
and measured prediction loss, using explicit model and sampling assumptions.

## Exact reproduction

Two fresh local builds on 13 September 2026 matched the reviewed PDF byte for
byte. Both retained text extractions were identical: 46,074 bytes. Each PDF has
13 A4 pages and 24 embedded font entries with Unicode mappings. Both final TeX
logs passed the warning, missing-character and box-diagnostic checks.
First-pass cross-reference warnings were retained and resolved by pass two.

Run the public reproduction command with the selected programs on `PATH`:

```text
python3 -I -S -B scripts/build-finite-target-copy-mgw-pdf.py --check --tex-root <selected-tex-live-2024-root> --work-dir <new-build-directory>
```

The [v4 input profile](../latex/mgw-target-copy/publication-inputs-v4.json) binds
six document inputs, six executable files and version strings, 231 selected
TeX files, sixteen font aliases, the source epoch and the exact reference PDF.
Its SHA-256 is
`8cc3f3d71fa218539f21b10a07f0e65c0b42c9ff2a8569f33c2b151b4ecf5f46`.
The selected tools include Pandoc 3.10.2, LuaHBTeX from TeX Live 2024,
Poppler 26.06.0 and librsvg 2.62.3. The build retains
`SOURCE_DATE_EPOCH=1789084800`, disables shell escape, and uses a restricted
child environment and the repository's report styles.

The [builder](../../../scripts/build-finite-target-copy-mgw-pdf.py) creates two
fresh build directories and runs two LuaLaTeX passes per build. It retains each
command's output, rejects nonzero status and unexpected stderr, checks final
diagnostics, fonts, A4 geometry, the exact page count and nonempty extracted
text, then compares both PDFs with the reference. It rechecks the selected
source, tool, TeX and profile bytes after both builds. Filesystem stability
and the declared installed native runtime remain assumptions; these byte
checks do not establish a complete native-loader environment.

The [controller self-test](../../../scripts/check-finite-target-copy-mgw-pdf-self-test.py)
checks input failures, existing-directory preservation, diagnostic retention,
warning recognition, early cross-toolchain refusal, conflicting modes and
eleven aggregate-dispatch mutations. Its synthetic checks and the native
two-build check have separate scopes. The aggregate requires an explicit
`PID_RS_MGW_TARGET_COPY_TEX_ROOT` in exact mode. Cross-toolchain mode refuses
with status 2; no alternate producer profile has been reviewed.

## Visual review and retained development results

All thirteen pages were inspected at 90 dpi. Pages 5, 6, 9, 10, 12 and 13 were
also inspected at 300 dpi and in 150 dpi grayscale. The figure's shaded union
and inner anchor frame remain distinguishable without color. The formal map
starts with its heading on page 12 and continues with a repeated header on
page 13. All eleven theorem identifiers occur once as complete tokens in raw
and layout text extraction and in the separate pypdf table-page extraction.

The scoped single-PDF navigation check found no action or destination error.
It used the retained public navigation inventory and office-document anchor
inventory. It does not establish external URL availability or replace the
complete publication-link gate. The PDF is not tagged for accessibility, and
text extraction does not preserve every two-dimensional mathematical layout.
The visual and record reviews were model reviews with shared tools and inputs;
they are not human or institutional review.

The first expanded development output had thirteen pages. Its unchanged
eleven-page guard rejected it. Visual review then found three layout defects:
an isolated “while” before its display, a formal-map heading separated from
the table, and identifiers split inside words. The filter now keeps the short
introduction with its display, permits complete formal-map rows to continue
across pages, and preserves inline identifiers. The second development output
corrected those defects but still failed the retained eleven-page guard.
Only after reviewing that actual output was a new thirteen-page reference
selected and checked with two fresh builds. Both earlier development failures
retain their original outcomes.

The predecessor presentation, source and controller are preserved in repository
history. Its [v1 profile](../latex/mgw-target-copy/publication-inputs-v1.json)
remains unchanged. Earlier controller failures included discarded diagnostics,
unchecked producer inputs, reused work directories, a warning matcher that
mistook a package description for a warning, omitted PDF-backend warning
headings, and relative executable paths that failed after a directory change.
The existing causal controls retain those cases. Raw execution records with
local paths remain in restricted ignored custody; this record does not claim
that they form a complete public replay package.

## Formal and statistical scope

[SOURCE_GRAPH.json](SOURCE_GRAPH.json) binds the seventeen source modules and
eleven target reports. [REPLAY_ACCEPTANCE.json](REPLAY_ACCEPTANCE.json) records
the eighteen-command ledger and remaining operational evidence gaps. The
[correction account](../../evidence/mgw-target-copy-replay-correction-2026-09-12.md)
retracts the unsupported original full-read claim and preserves its preimage.
The retained replay uses the same Lean kernel implementation as source
compilation. Written entropy consequences and worked examples are identified
as written derivations rather than additional Lean exports.

This publication revision adds no proof replay, executable-refinement theorem,
estimator calibration, sensor-selection guarantee or training result. Its exact
finite-law formulas do not transfer to another PID, to continuous or hyperbolic
inputs, or to a sampled population without the corresponding assumptions and
separate evidence.
