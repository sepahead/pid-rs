import PidFiniteConvergence

/-!
# Semantic contract for paper-facing finite-event claims

This file is checked separately from the `PidFiniteConvergence` library root.  Its examples pin
the intended source-event disjunction, target restriction, concrete fractional-cover corollaries,
and the generic (supplied-inverse) scope of the Möbius row claim.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators

open PidFiniteConvergence

universe u v w

/-! The source event is a disjunction across collections and a conjunction within each one. -/
example
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex))
    (anchor candidate : CategoricalKey sourceIndex sourceValue targetValue) :
    candidate ∈ sxSourceEvent collections anchor ↔
      ∃ collection ∈ collections,
        ∀ source ∈ collection, anchor.1 source = candidate.1 source := by
  classical
  unfold sxSourceEvent sourceBranchEvent
  constructor
  · intro h
    rcases Finset.mem_biUnion.mp h with ⟨collection, hcollection, hbranch⟩
    exact ⟨collection, hcollection, (Finset.mem_filter.mp hbranch).2⟩
  · rintro ⟨collection, hcollection, hsource⟩
    exact Finset.mem_biUnion.mpr
      ⟨collection, hcollection,
        Finset.mem_filter.mpr ⟨Finset.mem_univ candidate, hsource⟩⟩

/-! The target event matches exactly the target coordinate. -/
example
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (anchor candidate : CategoricalKey sourceIndex sourceValue targetValue) :
    candidate ∈ targetBranchEvent anchor ↔ anchor.2 = candidate.2 := by
  classical
  unfold targetBranchEvent
  constructor
  · intro h
    exact (Finset.mem_filter.mp h).2
  · intro h
    exact Finset.mem_filter.mpr ⟨Finset.mem_univ candidate, h⟩

/-! The target-restricted source event conjoins each source branch with target matching. -/
example
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex))
    (anchor candidate : CategoricalKey sourceIndex sourceValue targetValue) :
    candidate ∈ sxTargetRestrictedEvent collections anchor ↔
      ∃ collection ∈ collections,
        (∀ source ∈ collection, anchor.1 source = candidate.1 source) ∧
          anchor.2 = candidate.2 := by
  classical
  unfold sxTargetRestrictedEvent sourceTargetBranchEvent
  constructor
  · intro h
    rcases Finset.mem_biUnion.mp h with ⟨collection, hcollection, hbranch⟩
    exact ⟨collection, hcollection, (Finset.mem_filter.mp hbranch).2⟩
  · rintro ⟨collection, hcollection, hbranch⟩
    exact Finset.mem_biUnion.mpr
      ⟨collection, hcollection,
        Finset.mem_filter.mpr ⟨Finset.mem_univ candidate, hbranch⟩⟩

/-! The keyed target restriction is exactly the source event intersected with target matching. -/
example
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex))
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    sxTargetRestrictedEvent collections anchor =
      sxSourceEvent collections anchor ∩ targetBranchEvent anchor := by
  exact sx_target_restricted_event_eq_inter collections anchor

/-! The source, target-restricted, and target events have the stated equivalence-class covers. -/
example
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex)) :
    IsFiniteEquivalenceUnion
          collections
          (fun collection =>
            sourceCollectionEquivalent
              (sourceValue := sourceValue) (targetValue := targetValue) collection)
          sourceBranchEvent
          (sxSourceEvent collections) ∧
      IsFiniteEquivalenceUnion
          collections
          (fun collection =>
            sourceTargetCollectionEquivalent
              (sourceValue := sourceValue) (targetValue := targetValue) collection)
          sourceTargetBranchEvent
          (sxTargetRestrictedEvent collections) ∧
        IsFiniteEquivalenceUnion
          ({()} : Finset Unit)
          (fun _ =>
            targetEquivalent
              (sourceIndex := sourceIndex) (sourceValue := sourceValue)
              (targetValue := targetValue))
          (fun _ => targetBranchEvent)
          targetBranchEvent := by
  exact
    ⟨sx_source_event_equivalence_union collections,
      sx_target_restricted_event_equivalence_union collections,
      sx_target_event_equivalence_union⟩

/-! The keyed event map depends on the ambient key and anchor, not on the supplied law. -/
example
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (leftLaw rightLaw : CategoricalKey sourceIndex sourceValue targetValue → ℝ)
    (collections : Finset (Finset sourceIndex))
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    sxKeyedEventsUnderLaw leftLaw collections anchor =
      sxKeyedEventsUnderLaw rightLaw collections anchor := by
  exact sx_keyed_events_fixed_across_laws leftLaw rightLaw collections anchor

