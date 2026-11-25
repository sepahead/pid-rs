prelude
import Init.Tactics
import Init.ByCases
import Init.Omega
import Init.Data.List.Count
import Init.Data.List.Lemmas
import Init.Data.Nat.Order
import Init.Data.Nat.MinMax

namespace W7

structure Row where
  left : Nat
  right : Nat
  target : Nat
  deriving DecidableEq, Repr

def source (v : Row) : Nat := min v.left v.right
def joint (v : Row) : Nat := max (source v) v.target
def src (r : Nat) (v : Row) : Bool := decide (source v < r)
def tgt (r : Nat) (v : Row) : Bool := decide (v.target < r)
def inner (r : Nat) (v : Row) : Bool := decide (joint v < r)
def edge (r : Nat) (v : Row) : Bool := decide (joint v = r)

def Realizes (rows : List Row) (r k x y : Nat) : Prop :=
  0 < r ∧ rows.countP (inner r) + 1 = k ∧ rows.countP (edge r) = 1 ∧
  rows.countP (src r) + 1 = x ∧ rows.countP (tgt r) + 1 = y

instance (rows : List Row) (r k x y : Nat) : Decidable (Realizes rows r k x y) :=
  inferInstanceAs (Decidable (0 < r ∧ rows.countP (inner r) + 1 = k ∧ rows.countP (edge r) = 1 ∧
    rows.countP (src r) + 1 = x ∧ rows.countP (tgt r) + 1 = y))

def Triangle (n k x y : Nat) : Prop :=
  k ≤ x ∧ x ≤ n ∧ k ≤ y ∧ y ≤ n ∧ x + y ≤ n + k

def outside (p q d : Nat) : List Row :=
  List.replicate p ⟨4,1,3⟩ ++ List.replicate q ⟨3,4,1⟩ ++ List.replicate d ⟨4,3,3⟩

def boundary : Nat → Nat → Nat → List Row
  | p + 1, q, d => ⟨4,1,2⟩ :: outside p q d
  | 0, q + 1, d => ⟨2,4,1⟩ :: outside 0 q d
  | 0, 0, d + 1 => ⟨4,2,2⟩ :: outside 0 0 d
  | 0, 0, 0 => []

def witness (h p q d : Nat) : List Row :=
  List.replicate h ⟨1,4,1⟩ ++ boundary p q d

end W7
