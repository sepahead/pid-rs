prelude
import Proof
open Nested

example (p : Nat → Prop) (h : Decreases p) (a : Node) :
    a.holds p ↔ p a.level := node_matches p h a
example (a : Node) (j : Nat) : a.covers j ↔ j ≤ a.level := suffix_incidence j a
example (s : Nat → Int) (a : Node) : prefixSum s a.level = s a.level - s 0 :=
  cumulative_sum s a

def mixed : Node := .either (.branch (.both (.one 1) (.one 3))) (.branch (.one 2))
example : mixed.level = 2 := by decide +kernel
example : mixed.covers 2 := by change (2 ≤ 1 ∨ 2 ≤ 3) ∧ 2 ≤ 2; decide +kernel
example : ¬ mixed.covers 3 := by change ¬ ((3 ≤ 1 ∨ 3 ≤ 3) ∧ 3 ≤ 2); decide +kernel
example : mixed.holds (fun i => i ≤ 2) := by
  change (1 ≤ 2 ∧ 3 ≤ 2) ∨ 2 ≤ 2
  decide +kernel
example : ¬ mixed.holds (fun i => i ≤ 1) := by
  change ¬ ((1 ≤ 1 ∧ 3 ≤ 1) ∨ 2 ≤ 1)
  decide +kernel
example : (.branch (.both (.one 1) (.one 1)) : Node).level = 1 := by decide +kernel
example : (Node.either (.branch (.one 4)) (.branch (.one 4))).level = 4 := by decide +kernel
example : (.branch (.one 0) : Node).level = 0 := by decide +kernel
example : ¬ mixed.holds (fun i => i = 3) := by
  change ¬ ((1 = 3 ∧ 3 = 3) ∨ 2 = 3)
  decide +kernel
example : (fun i : Nat => i = 3) (Branch.level (.both (.one 1) (.one 3))) := rfl
example : ¬ Branch.holds (fun i => i = 3) (.both (.one 1) (.one 3)) := by
  change ¬ (1 = 3 ∧ 3 = 3)
  decide +kernel
example : Decreases (fun i => i ≤ 2) := fun _ _ h₁ h₂ => Nat.le_trans h₁ h₂

def four : Node := .either (.branch (.both (.one 1) (.one 4))) (.branch (.both (.one 2) (.one 3)))
example : four.level = 3 := by decide +kernel
example : four.covers 3 := by
  change (3 ≤ 1 ∨ 3 ≤ 4) ∧ (3 ≤ 2 ∨ 3 ≤ 3)
  decide +kernel
example : ¬ four.covers 4 := by
  change ¬ ((4 ≤ 1 ∨ 4 ≤ 4) ∧ (4 ≤ 2 ∨ 4 ≤ 3))
  decide +kernel
example : four.holds (fun i => i ≤ 3) := by
  change (1 ≤ 3 ∧ 4 ≤ 3) ∨ (2 ≤ 3 ∧ 3 ≤ 3)
  decide +kernel
example : ¬ four.holds (fun i => i ≤ 2) := by
  change ¬ ((1 ≤ 2 ∧ 4 ≤ 2) ∨ (2 ≤ 2 ∧ 3 ≤ 2))
  decide +kernel

set_option pp.proofs true
set_option pp.deepTerms true
set_option pp.maxSteps 3000000
#print axioms Nested.branch_reaches
#print axioms Nested.suffix_incidence
#print axioms Nested.branch_matches
#print axioms Nested.node_matches
#print axioms Nested.event_extensional
#print axioms Nested.cumulative_sum
#print Nested.branch_reaches
#print Nested.suffix_incidence
#print Nested.branch_matches
#print Nested.node_matches
#print Nested.event_extensional
#print Nested.cumulative_sum
