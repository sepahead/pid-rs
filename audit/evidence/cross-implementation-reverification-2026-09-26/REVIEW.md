# Review record: cross-implementation re-verification

**Sepehr Mahmoudian** · 26 September 2026

This record belongs to the report
[Cross-implementation re-verification of pid-rs estimators and mathematical results](../cross-implementation-reverification-2026-09-26.md).
It lists every review lens, finding and disposition. All reviews below are **model review**: advisory
output from AI-assisted sessions. None is human, institutional or independent review.

## 1. Reviewed object and reviewers

The first review round read the second draft of the report (25 September 2026, 11 PDF pages),
its evidence directory and the repository at commit `d1f401a`. Three sessions ran in parallel,
each with a separate lens set:

| Session | Lens set | Outcome |
|---|---|---|
| A | Mathematics and statistics: 22 lenses | Completed; 2 major, 7 minor findings and nits |
| B | Provenance and consistency: 17 lenses | Completed; 1 blocker, 4 major, 9 minor findings and nits |
| C | Language, accessibility and layout | Stopped by a service rate limit before it reported |

Shared dependencies: all sessions used the same model family, read the same draft and repository,
and had the same author session as their source of context. Their agreement is therefore not
independent confirmation. Where a finding changed a claim, the author session re-checked it with a
script before accepting it. The final review round in Section 4 covers the lenses of session C.

## 2. Findings and dispositions

### 2.1 Session A: mathematics and statistics

| Finding | Severity | Disposition |
|---|---|---|
| A1. The percentile indices drop unequal tails in binary64 for other valid $\alpha$ (for example $\alpha=0.29$, $B=200$) | Major | Confirmed by script: 22 of 99 two-decimal $\alpha$ values are affected. Fixed in code with two tests (report Section 7). |
| A2. The explanation of the tiny-$\delta$ binary64 trials is wrong: six trials, not one; the exact $\Lambda$ differs; the true change is not below $10^{-19}$; $q$ is not a law | Major | Confirmed by an exact diagnostic. The test was rebuilt in exact rational arithmetic; the old test and a diagnosis are archived (Section 6). |
| A3. “Attained within rounding” misattributes the excess; report per-component maxima; cite the repository proof | Minor | Confirmed for trial 1009. Section 6 now reports per-component maxima and restates the proof route. |
| A4. The decimal-$\alpha$ agreement claim is not produced by the retained script | Minor | The script now computes and prints it. |
| A5. Symbols in the support-change item are undefined | Minor | Section 8.4 now defines them and gives the witness masses. |
| A6. “A 34-limb accumulator holds every exact sum” needs a term bound | Minor | Section 8.5 now states the two magnitudes and the `usize::MAX` term bound. |
| A7. “Six Gaussian systems” is wrong for the product target | Minor | Now “systems with Gaussian inputs”. |
| A8. “Exact harmonic numbers” is inaccurate | Minor | Reworded as accurate to rounding. |
| A9. The linked review record did not exist | Minor | This file. |
| A10. Nits: whole-call failure on an ambiguous shell; the Lemma 2 corollary needs the shared distance fold and strict pruning; the $\alpha$ domain and the one-line identity proof; the singleton cumulative; “parity target”; colors with $n_a>0$; two solves per realization and $O(N^2\log N)$ time; the truncated quote | Nit | All applied. |

Session A found no error in the equations and derivations of the report's notation, continuous
checks and re-derived results (22 lenses). It confirmed the XOR value against MGW's worked
example, the antichain counts 4, 18 and 166, the Gamma argument, the Hölder and Chernoff constants,
the witness identity, the exact-summation bit positions and the FDR step-up.

### 2.2 Session B: provenance and consistency

