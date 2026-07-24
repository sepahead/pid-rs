import PidFiniteConvergence.SxEventBridge

/-!
# Finite equivalence-union fractional-cover bound

For a finite key space, nonnegative overlap vector `r`, nonnegative residual vector `d`, and a
keyed neighborhood map `N`, this module defines the support-restricted overlap load

`T_N(r,d) = ∑ x with 0 < r x, r x * d(N x) / r(N x)`.

It proves that one equivalence-class neighborhood has load at most `∑ d`, then transfers that
bound to any finite union of `J` equivalence-class branches:

`T_N(r,d) ≤ J * ∑ d`.

The final eta form assumes `∑ d = eta` and yields `T_N(r,d) ≤ J * eta`.  Denominator positivity
is proved for every positive-overlap anchor whenever the branch cover is nonempty.  The empty-cover
case is handled separately and has zero load, so the final generic theorem needs no nonemptiness
assumption.  No probability normalization is required: nonnegativity and the stated residual
total are the complete analytic hypotheses.

Concrete corollaries instantiate the result for the heterogeneous finite-alphabet shared-
exclusions source event, target-restricted event, and target event from `SxEventBridge`.

This module proves a deterministic exact-real finite-sum inequality.  It does not yet formalize
logarithmic local-information continuity, population-to-empirical sampling, averaged SxPID
cumulatives, Möbius inversion, or refinement to Rust floating-point execution.
-/

set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators
namespace PidFiniteConvergence

universe u v w

variable {key : Type u}

/-- The finite set of keys carrying strictly positive overlap mass. -/
noncomputable def positiveMassSupport [Fintype key] (mass : key → ℝ) : Finset key :=
  Finset.univ.filter fun x => 0 < mass x

/-- The total fractional weight assigned to one candidate by all positive-overlap anchors in a
single keyed neighborhood map. -/
noncomputable def equivalenceClassCoverWeight
    [Fintype key] [DecidableEq key]
    (overlap : key → ℝ) (neighborhood : key → Finset key) (candidate : key) : ℝ :=
  ∑ anchor ∈ positiveMassSupport overlap,
    if candidate ∈ neighborhood anchor then
      overlap anchor / finiteEventMass overlap (neighborhood anchor)
    else 0

/-- The support-restricted overlap load `T_N(r,d)`.  Division is totalized by Lean; later
theorems prove every denominator used by a nonempty equivalence cover is strictly positive. -/
noncomputable def equivalenceNeighborhoodOverlapLoad
    [Fintype key] [DecidableEq key]
    (overlap residual : key → ℝ) (neighborhood : key → Finset key) : ℝ :=
  ∑ anchor ∈ positiveMassSupport overlap,
    overlap anchor *
      (finiteEventMass residual (neighborhood anchor) /
        finiteEventMass overlap (neighborhood anchor))

/-- Related anchors induce the same equivalence-class neighborhood. -/
theorem equivalence_class_neighborhood_eq_of_related
    [DecidableEq key]
    {relation : key → key → Prop} {neighborhood : key → Finset key}
    (hclass : IsEquivalenceClassNeighborhood relation neighborhood)
    {left right : key} (hrelated : relation left right) :
    neighborhood left = neighborhood right := by
  ext candidate
  rw [hclass.2 left candidate, hclass.2 right candidate]
  constructor
  · intro hleft
    exact hclass.1.3 (hclass.1.2 hrelated) hleft
  · intro hright
    exact hclass.1.3 hrelated hright

/-- A positive-overlap anchor gives a strictly positive class denominator. -/
theorem equivalence_class_event_mass_positive_on_support
    [Fintype key] [DecidableEq key]
    (overlap : key → ℝ) (neighborhood : key → Finset key)
    {relation : key → key → Prop}
    (hclass : IsEquivalenceClassNeighborhood relation neighborhood)
    (hoverlap : ∀ x, 0 ≤ overlap x)
    {anchor : key} (hanchor : anchor ∈ positiveMassSupport overlap) :
    0 < finiteEventMass overlap (neighborhood anchor) := by
  exact
    event_mass_positive_of_mem hoverlap
      (equivalence_class_neighborhood_anchor_mem hclass anchor)
      (Finset.mem_filter.1 hanchor).2

