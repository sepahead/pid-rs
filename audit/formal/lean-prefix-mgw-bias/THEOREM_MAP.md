# Exact theorem and proof-source map

Five universal finite-categorical bias families were accepted locally on 8 September 2026. The selected candidate has 720 lines and 34,113 bytes, SHA-256 `c945862f2bb64825ad5b754cd6fcd4f32da02c0377f13074d9192b6568e3fb45`. Its five public declarations are direct aliases of private proof terms. Its 36 private lemmas are implementation steps of those proofs, not 36 separately accepted scientific families.

The preserved [contract](formal/accepted_Contract.lean), [raw quantified views](formal/accepted_RawTargets.lean), [alias views](formal/accepted_AliasTargets.lean) and [selected candidate](formal/accepted_Candidate.lean) are inspection copies of the accepted exact sources. Their filenames do not constitute a runnable replay layout. The preserved Contract header describes its earlier type-preparation stage as an unexecuted proposal with unproved targets; that historical comment predates the separately accepted candidate and remains unchanged to preserve the exact accepted source identity. The complete accepted closure and its operational records remain separate evidence; public/hosted replay must bind that closure explicitly.

## The five exports

| Public export | Full target and input scope | Exposition result | Selected source |
| --- | --- | --- | --- |
| `actual_finite_bias` | Finite complete-key normalized nonnegative law; nonempty finite source index; valid node; constructs supported unique informative/misinformative inverse families; all supported anchors and all natural horizons | Actual component tails, native block mean, signed/max/query/surprisal/inverse bounds, equations (18)--(22) | `proof_actual_bias`, line 525; public alias, line 705 |
| `fiber_inverse_moment` | Any finite carrier and finite projection codomain; normalized nonnegative weights; no injectivity or surjectivity assumption | Population fiber reciprocal identity, equation (23) | `proof_fiber_inverse`, line 355; public alias, line 708 |
| `support_moment_bounds` | Same categorical law and valid node; includes every member collection's source and joint projections | Moment lower/upper bounds and target-support equality, equation (24) | `proof_support_moments`, line 464; public alias, line 711 |
| `projected_support_bias` | Categorical law; any supplied supported inverse pair; any member collection; every horizon | Signed and absolute projected-support bounds, equation (25) | `proof_projected_bias`, line 665; public alias, line 714 |
| `mass_floor_bias` | Categorical law; any supplied supported inverse pair; known $0<\eta\le1$ with $q_z\ge\eta$ on positive population support; every horizon | Remainder and geometric population-floor bounds, equation (27) | `proof_floor_bias`, line 687; public alias, line 717 |

The fiber theorem has two universe parameters. The other four have three, including the dependent source-alphabet universe. These are the exact quantified source targets; no finite fixture or example replaces them.

## All proof steps

| Private declaration(s), start line | Mathematical role | Used by |
| --- | --- | --- |
| `shifted_hasSum`, 12 | Removing a finite prefix from an actual summable real series gives its shifted tail and exact remainder | Scalar and atom tails |
| `log_hasSum`, 21; `remainder_hasSum`, 29 | Logarithm series on $0<q\le1$ and its shifted form | Remainder identities |
| `geometric_tail_hasSum`, 34 | Exact geometric tail $(1-q)^{h+1}/q$ | Scalar bounds |
| `remainder_basic`, 42 | Nonnegative remainder, logarithmic envelope, geometric envelope and inverse envelope | Actual and floor bias |
| `remainder_difference`, 75 | Nonnegative power differences, termwise denominator bound, full geometric difference minus a nonnegative finite prefix | Signed negative envelope and monotonicity |
| `dominated_tail`, 120 | Comparing shifted sums of nonnegative dominated component terms | Actual coordinate tails |
| `mean_choose_div`, 130; `mean_binomial_cancel`, 139; `mean_binomial_thinning`, 164 | Retained-rank choose identity and exact raw-time binomial sum | Negative increment envelope |
| `power_cumulative`, 190; `join_envelope`, 200 | Join-power cumulative identity and nonnegative coordinate domination | Positive/conditional word envelopes |
| `cumulative_model`, 215; `word_envelope`, 226 | Actual redundancy-order conversion and accepted word/join correspondence | Native coefficient envelope |
| `anchor_domains`, 238 | Native event inclusions and anchor lower mass | Supported denominator domains |
| `raw_envelopes`, 260 | Conditional Law after $v>0$, nonnegative binomial factors and positive/negative raw-time bounds | Actual component tails |
| `average_eq_sum`, 293; `average_mono`, 304; `average_const`, 315 | Zero-weight handling, supported monotonicity and exact mass-one constants | Native mean and moments |
| `average_sub`, 321; `average_div`, 330 | Exact supported averaging algebra | Signed and inverse envelopes |
| `fiber_nonneg`, 339; `fiber_anchor_le`, 345; `proof_fiber_inverse`, 355 | Nonnegative fiber masses, supported denominators and finite regrouping; zero fibers contribute zero | Partition identity and support moments |
| `inverse_antitone`, 383; `inverse_lower`, 390; `inverse_self`, 397 | Positive reciprocal monotonicity, lower bound one, and full-key support identity | Moment comparisons |
| `target_fiber`, 408; `source_fiber`, 421; `joint_fiber`, 442 | Exact native event/projection fiber correspondence, including dependent source alphabets | Target count and collection bounds |
| `proof_support_moments`, 464 | Each member-collection fiber is contained in its corresponding query event | Support export and projected bias |
| `actual_block_average`, 508 | Accepted native finite-product expectation rewritten in the new partial-mean definitions | End-to-end actual bias |
| `proof_actual_bias`, 525 | Accepted component integral HasSum values, tail domination, signed subtraction, finite averaging and moment bounds | Main export and corollaries |
| `pair_unique`, 648 | Uniqueness on supported anchors and equality of zero families off support | Arbitrary supplied-pair transfer |
| `proof_projected_bias`, 665; `proof_floor_bias`, 687 | Moment or population-floor substitution after exact pair identification | Final two exports |

