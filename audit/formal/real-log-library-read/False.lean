module
public import Mathlib.Analysis.SpecialFunctions.Log.Deriv

example : (1 : ℝ) < 0 := by
  exact (show (0 : ℝ) < 1 from zero_lt_one)
