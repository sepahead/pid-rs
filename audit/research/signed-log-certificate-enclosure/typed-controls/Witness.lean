prelude
import Proof
open N2 N2Round

example : (loopState 1 3 4 1).hi = 2 := by decide +kernel
example : up 16 27 = 1 := by decide +kernel
example : (loopState 1 3 4 1).hi ≠ up 16 27 := by decide +kernel
example : returned 1 3 4 = (10,16) := by decide +kernel
example : returned 1 3 4 ≠ (10,15) := by decide +kernel
example : 10 * 1215 ≤ 13472 ∧ 13472 + 1215 ≤ 15 * 1215 := by decide +kernel
example : returned 0 3 0 = (0,0) := by decide +kernel
example : (0 : Int) = -((- (0 : Int)) / 3) := by decide +kernel
example : DivisionClaim := signed_ceiling
