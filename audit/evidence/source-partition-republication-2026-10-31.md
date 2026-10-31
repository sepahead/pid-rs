# Republication of the source-partition report, 31 October 2026

Status: dated record of one publication change. It changes no theorem, estimator, evidence class
or number of the report. It records why the report was republished in this form, the review
criteria that were applied, the visual review of the new PDF and the checks that ran. All review
work here is AI-agent work in one session; no human reviewed this record or the report.

## 1. What changed

The [source-partition report](../research/source-coupling-compression/EXPOSITION.md) of
24 October 2026 had three known defects: its status statement still called it an unadmitted local
draft, it stated the identity $D=L+2R$ only for deterministic recodings, and it used names that the
project had coined (*law*, *cumulative*, *carrier*, *allocation movement* and others). A dated
[addendum](../research/source-coupling-compression/ADDENDUM-2026-10-30.md) and the
[adjudication record](math-stats-review-adjudication-2026-10-30.md) of an AI-agent review held the
corrections and new results, but a reader of the report or its PDF did not see them.

The republished report takes in the addendum's results with their proofs, uses the standard terms
of the [terminology list](../../TERMINOLOGY.md), corrects the status statement, defines its terms
and symbols before the first formula and gives replay commands that were run as written. Three
figures change their words only. The Markdown now shows the figures through their SVG companions,
which GitHub can display; the first version linked the figure PDFs, which GitHub cannot show as
images. Each SVG is the Poppler output of its figure PDF with one added ivory rectangle under the
drawing, so that the figure stays readable in GitHub's dark mode. The Pandoc filter accepts the new
byline, maps each SVG image back to its vector PDF before the LaTeX is written, and turns every
relative link into an absolute repository URL, because the PDF admits only absolute URI actions. The
builder binds the new inputs, the 17-page count and the renamed section headings.

| File | Bytes | SHA-256 |
|---|---:|---|
| `audit/research/source-coupling-compression/EXPOSITION.md` | 51,374 | `f0fdd3c50e0d46dbd078bf9807adaf505807e6174933ddb9f7faa50761617685` |
| `output/pdf/source-coupling-compression.pdf` | 208,911 | `96089c4c24647b8eb0895fd0b229135b672acd247c16662c3f9600d120763d63` |
| `audit/research/source-coupling-compression/figures/allocation-comparison.pdf` | 10,508 | `f5f14e96d13a5818f6f28ee12b70c7d33a119b75f8621fb2ef69be6aac132738` |
| `audit/research/source-coupling-compression/figures/prediction-comparison-v2.pdf` | 7,642 | `4dbbddfe957b8dfb858c5217b39e73ef5b6d18372e1c421236d9549874af9236` |
| `audit/research/source-coupling-compression/figures/office-recoding.pdf` | 13,284 | `075f6400e982d5d9f2743b5213fd87c4e1d006b0f79c7a9742a7591e7d544207` |
| `audit/research/source-coupling-compression/figures/allocation-comparison.svg` | 50,833 | `1d5ef3900729892346b31c8e47c589e06052eb58c3ae6108c0fcb4c28dac45ea` |
| `audit/research/source-coupling-compression/figures/prediction-comparison-v2.svg` | 44,143 | `46e1c77ee397f231ad8d6f12cfcbc647619f239bb6696387d50aff5ccab51a0c` |
| `audit/research/source-coupling-compression/figures/office-recoding.svg` | 73,624 | `23df3cce3037323b366122fc3b5468f5511e9c5b9168ce30078b6b3cd5d0b220` |
| `audit/formal/latex/source-coupling-compression/report-filter.lua` | 2,276 | `bdcc61e4e0537f7568e4a50d8c91b0389f01495adc817920880ed6703b83484e` |
| `audit/formal/latex/source-coupling-compression/publication.tex` | 1,888 | `f50d1e757dcbfbf1d370777060c0e39f231f47965d94de939a64b11bb1ced9d6` |
| `scripts/build-source-coupling-compression-pdf.py` | 55,019 | `b27f1c59a1b7ba50e73d4ce3d69480cacec11d25299800473c3c959a5e77f06a` |

