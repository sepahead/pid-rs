import PidFiniteConvergence.Deterministic
import Mathlib.Data.Fintype.Pi

/-!
# Finite categorical shared-exclusions event bridge

This module defines a complete finite categorical key, source-collection matching, target
matching, source-event unions, and target-restricted source-event unions.  It proves the semantic
facts needed to instantiate a theorem for unions of equivalence-class neighborhoods:

* source matching, target matching, and their conjunction are equivalence relations;
* each branch event is exactly the equivalence class of its keyed anchor;
* the source event and target-restricted event are finite unions of those branch classes;
* the target event is one equivalence class;
* every nonempty keyed event contains its anchor;
* the target-restricted event is the intersection of the source and target events;
* positive mass at the keyed anchor makes every relevant event mass positive; and
* the complete event map is independent of the law whose masses are later evaluated.

The key uses a dependent Cartesian product: source coordinate `i` has its own finite alphabet
`sourceValue i`.  Thus the formal ambient space is exactly
`((i : sourceIndex) → sourceValue i) × targetValue`; no tagged common-alphabet embedding or
unreachable cross-coordinate states are introduced.

This module does not define local information values, averaged cumulatives, the redundancy
lattice, Möbius inversion, sampling, or executable arithmetic.  Its role is the finite event
semantics between categorical keys and an abstract equivalence-neighborhood continuity theorem.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators

namespace PidFiniteConvergence

universe u v w x

/-- A complete categorical realization with finitely many source coordinates and one target. -/
abbrev CategoricalKey (sourceIndex : Type u) (sourceValue : sourceIndex → Type v)
    (targetValue : Type w) :=
  ((source : sourceIndex) → sourceValue source) × targetValue

/-- Two keys match a source collection when every selected source coordinate agrees. -/
def sourceCollectionEquivalent
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    (collection : Finset sourceIndex)
    (left right : CategoricalKey sourceIndex sourceValue targetValue) : Prop :=
  ∀ source ∈ collection, left.1 source = right.1 source

/-- Two keys match at the target coordinate. -/
def targetEquivalent
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    (left right : CategoricalKey sourceIndex sourceValue targetValue) : Prop :=
  left.2 = right.2

/-- A source-and-target branch matches both a source collection and the target coordinate. -/
def sourceTargetCollectionEquivalent
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    (collection : Finset sourceIndex)
    (left right : CategoricalKey sourceIndex sourceValue targetValue) : Prop :=
  sourceCollectionEquivalent collection left right ∧ targetEquivalent left right

/-- Source-collection matching is an equivalence relation on complete keys. -/
theorem source_collection_equivalence
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    (collection : Finset sourceIndex) :
    Equivalence
      (sourceCollectionEquivalent
        (sourceValue := sourceValue) (targetValue := targetValue) collection) := by
  constructor
  · intro key source _
    rfl
  · intro left right h source hsource
    exact (h source hsource).symm
  · intro first second third hfirst hsecond source hsource
    exact (hfirst source hsource).trans (hsecond source hsource)

/-- Target matching is an equivalence relation on complete keys. -/
theorem target_equivalence
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w} :
    Equivalence
      (targetEquivalent
        (sourceIndex := sourceIndex) (sourceValue := sourceValue)
        (targetValue := targetValue)) := by
  constructor
  · intro key
    rfl
  · intro left right h
    exact h.symm
  · intro first second third hfirst hsecond
    exact hfirst.trans hsecond

/-- Conjoining source-collection and target matching is an equivalence relation. -/
theorem source_target_collection_equivalence
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    (collection : Finset sourceIndex) :
    Equivalence
      (sourceTargetCollectionEquivalent
        (sourceValue := sourceValue) (targetValue := targetValue) collection) := by
  have hsource :=
    source_collection_equivalence
      (sourceValue := sourceValue) (targetValue := targetValue) collection
  have htarget :
      Equivalence
        (targetEquivalent
          (sourceIndex := sourceIndex) (sourceValue := sourceValue)
          (targetValue := targetValue)) :=
    target_equivalence
  constructor
  · intro key
    exact ⟨hsource.1 key, htarget.1 key⟩
  · intro left right h
    exact ⟨hsource.2 h.1, htarget.2 h.2⟩
  · intro first second third hfirst hsecond
    exact
      ⟨hsource.3 hfirst.1 hsecond.1,
        htarget.3 hfirst.2 hsecond.2⟩

/-- A branch event keyed by a source collection. -/
noncomputable def sourceBranchEvent
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collection : Finset sourceIndex)
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    Finset (CategoricalKey sourceIndex sourceValue targetValue) := by
  classical
  exact
    Finset.univ.filter fun candidate =>
      sourceCollectionEquivalent collection anchor candidate

