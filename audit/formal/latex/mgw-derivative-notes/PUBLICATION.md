# Derivative-note publication source and reproduction contract

The canonical scientific sources are the [finite-prefix derivative paper](../../../research/finite-prefix-mgw-gradient/EXPOSITION.md)
and the [handwritten support-change MI cusp](../../../research/support-change-mi-cusp/EXPOSITION.md).
The gradient paper has eleven locally accepted formal theorem families; the cusp's formal proof
remains open. The [theorem map](../../lean-prefix-mgw-gradient/THEOREM_MAP.md) defines that boundary.
This document describes artifact production, which adds no mathematical acceptance.

The [version-2 input profile](publication-inputs-v2.json) binds eleven source files and the
13-page [gradient PDF](../../../../output/pdf/finite-prefix-mgw-gradient.pdf) and 5-page
[cusp PDF](../../../../output/pdf/support-change-mi-cusp.pdf). It changes the two manuscript inputs
and two generated TeX references for the Markdown math-syntax repair; the schema remains version 1.
Four complete exact checks, covering both notes in normal and optimized Python, reproduced the
selected TeX, PDFs, observations and gradient figure. All eight PDF builds matched the previously
reviewed artifact bytes. The [current record](MARKDOWN_MATH_CORRECTION.json) separates this local
v2 reproduction from the full aggregate, final source-state and hosted/mainline evidence.

The [version-1 profile](publication-inputs-v1.json) and its dated
[observation record](PUBLICATION_OBSERVATION.json) remain unchanged historical evidence, including
the visual review of the identical PDF artifacts. The [rendering correction](MARKDOWN_MATH_CORRECTION.md)
retains the failed predecessor and explains the source and TeX changes. No estimator, benchmark
or application result follows from the adapter.

## Sources and diagram

The [two-kind adapter](../../../../scripts/build-mgw-derivative-notes-pdf.py) uses the unchanged
[reviewed runtime](../../lean-prefix-mgw-mean/replay-support/runtime.py), the existing
[native tool profile](../prefix-mgw-bias/native-tools-v2.json) and
[pypdf 6.16.1 source inventory](../prefix-mgw-bias/reader-source-v2.json).
The reader is copied from a declared existing source directory into a fresh private package before
import. The profiles remain their existing objects and do not claim prior production of these notes.

The local template reuses the current [workflow publication style](../pid-rs-workflow-publication.sty)
and [report table style](../pid-rs-report-tables.sty). Its metadata and running heads identify the
research note and its finite-categorical or handwritten-negative status. No external private design source,
shared-style edit or duplicated tool/parser inventory is needed.

The gradient source includes one [canonical explanatory SVG](../../../research/finite-prefix-mgw-gradient/figures/prefix-score-experiment.svg).
It shows the random anchor, the actual signed arrival-rank statistic, the score of every complete
row, and the separate comparison of the prefix mean derivative with the full-atom derivative.
Its adjacent prose states the extra gap assumptions, latent-score interpretation and nats per
scalar-parameter unit. The cusp's exact table and limits remain sufficient without a second plot.

The SVG uses explicit text spans and local palette values. The source is supplied directly to the
already pinned rsvg-convert PDF route. Unlike the older simple-text bias figures, it needs no
Unicode-subscript rewriting stage. The PDF filter maps exactly that SVG to its vector derivative.
There are no external images or numerical curve data.

The preferred gradient preimage remains separately preserved in source custody. The figure
reference/caption and the linked support-moment citation clarification are explicit successor
edits. No new mathematical assumption or bound is introduced by the illustration.

## Finite input and output contracts

The adapter accepts exactly gradient or cusp. The input manifest must have the exact eleven-path
roster from its source. The filter permits only the enumerated canonical repository links,
three cited primary HTTPS destinations and the one gradient image. It checks the source title,
kind metadata and image count. Current Markdown uses GitHub dollar delimiters. The unchanged
Pandoc reader enables both `tex_math_dollars` and `tex_math_single_backslash`; accepting a source
in Pandoc does not establish its GitHub rendering. Each exact run compares fresh native output
with the selected TeX and PDF references.

