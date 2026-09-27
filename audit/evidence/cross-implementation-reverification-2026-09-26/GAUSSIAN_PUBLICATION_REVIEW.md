# Gaussian diagnostic publication review — 27 September 2026

Author: Sepehr Mahmoudian.

This record covers the added Section 4.5 and cost/reproduction text in the
[re-verification report](../cross-implementation-reverification-2026-09-26.md) and its
[24-page PDF](../../../output/pdf/cross-implementation-reverification.pdf).
It does not extend the original comparison manifest or replay its experiments. The
[execution projection](results/continuous-gaussian-diagnostic-2026-09-27.json) records the
separate unchanged Rust run and its original input and log identities.

## Purpose and scientific disposition

Agreement between implementations does not measure error against a population estimand. The
existing Gaussian diagnostic supplies a different check: it compares the estimated Ehrlich
shared-exclusions redundancy with an analytic-integrand mean on the same rows. Publishing all
four settings exposes the largest observed discrepancy instead of retaining only favorable cases.
It adds diagnostic evidence and explanation, not a new estimator or scientific-priority claim.
The defining source is Ehrlich et al. (2024),
[arXiv:2311.06373v3](https://arxiv.org/abs/2311.06373v3), Definition 2 and its relative-precision
convention. The categorical MGW functional and Lorentz KSG adaptation are separate objects.

Independent-first source review and a separate root derivation checked the density-ratio formula,
the Rust helper, printed data, timing scope and provenance. The review corrected these distinctions:

- Full-dimensional Gaussian densities describe the ideal generating population, not a property
  proved of a finite deterministic pseudorandom sample.
- Restarting the same seed couples the four noise settings. They are not four independent trials.
- The reference is a sample mean of the analytic integrand, not an exact population expectation.
- Its Monte Carlo standard error estimates uncertainty in that mean under the ideal IID model.
  It does not estimate uncertainty in the paired discrepancy or the PID atoms. Local kNN terms
  share fitted neighbours; treating them as independent does not supply that missing uncertainty.
- The 1.42-second observation covers four full PID2 calls, generation, reference calculations and
  validation. It is neither isolated redundancy latency nor a repeated performance benchmark.
- The selected ignored test contains no numerical accuracy assertion. Its successful exit records
  execution, not calibration. No tolerance was changed to accept the observed discrepancies.
- The historical comparison manifest and `run.sh` exclude this later diagnostic. The new public
  JSON is a labelled projection, not a complete raw or authenticated execution receipt.

The review considered no publication, code-reading alone, repeat execution, a new independent
simulation study, a population integral, existing implementation comparison, MI-only reporting,
new estimator development, a separate paper, and a scoped addition to the existing report.
The scoped addition preserves useful observations without implying evidence from unperformed
studies. Independent dataset repetitions remain the next appropriate discrepancy study; a
population integral would answer a separate reference-accuracy question. Review agreement is
not proof. Reviewers share the repository, source definitions, toolchain, filesystem and model
infrastructure; no institutional, custody or data independence is claimed.

## Render review

The root and a separate reviewer inspected all 24 pages at 96 dpi and pages 9, 10, 18, 19, 20 and
24 at 180 dpi. They found no clipped equations, missing glyphs, overlapping tables or obscured
assumptions. The high-resolution pages cover the Gaussian formulas, complete numeric table,
Rust costs, reproduction commands and reference continuation. The exact reviewed PDF SHA-256 is
`a1f99ced21036a70a5f4d55043b897cdc54bc1a8b11f7bf1c13bea54b99e235d`.
The source Markdown SHA-256 is
`a407b0af93d2a969265d36ae1d1916c81e5c1f07830d697aab0208fa3fcacee6`.

| Review lens | Observation and scope |
|---|---|
| Hierarchy | Numbered sections distinguish the new reference comparison from implementation agreement. |
| Typography | Body text, subscripts, hats and mathematical operators remain legible. |
| Grid | Equations, tables and command blocks fit the text area. |
| Spacing and rhythm | The new table and its interpretation remain adjacent. |
| Narrative order | Model, integrand, uncertainty, results and limitations appear in that order. |
| Motif provenance | The existing repository-local publication template supplies the decoration. |
| Motif coherence | Page corners use the established report motif. |
| Ornamental restraint | Decoration stays outside scientific content. |
| Palette identity | Existing lapis headings and turquoise subordinate headings are retained. |
| Pattern/data separation | No pattern encodes a number, claim status or statistical result. |
| Color-redundant labels | Text identifies every estimate and reference column. |
| Grayscale legibility | Differences are carried by labels and structure rather than hue alone. |
| Search and extraction | Real text extracts in reading order, including the complete Cargo command. |
| Print fidelity | Normal and high-resolution renders show intact mathematical glyphs. |
| A4 profile and fonts | All 24 pages are A4; the PDF is tagged, version 1.7; all 24 font objects have embedded programs. |
| Links and actions | 49 URI annotations, 28 distinct repository URIs; 50 internal outline destinations and the first-page catalog action resolve internally. No forbidden action or attachment was found in the object review. |
| Deterministic reproduction | Fixed build inputs and a source-derived trailer ID are retained. This visual record does not replace the exact rebuild gate. |
| Source/asset separation | Markdown remains canonical; the PDF is its derived presentation. |
| Portable dependencies | The existing repository-local header, filter and style files are used. |
| Rendered inspection | All pages were inspected at normal size; the six declared pages were inspected at high resolution. |

The annotation action inventory is `URI=49, GoTo=0, GoToR=0`. The separate full-object inventory
contains 51 `GoTo` actions: 50 outline bookmarks and the catalog's first-page action. These counts
refer to different sets. The publication checker retains exact annotation and repository-URI
inventories, source-derived trailer binding, font, text and render checks. Author metadata was
also inspected; the separate `check-publication-authorship.py` gate checks that credit.
This source/render record supplies no new formal-proof, estimator-calibration or application
acceptance. Repository checks and hosted outcomes must be read at the containing commit.