/-! Positive anchor mass makes all three keyed event masses strictly positive. -/
example
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    {collections : Finset (Finset sourceIndex)}
    (hcollections : collections.Nonempty)
    (mass : CategoricalKey sourceIndex sourceValue targetValue → ℝ)
    (hmassNonnegative : ∀ key, 0 ≤ mass key)
    (anchor : CategoricalKey sourceIndex sourceValue targetValue)
    (hanchorPositive : 0 < mass anchor) :
    0 < finiteEventMass mass (sxSourceEvent collections anchor) ∧
      0 < finiteEventMass mass (targetBranchEvent anchor) ∧
        0 < finiteEventMass mass (sxTargetRestrictedEvent collections anchor) := by
  exact
    ⟨sx_source_event_mass_positive
        hcollections mass hmassNonnegative anchor hanchorPositive,
      sx_target_event_mass_positive
        mass hmassNonnegative anchor hanchorPositive,
      sx_target_restricted_event_mass_positive
        hcollections mass hmassNonnegative anchor hanchorPositive⟩

/-!
The generic finite-union theorem needs only the displayed nonnegativity, cover, and named residual
total premises.  In particular, it does not import a probability-law normalization premise.
-/
example
    {key : Type u} {branch : Type v}
    [Fintype key] [DecidableEq branch] [DecidableEq key]
    (overlap residual : key → ℝ)
    {branches : Finset branch}
    {relation : branch → key → key → Prop}
    {neighborhood : branch → key → Finset key}
    {event : key → Finset key}
    (hcover : IsFiniteEquivalenceUnion branches relation neighborhood event)
    (hoverlap : ∀ x, 0 ≤ overlap x)
    (hresidual : ∀ x, 0 ≤ residual x)
    {eta : ℝ}
    (hresidualTotal : finiteEventMass residual Finset.univ = eta) :
    equivalenceNeighborhoodOverlapLoad overlap residual event ≤
      branches.card * eta := by
  exact
    finite_equivalence_union_fractional_cover_bound
      overlap residual hcover hoverlap hresidual hresidualTotal

/-!
For the categorical event map, the source and target-restricted loads have the collection-cardinal
factor, while the one-class target load has factor one.
-/
example
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex))
    (overlap residual : CategoricalKey sourceIndex sourceValue targetValue → ℝ)
    (hoverlap : ∀ key, 0 ≤ overlap key)
    (hresidual : ∀ key, 0 ≤ residual key)
    {eta : ℝ}
    (hresidualTotal : finiteEventMass residual Finset.univ = eta) :
    equivalenceNeighborhoodOverlapLoad overlap residual
          (sxSourceEvent collections) ≤
        collections.card * eta ∧
      equivalenceNeighborhoodOverlapLoad overlap residual
            (sxTargetRestrictedEvent collections) ≤
          collections.card * eta ∧
        equivalenceNeighborhoodOverlapLoad overlap residual targetBranchEvent ≤
          eta := by
  exact
    ⟨sx_source_fractional_cover_bound
        collections overlap residual hoverlap hresidual hresidualTotal,
      sx_target_restricted_fractional_cover_bound
        collections overlap residual hoverlap hresidual hresidualTotal,
      sx_target_fractional_cover_bound
        overlap residual hoverlap hresidual hresidualTotal⟩

/-!
The Möbius row identity is generic: the order is any finite partial order with a least node, and
the matrix is supplied together with the displayed left-inverse equation.
-/
example
    {κ : Type u}
    [Fintype κ] [DecidableEq κ] [PartialOrder κ] [DecidableLE κ] [OrderBot κ]
    (mobius : Matrix κ κ ℝ)
    (hinverse : mobius * downSetZetaMatrix κ = 1)
    (row : κ) :
    ∑ column, mobius row column = if row = ⊥ then 1 else 0 := by
  exact mobius_row_sum_eq_ite_bot mobius hinverse row

/-!
The four two-source nodes are cumulative event nodes.  In particular, the one-source and joint
nodes are not labels for unique-information or synergy atoms.
-/
example :
    sxPid2Collections .sourceOne = {{0}} ∧
      sxPid2Collections .sourceTwo = {{1}} ∧
        sxPid2Collections .jointSources = {{0, 1}} ∧
          sxPid2Collections .redundancy = {{0}, {1}} := by
  exact sx_pid2_node_collection_semantics

private def sxPid2AsymmetricCount
    (key : CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2)) : ℕ :=
  match (key.1 0).val, (key.1 1).val, key.2.val with
  | 0, 0, 0 => 1
  | 0, 0, 1 => 2
  | 0, 1, 0 => 3
  | 0, 1, 1 => 4
  | 1, 0, 0 => 5
  | 1, 0, 1 => 8
  | 1, 1, 0 => 6
  | 1, 1, 1 => 7
  | _, _, _ => 0