/-- Filtering a nonnegative event mass to its strictly positive cells does not change its sum. -/
theorem positive_support_filter_event_sum_eq_event_mass
    [Fintype key] [DecidableEq key]
    (mass : key → ℝ) (event : Finset key)
    (hmass : ∀ x, 0 ≤ mass x) :
    (∑ x ∈ event.filter fun x => 0 < mass x, mass x) =
      finiteEventMass mass event := by
  apply Finset.sum_subset (Finset.filter_subset _ _)
  intro x hxevent hxfilter
  have hnotPositive : ¬ 0 < mass x := by
    intro hpositive
    exact hxfilter (by simpa using ⟨hxevent, hpositive⟩)
  exact le_antisymm (le_of_not_gt hnotPositive) (hmass x)

/-- One equivalence class has fractional cover weight at most one at every candidate. -/
theorem equivalence_class_cover_weight_le_one
    [Fintype key] [DecidableEq key]
    (overlap : key → ℝ) (neighborhood : key → Finset key)
    {relation : key → key → Prop}
    (hclass : IsEquivalenceClassNeighborhood relation neighborhood)
    (hoverlap : ∀ x, 0 ≤ overlap x)
    (candidate : key) :
    equivalenceClassCoverWeight overlap neighborhood candidate ≤ 1 := by
  let selected := (neighborhood candidate).filter fun x => 0 < overlap x
  have hselected :
      (positiveMassSupport overlap).filter
          (fun anchor => candidate ∈ neighborhood anchor) = selected := by
    ext anchor
    simp only [Finset.mem_filter, positiveMassSupport, Finset.mem_univ, true_and, selected]
    constructor
    · rintro ⟨hpositive, hcandidate⟩
      exact
        ⟨(hclass.2 candidate anchor).2
            (hclass.1.2 ((hclass.2 anchor candidate).1 hcandidate)),
          hpositive⟩
    · rintro ⟨hrelated, hpositive⟩
      exact
        ⟨hpositive,
          (hclass.2 anchor candidate).2
            (hclass.1.2 ((hclass.2 candidate anchor).1 hrelated))⟩
  rw [equivalenceClassCoverWeight]
  rw [← Finset.sum_filter]
  rw [hselected]
  have hneighborhood : ∀ anchor ∈ selected,
      neighborhood anchor = neighborhood candidate := by
    intro anchor hanchor
    have hrelated : relation candidate anchor :=
      (hclass.2 candidate anchor).1 ((Finset.mem_filter.1 hanchor).1)
    exact equivalence_class_neighborhood_eq_of_related hclass (hclass.1.2 hrelated)
  calc
    (∑ anchor ∈ selected,
        overlap anchor / finiteEventMass overlap (neighborhood anchor)) =
      ∑ anchor ∈ selected,
        overlap anchor / finiteEventMass overlap (neighborhood candidate) := by
      apply Finset.sum_congr rfl
      intro anchor hanchor
      rw [hneighborhood anchor hanchor]
    _ =
      (∑ anchor ∈ selected, overlap anchor) /
        finiteEventMass overlap (neighborhood candidate) := by
      simp only [div_eq_mul_inv]
      rw [Finset.sum_mul]
    _ ≤ 1 := by
      rw [positive_support_filter_event_sum_eq_event_mass overlap
        (neighborhood candidate) hoverlap]
      by_cases hzero : finiteEventMass overlap (neighborhood candidate) = 0
      · simp [hzero]
      · simp [hzero]

/-- Finite Fubini/regrouping identity: a neighborhood load is the residual mass weighted by its
candidatewise fractional-cover coefficient. -/
theorem equivalence_neighborhood_overlap_load_eq_cover_sum
    [Fintype key] [DecidableEq key]
    (overlap residual : key → ℝ) (neighborhood : key → Finset key) :
    equivalenceNeighborhoodOverlapLoad overlap residual neighborhood =
      ∑ candidate, residual candidate *
        equivalenceClassCoverWeight overlap neighborhood candidate := by
  classical
  rw [equivalenceNeighborhoodOverlapLoad]
  simp only [equivalenceClassCoverWeight]
  have hanchor :
      ∀ anchor,
        overlap anchor *
            (finiteEventMass residual (neighborhood anchor) /
              finiteEventMass overlap (neighborhood anchor)) =
          ∑ candidate,
            residual candidate *
              (if candidate ∈ neighborhood anchor then
                overlap anchor / finiteEventMass overlap (neighborhood anchor)
              else 0) := by
    intro anchor
    rw [finiteEventMass]
    calc
      overlap anchor *
          ((∑ candidate ∈ neighborhood anchor, residual candidate) /
            finiteEventMass overlap (neighborhood anchor)) =
        ∑ candidate ∈ neighborhood anchor,
          residual candidate *
            (overlap anchor / finiteEventMass overlap (neighborhood anchor)) := by
        rw [← Finset.sum_mul]
        ring
      _ =
        ∑ candidate,
          residual candidate *
            (if candidate ∈ neighborhood anchor then
              overlap anchor / finiteEventMass overlap (neighborhood anchor)
            else 0) := by
        simp only [mul_ite, mul_zero]
        rw [← Finset.sum_filter]
        apply Finset.sum_congr
        · ext candidate
          simp
        · intro candidate _
          rfl
  simp_rw [hanchor]
  rw [Finset.sum_comm]
  simp only [Finset.mul_sum]