The figure sources were compiled with the exact profile of the report build. Before any change, the
same procedure rebuilt all three committed figure PDFs byte for byte, and Poppler 26.06.0
(`pdftocairo -svg`) rebuilt their three SVG companions byte for byte. The new SVGs are that output
with the rectangle `<rect x="-1" y="-1" width="W+2" height="H+2" fill="#F7F3E9"/>` inserted after
`</defs>`, where `W` and `H` are the width and height of the viewBox. Moving the Markdown images to
the SVGs left the Pandoc output and the PDF byte for byte unchanged. The first version of every changed file stays in the Git
history of `main` at commit `7b45ca6846a40bc6fd94653a24e640de19d70ad6`.

## 2. Approaches compared

| Approach | Why it was or was not taken |
|---|---|
| No action: keep the report and the separate addendum | Rejected. The report kept a false status statement and coined terms, and a PDF reader would not find the corrections. |
| Correct only the status statement | Rejected. The restricted statement of $D=L+2R$ and the weaker lower bound would remain. |
| Link the addendum from the report | Rejected. Two documents would have to be read together, and the report would keep its coined terms. |
| Take the addendum into the report and adopt the standard terms | Selected. One document carries every current statement; the addendum stays as the dated record of the change. |
| Withdraw the report and publish a new one under a new name | Rejected. Existing citations name this title; Git already keeps the first version. |
| Split the report into a theory note and a data note | Rejected. It needs new paths and required checks and gives a reader of 17 pages no clear benefit. |
| Present the results only in a longer external document | Rejected. The repository report is the cited primary record of these results. |
| Republish the Markdown and keep the old PDF | Rejected. The Markdown and the PDF must agree. |
| Simplest route without PID: report only mutual-information changes | Rejected. The question is about attribution to sources; on office test $L=0$ while $D\approx0.58$ nats, so mutual information alone cannot see the change. |
| Rewrite the report as a native LaTeX paper | Rejected. The reviewed Pandoc route and its exact check exist; a new route needs a new reviewed check. |
| Wait for a human reviewer | Rejected for now. The changes are corrections and integrations that were checked here; human review remains an open obligation and is stated as such. |

The selected approach would need to be reconsidered if a later check found a numerical difference
between the report and its machine records, or if a human reviewer rejected a proof.

## 3. Review criteria

The criteria below were applied one after another by the same agent session that wrote the
revision. They describe what the review covered. They are not independent reviewers, and their
number is no evidence of correctness.