/-- The keyed target event. -/
noncomputable def targetBranchEvent
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    Finset (CategoricalKey sourceIndex sourceValue targetValue) := by
  classical
  exact Finset.univ.filter fun candidate => targetEquivalent anchor candidate

/-- A branch event keyed by one source collection and the target. -/
noncomputable def sourceTargetBranchEvent
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collection : Finset sourceIndex)
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    Finset (CategoricalKey sourceIndex sourceValue targetValue) := by
  classical
  exact
    Finset.univ.filter fun candidate =>
      sourceTargetCollectionEquivalent collection anchor candidate

/-- A finite branch is an equivalence-class neighborhood exactly when its membership predicate is
the supplied equivalence relation. -/
def IsEquivalenceClassNeighborhood
    {key : Type x} (relation : key → key → Prop)
    (neighborhood : key → Finset key) : Prop :=
  Equivalence relation ∧
    ∀ anchor candidate, candidate ∈ neighborhood anchor ↔ relation anchor candidate

/-- A keyed event is a finite union of branchwise equivalence-class neighborhoods.  The number
of branches in this witness is `branches.card`. -/
def IsFiniteEquivalenceUnion
    {branch : Type u} {key : Type x}
    [DecidableEq key]
    (branches : Finset branch)
    (relation : branch → key → key → Prop)
    (neighborhood : branch → key → Finset key)
    (event : key → Finset key) : Prop :=
  (∀ branch ∈ branches,
      IsEquivalenceClassNeighborhood (relation branch) (neighborhood branch)) ∧
    ∀ anchor, event anchor = branches.biUnion fun branch => neighborhood branch anchor

/-- Every equivalence-class neighborhood contains its anchor. -/
theorem equivalence_class_neighborhood_anchor_mem
    {key : Type x} {relation : key → key → Prop}
    {neighborhood : key → Finset key}
    (hclass : IsEquivalenceClassNeighborhood relation neighborhood)
    (anchor : key) :
    anchor ∈ neighborhood anchor := by
  exact (hclass.2 anchor anchor).2 (hclass.1.1 anchor)

/-- Every nonempty finite union of equivalence-class neighborhoods satisfies the generic anchor
condition. -/
theorem finite_equivalence_union_anchor_mem
    {branch : Type u} {key : Type x}
    [DecidableEq branch] [DecidableEq key]
    {branches : Finset branch}
    {relation : branch → key → key → Prop}
    {neighborhood : branch → key → Finset key}
    {event : key → Finset key}
    (hcover :
      IsFiniteEquivalenceUnion branches relation neighborhood event)
    (hbranches : branches.Nonempty)
    (anchor : key) :
    anchor ∈ event anchor := by
  obtain ⟨branch, hbranch⟩ := hbranches
  rw [hcover.2 anchor]
  exact
    Finset.mem_biUnion.mpr
      ⟨branch, hbranch,
        equivalence_class_neighborhood_anchor_mem
          (hcover.1 branch hbranch) anchor⟩

/-- A source branch is exactly the equivalence class of its anchor. -/
theorem source_branch_is_equivalence_class
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collection : Finset sourceIndex) :
    IsEquivalenceClassNeighborhood
      (sourceCollectionEquivalent
        (sourceValue := sourceValue) (targetValue := targetValue) collection)
      (sourceBranchEvent collection) := by
  constructor
  · exact source_collection_equivalence collection
  · intro anchor candidate
    simp [sourceBranchEvent]

/-- The target branch is exactly the target-equivalence class of its anchor. -/
theorem target_branch_is_equivalence_class
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue] :
    IsEquivalenceClassNeighborhood
      (targetEquivalent
        (sourceIndex := sourceIndex) (sourceValue := sourceValue)
        (targetValue := targetValue))
      targetBranchEvent := by
  constructor
  · exact target_equivalence
  · intro anchor candidate
    simp [targetBranchEvent]

/-- A source-and-target branch is exactly the corresponding conjunctive equivalence class. -/
theorem source_target_branch_is_equivalence_class
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collection : Finset sourceIndex) :
    IsEquivalenceClassNeighborhood
      (sourceTargetCollectionEquivalent
        (sourceValue := sourceValue) (targetValue := targetValue) collection)
      (sourceTargetBranchEvent collection) := by
  constructor
  · exact source_target_collection_equivalence collection
  · intro anchor candidate
    simp [sourceTargetBranchEvent]

