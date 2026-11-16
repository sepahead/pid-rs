# Conditional-probability wording erratum, 15 November 2026

Sepehr Mahmoudian · 2026.

The correction assessment began on 15 November 2026. The publication checks and rendered-page
review were completed on 16 November 2026 UTC.

This corrects one explanatory clause in Proof 3 of the
[source-partition report](../research/source-coupling-compression/EXPOSITION.md#proof-3-deterministic-refinement)
and on page 4 of its [PDF](../../output/pdf/source-coupling-compression.pdf).
The displayed equation, proof, numbers and scientific boundaries do not change.
The report retains its October edition date; this separately dated record identifies the correction.
The [31 October republication record](source-partition-republication-2026-10-31.md)
retains its original bytes and describes its original publication only.

## Correction and retained negative evidence

The rejected clause is: “the ratio inside the logarithm is a conditional probability.”
The corrected clause is: “the logarithm of the ratio is the negative logarithm of the conditional
probability.” The rest of the paragraph is unchanged.

The fine vector and its deterministic coordinatewise coarsening in Proof 3 define a fine event
contained in a coarse event at each supported reference outcome. Both events have positive
probability. The conditional probability of the fine event given the coarse event is therefore
the fine probability divided by the coarse probability. The displayed equation uses the opposite
ratio inside a logarithm, correctly making it the negative conditional logarithm. Its average is
the stated conditional entropy. An equal-mass case can hide the wording error because both ratios
are one. No change to the equation is warranted.

This is an elementary finite-probability correction in the project-defined exposition. The
report's named PID object remains finite categorical Makkeh–Gutknecht–Wibral shared exclusions,
defined in arXiv:2002.03356v5 and expressed here in nats. This record adopts no new method,
estimator, alphabet, target, source grouping, sampling model or application. It does not adjudicate
paper correspondence, formal probability, executable or binary64 refinement, calibration,
consistency, population support or the five open three-source programmes.

The predecessor source, PDF and builder remain in the accepted history at commit
`22d971549749385bfec83a02448dc0de4a0a4fa1`. Their exact identities below preserve the rejected
wording's scope; they must not be described as the corrected artifacts. The October receipt,
wrapper, filter, figures, styles, fonts and notices were not rewritten.

| Artifact | Before: bytes; SHA-256 | Corrected: bytes; SHA-256 |
|---|---|---|
| Canonical Markdown | 51,913; `693c8847db767eccebb320b8cbfc84891006c842fb4510b789d3dce341ae8ce4` | 51,937; `7022c82cdb583d055062e677bb5f3935050c2d5befb1030212c893b9e7010d4f` |
| Generated body TeX | 58,655; `37d227de54e2aedd8e886154f944424e3f12a21a9a67cd9594df51a28b5a192c` | 58,679; `3247dc12a1c2aee6d6c4433413bc22270aca0298eade5172a3a5564778032952` |
| Report PDF | 209,172; `056dc531f5ec1cb6e73615733426b4bebf3da8e5f1412a6b93dbea569d5402f0` | 209,185; `9f10034ea1cdc3bce62f2a47fa8affca26ca993b18ab697bcda151eb49de8f49` |
| Exact builder | 55,019; `452067d27d8bc28f626905a4da57aca2196b65de28c97667c08f5da1f2fa45cf` | 55,019; `753995ee03f93b48dc2e9f3c537d5c0b6226d2de5f4aae4e403555f7da3aa138` |

The body TeX is a generated projection, not a separately edited source. The old Markdown
reproduced the old body pin exactly. The new body diff changes only the same explanatory clause.
All 465 mathematical spans of the Markdown remain exact. The builder changes only its current
Markdown, generated-body and PDF identity pins; its predicates and tool identities stay fixed.

## Routes and review accounting

The narrow correction was selected before candidate editing, from the following routes. Each
rejected route can be reconsidered if its stated condition changes.

| Route | Assumption, failure condition and disposition |
|---|---|
| No action | Assumes the known false identification cannot mislead. The nested-event definition disproves that identification; rejected. |
| Plain conditional-probability algebra and paired correction | Needs nested positive-mass events and deterministic coarsening. These are explicit in Proof 3; selected as the simplest route without PID machinery. Reopen if those definitions change. |
| Markdown correction alone | Needs withdrawal of the companion PDF. That has not occurred; rejected because the paired publication must agree. |
| Patch only the PDF | Needs an equally corrected reproducible source. Without it the projection fails; rejected. |
| Add an external probability citation | Would still leave the false clause active unless it is corrected. The elementary definition already resolves the issue; rejected as an additional step. |
| Expand the report with a new lemma and example | Requires extra exposition and pagination changes. Reconsider if the direct correction remains unclear; unnecessary here. |
| Formalize the probability argument in Lean | Needs its own frozen scientific task and qualified tool route. That separate open obligation is not needed for this wording correction; deferred. |
| Run a new solver or enumeration campaign | Would check selected instances rather than repair this elementary identification. Reconsider if event semantics become uncertain; rejected here. |
| Change the displayed equation | Would turn the correct negative-log identity into a false one. Rejected unless the mathematical object itself changes. |
| Rename or split the report | Needs path, citation and producer migration without a corrective benefit. Reconsider for substantial new content; rejected here. |
| Withdraw the report | Needs a load-bearing result or publication defect. This bounded check finds a clause error; rejected for this scope. |
| Wait for a broader review | Leaves an active known error despite a bounded repair. Rejected; human proof review remains separately open. |

An advisory mathematical reviewer (`math_stats_council`) recorded the finding before this editor
(`reciprocal_erratum`) received it. The editor then inspected the exact definitions, equation,
builder and artifacts after exposure to that finding. The editor's check is contextual, not a
blind reconstruction. Both roles are model work; no human or institutional review is claimed.
Source, mathematical transcription, model family, Python runtime, host, owner and custody remain
shared dependencies. Model agreement supplies no mathematical evidence.

The following 57 named hostile lenses were applied to this bounded correction. The central
failure cut is ratio orientation under event inclusion; the other lenses keep the existing
objects, evidence classes and nonclaims fixed. Counts name coverage, not independent reviewers:
research question; why PID; named MGW functional identity; no-PID conditional-probability
comparator; MI/CMI comparator; direct task loss; fixed-model ablation; retrained ablation;
explicit failure utility; coverage alternative; Bayesian design alternative; Fisher design
alternative; other PID functional; source grouping; target identity; finite alphabet;
probability-law normalization; supported anchor; positive coarse denominator; positive fine
numerator; deterministic coordinate map; branch-event inclusion; conditional-event intersection;
ratio orientation; reciprocal identity; natural-log sign; conditional-entropy averaging;
outside-coordinate marginalization; target-stratum repetition; zero-probability omission;
absence of a source-independence assumption; pointwise versus averaged; empirical versus
population; unchanged main upper bound; unchanged target-aware bound; unchanged Möbius
coefficients; unchanged lower bound; unchanged counterexamples; no numerical change;
no calibration credit; no formal-proof promotion; no Rust-refinement credit; source-paper
boundary; versioned local-object identity; candidate pool and selection; prior exposure; judge
reuse; semantic independence; implementation independence; data independence; custody
independence; institutional independence; negative-evidence retention; old-receipt immutability;
source/TeX/PDF correspondence; authorship and citation; private-locator exclusion.

There was one wording candidate and no best-of-several selection. Its acceptance conditions
preserved every formula and number and required the existing exact publication checks. Repeated
producer runs check one fixed artifact; they are not new scientific candidates or statistical
confirmation. No dissent about the ratio correction arose in this bounded exchange. The
strongest surviving limitation is shared semantic and host dependence, together with the absence
of a human proof review. A contradictory local definition, changed formula or failed applicable
publication gate would reopen the correction's disposition.

## Mechanical and visual evidence

The existing pinned Pandoc/LuaLaTeX route produced the corrected candidate. Two additional fresh
builds reproduced it byte for byte. The existing full PDF/controller/dispatch controls passed
under ordinary and optimized Python: 78 cases per mode, comprising 5 positive and 73 rejected
controls. The separate dispatch-only route passed 28 cases per mode, comprising 3 positive and
25 rejected controls. Cross-toolchain mode returned its required refusal, status 2, with zero
build credit. Controls and refusal are distinct from reproduction and visual evidence.

The exact semantic check found 17 A4 pages, PDF 1.7, the author and title metadata, visible author,
20 embedded Unicode-mapped font resources and 45 admitted actions. The PDF remains untagged.
The final TeX log had no admitted warning or layout diagnostic. No scientific experiment,
solver campaign or Lean replay was run for this erratum.

Poppler 26.06.0 rendered every old and corrected page in color and grayscale at 100 dpi. Only
page 4 differs in either rendered set; all other page PNGs are byte-identical. The editor
actually inspected all 17 corrected pages in both modes, the old page 4, and a predeclared
high-risk subset at 300 dpi: page 1 (title/byline), page 4 (changed proof and equation), and
page 17 (commands/citation). The changed paragraph fits within its text block and does not
alter a page break. No visual repair or design change was needed.

| Required visual lens | Disposition for this publication surface |
|---|---|
| Hierarchy | Existing title, section and proof hierarchy remains clear; page 4 places the corrected explanation directly after its equation. |
| Typography | Pinned text and mathematics remain legible, with no missing glyph seen. |
| Grid | The paragraph stays within the established margins. |
| Spacing/rhythm | The corrected paragraph adds one line within the existing page; no collision or irregular gap appears. |
| Narrative order | Definitions, nested-event argument, equation and conditional-entropy conclusion retain their order. |
| Motif provenance | Only the existing repository-local title band and corner rosettes are used. |
| Motif coherence | The unchanged decoration remains consistent across pages. |
| Ornamental restraint | Decoration stays low contrast and outside the text block. |
| Palette identity | Existing lapis title, turquoise subordinate headings and established accent rules are retained. |
| Pattern/data-semantic separation | No decorative pattern encodes a mathematical status or value. |
| Color-redundant labels | Unchanged figures keep their labels, legend order and companion tables. |
| Grayscale legibility | All 17 pages remain legible; figure series retain the same order and labels. |
| Real-text searchability and logical extraction order | Both extractors preserve the proof's sentence/equation order; only page 4 text changes. No accessibility-conformance claim follows. |
| Print fidelity | Rendered text, rules and vector figures show no clipping or raster substitution. No physical print test is claimed. |
| A4/PDF profile and embedded fonts | Exact checks retain 17 unrotated A4 PDF 1.7 pages and embedded Unicode-mapped fonts. |
| Link/action safety | The existing semantic scanner admits only the established destinations and URI/GoTo actions. |
| Deterministic reproduction | Two fresh source builds equal each other and the corrected PDF bytes. |
| Source/derived-asset separation | Markdown and repository-local producer inputs remain sources; body TeX and PDF remain derived. |
| Portable repository-local dependencies | The existing wrapper, filter, styles, fonts and notices remain exact; no new runtime dependency. This is no cross-toolchain acceptance. |
| Normal-size and high-resolution rendered inspection | All pages viewed in color/grayscale at 100 dpi; pages 1, 4 and 17 also viewed at 300 dpi. |

This record reports local leaf checks and model visual inspection only. Integration checks,
staged publication-link checks, exact-commit hosted checks and remote-main publication are
separate obligations recorded by the integration milestone. No local receipt establishes those
future events or upgrades the report's scientific status.

Suggested citation: Sepehr Mahmoudian, *Source partitions and shared-exclusions information*
(2026), with this dated erratum and the exact containing commit or release. For the software,
use [CITATION.cff](../../CITATION.cff); cite the defining MGW paper separately.
