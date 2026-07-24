# Lean theorem map

## Scope

This map records every definition and theorem added by
[`SupportChangeContinuity.lean`](../../../audit/formal/lean/PidFiniteConvergence/SupportChangeContinuity.lean)
,
[`SxEventBridge.lean`](../../../audit/formal/lean/PidFiniteConvergence/SxEventBridge.lean),
and
[`FractionalCover.lean`](../../../audit/formal/lean/PidFiniteConvergence/FractionalCover.lean),
and relates them to the analytic obligations in
[`../obligations.md`](../obligations.md). The first module checks support-change-tolerant
finite-vector algebra without a positive support-mass floor. The second defines the packet's
complete heterogeneous finite categorical keys and keyed shared-exclusions events, then checks
their equivalence-neighborhood, anchoring, intersection, positivity, and law-independence
properties. The third proves the finite equivalence-union fractional-cover load inequality and
instantiates it for the source, target-restricted, and target events. These modules still do not
define averaged Sx cumulatives or atoms, a probability-law type, the complete redundancy lattice,
or Rust values.

The complete replay and digest record is
[`../route-memos/formal.md`](../route-memos/formal.md).

## Definitions

| Lean name | Exact role | Semantic limitation |
|---|---|---|
| `overlapMass` | Coordinatewise minimum of two real vectors | Not a coupling object or probability-law construction |
| `leftResidual` | First vector minus coordinatewise overlap | No PMF or total-variation type |
| `rightResidual` | Second vector minus coordinatewise overlap | No PMF or total-variation type |
| `residualEntropy` | Finite sum of `Real.negMulLog` over a residual vector | Not an Sx entropy or atom definition |
| `residualPositiveSupport` | Finite set of coordinates with positive residual | The ambient finite type remains fixed |
| `downSetZetaMatrix` | Generic matrix with entry one when the column is below the row | Not identified with the Sx redundancy lattice |
| `equivalenceUnionCommonModulus` | Scalar function $g_J(\eta)$ | Not proved to bound a paper-defined event functional |
| `CategoricalKey` | Exact dependent Cartesian product `((i : sourceIndex) → sourceValue i) × targetValue` | Each coordinate may have its own finite alphabet; all source alphabets currently inhabit one universe level |
| `sourceCollectionEquivalent` | Equality on every source coordinate selected by one finite collection | No antichain premise is needed at the event-construction layer |
| `targetEquivalent` | Equality of target values | Pure categorical predicate |
| `sourceTargetCollectionEquivalent` | Conjunction of one source-collection match and target match | Pure categorical predicate |
| `sourceBranchEvent` | Complete ambient-key equivalence class for one source collection | Independent of law masses |
| `targetBranchEvent` | Complete ambient-key target equivalence class | Independent of law masses |
| `sourceTargetBranchEvent` | Complete ambient-key source-and-target equivalence class | Independent of law masses |
| `IsEquivalenceClassNeighborhood` | Predicate identifying a keyed branch with one equivalence class | Does not prove an analytic load inequality |
| `IsFiniteEquivalenceUnion` | Predicate identifying a keyed event with a finite branch union | Its witness has exactly `branches.card` indexed branches |
| `sxSourceEvent` | Union of source-collection branches, the packet's $A_\beta$ | Collections are accepted as a finite family; antichain validity is external |
| `sxTargetRestrictedEvent` | Union of source-and-target branches, the packet's $B_\beta$ | Collections are accepted as a finite family |
| `SxKeyedEvents` and `sxKeyedEvents` | Bundled $A_\beta$, $C$, and $B_\beta$ event triple | No local logarithms or averages |
| `sxKeyedEventsUnderLaw` | Law-indexed view used to state fixed-map equality | The law is intentionally absent from every event predicate |
| `finiteEventMass` | Finite sum of a real mass vector on an event | Does not bundle PMF conditions |
| `positiveMassSupport` | Finite set of anchors with strictly positive overlap mass | Defined for an arbitrary nonnegative real vector, not a bundled PMF |
| `equivalenceClassCoverWeight` | Candidatewise fractional weight accumulated from positive-overlap anchors | Its at-most-one theorem requires one equivalence-class neighborhood |
| `equivalenceNeighborhoodOverlapLoad` | The support-restricted load $T_N(r,d)=\sum_{x:r_x>0}r_x\,d(N_x)/r(N_x)$ | Defined for an arbitrary keyed finite-event map; structural assumptions enter the theorems |

## R1: overlap and residual algebra

