# Mathematical paper source corrections — 20 September 2026

These corrections make five existing arguments state their intended domains and notation. They
change the explanatory Markdown, TeX and PDFs. They do not add an estimator or change a formal
theorem statement. The [results guide](../../MATHEMATICAL_RESULTS_GUIDE.md) remains the reading map;
the linked papers give the complete definitions, derivations, examples and evidence limits.

## Why these corrections were needed

| Paper | Correction and reason |
|---|---|
| [Dependency concentration](../../DEPENDENCY_COLORED_SXPID_CONCENTRATION.md) | The displayed chain has five objects and four arrows. Its first two arrows are bookkeeping; the third is the probability bound; the fourth is continuity. The final implication also requires a justified positive population-cell floor and a strict common-support margin. |
| [Support-change continuity](../../SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md) | Separate the singleton alphabet before formulas containing the logarithm of an alphabet-dependent factor. Both singleton laws coincide, so their atom differences are zero for every supplied admissible radius. The displayed general envelopes require at least two alphabet elements. |
| [Exact log-product assurance](../formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md) | Define event counts as the sum of observed multiplicities. Distinguish the target value from its count when writing the target event. This prevents readers from replacing row counts by the number of distinct keys or interpreting a frequency as a target label. |
| [Finite-alphabet convergence](../../FINITE_ALPHABET_PLUGIN_CONVERGENCE.md) | Attach support containment to the introductory implication chain, as already required by FA-1. Convergence of masses alone does not imply eventual equality of supports. |
| [Ecosystem compatibility](../../ECOSYSTEM_COMPATIBILITY_AUDIT.md) | State joint absolute continuity of the complete design matrix, its independence from the target vector and the dimension condition for the full-row-rank example. Continuous entry marginals alone are insufficient. Independent standard Gaussian entries supply one model satisfying the stated joint assumption. |

The first four papers concern finite categorical shared-exclusions PID or its exact finite-table
assurance. The rank example concerns supervised reuse of evaluation rows; it is not a theorem
about a continuous PID estimator. None of these corrections transfers a categorical result to
Ehrlich's continuous functional, supplies a population cell floor from observed counts, or proves
an application benefit.

## Presentation review and retained limits

The five corrected papers were built privately from the reviewed sources. Normal and optimized
document-semantic checks passed. The final LaTeX logs passed the existing warning, box and
reference checks. Rendered comparison identified every page changed from the previous PDFs.
Actual visual review covered those pages and a stated high-resolution subset.

The first exact-count rendering exposed two isolated paragraph lines across page breaks. The
successor changes only TeX widow and club penalties. It preserves the wording, equations, fonts
and page geometry. Its separate reference page contains both complete entries. The earlier
rendering and review remain retained as development evidence; no mathematical failure is inferred
from a page-break defect.

The changed explanations do not extend the scope of the existing Lean results. In particular,
exact-log's seven checked log/product/sign statements do not prove the concrete event-count
extraction, sampling validity or general Rust refinement. The unchanged exact PDF wrapper still
requires its fresh pinned Lean replay and receipt comparison. The full publication gate remains
required before commit. This source and visual review does not itself assert a completed wrapper,
hosted run, accessibility audit or physical print test.

The preceding source and PDF versions remain in commit
`f34a1694419513fa2522f27e5996716316d44db9`. Current dependency bindings change only in the active
maps; historical formal receipts and their bindings remain intact. The corresponding PDF links
are listed below so that the explanatory and printable versions can be read together.

- [Dependency concentration PDF](../../output/pdf/dependency-colored-sxpid-concentration.pdf)
- [Support-change continuity PDF](../../output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf)
- [Exact log-product PDF](../../output/pdf/exact-log-product-sxpid2-assurance.pdf)
- [Finite-alphabet convergence PDF](../../output/pdf/finite-alphabet-plugin-convergence.pdf)
- [Ecosystem compatibility PDF](../../output/pdf/ecosystem-compatibility-audit.pdf)