The native profile binds the selected primary executables, interpreter, fixed process observer,
five explicit font inputs and LuaLaTeX format. It does not bind all dynamic libraries, all fonts
the TeX distribution might use or the complete TeX installation. Actual output font checks and
review remain required.

Every direct source/PDF/text descriptor read is no-follow and nonblocking, checks regular-file
identity before and after opening, and reads at most its cap plus one byte. The default cap is
32 MiB. Only named native binary captures use their already reviewed exact larger byte size,
bounded above by 512 MiB. A small Snapshot subclass retains the reviewed runtime's storage and
verification operations while using these bounded reads. This is not an atomic filesystem
snapshot or a defense against an arbitrarily hostile operating system.

Discovery makes two fresh candidate builds and requires their exact bytes and observations to
agree. Its result is explicitly no-adoption. The owner must inspect the actual raw TeX, vector
PDF, full PDFs, extracted text, links, headings, fonts and all changed pages before accepting any
reference. A discovery result cannot fill its own expected fields or publish an artifact.

For a later reviewed reference, the output record binds actual TeX and PDF byte entries and the
complete observed finite PDF structure. Gradient additionally binds the actual vector-PDF bytes.
Retain the expected TeX at gradient.expected.tex or cusp.expected.tex and the gradient vector PDF
at figures/prefix-score-experiment.pdf. Exact mode reads these actual reference files and the
corresponding canonical output/pdf artifact before producing two new builds. It compares raw
bytes and the complete recorded observation. It never overwrites public references.

The observation includes the actual A4 page geometry, language, heading destinations, URI and
internal-action inventories, named destinations, extracted text hashes and font rows. The reader
rejects diagnostics, encryption, unsupported action/file keys and unlisted URI actions. Discovery
checks do not substitute for review of visible heading locations, extraction order or legibility.
There is no PDF/UA, generic viewer-safety or accessibility certification.

## Original execution registration

Production requires isolated Python with -I -S -B, optionally -O, an actual externally reviewed
registration and its raw hash, the actual manifest hash, a new private work directory, and the
caller's original same-host monotonic stage endpoint. That endpoint must be copied unchanged into
every invocation belonging to the same registered stage and passed explicitly on the command line.
An entry-time UTC-to-monotonic conversion is only an additional per-call minimum.

The execution registration fields are:

~~~text
schema: pid-rs/mgw-derivative-note-execution-v1
status: reviewed-source-ready-for-discovery OR reviewed-source-ready-for-exact
kind, mode, root, work_dir, optimization
registered_utc, deadline_utc, stage_started_utc, stage_deadline_utc
stage_monotonic_deadline
maximum_builds, maximum_commands
manifest_sha256, builder_sha256, python_sha256
tool_selectors, reader_directory
~~~

The fixed tool-selector roster is pandoc, lualatex, rsvg-convert, kpsewhich, fc-cache, bash,
pdfinfo, pdffonts and pdftotext. Paths and timestamps belong in fresh private registrations.
The source profile supplies their expected identities, not machine-specific path guesses.
The monotonic value is a finite JSON number preserving the caller's exact floating-point value.
It is meaningful only in the same host's monotonic clock domain. Never copy it into another
machine's run or renew it for a later child.

Each invocation has two builds. Its fixed command count is 40 for gradient or 36 for cusp.
Each build has two LuaLaTeX passes. The command list, in order, is:

| Operation per build | Gradient | Cusp |
|---|---:|---:|
| Pandoc and LuaLaTeX version probes | 2 | 2 |
| rsvg-convert version probe | 1 | 0 |
| Format lookup before production | 1 | 1 |
| Five exact font lookups | 5 | 5 |
| Private font-cache build | 1 | 1 |
| One SVG-to-vector-PDF conversion | 1 | 0 |
| Pandoc TeX production | 1 | 1 |
| LuaLaTeX passes | 2 | 2 |
| Strict final log check | 1 | 1 |
| PDF info, fonts, layout text and bounding-box text | 4 | 4 |
| Format lookup after production | 1 | 1 |
| Total | 20 | 18 |

The producer registration may span at most 45 minutes and its enclosing stage at most 90 minutes,
following the reused native profile. The actual owner may choose shorter bounds. The source
preparation window is separate and never becomes a production authorization.

