import PidFiniteConvergence.Deterministic
import Mathlib.Data.Matrix.Diagonal

/-!
# Finite-law algebra without a positive support-mass floor

This module proves exact-real algebraic facts used by a support-change-tolerant continuity
argument for averaged finite-alphabet shared-exclusions quantities:

* two equal-total nonnegative vectors split into their pointwise overlap and two residuals;
* the residuals have equal total mass and disjoint positive supports;
* concavity of the entropy summand gives a balanced-cardinality upper bound for the sum of
  two equal-mass residual entropies;
* a nonnegative pointwise component bounded by the base-law surprisal has every residual-weighted
  average between zero and the residual entropy;
* a signed pointwise value with the same surprisal envelope has residual-weighted absolute value
  at most the residual entropy;
* two component residuals combine through a maximum, while two signed residuals combine through
  a sum;
* the inverse of a finite down-set zeta matrix has row sum one at the least node and zero
  elsewhere; and
* the structural common-overlap logarithmic modulus has the correct endpoints and is at most its
  linear envelope.

The statements below do not define shared-exclusions events, the redundancy lattice, pointwise
partial-information atoms, sampling assumptions, or floating-point arithmetic. In particular,
the component transfer lemmas take their pointwise sign and surprisal bounds as premises.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators

namespace PidFiniteConvergence

variable {ι : Type*}

/-- Pointwise common mass of two finite vectors. -/
def overlapMass (p q : ι → ℝ) (i : ι) : ℝ :=
  min (p i) (q i)

/-- Residual mass belonging to the first vector after removing pointwise overlap. -/
def leftResidual (p q : ι → ℝ) (i : ι) : ℝ :=
  p i - overlapMass p q i

/-- Residual mass belonging to the second vector after removing pointwise overlap. -/
def rightResidual (p q : ι → ℝ) (i : ι) : ℝ :=
  q i - overlapMass p q i

/-- Overlap plus the first residual reconstructs the first vector pointwise. -/
theorem overlap_add_left_residual (p q : ι → ℝ) (i : ι) :
    overlapMass p q i + leftResidual p q i = p i := by
  simp [leftResidual]

/-- Overlap plus the second residual reconstructs the second vector pointwise. -/
theorem overlap_add_right_residual (p q : ι → ℝ) (i : ι) :
    overlapMass p q i + rightResidual p q i = q i := by
  simp [rightResidual]

/-- The first residual is pointwise nonnegative. -/
theorem left_residual_nonnegative (p q : ι → ℝ) (i : ι) :
    0 ≤ leftResidual p q i := by
  exact sub_nonneg.mpr (min_le_left (p i) (q i))

/-- The second residual is pointwise nonnegative. -/
theorem right_residual_nonnegative (p q : ι → ℝ) (i : ι) :
    0 ≤ rightResidual p q i := by
  exact sub_nonneg.mpr (min_le_right (p i) (q i))

/-- At every coordinate at least one residual vanishes. -/
theorem left_or_right_residual_eq_zero (p q : ι → ℝ) (i : ι) :
    leftResidual p q i = 0 ∨ rightResidual p q i = 0 := by
  rcases le_total (p i) (q i) with h | h
  · left
    simp [leftResidual, overlapMass, min_eq_left h]
  · right
    simp [rightResidual, overlapMass, min_eq_right h]

/-- The difference of the residuals is the original pointwise difference. -/
theorem left_residual_sub_right_residual (p q : ι → ℝ) (i : ι) :
    leftResidual p q i - rightResidual p q i = p i - q i := by
  simp [leftResidual, rightResidual]

/-- The pointwise absolute difference is the sum of the two disjoint residuals. -/
theorem abs_sub_eq_left_add_right_residual (p q : ι → ℝ) (i : ι) :
    |p i - q i| = leftResidual p q i + rightResidual p q i := by
  rw [← left_residual_sub_right_residual p q i]
  rcases left_or_right_residual_eq_zero p q i with hleft | hright
  · rw [hleft, zero_sub, abs_neg, abs_of_nonneg (right_residual_nonnegative p q i), zero_add]
  · rw [hright, sub_zero, abs_of_nonneg (left_residual_nonnegative p q i), add_zero]

/-- Equal-total finite vectors have residuals of equal total mass. -/
theorem sum_left_residual_eq_sum_right_residual
    [Fintype ι] (p q : ι → ℝ)
    (htotal : ∑ i, p i = ∑ i, q i) :
    ∑ i, leftResidual p q i = ∑ i, rightResidual p q i := by
  simp only [leftResidual, rightResidual, Finset.sum_sub_distrib]
  linarith

