# Signed MGW information, prediction and acquisition: publication record

This revision explains when categorical shared-exclusions PID can inform analysis and when a
sensor or learning decision needs a different objective. It adds a worked decomposition of
existing office-recording prediction losses. It does not report a new estimator, a trained
PID policy, population calibration, or a general completed Lean theorem.

## Scientific scope and useful result

The canonical [comparison and decision note](../../PID_ALTERNATIVES_AND_INCREMENTAL_VALUE.md)
gives the full assumptions, derivations, counterexamples and follow-up procedures. The
[sensor guide, §8.4](../../PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md) gives the concise
standalone explanation with a finite example, an actual recording and a signed-value figure.
The [49-page PDF](../../output/pdf/pid-sensor-placement-and-galadriel-guide.pdf) is its projection.

For one finite law and the stated two-source grouping, signed unique added information plus
signed synergy equals conditional mutual information (CMI). Synergy alone can assign the same
value to an independent noise source and the missing target bit. The
[retained finite construction](mgw-fixed-world-added-information-2026-09-09.md) has 21 named
Lean targets. The displayed remaining atom values follow from the stated inversion algebra;
they are not additional named targets. The more general target-copy and noisy-channel arguments
remain written derivations with separately open general formal obligations.
The general target-copy argument fixes the complete source joint law. Equal separate source
marginals do not meet that condition; the canonical wording now makes this requirement explicit.

This distinction matters in sensor analysis: report the complete signed allocation and the
information increment together. It matters in learning: improving an allocation coordinate is
not a proof of improving prediction. It matters in acquisition: compare expected task benefit
with cost and stopping; for sequential decisions, condition on the complete available history
and integrate unavailable readings and targets. The canonical note treats original-law
conditional averages and PID recomputed under a conditional law as different operations.
It also addresses baseline representation collapse, arbitrary atom weights, hard-bin gradients,
lookahead for XOR-like complementarity, and passive versus action-changing observation laws.

The [fixed-predictor loss calculation](occupancy-fixed-predictor-loss-decomposition-2026-09-10.md)
uses the retained four-bin light/CO2 counts and training-only probability predictors. It expands
the classical log-loss identity into entropy plus expected conditional KL discrepancy. On the
later 9,752-row recording, adding CO2 gives CMI 0.0015580124044019372 nats, but increases the fitted
model discrepancy by 0.004876980823350269 nats. The resulting log-loss gain is
-0.0033189684189498564 nats. The input, exact rational count ratios, numerical evaluation,
three-recording table, replay command and rejected calculator source are retained with that note.
Nineteen arithmetic residual checks satisfy the selected 1e-12-nat fixture tolerance; their
maximum is 1.5269903397285844e-15. This tolerance is not a proved rounding-error bound.

The contribution here is the repository-specific derivation, interpretation and reproducible
analysis of these fixed records. CMI, proper scoring rules, entropy/KL decomposition and published
MGW/Ehrlich definitions are prior work, cited in the canonical documents. No priority claim is
made for the general obstruction. Temporal recording rows are not independent test episodes;
these exposed records are development evidence. The categorical identities do not establish
continuous Ehrlich PID, high-dimensional kNN calibration or a hyperbolic estimator theorem.

## Publication and focused verification

The PDF is 1,476,398 bytes, SHA-256
`35884332e8294e6c5fd105788f6f2bae5dde3044003452b117ae15c0e66d3f42`.
Its canonical guide SHA-256 is
`c425091592eec6ae6814ce4a765441401054f58a266dcdf3b6bebddc533ed31e`.
The existing signed-cancellation SVG/PDF pair is imported without changing its bytes or running
a new vector renderer. The manifest distinguishes that exact reuse from the original
rendering observation for three figure pairs. The builder and leaf bind the complete source/derivative roster.

The successful producer completed in 58.45 seconds after three LuaLaTeX passes, with no retained
glyph or overfull-box diagnostic. A separate complete exact leaf completed in 70.94 seconds:
the rebuilt PDF is byte-identical; both artifacts pass the full 49-page, font, strict object,
trailer-ID, action, URI and spacing-shim checks; all 49 pages render. Both object passes report
45 unique permitted HTTPS URIs and 18 structurally restricted nonpainting U+0020 shims.
The font roster has 60 rows: 22 CID Type 0C, 18 TrueType, two narrowly admitted SourceSansPro
Type 1C rows, and 18 Type 3 spacing shims. All are embedded and Unicode-mapped. The named-family
and type counts are marginal histograms; the gate does not claim raw font-program identity or
a complete family/type cross-table for inherited CID/TrueType rows.

The new import suite executes the actual pinned builder validation and Pandoc filter. Normal
and optimized Python each pass 21 focused cases: 19 asset-validator cases and two filter cases.
Separate retained runs completed in 2.91 and 2.94 seconds. The complete exact leaf also invokes
both modes. These checks cover selected identity, malformed-input and routing boundaries;
they do not prove all builder behavior, mathematical correctness or general isolation.

The leaf used the successful producer's selected font bytes and fontconfig, with a fresh TeX
cache and work root. That fontconfig still designated its earlier generated cache directory.
No pre-run inventory of that directory was selected, so this record makes no cache immutability
or independent cold-cache claim. Selected source/font inputs were unchanged. Runtime limits are
observed bounds and process timeout controls, not hard storage quotas or arbitrary descendant
containment.