For each native command, the child timeout is the minimum of 300 seconds, the remaining original
UTC invocation time and the remaining caller-bound monotonic time. Streams are capped at 4 MiB
each. The unchanged runtime samples process-group RSS with a 4 GiB threshold and records cleanup.
These are observed cooperative limits, not a hard OS memory guarantee or complete descendant
custody.

The owned work-root allowance is 768 MiB. A 16 MiB reserve is held before terminal result writing,
and the final RESULT is included in the after-write observed byte check. This allowance covers
the captured source/tool blobs and both builds. It is not a whole-stage or filesystem quota.
The outer supervisor must separately register and check a complete-stage allowance covering all
invocation roots, control outputs, outer stdout/stderr, registration records, retained failures and
its own final custody records. No stage-wide disk success follows from a child work-root check.

The owner must also retain outer start/end/exit and elapsed observations. Late completion,
nonzero return, missing result, resource failure or partial finalization is failure even if a
partial inner record once contained a success label. A late result write preserves its first bytes
before failed replacement. Every failed attempt remains in custody; no automatic retry is allowed.

## Controls and publication boundary

The [finite inert controls](../../../../scripts/check-mgw-derivative-notes-pdf-self-test.py)
have an exact [95-case roster](controls/roster-v1.json). They cover source/kind/refusal boundaries,
byte and path checks, selectors, finite link mapping and literal Lua wiring, original registration
and monotonic bindings, bounded direct inputs, and cross-toolchain refusal before admission.
The controls include the actual observer with a finite reader substitute and strict text-domain conversion. Their small file and FIFO fixtures are confined to the fresh registered control output directory.
They run no native producer, SVG/XML/PDF parser, pypdf import, Lua engine or proof.

Control registration additionally binds its own source, builder source, input manifest, roster,
active Python, fresh output, integer optimization, exact 95-case budget, original UTC bounds and
the original control-stage monotonic endpoint. The maximum control window is 20 minutes.
Run normal and optimized controls only after independent source review and actual admission.
A literal filter check does not prove Pandoc executes that filter correctly.

Every new publication surface requires the existing twenty-lens visual review and actual normal-size
inspection of all changed pages plus a declared high-risk subset at high resolution. Root inspected
all current pages, dense mathematics, the diagram's small labels and the final references. Actual
grayscale renders supplement the color review. An earlier candidate retained a stale figure label
and a two-line final page; its corrected successor preserves every mathematical step and citation.
The [historical artifact and visual-review record](PUBLICATION_OBSERVATION.json) binds those
identical PDFs; the [current v2 record](MARKDOWN_MATH_CORRECTION.json) binds their new reproduction.

Unsupported cross-toolchain calls return status 2 before registration reads, work creation, parser
loading or native launch. This is explicit refusal, not hosted reproduction. The aggregate
[gate](../../../../scripts/check-formal-pdf-set.sh) includes both papers. Its sixteen
`PID_RS_DERIVATIVE_*` inputs carry the selected Python, manifest hash, two control registrations,
two producer registrations, their hashes and output paths, and the original control/production
monotonic endpoints. It runs normal/optimized controls and both exact producers before the older
long-running checks. The [dispatch controls](../../../../scripts/check-mgw-derivative-pdf-dispatch-self-test.py)
check missing fields, argument order, failure propagation and unsupported-mode nonexecution.

The PDF observation comparison checks shape, exact JSON type and value recursively. It rejects
boolean/integer and integer/float substitutions at every nesting level, missing or extra fields,
list changes and nonfinite numbers. Nineteen added controls exercise the exact reference predicate,
including both current observation records and a changed PDF byte. These controls run no PDF
parser. The [correction record](OBSERVATION_EQUALITY_CORRECTION.md) retains the original predicate,
minimal coercion witnesses and the unchanged mathematical scope.

Raw production and failed-predecessor records remain in local custody. The public observation is a
portable projection, not a substitute for those raw records or permanent archival custody. Exact
source-to-reference reproduction, exact-commit hosted evidence and main integration have separate
recorded outcomes. They do not establish scientific priority, numerical calibration or task value.
