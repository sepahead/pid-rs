# Exact statement and source correspondence

The three exports in `PidPrefixMgwMeanCandidate` have universes `u`, `v`, `w`. Each is checked against complete [raw targets](sources/PidPrefixMgwMean/RawTargets.lean), [alias targets](sources/PidPrefixMgwMean/AliasTargets.lean), and the [contract](sources/PidPrefixMgwMean/Contract.lean). The [actual semantic judge](sources/PidPrefixMgwMean/SemanticJudge.lean) checks the public environment roster and uses the inherited DNF judge to compare complete types, universes, constant kinds and transitive axioms. A source regex or printed type string alone is insufficient.

| Export | Exact mathematical inputs and conclusion | Main proof route in the accepted candidate |
|---|---|---|
| `word_coefficient_join_power` | Finite nonempty source index set, finite categorical alphabets, arbitrary **signed** row weights `r`, anchor `z`, node `alpha`, natural `n`, and a semilattice structure satisfying `ExactOps`. The word coefficient at length `n+1` equals `joinPower (weights r z) n alpha`. No PMF or nonnegative-weight premise. | `prefix_cumulative_indicator`, finite weighted-word lower sums, `signed_power_cumulative`, and finite lower-cumulative uniqueness; private conclusion at line 298, public export at line 881. |
| `finite_block_expectation` | Under `Law p`, proves integrability of actual block and component functions, fresh-anchor expansion, and the exact finite binomial-thinning formula at every `h`, including zero. Supported-anchor conditioning is guarded by `0 < p z`; unsupported anchors contribute zero. | Finite product integral, prefix truncation/normalization, anchor split and six-proof probability formulas; private conclusion at line 424, public export at line 884. |
| `prefix_expectations_to_mgw_mean` | Under `Law p`, constructs informative/misinformative inverse families, sets them to zero off support, proves supported uniqueness and both component `HasSum`s, then proves convergence of the actual block expectations to the complete joint-law average of the signed atom. Desired inverses, series or expectation limits are not receiver premises. | `mean_hasSum_of_cumulative` finite-poset induction, logarithmic series, binomial cancellation, actual MGW inverses and finite anchor averaging; private conclusion at line 877, public export at line 887. |

The private helper names containing `proposed_` and the frozen contracts' original source-preparation comments are historical names/comments. Their bytes are preserved. Current local acceptance comes from the later proof evidence; renaming a private helper or rewriting an old preparation comment is unnecessary.

## Definitions identify the scientific object

| Mathematical object | Actual source definition | Meaning and boundary |
|---|---|---|
| Complete key and law | `PidMgwBridgeContract.Key`, `Law` | A finite complete source-and-target row; nonnegative masses sum to one. Alphabet product notation imposes no within-row independence. |
| PID carrier/order/join | `Node`, `rawLE`, `rawJoin`, `ExactOps` in [MGW contract](sources/PidMgwBridge/Contract.lean) | Nonempty antichains of nonempty source subsets, the actual Williams–Beer redundancy order, and minimal pairwise-union joins. |
| MGW event | `sourceMass`, `targetMass`, `restrictedMass` | OR of source-subset equality conjunctions, the common target event, and their intersection, all under the same joint law. |
| Generator/inverses | `weights`, `InfInverse`, `MisInverse` | Actual mismatch-generator masses and lower-cumulative informative/misinformative component inverses. Supported anchors supply strictly positive log/division domains. |
| Product experiment | `keyMeasure`, `rowLaw`, `experimentLaw` in [probability contract](sources/PidPrefixProbability/Contract.lean) | Native finite product measures for iid complete rows. Each block has a fresh anchor plus `h` subsequent rows. |
| Prefix statistic | `positiveOnPrefix`, `negativeOnPrefix`, `blockStatistic` | Positive increments divide by prefix length. A negative increment requires the current target hit and divides by the number of retained target-matching rows. |
| Finite word | `wordCoefficient` | Finite sum of row-weight products with the exact prefix predicate. Zero-based `joinPower n` contains `n+1` weight factors. |
| Population atom | Third mean target's `∑ z, p z * (plus z alpha - minus z alpha)` | Complete **joint-law** average, in nats; unsupported values are harmless zero extension. |

For a supported anchor, let `a = P(E_alpha)`, `v = P(T=t)`, and `q = P(E_alpha ∩ {T=t})`. The definitions and MGW bridge give `a>0`, `q>0`, and `q≤v≤1`. The positive lower-cumulative increment expectation at raw length `j≥1` is `(1-a)^j/j`; the negative one is `((1-q)^j-(1-v)^j)/j`. Their sums give `-log a` and `log(v/q)`. Finite-poset inversion recovers nodewise sums before finite anchor averaging gives the mean limit. Raw elapsed time is not substituted for retained target rank in the negative statistic.

## Primary correspondence and limits

The defining paper is Makkeh, Gutknecht and Wibral, [arXiv:2002.03356v5](https://arxiv.org/abs/2002.03356v5), published as [Physical Review E 103, 032149 (2021)](https://doi.org/10.1103/PhysRevE.103.032149). Equation 6 supplies the OR-of-AND event; Equations 7–8 the local shared-exclusions functional; Equations 13/19 the lower-cumulative atom relation; Equations 15a–b the informative/misinformative split; Equation 17 the complete joint-law average; Appendix A.1 the underlying order. Paper bit values convert to nats by multiplication by `log 2`. The retained primary HTML used in source review has SHA-256 `51df29de6fc67be99b4d0ff94f2a0743f0446fc4aa84f5a9fda9afd133fe79d6`; it is a retained rendering of v5, not a new paper revision.

MGW defines the functional. The prefix statistic, the bridge to its expected value and the packaging are project constructions. The result does not supply finite-horizon unbiasedness, a uniform rate, confidence coverage, a common probability-space almost-sure limit, executable refinement, or transfer to continuous Ehrlich/other PID functionals. Empty complete-row carriers admit no normalized law; zero masses and constant variables are otherwise allowed. Constant-target cancellation is almost sure under that law, not a statement about every zero-mass ambient array.

Only `Classical.choice`, `Quot.sound`, and `propext` appear in the accepted transitive axiom arrays. The [expected records](replay-support/EXPECTED_MEAN_RECORDS.json) are copied from historical acceptance. A later replay must produce them again from the actual judge and fresh root closure; the copied array itself proves nothing new.
