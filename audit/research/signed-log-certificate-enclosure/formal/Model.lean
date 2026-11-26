prelude
import Init.Tactics
import Init.Omega
import Init.Data.Nat.Lemmas
import Init.Data.Int.DivMod.Lemmas
import Init.Data.List.Basic

/- Finite, positive-denominator natural model of the registered arithmetic.py loop. -/
namespace N2

def admitted (p : Nat) : Prop := p ∈ [256, 384, 512, 768, 1024, 1536, 2048]

def guardBits : Nat := 24

def internalBits (p : Nat) : Nat := p + guardBits

def scale (s : Nat) : Nat := 2 ^ s

/-- On a positive denominator, this is mathematical ceiling division on naturals. -/
def up (a b : Nat) : Nat := (a + (b - 1)) / b

def count (s : Nat) : Nat := up s 3 + 1

structure State where
  lo : Nat
  hi : Nat
  sumLo : Nat
  sumHi : Nat
  deriving DecidableEq, Repr

structure Steps where
  lo : Nat
  hi : Nat
  deriving DecidableEq, Repr

def start (n d s : Nat) : State :=
  let b := scale s
  ⟨n * b / d, up (n * b) d, 0, 0⟩

def steps (n d s : Nat) : Steps :=
  let b := scale s
  let x := start n d s
  ⟨x.lo * x.lo / b, up (x.hi * x.hi) b⟩

def advance (b : Nat) (h : Steps) (i : Nat) (x : State) : State :=
  let odd := 2 * i + 1
  ⟨x.lo * h.lo / b, up (x.hi * h.hi) b,
    x.sumLo + 2 * x.lo / odd, x.sumHi + up (2 * x.hi) odd⟩

def loopState (n d s : Nat) : Nat → State
  | 0 => start n d s
  | i + 1 => advance (scale s) (steps n d s) i (loopState n d s i)

/-- Exact numerator and strictly positive denominator for the finite odd partial sum.
The factors use the independent exponents n^(2i+1), d^(2i+1), and no rounded power state. -/
def partialSum (n d : Nat) : Nat → Nat × Nat
  | 0 => (0, 1)
  | i + 1 =>
    let prev := partialSum n d i
    let odd := 2 * i + 1
    let termDen := d ^ odd * odd
    (prev.1 * termDen + (2 * n ^ odd) * prev.2, prev.2 * termDen)

def enclosedPrefix (n d s i : Nat) : Prop :=
  let b := scale s
  let v := loopState n d s i
  let odd := 2 * i + 1
  let t := partialSum n d i
  0 < t.2 ∧ v.lo * d ^ odd ≤ b * n ^ odd ∧ b * n ^ odd ≤ v.hi * d ^ odd ∧
    v.sumLo * t.2 ≤ b * t.1 ∧ b * t.1 ≤ v.sumHi * t.2

def returned (n d s : Nat) : Nat × Nat :=
  if n = 0 then (0, 0) else
    let v := loopState n d s (count s)
    (v.sumLo, v.sumHi + 1)

def returnedClaim (n d s : Nat) : Prop :=
  let v := returned n d s
  let t := partialSum n d (count s)
  if n = 0 then v = (0, 0) else
    v.1 * t.2 ≤ scale s * t.1 ∧ scale s * t.1 + t.2 ≤ v.2 * t.2

/-- Nat.up must agree with the signed-floor expression in Python on this domain. -/
def DivisionClaim : Prop :=
  ∀ a b : Nat, 0 < b → ((up a b : Nat) : Int) = -((- (a : Int)) / (b : Int))

def PrefixClaim : Prop :=
  ∀ n d p : Nat, 0 < d → 3 * n ≤ d → admitted p →
    (∀ i : Nat, i ≤ count (internalBits p) → enclosedPrefix n d (internalBits p) i) ∧
      returnedClaim n d (internalBits p)

def Statement : Prop := DivisionClaim ∧ PrefixClaim

end N2