/-- Every source branch contains its keyed anchor. -/
theorem source_branch_anchor_mem
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collection : Finset sourceIndex)
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    anchor ∈ sourceBranchEvent collection anchor := by
  simp [sourceBranchEvent, sourceCollectionEquivalent]

/-- Every target branch contains its keyed anchor. -/
theorem target_branch_anchor_mem
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    anchor ∈ targetBranchEvent anchor := by
  simp [targetBranchEvent, targetEquivalent]

/-- Every source-and-target branch contains its keyed anchor. -/
theorem source_target_branch_anchor_mem
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collection : Finset sourceIndex)
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    anchor ∈ sourceTargetBranchEvent collection anchor := by
  simp [
    sourceTargetBranchEvent,
    sourceTargetCollectionEquivalent,
    sourceCollectionEquivalent,
    targetEquivalent
  ]

/-- The categorical shared-exclusions source event is a finite union over source-collection
branches. -/
noncomputable def sxSourceEvent
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex))
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    Finset (CategoricalKey sourceIndex sourceValue targetValue) :=
  collections.biUnion fun collection => sourceBranchEvent collection anchor

/-- The target-restricted source event is a union of source-and-target branches. -/
noncomputable def sxTargetRestrictedEvent
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex))
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    Finset (CategoricalKey sourceIndex sourceValue targetValue) :=
  collections.biUnion fun collection => sourceTargetBranchEvent collection anchor

/-- The source event has an equivalence-neighborhood cover with exactly
`collections.card` indexed branches. -/
theorem sx_source_event_equivalence_union
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex)) :
    IsFiniteEquivalenceUnion
      collections
      (fun collection =>
        sourceCollectionEquivalent
          (sourceValue := sourceValue) (targetValue := targetValue) collection)
      sourceBranchEvent
      (sxSourceEvent collections) := by
  constructor
  · intro collection _
    exact source_branch_is_equivalence_class collection
  · intro anchor
    rfl

/-- The target-restricted event has an equivalence-neighborhood cover with exactly
`collections.card` indexed branches. -/
theorem sx_target_restricted_event_equivalence_union
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex)) :
    IsFiniteEquivalenceUnion
      collections
      (fun collection =>
        sourceTargetCollectionEquivalent
          (sourceValue := sourceValue) (targetValue := targetValue) collection)
      sourceTargetBranchEvent
      (sxTargetRestrictedEvent collections) := by
  constructor
  · intro collection _
    exact source_target_branch_is_equivalence_class collection
  · intro anchor
    rfl

/-- The target event is a one-branch equivalence-neighborhood union. -/
theorem sx_target_event_equivalence_union
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue] :
    IsFiniteEquivalenceUnion
      ({()} : Finset Unit)
      (fun _ =>
        targetEquivalent
          (sourceIndex := sourceIndex) (sourceValue := sourceValue)
          (targetValue := targetValue))
      (fun _ => targetBranchEvent)
      targetBranchEvent := by
  constructor
  · intro branch _
    exact target_branch_is_equivalence_class
  · intro anchor
    simp

/-- A nonempty source event contains its keyed anchor. -/
theorem sx_source_event_anchor_mem
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    {collections : Finset (Finset sourceIndex)}
    (hcollections : collections.Nonempty)
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    anchor ∈ sxSourceEvent collections anchor := by
  obtain ⟨collection, hcollection⟩ := hcollections
  exact Finset.mem_biUnion.mpr
    ⟨collection, hcollection, source_branch_anchor_mem collection anchor⟩

/-- A nonempty target-restricted event contains its keyed anchor. -/
theorem sx_target_restricted_event_anchor_mem
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    {collections : Finset (Finset sourceIndex)}
    (hcollections : collections.Nonempty)
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    anchor ∈ sxTargetRestrictedEvent collections anchor := by
  obtain ⟨collection, hcollection⟩ := hcollections
  exact Finset.mem_biUnion.mpr
    ⟨collection, hcollection, source_target_branch_anchor_mem collection anchor⟩

/-- A source-and-target branch equals its source branch intersected with the target branch. -/
theorem source_target_branch_event_eq_inter
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collection : Finset sourceIndex)
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    sourceTargetBranchEvent collection anchor =
      sourceBranchEvent collection anchor ∩ targetBranchEvent anchor := by
  ext candidate
  simp [
    sourceTargetBranchEvent,
    sourceBranchEvent,
    targetBranchEvent,
    sourceTargetCollectionEquivalent
  ]

