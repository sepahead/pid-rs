module
public import Check

set_option autoImplicit false

public section

example : ¬ ((1 : ℝ) / 2) ^ 3 / (4 * (1 - ((1 : ℝ) / 2) ^ 2)) <
    PIDRealTail.halfTail 1 ((1 : ℝ) / 2) := by
  exact PIDRealTail.tooSmallAtHalf
