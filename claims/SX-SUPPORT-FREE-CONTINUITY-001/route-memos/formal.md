# Formal route memo

## Route record

| Field | Value |
|---|---|
| Route ID | `SX-SUPPORT-FREE-CONTINUITY-001-FORMAL-01` |
| Historical claim identity | Revision 1; this route was later enlarged through revision 3 |
| Date | 2026-07-24 |
| Mathematical family | Exact-real finite-vector, entropy, matrix, heterogeneous categorical-event, and finite fractional-cover algebra |
| Checked aggregate | [`PidFiniteConvergence.lean`](../../../audit/formal/lean/PidFiniteConvergence.lean), importing exactly six checked submodules |
| New semantic module | [`SxEventBridge.lean`](../../../audit/formal/lean/PidFiniteConvergence/SxEventBridge.lean) |
| New analytic module | [`FractionalCover.lean`](../../../audit/formal/lean/PidFiniteConvergence/FractionalCover.lean) |
| Theorem inventory | [`../formal/theorem-map.md`](../formal/theorem-map.md) |
| Enumerated inventories | 37 support-change theorems; 22 Sx event-bridge theorems; 20 fractional-cover/load theorems |
| Current obligations | Abstract parts of R1 and E1; concrete S1 event semantics; the finite-load part of G1; one generic row identity for M1; scalar properties relevant to G1 |
| Evidence label | `CHECKED-EXACTLY` for the listed Lean statements only |
| Route status | Kernel replay passes; this enlarged partial route did not adjudicate historical revision 1 and does not itself establish the complete support-change continuity theorem |

This route was added after exploratory work had started. It is not preregistered or an independent
audit.

## Scope and terminology

The preferred description is **support-change-tolerant** or **without a positive support-mass
floor**. The checked statements permit zero coordinates and do not assume a uniform positive lower
bound on coordinate mass.

The claim identifier retains the revision-1 `SUPPORT-FREE` spelling as historical packet identity.
The checked module uses the qualified `SupportChangeContinuity.lean` name. The target claim fixes a
finite ambient alphabet, source count, event map, full redundancy lattice, and Möbius inverse.
The formal event bridge now fixes the exact heterogeneous dependent Cartesian product

$$
\left(\prod_{i:\mathcal I}\mathcal S_i\right)\times\mathcal T
$$

as `((i : sourceIndex) → sourceValue i) × targetValue`. Each source coordinate may therefore have
its own finite alphabet; no common tagged alphabet or unreachable cross-coordinate states are
introduced. All source alphabets currently inhabit one Lean universe level, and `Finset.univ`
still enumerates the complete product.

The formal modules define the keyed Sx source union $A_\beta$, target event $C$, and
target-restricted union $B_\beta$, and prove that this map is independent of the supplied law
vector. They do not define or identify the complete Sx redundancy lattice. They do not cover a
changing ambient product, changing collection family, changing event map, or changing lattice.

## Strongest checked results

For two finite real vectors $p,q$, the support-change module defines their coordinatewise overlap
and left and right residuals. Across the checked modules, Lean checks:

1. pointwise reconstruction, residual nonnegativity, and disjoint positive supports;
2. equality of the two residual masses when $p$ and $q$ have equal total mass;
3. the exact identity
   $$
   \sum_i \lvert p_i-q_i\rvert=2\sum_i r_i^p;
   $$
4. for positive repeated residual mass
   $\eta=\sum_i r_i^p=\sum_i r_i^q$ and $K=\lvert\iota\rvert$,
   $$
   H(r^p)+H(r^q)
   \leq
   \eta\log\!\left(\frac{\lfloor K^2/4\rfloor}{\eta^2}\right);
   $$
5. abstract residual-transfer bounds conditional on supplied pointwise sign and surprisal
   envelopes;
6. the row-sum identity for any supplied left inverse of a finite down-set zeta matrix; and
7. endpoint values and the combined bounds
   $0\leq g_J(\eta)\leq J\eta$ for $0\leq\eta\leq1$, where
   $$
   g_J(\eta)
   =
   (1-\eta)\log\!\left(1+\frac{J\eta}{1-\eta}\right).
   $$