| Lean theorem | Checked analytic fact | Imported premises or boundary |
|---|---|---|
| `overlap_add_left_residual` | Overlap plus the left residual reconstructs the first vector coordinatewise | Pure real-vector identity |
| `overlap_add_right_residual` | Overlap plus the right residual reconstructs the second vector coordinatewise | Pure real-vector identity |
| `left_residual_nonnegative` | Every left residual coordinate is nonnegative | Follows from coordinatewise minimum |
| `right_residual_nonnegative` | Every right residual coordinate is nonnegative | Follows from coordinatewise minimum |
| `left_or_right_residual_eq_zero` | At least one residual vanishes at every coordinate | Does not construct a coupling |
| `left_residual_sub_right_residual` | Residual difference equals the original coordinate difference | Pure real-vector identity |
| `abs_sub_eq_left_add_right_residual` | Absolute coordinate difference equals the sum of the two residuals | Uses coordinatewise residual disjointness |
| `sum_left_residual_eq_sum_right_residual` | Equal-total vectors have equal residual masses | Assumes equality of total sums |
| `sum_abs_sub_eq_two_mul_sum_left_residual` | The finite $\ell_1$ distance equals twice the left residual mass | Assumes equality of total sums; no semantic TV definition |
| `sum_overlap_eq_one_sub_sum_left_residual` | Total overlap is one minus left residual mass | Assumes the first vector sums to one |
| `left_residual_le_of_nonnegative` | Left residual is bounded by the first base vector | Assumes both base coordinates are nonnegative |
| `right_residual_le_of_nonnegative` | Right residual is bounded by the second base vector | Assumes both base coordinates are nonnegative |

These results check abstract R1 algebra. They do not bundle normalization, nonnegativity, and finite
support into a probability-law structure, and they do not connect the residual mass to a library
definition of total variation.

## E1: support reduction and residual entropy

| Lean theorem | Checked analytic fact | Imported premises or boundary |
|---|---|---|
| `residual_eq_zero_outside_positive_support` | A nonnegative residual vanishes outside its positive support | Assumes coordinatewise nonnegativity |
| `positive_support_card_positive_of_sum_positive` | Positive residual mass implies nonempty positive support | Assumes nonnegativity and positive total mass |
| `sum_positive_support_eq_sum` | Restricting a nonnegative residual sum to positive support preserves its total | Exact finite sum |
| `left_right_positive_support_disjoint` | Positive supports of the overlap residuals are disjoint | Pure overlap construction |
| `residual_entropy_nonnegative` | Residual entropy is nonnegative | Assumes every coordinate lies in $[0,1]$ |
| `sum_neg_mul_log_le_card_mul_neg_mul_log_average` | Jensen bounds a finite support sum by support size times the entropy summand at average mass | Assumes nonempty support and nonnegative masses |
| `residual_entropy_le_card_mul_neg_mul_log_average` | The Jensen bound controls the full residual entropy when mass vanishes off the stated support | Assumes nonempty support, nonnegativity, and the outside-zero premise |
| `card_mul_neg_mul_log_average_eq_mass_mul_log_card_div_mass` | Converts the average-mass form to $m\log(k/m)$ | Assumes positive cardinality and positive mass |
| `residual_entropy_le_mass_mul_log_card_div_mass` | Bounds one residual entropy by $m\log(k/m)$ | Assumes positive support size and mass plus exact support and total premises |
| `card_mul_card_le_balanced_ambient` | Two disjoint support cardinalities have product at most $\lfloor K^2/4\rfloor$ | Fixed finite ambient type |
| `add_residual_entropy_le_mass_mul_log_card_product_div_mass_sq` | Bounds two equal-mass residual entropies using the product of their support sizes | Assumes both support sizes and repeated mass are positive |
| `add_residual_entropy_le_balanced_ambient_bound` | Replaces the support product by the balanced ambient ceiling | Assumes disjoint nonempty supports and positive repeated mass |
| `overlap_residual_entropy_sum_le_balanced_ambient_bound` | For equal-total vectors and $\eta>0$, checks $H(r^p)+H(r^q)\leq\eta\log(\lfloor K^2/4\rfloor/\eta^2)$ | Assumes equal totals and strictly positive left residual total |

The last theorem is the strongest packaged residual-entropy result. It assumes $\eta>0$; the
module has no combined theorem covering $\eta=0$. Its comment notes the probability
interpretation, but its formal statement contains only real vectors, equal finite sums, and a
positive residual total.

## E1: abstract component transfer