The complete exact formal-PDF aggregate passed in 1,986.11 seconds. It reproduced the sensor
guide and every other declared paper under their existing acceptance relations. Its 64,106-byte
standard output has SHA-256
`983803684e865b77868ee27ae97363ab3c93748d0b9cb6f2f834e79eac2649cc`.
Standard error contains two successful 13-test synchronizer transcripts. At the post-aggregate
check, all 29 selected source files retained their registered bytes. The corrected canonical
note also passed the normal and optimized Markdown math checks.

The unchanged applicable package-metadata, release-control, certified-claim and Lean-freeze
checks passed. Both Python modes passed 126 certified-claim and 147 freeze-control mutations
per mode. Their selected inputs were matched before reusing those results. Final source-state
binding and hosted acceptance are separate obligations; resolve mainline integration from the
exact containing commit and its hosted evidence.

## Visual review and retained defects

One reviewer inspected all 49 normal-size page renders and four detail/grayscale renders of
physical pages 28 and 29. A second reviewer inspected physical pages 1–3, 26–31 and 46–49 plus
those four detail/grayscale views. Coverage is 53 and 17 images, respectively; the second pass
is a subset review. The figure/filter contributor participated in visual review, so these are
not fully independent design and evaluation teams.

No material clipping, missing mathematical symbol or ambiguous new figure/table label was
observed. Five previously missing prose/table CO2 subscripts are visible. The new derivation
introduction stays with its equation. The signed chart uses a common linear nat scale and
explicit signs; its small CMI has both a numerical value and an annotation. Grayscale retains
the argument through direction, signs and labels.

The required publication lenses have these scoped dispositions:

| Lenses | Evidence and limit |
| --- | --- |
| Hierarchy; typography; grid; spacing/rhythm; narrative order | Complete rendered pass; the new derivation, two tables and four-step procedure are readable. Three earlier flow notes remain below. |
| Motif provenance; motif coherence; ornamental restraint; palette identity | Existing repository-local design and exact figure assets retained; restrained cover patterns stay behind text. No private design runtime is imported. |
| Pattern/data-semantic separation; color-redundant labels; grayscale legibility | Decoration does not encode a result; explicit values, signs and bar geometry survive grayscale. |
| Real-text searchability and logical extraction order; print fidelity | Text extraction and rendered equations/labels inspected. No physical printer test or PDF/UA claim. |
| A4/PDF profile and embedded fonts; link/action safety; deterministic reproduction | Both complete object profiles and exact rebuilt bytes pass the leaf; this is the selected toolchain relation. |
| Source/derived-asset separation; portable repository-local dependencies | Canonical Markdown/SVGs, exact imported derivatives and source roster remain distinct. |
| Normal-size plus high-resolution rendered inspection | Full 49-page normal pass; declared high-risk pages 28/29 at 220 dpi, plus grayscale at 120 dpi. |

Three minor paragraph-to-display/table breaks remain outside §8.4: physical pages 10→11
(§2.7 bounds), 44→45 (the joint-law average), and 45→46 (the four-anchor table). Their content
is complete and readable. They are retained for a focused flow pass. The prior PDF was not
compared for these sites, so this record does not call them unchanged or newly introduced.
An earlier review mistakenly reported absent headers/footers on two intermediate renders;
exact-image reinspection withdrew that observation. No page-style change followed it.

## Rejected publication routes and next actions

The first producer attempt stopped because the selected Lua font cache was outside the allowed
TeX output boundary. Moving the cache below that boundary preserved the restrictive output
policy. The second attempt completed TeX but failed the glyph gate on five U+2082 characters.
Using explicit mathematical subscripts fixed the actual source defect. A narrow paragraph
spacing rule fixed the new introduction/display split. Both failed attempts remain rejected;
the later success does not relabel them. Local raw logs and preimages retain their exact bytes.
They are local diagnostic custody, not a claimed off-host archive.

An earlier complete-aggregate attempt stopped in the custody-receipt builder path after
528.45 seconds, with child status 43 and wrapper status 1. The inherited leaf cleanup removed
the inner diagnostics, so the precise cause remains unresolved. A separately registered
successor restored the earlier recorded environment overrides and first ran the unchanged
custody builder successfully. The full aggregate then passed as recorded above. This result
supports use of that override profile; it does not identify which earlier setting caused the
failure. Three inspected cache files have verified local preservation copies; their originals
remain intact. The failed aggregate retains its failed disposition.

Profile-only, build-only, leaf-only and cross-toolchain substitutes were rejected for publication
acceptance. The selected route retains the complete exact leaf, full exact publication set,
causal source/package gates and final source-state binding. A broad Rust rebuild has no new
causal input in this documentation-only milestone. A new estimator or policy is not inferred
from a successful publication check.

Scientific follow-up is concrete: close the general event-mass and target-copy formal targets;
retain direct CMI and task-loss baselines; test frozen models on new complete episodes; compare
calibration and regularization under identical tuning budgets; evaluate at most four fixed
sensor packages against cost, stopping and joint-subset/lookahead baselines. Any PID feature or
regularizer needs a separately specified objective and measured incremental value. Camera-pose
search and action-changing robotics require their own candidate and transition models.
No existing scientific result, negative source or branch fragment is retired by this publication
milestone. Retirement still requires verified successors and absence of an active owner.
