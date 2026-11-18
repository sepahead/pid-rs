import Mathlib.Data.Fintype.Powerset
import Mathlib.Algebra.BigOperators.Group.Finset.Defs

set_option autoImplicit false
set_option warningAsError true

namespace PidFin3Fault06

abbrev Source := Fin 3
abbrev Branch := Finset Source
abbrev Family := Finset Branch

def Valid (A : Family) : Prop :=
  A.Nonempty ∧ (∀ a ∈ A, a.Nonempty) ∧
    ∀ a ∈ A, ∀ b ∈ A, a ⊆ b → a = b

instance (A : Family) : Decidable (Valid A) :=
  inferInstanceAs (Decidable
    (A.Nonempty ∧ (∀ a ∈ A, a.Nonempty) ∧ ∀ a ∈ A, ∀ b ∈ A, a ⊆ b → a = b))

def nonemptyBranches : Finset Branch :=
  (Finset.univ : Finset Source).powerset.filter fun a => a.Nonempty

def carrier : Finset Family :=
  nonemptyBranches.powerset.filter Valid

def encode (a : Branch) : Nat := a.sum fun i => 2 ^ i.val

def decode (m : Nat) : Branch :=
  (Finset.univ : Finset Source).filter fun i => m.testBit i.val = true

def LE (A B : Family) : Prop := ∀ b ∈ B, ∃ a ∈ A, a ⊆ b

def DNF (A : Family) (pattern : Source → Bool) : Prop :=
  ∃ a ∈ A, ∀ i ∈ a, pattern i = true

def registryMasks (i : Fin 18) : List Nat :=
  match i.val with
  | 0 => [1]
  | 1 => [2]
  | 2 => [3]
  | 3 => [4]
  | 4 => [5]
  | 5 => [6]
  | 6 => [7]
  | 7 => [1, 2]
  | 8 => [1, 4]
  | 9 => [1, 6]
  | 10 => [2, 4]
  | 11 => [2, 5]
  | 12 => [3, 4]
  | 13 => [3, 5]
  | 14 => [3, 6]
  | 15 => [5, 6]
  | 16 => [1, 2, 4]
  | _ => [3, 5, 6]

def registry (i : Fin 18) : Family :=
  (registryMasks i).toFinset.image decode

def rowSignature (i : Fin 18) : String :=
  match i.val with
  | 0 => "100000011100000010"
  | 1 => "010000010011000010"
  | 2 => "111000011111111011"
  | 3 => "000100001010100010"
  | 4 => "100110011111110111"
  | 5 => "010101011111101111"
  | 6 => "111111111111111111"
  | 7 => "000000010000000010"
  | 8 => "000000001000000010"
  | 9 => "000000011100000010"
  | 10 => "000000000010000010"
  | 11 => "000000010011000010"
  | 12 => "000000001010100010"
  | 13 => "100000011111110011"
  | 14 => "010000011111101011"
  | 15 => "000100011111100111"
  | 16 => "000000000000000010"
  | _ => "000000011111100011"

def expectedZeta (i j : Fin 18) : Bool :=
  ((rowSignature i).toList[j.val]!) == '1'

def codecRangeTarget : Prop := ∀ a : Branch, encode a < 8
def decodeEncodeTarget : Prop := ∀ a : Branch, decode (encode a) = a
def encodeDecodeTarget : Prop := ∀ m : Nat, encode (decode m) = m
def codecNonemptyTarget : Prop := ∀ a : Branch, a.Nonempty ↔ encode a ≠ 0
def codecSubsetTarget : Prop :=
  ∀ a b : Branch, a ⊆ b ↔ (encode a &&& encode b) = encode a
def codecAnchorsTarget : Prop :=
  encode {0} = 1 ∧ encode {1} = 2 ∧ encode {2} = 4 ∧
    decode 1 = {0} ∧ decode 2 = {1} ∧ decode 4 = {2}
def carrierMembershipTarget : Prop := ∀ A : Family, A ∈ carrier ↔ Valid A
def carrierCardinalityTarget : Prop := carrier.card = 18
def registryPointwiseTarget : Prop :=
  ∀ i : Fin 18, (registry i).image encode = (registryMasks i).toFinset
def registryInjectiveTarget : Prop := Function.Injective registry
def registryCoverageTarget : Prop :=
  ∀ A : Family, Valid A ↔ ∃ i : Fin 18, registry i = A
def reflexivityTarget : Prop := ∀ A : Family, LE A A
def transitivityTarget : Prop := ∀ A B C : Family, LE A B → LE B C → LE A C
def antisymmetryTarget : Prop :=
  ∀ A B : Family, Valid A → Valid B → LE A B → LE B A → A = B
def reverseDnfTarget : Prop :=
  ∀ A B : Family, LE A B ↔ ∀ pattern : Source → Bool, DNF B pattern → DNF A pattern
def rowShapeTarget : Prop :=
  ∀ i : Fin 18, (rowSignature i).toList.length = 18 ∧
    ∀ c ∈ (rowSignature i).toList, c = '0' ∨ c = '1'
def zetaEntriesTarget : Prop :=
  ∀ i j : Fin 18, expectedZeta i j = true ↔ LE (registry j) (registry i)
def zetaCensusTarget : Prop :=
  ((Finset.univ : Finset (Fin 18)).sum fun i =>
    ((Finset.univ : Finset (Fin 18)).filter fun j => expectedZeta i j = true).card) = 129
def extremesTarget : Prop :=
  (∀ i : Fin 18, LE (registry 16) (registry i) ∧ LE (registry i) (registry 6)) ∧
    LE (registry 0) (registry 2) ∧ ¬ LE (registry 2) (registry 0) ∧
      LE (registry 7) (registry 2) ∧ ¬ LE (registry 2) (registry 7)

end PidFin3Fault06