| Lean theorem | Checked analytic fact | Imported premises or boundary |
|---|---|---|
| `residual_weighted_component_between_zero_and_entropy` | A residual-weighted nonnegative component lies between zero and residual entropy | Pointwise sign, residual/base domination, and surprisal upper bound are premises |
| `abs_residual_weighted_signed_value_le_entropy` | The absolute residual-weighted sum of a signed value is at most residual entropy | Pointwise absolute surprisal envelope is a premise |
| `abs_component_residual_sub_le_max_entropy` | The difference of two nonnegative bounded residual contributions is controlled by the larger entropy ceiling | Abstract scalar premises only |
| `abs_signed_residual_sub_le_add_entropy` | The difference of two signed bounded residual contributions is controlled by the sum of entropy ceilings | Abstract scalar premises only |
| `abs_overlap_component_residual_sub_le_max_entropy` | Applies the nonnegative-component transfer directly to overlap residuals | Base-vector nonnegativity and both pointwise component envelopes remain premises |
| `abs_overlap_signed_residual_sub_le_add_entropy` | Applies signed transfer directly to overlap residuals | Base-vector nonnegativity and both absolute pointwise envelopes remain premises |

These theorems do not prove that informative or misinformative Sx components satisfy the imported
pointwise premises. They also do not define a net Sx quantity. Instantiating them requires the
paper-defined event formulas, component theorems, top-node zeta reconstruction, boundary
convention, and averaging bridge.

## S1 and B1: finite categorical event semantics

| Lean theorem | Checked analytic fact | Imported premises or boundary |
|---|---|---|
| `source_collection_equivalence` | Matching all coordinates in a selected source collection is an equivalence relation on complete keys | Uses the packet's finite-key definition |
| `target_equivalence` | Target matching is an equivalence relation | Pure equality |
| `source_target_collection_equivalence` | Conjoining source-collection and target matching remains an equivalence relation | Pure conjunction of the preceding relations |
| `equivalence_class_neighborhood_anchor_mem` | Every equivalence-class neighborhood contains its keyed anchor | Generic equivalence-class premise |
| `finite_equivalence_union_anchor_mem` | Every nonempty finite equivalence-class union satisfies the generic anchor condition | Assumes a nonempty branch family |
| `source_branch_is_equivalence_class` | A source branch contains exactly the keys equivalent to its keyed anchor | Complete fixed ambient key type |
| `target_branch_is_equivalence_class` | The target event is exactly one target-equivalence class | Complete fixed ambient key type |
| `source_target_branch_is_equivalence_class` | A target-restricted source branch is exactly one conjunctive equivalence class | Complete fixed ambient key type |
| `source_branch_anchor_mem` | Every source branch contains its key | Reflexivity |
| `target_branch_anchor_mem` | Every target branch contains its key | Reflexivity |
| `source_target_branch_anchor_mem` | Every target-restricted source branch contains its key | Reflexivity |
| `sx_source_event_equivalence_union` | $A_\beta$ is a union of exactly `collections.card` source-equivalence branches | The finite family need not be proved to be an antichain for this event fact |
| `sx_target_restricted_event_equivalence_union` | $B_\beta$ is a union of exactly `collections.card` source-and-target equivalence branches | Same finite-family boundary |
| `sx_target_event_equivalence_union` | $C$ is a one-branch target-equivalence union | Exact one-branch witness |
| `sx_source_event_anchor_mem` | A nonempty $A_\beta$ contains its key | Assumes the collection family is nonempty |
| `sx_target_restricted_event_anchor_mem` | A nonempty $B_\beta$ contains its key | Assumes the collection family is nonempty |
| `source_target_branch_event_eq_inter` | Each target-restricted branch is its source branch intersected with $C$ | Exact finite-event equality |
| `sx_target_restricted_event_eq_inter` | $B_\beta=A_\beta\cap C$ | Exact finite-event equality, including overlapping source branches |
| `sx_keyed_events_fixed_across_laws` | Two mass vectors on the same complete ambient key type induce definitionally equal event triples | This is event-map equality, not equality of evaluated event masses |
| `sx_source_event_mass_positive` | Positive anchor mass makes $p(A_\beta(z))>0$ | Assumes nonnegative masses and a nonempty collection family |
| `sx_target_event_mass_positive` | Positive anchor mass makes $p(C(z))>0$ | Assumes nonnegative masses |
| `sx_target_restricted_event_mass_positive` | Positive anchor mass makes $p(B_\beta(z))>0$ | Assumes nonnegative masses and a nonempty collection family |

