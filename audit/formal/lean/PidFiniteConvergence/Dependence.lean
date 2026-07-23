import PidFiniteConvergence.Deterministic
import Mathlib.Algebra.Order.BigOperators.Ring.Finset

/-!
# Deterministic core for dependency-colored finite-alphabet bounds

This module proves deterministic and algebraic obligations used by the dependency-colored
finite-alphabet concentration argument:

* event-mass error is at most one half of joint `L1` error, and the positive-coordinate event
  attains that bound for a zero-total signed vector;
* strict `L1` separation from a support face preserves a positive cell;
* one logarithm has the stated local modulus;
* the local logarithmic modulus is monotone in the law error;
* the logarithmic modulus has the stated rational upper bound;
* the effective-color numerator and its normalized factor have the stated bounds;
* a fixed Mobius row multiplies a coordinatewise modulus by its absolute row sum;
* a finite weighted average obeys generic value-and-weight perturbation bounds, including the
  sharper half-range bound obtained by centering equal-total weights; and
* the `1 / (n * (n + 1))` anytime-error allocation telescopes exactly.

The encoded statements are exact-real lemmas. This module does not encode random variables,
mutual independence, generalized Holder, Hoeffding's lemma, a Chernoff argument, a union bound,
the shared-exclusions event construction, an identification of the generic perturbation lemmas
with a PID quantity, or the pid-rs implementation. The probabilistic theorem and the refinement
boundary remain explicit prose proofs outside Lean.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators

namespace PidFiniteConvergence

variable {ι : Type*}