| Criterion | Finding and disposition |
|---|---|
| Research question stated | Stated in Section 1 with why it matters; the overstatement "whether a recoding can change the attribution" was corrected to what upper and lower bounds actually tell. |
| Why PID at all | The question concerns attribution to sources; Section 7 shows a recorded case with $L=0$ and $D>0$. |
| Why this PID functional | The report keeps to MGW categorical shared exclusions and says that no result transfers to another measure. |
| Why not mutual or conditional mutual information | The lower bounds use exactly these quantities; Section 3 states what they can and cannot establish. |
| Why not direct prediction loss | Section 7 reports log loss and Brier scores separately and states that they answer a different question. |
| Source grouping and target | Fixed by the study design in Section 6; unchanged. |
| Alphabet and binarisation | Lower-median thresholds fitted on training days; unchanged and stated. |
| Estimand: empirical versus population | Every number is for an empirical distribution; Section 7 states the plug-in bias with an exact example. |
| Units | Nats throughout; the defining paper uses bits, which Section 1 states. |
| Definitions before use | A terms table and a symbol table precede the first formula. |
| Terminology list | Every coined name of the first version was replaced; code identifiers keep their spelling. |
| Proof of the coupling bound | Five proof steps re-read; the target form (12) follows from the same refinement intervals. |
| Proof of the closed-form lower bound | Both directions re-read; the level-set construction gives nonnegative weights on lattice nodes. |
| Dual certificates | The 48 vectors satisfy $\lvert A^\top y\rvert\le1$; the checker ran and reported six improved distributions. |
| Identity $D=L+2R$ | Holds for every pair of distributions on the same lattice; the restricted first statement was corrected. |
| Invariance theorem | Statement and both directions unchanged; the relabelling reading of statement 1 was checked. |
| Counterexample | Atom values and the attaining lower bound for $B=\{3\}$ were re-derived. |
| Two-value comparison | The meaning of the incidence digits was mis-stated in a draft and corrected before publication. |
| Range bound | Uses MGW Theorem IV.3; the comparison with bound (1) now covers all 21 distributions with $D>0$. |
| Polytope refinement | Labelled exploratory because it was solved in binary64. |
| Third saved bound | Its source is an earlier unpublished note; the report says that it does not derive it and that it is uninformative. |
| Recorded-data shift | Tail masses and constant sources are tabulated; the office results are read as a code frozen on training days. |
| In-sample scores | 205 of 445 score records use training rows; stated. |
| Smoothing change in refits | Stated, with the exact arithmetic of the room validation loss. |
| Sparse cells | Stated with counts and an exact bias example. |
| Numbers against the first version | Every number of the first version is kept; table cells were compared with the first version and the addendum. |
| Numbers against machine records | The third bound's range (49.3 to 270.3 nats) and the 21 distributions with $D>0$ were recomputed from the published campaign files. |
| Replay commands | Run as written from a checkout; the study output differs from the published campaign only in the timing record, and the bound check output is byte-identical. |
| Exact arithmetic claims | Unchanged; the outward-interval rules are restated without change. |
| Formal-evidence scope | Z3 checks are described as algebra checks, not a probability theorem; no new Lean proof is claimed. |
| Evidence classes | Proofs, executions, exploratory computations and model reviews are named separately. |
| AI role | Section 8 states that the derivations and reviews are AI-agent work and that no human checked them. |
| Review independence | The review of 28 October and its adjudication are described as correlated model output. |
| Negative results | Rejected approaches and the non-concavity counterexample stay in Section 8. |
| Exposure | The data and earlier results were known before the study; stated. |
| Selection | No best of several scientific results was selected; stated. |
| Priority | No priority claim; bounded searches only. |
| Calibration and population claims | None made; stated in the status paragraph and Section 8. |
| Rust correspondence | Section 9 states that no production Rust interface exists. |
| Computational cost | Section 9 covers the new certificates and the exploratory program; no Rust timing is claimed. |
| Social-media sources | None cited. |
| Authorship and citation | The byline, PDF metadata and suggested citation name the author; the citation asks for the exact commit. |
| Status statement | Corrected: both versions are on the main branch, and being there settles no open question. |
| Links | Every relative link becomes an absolute repository URL in the PDF; a link that would leave the repository stops the build. |
| Private paths | No machine path appears; the PDF check rejects private paths in the text. |
| Markdown rendering | Only portable math delimiters are used; the Markdown math check passes. |
| Figures and words | The three figures use the same terms as the text; the prediction table follows the bar order of its figure. |
| Plain language | Short sentences and standard terms; no conformance to ASD-STE100 is claimed. |
| Junior-mathematician reader | Every step of the new proofs is written out, including the level-set construction. |
| Consistency with the addendum | The addendum stays unchanged as the dated record; the report states that it took its results. |
| Consistency with other documents | The README row, the scripts guide (page count, terms), the handoff and the changelog were updated together. |
| Reproducibility of the PDF | Two fresh builds are byte-identical to the committed PDF. |

## 4. Visual review

The new PDF was inspected page by page through the 20 criteria that the repository requires for a
changed publication surface. Every page was inspected in color at 100 dpi while the defects below
were fixed. The 17 final pages were then inspected in color and in grayscale at 80 dpi, and a
declared high-risk subset at 300 dpi: the title block (page 1), the proof of the closed-form bound
(page 7), the legend of Figure 1 (page 12) and the command block (page 17). The colors of the accent
rules of pages 1 and 3 were sampled at 300 dpi and are the same saffron. Two small text changes
followed; for each, a pixel comparison of the grayscale renders found the changed pages (page 2,
then pages 3 and 4), which were inspected again in color at 100 dpi. No 300 dpi detail lies on a
page that those changes touched. The three SVG companions that the Markdown shows were rendered at
860 px wide on the dark page color of GitHub (`#0d1117`): each figure appears on an opaque ivory
card with no dark pixel on its edges.

