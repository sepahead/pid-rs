# Publication record for the finite target-copy MGW note

This record describes the presentation artifact for
[`finite-target-copy-mgw-synergy.md`](../../evidence/finite-target-copy-mgw-synergy.md).
The document concerns only the finite categorical shared-exclusions construction of
Makkeh, Gutknecht, and Wibral. It does not transfer results to `I_min`, continuous shared
exclusions, KSG, or another PID.

## Inputs and result

The Markdown source is 21,198 bytes. The figure source is the repository-local SVG at
[`audit/formal/latex/figures/mgw-target-copy/event-union.svg`](../latex/figures/mgw-target-copy/event-union.svg).
The PDF is [`output/pdf/finite-target-copy-mgw-synergy.pdf`](../../../output/pdf/finite-target-copy-mgw-synergy.pdf).
The committed PDF is an 11-page A4 document with embedded Latin Modern and Source Sans Pro
fonts. Its SHA-256 is recorded by the release commit and can be recomputed with:

```text
sha256sum output/pdf/finite-target-copy-mgw-synergy.pdf
pdfinfo output/pdf/finite-target-copy-mgw-synergy.pdf
pdffonts output/pdf/finite-target-copy-mgw-synergy.pdf
```

The presentation uses the repository-local report palette and restrained vector decoration.
The SVG gives a worked $2\times2$ source-law example, labels the OR event and anchor, and shows
the cancellation of the positive full-key and target-event masses. The figure title says that
the complete source joint law determines the target-copy synergy; the union mass is one factor
of the formula and is not sufficient by itself.

## Reproduction boundary

The PDF was generated from the Markdown source with Pandoc, a repository-specific Lua filter,
LuaLaTeX, and the repository publication style. The build used pinned TeX-tree font bytes,
`SOURCE_DATE_EPOCH=1789084800`, `-no-shell-escape`, and two LuaLaTeX passes. Rendered pages
were inspected at normal size, including the title page, proof tables, worked examples, and
the SVG page. Searchable text, A4 geometry, font embedding, and the absence of unresolved
placeholders were checked with Poppler tools.

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