/-- The overlap load of one equivalence-class neighborhood is at most the total residual mass. -/
theorem equivalence_class_overlap_load_le_total
    [Fintype key] [DecidableEq key]
    (overlap residual : key → ℝ) (neighborhood : key → Finset key)
    {relation : key → key → Prop}
    (hclass : IsEquivalenceClassNeighborhood relation neighborhood)
    (hoverlap : ∀ x, 0 ≤ overlap x)
    (hresidual : ∀ x, 0 ≤ residual x) :
    equivalenceNeighborhoodOverlapLoad overlap residual neighborhood ≤
      finiteEventMass residual Finset.univ := by
  rw [equivalence_neighborhood_overlap_load_eq_cover_sum]
  rw [finiteEventMass]
  apply Finset.sum_le_sum
  intro candidate _
  calc
    residual candidate *
        equivalenceClassCoverWeight overlap neighborhood candidate ≤
      residual candidate * 1 := by
        exact
          mul_le_mul_of_nonneg_left
            (equivalence_class_cover_weight_le_one
              overlap neighborhood hclass hoverlap candidate)
            (hresidual candidate)
    _ = residual candidate := by ring

/-- A finite event has nonnegative mass under a pointwise nonnegative vector. -/
theorem finite_event_mass_nonnegative
    [DecidableEq key]
    (mass : key → ℝ) (event : Finset key)
    (hmass : ∀ x, 0 ≤ mass x) :
    0 ≤ finiteEventMass mass event := by
  exact Finset.sum_nonneg fun x _ => hmass x

/-- Every support-restricted neighborhood load is nonnegative when both input vectors are
pointwise nonnegative; no equivalence-cover premise is needed. -/
theorem equivalence_neighborhood_overlap_load_nonnegative
    [Fintype key] [DecidableEq key]
    (overlap residual : key → ℝ) (neighborhood : key → Finset key)
    (hoverlap : ∀ x, 0 ≤ overlap x)
    (hresidual : ∀ x, 0 ≤ residual x) :
    0 ≤ equivalenceNeighborhoodOverlapLoad overlap residual neighborhood := by
  rw [equivalenceNeighborhoodOverlapLoad]
  apply Finset.sum_nonneg
  intro anchor _
  exact
    mul_nonneg (hoverlap anchor)
      (div_nonneg
        (finite_event_mass_nonnegative
          residual (neighborhood anchor) hresidual)
        (finite_event_mass_nonnegative
          overlap (neighborhood anchor) hoverlap))

/-- Finite event mass is monotone under inclusion for pointwise nonnegative vectors. -/
theorem finite_event_mass_mono
    [DecidableEq key]
    (mass : key → ℝ) {left right : Finset key}
    (hmass : ∀ x, 0 ≤ mass x)
    (hsubset : left ⊆ right) :
    finiteEventMass mass left ≤ finiteEventMass mass right := by
  exact
    Finset.sum_le_sum_of_subset_of_nonneg hsubset
      (fun x _ _ => hmass x)

/-- The mass of a union is at most the sum of the two event masses. -/
theorem finite_event_mass_union_le
    [DecidableEq key]
    (mass : key → ℝ) (left right : Finset key)
    (hmass : ∀ x, 0 ≤ mass x) :
    finiteEventMass mass (left ∪ right) ≤
      finiteEventMass mass left + finiteEventMass mass right := by
  have hintersection :
      0 ≤ finiteEventMass mass (left ∩ right) :=
    finite_event_mass_nonnegative mass (left ∩ right) hmass
  calc
    finiteEventMass mass (left ∪ right) ≤
        finiteEventMass mass (left ∪ right) +
          finiteEventMass mass (left ∩ right) :=
      le_add_of_nonneg_right hintersection
    _ = finiteEventMass mass left + finiteEventMass mass right := by
      exact Finset.sum_union_inter