/-- If a finite signed vector has total mass zero, the absolute mass of every event is at most one
half of its `L1` norm. -/
theorem abs_event_sum_le_half_l1 [Fintype ι] [DecidableEq ι]
    (difference : ι → ℝ) (event : Finset ι)
    (htotal : ∑ i, difference i = 0) :
    |∑ i ∈ event, difference i| ≤ (∑ i, |difference i|) / 2 := by
  let complement := Finset.univ \ event
  have hevent_subset : event ⊆ Finset.univ := Finset.subset_univ event
  have hcomplement :
      ∑ i ∈ complement, difference i = -(∑ i ∈ event, difference i) := by
    dsimp [complement]
    have hsplit :
        (∑ i ∈ Finset.univ \ event, difference i) +
          ∑ i ∈ event, difference i = ∑ i ∈ Finset.univ, difference i :=
      Finset.sum_sdiff hevent_subset
    have htotal' : ∑ i ∈ Finset.univ, difference i = 0 := by simpa using htotal
    rw [htotal'] at hsplit
    linarith
  have habs_complement :
      ∑ i ∈ complement, |difference i| =
        (∑ i, |difference i|) - ∑ i ∈ event, |difference i| := by
    dsimp [complement]
    have hsplit :
        (∑ i ∈ Finset.univ \ event, |difference i|) +
          ∑ i ∈ event, |difference i| = ∑ i ∈ Finset.univ, |difference i| :=
      Finset.sum_sdiff hevent_subset
    linarith
  have hevent_triangle :
      |∑ i ∈ event, difference i| ≤ ∑ i ∈ event, |difference i| := by
    exact Finset.abs_sum_le_sum_abs (f := difference) event
  have hcomplement_triangle :
      |∑ i ∈ complement, difference i| ≤ ∑ i ∈ complement, |difference i| := by
    exact Finset.abs_sum_le_sum_abs (f := difference) complement
  rw [hcomplement, abs_neg] at hcomplement_triangle
  linarith

/-- The event of coordinates with strictly positive signed mass. The `DecidableEq` premise is
explicit. The definition is noncomputable because exact order comparison on `Real` is
noncomputable. -/
noncomputable def positiveCoordinateEvent [Fintype ι] [DecidableEq ι]
    (difference : ι → ℝ) : Finset ι :=
  Finset.univ.filter fun i => 0 < difference i

/-- For a finite signed vector with total mass zero, the positive-coordinate event attains one
half of the `L1` norm. Finite indexing and decidable equality are explicit premises; the event
uses the noncomputable exact-order decision on `Real` declared above. -/
theorem sum_positive_coordinate_event_eq_half_l1 [Fintype ι] [DecidableEq ι]
    (difference : ι → ℝ)
    (htotal : ∑ i, difference i = 0) :
    (∑ i ∈ positiveCoordinateEvent difference, difference i) =
      (∑ i, |difference i|) / 2 := by
  have hpositivePart :
      (∑ i ∈ positiveCoordinateEvent difference, difference i) =
        ∑ i, (difference i)⁺ := by
    simp only [positiveCoordinateEvent, Finset.sum_filter]
    apply Finset.sum_congr rfl
    intro i _
    by_cases hi : 0 < difference i
    · simp [hi, posPart_eq_self.mpr hi.le]
    · have hnonpositive : difference i ≤ 0 := le_of_not_gt hi
      simp [hi, posPart_eq_zero.mpr hnonpositive]
  have hsumPositivePart :
      (∑ i, |difference i|) = 2 * ∑ i, (difference i)⁺ := by
    calc
      (∑ i, |difference i|) =
          (∑ i, |difference i|) + ∑ i, difference i := by rw [htotal, add_zero]
      _ = ∑ i, (|difference i| + difference i) :=
        Finset.sum_add_distrib.symm
      _ = ∑ i, 2 * (difference i)⁺ := by
        apply Finset.sum_congr rfl
        intro i _
        simpa [two_smul, two_mul] using
          (abs_add_eq_two_nsmul_posPart (difference i))
      _ = 2 * ∑ i, (difference i)⁺ := by
        rw [Finset.mul_sum]
  rw [hpositivePart]
  linarith

/-- A positive reference cell cannot disappear while the `L1` error is strictly below twice the
minimum supported mass. -/
theorem positive_cell_of_half_l1_control
    {p q delta pMin : ℝ}
    (_hpMin : 0 < pMin) (hp : pMin ≤ p)
    (_hdelta : 0 ≤ delta) (hstrict : delta < 2 * pMin)
    (hcell : |q - p| ≤ delta / 2) :
    0 < q := by
  have hlower : -(delta / 2) ≤ q - p := neg_le_of_abs_le hcell
  linarith

/-- If a positive ratio lies between `1 - x` and `1 + x`, its log magnitude is bounded by
`-log (1 - x)`. -/
theorem abs_log_ratio_le_neg_log_one_sub
    {ratio x : ℝ}
    (hx0 : 0 ≤ x) (hx1 : x < 1)
    (hlower : 1 - x ≤ ratio) (hupper : ratio ≤ 1 + x) :
    |Real.log ratio| ≤ -Real.log (1 - x) := by
  have honeSub : 0 < 1 - x := sub_pos.mpr hx1
  have hratio : 0 < ratio := honeSub.trans_le hlower
  have honeAdd : 0 < 1 + x := by linarith
  have hlogLower : Real.log (1 - x) ≤ Real.log ratio :=
    Real.log_le_log honeSub hlower
  have hlogUpper : Real.log ratio ≤ Real.log (1 + x) :=
    Real.log_le_log hratio hupper
  have hplus : Real.log (1 + x) ≤ x := by
    have := Real.log_le_sub_one_of_pos honeAdd
    linarith
  have hminus : x ≤ -Real.log (1 - x) := by
    have := Real.log_le_sub_one_of_pos honeSub
    linarith
  rw [abs_le]
  constructor <;> linarith

/-- The stated one-log modulus follows from total-variation event control and a positive reference
lower bound. -/
theorem abs_log_change_le_local_modulus
    {p q delta pMin : ℝ}
    (hpMin : 0 < pMin) (hp : pMin ≤ p)
    (hdelta : 0 ≤ delta) (hstrict : delta < 2 * pMin)
    (hcell : |q - p| ≤ delta / 2) :
    |Real.log q - Real.log p| ≤
      -Real.log (1 - delta / (2 * pMin)) := by
  let x := delta / (2 * pMin)
  have hx0 : 0 ≤ x := by
    dsimp [x]
    positivity
  have hx1 : x < 1 := by
    dsimp [x]
    exact (div_lt_one (by positivity)).2 hstrict
  have hp0 : 0 < p := hpMin.trans_le hp
  have hq0 : 0 < q :=
    positive_cell_of_half_l1_control hpMin hp hdelta hstrict hcell
  have hpMinMul : pMin * x = delta / 2 := by
    dsimp [x]
    field_simp
  have hdeltaLe : delta / 2 ≤ p * x := by
    rw [← hpMinMul]
    exact mul_le_mul_of_nonneg_right hp hx0
  have hlowerDifference : -(delta / 2) ≤ q - p :=
    (neg_le_of_abs_le hcell)
  have hupperDifference : q - p ≤ delta / 2 :=
    (le_of_abs_le hcell)
  have hlowerRatio : 1 - x ≤ q / p := by
    rw [le_div_iff₀ hp0]
    nlinarith
  have hupperRatio : q / p ≤ 1 + x := by
    rw [div_le_iff₀ hp0]
    nlinarith
  rw [← Real.log_div hq0.ne' hp0.ne']
  exact abs_log_ratio_le_neg_log_one_sub hx0 hx1 hlowerRatio hupperRatio

/-- The local logarithmic modulus is nondecreasing in the `L1` error while the strict support
margin holds. -/
theorem local_log_modulus_mono
    {deltaSmall deltaLarge pMin : ℝ}
    (hpMin : 0 < pMin)
    (hdelta : deltaSmall ≤ deltaLarge)
    (hstrict : deltaLarge < 2 * pMin) :
    -Real.log (1 - deltaSmall / (2 * pMin)) ≤
      -Real.log (1 - deltaLarge / (2 * pMin)) := by
  have hdenominator : 0 < 2 * pMin := by positivity
  have hquotient :
      deltaSmall / (2 * pMin) ≤ deltaLarge / (2 * pMin) :=
    div_le_div_of_nonneg_right hdelta hdenominator.le
  have hlargePositive : 0 < 1 - deltaLarge / (2 * pMin) := by
    rw [sub_pos, div_lt_one hdenominator]
    exact hstrict
  have hargument :
      1 - deltaLarge / (2 * pMin) ≤
        1 - deltaSmall / (2 * pMin) := by
    linarith
  have hlog :=
    Real.log_le_log hlargePositive hargument
  linarith

/-- The logarithmic modulus is at most `x / (1 - x)` on `[0, 1)`. -/
theorem neg_log_one_sub_le_ratio {x : ℝ}
    (_hx0 : 0 ≤ x) (hx1 : x < 1) :
    -Real.log (1 - x) ≤ x / (1 - x) := by
  have honeSub : 0 < 1 - x := sub_pos.mpr hx1
  calc
    -Real.log (1 - x) = Real.log (1 - x)⁻¹ := by rw [Real.log_inv]
    _ ≤ (1 - x)⁻¹ - 1 := Real.log_le_sub_one_of_pos (inv_pos.mpr honeSub)
    _ = x / (1 - x) := by field_simp; ring

/-- On `0 ≤ x ≤ 1/4`, the logarithmic modulus is at most `4x/3`. -/
theorem neg_log_one_sub_le_four_thirds {x : ℝ}
    (hx0 : 0 ≤ x) (hxQuarter : x ≤ 1 / 4) :
    -Real.log (1 - x) ≤ 4 * x / 3 := by
  have hx1 : x < 1 := by linarith
  calc
    -Real.log (1 - x) ≤ x / (1 - x) :=
      neg_log_one_sub_le_ratio hx0 hx1
    _ ≤ 4 * x / 3 := by
      rw [div_le_iff₀ (sub_pos.mpr hx1)]
      nlinarith

/-- The complete algebraic chain for the refined local logarithmic modulus in the small-error
regime. The premise `pMin ≤ 1` is the explicit mass-domain condition needed to compare
`eta = delta / 2` with `xi = delta / (2 * pMin)`. This theorem does not encode a probability
law or identify the refined modulus with an SxPID quantity. -/
theorem refined_log_modulus_linearized_chain
    {delta pMin : ℝ}
    (hdelta : 0 ≤ delta)
    (hpMin : 0 < pMin)
    (hpMinOne : pMin ≤ 1)
    (hsmall : delta ≤ pMin / 2) :
    let eta := delta / 2
    let xi := delta / (2 * pMin)
    0 ≤ -Real.log (1 - xi) - eta ∧
      -Real.log (1 - xi) - eta ≤ -Real.log (1 - xi) ∧
      -Real.log (1 - xi) ≤ xi / (1 - xi) ∧
      xi / (1 - xi) ≤ 4 * xi / 3 ∧
      4 * xi / 3 = 2 * delta / (3 * pMin) := by
  dsimp only
  have hdenominator : 0 < 2 * pMin := by positivity
  have hxiNonnegative : 0 ≤ delta / (2 * pMin) := by positivity
  have hxiQuarter : delta / (2 * pMin) ≤ 1 / 4 := by
    rw [div_le_iff₀ hdenominator]
    nlinarith
  have hxiOne : delta / (2 * pMin) < 1 := by linarith
  have honeSub : 0 < 1 - delta / (2 * pMin) := sub_pos.mpr hxiOne
  have hxiLeLog :
      delta / (2 * pMin) ≤
        -Real.log (1 - delta / (2 * pMin)) := by
    have hlog :=
      Real.log_le_sub_one_of_pos honeSub
    linarith
  have hdeltaMul :
      delta * pMin ≤ delta := by
    nlinarith [mul_nonneg hdelta (sub_nonneg.mpr hpMinOne)]
  have hetaLeXi :
      delta / 2 ≤ delta / (2 * pMin) := by
    calc
      delta / 2 = (delta * pMin) / (2 * pMin) := by
        field_simp
      _ ≤ delta / (2 * pMin) :=
        div_le_div_of_nonneg_right hdeltaMul hdenominator.le
  have hlogLeRatio :
      -Real.log (1 - delta / (2 * pMin)) ≤
        (delta / (2 * pMin)) / (1 - delta / (2 * pMin)) :=
    neg_log_one_sub_le_ratio hxiNonnegative hxiOne
  have hratioLeFourThirds :
      (delta / (2 * pMin)) / (1 - delta / (2 * pMin)) ≤
        4 * (delta / (2 * pMin)) / 3 := by
    rw [div_le_iff₀ honeSub]
    nlinarith
  constructor
  · linarith
  · constructor
    · linarith
    · constructor
      · exact hlogLeRatio
      · constructor
        · exact hratioLeFourThirds
        · field_simp
          ring

/-- The effective-color numerator is at least the total class size. -/
theorem sum_le_effective_color_numerator
    (classes : Finset ι) (size : ι → ℝ)
    (hsize : ∀ i ∈ classes, 0 ≤ size i) :
    ∑ i ∈ classes, size i ≤ (∑ i ∈ classes, Real.sqrt (size i)) ^ 2 := by
  calc
    ∑ i ∈ classes, size i = ∑ i ∈ classes, (Real.sqrt (size i)) ^ 2 := by
      apply Finset.sum_congr rfl
      intro i hi
      exact (Real.sq_sqrt (hsize i hi)).symm
    _ ≤ (∑ i ∈ classes, Real.sqrt (size i)) ^ 2 :=
      Finset.sum_sq_le_sq_sum_of_nonneg fun i _ => Real.sqrt_nonneg (size i)

/-- The effective-color numerator is at most the number of occupied classes times their total
size. -/
theorem effective_color_numerator_le_card_mul_sum
    (classes : Finset ι) (size : ι → ℝ)
    (hsize : ∀ i ∈ classes, 0 ≤ size i) :
    (∑ i ∈ classes, Real.sqrt (size i)) ^ 2 ≤
      classes.card * ∑ i ∈ classes, size i := by
  have hcs := Finset.sum_mul_sq_le_sq_mul_sq classes
    (fun i => Real.sqrt (size i)) (fun _ => (1 : ℝ))
  have hsquares :
      (∑ i ∈ classes, (Real.sqrt (size i)) ^ 2) = ∑ i ∈ classes, size i := by
    apply Finset.sum_congr rfl
    intro i hi
    exact Real.sq_sqrt (hsize i hi)
  rw [hsquares] at hcs
  simpa [mul_comm] using hcs

/-- If the total class size is positive, the normalized effective-color factor lies between one
and the number of occupied classes. -/
theorem effective_color_factor_bounds
    (classes : Finset ι) (size : ι → ℝ)
    (hsize : ∀ i ∈ classes, 0 ≤ size i)
    (htotal : 0 < ∑ i ∈ classes, size i) :
    1 ≤ (∑ i ∈ classes, Real.sqrt (size i)) ^ 2 /
          (∑ i ∈ classes, size i) ∧
      (∑ i ∈ classes, Real.sqrt (size i)) ^ 2 /
          (∑ i ∈ classes, size i) ≤ classes.card := by
  constructor
  · rw [le_div_iff₀ htotal]
    simpa using sum_le_effective_color_numerator classes size hsize
  · rw [div_le_iff₀ htotal]
    exact effective_color_numerator_le_card_mul_sum classes size hsize

/-- A fixed linear row multiplies a coordinatewise error bound by its absolute row sum. -/
theorem abs_linear_row_le_abs_row_sum
    (indices : Finset ι) (coefficient error : ι → ℝ) {modulus : ℝ}
    (herror : ∀ i ∈ indices, |error i| ≤ modulus) :
    |∑ i ∈ indices, coefficient i * error i| ≤
      (∑ i ∈ indices, |coefficient i|) * modulus := by
  calc
    |∑ i ∈ indices, coefficient i * error i|
        ≤ ∑ i ∈ indices, |coefficient i * error i| :=
          Finset.abs_sum_le_sum_abs (f := fun i => coefficient i * error i) indices
    _ = ∑ i ∈ indices, |coefficient i| * |error i| := by
      apply Finset.sum_congr rfl
      intro i _
      exact abs_mul (coefficient i) (error i)
    _ ≤ ∑ i ∈ indices, |coefficient i| * modulus := by
      gcongr with i hi
      exact herror i hi
    _ = (∑ i ∈ indices, |coefficient i|) * modulus := by
      rw [Finset.sum_mul]

/-- A finite weighted average changes by at most the sum of a coordinatewise value bound and an
`L1` weight-change bound times a uniform bound on the reference values. This is a generic
deterministic result. It does not identify the values or weights with a PID construction. -/
theorem abs_weighted_average_change_le
    (indices : Finset ι)
    (pWeight qWeight valueP valueQ : ι → ℝ)
    {pointwiseBound weightBound delta : ℝ}
    (hqNonnegative : ∀ i ∈ indices, 0 ≤ qWeight i)
    (hqSum : ∑ i ∈ indices, qWeight i = 1)
    (_hpointwiseBoundNonnegative : 0 ≤ pointwiseBound)
    (hweightBoundNonnegative : 0 ≤ weightBound)
    (_hdeltaNonnegative : 0 ≤ delta)
    (hvalueChange :
      ∀ i ∈ indices, |valueQ i - valueP i| ≤ pointwiseBound)
    (hvalueP : ∀ i ∈ indices, |valueP i| ≤ weightBound)
    (hweightChange :
      ∑ i ∈ indices, |qWeight i - pWeight i| ≤ delta) :
    |(∑ i ∈ indices, qWeight i * valueQ i) -
        ∑ i ∈ indices, pWeight i * valueP i| ≤
      pointwiseBound + delta * weightBound := by
  have hdecomposition :
      (∑ i ∈ indices, qWeight i * valueQ i) -
          ∑ i ∈ indices, pWeight i * valueP i =
        (∑ i ∈ indices, qWeight i * (valueQ i - valueP i)) +
          ∑ i ∈ indices, (qWeight i - pWeight i) * valueP i := by
    rw [← Finset.sum_sub_distrib, ← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro i _
    ring
  have hvalueTerm :
      |∑ i ∈ indices, qWeight i * (valueQ i - valueP i)| ≤
        pointwiseBound := by
    calc
      |∑ i ∈ indices, qWeight i * (valueQ i - valueP i)|
          ≤ ∑ i ∈ indices, |qWeight i * (valueQ i - valueP i)| :=
            Finset.abs_sum_le_sum_abs
              (f := fun i => qWeight i * (valueQ i - valueP i)) indices
      _ = ∑ i ∈ indices, qWeight i * |valueQ i - valueP i| := by
        apply Finset.sum_congr rfl
        intro i hi
        rw [abs_mul, abs_of_nonneg (hqNonnegative i hi)]
      _ ≤ ∑ i ∈ indices, qWeight i * pointwiseBound := by
        apply Finset.sum_le_sum
        intro i hi
        exact mul_le_mul_of_nonneg_left
          (hvalueChange i hi) (hqNonnegative i hi)
      _ = pointwiseBound := by
        rw [← Finset.sum_mul, hqSum, one_mul]
  have hweightTerm :
      |∑ i ∈ indices, (qWeight i - pWeight i) * valueP i| ≤
        delta * weightBound := by
    calc
      |∑ i ∈ indices, (qWeight i - pWeight i) * valueP i|
          ≤ ∑ i ∈ indices, |(qWeight i - pWeight i) * valueP i| :=
            Finset.abs_sum_le_sum_abs
              (f := fun i => (qWeight i - pWeight i) * valueP i) indices
      _ = ∑ i ∈ indices, |qWeight i - pWeight i| * |valueP i| := by
        apply Finset.sum_congr rfl
        intro i _
        exact abs_mul (qWeight i - pWeight i) (valueP i)
      _ ≤ ∑ i ∈ indices, |qWeight i - pWeight i| * weightBound := by
        gcongr with i hi
        exact hvalueP i hi
      _ = (∑ i ∈ indices, |qWeight i - pWeight i|) * weightBound := by
        rw [Finset.sum_mul]
      _ ≤ delta * weightBound :=
        mul_le_mul_of_nonneg_right hweightChange hweightBoundNonnegative
  rw [hdecomposition]
  exact (abs_add_le _ _).trans (add_le_add hvalueTerm hweightTerm)

/-- Equal-total finite weights cancel the midpoint of a bounded reference-value interval. Their
signed weight term is therefore bounded by `L1 weight change * half the interval width`.
Nonnegativity of the weights is not needed for this stronger generic signed-vector statement. -/
theorem abs_weight_change_against_bounded_values_le_half_range
    (indices : Finset ι)
    (pWeight qWeight valueP : ι → ℝ)
    {lower upper delta : ℝ}
    (hpSum : ∑ i ∈ indices, pWeight i = 1)
    (hqSum : ∑ i ∈ indices, qWeight i = 1)
    (hlowerUpper : lower ≤ upper)
    (_hdeltaNonnegative : 0 ≤ delta)
    (hvalueRange :
      ∀ i ∈ indices, lower ≤ valueP i ∧ valueP i ≤ upper)
    (hweightChange :
      ∑ i ∈ indices, |qWeight i - pWeight i| ≤ delta) :
    |∑ i ∈ indices, (qWeight i - pWeight i) * valueP i| ≤
      delta * (upper - lower) / 2 := by
  have hweightDifferenceSum :
      ∑ i ∈ indices, (qWeight i - pWeight i) = 0 := by
    rw [Finset.sum_sub_distrib, hqSum, hpSum]
    norm_num
  have hcenteredValue :
      ∀ i ∈ indices,
        |valueP i - (lower + upper) / 2| ≤ (upper - lower) / 2 := by
    intro i hi
    rw [abs_le]
    constructor <;> linarith [hvalueRange i hi]
  have hhalfRangeNonnegative : 0 ≤ (upper - lower) / 2 := by
    linarith
  have hcenter :
      (∑ i ∈ indices, (qWeight i - pWeight i) * valueP i) =
        ∑ i ∈ indices,
          (qWeight i - pWeight i) *
            (valueP i - (lower + upper) / 2) := by
    calc
      (∑ i ∈ indices, (qWeight i - pWeight i) * valueP i) =
          ∑ i ∈ indices,
            ((qWeight i - pWeight i) *
                (valueP i - (lower + upper) / 2) +
              (qWeight i - pWeight i) * ((lower + upper) / 2)) := by
        apply Finset.sum_congr rfl
        intro i _
        ring
      _ =
          (∑ i ∈ indices,
            (qWeight i - pWeight i) *
              (valueP i - (lower + upper) / 2)) +
          ∑ i ∈ indices,
            (qWeight i - pWeight i) * ((lower + upper) / 2) :=
        Finset.sum_add_distrib
      _ =
          (∑ i ∈ indices,
            (qWeight i - pWeight i) *
              (valueP i - (lower + upper) / 2)) +
          (∑ i ∈ indices, (qWeight i - pWeight i)) *
            ((lower + upper) / 2) := by
        rw [Finset.sum_mul]
      _ =
          ∑ i ∈ indices,
            (qWeight i - pWeight i) *
              (valueP i - (lower + upper) / 2) := by
        rw [hweightDifferenceSum, zero_mul, add_zero]
  rw [hcenter]
  calc
    |∑ i ∈ indices,
        (qWeight i - pWeight i) *
          (valueP i - (lower + upper) / 2)|
        ≤ ∑ i ∈ indices,
            |(qWeight i - pWeight i) *
              (valueP i - (lower + upper) / 2)| :=
          Finset.abs_sum_le_sum_abs
            (f := fun i =>
              (qWeight i - pWeight i) *
                (valueP i - (lower + upper) / 2)) indices
    _ =
        ∑ i ∈ indices,
          |qWeight i - pWeight i| *
            |valueP i - (lower + upper) / 2| := by
      apply Finset.sum_congr rfl
      intro i _
      exact abs_mul
        (qWeight i - pWeight i) (valueP i - (lower + upper) / 2)
    _ ≤
        ∑ i ∈ indices,
          |qWeight i - pWeight i| * ((upper - lower) / 2) := by
      apply Finset.sum_le_sum
      intro i hi
      exact mul_le_mul_of_nonneg_left
        (hcenteredValue i hi) (abs_nonneg (qWeight i - pWeight i))
    _ =
        (∑ i ∈ indices, |qWeight i - pWeight i|) *
          ((upper - lower) / 2) := by
      rw [Finset.sum_mul]
    _ ≤ delta * ((upper - lower) / 2) :=
      mul_le_mul_of_nonneg_right hweightChange hhalfRangeNonnegative
    _ = delta * (upper - lower) / 2 := by ring

/-- A finite weighted average combines a coordinatewise value perturbation with the sharper
half-range weight perturbation. This is a generic deterministic result and does not identify the
values or weights with a PID construction. -/
theorem abs_weighted_average_change_le_pointwise_plus_half_range
    (indices : Finset ι)
    (pWeight qWeight valueP valueQ : ι → ℝ)
    {lower upper pointwiseBound delta : ℝ}
    (hqNonnegative : ∀ i ∈ indices, 0 ≤ qWeight i)
    (hpSum : ∑ i ∈ indices, pWeight i = 1)
    (hqSum : ∑ i ∈ indices, qWeight i = 1)
    (hlowerUpper : lower ≤ upper)
    (_hpointwiseBoundNonnegative : 0 ≤ pointwiseBound)
    (hdeltaNonnegative : 0 ≤ delta)
    (hvalueChange :
      ∀ i ∈ indices, |valueQ i - valueP i| ≤ pointwiseBound)
    (hvaluePRange :
      ∀ i ∈ indices, lower ≤ valueP i ∧ valueP i ≤ upper)
    (hweightChange :
      ∑ i ∈ indices, |qWeight i - pWeight i| ≤ delta) :
    |(∑ i ∈ indices, qWeight i * valueQ i) -
        ∑ i ∈ indices, pWeight i * valueP i| ≤
      pointwiseBound + delta * (upper - lower) / 2 := by
  have hdecomposition :
      (∑ i ∈ indices, qWeight i * valueQ i) -
          ∑ i ∈ indices, pWeight i * valueP i =
        (∑ i ∈ indices, qWeight i * (valueQ i - valueP i)) +
          ∑ i ∈ indices, (qWeight i - pWeight i) * valueP i := by
    rw [← Finset.sum_sub_distrib, ← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro i _
    ring
  have hvalueTerm :
      |∑ i ∈ indices, qWeight i * (valueQ i - valueP i)| ≤
        pointwiseBound := by
    calc
      |∑ i ∈ indices, qWeight i * (valueQ i - valueP i)|
          ≤ ∑ i ∈ indices, |qWeight i * (valueQ i - valueP i)| :=
            Finset.abs_sum_le_sum_abs
              (f := fun i => qWeight i * (valueQ i - valueP i)) indices
      _ = ∑ i ∈ indices, qWeight i * |valueQ i - valueP i| := by
        apply Finset.sum_congr rfl
        intro i hi
        rw [abs_mul, abs_of_nonneg (hqNonnegative i hi)]
      _ ≤ ∑ i ∈ indices, qWeight i * pointwiseBound := by
        apply Finset.sum_le_sum
        intro i hi
        exact mul_le_mul_of_nonneg_left
          (hvalueChange i hi) (hqNonnegative i hi)
      _ = pointwiseBound := by
        rw [← Finset.sum_mul, hqSum, one_mul]
  have hweightTerm :
      |∑ i ∈ indices, (qWeight i - pWeight i) * valueP i| ≤
        delta * (upper - lower) / 2 :=
    abs_weight_change_against_bounded_values_le_half_range
      indices pWeight qWeight valueP hpSum hqSum hlowerUpper
      hdeltaNonnegative hvaluePRange hweightChange
  rw [hdecomposition]
  exact (abs_add_le _ _).trans (add_le_add hvalueTerm hweightTerm)

/-- The first `count` terms of `1 / (n(n+1))`, indexed from `n = 1`, telescope exactly. -/
theorem telescoping_anytime_spending (count : ℕ) :
    (∑ k ∈ Finset.range count,
      (1 : ℝ) / ((k + 1 : ℕ) * (k + 2 : ℕ))) =
      1 - 1 / (count + 1 : ℕ) := by
  induction count with
  | zero => norm_num
  | succ count ih =>
      rw [Finset.sum_range_succ, ih]
      push_cast
      have hcount : (0 : ℝ) < count + 1 := by positivity
      have hnext : (0 : ℝ) < count + 2 := by positivity
      field_simp
      ring

/-- Every finite prefix of the anytime-error allocation spends at most one unit. -/
theorem telescoping_anytime_spending_le_one (count : ℕ) :
    (∑ k ∈ Finset.range count,
      (1 : ℝ) / ((k + 1 : ℕ) * (k + 2 : ℕ))) ≤ 1 := by
  rw [telescoping_anytime_spending]
  have hnonneg : 0 ≤ (1 : ℝ) / (count + 1 : ℕ) := by positivity
  linarith

/-- Substituting the un-clipped radius into the Chernoff exponent cancels to the selected log
budget. -/
theorem concentration_radius_exponent_cancels
    {sampleSize proxy logBudget : ℝ}
    (hsample : sampleSize ≠ 0) (hproxy : proxy ≠ 0) :
    -(sampleSize ^ 2 * ((2 * proxy / sampleSize ^ 2) * logBudget)) /
        (2 * proxy) = -logBudget := by
  field_simp

end PidFiniteConvergence
