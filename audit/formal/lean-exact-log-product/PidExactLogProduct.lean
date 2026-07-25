import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic

/-!
# Exact multiplicative normalization of finite log expressions

This standalone module proves the representation theorem used by the bounded categorical SxPID2
exact-product checker. It deliberately does not define a PID measure. Only after the
Makkeh--Gutknecht--Wibral source-event unions, target intersections, empirical weights, and
integer Möbius matrix have been fixed does the executable checker instantiate this generic result.

The module proves that a finite integer linear combination of logarithms is the logarithm of an
exact signed-power product. A positive scaling by `1 / n` preserves exact sign, and the scaled
value is zero exactly when the product is one.

The formal boundary is strict: this file does not prove the SxPID event extraction, the concrete
two-source lattice matrix, Rust or Python refinement, data or sampling assumptions, estimator
calibration, or any property of another PID definition.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators

namespace PidExactLogProduct

variable {ι : Type*}

/-- The logarithm turns a finite product with signed integer exponents into the corresponding
integer linear combination of logarithms. -/
theorem log_finset_zpow_product (indices : Finset ι) (argument : ι → ℝ)
    (exponent : ι → ℤ) (hpositive : ∀ i ∈ indices, 0 < argument i) :
    Real.log (∏ i ∈ indices, argument i ^ exponent i) =
      ∑ i ∈ indices, (exponent i : ℝ) * Real.log (argument i) := by
  calc
    Real.log (∏ i ∈ indices, argument i ^ exponent i) =
        ∑ i ∈ indices, Real.log (argument i ^ exponent i) := by
      apply Real.log_prod
      intro i hi
      exact zpow_ne_zero _ (hpositive i hi).ne'
    _ = ∑ i ∈ indices, (exponent i : ℝ) * Real.log (argument i) := by
      apply Finset.sum_congr rfl
      intro i _
      exact Real.log_zpow (argument i) (exponent i)

/-- Any finite exact log expression whose coefficients become integers after multiplication by
`n` equals `log R / n`, where `R` is the exact signed-power product. -/
theorem scaled_log_sum_eq_log_product (indices : Finset ι) (argument : ι → ℝ)
    (exponent : ι → ℤ) (n : ℕ) (hpositive : ∀ i ∈ indices, 0 < argument i) :
    (1 / (n : ℝ)) *
        (∑ i ∈ indices, (exponent i : ℝ) * Real.log (argument i)) =
      (1 / (n : ℝ)) * Real.log (∏ i ∈ indices, argument i ^ exponent i) := by
  rw [log_finset_zpow_product indices argument exponent hpositive]

/-- A positive exact product gives a positive scaled logarithm exactly when it exceeds one. -/
theorem scaled_log_pos_iff {product : ℝ} {n : ℕ}
    (hproduct : 0 < product) (hn : 0 < n) :
    0 < (1 / (n : ℝ)) * Real.log product ↔ 1 < product := by
  have hscale : 0 < (1 / (n : ℝ)) := one_div_pos.mpr (Nat.cast_pos.mpr hn)
  rw [mul_pos_iff_of_pos_left hscale, Real.log_pos_iff hproduct.le]

/-- A positive exact product gives a negative scaled logarithm exactly when it is below one. -/
theorem scaled_log_neg_iff {product : ℝ} {n : ℕ}
    (hproduct : 0 < product) (hn : 0 < n) :
    (1 / (n : ℝ)) * Real.log product < 0 ↔ product < 1 := by
  have hscale : 0 < (1 / (n : ℝ)) := one_div_pos.mpr (Nat.cast_pos.mpr hn)
  calc
    (1 / (n : ℝ)) * Real.log product < 0 ↔
        0 < -((1 / (n : ℝ)) * Real.log product) := neg_pos.symm
    _ ↔ 0 < (1 / (n : ℝ)) * (-Real.log product) := by ring_nf
    _ ↔ 0 < -Real.log product := mul_pos_iff_of_pos_left hscale
    _ ↔ Real.log product < 0 := neg_pos
    _ ↔ product < 1 := Real.log_neg_iff hproduct

/-- A positive exact product gives an exact-zero scaled logarithm exactly at product one. -/
theorem scaled_log_eq_zero_iff {product : ℝ} {n : ℕ}
    (hproduct : 0 < product) (hn : 0 < n) :
    (1 / (n : ℝ)) * Real.log product = 0 ↔ product = 1 := by
  have hnreal : (n : ℝ) ≠ 0 := (Nat.cast_pos.mpr hn).ne'
  have hscale : (1 / (n : ℝ)) ≠ 0 := one_div_ne_zero hnreal
  constructor
  · intro hzero
    have hlog : Real.log product = 0 := (mul_eq_zero.mp hzero).resolve_left hscale
    rcases Real.log_eq_zero.mp hlog with hproduct_zero | hproduct_one | hproduct_neg_one
    · exact (hproduct.ne' hproduct_zero).elim
    · exact hproduct_one
    · linarith
  · intro hproduct_one
    simp [hproduct_one]

/-- Syntactic nonemptiness is not a complete nonzero test: two positive, nonunit rational-style
log arguments can cancel through an exact reciprocal relation. -/
theorem two_nontrivial_logs_cancel {x : ℝ} (hpositive : 0 < x) (hne_one : x ≠ 1) :
    Real.log x + Real.log x⁻¹ = 0 ∧ 0 < x⁻¹ ∧ x ≠ 1 ∧ x⁻¹ ≠ 1 := by
  constructor
  · rw [Real.log_inv]
    ring
  · exact ⟨inv_pos.mpr hpositive, hne_one, inv_ne_one.mpr hne_one⟩

/-- The retained five-term empirical witness is an exact multiplicative cancellation, not a
floating-point coincidence.  This theorem checks the rational product used by the executable
`n = 8` counterexample; the separate exact-rational and Rust routes bind these factors to the
SxPID2 unique-one net atom. -/
theorem retained_five_term_product_eq_one :
    (8 / 15 : ℚ)⁻¹ * (4 / 5 : ℚ) * (8 / 9 : ℚ) * (4 / 3 : ℚ) * (16 / 9 : ℚ)⁻¹ = 1 := by
  norm_num

end PidExactLogProduct