/-- The mass of a finite union is at most the sum of its branch masses, with repeated cells
counted separately on the right. -/
theorem finite_event_mass_biUnion_le_sum
    {branch : Type v}
    [DecidableEq branch] [DecidableEq key]
    (mass : key → ℝ) (branches : Finset branch)
    (events : branch → Finset key)
    (hmass : ∀ x, 0 ≤ mass x) :
    finiteEventMass mass (branches.biUnion events) ≤
      ∑ branch ∈ branches, finiteEventMass mass (events branch) := by
  induction branches using Finset.induction_on with
  | empty =>
      simp [finiteEventMass]
  | @insert branch branches hnotMem ih =>
      rw [Finset.biUnion_insert]
      rw [Finset.sum_insert hnotMem]
      exact
        (finite_event_mass_union_le
          mass (events branch) (branches.biUnion events) hmass).trans
          (add_le_add le_rfl ih)

/-- In a nonempty finite equivalence union, every positive-overlap anchor gives a strictly
positive union denominator. -/
theorem finite_equivalence_union_event_mass_positive_on_support
    {branch : Type v}
    [Fintype key] [DecidableEq branch] [DecidableEq key]
    (overlap : key → ℝ)
    {branches : Finset branch}
    {relation : branch → key → key → Prop}
    {neighborhood : branch → key → Finset key}
    {event : key → Finset key}
    (hcover : IsFiniteEquivalenceUnion branches relation neighborhood event)
    (hbranches : branches.Nonempty)
    (hoverlap : ∀ x, 0 ≤ overlap x)
    {anchor : key} (hanchor : anchor ∈ positiveMassSupport overlap) :
    0 < finiteEventMass overlap (event anchor) := by
  exact
    event_mass_positive_of_mem hoverlap
      (finite_equivalence_union_anchor_mem hcover hbranches anchor)
      (Finset.mem_filter.1 hanchor).2

/-- At a positive-overlap anchor, the residual/overlap ratio of a nonempty branch union is at most
the sum of its branchwise ratios. -/
theorem finite_equivalence_union_ratio_le_branch_sum
    {branch : Type v}
    [Fintype key] [DecidableEq branch] [DecidableEq key]
    (overlap residual : key → ℝ)
    {branches : Finset branch}
    {relation : branch → key → key → Prop}
    {neighborhood : branch → key → Finset key}
    {event : key → Finset key}
    (hcover : IsFiniteEquivalenceUnion branches relation neighborhood event)
    (hbranches : branches.Nonempty)
    (hoverlap : ∀ x, 0 ≤ overlap x)
    (hresidual : ∀ x, 0 ≤ residual x)
    {anchor : key} (hanchor : anchor ∈ positiveMassSupport overlap) :
    finiteEventMass residual (event anchor) /
        finiteEventMass overlap (event anchor) ≤
      ∑ branch ∈ branches,
        finiteEventMass residual (neighborhood branch anchor) /
          finiteEventMass overlap (neighborhood branch anchor) := by
  have heventPositive :
      0 < finiteEventMass overlap (event anchor) :=
    finite_equivalence_union_event_mass_positive_on_support
      overlap hcover hbranches hoverlap hanchor
  have hbranchPositive :
      ∀ branch ∈ branches,
        0 < finiteEventMass overlap (neighborhood branch anchor) := by
    intro branch hbranch
    exact
      equivalence_class_event_mass_positive_on_support
        overlap (neighborhood branch) (hcover.1 branch hbranch)
        hoverlap hanchor
  have hbranchSubset :
      ∀ branch ∈ branches, neighborhood branch anchor ⊆ event anchor := by
    intro branch hbranch
    rw [hcover.2 anchor]
    exact Finset.subset_biUnion_of_mem (fun index => neighborhood index anchor) hbranch
  have hbranchDenominator :
      ∀ branch ∈ branches,
        finiteEventMass overlap (neighborhood branch anchor) ≤
          finiteEventMass overlap (event anchor) := by
    intro branch hbranch
    exact finite_event_mass_mono overlap hoverlap (hbranchSubset branch hbranch)
  have hunionNumerator :
      finiteEventMass residual (event anchor) ≤
        ∑ branch ∈ branches,
          finiteEventMass residual (neighborhood branch anchor) := by
    rw [hcover.2 anchor]
    exact
      finite_event_mass_biUnion_le_sum
        residual branches (fun branch => neighborhood branch anchor) hresidual
  calc
    finiteEventMass residual (event anchor) /
        finiteEventMass overlap (event anchor) ≤
      (∑ branch ∈ branches,
          finiteEventMass residual (neighborhood branch anchor)) /
        finiteEventMass overlap (event anchor) := by
      exact div_le_div_of_nonneg_right hunionNumerator heventPositive.le
    _ =
      ∑ branch ∈ branches,
        finiteEventMass residual (neighborhood branch anchor) /
          finiteEventMass overlap (event anchor) := by
      simp only [div_eq_mul_inv]
      rw [Finset.sum_mul]
    _ ≤
      ∑ branch ∈ branches,
        finiteEventMass residual (neighborhood branch anchor) /
          finiteEventMass overlap (neighborhood branch anchor) := by
      apply Finset.sum_le_sum
      intro branch hbranch
      exact
        div_le_div_of_nonneg_left
          (finite_event_mass_nonnegative
            residual (neighborhood branch anchor) hresidual)
          (hbranchPositive branch hbranch)
          (hbranchDenominator branch hbranch)

