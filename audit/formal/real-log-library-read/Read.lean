module
public import Mathlib.Analysis.SpecialFunctions.Log.Deriv

set_option autoImplicit false

public section
open Finset Real
namespace PIDLogLibrary

theorem lower {x : ℝ} (h₀ : 0 ≤ x) (h : x < 1) (n : ℕ) :
    ∑ i ∈ range n, x ^ (2 * i + 1) / (2 * i + 1) ≤ (1 / 2 : ℝ) * log ((1 + x) / (1 - x)) :=
  Real.sum_range_le_log_div h₀ h n

theorem upper {x : ℝ} (h₀ : 0 ≤ x) (h : x < 1) (n : ℕ) :
    (1 / 2 : ℝ) * log ((1 + x) / (1 - x)) ≤
      (∑ i ∈ range n, x ^ (2 * i + 1) / (2 * i + 1)) + x ^ (2 * n + 1) / (1 - x ^ 2) :=
  Real.log_div_le_sum_range_add h₀ h n

end PIDLogLibrary

set_option pp.fullNames true
set_option pp.deepTerms true
set_option pp.proofs true
set_option pp.maxSteps 1000000
#print PIDLogLibrary.lower
#print PIDLogLibrary.upper
#check @PIDLogLibrary.lower
#check @Real.sum_range_le_log_div
#check @PIDLogLibrary.upper
#check @Real.log_div_le_sum_range_add
#print axioms PIDLogLibrary.lower
#print axioms PIDLogLibrary.upper
#print axioms Real.sum_range_le_log_div
#print axioms Real.log_div_le_sum_range_add
