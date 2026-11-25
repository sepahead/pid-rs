module
public import Mathlib.Analysis.SpecialFunctions.Log.Deriv

set_option autoImplicit false

@[expose] public section

open Finset

namespace PIDRealTail

noncomputable def halfTail (n : ℕ) (x : ℝ) : ℝ :=
  (1 / 2 : ℝ) * Real.log ((1 + x) / (1 - x)) -
    ∑ i ∈ range n, x ^ (2 * i + 1) / (2 * (i : ℝ) + 1)

noncomputable def upper (n : ℕ) (x : ℝ) : ℝ :=
  x ^ (2 * n + 1) / ((2 * (n : ℝ) + 1) * (1 - x ^ 2))

end PIDRealTail