8. 22 concrete event-bridge theorems: source, target, and source-target matching are equivalence
   relations; $A_\beta$ and $B_\beta$ are unions of exactly
   $\lvert\beta\rvert$ equivalence-class branches; $C$ is one class;
   $B_\beta=A_\beta\cap C$; keyed events contain their anchors when the branch family is
   nonempty; positive anchor mass makes the needed denominators positive; and the event map is
   fixed across law vectors;
9. the support-restricted finite load
   $$
   T_N(r,d)
   =
   \sum_{x:r_x>0}
   r_x\,\frac{d(N_x)}{r(N_x)}
   $$
   is nonnegative for nonnegative $r,d$, one equivalence-class branch has load at most
   $\sum_xd_x$, and any finite $J$-branch equivalence union satisfies
   $$
   0\leq T_N(r,d)\leq J\eta
   \qquad\text{when}\qquad
   \sum_xd_x=\eta;
   $$
10. the preceding load bound is instantiated for the exact Sx events:
    $$
    T_{A_\beta}(r,d),T_{B_\beta}(r,d)
    \leq
    \lvert\beta\rvert\eta,
    \qquad
    T_C(r,d)\leq\eta.
    $$

The finite-load theorem explicitly handles an empty branch cover and proves strict denominator
positivity on positive-overlap support in the nonempty case. It does not require probability
normalization. The balanced residual-entropy theorem still assumes $\eta>0$ and is not packaged
with its $\eta=0$ endpoint.

## Enumerated new theorem inventories

The checker requires the 22 `SxEventBridge.lean` theorem declarations in this exact grouped
inventory:

| Group | Lean theorem names |
|---|---|
| Relations | `source_collection_equivalence`; `target_equivalence`; `source_target_collection_equivalence` |
| Generic anchors | `equivalence_class_neighborhood_anchor_mem`; `finite_equivalence_union_anchor_mem` |
| Exact branch classes | `source_branch_is_equivalence_class`; `target_branch_is_equivalence_class`; `source_target_branch_is_equivalence_class` |
| Branch anchors | `source_branch_anchor_mem`; `target_branch_anchor_mem`; `source_target_branch_anchor_mem` |
| Exact finite covers | `sx_source_event_equivalence_union`; `sx_target_restricted_event_equivalence_union`; `sx_target_event_equivalence_union` |
| Event anchors and intersections | `sx_source_event_anchor_mem`; `sx_target_restricted_event_anchor_mem`; `source_target_branch_event_eq_inter`; `sx_target_restricted_event_eq_inter` |
| Fixed event map | `sx_keyed_events_fixed_across_laws` |
| Positive event masses | `sx_source_event_mass_positive`; `sx_target_event_mass_positive`; `sx_target_restricted_event_mass_positive` |

The checker separately requires the 20 `FractionalCover.lean` theorem declarations:

| Group | Lean theorem names |
|---|---|
| One-class load route | `equivalence_class_neighborhood_eq_of_related`; `equivalence_class_event_mass_positive_on_support`; `positive_support_filter_event_sum_eq_event_mass`; `equivalence_class_cover_weight_le_one`; `equivalence_neighborhood_overlap_load_eq_cover_sum`; `equivalence_class_overlap_load_le_total` |
| Nonnegativity and finite-event algebra | `finite_event_mass_nonnegative`; `equivalence_neighborhood_overlap_load_nonnegative`; `finite_event_mass_mono`; `finite_event_mass_union_le`; `finite_event_mass_biUnion_le_sum` |
| Finite-union transfer | `finite_equivalence_union_event_mass_positive_on_support`; `finite_equivalence_union_ratio_le_branch_sum`; `finite_equivalence_union_overlap_load_le_of_nonempty`; `finite_equivalence_union_overlap_load_le`; `finite_equivalence_union_fractional_cover_bound`; `finite_equivalence_union_fractional_cover_bounds` |
| Concrete Sx corollaries | `sx_source_fractional_cover_bound`; `sx_target_restricted_fractional_cover_bound`; `sx_target_fractional_cover_bound` |

The complete 37-theorem support-change inventory and role-by-role premise map remain in
[`../formal/theorem-map.md`](../formal/theorem-map.md).

## Pinned replay route

Run from the repository root:

```text
python3 scripts/check-lean-finite-convergence.py
```

The checker:

- requires `leanprover/lean4:v4.32.0`;
- requires the exact Lake project declaration and manifest bytes;
- resolves Mathlib to commit
  `81a5d257c8e410db227a6665ed08f64fea08e997`;
- verifies every dependency checkout against its pinned origin and revision and requires it to be
  clean;
- requires exactly seven project Lean sources and the exact root import list;
- requires `warningAsError` in each checked submodule and rejects its restricted proof-token set;
- requires the exact 37-theorem support-change, 22-theorem Sx event-bridge, and 20-theorem
  fractional-cover inventories;
- rejects regression from the dependent heterogeneous source product to a shared source-value
  alphabet by checking the relevant source declarations;
- runs `lake build PidFiniteConvergence`;
- replays `lake env leanchecker PidFiniteConvergence`; and
- uses Lean's structured `collectAxioms` API, without parsing display output, to reject any logical
  assumption outside `propext`, `Classical.choice`, and `Quot.sound` for all three complete
  enumerated theorem inventories.

Observed successful result:

```text
OK: checked 7 Lean sources for the deterministic finite-alphabet convergence, dependency-color, local-continuity, support-change-tolerant core, heterogeneous finite categorical Sx event bridge, and equivalence-union fractional-cover bound (Lean (version 4.32.0, arm64-apple-darwin24.6.0, commit 8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release))
```

The direct project command also passed:

```text
cd audit/formal/lean
lake build PidFiniteConvergence
lake env leanchecker PidFiniteConvergence
```

## Artifact digests

These SHA-256 values identify the working-tree bytes checked on 2026-07-24. They do not attest to
authorship, provenance, or a committed repository state.

| Artifact | SHA-256 |
|---|---|
| [`audit/formal/lean/PidFiniteConvergence.lean`](../../../audit/formal/lean/PidFiniteConvergence.lean) | `5a3ea91f1523557c9eaeccb9872b4216c768950fdcf289194b61e2ce581559af` |
| [`audit/formal/lean/PidFiniteConvergence/Dependence.lean`](../../../audit/formal/lean/PidFiniteConvergence/Dependence.lean) | `39419a78bd294abdf7d545083ae6207c7e1db9ffbe88c3c03d2545c8397f709e` |
| [`audit/formal/lean/PidFiniteConvergence/Deterministic.lean`](../../../audit/formal/lean/PidFiniteConvergence/Deterministic.lean) | `e9dbd7c5b4578aabf92b76c0b8b684db4c1c1038dcdb033239b0076685c41610` |
| [`audit/formal/lean/PidFiniteConvergence/FractionalCover.lean`](../../../audit/formal/lean/PidFiniteConvergence/FractionalCover.lean) | `4ea504a565a69f5222c205e01050b750e780ed17cb02558fe08e0c32e2f5718c` |
| [`audit/formal/lean/PidFiniteConvergence/LocalContinuity.lean`](../../../audit/formal/lean/PidFiniteConvergence/LocalContinuity.lean) | `ac390d977bce813c7e882f719f33fdaed106fd2b776304f7c119f01bb0483756` |
| [`audit/formal/lean/PidFiniteConvergence/SupportChangeContinuity.lean`](../../../audit/formal/lean/PidFiniteConvergence/SupportChangeContinuity.lean) | `f5b8b110f69e9d879edbc46948fa67153932540c2cf0ad791771fd6fe30c8370` |
| [`audit/formal/lean/PidFiniteConvergence/SxEventBridge.lean`](../../../audit/formal/lean/PidFiniteConvergence/SxEventBridge.lean) | `8fea4b7f215904262c171a0e5ccca0c7111b8e037b91733813c2326ccac84eb3` |
| [`scripts/check-lean-finite-convergence.py`](../../../scripts/check-lean-finite-convergence.py) | `00d19ba6f9cde4006d51f336baf0ffad74d53e63380f3ffe65852059349cd7c9` |
| [`claims/SX-SUPPORT-FREE-CONTINUITY-001/formal/theorem-map.md`](../formal/theorem-map.md) | `98f0ab43b8bd5645438d24985cfd48cf1c5602f75d755f88f31c3a67e6494465` |
| [`audit/formal/lean/lean-toolchain`](../../../audit/formal/lean/lean-toolchain) | `2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e` |
| [`audit/formal/lean/lakefile.toml`](../../../audit/formal/lean/lakefile.toml) | `1c3f1818c4a62ab48f4ae05de573f6d884aaf7f7397a21646df162151cfccdf1` |
| [`audit/formal/lean/lake-manifest.json`](../../../audit/formal/lean/lake-manifest.json) | `e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd` |

