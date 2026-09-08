# Workflow PDF text-profile repair — 8 September 2026

The workflow PDF checker now admits four exact diagram extraction orders observed from the
current publication: two on page 10 and two on page 12. It still requires exact default text,
the same page contents, and ordered prose outside those two diagrams. The complete checker
self-test passed 416 controls. A separate full-projection test passed 44 cases in each of normal
and optimized Python. Full publication and hosted checks are recorded separately below.

This repairs publication verification. It changes no PID definition, mathematical statement,
estimator, figure, PDF, scientific threshold, or accepted mathematical result.

## Failure and cause

[CI at e726576](https://github.com/sepahead/pid-rs/actions/runs/34084133975) completed with
46 of 47 jobs successful. Its PDF job rejected the page 10 label-adjacency condition. Reading
order in a layout extraction can interleave cells whose text sits on different baselines.
Adjacency in the extracted token list did not describe the intended diagram cell relation.

Three local diagnostic builds also failed before producing a complete accepted artifact. Their
retained records distinguish the source/tool-path environment from the bind-mounted filesystem,
which rejected font-cache exchange or link-metadata operations. A fourth build used native Linux
scratch storage. It completed at 04:06:59 UTC and failed the old page 10 text guard. That failure
remains a failure: archival success and a zero supervisor exit did not make the checker pass.

The fourth build produced two byte-identical PDFs with SHA-256
`273257154992a7dcdad2a801d06e6f94fc103b2ce3a5a0f0f9a52ee650a0b9c2`.
All 87 page comparisons passed the existing color and grayscale raster limits. Default text
extraction matched the committed PDF exactly. Layout extraction showed one additional page 12
order: the words “premise or input” precede “deterministic exact output Checker”. The SVG places
these words in the intended separate cells. Review of pages 10 and 12 found no visible clipping
or misplaced cells. This focused inspection does not replace the
[existing complete visual receipt](mathematical-workflow-visual-receipt-2026-09-05.md).

## Bounded repair

The checker validates each diagram's whole token sequence against its finite profile list,
even when the two input lists are equal. Page 10 spans the unique `ROUTE DEPENDENCE` marker to
`Figure 3:`; page 12 spans `CHANGE CONTROL` to `Figure 4:`. Captions and surrounding prose keep
their full token order. The checker retains strict UTF-8, permitted ASCII layout whitespace,
87 nonempty page partitions, exact default extraction bytes, and per-page token multiplicities.

The admitted profile hashes below cover the UTF-8 JSON token array, with Unicode preserved,
compact separators, and no trailing newline. They identify these arrays only; they do not
identify or authenticate an entire document producer.

| Page | Tokens | Profile SHA-256 |
|---|---:|---|
| 10 | 77 | `8d3c2ff3b2aa2779d9a902b51187631c18adc86e340725c8e649fa1292b32bd5` |
| 10 | 77 | `5ab5cb84f68d16df51d381dd91524b0b2493f7f809ab93fec33f00a1da86d03a` |
| 12 | 98 | `1a562811c965a8113552eeab2fe0cff61e4839e0e59ad71cded1d7c3536208ce` |
| 12 | 98 | `3f5269ede48a8604ed52b8e6e92c46c84648032c0432e31896515cdc29f52f10` |

Independent-first source critique found a second defect in the proposed test harness: ordinary
Python equality treats floating-point keys `10.0` and `12.0` as equal to the reviewed integers.
The successor requires the parsed key's exact type to be `int`. Two causal controls exercise
these substitutions. The initial proposal and critique remain preserved; neither received
execution credit from the successor's results.

The selected route keeps finite profiles and strict exterior order. Review retained exact PDF
bytes as the same-toolchain gate and exact default extraction as a mandatory cross-toolchain
guard. It rejected equality shortcuts, arbitrary token sorting and label deletion. A generic
cell parser, coordinate parser, SVG redesign, or single-producer policy would require a separate
contract. A new extraction order must receive new evidence and review before admission.

## Observed checks

| Check | Exact observation |
|---|---|
| Full retained projections, normal Python | 44 cases: 10 accepted and 34 expected rejections; completed 05:11:02 UTC |
| Full retained projections, optimized Python | Same 44 cases and outcomes; completed 05:11:06 UTC |
| Complete shell self-test | 416 controls passed; completed 05:16:18 UTC; empty stderr; all 29 input source files unchanged |
| Full production Linux PDF check | Failed at 05:42:44 UTC: the final source inventory rejected `scripts/__pycache__` because its directory mode was not `0555`; no timeout; source and executable hashes unchanged |
| Full formal PDF set, exact mode | Passed at 05:52:42 UTC, including every declared paper, the root blueprint, publication links and their controls |
| Current operational and certified-document bindings | All eight normal/optimized checks and self-tests passed at 05:23:27 UTC |
| Final source-state and post-commit identity | Recorded at the milestone commit; these checks grant no mathematical or hosted credit |
| Hosted checks and main integration | Pending at the new commit; earlier results do not cover this repair |

The 416 controls comprise 345 retained controls and 71 text-portability controls. The latter
contain 59 comparator cases and 12 source checks. Compact fixtures use independently embedded
measured diagram sequences with synthetic surrounding prose. The separate 88 full-projection
executions use retained complete extractions and explicit mutations; they are not additional
cases in the shell suite. Neither count is a theorem count.

The production Linux failure is separate from diagram extraction. The final inventory correctly
refused a cache directory that was absent from the declared source snapshot. The read-only
inventory guard remains in place. A separate repair must prevent that runtime write and pass
the complete production check. Its failure is not waived by the exact-mode result.

The current results-guide checker also retains an explicit refusal for its pending Linux v3
profile. Historical v2 evidence does not admit that newer edition. This milestone does not
claim that the complete hosted cross-toolchain suite passes.

The exact wrapper is `20e891182a611fdeac59afd8a1fde9f0f4ba8bfa22c045f9c276a61dea0deffa`;
the self-test is `8b2abde57783899cfb65091e5a5b103d41466aa9a66115130a63818e6fd14d62`.
Root review rehashed every control input and stream, the 306-file independent review packet,
and the 28-file correction packet. The reviewer shared the repository, retained evidence and
model-assisted workflow. Separate review roles do not establish human or institutional
independence. Private machine locations remain in ignored recovery records.

The code and repeatable controls are in the [wrapper](../../scripts/check-mathematical-workflow-pdf.sh),
[self-test](../../scripts/check-mathematical-workflow-pdf-self-test.sh), and
[scripts guide](../../scripts/README.md). Earlier public checker bytes remain in Git history.
Historical Lean replay and closed C8/C12 records retain their original bindings and outcomes.