| Finding | Severity | Disposition |
|---|---|---|
| B1. The linked review record did not exist | Blocker | This file; listed in the manifest; the link gate runs on the staged snapshot. |
| B2. The claim that four sources had no from-definition comparison is false | Major | Confirmed: an exact-rational oracle test from commit `e57b34e` covers fixed four-source tables. Summary, Section 3.3 and routes 1 and 4 corrected. |
| B3. The Levina–Bickel locator gives the wrong section, and the quote is truncated | Major | Confirmed against the retrieved PDF (same bytes as recorded). Now Section 3, below Equation (8), in the code, catalog, generated views and report; full quote. |
| B4. The binary64 boundary evidence is explained wrongly and incompletely | Major | Same as A2. |
| B5. Independence is overstated; the five-part record and edge statuses are missing | Major | Title and file names now say “cross-implementation”; Sections 1.2 and 1.3 add the independence record, edge statuses and the retrospective label. |
| B6. PDF rebuild claims have no retained record | Minor | The v6 and v9 exact runs are retained as a sanitized record in `results/`; the publication entry makes no v9 execution claim without it. |
| B7. No CHANGELOG entry | Minor | Entries added for the fix, the correction and this report. |
| B8. `run.sh` accepts relative or in-checkout work paths, shares the Cargo target, keeps only summary test lines and does not compare outputs | Minor | All fixed. |
| B9. The checkers never fail; duplicate keys and antichains pass; some wording overstates | Minor | The checkers now fail closed on malformed input and on differences above $10^{-12}$ nats; wording corrected. The retained self-test rejects 17 hostile inputs (Section 4 lists the later additions). |
| B10. Two percentile statements are not produced by the retained script | Minor | Same as A4. |
| B11. Uncited references, missing retrieval records and truncated titles | Minor | Janson and Cover–Thomas are now cited; retrieval URLs and dates added; titles and pages completed. |
| B12. The routes lack assumptions, failure conditions, evidence and reversal conditions | Minor | Section 10 now gives them for every route. |
| B13. The Rust section omits resource limits, failure behavior, memory, support and offline use; sub-timings are unretained | Minor | Section 11 extended; timings now come from the retained `timing.txt`. |
| B14. Nits: an inherited “under v6” label in the v9 profile; a long line; the test export included the generators; no retained run on `b84d1a3`; the kd-tree covers only KSG terms | Nit | All applied; the report no longer cites `b84d1a3`. |

Session B confirmed that every tabulated number matched the retained outputs, that all manifest
hashes matched, that both retrieved sources had the recorded sizes and hashes, and that the v6 and
v9 profiles differ from their predecessors only in the `METHODS.md` pin and scope text.

## 3. Changes that followed from the review

- Commit `0e96b2b`: the percentile fix with two tests, and the Levina–Bickel locator
  correction with every regenerated dependent view and hash.
- This report: renamed from “independent” to “cross-implementation”, rewritten Sections 1, 3, 6,
  7, 8.4, 9, 10 and 11, fail-closed checkers, an exact one-$\Lambda$ test, an archived binary64 test
  with an exact diagnostic, and a hardened `run.sh`.

## 4. Final review round

The second round reviewed the revised draft (15 PDF pages), the evidence directory and the staged
code change. Two sessions ran in parallel:

| Session | Lens set | Outcome |
|---|---|---|
| D | Mathematics, statistics and the code fix: 12 lenses | Completed; 1 blocker as staged, 1 major, 5 minor findings and 3 nits |
| E | Language, layout and consistency: 8 lenses | Stopped by a service rate limit before it reported |

Session D findings and dispositions:

| Finding | Severity | Disposition |
|---|---|---|
| D1. The evidence directory was stale: old results, no new one-$\Lambda$ output, an old manifest | Blocker as staged | Expected at that stage. All results were regenerated by `run.sh` on both commits, compared byte for byte, and listed in a new manifest. |
| D2. The affected-routine list was wrong: `bootstrap_pid3` is compiled out, and `bootstrap_quantized_sxpid2` was missing | Major | Confirmed in the code. The report, the changelog entry and the commit message now name the live routines and state that `bootstrap_pid3` is compiled out. The first commit was amended before it was pushed. |
| D3. Trial 2264 had the same two donor and receiver cells, not distinct ones; trial 197 needed an explanation | Minor | Confirmed by the extended diagnostic, which now prints the donor and receiver sets and the changed-cell masses. Section 6.3 corrected. |
| D4. The attainment explanation omitted the misinformative condition | Minor | Section 6.2 now states the conditions for both components and the counts 39 and 51. |
| D5. Some malformed inputs still passed the checkers | Minor | The checkers now require the case counts, every list length and 18 distinct PID3 antichains, and they type-check every input. The self-test covers these cases (17 in total). |
| D6. The report said three sessions reviewed the draft, although one stopped | Minor | Wording corrected in Sections 1.2 and 12. |
| D7. The continuous generator records the full-PID3 error instead of stopping | Minor | Section 11 corrected. |
| D8. The lower-index claim holds more generally, and the tail count can also exceed the exact floor for the binary64 $\alpha$ | Nit | The report now keeps the claim to the tested pairs, reports the 13,950 pairs with a count one above that floor, and shows that the clamp was never active. |
| D9. The test description was inaccurate, and `bootstrap_rows_stats` had no test | Nit | A third test now covers `bootstrap_rows_stats`; it fails when that call site uses the old form. The description is corrected. |
| D10. The tolerance $10^{-50}$ was too fine for 60-digit logarithms, and the screening step was only asserted | Nit | The one-$\Lambda$ test now evaluates every ratio with 80 digits, with tolerance $10^{-60}$, and has no screening step. |

Session D confirmed Lemma 2, the one-$\Lambda$ proof route, the percentile identity, the Levina–Bickel
derivation and quotation, the Hölder and Chernoff constants, the continuity witness, the
exact-summation limb count and the kd-tree pruning rule. It reproduced the dumps byte for byte and
the test counts of the staged code. Before stopping, session E noted one inconsistency: an earlier
version of finding B9 above said seven hostile inputs instead of the current count. That is
corrected. The author session performed the language and layout lenses of sessions C and E on the
final PDF; Section 5 records that pass.

## 5. Repository gates

All gates ran on 26 September 2026 on macOS 26.5.1 arm64. Hosted CI is recorded separately
after the push.

| Gate | Scope | Outcome |
|---|---|---|
| Rust formatting, Clippy with `-D warnings`, rustdoc with `-D warnings` | Commit `0e96b2b`; this commit changes no Rust source | Passed |
| `pid-core` tests: workspace, no default features, `parallel`, all features, release with all features | Commit `0e96b2b` | Passed; 728 passed, 0 failed, 6 ignored with all features |
| The 142 single-line Python checker commands of the CI workflow, normal and optimized | This commit, staged | Passed in three lanes (106, 30 and 6 commands) |
| Public API declaration snapshots | Commit `0e96b2b` | Passed; no declaration changed |
| Post-commit source state, both modes, with its hostile suite | Commit `0e96b2b` | Passed |
| Publication links, normal and optimized; Markdown math; review evidence | This commit, staged | Passed |
| New PDF checker, exact and cross-toolchain modes; two hostile corruptions | This commit | Passed; both corruptions rejected |
| Formal-PDF set inventory and self-test | This commit | Passed; 184 typed-inventory controls |
| Formal-PDF set, full cross-toolchain aggregate | This commit | Stopped at an earlier paper's workflow gate, which needs `pypdf==6.16.1` on its admitted interpreter path; left to hosted CI |
| `run.sh` on `d1f401a` and `0e96b2b`, then a confirmation run on each | This commit | Passed; every retained output matched byte for byte |

**Author language and layout pass.** Because sessions C and E stopped, the author session read the
report against the house style (short sentences, defined terms, consistent notation) and inspected
all 16 rendered PDF pages. The pass split long sentences, defined $y_T$ and $y_a$, separated the
three uses of $\alpha$ (antichain, tail mass, failure probability), let long code spans break,
replaced straight quotes, fixed a stretched bullet and a directory link, and moved one sentinel out
of a table cell. This pass is advisory model review, not independent language review.
