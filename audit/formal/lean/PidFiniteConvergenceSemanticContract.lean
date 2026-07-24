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
  simp [sxSourceEvent, sourceBranchEvent, sourceCollectionEquivalent]

/-! The target event matches exactly the target coordinate. -/
example
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (anchor candidate : CategoricalKey sourceIndex sourceValue targetValue) :
    candidate ∈ targetBranchEvent anchor ↔ anchor.2 = candidate.2 := by
  classical
  simp [targetBranchEvent, targetEquivalent]

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
  simp [
    sxTargetRestrictedEvent,
    sourceTargetBranchEvent,
    sourceTargetCollectionEquivalent,
    sourceCollectionEquivalent,
    targetEquivalent
  ]

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
