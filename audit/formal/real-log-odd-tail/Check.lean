module
public import Proof

set_option autoImplicit false

public section

open Finset

namespace PIDRealTail

theorem fullStatement (n : ℕ) (x : ℝ) (hx : 0 ≤ x) (h1 : x < 1) :
    let h := (1 / 2 : ℝ) * Real.log ((1 + x) / (1 - x)) -
      ∑ i ∈ range n, x ^ (2 * i + 1) / (2 * (i : ℝ) + 1)
    let u := x ^ (2 * n + 1) / ((2 * (n : ℝ) + 1) * (1 - x ^ 2))
    (0 ≤ h ∧ h ≤ u) ∧ (0 < x → 0 < h ∧ h < u) := by
  exact ⟨⟨(sharp n hx h1).1, (sharp n hx h1).2.1⟩, (sharp n hx h1).2.2⟩

theorem equalityAtZero (n : ℕ) : halfTail n 0 = 0 ∧ upper n 0 = 0 := by
  simp [halfTail, upper]

theorem atOneThird : 0 < halfTail 1 ((1 : ℝ) / 3) ∧
    halfTail 1 ((1 : ℝ) / 3) < upper 1 ((1 : ℝ) / 3) := by
  exact (sharp (x := (1 : ℝ) / 3) 1 (by norm_num) (by norm_num)).2.2 (by norm_num)

theorem tooSmallAtHalf :
    ((1 : ℝ) / 2) ^ 3 / (4 * (1 - ((1 : ℝ) / 2) ^ 2)) < halfTail 1 ((1 : ℝ) / 2) := by
  have hl := Real.sum_range_le_log_div (x := (1 : ℝ) / 2) (by norm_num) (by norm_num) 3
  norm_num [halfTail, Finset.sum_range_succ] at hl ⊢
  linarith

set_option pp.fullNames true
#print PIDRealTail.halfTail
#print PIDRealTail.upper
#check @PIDRealTail.sharp
#print PIDRealTail.fullStatement
#print PIDRealTail.equalityAtZero
#print PIDRealTail.atOneThird
#print PIDRealTail.tooSmallAtHalf
#print axioms PIDRealTail.sharp
#print axioms PIDRealTail.fullStatement
#print axioms PIDRealTail.equalityAtZero
#print axioms PIDRealTail.atOneThird
#print axioms PIDRealTail.tooSmallAtHalf

end PIDRealTail