private def sxPid2AsymmetricAnchor :
    CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2) :=
  (![0, 0], 0)

private def sxPid2AllBinaryKeys :
    Finset (CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2)) :=
  {(![0, 0], 0), (![0, 0], 1), (![0, 1], 0), (![0, 1], 1),
    (![1, 0], 0), (![1, 0], 1), (![1, 1], 0), (![1, 1], 1)}

private def sxPid2SourceOneOnlyCandidate :
    CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2) :=
  (![0, 1], 1)

private def sxPid2MarginalButNotJointCandidate :
    CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2) :=
  (![0, 1], 0)

/-!
This asymmetric witness separates the two sources, redundancy union, target restriction, and
joint-source event.  A source swap or erased target restriction changes the proposition.
-/
example :
    sxPid2SourceOneOnlyCandidate ∈
        sxPid2SourceEvent .sourceOne sxPid2AsymmetricAnchor ∧
      sxPid2SourceOneOnlyCandidate ∉
        sxPid2SourceEvent .sourceTwo sxPid2AsymmetricAnchor ∧
      sxPid2SourceOneOnlyCandidate ∈
        sxPid2SourceEvent .redundancy sxPid2AsymmetricAnchor ∧
      sxPid2SourceOneOnlyCandidate ∉
        sxPid2TargetRestrictedEvent .sourceOne sxPid2AsymmetricAnchor ∧
      sxPid2MarginalButNotJointCandidate ∈
        sxPid2TargetRestrictedEvent .sourceOne sxPid2AsymmetricAnchor ∧
      sxPid2MarginalButNotJointCandidate ∉
        sxPid2TargetRestrictedEvent .jointSources sxPid2AsymmetricAnchor := by
  norm_num [sxPid2SourceOneOnlyCandidate, sxPid2MarginalButNotJointCandidate,
    sxPid2AsymmetricAnchor, sxPid2SourceEvent, sxPid2TargetRestrictedEvent,
    sxPid2Collections, sxSourceEvent, sxTargetRestrictedEvent, sourceBranchEvent,
    sourceTargetBranchEvent, sourceTargetCollectionEquivalent,
    sourceCollectionEquivalent, targetEquivalent]

/-! Exact total, target, and four source-event counts for the asymmetric witness. -/
example :
    totalCount sxPid2AsymmetricCount = 36 ∧
      eventCount sxPid2AsymmetricCount
          (targetBranchEvent sxPid2AsymmetricAnchor) = 15 ∧
        eventCount sxPid2AsymmetricCount
            (sxPid2SourceEvent .sourceOne sxPid2AsymmetricAnchor) = 10 ∧
          eventCount sxPid2AsymmetricCount
              (sxPid2SourceEvent .sourceTwo sxPid2AsymmetricAnchor) = 16 ∧
            eventCount sxPid2AsymmetricCount
                (sxPid2SourceEvent .jointSources sxPid2AsymmetricAnchor) = 3 ∧
              eventCount sxPid2AsymmetricCount
                  (sxPid2SourceEvent .redundancy sxPid2AsymmetricAnchor) = 23 :=
  set_option backward.isDefEq.respectTransparency.types false in by
  have h_univ :
      (Finset.univ : Finset (CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2))) =
        sxPid2AllBinaryKeys := by
    decide
  constructor
  · rw [totalCount, h_univ]
    decide
  constructor
  · simp only [eventCount, targetBranchEvent, targetEquivalent]
    rw [h_univ]
    decide
  · simp only [eventCount, sxPid2SourceEvent, sxPid2Collections, sxSourceEvent,
      sourceBranchEvent, sourceCollectionEquivalent]
    rw [h_univ]
    decide

/-! Exact target-restricted counts for all four nodes of the asymmetric witness. -/
example :
    eventCount sxPid2AsymmetricCount
        (sxPid2TargetRestrictedEvent .sourceOne sxPid2AsymmetricAnchor) = 4 ∧
      eventCount sxPid2AsymmetricCount
          (sxPid2TargetRestrictedEvent .sourceTwo sxPid2AsymmetricAnchor) = 6 ∧
        eventCount sxPid2AsymmetricCount
            (sxPid2TargetRestrictedEvent .jointSources sxPid2AsymmetricAnchor) = 1 ∧
          eventCount sxPid2AsymmetricCount
              (sxPid2TargetRestrictedEvent .redundancy sxPid2AsymmetricAnchor) = 9 :=
  set_option backward.isDefEq.respectTransparency.types false in by
  have h_univ :
      (Finset.univ : Finset (CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2))) =
        sxPid2AllBinaryKeys := by
    decide
  simp only [eventCount, sxPid2TargetRestrictedEvent, sxPid2Collections,
    sxTargetRestrictedEvent, sourceTargetBranchEvent,
    sourceTargetCollectionEquivalent, sourceCollectionEquivalent, targetEquivalent]
  rw [h_univ]
  decide

