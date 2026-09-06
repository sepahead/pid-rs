import Contract
import Mathlib.Tactic.FinCases

/-! Reviewer finite controls. These declarations are not candidate exports. -/
set_option autoImplicit false
set_option warningAsError true
namespace PidSxDnfOrderJudgeControls
open PidSxDnfOrderContract PidFiniteConvergence

def either : Finset (Finset (Fin 3)) := {{0}, {1}}
def both : Finset (Finset (Fin 3)) := {{0, 1}}
def only0 : Finset (Finset (Fin 3)) := {{0}}
def only1 : Finset (Finset (Fin 3)) := {{1}}
def p100 : Fin 3 → Bool := fun i => decide (i = 0)
def p010 : Fin 3 → Bool := fun i => decide (i = 1)

universe u

theorem p01_general (S : Type u) (alpha : Finset (Finset S)) :
    RedundancyLE alpha alpha ∧ ∀ e, DNF alpha e → DNF alpha e := by
  exact ⟨fun b hb => ⟨b, hb, fun _ hi => hi⟩, fun _ h => h⟩

theorem p02_truth_table :
    ¬ DNF either (fun _ => false) ∧ ¬ DNF both (fun _ => false) ∧
    DNF either p100 ∧ ¬ DNF both p100 ∧
    DNF either p010 ∧ ¬ DNF both p010 ∧
    DNF either (fun i => decide (i = 0 ∨ i = 1)) ∧
    DNF both (fun i => decide (i = 0 ∨ i = 1)) := by
  simp only [DNF]
  decide +kernel

theorem p01_reflexive : RedundancyLE either either := by simp only [RedundancyLE]; decide +kernel

theorem p02_direction : RedundancyLE either both ∧ ¬ RedundancyLE both either ∧
    DNF either p100 ∧ ¬ DNF both p100 := by simp only [RedundancyLE, DNF]; decide +kernel

theorem p03_empty_family : ¬ DNF (∅ : Finset (Finset (Fin 3))) p100 := by simp only [DNF]; decide +kernel

theorem p04_empty_branch : DNF ({∅} : Finset (Finset (Fin 3))) (fun _ => false) := by simp only [DNF]; decide +kernel

theorem p05_empty_index : ¬ DNF (∅ : Finset (Finset (Fin 0))) (fun _ => false) ∧
    DNF ({∅} : Finset (Finset (Fin 0))) (fun _ => false) := by simp only [DNF]; decide +kernel

def Heterogeneous : Fin 2 → Type := fun i => if i = 0 then Unit else Bool
instance (i : Fin 2) : Fintype (Heterogeneous i) := by unfold Heterogeneous; split <;> infer_instance
instance (i : Fin 2) : DecidableEq (Heterogeneous i) := by unfold Heterogeneous; split <;> infer_instance

theorem p06_dependent_key : Nonempty (CategoricalKey (Fin 2) Heterogeneous Bool) := by
  refine ⟨(fun i => ?_, false)⟩
  unfold Heterogeneous
  split
  · exact ()
  · exact false

def x : CategoricalKey (Fin 3) (fun _ => Bool) Bool := (fun _ => false, false)
def changedTarget : CategoricalKey (Fin 3) (fun _ => Bool) Bool := (fun _ => false, true)
def noSourceMatch : CategoricalKey (Fin 3) (fun _ => Bool) Bool := (fun _ => true, false)

theorem p07_source_ignores_target : changedTarget ∈ sxSourceEvent only0 x ∧
    changedTarget ∉ sxTargetRestrictedEvent only0 x := by
  simp [changedTarget, x, only0, sxSourceEvent, sxTargetRestrictedEvent,
    sourceBranchEvent, sourceTargetBranchEvent, sourceCollectionEquivalent,
    sourceTargetCollectionEquivalent, targetEquivalent]

theorem p08_boolean_alternatives (e : Fin 3 → Bool) :
    EqualityPattern x (fun i => !(e i), false) = e := by
  funext i
  cases h : e i <;> simp [EqualityPattern, x, h]

theorem p09_singleton_collision :
    sxSourceEvent only0 singletonAnchor = sxSourceEvent only1 singletonAnchor ∧
    ¬ RedundancyLE only0 only1 ∧ ¬ RedundancyLE only1 only0 := by
  refine ⟨?_, by simp only [RedundancyLE]; decide +kernel, by simp only [RedundancyLE]; decide +kernel⟩
  ext y
  simp [sxSourceEvent, sourceBranchEvent, sourceCollectionEquivalent, only0, only1, singletonAnchor]

