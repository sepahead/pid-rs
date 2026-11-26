prelude
import Proof
open N2

example : (loopState 1 3 4 1).hi = up 16 27 := by decide +kernel