/-- For equal-total finite vectors, the `L1` distance is twice either residual mass. -/
theorem sum_abs_sub_eq_two_mul_sum_left_residual
    [Fintype ι] (p q : ι → ℝ)
    (htotal : ∑ i, p i = ∑ i, q i) :
    ∑ i, |p i - q i| = 2 * ∑ i, leftResidual p q i := by
  calc
    ∑ i, |p i - q i| =
        ∑ i, (leftResidual p q i + rightResidual p q i) := by
      apply Finset.sum_congr rfl
      intro i _
      exact abs_sub_eq_left_add_right_residual p q i
    _ =
        (∑ i, leftResidual p q i) +
          ∑ i, rightResidual p q i :=
      Finset.sum_add_distrib
    _ = 2 * ∑ i, leftResidual p q i := by
      rw [sum_left_residual_eq_sum_right_residual p q htotal]
      ring

/-- For probability vectors, overlap mass is one minus either residual mass. -/
theorem sum_overlap_eq_one_sub_sum_left_residual
    [Fintype ι] (p q : ι → ℝ)
    (hp : ∑ i, p i = 1) :
    ∑ i, overlapMass p q i = 1 - ∑ i, leftResidual p q i := by
  have hreconstruct :
      (∑ i, overlapMass p q i) + ∑ i, leftResidual p q i = ∑ i, p i := by
    rw [← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro i _
    exact overlap_add_left_residual p q i
  rw [hp] at hreconstruct
  linarith

/-- A nonnegative overlap leaves each residual below its corresponding original mass. -/
theorem left_residual_le_of_nonnegative
    (p q : ι → ℝ) (i : ι)
    (hp : 0 ≤ p i) (hq : 0 ≤ q i) :
    leftResidual p q i ≤ p i := by
  have hoverlap : 0 ≤ overlapMass p q i := by
    exact le_min hp hq
  simp only [leftResidual]
  linarith

/-- A nonnegative overlap leaves each residual below its corresponding original mass. -/
theorem right_residual_le_of_nonnegative
    (p q : ι → ℝ) (i : ι)
    (hp : 0 ≤ p i) (hq : 0 ≤ q i) :
    rightResidual p q i ≤ q i := by
  have hoverlap : 0 ≤ overlapMass p q i := by
    exact le_min hp hq
  simp only [rightResidual]
  linarith

/-- Entropy of a finite nonnegative residual vector, using the continuous zero convention. -/
noncomputable def residualEntropy [Fintype ι] (residual : ι → ℝ) : ℝ :=
  ∑ i, Real.negMulLog (residual i)

/-- Coordinates carrying strictly positive residual mass. -/
noncomputable def residualPositiveSupport
    [Fintype ι] [DecidableEq ι] (residual : ι → ℝ) : Finset ι :=
  Finset.univ.filter fun i => 0 < residual i

/-- A nonnegative residual vanishes outside its positive support. -/
theorem residual_eq_zero_outside_positive_support
    [Fintype ι] [DecidableEq ι]
    (residual : ι → ℝ)
    (hnonnegative : ∀ i, 0 ≤ residual i)
    (i : ι)
    (houtside : i ∉ residualPositiveSupport residual) :
    residual i = 0 := by
  have hnotPositive : ¬0 < residual i := by
    simpa [residualPositiveSupport] using houtside
  exact le_antisymm (le_of_not_gt hnotPositive) (hnonnegative i)

/-- A nonnegative residual with positive total mass has nonempty positive support. -/
theorem positive_support_card_positive_of_sum_positive
    [Fintype ι] [DecidableEq ι]
    (residual : ι → ℝ)
    (hnonnegative : ∀ i, 0 ≤ residual i)
    (hsumPositive : 0 < ∑ i, residual i) :
    0 < (residualPositiveSupport residual).card := by
  have hexists :
      ∃ i ∈ (Finset.univ : Finset ι), 0 < residual i :=
    (Finset.sum_pos_iff_of_nonneg
      (fun i (_ : i ∈ (Finset.univ : Finset ι)) => hnonnegative i)).mp
      hsumPositive
  obtain ⟨i, _, hi⟩ := hexists
  exact Finset.card_pos.mpr ⟨i, by simp [residualPositiveSupport, hi]⟩

/-- Summing a nonnegative residual over its positive support gives its full total mass. -/
theorem sum_positive_support_eq_sum
    [Fintype ι] [DecidableEq ι]
    (residual : ι → ℝ)
    (hnonnegative : ∀ i, 0 ≤ residual i) :
    (∑ i ∈ residualPositiveSupport residual, residual i) =
      ∑ i, residual i := by
  apply Finset.sum_subset (Finset.subset_univ (residualPositiveSupport residual))
  intro i _ hi
  exact residual_eq_zero_outside_positive_support residual hnonnegative i hi

/-- The positive supports of the two overlap residuals are disjoint. -/
theorem left_right_positive_support_disjoint
    [Fintype ι] [DecidableEq ι]
    (p q : ι → ℝ) :
    Disjoint
      (residualPositiveSupport (leftResidual p q))
      (residualPositiveSupport (rightResidual p q)) := by
  rw [Finset.disjoint_left]
  intro i hleft hright
  have hleftPositive : 0 < leftResidual p q i := by
    simpa [residualPositiveSupport] using hleft
  have hrightPositive : 0 < rightResidual p q i := by
    simpa [residualPositiveSupport] using hright
  rcases left_or_right_residual_eq_zero p q i with hzero | hzero
  · linarith
  · linarith

/-- A residual entropy is nonnegative when every residual coordinate lies in `[0, 1]`. -/
theorem residual_entropy_nonnegative
    [Fintype ι] (residual : ι → ℝ)
    (hnonnegative : ∀ i, 0 ≤ residual i)
    (hleOne : ∀ i, residual i ≤ 1) :
    0 ≤ residualEntropy residual := by
  apply Finset.sum_nonneg
  intro i _
  exact Real.negMulLog_nonneg (hnonnegative i) (hleOne i)

/-- Concavity of the entropy summand bounds entropy on a stated nonempty finite support by the
support size times the entropy summand at the average mass. -/
theorem sum_neg_mul_log_le_card_mul_neg_mul_log_average
    (support : Finset ι) (mass : ι → ℝ)
    (hcard : 0 < support.card)
    (hnonnegative : ∀ i ∈ support, 0 ≤ mass i) :
    (∑ i ∈ support, Real.negMulLog (mass i)) ≤
      (support.card : ℝ) *
        Real.negMulLog
          (((support.card : ℝ)⁻¹) * ∑ i ∈ support, mass i) := by
  let size : ℝ := support.card
  have hsizePositive : 0 < size := by
    change 0 < (support.card : ℝ)
    exact_mod_cast hcard
  have hweightSum :
      ∑ i ∈ support, size⁻¹ = 1 := by
    simp only [Finset.sum_const, nsmul_eq_mul]
    change (support.card : ℝ) * size⁻¹ = 1
    exact mul_inv_cancel₀ hsizePositive.ne'
  have hjensen :=
    Real.concaveOn_negMulLog.le_map_sum
      (t := support)
      (w := fun _ => size⁻¹)
      (p := mass)
      (fun _ _ => inv_nonneg.mpr hsizePositive.le)
      hweightSum
      (fun i hi => hnonnegative i hi)
  have hjensen' :
      size⁻¹ * (∑ i ∈ support, Real.negMulLog (mass i)) ≤
        Real.negMulLog
          (size⁻¹ * ∑ i ∈ support, mass i) := by
    simpa [Finset.mul_sum] using hjensen
  calc
    (∑ i ∈ support, Real.negMulLog (mass i)) =
        size *
          (size⁻¹ * ∑ i ∈ support, Real.negMulLog (mass i)) := by
      rw [← mul_assoc, mul_inv_cancel₀ hsizePositive.ne', one_mul]
    _ ≤
        size *
          Real.negMulLog
            (size⁻¹ * ∑ i ∈ support, mass i) :=
      mul_le_mul_of_nonneg_left hjensen' hsizePositive.le
    _ =
        (support.card : ℝ) *
          Real.negMulLog
            (((support.card : ℝ)⁻¹) * ∑ i ∈ support, mass i) := rfl

/-- If all residual mass is carried by a stated nonempty support, the same cardinality bound
controls the full residual entropy. -/
theorem residual_entropy_le_card_mul_neg_mul_log_average
    [Fintype ι] [DecidableEq ι]
    (support : Finset ι) (residual : ι → ℝ)
    (hcard : 0 < support.card)
    (hnonnegative : ∀ i, 0 ≤ residual i)
    (houtside : ∀ i ∉ support, residual i = 0) :
    residualEntropy residual ≤
      (support.card : ℝ) *
        Real.negMulLog
          (((support.card : ℝ)⁻¹) * ∑ i ∈ support, residual i) := by
  have hsupportSum :
      (∑ i ∈ support, Real.negMulLog (residual i)) =
        ∑ i, Real.negMulLog (residual i) := by
    apply Finset.sum_subset (Finset.subset_univ support)
    intro i _ hi
    rw [houtside i hi]
    exact Real.negMulLog_zero
  rw [residualEntropy, ← hsupportSum]
  exact
    sum_neg_mul_log_le_card_mul_neg_mul_log_average
      support residual hcard (fun i _ => hnonnegative i)

/-- The cardinality-times-average form of the entropy ceiling equals its usual logarithmic form
when both the support size and total mass are positive. -/
theorem card_mul_neg_mul_log_average_eq_mass_mul_log_card_div_mass
    {cardinality : ℕ} {mass : ℝ}
    (hcard : 0 < cardinality) (hmass : 0 < mass) :
    (cardinality : ℝ) *
        Real.negMulLog (((cardinality : ℝ)⁻¹) * mass) =
      mass * Real.log ((cardinality : ℝ) / mass) := by
  have hcardReal : (0 : ℝ) < cardinality := by
    exact_mod_cast hcard
  rw [inv_mul_eq_div]
  simp only [Real.negMulLog]
  rw [Real.log_div hmass.ne' hcardReal.ne']
  rw [Real.log_div hcardReal.ne' hmass.ne']
  field_simp
  ring

/-- Logarithmic form of the finite-support residual-entropy ceiling. -/
theorem residual_entropy_le_mass_mul_log_card_div_mass
    [Fintype ι] [DecidableEq ι]
    (support : Finset ι) (residual : ι → ℝ) {mass : ℝ}
    (hcard : 0 < support.card)
    (hmass : 0 < mass)
    (hnonnegative : ∀ i, 0 ≤ residual i)
    (houtside : ∀ i ∉ support, residual i = 0)
    (hsum : ∑ i ∈ support, residual i = mass) :
    residualEntropy residual ≤
      mass * Real.log ((support.card : ℝ) / mass) := by
  calc
    residualEntropy residual ≤
        (support.card : ℝ) *
          Real.negMulLog
            (((support.card : ℝ)⁻¹) *
              ∑ i ∈ support, residual i) :=
      residual_entropy_le_card_mul_neg_mul_log_average
        support residual hcard hnonnegative houtside
    _ =
        (support.card : ℝ) *
          Real.negMulLog (((support.card : ℝ)⁻¹) * mass) := by
      rw [hsum]
    _ = mass * Real.log ((support.card : ℝ) / mass) :=
      card_mul_neg_mul_log_average_eq_mass_mul_log_card_div_mass hcard hmass

/-- Two nonempty disjoint finite supports occupy at most the balanced-product ceiling of the
ambient finite type. -/
theorem card_mul_card_le_balanced_ambient
    [Fintype ι] [DecidableEq ι]
    (leftSupport rightSupport : Finset ι)
    (hdisjoint : Disjoint leftSupport rightSupport) :
    leftSupport.card * rightSupport.card ≤
      (Fintype.card ι * Fintype.card ι) / 4 := by
  have hsum :
      leftSupport.card + rightSupport.card ≤ Fintype.card ι := by
    rw [← Finset.card_union_of_disjoint hdisjoint]
    exact Finset.card_le_univ _
  have hsumReal :
      (leftSupport.card : ℝ) + rightSupport.card ≤ Fintype.card ι := by
    exact_mod_cast hsum
  have hsquare :
      ((leftSupport.card : ℝ) + rightSupport.card) *
          ((leftSupport.card : ℝ) + rightSupport.card) ≤
        (Fintype.card ι : ℝ) * Fintype.card ι :=
    mul_self_le_mul_self (by positivity) hsumReal
  have hbalanced :
      (leftSupport.card * rightSupport.card * 4 : ℕ) ≤
        Fintype.card ι * Fintype.card ι := by
    exact_mod_cast
      (show
        (leftSupport.card : ℝ) * rightSupport.card * 4 ≤
          (Fintype.card ι : ℝ) * Fintype.card ι by
        nlinarith [sq_nonneg ((leftSupport.card : ℝ) - rightSupport.card)])
  exact (Nat.le_div_iff_mul_le (by decide : 0 < 4)).2 hbalanced

/-- Entropies of two equal-mass residuals on stated nonempty supports are bounded by the logarithm
of the support-cardinality product. -/
theorem add_residual_entropy_le_mass_mul_log_card_product_div_mass_sq
    [Fintype ι] [DecidableEq ι]
    (leftSupport rightSupport : Finset ι)
    (leftResidualMass rightResidualMass : ι → ℝ)
    {mass : ℝ}
    (hleftCard : 0 < leftSupport.card)
    (hrightCard : 0 < rightSupport.card)
    (hmass : 0 < mass)
    (hleftNonnegative : ∀ i, 0 ≤ leftResidualMass i)
    (hrightNonnegative : ∀ i, 0 ≤ rightResidualMass i)
    (hleftOutside : ∀ i ∉ leftSupport, leftResidualMass i = 0)
    (hrightOutside : ∀ i ∉ rightSupport, rightResidualMass i = 0)
    (hleftSum : ∑ i ∈ leftSupport, leftResidualMass i = mass)
    (hrightSum : ∑ i ∈ rightSupport, rightResidualMass i = mass) :
    residualEntropy leftResidualMass + residualEntropy rightResidualMass ≤
      mass *
        Real.log
          (((leftSupport.card : ℝ) * rightSupport.card) / mass ^ 2) := by
  have hleft :=
    residual_entropy_le_mass_mul_log_card_div_mass
      leftSupport leftResidualMass hleftCard hmass hleftNonnegative
      hleftOutside hleftSum
  have hright :=
    residual_entropy_le_mass_mul_log_card_div_mass
      rightSupport rightResidualMass hrightCard hmass hrightNonnegative
      hrightOutside hrightSum
  have hleftCardReal : (0 : ℝ) < leftSupport.card := by
    exact_mod_cast hleftCard
  have hrightCardReal : (0 : ℝ) < rightSupport.card := by
    exact_mod_cast hrightCard
  have hproduct :
      ((leftSupport.card : ℝ) / mass) *
          ((rightSupport.card : ℝ) / mass) =
        ((leftSupport.card : ℝ) * rightSupport.card) / mass ^ 2 := by
    field_simp
  calc
    residualEntropy leftResidualMass + residualEntropy rightResidualMass ≤
        mass * Real.log ((leftSupport.card : ℝ) / mass) +
          mass * Real.log ((rightSupport.card : ℝ) / mass) :=
      add_le_add hleft hright
    _ =
        mass *
          (Real.log ((leftSupport.card : ℝ) / mass) +
            Real.log ((rightSupport.card : ℝ) / mass)) := by ring
    _ =
        mass *
          Real.log
            (((leftSupport.card : ℝ) / mass) *
              ((rightSupport.card : ℝ) / mass)) := by
      rw [Real.log_mul
        (div_ne_zero hleftCardReal.ne' hmass.ne')
        (div_ne_zero hrightCardReal.ne' hmass.ne')]
    _ =
        mass *
          Real.log
            (((leftSupport.card : ℝ) * rightSupport.card) / mass ^ 2) := by
      rw [hproduct]

/-- Balanced-cardinality entropy upper bound for two equal-mass residuals with disjoint positive
supports. -/
theorem add_residual_entropy_le_balanced_ambient_bound
    [Fintype ι] [DecidableEq ι]
    (leftSupport rightSupport : Finset ι)
    (leftResidualMass rightResidualMass : ι → ℝ)
    {mass : ℝ}
    (hdisjoint : Disjoint leftSupport rightSupport)
    (hleftCard : 0 < leftSupport.card)
    (hrightCard : 0 < rightSupport.card)
    (hmass : 0 < mass)
    (hleftNonnegative : ∀ i, 0 ≤ leftResidualMass i)
    (hrightNonnegative : ∀ i, 0 ≤ rightResidualMass i)
    (hleftOutside : ∀ i ∉ leftSupport, leftResidualMass i = 0)
    (hrightOutside : ∀ i ∉ rightSupport, rightResidualMass i = 0)
    (hleftSum : ∑ i ∈ leftSupport, leftResidualMass i = mass)
    (hrightSum : ∑ i ∈ rightSupport, rightResidualMass i = mass) :
    residualEntropy leftResidualMass + residualEntropy rightResidualMass ≤
      mass *
        Real.log
          ((((Fintype.card ι * Fintype.card ι) / 4 : ℕ) : ℝ) /
            mass ^ 2) := by
  have hproductBound :=
    card_mul_card_le_balanced_ambient
      leftSupport rightSupport hdisjoint
  have hproductPositive :
      0 < leftSupport.card * rightSupport.card :=
    Nat.mul_pos hleftCard hrightCard
  have hceilingPositive :
      0 < (Fintype.card ι * Fintype.card ι) / 4 :=
    hproductPositive.trans_le hproductBound
  have hbase :=
    add_residual_entropy_le_mass_mul_log_card_product_div_mass_sq
      leftSupport rightSupport leftResidualMass rightResidualMass
      hleftCard hrightCard hmass hleftNonnegative hrightNonnegative
      hleftOutside hrightOutside hleftSum hrightSum
  have hdenominatorPositive : 0 < mass ^ 2 := sq_pos_of_pos hmass
  have hargumentPositive :
      0 <
        ((leftSupport.card : ℝ) * rightSupport.card) / mass ^ 2 := by
    positivity
  have hargumentOrder :
      ((leftSupport.card : ℝ) * rightSupport.card) / mass ^ 2 ≤
        (((Fintype.card ι * Fintype.card ι) / 4 : ℕ) : ℝ) /
          mass ^ 2 := by
    apply div_le_div_of_nonneg_right _ hdenominatorPositive.le
    exact_mod_cast hproductBound
  have hlogOrder :
      Real.log
          (((leftSupport.card : ℝ) * rightSupport.card) / mass ^ 2) ≤
        Real.log
          ((((Fintype.card ι * Fintype.card ι) / 4 : ℕ) : ℝ) /
            mass ^ 2) :=
    Real.log_le_log hargumentPositive hargumentOrder
  exact hbase.trans (mul_le_mul_of_nonneg_left hlogOrder hmass.le)

/-- The overlap construction itself satisfies the balanced-cardinality entropy upper bound.
For probability laws, the repeated residual total is their total-variation distance. -/
theorem overlap_residual_entropy_sum_le_balanced_ambient_bound
    [Fintype ι] [DecidableEq ι]
    (p q : ι → ℝ)
    (htotal : ∑ i, p i = ∑ i, q i)
    (hresidualPositive : 0 < ∑ i, leftResidual p q i) :
    residualEntropy (leftResidual p q) +
        residualEntropy (rightResidual p q) ≤
      (∑ i, leftResidual p q i) *
        Real.log
          ((((Fintype.card ι * Fintype.card ι) / 4 : ℕ) : ℝ) /
            (∑ i, leftResidual p q i) ^ 2) := by
  have hsumResidual :=
    sum_left_residual_eq_sum_right_residual p q htotal
  have hrightResidualPositive :
      0 < ∑ i, rightResidual p q i := by
    rw [← hsumResidual]
    exact hresidualPositive
  have hleftCard :
      0 < (residualPositiveSupport (leftResidual p q)).card :=
    positive_support_card_positive_of_sum_positive
      (leftResidual p q)
      (left_residual_nonnegative p q)
      hresidualPositive
  have hrightCard :
      0 < (residualPositiveSupport (rightResidual p q)).card :=
    positive_support_card_positive_of_sum_positive
      (rightResidual p q)
      (right_residual_nonnegative p q)
      hrightResidualPositive
  have hleftSum :
      (∑ i ∈ residualPositiveSupport (leftResidual p q),
          leftResidual p q i) =
        ∑ i, leftResidual p q i :=
    sum_positive_support_eq_sum
      (leftResidual p q) (left_residual_nonnegative p q)
  have hrightSum :
      (∑ i ∈ residualPositiveSupport (rightResidual p q),
          rightResidual p q i) =
        ∑ i, leftResidual p q i := by
    rw [
      sum_positive_support_eq_sum
        (rightResidual p q) (right_residual_nonnegative p q),
      ← hsumResidual
    ]
  exact
    add_residual_entropy_le_balanced_ambient_bound
      (residualPositiveSupport (leftResidual p q))
      (residualPositiveSupport (rightResidual p q))
      (leftResidual p q)
      (rightResidual p q)
      (left_right_positive_support_disjoint p q)
      hleftCard
      hrightCard
      hresidualPositive
      (left_residual_nonnegative p q)
      (right_residual_nonnegative p q)
      (residual_eq_zero_outside_positive_support
        (leftResidual p q) (left_residual_nonnegative p q))
      (residual_eq_zero_outside_positive_support
        (rightResidual p q) (right_residual_nonnegative p q))
      hleftSum
      hrightSum

/-- A residual-weighted nonnegative component bounded by base-law surprisal is at most residual
entropy. The premise `residual ≤ base` makes every logarithm comparison occur at positive
coordinates only. -/
theorem residual_weighted_component_between_zero_and_entropy
    [Fintype ι]
    (residual base value : ι → ℝ)
    (hresidual : ∀ i, 0 ≤ residual i)
    (hresidualBase : ∀ i, residual i ≤ base i)
    (hvalueNonnegative : ∀ i, 0 ≤ value i)
    (hvalueUpper : ∀ i, value i ≤ -Real.log (base i)) :
    0 ≤ ∑ i, residual i * value i ∧
      ∑ i, residual i * value i ≤ residualEntropy residual := by
  constructor
  · apply Finset.sum_nonneg
    intro i _
    exact mul_nonneg (hresidual i) (hvalueNonnegative i)
  · apply Finset.sum_le_sum
    intro i _
    by_cases hzero : residual i = 0
    · simp [hzero]
    · have hpositive : 0 < residual i :=
        lt_of_le_of_ne (hresidual i) (Ne.symm hzero)
      have hlog :
          -Real.log (base i) ≤ -Real.log (residual i) := by
        have := Real.log_le_log hpositive (hresidualBase i)
        linarith
      calc
        residual i * value i
            ≤ residual i * (-Real.log (base i)) :=
          mul_le_mul_of_nonneg_left (hvalueUpper i) (hresidual i)
        _ ≤ residual i * (-Real.log (residual i)) :=
          mul_le_mul_of_nonneg_left hlog (hresidual i)
        _ = Real.negMulLog (residual i) := by
          simp [Real.negMulLog]

/-- A residual-weighted signed value bounded in magnitude by base-law surprisal has absolute value
at most residual entropy. -/
theorem abs_residual_weighted_signed_value_le_entropy
    [Fintype ι]
    (residual base value : ι → ℝ)
    (hresidual : ∀ i, 0 ≤ residual i)
    (hresidualBase : ∀ i, residual i ≤ base i)
    (hvalueUpper : ∀ i, |value i| ≤ -Real.log (base i)) :
    |∑ i, residual i * value i| ≤ residualEntropy residual := by
  calc
    |∑ i, residual i * value i|
        ≤ ∑ i, |residual i * value i| :=
      Finset.abs_sum_le_sum_abs (f := fun i => residual i * value i) Finset.univ
    _ = ∑ i, residual i * |value i| := by
      apply Finset.sum_congr rfl
      intro i _
      rw [abs_mul, abs_of_nonneg (hresidual i)]
    _ ≤ residualEntropy residual := by
      exact
        (residual_weighted_component_between_zero_and_entropy
          residual base (fun i => |value i|)
          hresidual hresidualBase
          (fun i => abs_nonneg (value i)) hvalueUpper).2

/-- The difference of two nonnegative component residuals uses the larger entropy ceiling, not
their sum. -/
theorem abs_component_residual_sub_le_max_entropy
    {left right leftEntropy rightEntropy : ℝ}
    (hleftNonnegative : 0 ≤ left)
    (hrightNonnegative : 0 ≤ right)
    (hleftUpper : left ≤ leftEntropy)
    (hrightUpper : right ≤ rightEntropy) :
    |left - right| ≤ max leftEntropy rightEntropy := by
  rw [abs_le]
  constructor
  · have hrightMax : right ≤ max leftEntropy rightEntropy :=
      hrightUpper.trans (le_max_right _ _)
    linarith
  · have hleftMax : left ≤ max leftEntropy rightEntropy :=
      hleftUpper.trans (le_max_left _ _)
    linarith

/-- The difference of two signed residuals uses the sum of their entropy ceilings. -/
theorem abs_signed_residual_sub_le_add_entropy
    {left right leftEntropy rightEntropy : ℝ}
    (hleft : |left| ≤ leftEntropy)
    (hright : |right| ≤ rightEntropy) :
    |left - right| ≤ leftEntropy + rightEntropy := by
  rw [abs_le] at hleft hright ⊢
  constructor <;> linarith

/-- Pointwise nonnegative component and surprisal premises transfer the two overlap residuals with
one maximum entropy term. This is the abstract sign-sharpened component step used before any
scientific identification. -/
theorem abs_overlap_component_residual_sub_le_max_entropy
    [Fintype ι]
    (p q leftValue rightValue : ι → ℝ)
    (hpNonnegative : ∀ i, 0 ≤ p i)
    (hqNonnegative : ∀ i, 0 ≤ q i)
    (hleftValueNonnegative : ∀ i, 0 ≤ leftValue i)
    (hrightValueNonnegative : ∀ i, 0 ≤ rightValue i)
    (hleftValueUpper : ∀ i, leftValue i ≤ -Real.log (p i))
    (hrightValueUpper : ∀ i, rightValue i ≤ -Real.log (q i)) :
    |(∑ i, leftResidual p q i * leftValue i) -
        ∑ i, rightResidual p q i * rightValue i| ≤
      max
        (residualEntropy (leftResidual p q))
        (residualEntropy (rightResidual p q)) := by
  have hleft :=
    residual_weighted_component_between_zero_and_entropy
      (leftResidual p q) p leftValue
      (left_residual_nonnegative p q)
      (fun i =>
        left_residual_le_of_nonnegative p q i
          (hpNonnegative i) (hqNonnegative i))
      hleftValueNonnegative hleftValueUpper
  have hright :=
    residual_weighted_component_between_zero_and_entropy
      (rightResidual p q) q rightValue
      (right_residual_nonnegative p q)
      (fun i =>
        right_residual_le_of_nonnegative p q i
          (hpNonnegative i) (hqNonnegative i))
      hrightValueNonnegative hrightValueUpper
  exact
    abs_component_residual_sub_le_max_entropy
      hleft.1 hright.1 hleft.2 hright.2

/-- Pointwise signed surprisal premises transfer the two overlap residuals with the sum of their
entropy terms. -/
theorem abs_overlap_signed_residual_sub_le_add_entropy
    [Fintype ι]
    (p q leftValue rightValue : ι → ℝ)
    (hpNonnegative : ∀ i, 0 ≤ p i)
    (hqNonnegative : ∀ i, 0 ≤ q i)
    (hleftValueUpper : ∀ i, |leftValue i| ≤ -Real.log (p i))
    (hrightValueUpper : ∀ i, |rightValue i| ≤ -Real.log (q i)) :
    |(∑ i, leftResidual p q i * leftValue i) -
        ∑ i, rightResidual p q i * rightValue i| ≤
      residualEntropy (leftResidual p q) +
        residualEntropy (rightResidual p q) := by
  have hleft :=
    abs_residual_weighted_signed_value_le_entropy
      (leftResidual p q) p leftValue
      (left_residual_nonnegative p q)
      (fun i =>
        left_residual_le_of_nonnegative p q i
          (hpNonnegative i) (hqNonnegative i))
      hleftValueUpper
  have hright :=
    abs_residual_weighted_signed_value_le_entropy
      (rightResidual p q) q rightValue
      (right_residual_nonnegative p q)
      (fun i =>
        right_residual_le_of_nonnegative p q i
          (hpNonnegative i) (hqNonnegative i))
      hrightValueUpper
  exact abs_signed_residual_sub_le_add_entropy hleft hright

/-- Down-set zeta matrix of a finite ordered type. Rows index cumulatives and columns index
atoms. -/
def downSetZetaMatrix
    (κ : Type*) [LE κ] [DecidableLE κ] : Matrix κ κ ℝ :=
  fun row column => if column ≤ row then 1 else 0

/-- If `mobius` is a left inverse of the down-set zeta matrix, its row sum is one at the least
node and zero elsewhere. -/
theorem mobius_row_sum_eq_ite_bot
    {κ : Type*} [Fintype κ] [DecidableEq κ] [PartialOrder κ] [DecidableLE κ] [OrderBot κ]
    (mobius : Matrix κ κ ℝ)
    (hinverse : mobius * downSetZetaMatrix κ = 1)
    (row : κ) :
    ∑ column, mobius row column = if row = ⊥ then 1 else 0 := by
  have hentry := congr_fun (congr_fun hinverse row) ⊥
  simpa [Matrix.mul_apply, Matrix.one_apply, downSetZetaMatrix] using hentry

/-- Structural common-overlap modulus for a union of `collections` equivalence neighborhoods.
The field convention at `eta = 1` supplies its intended endpoint value. -/
noncomputable def equivalenceUnionCommonModulus
    (collections : ℕ) (eta : ℝ) : ℝ :=
  (1 - eta) *
    Real.log (1 + (collections : ℝ) * eta / (1 - eta))

/-- The structural common-overlap modulus vanishes at zero law distance. -/
@[simp] theorem equivalence_union_common_modulus_zero (collections : ℕ) :
    equivalenceUnionCommonModulus collections 0 = 0 := by
  simp [equivalenceUnionCommonModulus]

/-- The totalized field expression has the intended endpoint value at distance one. -/
@[simp] theorem equivalence_union_common_modulus_one (collections : ℕ) :
    equivalenceUnionCommonModulus collections 1 = 0 := by
  simp [equivalenceUnionCommonModulus]

/-- On the probability-distance interval below one, the structural common-overlap modulus is
nonnegative. -/
theorem equivalence_union_common_modulus_nonnegative
    (collections : ℕ) {eta : ℝ}
    (hetaNonnegative : 0 ≤ eta) (hetaOne : eta < 1) :
    0 ≤ equivalenceUnionCommonModulus collections eta := by
  have honeMinus : 0 ≤ 1 - eta := by linarith
  have hratio :
      0 ≤ (collections : ℝ) * eta / (1 - eta) := by
    positivity
  have hlog :
      0 ≤ Real.log (1 + (collections : ℝ) * eta / (1 - eta)) := by
    exact Real.log_nonneg (by linarith)
  exact mul_nonneg honeMinus hlog

/-- The structural logarithmic modulus is at most its simple linear envelope. -/
theorem equivalence_union_common_modulus_le_linear
    (collections : ℕ) {eta : ℝ}
    (hetaNonnegative : 0 ≤ eta) (hetaOne : eta < 1) :
    equivalenceUnionCommonModulus collections eta ≤
      (collections : ℝ) * eta := by
  have honeMinusPositive : 0 < 1 - eta := sub_pos.mpr hetaOne
  have hratio :
      0 ≤ (collections : ℝ) * eta / (1 - eta) := by
    positivity
  have hargument :
      0 < 1 + (collections : ℝ) * eta / (1 - eta) := by
    linarith
  have hlog :
      Real.log (1 + (collections : ℝ) * eta / (1 - eta)) ≤
        (collections : ℝ) * eta / (1 - eta) := by
    have := Real.log_le_sub_one_of_pos hargument
    linarith
  calc
    equivalenceUnionCommonModulus collections eta =
        (1 - eta) *
          Real.log (1 + (collections : ℝ) * eta / (1 - eta)) := rfl
    _ ≤
        (1 - eta) *
          ((collections : ℝ) * eta / (1 - eta)) :=
      mul_le_mul_of_nonneg_left hlog honeMinusPositive.le
    _ = (collections : ℝ) * eta := by
      field_simp

/-- On the closed probability-distance interval, the structural common-overlap modulus is
nonnegative and no larger than its simple linear envelope. -/
theorem equivalence_union_common_modulus_closed_interval_bounds
    (collections : ℕ) {eta : ℝ}
    (hetaNonnegative : 0 ≤ eta) (hetaOne : eta ≤ 1) :
    0 ≤ equivalenceUnionCommonModulus collections eta ∧
      equivalenceUnionCommonModulus collections eta ≤
        (collections : ℝ) * eta := by
  rcases lt_or_eq_of_le hetaOne with hetaInterior | rfl
  · exact
      ⟨equivalence_union_common_modulus_nonnegative
          collections hetaNonnegative hetaInterior,
        equivalence_union_common_modulus_le_linear
          collections hetaNonnegative hetaInterior⟩
  · simp

end PidFiniteConvergence
