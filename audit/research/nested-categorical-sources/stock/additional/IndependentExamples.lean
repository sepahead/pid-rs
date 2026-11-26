prelude
import Observer
open Nested

namespace IndependentExamples

def fibre (i : Nat) (w : Fin 5) : Prop := w.val + i ≤ 4

theorem decreases (w : Fin 5) : Decreases (fun i => fibre i w) := by
  intro i j hij hj
  change w.val + j ≤ 4 at hj
  change w.val + i ≤ 4
  omega

example : (fun w : Fin 5 => four.holds (fun i => fibre i w)) = fibre 3 := by
  exact event_extensional fibre decreases four

example : four.holds (fun i => fibre i (1 : Fin 5)) := by
  change (1 + 1 ≤ 4 ∧ 1 + 4 ≤ 4) ∨ (1 + 2 ≤ 4 ∧ 1 + 3 ≤ 4)
  decide +kernel

example : ¬ fibre 4 (1 : Fin 5) := by
  change ¬ (1 + 4 ≤ 4)
  decide +kernel

example : ¬ four.holds (fun i => fibre i (2 : Fin 5)) := by
  change ¬ ((2 + 1 ≤ 4 ∧ 2 + 4 ≤ 4) ∨ (2 + 2 ≤ 4 ∧ 2 + 3 ≤ 4))
  decide +kernel

example : fibre 2 (2 : Fin 5) := by
  change 2 + 2 ≤ 4
  decide +kernel

example : ¬ four.holds (fun i => i = 3) ∧ (four.level = 3) := by
  change ¬ ((1 = 3 ∧ 4 = 3) ∨ (2 = 3 ∧ 3 = 3)) ∧ 3 = 3
  decide +kernel

def values (i : Nat) : Int :=
  if i = 0 then 7 else if i = 1 then 2 else if i = 2 then 8 else 1

example : prefixSum values four.level = -6 := by decide +kernel
example : prefixSum values four.level ≠ values four.level := by decide +kernel
end IndependentExamples
