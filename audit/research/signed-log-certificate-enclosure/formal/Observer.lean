prelude
import Proof
open N2 N2Round
example : DivisionClaim := signed_ceiling
example : Statement := scheduled
example (n d s i : Nat) (hd : 0 < d) : enclosedPrefix n d s i := all_prefixes n d s i hd
example : (loopState 1 3 2 0).lo = 1 := by decide +kernel
example : (loopState 1 3 2 0).hi = 2 := by decide +kernel
example : (loopState 1 3 2 1).lo = 0 := by decide +kernel
example : (loopState 1 3 2 1).hi = 1 := by decide +kernel
example : (loopState 1 3 2 1).sumLo = 2 := by decide +kernel
example : (loopState 1 3 2 1).sumHi = 4 := by decide +kernel
example : partialSum 1 3 2 = (168, 243) := by decide +kernel
example : up 6 3 = 2 := by decide +kernel
example : up 7 3 = 3 := by decide +kernel
example : up 0 9 = 0 := by decide +kernel
example : (returned 1 3 2).2 = 6 := by decide +kernel
example : enclosedPrefix 4 1 0 2 := all_prefixes 4 1 0 2 (by decide)
example : returned 0 3 3 = (0, 0) := by decide +kernel
example : returned 1 3 2 = (2, 6) := by decide +kernel
example : returned 1 3 3 = (4, 8) := by decide +kernel
example : returned 1 5 8 = (102, 109) := by decide +kernel
example : returned 2 9 4 = (6, 11) := by decide +kernel
example : returned 1 4 2 = (2, 4) := by decide +kernel
example : returned 5 16 7 = (82, 87) := by decide +kernel

set_option pp.proofs true
set_option pp.deepTerms true
set_option pp.maxSteps 3000000
#print axioms N2Round.ceil_upper
#print axioms N2Round.signed_ceiling
#print axioms N2Round.initial_interval
#print axioms N2Round.product_lower
#print axioms N2Round.product_upper
#print axioms N2Round.product_interval
#print axioms N2Round.term_interval
#print axioms N2Round.add_interval
#print axioms N2Round.square_steps
#print axioms N2Round.odd_power_step
#print axioms N2Round.all_prefixes
#print axioms N2Round.returned_finite
#print axioms N2Round.scheduled
#print N2Round.ceil_upper
#print N2Round.signed_ceiling
#print N2Round.initial_interval
#print N2Round.product_lower
#print N2Round.product_upper
#print N2Round.product_interval
#print N2Round.term_interval
#print N2Round.add_interval
#print N2Round.square_steps
#print N2Round.odd_power_step
#print N2Round.all_prefixes
#print N2Round.returned_finite
#print N2Round.scheduled