theorem p10_diagonal :
    (∀ y ∈ binaryDiagonal,
      y ∈ sxSourceEvent only0 binaryAnchor ↔ y ∈ sxSourceEvent only1 binaryAnchor) ∧
    ((fun i => !(p100 i), ()) : CategoricalKey (Fin 3) (fun _ => Bool) Unit)
      ∈ sxSourceEvent only0 binaryAnchor ∧
    ((fun i => !(p100 i), ()) : CategoricalKey (Fin 3) (fun _ => Bool) Unit)
      ∉ sxSourceEvent only1 binaryAnchor := by
  refine ⟨?_, ?_, ?_⟩
  · intro y hy
    have h : y.1 0 = y.1 1 := hy.1
    simp [sxSourceEvent, sourceBranchEvent, sourceCollectionEquivalent, only0, only1, binaryAnchor, h]
  · simp [sxSourceEvent, sourceBranchEvent, sourceCollectionEquivalent, only0, binaryAnchor, p100]
  · simp [sxSourceEvent, sourceBranchEvent, sourceCollectionEquivalent, only1, binaryAnchor, p100]

theorem p11_absorption : ¬ IsInclusionAntichain absorbedFamily ∧
    absorbedFamily ≠ singletonLeft ∧ RedundancyLE absorbedFamily singletonLeft ∧
    RedundancyLE singletonLeft absorbedFamily ∧
    (∀ e : Fin 3 → Bool, DNF absorbedFamily e ↔ DNF singletonLeft e) := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · simp only [IsInclusionAntichain]
    decide +kernel
  · decide +kernel
  · simp only [RedundancyLE]
    decide +kernel
  · simp only [RedundancyLE]
    decide +kernel
  · intro e
    simp [DNF, absorbedFamily, singletonLeft]
    exact fun h _ => h


/-- M03 replaces the universal branch obligation by an existential one. -/
theorem m03_existential_branch :
    (∃ b ∈ either, ∃ a ∈ only0, a ⊆ b) ∧ ¬ RedundancyLE only0 either ∧
    DNF either p010 ∧ ¬ DNF only0 p010 := by simp only [RedundancyLE, DNF]; decide +kernel

/-- M04 permits a witness that is not in the source family. -/
theorem m04_missing_family_membership :
    (∀ b ∈ only1, ∃ a : Finset (Fin 3), a ⊆ b) ∧
    ¬ RedundancyLE only0 only1 ∧ DNF only1 p010 ∧ ¬ DNF only0 p010 := by simp only [RedundancyLE, DNF]; decide +kernel

theorem m05_or_inside_branch :
    (∃ a ∈ both, ∃ i ∈ a, p100 i = true) ∧ ¬ DNF both p100 := by simp only [DNF]; decide +kernel

theorem m06_and_across_family :
    DNF either p100 ∧ ¬ (∀ a ∈ either, ∀ i ∈ a, p100 i = true) := by simp only [DNF]; decide +kernel

theorem m07_all_true_only : DNF only0 (fun _ => true) ∧ DNF only1 (fun _ => true) ∧
    ¬ RedundancyLE only0 only1 := by simp only [RedundancyLE, DNF]; decide +kernel

theorem m10_swapped_pattern :
    DNF only0 p100 ∧ ¬ DNF only0 (fun i => p100 (if i = 0 then 1 else if i = 1 then 0 else i)) := by simp only [DNF]; decide +kernel

theorem m12_diagonal_not_realizing : ¬ RealizesAllPatterns binaryAnchor binaryDiagonal := by
  intro h
  obtain ⟨y, hy, he⟩ := h p100
  have same : EqualityPattern binaryAnchor y 0 = EqualityPattern binaryAnchor y 1 := by
    simp only [EqualityPattern, binaryAnchor, hy.1]
    rfl
  rw [he] at same
  simp [p100] at same

theorem m13_one_pattern_is_insufficient :
    EqualityPattern singletonAnchor singletonAnchor = (fun _ => true) ∧
    ¬ ∃ y : CategoricalKey (Fin 3) (fun _ => Unit) Unit,
      EqualityPattern singletonAnchor y = (fun _ => false) := by
  constructor
  · rfl
  · intro ⟨y, hy⟩
    have h := congrFun hy 0
    simp [EqualityPattern, singletonAnchor] at h

theorem m16_union_membership : noSourceMatch ∈ sxSourceEvent only0 x ∪ targetBranchEvent x ∧
    noSourceMatch ∉ sxTargetRestrictedEvent only0 x := by
  simp [noSourceMatch, x, only0, sxSourceEvent, sxTargetRestrictedEvent,
    sourceBranchEvent, targetBranchEvent, sourceTargetBranchEvent, sourceCollectionEquivalent,
    sourceTargetCollectionEquivalent, targetEquivalent]

end PidSxDnfOrderJudgeControls
