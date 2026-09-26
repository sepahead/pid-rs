# Review record: shared-exclusion redundancy as fault tolerance

**Sepehr Mahmoudian** · 26 September 2026

This record belongs to the research note
[Shared-exclusion redundancy as fault tolerance for multisensor systems](EXPOSITION.md). It lists every
review lens, finding and disposition. All reviews are **model review**: advisory output from
AI-assisted sessions. None is human, institutional or independent review.

## 1. Reviewed object and reviewers

Two sessions reviewed the first full draft (10 PDF pages), its Lean file, scripts and outputs, in
parallel and with separate lens sets:

| Session | Lens set | Outcome |
|---|---|---|
| F | Mathematics and formal proofs: 12 lenses | Completed; 2 major, 4 minor findings and nits |
| G | Experiment, statistics and claims: 8 lenses | Completed; 4 major, 5 minor findings and 2 nits |

Shared dependencies: both sessions used the same model family and read the same draft and
repository; their agreement is not independent confirmation. The author session re-checked every
accepted finding against the sources, the data or a script before changing the note.

## 2. Session F: mathematics and formal proofs

| Finding | Severity | Disposition |
|---|---|---|
| F1. Milzman (2024) already defines the erasure analogue of tolerance (his Definition 3), proves the order correspondence that contains the tolerance half of Lemma 2 (his Theorem 1) and uses the threshold antichain; the note credited none of this | Major | Confirmed from the paper. Section 11 now credits all three and states the differences: value faults instead of erasures, the MGW measure instead of $I_{\mathrm{ft}}$, and non-monotone threshold values. The Summary points to Section 11. |
| F2. MGW's own operational interpretation (Section V.B) already describes the bottom-node case: a channel emitting a disjunction whose substatements may be false, decoded by a Bayes-optimal receiver, averaged over uses with all substatements true | Major | Confirmed from the paper. Section 11 now cites it as the closest precursor and states what the note extends. |
| F3. No bound was computed on data, and the scored forecast (smoothed, fitted on another recording) lies outside Theorem 2 | Minor | Version 3 of the experiment computes the bound on every row with training support and reports where it does not apply. Section 7.3 states that smoothing can move the forecast below the bound, with the exact example $61/102<0.6$, and that the numbers show scale, not a test. |
| F4. Section 9 dropped the premise $p(s',t)>0$ and hid that the forecast knew the fault count | Minor | Both qualifiers added. |
| F5. The second row of the check table was a solver-consistency check only | Minor | `theory_checks.py` now computes $I(S;T)$ directly and compares it with the top-node cumulative; the table row is relabelled. |
| F6. The interpretation after Theorem 1 needs closure of tolerated fault sets under subsets, not symmetry | Nit | Sentence added. |
| F7. Wording: "larger event", the duplicated-noise explanation, the parity sentence, $O(R)$ memory, the conventions of the mixture bound | Nit | All corrected. |
| F8. Lean docstring label, the unstated positivity and logarithmic forms, missing manifest and review files, one opening quote | Nit | Label fixed; the note states that Lean checks the probability inequality and that the logarithmic form follows by monotonicity; this file and the manifest now exist; quotes fixed. |

Session F confirmed Theorem 1, Corollary 1 with its end cases, Lemma 2 and the chain, Propositions 3
and 4, the monotonicity claims, Theorem 2, the exact example values, the Dedekind counts and the
faithfulness of the Lean encoding. It reran the Lean receipt and the theory checks and reproduced
their outputs byte for byte.

## 3. Session G: experiment, statistics and claims

| Finding | Severity | Disposition |
|---|---|---|
| G1. Blocks of 60 rows are too short for these series; at data-driven lengths some intervals include zero | Major | Version 3 reports blocks of 60, 360 and 720 rows. The note now states that 4 of 40 intervals include zero at 60 rows and 8 at 360 or 720 rows, and it no longer claims that every interval excludes zero. |
| G2. Every condition gave the forecast the exact fault count, and every row was faulted | Major | Version 3 adds wrong budgets ($f\ne k$) and expected losses for partial fault rates. The negative results (too small a budget; few faulted rows) are reported in Sections 7.4 and 8, and the claims are qualified. |
| G3. The HLW evidence was weak: $\mathrm{FT}_1$ ranks HLW 8th of 10, the erasure measure ties, $\mathrm{FT}_2$ does not flag it, and negative correlations were unreported | Major | Section 7.6 now uses the loss $\mathrm{MI}-\mathrm{FT}_1$, reports that the erasure measure shows the same weakness and that $\mathrm{FT}_2$ does not, calls HLW one post hoc example, and reports the negative correlations in Section 8. |
| G4. Humidity ratio is derived from temperature and humidity, so independent faults on it are not physically consistent | Major | Confirmed (conditional entropy 0.170 of 1.144 nats). The primary analysis now uses the four physical sensors; the five-channel analysis is secondary and disclosed. |
| G5. Smoothing, unseen states and the shift between recordings were not quantified | Minor | Version 3 reports unseen clean states, clamped values and occupancy rates, and adds an oblivious forecast with back-off to the prior. |
| G6. The oracle's smoothing is worth many training rows | Minor | Disclosed, with a second oracle that adds the weighted mass of one average row; both are reported. |
| G7. Theorem 2 does not apply to rows whose state and label are unseen in training | Minor | Reported (8.3% and 34.9% of rows), with the losses on both kinds of rows. |
| G8. "Not significantly worse" overread the intervals | Minor | Replaced by the differences and their intervals. |
| G9. The changes from version 1 to version 2 were not described | Minor | Section 13 now describes all three versions. |
| G10. A value was mis-rounded ($\mathrm{FT}_3$) | Nit | The five-channel profile now reads 0.260. |
| G11. "Keeps 84%" read as information kept under a fault | Nit | Section 7.2 now says the profile values are clean, in-sample values. |

Session G reproduced both experiment versions byte for byte, found no implementation bug or test
leakage, and matched all 278 checked table values against the JSON.

## 4. Author language and layout pass

The author session read the revised note against the house style and inspected every rendered PDF
page. The PDF uses the repository's shared report design; all 14 pages were inspected. The pass
replaced subscript characters that the font lacks with mathematical subscripts, set table widths
for the new tables, and replaced straight quotes. This pass is advisory model review.

## 5. Checks

All checks ran on 26 September 2026 on macOS 26.5.1 arm64. Hosted CI is recorded separately after
the push.

| Check | Outcome |
|---|---|
| `run.sh` with `--with-lean`: theory checks, pid-rs down-set cross-check, all three experiment versions, Lean compile and axiom receipt | Passed; all six outputs matched the retained copies byte for byte ([record](results/reproduction-confirmation.txt)) |
| PDF checker, exact and cross-toolchain modes; one hostile corruption | Passed; the corruption was rejected |
| Formal-PDF set inventory and self-test | Passed; 186 typed-inventory controls |
| Publication links, normal and optimized; Markdown math; review evidence | Passed |
| Lean toolchain freeze and certified-claim checks, with self-test | Passed |
| The 106 single-line Python checker commands of the CI workflow outside the Lean, Z3 and KSG-preservation lanes | Passed |

The Lean, Z3 and KSG-preservation lanes and the Rust suite were not rerun for this commit, because no
file that they bind or build changed; they passed on the previous commit.
