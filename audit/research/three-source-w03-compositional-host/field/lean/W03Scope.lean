import W03Literal
import ProjectionCore

set_option autoImplicit false
set_option maxRecDepth 65536
namespace W03Scope
open SmtW02

abbrev Family := Fin 128
abbrev Mask := Fin 8
abbrev SourceValuation := Valuation originalScript

def slot : Fin (declarations originalScript).length := ⟨0, by decide⟩
def family (v : SourceValuation) : Family := (v slot).toFin
def extend (x : Family) : SourceValuation :=
  ArchivedProjection.put originalScript slot (BitVec.ofFin x) (zeroValuation originalScript)

def masks : List Nat := [1, 2, 3, 4, 5, 6, 7]
def member (f : Family) (u : Nat) : Bool := u != 0 && f.val.testBit (u - 1)
def subsetMask (u v : Nat) : Bool := Nat.land u v == u
def incomparable (f : Family) : Bool :=
  masks.all (fun u => masks.all (fun v => !(decide (u < v) && member f u && member f v &&
    (subsetMask u v || subsetMask v u))))
def valid (f : Family) : Bool := f.val != 0 && incomparable f
def order (a b : Family) : Bool :=
  masks.all (fun v => !(member b v) || masks.any (fun u => member a u && subsetMask u v))

def selected : List Cmd := [27, 28, 29, 30, 32].filterMap (fun i => originalScript[i]?)
def small : Option DynamicState := selected.foldlM (dynamicStep (fun _ => none)) {}
def full (v : SourceValuation) : Option DynamicState := do
  let cmds ← currentCommands originalScript
  (cmds.take 82).foldlM (dynamicStep (valuationLookup (declarations originalScript) v)) {}

def invoke (s : Option DynamicState) (name : String) (args : List Value) : Option Bool := do
  let st ← s
  let f ← st.globals.lookup name
  let answer ← f args
  answer.getBool

def maskArg (u : Mask) : Value := .bits 3 u.val
def familyArg (a : Family) : Value := .bits 7 a.val

def callsAgree (l r : Option DynamicState) : Prop :=
  (∀ u v : Mask, invoke l "sub" [maskArg u, maskArg v] = invoke r "sub" [maskArg u, maskArg v]) ∧
  (∀ (a : Family) (u : Mask), invoke l "has" [familyArg a, maskArg u] = invoke r "has" [familyArg a, maskArg u]) ∧
  (∀ a : Family, invoke l "incomparable" [familyArg a] = invoke r "incomparable" [familyArg a]) ∧
  (∀ a : Family, invoke l "valid" [familyArg a] = invoke r "valid" [familyArg a]) ∧
  (∀ a b : Family, invoke l "leq" [familyArg a, familyArg b] = invoke r "leq" [familyArg a, familyArg b])

def Meaning : Prop :=
  (∀ u v : Mask, invoke small "sub" [maskArg u, maskArg v] = some (subsetMask u.val v.val)) ∧
  (∀ (a : Family) (u : Mask), invoke small "has" [familyArg a, maskArg u] = some (member a u.val)) ∧
  (∀ a : Family, invoke small "incomparable" [familyArg a] = some (incomparable a)) ∧
  (∀ a : Family, invoke small "valid" [familyArg a] = some (valid a)) ∧
  (∀ a b : Family, invoke small "leq" [familyArg a, familyArg b] = some (order a b))

def Transport : Prop :=
  ∀ v : SourceValuation, callsAgree (full v) small

def Diagonal : Prop :=
  (∀ a : Family, order a a = true) ∧
  (∀ (v : SourceValuation) (a : Family), invoke (full v) "leq" [familyArg a, familyArg a] = some true)

def Complete : Prop :=
  wellFormed originalScript = true ∧
  Nonempty SourceValuation ∧
  (∀ x : Family, family (extend x) = x) ∧
  (∀ (v : SourceValuation) (a b : Family), invoke (full v) "leq" [familyArg a, familyArg b] = some (order a b)) ∧
  (∀ v : SourceValuation, invoke (full v) "valid" [familyArg (family v)] = some (valid (family v))) ∧
  (∀ v : SourceValuation, evaluate originalScript v = some [valid (family v), false]) ∧
  (¬ ∃ v : SourceValuation, Satisfies originalScript v)

end W03Scope