The review found and fixed these defects before the PDF was bound:

- The TeX build stopped on `\square`, which the wrapper does not define; the proof now ends with a
  sentence, which also renders on GitHub.
- A fenced code block produced an undefined `Shaded` environment, and its long lines would have
  overflowed; the commands now use a plain block with short lines.
- Three tables with long headers spread across the page and wrapped their first column; their
  headers were shortened or the table transposed.
- A table split after its first row; the shorter tables above it removed the split.
- Inline code broke in the middle of words; the comparison commands moved into the command block.
- A nearly empty last page and a large gap before a figure; the figure now precedes its table and
  the report ends on page 17.
- The office figure set the relation signs with wide math spacing and serif digits; its digits now
  use the figure font and its arrows ordinary spaces.
- Numbers of four or more digits mixed styles; they now use a thousands comma throughout.
- The terms and symbols tables gave their meaning column only half the width; their columns now
  have the ratio 1:3.
- Emphasis in capital letters, kept from the first version, became italics.

| Criterion | Result |
|---|---|
| Hierarchy | Title, ten numbered sections and their subsections read in order; the revision note precedes Section 1. |
| Typography | Body, headings, code and mathematics use the pinned fonts; no missing glyph. |
| Grid | Margins, table widths and figure widths follow the established design. |
| Spacing and rhythm | The fixes above removed the gaps and splits; no other irregular spacing was seen. |
| Narrative order | Question, definitions, upper bound, lower bounds, invariance, comparison, data, results, evidence, cost, reproduction. |
| Motif provenance | Only the repository's existing title band and corner rosettes; no new motif. |
| Motif coherence | Unchanged from the reviewed design. |
| Ornamental restraint | Decoration stays low in contrast and outside the text block. |
| Palette identity | Lapis title, turquoise subtitle and subheadings, bronze accent rules; figure colors are the palette colors. |
| Pattern and data separation | No pattern encodes data. |
| Color-redundant labels | Figure 1 labels every bar with its value; Figure 2 has the table of its values; series follow legend order. |
| Grayscale legibility | All text, tables and code stay legible; bar series stay distinguishable by order and value labels. |
| Real-text searchability | Text extraction finds every section heading; the PDF check confirms the headings and the author. |
| Print fidelity | A4, vector figures, no rotated pages. |
| A4 and font profile | Every page is A4; every font is embedded with a Unicode map (PDF check). |
| Link and action safety | Only URI and GoTo actions, all URIs absolute (PDF check). |
| Deterministic reproduction | Two fresh builds equal the committed bytes. |
| Source and derived assets | The Markdown, figure sources and data stay the sources; the PDF, figure PDFs and SVGs are derived and pinned. |
| Portable local dependencies | The wrapper, filter, styles and fonts are repository files; no external runtime dependency. |
| Normal and high-resolution inspection | Done as described above. |

## 5. Checks that ran

- The exact report check with two fresh builds: accepted, both byte-identical to the committed PDF
  above, with every semantic predicate of the builder.
- The report's full controls in ordinary and optimized Python, its dispatch-only controls in both
  modes, and the cross-toolchain refusal with status 2.
- The Markdown math check, and the Markdown view on GitHub at the branch commit: all three figures
  load, and every one of the 449 math expressions renders. One display formula, the recurrence (7)
  for the Möbius matrix, did not render because GitHub read `k<i` as the start of an HTML tag; the
  first version had the same defect. It now reads `k < i`; TeX ignores the spaces, and the PDF is
  byte for byte unchanged.
- The three replay commands of Section 10 of the report, followed by the two comparisons, from a
  checkout of this branch with the raw recordings supplied by `--raw-dir`.
- The repository checks named in the commit message that contains this record.

## 6. Limits

This is an AI-agent review of one session. It cannot replace a human reader of the proofs, an
independent re-implementation or a hosted render. A visual inspection by a model can miss defects
that a person would see. The record adds no formal, statistical, calibration or priority result to
the report.