/-- A nonempty union of `J` equivalence-class branches has load at most `J` times total residual
mass. -/
theorem finite_equivalence_union_overlap_load_le_of_nonempty
    {branch : Type v}
    [Fintype key] [DecidableEq branch] [DecidableEq key]
    (overlap residual : key → ℝ)
    {branches : Finset branch}
    {relation : branch → key → key → Prop}
    {neighborhood : branch → key → Finset key}
    {event : key → Finset key}
    (hcover : IsFiniteEquivalenceUnion branches relation neighborhood event)
    (hbranches : branches.Nonempty)
    (hoverlap : ∀ x, 0 ≤ overlap x)
    (hresidual : ∀ x, 0 ≤ residual x) :
    equivalenceNeighborhoodOverlapLoad overlap residual event ≤
      branches.card * finiteEventMass residual Finset.univ := by
  rw [equivalenceNeighborhoodOverlapLoad]
  calc
    (∑ anchor ∈ positiveMassSupport overlap,
        overlap anchor *
          (finiteEventMass residual (event anchor) /
            finiteEventMass overlap (event anchor))) ≤
      ∑ anchor ∈ positiveMassSupport overlap,
        overlap anchor *
          (∑ branch ∈ branches,
            finiteEventMass residual (neighborhood branch anchor) /
              finiteEventMass overlap (neighborhood branch anchor)) := by
      apply Finset.sum_le_sum
      intro anchor hanchor
      exact
        mul_le_mul_of_nonneg_left
          (finite_equivalence_union_ratio_le_branch_sum
            overlap residual hcover hbranches hoverlap hresidual hanchor)
          (hoverlap anchor)
    _ =
      ∑ branch ∈ branches,
        equivalenceNeighborhoodOverlapLoad overlap residual
          (neighborhood branch) := by
      simp_rw [Finset.mul_sum]
      rw [Finset.sum_comm]
      rfl
    _ ≤
      ∑ branch ∈ branches,
        finiteEventMass residual Finset.univ := by
      apply Finset.sum_le_sum
      intro branch hbranch
      exact
        equivalence_class_overlap_load_le_total
          overlap residual (neighborhood branch)
          (hcover.1 branch hbranch) hoverlap hresidual
    _ = branches.card * finiteEventMass residual Finset.univ := by
      simp

