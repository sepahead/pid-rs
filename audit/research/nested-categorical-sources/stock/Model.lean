prelude
import Init.Tactics
import Init.ByCases
import Init.Omega
import Init.Data.Nat.MinMax
import Init.Data.Int.Order

namespace Nested

/-- A conjunction of one or more source matches. The indices identify source levels. -/
inductive Branch where
  | one : Nat → Branch
  | both : Branch → Branch → Branch
  deriving Repr

/-- A disjunction of one or more branches. -/
inductive Node where
  | branch : Branch → Node
  | either : Node → Node → Node
  deriving Repr

def Branch.level : Branch → Nat
  | .one i => i
  | .both a b => max a.level b.level

def Node.level : Node → Nat
  | .branch b => b.level
  | .either a b => min a.level b.level

/-- At an outcome, p i means that the level-i reading matches. -/
def Branch.holds (p : Nat → Prop) : Branch → Prop
  | .one i => p i
  | .both a b => a.holds p ∧ b.holds p

def Node.holds (p : Nat → Prop) : Node → Prop
  | .branch b => b.holds p
  | .either a b => a.holds p ∨ b.holds p

/-- At least one index in this branch belongs to the suffix starting at j. -/
def Branch.reaches (j : Nat) : Branch → Prop
  | .one i => j ≤ i
  | .both a b => a.reaches j ∨ b.reaches j

/-- Every branch of the node contains at least one member of the suffix. -/
def Node.covers (j : Nat) : Node → Prop
  | .branch b => b.reaches j
  | .either a b => a.covers j ∧ b.covers j

def Decreases (p : Nat → Prop) : Prop := ∀ i j : Nat, i ≤ j → p j → p i

def prefixSum (s : Nat → Int) : Nat → Int
  | 0 => 0
  | n+1 => prefixSum s n + (s (n+1) - s n)

end Nested