These results close the concrete finite event-construction seam used by the packet: conjunction
within a source collection, disjunction across collections, target intersection, the exact
$J=|\beta|$ equivalence-class cover, keyed anchoring, and a fixed event map across support
changes. They do not formalize the bibliographic claim that these definitions reproduce a
particular publication; that provenance mapping remains documentary evidence. They also do not
define a support-restricted logarithmic local-information functional or connect the definitions
to Rust. The finite-load inequality for these exact event maps is checked separately below.

## G1: finite equivalence-union fractional-cover load

For nonnegative finite vectors $r,d$ and a keyed finite-event map $N$, the checked definition is

$$
T_N(r,d)=
\sum_{x:r_x>0}
r_x\,\frac{d(N_x)}{r(N_x)}.
$$

No probability normalization is used. The named-total theorem assumes
$\sum_x d_x=\eta$; coordinatewise nonnegativity then entails $\eta\geq0$.

| Lean theorem | Checked analytic fact | Imported premises or boundary |
|---|---|---|
| `equivalence_class_neighborhood_eq_of_related` | Related anchors have identical equivalence-class neighborhoods | Generic equivalence relation and exact class-membership premise |
| `equivalence_class_event_mass_positive_on_support` | Every denominator for a positive-overlap anchor is strictly positive | Nonnegative overlap vector and one equivalence-class neighborhood |
| `positive_support_filter_event_sum_eq_event_mass` | Removing zero-mass cells from a finite event leaves its nonnegative mass unchanged | Pointwise nonnegativity |
| `equivalence_class_cover_weight_le_one` | The candidatewise fractional-cover coefficient of one equivalence class is at most one | Includes the zero-class-mass case; no division-by-zero premise is hidden |
| `equivalence_neighborhood_overlap_load_eq_cover_sum` | Finite Fubini/regrouping rewrites $T_N$ as residual mass times candidatewise cover weight | Exact finite sums; no sign premise needed for the equality |
| `equivalence_class_overlap_load_le_total` | One equivalence-class neighborhood satisfies $T_N(r,d)\leq\sum_x d_x$ | Both vectors are pointwise nonnegative |
| `finite_event_mass_nonnegative` | A finite event has nonnegative mass | Pointwise nonnegative vector |
| `equivalence_neighborhood_overlap_load_nonnegative` | $T_N(r,d)\geq0$ for every keyed finite-event map | Both vectors are pointwise nonnegative; no equivalence-cover premise is needed |
| `finite_event_mass_mono` | Event mass is monotone under finite-set inclusion | Pointwise nonnegative vector |
| `finite_event_mass_union_le` | The mass of a union is at most the sum of branch masses | Repeated cells may be counted twice on the right |
| `finite_event_mass_biUnion_le_sum` | A finite union's mass is at most the sum of all indexed branch masses | Repeated cells may be counted once per branch on the right |
| `finite_equivalence_union_event_mass_positive_on_support` | A nonempty equivalence union has a strictly positive denominator at every positive-overlap anchor | Nonempty indexed branch family |
| `finite_equivalence_union_ratio_le_branch_sum` | At each positive-overlap anchor, the union ratio is bounded by the sum of branch ratios | Nonempty cover plus nonnegative overlap and residual vectors; branch and union denominator positivity is proved internally |
| `finite_equivalence_union_overlap_load_le_of_nonempty` | A nonempty $J$-branch union satisfies $T_N(r,d)\leq J\sum_xd_x$ | Exact `IsFiniteEquivalenceUnion` witness |
| `finite_equivalence_union_overlap_load_le` | The same $J$-branch bound also holds for an empty cover | Empty cover is split explicitly and has zero load |
| `finite_equivalence_union_fractional_cover_bound` | If $\sum_xd_x=\eta$, then $T_N(r,d)\leq J\eta$ | This is the requested generic finite fractional-cover theorem |
| `finite_equivalence_union_fractional_cover_bounds` | Packages $0\leq T_N(r,d)\leq J\eta$ | Same complete hypotheses as the named-total upper bound |
| `sx_source_fractional_cover_bound` | $T_{A_\beta}(r,d)\leq\lvert\beta\rvert\eta$ | Uses the exact heterogeneous-key source-event cover; collections need not be nonempty |
| `sx_target_restricted_fractional_cover_bound` | $T_{B_\beta}(r,d)\leq\lvert\beta\rvert\eta$ | Uses the exact source-and-target branch cover; collections need not be nonempty |
| `sx_target_fractional_cover_bound` | $T_C(r,d)\leq\eta$ | The target event is one equivalence class |

