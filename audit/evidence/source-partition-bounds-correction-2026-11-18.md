# Corrections to the source-partition study, 18 November 2026

Sepehr Mahmoudian · 2026

Can a reader use the published decimal bounds as interval endpoints, and what do the finite tables establish about rare cells and constant sources? A decimal endpoint on the wrong side of an exact value can invalidate a downstream bound. Confusing a finite table with a repeated sample can turn an exact calculation into an unsupported population claim. This record identifies four corrections in Sections 3, 5 and 7 of *Source partitions and shared-exclusions information*. The October edition date identifies the underlying study. [Corrected report](../research/source-coupling-compression/EXPOSITION.md) · [PDF](../../output/pdf/source-coupling-compression.pdf) · [October addendum](../research/source-coupling-compression/ADDENDUM-2026-10-30.md) · [15 November erratum](source-partition-conditional-probability-erratum-2026-11-15.md).

## Terms and scope

An **empirical distribution** assigns each observed outcome its relative frequency. A **signed atom** is one part of the averaged categorical shared-exclusions decomposition. Here the defining source is Makkeh, Gutknecht and Wibral, revision 5. Across two representations of the same rows, **D** is the sum of the absolute changes of these signed atoms. **X** is the kept categorical source, **Y** the pair of other categorical sources and **T** the target. **I** denotes Shannon mutual information. All information values use natural logarithms and are in nats. **Bias** is the expected estimate under a repeated-sampling law minus its population value. A **dual witness** is a vector that certifies a lower bound through the constraints of the linear program. An **outward decimal endpoint** stays below or at an exact lower value, or above or at an exact upper value. [Method source, arXiv:2002.03356v5](https://arxiv.org/abs/2002.03356v5) · [Report definitions and proofs](../research/source-coupling-compression/EXPOSITION.md).

The report specifies a project-defined finite-source comparison. Three sources, a common target and the recorded joint rows define each of its 30 empirical distributions. The study fitted quantizers and recodings using its designated training rows. Each evaluation distribution uses its own recorded counts. The decimal producer consumes their saved rational enclosures. Each interval encloses a quantity evaluated on its named empirical law. The program's chain witnesses, the exploratory optimization and a sampling bias have distinct meanings. [October study and limits](../research/source-coupling-compression/EXPOSITION.md) · [Three-source claim decision](../../claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v3.md).

## Four corrections

1. **Decimal bounds, Section 3 and PDF page 8.** The predecessor producer converted rational endpoints to binary64 and printed the nearest twelve-place decimal. On the 30 published distributions, 12 chain lower strings exceeded their exact dual values and 13 saved-cut lower strings exceeded their exact cut values. In 14 cases the allocation upper string fell below even the saved *lower* endpoint of the allocation. For the room test, the old upper string was `0.341754144236`. The saved lower endpoint was `844902811256620499416079011/2472253301111916662274129920`, strictly above that decimal. The corrected upper string is `0.341754144237`. An upward-rounded chain lower value can still lie below the actual allocation, so the 12 mismatches identify loss of the witness guarantee at serialization. [Certificate producer](../research/source-coupling-compression/verification/chain_lower_certificate.py) · [Published study record](../research/source-coupling-compression/evidence/campaign/REPORT.json).
2. **Constant pair, Section 5 and PDF page 9.** With one possible value of the source pair, its coordinates always match the supported reference row. A node event is certain if some branch omits the retained source. Otherwise its event is the matching event of the retained source. The averaged redundancy is therefore zero or the mutual information of the retained source and target. The complete-lattice inversion gives a single *possible* nonzero signed atom, at the retained singleton. Its value is $I(X;T)$, which vanishes when the retained source and target are independent. Such a recoding has $D=0$. The previous text incorrectly required a nonzero atom. [Derivation in Section 5](../research/source-coupling-compression/EXPOSITION.md#5-an-exact-comparison-when-the-recoded-pair-takes-two-values).
3. **Numerical extrema, Section 7 and PDF pages 12–13.** The 30 computed minima agreed with the chain bound at the reported precision. HiGHS solved a linear program for the minima and a mixed-integer linear program for the maxima in binary64. An exact equality or an exact certificate of the computed maxima would require separate evidence. The exact dual witnesses in Section 3 have their own rational checks. [Numerical study](../research/source-coupling-compression/EXPOSITION.md#7-results-and-limitations) · [Retained exploratory source](../research/source-coupling-compression/verification/component-sandwich-exploratory.py.txt).
4. **Sparse cells, Section 7 and PDF page 15.** The sparse counts determine the empirical atoms. A repeated-sampling law is needed to assign population bias to a named atom. None was measured for these recordings. For the report's separate Shannon example, draw two independent copies of a pair of independent fair bits. Empirical mutual information equals $\ln 2$ exactly when both bits switch between the two draws, an event of probability one quarter. In every other case at least one empirical bit is constant. The mean is $(\ln 2)/4$ and the population mutual information is zero. A constant target gives zero signed atoms for every sample, including sparse samples. [Study rows and sampling limits](../research/source-coupling-compression/EXPOSITION.md#7-results-and-limitations).

## Rust implementation and computational cost

The published default Rust API `stable::categorical::discrete_sxpid_n` computes finite categorical atoms for two to four sources. The study's partition bounds and exploratory linear programs have no production Rust interface. The finite reference covers three binary sources, up to four target values, at most 32,768 rows and at most 32 occupied joint outcomes. The decimal correction affects the separate offline Python certificate printer. It checks 48 witnesses against 18 nodes once. Each of the 30 records then needs 48 rational sums of at most three nonzero terms to evaluate the witnesses, plus comparisons and the three decimal conversions. One conversion multiplies the rational numerator by a fixed power of ten and divides by the denominator with an integer remainder. A lower endpoint uses the integer quotient. An upper endpoint increases that quotient by one exactly when the remainder is positive. The error is strictly less than one unit in the twelfth decimal place. Integer memory and arithmetic cost depend on operand bit length. Output remains three strings and an improvement flag per record alongside its identification fields. Six improvements are determined before decimal projection. A failed digest, malformed interval roster or violated bound terminates the existing verifier. This correction adds no fitting, resampling or timing estimate. [Certificate producer](../research/source-coupling-compression/verification/chain_lower_certificate.py) · [Runtime scope and costs](../research/source-coupling-compression/EXPOSITION.md#9-rust-implementation-and-computational-cost).

The source method, the project's signed-atom comparison, the executable rational script, the decimal strings and the use of any recorded result each have their own assumptions. The report's proof-to-Rust, paper-to-formal-object, population calibration and application questions stay open. The dated October addendum and its republication receipt retain their original readings, including the superseded sparse-cell and numerical language. Cite this correction when using them. [October republication](source-partition-republication-2026-10-31.md) · [Earlier erratum](source-partition-conditional-probability-erratum-2026-11-15.md).

## Reproducing the decimal check

The separately held check used a fresh extraction of the predecessor commit with only the corrected printer substituted. In each of normal and optimized Python, an independently written integer-coefficient loop checked the three output fields for all 30 published laws against their exact rational endpoints. All 90 fields per mode rounded outward by less than one unit in the twelfth decimal place. The six exact improvement flags persisted. Against the predecessor in both modes the same predicate rejected the 12 chain lower, 13 saved-cut lower and 14 allocation upper values listed above. The verifier and producer share the same published study, so this evidence concerns arithmetic and serialization on that study. One registered repair implementation was submitted against this fixed predicate.

A smaller, reusable check below exercises the decimal helper independently of the recorded inputs. From the repository root, run it under both the normal and optimized interpreter. Decimal-grid equality, zero, both signs, a carry across an integer and the room-test example are among the cases. The broader 30-law check above also inspected the three fields at the public JSON boundary.

~~~sh
for mode in normal optimized; do
  if [ "$mode" = optimized ]; then set -- -O; else set --; fi
  python3 "$@" -I -S -B - <<'PY'
from fractions import Fraction
from runpy import run_path

module = run_path("audit/research/source-coupling-compression/verification/chain_lower_certificate.py")
project = module["decimal_endpoint"]
quantum = Fraction(1, 10**12)
for value in (Fraction(0), quantum, -quantum, Fraction(1, 3), Fraction(-2, 3),
              1 - quantum / 3, Fraction(844902811256620499416079011, 2472253301111916662274129920)):
    lower = Fraction(project(value, upper=False))
    upper = Fraction(project(value, upper=True))
    if not (0 <= value - lower < quantum and 0 <= upper - value < quantum):
        raise SystemExit(f"decimal projection failed for {value}")
PY
  [ "$?" -eq 0 ] || exit 1
done
~~~

## Options and review scope

| Route | Assumption, disposition and evidence needed to reopen |
|---|---|
| Keep the published wording and output | The recorded room-test rational contradicts its decimal upper endpoint. The constant target contradicts the required nonzero atom. A different meaning for the output would need a new consumer contract. |
| Use ordinary Shannon mutual information | Selected for the retained atom and two-draw sampling example. It answers those questions directly. An atom of a different decomposition would need its own derivation. |
| Directed integer division | Selected for the fixed twelve-place interface. The quotient and remainder decide the direction even for negative rationals. A changed precision or decimal interface would require a new check. |
| Publish rational strings | Would retain exact endpoints for fraction-aware clients. The existing interface uses fixed decimal strings. Reconsider if a separately versioned rational field is requested. |
| Increase nearest-decimal precision | Every fixed grid still has interior points whose nearest projection crosses the required side. A one-sided rounding rule is required. |
| Estimate atom bias from the 30 existing tables | Would require a repeated-sampling model for the recordings. The tables establish the descriptive quantities. A declared population and sampling mechanism would reopen this analysis. |
| Bootstrap the recorded rows | Would require a defensible sampling unit and dependence model, including overlapping roles or days. Reopen with a separate statistical design. |
| Run an independent sampling study | Could estimate bias for specified atoms and a named population. It needs reserved observations or a validated generative law. |
| Use task loss or fixed-model and retrained ablation | Answers the predictive effects of recoding for a particular learner and row role. Deployment utility needs a separate outcome and study. |
| Require exact LP or mixed-integer certificates | Appropriate for an exact optimality claim. The retained exploratory output supplies binary64 agreement. Exact primal and dual or exhaustive evidence would reopen the claim. |
| Add a formal probability theorem | Would need a fixed statement, approved toolchain, checked proof and correspondence to the report. The present change repairs the output contract and qualifies the written evidence. |
| Withdraw the finite study or overwrite its history | The checked rational witness and the recorded empirical quantities still answer the finite question. The superseded words and outputs remain available for audit. A new counterexample to the underlying finite proof would reopen its decision. |

The finite mathematical reviewer wrote the first model critique before seeing the other council members' conclusions. The same reviewer then edited the report and inspected its renderings. A second model role held the previously fixed decimal checks. Both roles had common sources, model context, host and repository custody. No human scientific disposition was available. The following 60 challenges record the coverage of the corrective review. They carry no additional proof or sample size.

| Scope | Ten named challenges applied |
|---|---|
| Mathematical identity | Defining paper, source revision, natural-log units, complete lattice, disjunction across branches, conjunction within a branch, distinct coordinates, retained source, common target, singleton reconstruction. |
| Domain | Supported reference row, impossible rows, constant target, constant pair, independent retained source and target, zero contrast, nonnegative components, coupling marginals, common target alphabet, empirical normalization. |
| Sampling | Population definition, random estimator, repeated-sampling mechanism, within-pair bit independence, independence across draws, sparse counts, training-row selection, dependence across recording days, fixed-model ablation, retrained ablation. |
| Alternatives | No action, Shannon calculation, direct task loss, explicit failure utility, coverage design, Bayesian design, Fisher design, Williams–Beer comparator, alternate grouping, alternative PID functional. |
| Numerics | Lower direction, upper direction, exactly representable decimals, signed zero, one-unit bound, carry between decimal units, exact improvement flag, JSON schema, linear versus mixed-integer minimization or maximization, primal and dual feasibility. |
| Evidence | Solver tolerance, displayed versus rational certificate, population bias measurement, source and PDF identity, clean-source reproduction, semantic independence, host and custody independence, human review, formal proof scope, retained negative evidence. |

## Publication checks

The predecessor at `1479fc5e0ca15e5ef9c5521f8bc7aa36f2a98d20` is recoverable in repository history. The six-place table in the report and the October addendum shows approximations in nats. For interval calculations use the outward JSON endpoints or their exact inputs. The October addendum's SHA-256 remains `a1caa608ede201dd670a0cfb1ee862cddf1a20f97aacb8d15f8b0a94a3c6693b`. The source and generated identities below distinguish it from the current report.

| Artifact | Previous SHA-256 | Corrected SHA-256 |
|---|---|---|
| Certificate printer | `8aa1b34c4e680422d25cef33740386c61f054f34549fcc010bcfa1a6bfa90056` | `ef00393160a598b8cdf54e1618d67ab25b2fff2ebc4bbca8a0c95b180069f926` |
| Report Markdown | `7022c82cdb583d055062e677bb5f3935050c2d5befb1030212c893b9e7010d4f` | `39d62f62b49d936eb897791992e60d0680f6ce43c8e375066f5ce5bb1b373902` |
| Generated body TeX | `3247dc12a1c2aee6d6c4433413bc22270aca0298eade5172a3a5564778032952` | `144fc0c35ec0ba6da5a9aa6cea3efc9079a8c32eed99fa097aee8b45d03ef668` |
| PDF | `9f10034ea1cdc3bce62f2a47fa8affca26ca993b18ab697bcda151eb49de8f49` | `d325c30d30da0f150029b37e11068ef2cca665126c097008e9f235558260ff3f` |
| Exact PDF builder | `753995ee03f93b48dc2e9f3c537d5c0b6226d2de5f4aae4e403555f7da3aa138` | `3da6eaf267b387f1813dfddac9a709c01d3b5a5a27aac83c4f4024469d24d80a` |

The existing native PDF builder produced the same 209,419 bytes in two clean builds under normal Python and in two more under optimized Python. In each mode the full hostile control suite accepted five positive cases and rejected 73 controls. Dispatch alone accepted three positive cases and rejected 25 controls. The cross-toolchain route returned its required status 2. The three input or output identity pins changed in the builder. Its existing acceptance predicates, wrapper, figures, font resources and control program were retained. [Producer](../../scripts/build-source-coupling-compression-pdf.py) · [Publication controls](../../scripts/check-source-coupling-compression-pdf-self-test.py).

Poppler 26.06.0 rendered all 17 predecessor and corrected pages in color and grayscale at 100 dpi. Only pages 1, 8, 9, 12, 13 and 15 differ in either raster set. The editor inspected color and grayscale sheets covering all pages, then each changed page at full normal size in both modes and original-resolution details from pages 1, 8, 9, 12, 13, 15 and 17 at 300 dpi. A rejected first layout moved the last glossary row to the next page. Shortening the revision notice restored the earlier page break. The final notice fits on one line.

| Visual review lens | Finding |
|---|---|
| Hierarchy | The revision notice sits between the edition history and the research question. |
| Typography | The revised body, formulas and table headings show legible glyphs. |
| Grid | The revised paragraphs stay within the established text column. |
| Spacing and rhythm | The shorter edition notice allows the glossary and symbol table to finish on page 2. |
| Narrative order | Definitions precede the proof, computation and recorded-data interpretation. |
| Motif provenance | The established local title band and corner rosettes provide the decoration. |
| Motif coherence | The cover and inner sheets retain the same visual family. |
| Ornamental restraint | The light corner patterns leave the body text clear. |
| Palette identity | Primary lapis titles, turquoise subordinate headings and bronze rules retain their roles. |
| Pattern and data semantics | Figure values use labeled marks and tables. Decorative lines carry no quantitative meaning. |
| Color-redundant labels | Figures keep labeled series, consistent bar order and accompanying numerical values. |
| Grayscale legibility | The bars can be located by series order and the adjacent tables give exact displayed values. |
| Real text and extraction order | The notice, certificate direction, constant-pair qualification, LP language and sampling explanation are searchable in reading order. |
| Print fidelity | Vector text, equations and rules remain clear in rendered details. A physical print proof is open. |
| A4 profile and embedded fonts | The checker found 17 unrotated A4 pages, PDF 1.7 and 20 embedded Unicode-mapped font resources. The PDF is untagged. |
| Link and action safety | The semantic check admitted 46 actions, including the added correction link. |
| Deterministic reproduction | Four native builds yielded the same bytes under the two Python modes. |
| Source and derived assets | The Markdown is canonical, and the builder derives body TeX and PDF. |
| Portable repository-local dependencies | The existing wrapper, local resource pins and fonts produced the result on the admitted native profile. |
| Normal-size and high-resolution inspection | Six changed pages received individual full-size color and grayscale review, and seven pages supplied high-resolution details. |

Cite Sepehr Mahmoudian, *Source partitions and shared-exclusions information* (2026), with this 18 November correction and the exact containing repository commit or release. Cite the defining MGW paper separately and use the software citation for pid-rs. [CITATION.cff](../../CITATION.cff) · [Makkeh, Gutknecht and Wibral](https://arxiv.org/abs/2002.03356v5).
