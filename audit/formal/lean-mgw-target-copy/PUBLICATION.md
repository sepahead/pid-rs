# Publication record for the finite target-copy MGW note

This record describes the presentation artifact for
[`finite-target-copy-mgw-synergy.md`](../../evidence/finite-target-copy-mgw-synergy.md).
The document concerns only the finite categorical shared-exclusions construction of
Makkeh, Gutknecht, and Wibral. It does not transfer results to `I_min`, continuous shared
exclusions, KSG, or another PID.

## Inputs and result

The Markdown source is 21,440 bytes. Its SHA-256 is
`fefe6f39d5511d9bf364f458481558e2f794faecb45cdd3260347ecd6de4b272`. The figure source is the repository-local SVG at
[`audit/formal/latex/figures/mgw-target-copy/event-union.svg`](../latex/figures/mgw-target-copy/event-union.svg).
Its SHA-256 is `280d19e9b63659ebe9aeaba74e09d11476be729a784c612f0a69679e05d3a22c`.
The PDF is [`output/pdf/finite-target-copy-mgw-synergy.pdf`](../../../output/pdf/finite-target-copy-mgw-synergy.pdf).
The committed PDF is an 11-page A4 document with embedded fonts. Its SHA-256 is
`22fafcbdbec1294d7e1569e71528a45075de7e91be10b751138f5da093459ddc` and its size is 163,435
bytes. Recompute it with:

```text
sha256sum output/pdf/finite-target-copy-mgw-synergy.pdf
pdfinfo output/pdf/finite-target-copy-mgw-synergy.pdf
pdffonts output/pdf/finite-target-copy-mgw-synergy.pdf
```

The presentation uses the repository-local report palette and restrained vector decoration.
The SVG gives a worked $2\times2$ source-law example, labels the OR event and anchor, and shows
the cancellation of the positive full-key and target-event masses. Its title says that the
complete source joint law determines target-copy synergy; the union mass is one factor of the
formula and is not sufficient by itself.

## Reproduction boundary

The PDF was generated from the committed Markdown source with Pandoc 3.10.2, the committed
`audit/formal/latex/mgw-target-copy/filter.lua`, LuaHBTeX from TeX Live 2024, and the repository
publication style. The build used the reviewed TeX-tree font bytes,
`SOURCE_DATE_EPOCH=1789084800`, `-no-shell-escape`, and two LuaLaTeX passes. Rendered pages
were inspected at 150 dpi for all 11 pages, with pages 1, 8, 10 and 11 reviewed at high detail;
the complete set was also rendered in grayscale and at 300 dpi. Searchable text, A4 geometry,
font embedding, and the absence of unresolved placeholders were checked with Poppler tools.
The public reproduction command is:

```text
python3 -I -S -B scripts/build-finite-target-copy-mgw-pdf.py --check --tex-root <selected-tex-live-2024-root> --work-dir <new-build-directory>
```

The selected programs must be available on `PATH` and match the executable hashes and versions
in the [input profile](../latex/mgw-target-copy/publication-inputs-v1.json). The builder checks
six source files, all declared font and selected TeX-file bytes, and six executable files. It
uses the repository-local [template](../latex/mgw-target-copy/publication.tex), creates two
fresh build directories, supplies a restricted child environment, retains each command's
stdout and stderr, rejects nonzero status and unexpected stderr, and checks the final TeX
logs for named warning, missing-character, and box-overflow diagnostics. Initial first-pass
cross-reference warnings are resolved by the second pass. Both fresh PDFs must agree, and
`--check` requires exact equality with the committed PDF. Inputs are rechecked after the builds;
filesystem stability and the declared installed native runtime remain assumptions.

The controller correction reproduces the already inspected PDF bytes above. Its
[self-test](../../../scripts/check-finite-target-copy-mgw-pdf-self-test.py) checks input failures,
existing-directory preservation, diagnostic retention, TeX warning recognition, early
cross-toolchain refusal, conflicting modes, and eleven aggregate-dispatch mutations. Synthetic
controller tests do not replace the native two-build check. The aggregate requires an explicit
`PID_RS_MGW_TARGET_COPY_TEX_ROOT` in exact mode. Cross-toolchain mode refuses with status 2;
no alternate producer profile has been reviewed.

The predecessor controller at `1522faa6bc7f9522c5ed8757f6e94fa24ac953e2` discarded tool
diagnostics, did not verify the claimed producer/font profile, and reused an existing work
directory. These were controller limitations, not evidence of a false theorem. During repair,
an unrestricted search for the word `warning` incorrectly matched the `infwarerr` package's
description. The corrected diagnostic matcher retains that description as a positive control
while rejecting actual warning headings. A later source review found that bare PDF-backend
warnings and `LuaHBTeX warning` headings were missing from the matcher. Both now have rejection
controls; neither occurred in the retained exact-build logs. The review also found that relative
`PATH` entries could fail after the child changed directory. Selected executable paths now become
absolute while retaining their invocation names; a subprocess control covers that case.
The failed build and all prior controller bytes remain
preserved; no historical run is relabeled as using the corrected controller.

This is a bounded presentation record. It is not a hermetic native-loader trace, an
independent PDF renderer, a proof replay, an independent Lean kernel, a paper-priority claim,
or evidence of estimator calibration, sensor-selection value, or deployment readiness.

## Formal correspondence

The exact source graph, target roster, evidence streams, and fresh same-kernel replay record are
in this directory. [`SOURCE_GRAPH.json`](SOURCE_GRAPH.json) binds 17 source modules and 11
target reports. [`REPLAY_ACCEPTANCE.json`](REPLAY_ACCEPTANCE.json) records the 18-command replay
and its scope. The replay uses the same Lean kernel implementation as the source compilation;
it is therefore not independent-kernel verification. The written entropy consequences and
worked examples are marked as written derivations in the Markdown and are not silently counted
as additional Lean exports.