This closes the finite combinatorial load step, including support restriction, denominator
positivity, duplicate branch overlap, and the empty-cover endpoint. It does **not** by itself
bound a logarithmic common term. That next step must define the relevant support-restricted log
functional, derive its path/integral comparison from this load theorem, and identify the result
with the paper-defined informative or misinformative Sx cumulative.

## M1: generic zeta/Möbius row identity

| Lean theorem | Checked analytic fact | Imported premises or boundary |
|---|---|---|
| `mobius_row_sum_eq_ite_bot` | A row of a supplied left inverse of the generic down-set zeta matrix sums to one at the least node and zero elsewhere | Assumes a finite partial order with a least node and assumes the supplied matrix-left-inverse equation |

This theorem does not construct the full antichain lattice, prove its orientation, calculate its
Möbius inverse, identify that inverse with an implementation matrix, or prove that inversion
commutes with averaging.

## G1: scalar common-modulus properties

| Lean theorem | Checked analytic fact | Imported premises or boundary |
|---|---|---|
| `equivalence_union_common_modulus_zero` | $g_J(0)=0$ | Scalar identity |
| `equivalence_union_common_modulus_one` | The totalized field expression evaluates to zero at $\eta=1$ | This is an endpoint value, not an event-functional bound |
| `equivalence_union_common_modulus_nonnegative` | $g_J(\eta)\geq0$ for $0\leq\eta<1$ | Assumes the stated interval |
| `equivalence_union_common_modulus_le_linear` | $g_J(\eta)\leq J\eta$ for $0\leq\eta<1$ | Assumes the stated interval |
| `equivalence_union_common_modulus_closed_interval_bounds` | $0\leq g_J(\eta)\leq J\eta$ for $0\leq\eta\leq1$ | Splits the strict interior from the explicitly defined $\eta=1$ value; still only a scalar result |

The event bridge checks that $A_\beta$ and $B_\beta$ satisfy the finite
$J=|\beta|$ union-of-equivalence-neighborhood structural premise, and that $C$ satisfies its
one-branch version. `finite_equivalence_union_fractional_cover_bound` now checks
$T_N\leq J\eta$, and the three Sx corollaries instantiate it for those concrete event maps.
No theorem yet derives the scalar logarithmic modulus $g_J$ from this load inequality, proves the
paper-defined weighted common-term bound, or formalizes a sharpness witness.

## Analytic obligations not represented by a checked theorem

| Obligation | Missing bridge |
|---|---|
| Probability semantics | Probability-law type, normalization/nonnegativity package, semantic total variation, and maximal coupling |
| B1 | Support-restricted logarithmic functional and equality with any fixed-alphabet totalization; keyed event positivity is checked |
| G1 remaining bridge | The support-restricted load $T_N$ and its $J\eta$ bound are checked. Still missing are the support-restricted logarithmic functional $L_N$, the path/integral transfer from $T_N$ to the scalar modulus, and identification with paper-defined Sx common terms |
| S1 provenance boundary | Machine identification of the checked event definitions with the cited publication; the finite source-collection union and target-intersection semantics themselves are checked |
| N1 | Formal transfer of the published informative and misinformative pointwise component results, including the top-node zeta route to the required envelope |
| A1 | Averaged informative, misinformative, and net cumulative continuity |
| M1 | Concrete full-lattice zeta/Möbius identification and commutation of finite inversion with averaging |
| A2 and A3 | Averaged component and net atom continuity |
| F1 | End-to-end composition of the categorical SxPID semantic path |
| Residual endpoint packaging | One residual-entropy theorem covering both $\eta=0$ and $\eta>0$ |
| Pointwise boundary behavior | No pointwise continuity statement; the packet retains counterexamples separately |
| Quantitative sharpness | No formal sharpness witness for $g_J$ or another modulus |
| T1 | Sampling, concentration, consistency, dependence, or calibration results |
| I1 | Rust implementation refinement, binary64 error, fixture, or oracle correspondence |

## Permitted citation

The artifact may be cited as a checked exact-real finite-vector, residual-entropy, conditional
transfer, generic matrix-row, scalar-modulus, heterogeneous finite categorical Sx event-semantics,
and finite equivalence-union fractional-cover route. In particular, the exact
equivalence-class covers for $A_\beta$, $B_\beta$, and $C$, the identity
$B_\beta=A_\beta\cap C$, anchor positivity, the law-independent event map, and
$T_{A_\beta},T_{B_\beta}\leq\lvert\beta\rvert\eta$ with $T_C\leq\eta$ are checked. It must not be cited as a
proof of the complete categorical SxPID continuity theorem, the logarithmic common-term transfer,
a probability-semantic theorem, or a Rust implementation theorem.