/-- The target-restricted source event equals the source event intersected with the target
event. -/
theorem sx_target_restricted_event_eq_inter
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex))
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    sxTargetRestrictedEvent collections anchor =
      sxSourceEvent collections anchor ∩ targetBranchEvent anchor := by
  ext candidate
  simp only [
    sxTargetRestrictedEvent,
    sxSourceEvent,
    Finset.mem_biUnion,
    sourceTargetBranchEvent,
    sourceBranchEvent,
    targetBranchEvent,
    Finset.mem_filter,
    Finset.mem_univ,
    true_and,
    sourceTargetCollectionEquivalent,
    Finset.mem_inter
  ]
  constructor
  · rintro ⟨collection, hcollection, hsource, htarget⟩
    exact ⟨⟨collection, hcollection, hsource⟩, htarget⟩
  · rintro ⟨⟨collection, hcollection, hsource⟩, htarget⟩
    exact ⟨collection, hcollection, hsource, htarget⟩

/-- The complete keyed event triple used by categorical shared exclusions. -/
structure SxKeyedEvents (key : Type x) where
  source : Finset key
  target : Finset key
  targetRestricted : Finset key
deriving DecidableEq

/-- The complete categorical shared-exclusions event map on the fixed ambient key type. -/
noncomputable def sxKeyedEvents
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex))
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    SxKeyedEvents (CategoricalKey sourceIndex sourceValue targetValue) where
  source := sxSourceEvent collections anchor
  target := targetBranchEvent anchor
  targetRestricted := sxTargetRestrictedEvent collections anchor

/-- A law-indexed view of the event map.  The law parameter is intentionally absent from every
event predicate. -/
noncomputable def sxKeyedEventsUnderLaw
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (_law : CategoricalKey sourceIndex sourceValue targetValue → ℝ)
    (collections : Finset (Finset sourceIndex))
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    SxKeyedEvents (CategoricalKey sourceIndex sourceValue targetValue) :=
  sxKeyedEvents collections anchor

/-- Two laws on the same complete ambient key type induce exactly the same keyed event map. -/
theorem sx_keyed_events_fixed_across_laws
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (leftLaw rightLaw : CategoricalKey sourceIndex sourceValue targetValue → ℝ)
    (collections : Finset (Finset sourceIndex))
    (anchor : CategoricalKey sourceIndex sourceValue targetValue) :
    sxKeyedEventsUnderLaw leftLaw collections anchor =
      sxKeyedEventsUnderLaw rightLaw collections anchor := by
  rfl

/-- A finite event mass evaluated under a real mass vector. -/
def finiteEventMass
    {key : Type x} (mass : key → ℝ) (event : Finset key) : ℝ :=
  ∑ candidate ∈ event, mass candidate

/-- Positive mass at an anchor makes the source event mass positive. -/
theorem sx_source_event_mass_positive
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    {collections : Finset (Finset sourceIndex)}
    (hcollections : collections.Nonempty)
    (mass : CategoricalKey sourceIndex sourceValue targetValue → ℝ)
    (hmassNonnegative : ∀ key, 0 ≤ mass key)
    (anchor : CategoricalKey sourceIndex sourceValue targetValue)
    (hanchorPositive : 0 < mass anchor) :
    0 < finiteEventMass mass (sxSourceEvent collections anchor) := by
  exact
    event_mass_positive_of_mem
      hmassNonnegative
      (sx_source_event_anchor_mem hcollections anchor)
      hanchorPositive

/-- Positive mass at an anchor makes the target event mass positive. -/
theorem sx_target_event_mass_positive
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (mass : CategoricalKey sourceIndex sourceValue targetValue → ℝ)
    (hmassNonnegative : ∀ key, 0 ≤ mass key)
    (anchor : CategoricalKey sourceIndex sourceValue targetValue)
    (hanchorPositive : 0 < mass anchor) :
    0 < finiteEventMass mass (targetBranchEvent anchor) := by
  exact
    event_mass_positive_of_mem
      hmassNonnegative
      (target_branch_anchor_mem anchor)
      hanchorPositive

/-- Positive mass at an anchor makes the target-restricted event mass positive. -/
theorem sx_target_restricted_event_mass_positive
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    {collections : Finset (Finset sourceIndex)}
    (hcollections : collections.Nonempty)
    (mass : CategoricalKey sourceIndex sourceValue targetValue → ℝ)
    (hmassNonnegative : ∀ key, 0 ≤ mass key)
    (anchor : CategoricalKey sourceIndex sourceValue targetValue)
    (hanchorPositive : 0 < mass anchor) :
    0 < finiteEventMass mass (sxTargetRestrictedEvent collections anchor) := by
  exact
    event_mass_positive_of_mem
      hmassNonnegative
      (sx_target_restricted_event_anchor_mem hcollections anchor)
      hanchorPositive

end PidFiniteConvergence
