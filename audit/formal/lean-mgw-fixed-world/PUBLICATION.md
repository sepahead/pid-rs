# Same MGW synergy, different added information

The [standalone paper](../../evidence/mgw-fixed-world-added-information-2026-09-09.md)
and its [PDF](../../../output/pdf/mgw-fixed-world-added-information.pdf) compare two
candidate sources under one fixed probability law. Let A, B and U be mutually
independent fair bits. Hold target Y=(A,B) and baseline source A fixed. Adding U or
B gives the same signed categorical MGW synergy, log(4/3), but conditional mutual
information 0 or log 2. All values are in nats. These are assigned finite
probabilities; the calculation assumes no sampled IID data.

This is a check on the meaning of a proposed sensor-selection or training score:
equal synergy need not mean equal added Shannon information. The complete signed
decomposition preserves the difference. CMI answers the added-information question
directly; predictive benefit requires a separate task, predictor and evaluation.
The paper states the event counts, probability maps, signed atoms and CMI calculation.
Its recorded office example supplies motivation, not evidence that the finite
model describes those measurements or that this score improves a deployed system.

The defining construction is categorical shared exclusions from Makkeh, Gutknecht
and Wibral, [arXiv:2002.03356v5](https://arxiv.org/abs/2002.03356v5).
MGW already publishes signed cancellation in Section VI.C and Table III. The
repository supplies the matched comparison, its derivation, scoped formalization
and teaching figures. Scientific priority for that comparison is unestablished.
The result does not transfer to a different PID or to continuous, mixed-support
or hyperbolic observations without a separate argument.

## Formal scope

The [21-target report](../../evidence/mgw-fixed-world-added-information-2026-09-09/target-report.json),
[contract](PidMgwFixedWorld/Contract.lean), [target roster](PidMgwFixedWorld/RawTargets.lean),
[proof](PidMgwFixedWorld/Candidate.lean), [judge](PidMgwFixedWorld/Judge.lean) and
[nine-module dependency graph](SOURCE_GRAPH.json) retain the existing finite result.
The other signed-atom tables follow the written finite sums and subtractions;
they are not additional named targets.

The [evidence guide](EVIDENCE.md), [later execution record](LATER_EXECUTION.json)
and [replay description](REPLAY.md) distinguish original attempts, successor
controls and the later research replay. That replay rebuilt nine project modules
and checked them in a fresh process using the same Lean kernel. It supplies no
independent proof-checker implementation or portable public replay product.
A reusable public replay controller and fresh hosted formal qualification remain
open. This citation repair adds no formal target or proof replay.

## Citation correction and preserved sources

The paper's MGW locator and Figure 1 now use Section VI.C. The mathematical text,
values, formal graph and theorem roster are unchanged. In the figure SVG, the
complete change is one byte: `3` becomes `C` in `§VI.3 / Table III`.
The selected [figure PDF](../latex/figures/mgw-fixed-world/mgw-matched-comparison.pdf)
is 63,453 bytes, SHA-256
`7aea252a79c2b4a904c1afc84c8ca4b678402f2a68654892b04da250dac3ec1c`.
Two actual corrected vector builds agree. An original-SVG control also reproduces
the original vector PDF exactly. The two PDFs' extracted text differs only at
the locator; their geometry and five embedded font rows match. Normal, detailed
and grayscale views preserve the signs, labels and layout.

The immutable [117-entry source map](../../evidence/mgw-fixed-world-added-information-2026-09-09/source-map.json)
continues to describe the archived bytes. The current builder resolves three
original map keys through explicit preserved copies:

| Original key | Preserved copy |
|---|---|
| Paper Markdown | [Citation preimage](../../evidence/mgw-fixed-world-added-information-2026-09-09.citation-preimage-v1.md.txt) |
| Figure 1 SVG | [SVG preimage](../latex/figures/mgw-fixed-world/mgw-matched-comparison.citation-preimage-v1.svg.txt) |
| Figure 1 PDF | [PDF preimage](../latex/figures/mgw-fixed-world/mgw-matched-comparison.citation-preimage-v1.pdf.bin) |

The other 114 keys retain direct lookups. Exact whole-source substitutions bind
the old and current Markdown/SVG citations. Separate artifact pins bind the old
and current figure PDFs; no bytewise PDF substitution is asserted. The builder's
finite-source record reports these distinctions and does not execute Lean.

The first citation-corrected paper build completed and produced two equal PDFs,
but its first figure still used the old section label. That output was not
selected as the new reference. The subsequent figure correction and original
control retain this negative finding without rewriting its execution outcome.
This was a citation defect, not a mathematical counterexample or a proof failure.

## Reproduction

The corrected containing paper has nine A4 pages and is 231,798 bytes, SHA-256
`b43e0d8902d9c919c6ab13a13c3a7c9d55ea07d3d02af1944edd0600d1801185`.
Two actual discovery builds produced these bytes. Both reproduced the unchanged
29,078-byte Pandoc body. The historical
[v4 input profile](../latex/mgw-fixed-world/publication-inputs-v4.json) bound this
observed reference; its SHA-256 is
`eadd3f7a30d51abe95351668f1ca95ad317578e8697d43888f1d76db3a49fd6d`.
The v1–v3 profiles preserve their historical observations and reference states.

The current [v5 input profile](../latex/mgw-fixed-world/publication-inputs-v5.json)
changes only the captured `METHODS.md` identity for the permutation-null metadata correction.
The selected PDF, TeX and figure references and every other input pin are unchanged. This
profile selection supplies no new build, native-input recheck or visual-review evidence. The
artifact and execution observations retained below remain scoped to v4 and its predecessors;
they do not establish a v5 execution. Any successor execution requires its own separately
retained exact-reference checks.

All nine pages were reviewed at normal size. Pages 1 and 9 were also reviewed
at high resolution and in grayscale. The paper has 20 embedded font subsets
with Unicode mappings. The single-PDF navigation check found 32 actions and
42 destinations with no error against its declared repository inputs; it does
not establish external URL availability or the full repository link gate.
Compared with the earlier nonselected paper, layout text changes only the
locator. Raw text also adds one space after the slash on that same figure line.

A separately admitted exact run on 13 September 2026 then reproduced the selected
reference in two fresh builds. The actual supervised command returned zero; its
terminal result was observed before both original 900-second deadlines. Complete
readback joined all 402 retained build records, 17 commands and 34 output streams.
Both paper PDFs and canonical bodies matched, and the selected source and public
file observations were unchanged. Independent readback confirmed these joins.
The exact run reused the earlier visual review through identical PDF bytes; it
added no proof or new page rendering.

The supervised builder took 14.21 seconds. Its peak sampled process-group memory
was 753,958,912 bytes, within the declared 4 GiB bound. The largest inner-command
sample was 778,682,368 bytes. All 20 disk samples stayed within the 2 GiB limit;
the largest was 350,776 KiB. Memory and disk samples are observations, not hard
operating-system caps. Repeated file observations are not an atomic snapshot.
The unchanged producer overwrites first-pass recorder and log files; only the
retained final files and separately captured command streams are claimed.

Use the [builder and documented commands](../../../scripts/README.md) with an
explicit canonical TeX root and a fresh work directory. Discovery retains a
candidate and diagnostics without admitting it. Exact mode rejects a pending
reference and then requires the admitted paper bytes from two fresh builds:

```text
python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --check --tex-root <canonical-tex-root> --work-dir <new-build-directory>
```

The exact collection requires `PID_RS_MGW_FIXED_WORLD_TEX_ROOT`. Cross-toolchain
mode refuses with status 2 because no equivalence relation has been admitted.
The existing normal/optimized controls check declared input, archive, recorder
and command failures; synthetic producers do not establish valid PDF generation.
Source and artifact checks do not establish complete native-loader capture.
Full-paper layout, fonts and navigation require their own actual observations.
The [font notices](../../../THIRD_PARTY_NOTICES.md#finite-mgw-publication-fonts)
identify the recorded embedded subsets and retained license texts.