/-!
The four exact rational logarithm arguments are pairwise distinguishable in the asymmetric
witness.  Their order is source one, source two, joint sources, then redundancy.
-/
example :
    countNetArgument sxPid2AsymmetricCount .sourceOne sxPid2AsymmetricAnchor = 24 / 25 ∧
      countNetArgument sxPid2AsymmetricCount .sourceTwo sxPid2AsymmetricAnchor = 9 / 10 ∧
        countNetArgument sxPid2AsymmetricCount .jointSources sxPid2AsymmetricAnchor = 4 / 5 ∧
          countNetArgument sxPid2AsymmetricCount .redundancy sxPid2AsymmetricAnchor =
            108 / 115 :=
  set_option backward.isDefEq.respectTransparency.types false in by
  have h_univ :
      (Finset.univ : Finset (CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2))) =
        sxPid2AllBinaryKeys := by
    decide
  have h_total : totalCount sxPid2AsymmetricCount = 36 := by
    rw [totalCount, h_univ]
    decide
  have h_target :
      eventCount sxPid2AsymmetricCount (targetBranchEvent sxPid2AsymmetricAnchor) = 15 := by
    simp only [eventCount, targetBranchEvent, targetEquivalent]
    rw [h_univ]
    decide
  have h_source :
      eventCount sxPid2AsymmetricCount
          (sxPid2SourceEvent .sourceOne sxPid2AsymmetricAnchor) = 10 ∧
        eventCount sxPid2AsymmetricCount
            (sxPid2SourceEvent .sourceTwo sxPid2AsymmetricAnchor) = 16 ∧
          eventCount sxPid2AsymmetricCount
              (sxPid2SourceEvent .jointSources sxPid2AsymmetricAnchor) = 3 ∧
            eventCount sxPid2AsymmetricCount
                (sxPid2SourceEvent .redundancy sxPid2AsymmetricAnchor) = 23 := by
    simp only [eventCount, sxPid2SourceEvent, sxPid2Collections, sxSourceEvent,
      sourceBranchEvent, sourceCollectionEquivalent]
    rw [h_univ]
    decide
  have h_restricted :
      eventCount sxPid2AsymmetricCount
          (sxPid2TargetRestrictedEvent .sourceOne sxPid2AsymmetricAnchor) = 4 ∧
        eventCount sxPid2AsymmetricCount
            (sxPid2TargetRestrictedEvent .sourceTwo sxPid2AsymmetricAnchor) = 6 ∧
          eventCount sxPid2AsymmetricCount
              (sxPid2TargetRestrictedEvent .jointSources sxPid2AsymmetricAnchor) = 1 ∧
            eventCount sxPid2AsymmetricCount
                (sxPid2TargetRestrictedEvent .redundancy sxPid2AsymmetricAnchor) = 9 := by
    simp only [eventCount, sxPid2TargetRestrictedEvent, sxPid2Collections,
      sxTargetRestrictedEvent, sourceTargetBranchEvent,
      sourceTargetCollectionEquivalent, sourceCollectionEquivalent, targetEquivalent]
    rw [h_univ]
    decide
  simp [countNetArgument, h_total, h_target, h_source.1, h_source.2.1,
    h_source.2.2.1, h_source.2.2.2, h_restricted.1, h_restricted.2.1,
    h_restricted.2.2.1, h_restricted.2.2.2]
  norm_num

/-!
For every finite heterogeneous two-source count table with positive total, positivity is derived on
positive count support and the averaged signed-net cumulative has the exact count expression.
-/
example
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    {anchor : CategoricalKey (Fin 2) sourceValue targetValue}
    (h_total : 0 < totalCount count)
    (hanchor : anchor ∈ positiveSupport count) :
    0 ≤ empiricalLaw count anchor ∧
      0 < countNetArgument count node anchor ∧
        averagedCumulativeNet (empiricalLaw count) node =
          ∑ key ∈ positiveSupport count,
            ((count key : ℝ) / (totalCount count : ℝ)) *
              Real.log ((countNetArgument count node key : ℚ) : ℝ) := by
  exact
    ⟨empirical_law_nonnegative count anchor,
      count_net_argument_positive_on_support count node h_total hanchor,
      sxpid2_averaged_cumulative_net_count_expression count node h_total⟩
