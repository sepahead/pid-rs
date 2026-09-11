import PidMgwTargetCopy.Interface
import PidMgwTargetCopyCandidate.Identities

/-!
Unexecuted source candidates for the unchanged local and averaged target-copy bounds.
The imported identity proofs are source-only dependencies, not accepted proof evidence.
All scalar inequalities below are connected to actual finite event or marginal masses.
The two exports retain the exact target propositions and add no hypotheses.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators
open PidFiniteConvergence PidMgwTargetCopy

namespace PidMgwTargetCopyCandidate

universe u v

private theorem logTargetCopyRatioBounds
    (a c j : ℝ) (hj : 0 < j) (hja : j ≤ a) (hjc : j ≤ c) :
    0 ≤ Real.log (a * c / (j * (a + c - j))) ∧
      Real.log (a * c / (j * (a + c - j))) ≤ Real.log (c / j) ∧
      Real.log (a * c / (j * (a + c - j))) ≤ Real.log (a / j) := by
  have ha : 0 < a := lt_of_lt_of_le hj hja
  have hc : 0 < c := lt_of_lt_of_le hj hjc
  have hd : 0 < a + c - j := by linarith
  have hdenominator : 0 < j * (a + c - j) := mul_pos hj hd
  have hproduct : j * (a + c - j) ≤ a * c := by
    have hresidual := mul_nonneg (sub_nonneg.mpr hja) (sub_nonneg.mpr hjc)
    nlinarith [hresidual]
  have hexpand :
      Real.log (a * c / (j * (a + c - j))) =
        Real.log a + Real.log c - (Real.log j + Real.log (a + c - j)) := by
    rw [Real.log_div (mul_ne_zero ha.ne' hc.ne') (mul_ne_zero hj.ne' hd.ne'),
      Real.log_mul ha.ne' hc.ne', Real.log_mul hj.ne' hd.ne']
  refine ⟨Real.log_nonneg ((one_le_div hdenominator).2 hproduct), ?_, ?_⟩
  · have hlog : Real.log a ≤ Real.log (a + c - j) :=
      Real.log_le_log ha (by linarith)
    rw [hexpand, Real.log_div hc.ne' hj.ne']
    linarith
  · have hlog : Real.log c ≤ Real.log (a + c - j) :=
      Real.log_le_log hc (by linarith)
    rw [hexpand, Real.log_div ha.ne' hj.ne']
    linarith

variable {sourceValue : Fin 2 → Type u} {B : Type v}
variable [∀ i, Fintype (sourceValue i)] [Fintype B]
variable [∀ i, DecidableEq (sourceValue i)] [DecidableEq B]

private theorem jointSourceMassLe
    (law : Key sourceValue B → ℝ) (hnonnegative : ∀ key, 0 ≤ law key)
    (anchor : Key sourceValue B) :
    sourceMass law .jointSources anchor ≤ sourceMass law .sourceOne anchor ∧
      sourceMass law .jointSources anchor ≤ sourceMass law .sourceTwo anchor := by
  classical
  have hevent :
      sxPid2SourceEvent .jointSources anchor =
        sxPid2SourceEvent .sourceOne anchor ∩ sxPid2SourceEvent .sourceTwo anchor := by
    simpa [sxPid2SourceEvent, sxPid2Collections, sxSourceEvent] using
      (source_singleton_branch_inter_eq_joint anchor).symm
  constructor
  · unfold sourceMass
    rw [hevent]
    exact finite_event_mass_mono law hnonnegative Finset.inter_subset_left
  · unfold sourceMass
    rw [hevent]
    exact finite_event_mass_mono law hnonnegative Finset.inter_subset_right

/-- The existing local signed-net atom lies between zero and both source surprises. -/
theorem localBounds : LocalBoundsTarget (sourceValue := sourceValue) (B := B) := by
  unfold LocalBoundsTarget
  intro law hlaw hcopy anchor hpositive
  dsimp only
  have hj : 0 < sourceMass law .jointSources anchor := by
    simpa only [sourceMass, sxPid2SourceEvent] using
      sx_source_event_mass_positive (sx_pid2_collections_nonempty .jointSources)
        law hlaw.1 anchor hpositive
  obtain ⟨hja, hjc⟩ := jointSourceMassLe law hlaw.1 anchor
  rw [localIdentity law hlaw hcopy anchor hpositive]
  simpa only [localFormula] using
    logTargetCopyRatioBounds
      (sourceMass law .sourceOne anchor) (sourceMass law .sourceTwo anchor)
      (sourceMass law .jointSources anchor) hj hja hjc

/-- The existing average is nonnegative and bounded by each finite conditional entropy. -/
theorem averagedBounds : AveragedBoundsTarget (sourceValue := sourceValue) (B := B) := by
  classical
  unfold AveragedBoundsTarget
  intro law hlaw hcopy
  dsimp only
  rw [averagedIdentity law hlaw hcopy]
  have hmarginal (row : SourceRow sourceValue) : 0 ≤ sourceLaw law row := by
    unfold sourceLaw
    exact Finset.sum_nonneg fun target _ => hlaw.1 (row, target)
  have hcoordinate (row : SourceRow sourceValue) (i : Fin 2) :
      sourceLaw law row ≤ coordinateMass (sourceLaw law) i (row i) := by
    unfold coordinateMass finiteEventMass
    exact Finset.single_le_sum (fun other _ => hmarginal other) (by simp)
  have hrow (row : SourceRow sourceValue)
      (hmem : row ∈ positiveMassSupport (sourceLaw law)) :
      0 ≤ rowFormula (sourceLaw law) row ∧
        rowFormula (sourceLaw law) row ≤
          Real.log (coordinateMass (sourceLaw law) 1 (row 1) / sourceLaw law row) ∧
        rowFormula (sourceLaw law) row ≤
          Real.log (coordinateMass (sourceLaw law) 0 (row 0) / sourceLaw law row) := by
    have hpositive : 0 < sourceLaw law row := by
      simpa only [positiveMassSupport, Finset.mem_filter, Finset.mem_univ, true_and]
        using hmem
    simpa only [rowFormula] using
      logTargetCopyRatioBounds
        (coordinateMass (sourceLaw law) 0 (row 0))
        (coordinateMass (sourceLaw law) 1 (row 1))
        (sourceLaw law row) hpositive (hcoordinate row 0) (hcoordinate row 1)
  constructor
  · exact Finset.sum_nonneg fun row hmem =>
      mul_nonneg (hmarginal row) (hrow row hmem).1
  · apply le_min
    · unfold sourceOneGivenTwoEntropy
      apply Finset.sum_le_sum
      intro row hmem
      exact mul_le_mul_of_nonneg_left (hrow row hmem).2.1 (hmarginal row)
    · unfold sourceTwoGivenOneEntropy
      apply Finset.sum_le_sum
      intro row hmem
      exact mul_le_mul_of_nonneg_left (hrow row hmem).2.2 (hmarginal row)

end PidMgwTargetCopyCandidate