## Obligation disposition

| Obligation | What this route checks | What remains |
|---|---|---|
| R1 | Exact overlap/residual identities for equal-total finite vectors | Probability-law types and the semantic identification with total variation |
| E1 | Finite-support entropy bounds and abstract residual transfer | Identification of Sx pointwise values with the sign and surprisal premises |
| S1 event semantics | Exact heterogeneous complete keys; source-collection conjunction; collection-family disjunction; target intersection; equivalence-class covers; anchors; positive event masses; fixed event map across law vectors | Machine-checked provenance identification with the cited Sx publication and the downstream local-information formulas |
| G1 finite load | Exact support-restricted $T_N$, denominator positivity, candidatewise class coefficient, finite-union ratio transfer, empty-cover endpoint, $0\leq T_N\leq J\eta$, and concrete $A_\beta,B_\beta,C$ corollaries | The support-restricted logarithmic functional, path/integral transfer to $g_J$, and identification with paper-defined common terms |
| M1 | A generic row-sum result for a supplied left inverse of a down-set zeta matrix | The paper-defined lattice, its orientation, its concrete inverse, and averaging commutation |
| G1 scalar modulus | Endpoint and closed-interval scalar bounds for the proposed equivalence-union common modulus | A checked theorem deriving that modulus from the finite-load result |
| B1, A1, A2, A3, F1 | No closure | Boundary totalization, averaged Sx cumulatives and atoms, full analytic composition, and semantic closure |
| I1, T1 | No result | Rust/binary64 refinement and statistical claims remain separate |

## Unformalized bridges

The checked modules do **not** establish any of the following:

1. Probability-law or PMF structures, normalization and nonnegativity as one bundled law type,
   semantic total variation, or a maximal-coupling construction. The checked
   $\ell_1=2\eta$ equality is finite-vector algebra only.
2. A support-restricted closed-simplex definition or equality with a fixed-alphabet
   totalization. In particular, B1 remains open.
3. A single packaged theorem identifying the abstract nonnegative vectors in the load theorem
   with `overlapMass p q` and one of the checked residual vectors. The constituent overlap,
   residual, and generic-load results are checked separately.
4. The support-restricted logarithmic loss quantity $L_N$, the path or integral step transferring
   $T_N\leq J\eta$ into the proposed $g_J$ modulus, or a proof that this modulus controls every
   paper-defined common term.
5. Machine-checked bibliographic identification of `sxSourceEvent`,
   `sxTargetRestrictedEvent`, and `targetBranchEvent` with the cited publication's definitions.
   The exact finite event predicates and their structural theorems are checked, but provenance is
   documentary.
6. The premise that a supplied source-collection family is a valid redundancy-lattice antichain,
   the fixed full redundancy lattice, its antichain order, or identification of its zeta and
   Möbius matrices with `downSetZetaMatrix` and the supplied inverse.
7. The Makkeh--Gutknecht--Wibral pointwise component nonnegativity, top-node zeta reconstruction,
   and resulting surprisal envelope. Those properties are premises of the abstract
   residual-transfer statements.
8. Identification of the abstract residual-weighted values with Sx component cumulatives or
   atoms, or proof that pointwise inversion and averaging commute.
9. A continuity theorem for any averaged Sx cumulative or atom, any claim of pointwise boundary
   continuity, or a sharpness witness for $g_J$.
10. Sampling, dependence coloring, concentration, estimator consistency, almost-sure convergence,
    or uncertainty calibration for this categorical functional.
11. Refinement to the Rust categorical implementation, binary64 arithmetic, numerical fixtures,
    or oracle comparisons.

Therefore this route may be cited for the exact heterogeneous categorical event semantics and
finite fractional-cover/load theorem stated above, but it must not be cited as the complete
categorical SxPID continuity theorem, a probability-semantic theorem, or a Rust conformance
theorem. Its checked scope is the exact theorem inventory in
[`../formal/theorem-map.md`](../formal/theorem-map.md).