The three binomial lemma bodies are explicit source reuse from the accepted mean candidate, whose SHA-256 is `17fc2d8fce5ad0ba28cc8348e9348911c393e6eb00515c8139fbd27b85331b6a`. They are recompiled as private proof text in the new candidate. Source reuse does not count as an independent proof route. The separately defined `finite_horizon_increment_bounds_target` is bypassed by shifted infinite tails; it is not a sixth accepted public theorem.

## Formal dependencies and exact trust boundary

The sole candidate import is `PidPrefixMgwBias.Contract`. The complete full run freshly compiles 27 source/object pairs before the candidate: 24 accepted dependency modules and three bias type modules. Those include the finite event model, actual MGW order and inverses, six prefix probability records and three mean records. The inherited eleven MGW, six prefix and three mean records are dependency evidence; they are not newly proved bias families.

The selected source and its exact cosmetic variant each passed normal and optimized Python full runs, each with a fresh complete kernel pass. The final-target negative control rejected a replacement of the last theorem while preserving the first four exact records. Four positive runs and this negative control support one five-family acceptance; they add zero extra theorem families. Development compilation alone had supplied no such acceptance.

The permitted proof axioms are exactly `Classical.choice`, `Quot.sound` and `propext`. The semantic judge checks theorem kind, actual export roster, raw and alias types under universe renaming and transitive axiom use. The fresh kernel checks proof terms under the declared pinned Lean/Mathlib closure. It does not establish arbitrary hostile-host safety, tool authenticity, paper correspondence or a Rust/binary64 refinement.

The pinned baseline is Lean 4.33.0 and Mathlib commit `db584cd6d46c92f209a44c0f1c829460d327499d`. Principal Mathlib dependencies include:

- `Real.hasSum_pow_div_log_of_abs_lt_one`, in [Log/Deriv.lean](https://github.com/leanprover-community/mathlib4/blob/db584cd6d46c92f209a44c0f1c829460d327499d/Mathlib/Analysis/SpecialFunctions/Log/Deriv.lean).
- `hasSum_geometric_of_lt_one`, in [SpecificLimits/Basic.lean](https://github.com/leanprover-community/mathlib4/blob/db584cd6d46c92f209a44c0f1c829460d327499d/Mathlib/Analysis/SpecificLimits/Basic.lean).
- Summable-series shifts, finite-prefix identities and order comparisons from the [infinite-sum library](https://github.com/leanprover-community/mathlib4/tree/db584cd6d46c92f209a44c0f1c829460d327499d/Mathlib/Topology/Algebra/InfiniteSum).
- `Nat.add_one_mul_choose_eq`, in [Nat/Choose/Basic.lean](https://github.com/leanprover-community/mathlib4/blob/db584cd6d46c92f209a44c0f1c829460d327499d/Mathlib/Data/Nat/Choose/Basic.lean), and the finite binomial theorem.

## What each evidence layer says

| Layer | Status and boundary |
| --- | --- |
| Exact formal five-target claim | Accepted locally under the specified frozen source/kernel matrix |
| Independent mathematical source review | No source blocker found; same-model advisory review with recorded exposure and shared dependencies |
| MGW paper-to-formal correspondence | Inherited exact-v5 scope; no new independent paper-verification result from this publication |
| Four explanatory examples | Hand derivations from definitions; no extra formal specialization export, numerical experiment or benchmark |
| Markdown/SVG/TeX and PDF reproduction | [Current local evidence](../latex/prefix-mgw-bias/CURRENT_REPRODUCTION.md): eight exact builds; no additional theorem or fresh raster-review claim |
| Hosted replay and public/mainline adoption | Separate root-owned obligations; local acceptance does not imply them |
| Rust/Python implementation and finite precision | Not established by these five theorems |
| Variance, coverage, stopping and dependent rows | Not established by these five theorems |
| Sensor decision utility or cross-PID transfer | Not established by these five theorems |

The accepted contract SHA-256 is `89d61c3fe0d1e63280329ec8877d94e9e292e32cddf63b95d674a71bcf713c45`; raw targets are `4f18d3b54e59562c6c5a3e114c5897be38088abc21565cae46d806250d554a2a`; aliases are `af0718c6c88e08998d3d53755b053a27698ec3b5186d74fb763ceb840c854570`. The local acceptance record digest is `e46380b7a2b38cf4969c1996a5256ae7e6bacc4397458bdec9dec41dcadba698`, and the independent final review digest is `9acd44a4f2fe054691478b6011dc794d02e22f9bfee020d9a6d2d31b072d86de`. Digests bind bytes; the corresponding retained records provide retrieval and do not by themselves prove authenticity.

The development route and four unsuccessful compiler candidates remain in the separate archive. They document elaboration and linter failures, not mathematical countermodels. The later pass does not relabel those failures. Invalid reasoning routes, including subtracting unrelated bounds and inferring coordinate positivity from cumulative positivity, remain rejected with explicit counterexamples in the review archive.
