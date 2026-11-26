prelude
import Init.Tactics
import Init.Omega
import Init.Data.Int.DivMod.Lemmas

namespace SignedGrid

/-- Signed ceiling on a positive divisor, as used by the original Python routine. -/
def up (x d : Int) : Int := -((-x) / d)

/-- The returned integer indices are l / d and up u d. -/
def width (l u d : Int) : Int := up u d - l / d

/-- Both inclusive, ordered intervals overlap, in the numerator's raw units. -/
def overlap (l u a b d : Int) : Prop := l ≤ u ∧ a ≤ b ∧ l ≤ b * d ∧ a * d ≤ u

/-- Width bound before the final rounding for at most 1024 occupied states. -/
def bitDivisor (n : Int) : Int := n * 16777216

end SignedGrid
