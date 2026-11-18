import Contract

set_option autoImplicit false
set_option warningAsError true

namespace PidFin3RawTargets
open PidFin3Contract

def codec_range : Prop := ∀ a : Finset (Fin 3), encode a < 8
def decode_encode : Prop := ∀ a : Finset (Fin 3), decode (encode a) = a
def encode_decode : Prop := ∀ m : Fin 8, encode (decode m.val) = m.val
def codec_nonempty : Prop := ∀ a : Finset (Fin 3), a.Nonempty ↔ encode a ≠ 0
def codec_subset : Prop :=
  ∀ a b : Finset (Fin 3), a ⊆ b ↔ (encode a &&& encode b) = encode a
def codec_anchors : Prop :=
  encode ({0} : Finset (Fin 3)) = 1 ∧ encode ({1} : Finset (Fin 3)) = 2 ∧
    encode ({2} : Finset (Fin 3)) = 4 ∧
      decode 1 = ({0} : Finset (Fin 3)) ∧ decode 2 = ({1} : Finset (Fin 3)) ∧
        decode 4 = ({2} : Finset (Fin 3))
def carrier_membership : Prop :=
  ∀ A : Finset (Finset (Fin 3)), A ∈ carrier ↔
    A.Nonempty ∧ (∀ a ∈ A, a.Nonempty) ∧
      ∀ a ∈ A, ∀ b ∈ A, a ⊆ b → a = b
def carrier_cardinality : Prop := carrier.card = 18
def registry_pointwise : Prop :=
  ∀ i : Fin 18, (registry i).image encode = (registryMasks i).toFinset
def registry_injective : Prop :=
  ∀ i j : Fin 18, registry i = registry j → i = j
def registry_coverage : Prop :=
  ∀ A : Finset (Finset (Fin 3)),
    (A.Nonempty ∧ (∀ a ∈ A, a.Nonempty) ∧
      ∀ a ∈ A, ∀ b ∈ A, a ⊆ b → a = b) ↔ ∃ i : Fin 18, registry i = A
def reflexivity : Prop :=
  ∀ A : Finset (Finset (Fin 3)), ∀ b ∈ A, ∃ a ∈ A, a ⊆ b
def transitivity : Prop :=
  ∀ A B C : Finset (Finset (Fin 3)),
    (∀ b ∈ B, ∃ a ∈ A, a ⊆ b) → (∀ c ∈ C, ∃ b ∈ B, b ⊆ c) →
      ∀ c ∈ C, ∃ a ∈ A, a ⊆ c
def antisymmetry : Prop :=
  ∀ A B : Finset (Finset (Fin 3)),
    (A.Nonempty ∧ (∀ a ∈ A, a.Nonempty) ∧
      ∀ a ∈ A, ∀ b ∈ A, a ⊆ b → a = b) →
    (B.Nonempty ∧ (∀ a ∈ B, a.Nonempty) ∧
      ∀ a ∈ B, ∀ b ∈ B, a ⊆ b → a = b) →
    (∀ b ∈ B, ∃ a ∈ A, a ⊆ b) → (∀ a ∈ A, ∃ b ∈ B, b ⊆ a) → A = B
def reverse_dnf : Prop :=
  ∀ A B : Finset (Finset (Fin 3)),
    (∀ b ∈ B, ∃ a ∈ A, a ⊆ b) ↔
      ∀ pattern : Fin 3 → Bool,
        (∃ b ∈ B, ∀ i ∈ b, pattern i = true) →
          ∃ a ∈ A, ∀ i ∈ a, pattern i = true
def row_shape : Prop :=
  ∀ i : Fin 18, (rowSignature i).toList.length = 18 ∧
    ∀ c ∈ (rowSignature i).toList, c = '0' ∨ c = '1'
def zeta_entries : Prop :=
  ∀ i j : Fin 18, expectedZeta i j = true ↔
    ∀ b ∈ registry i, ∃ a ∈ registry j, a ⊆ b
def zeta_census : Prop :=
  ((Finset.univ : Finset (Fin 18)).sum fun i =>
    ((Finset.univ : Finset (Fin 18)).filter fun j => expectedZeta i j = true).card) = 129
def extremes : Prop :=
  (∀ i : Fin 18,
    (∀ b ∈ registry i, ∃ a ∈ registry 16, a ⊆ b) ∧
    (∀ b ∈ registry 6, ∃ a ∈ registry i, a ⊆ b)) ∧
      (∀ b ∈ registry 2, ∃ a ∈ registry 0, a ⊆ b) ∧
        ¬ (∀ b ∈ registry 0, ∃ a ∈ registry 2, a ⊆ b) ∧
          (∀ b ∈ registry 2, ∃ a ∈ registry 7, a ⊆ b) ∧
            ¬ (∀ b ∈ registry 7, ∃ a ∈ registry 2, a ⊆ b)

end PidFin3RawTargets