/-- Any finite equivalence union, including the empty cover, has load at most its branch count
times total residual mass. -/
theorem finite_equivalence_union_overlap_load_le
    {branch : Type v}
    [Fintype key] [DecidableEq branch] [DecidableEq key]
    (overlap residual : key → ℝ)
    {branches : Finset branch}
    {relation : branch → key → key → Prop}
    {neighborhood : branch → key → Finset key}
    {event : key → Finset key}
    (hcover : IsFiniteEquivalenceUnion branches relation neighborhood event)
    (hoverlap : ∀ x, 0 ≤ overlap x)
    (hresidual : ∀ x, 0 ≤ residual x) :
    equivalenceNeighborhoodOverlapLoad overlap residual event ≤
      branches.card * finiteEventMass residual Finset.univ := by
  by_cases hbranches : branches.Nonempty
  · exact
      finite_equivalence_union_overlap_load_le_of_nonempty
        overlap residual hcover hbranches hoverlap hresidual
  · have hbranchesEmpty : branches = ∅ :=
      Finset.not_nonempty_iff_eq_empty.mp hbranches
    have heventEmpty : ∀ anchor, event anchor = ∅ := by
      intro anchor
      rw [hcover.2 anchor, hbranchesEmpty]
      simp
    rw [equivalenceNeighborhoodOverlapLoad]
    simp_rw [heventEmpty]
    simp [finiteEventMass, hbranchesEmpty]

/-- Fractional-cover theorem in the named-total form:
`T_N(r,d) ≤ branches.card * eta` whenever `∑ d = eta`. -/
theorem finite_equivalence_union_fractional_cover_bound
    {branch : Type v}
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
  rw [← hresidualTotal]
  exact
    finite_equivalence_union_overlap_load_le
      overlap residual hcover hoverlap hresidual

/-- Closed interval form of the fractional-cover theorem. -/
theorem finite_equivalence_union_fractional_cover_bounds
    {branch : Type v}
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
    0 ≤ equivalenceNeighborhoodOverlapLoad overlap residual event ∧
      equivalenceNeighborhoodOverlapLoad overlap residual event ≤
        branches.card * eta := by
  exact
    ⟨equivalence_neighborhood_overlap_load_nonnegative
        overlap residual event hoverlap hresidual,
      finite_equivalence_union_fractional_cover_bound
        overlap residual hcover hoverlap hresidual hresidualTotal⟩

/-- Shared-exclusions source-event instance of the fractional-cover theorem. -/
theorem sx_source_fractional_cover_bound
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex))
    (overlap residual :
      CategoricalKey sourceIndex sourceValue targetValue → ℝ)
    (hoverlap : ∀ key, 0 ≤ overlap key)
    (hresidual : ∀ key, 0 ≤ residual key)
    {eta : ℝ}
    (hresidualTotal : finiteEventMass residual Finset.univ = eta) :
    equivalenceNeighborhoodOverlapLoad overlap residual
        (sxSourceEvent collections) ≤
      collections.card * eta := by
  exact
    finite_equivalence_union_fractional_cover_bound
      overlap residual
      (sx_source_event_equivalence_union collections)
      hoverlap hresidual hresidualTotal

/-- Shared-exclusions target-restricted-event instance of the fractional-cover theorem. -/
theorem sx_target_restricted_fractional_cover_bound
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex))
    (overlap residual :
      CategoricalKey sourceIndex sourceValue targetValue → ℝ)
    (hoverlap : ∀ key, 0 ≤ overlap key)
    (hresidual : ∀ key, 0 ≤ residual key)
    {eta : ℝ}
    (hresidualTotal : finiteEventMass residual Finset.univ = eta) :
    equivalenceNeighborhoodOverlapLoad overlap residual
        (sxTargetRestrictedEvent collections) ≤
      collections.card * eta := by
  exact
    finite_equivalence_union_fractional_cover_bound
      overlap residual
      (sx_target_restricted_event_equivalence_union collections)
      hoverlap hresidual hresidualTotal

/-- The one-class keyed target event has overlap load at most `eta`. -/
theorem sx_target_fractional_cover_bound
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (overlap residual :
      CategoricalKey sourceIndex sourceValue targetValue → ℝ)
    (hoverlap : ∀ key, 0 ≤ overlap key)
    (hresidual : ∀ key, 0 ≤ residual key)
    {eta : ℝ}
    (hresidualTotal : finiteEventMass residual Finset.univ = eta) :
    equivalenceNeighborhoodOverlapLoad overlap residual targetBranchEvent ≤
      eta := by
  calc
    equivalenceNeighborhoodOverlapLoad overlap residual targetBranchEvent ≤
      finiteEventMass residual Finset.univ :=
        equivalence_class_overlap_load_le_total
          overlap residual targetBranchEvent target_branch_is_equivalence_class
          hoverlap hresidual
    _ = eta := hresidualTotal

end PidFiniteConvergence
