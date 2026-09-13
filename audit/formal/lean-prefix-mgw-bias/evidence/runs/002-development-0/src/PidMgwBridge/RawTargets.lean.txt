import PidMgwBridge.Contract

/-! Complete raw mathematical propositions, written from the adopted specification.
These values have type Prop. They do not supply proofs of those propositions.
The antichain and order formulas are expanded here as a separate source view. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators
open PidMgwBridgeContract

universe u v w
namespace PidMgwBridgeRawTargets

def rawValid {I : Type u} (family : Finset (Finset I)) : Prop :=
  family.Nonempty ∧ (∀ a ∈ family, a.Nonempty) ∧
    ∀ a ∈ family, ∀ b ∈ family, a ⊆ b → a = b

def rawOrder {I : Type u} (a b : Finset (Finset I)) : Prop :=
  ∀ collection ∈ b, ∃ witness ∈ a, witness ⊆ collection

def actual_join_lub : Prop :=
  ∀ (I : Type u) [Fintype I] [Nonempty I] [DecidableEq I],
    (∀ a b : Node I,
      rawValid (rawJoin a.val b.val) ∧
        ∀ c : Node I, rawOrder (rawJoin a.val b.val) c.val ↔
          (rawOrder a.val c.val ∧ rawOrder b.val c.val)) ∧
      ∃ sigma : SemilatticeSup (Node I),
        (∀ a b : Node I, sigma.le a b ↔ rawOrder a.val b.val) ∧
          (∀ a b : Node I, (sigma.sup a b).val = rawJoin a.val b.val)

def mismatch_generator_and_exclusion : Prop :=
  (∀ (I : Type u) [Fintype I] [Nonempty I] [DecidableEq I]
      (missing : Finset I), missing.Nonempty → rawValid (singles missing)) ∧
    ∀ (I : Type u) (X : I → Type v) (T : Type w)
        [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
        [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
        (z x : Key I X T) (a : Node I),
      x ∉ PidFiniteConvergence.sxSourceEvent a.val z ↔
        ((mismatches z x).Nonempty ∧ rawOrder (singles (mismatches z x)) a.val)

def generator_nonnegative_and_total : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (r : Key I X T → ℝ) (z : Key I X T),
    (∀ x, 0 ≤ r x) →
      (∀ b, 0 ≤ weights r z b) ∧
        nodeTotal (weights r z) = total r - fullSourceMass r z

def generator_lower_cumulative : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (r : Key I X T → ℝ) (z : Key I X T) (a : Node I),
    cumulative (weights r z) a = total r - sourceMass r z a

def target_conditioning_mass : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T),
    ((∀ x, 0 ≤ p x) ∧ total p = 1) → 0 < targetMass p z →
      ((∀ x, 0 ≤ conditioned p z x) ∧ total (conditioned p z) = 1) ∧
        ∀ event : Finset (Key I X T),
          PidFiniteConvergence.finiteEventMass (conditioned p z) event =
            PidFiniteConvergence.finiteEventMass p
              (event ∩ PidFiniteConvergence.targetBranchEvent z) / targetMass p z

def supported_anchor_domains : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T),
    ((∀ x, 0 ≤ p x) ∧ total p = 1) → 0 < p z →
      0 < fullSourceMass p z ∧ fullSourceMass p z ≤ 1 ∧
      0 < targetMass p z ∧ targetMass p z ≤ 1 ∧
      conditioned p z z = p z / targetMass p z ∧ 0 < conditioned p z z ∧
      nodeTotal (weights p z) = 1 - fullSourceMass p z ∧
      0 ≤ nodeTotal (weights p z) ∧ nodeTotal (weights p z) < 1 ∧
      nodeTotal (weights (conditioned p z) z) = 1 - p z / targetMass p z ∧
      0 ≤ nodeTotal (weights (conditioned p z) z) ∧
      nodeTotal (weights (conditioned p z) z) < 1 ∧
      ∀ a : Node I,
        0 < sourceMass p z a ∧ sourceMass p z a ≤ 1 ∧
        0 < restrictedMass p z a / targetMass p z ∧
        restrictedMass p z a / targetMass p z ≤ 1 ∧
        cumulative (weights p z) a = 1 - sourceMass p z a ∧
        cumulative (weights (conditioned p z) z) a =
          1 - restrictedMass p z a / targetMass p z

def conditional_generator_support : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T) (b : Node I),
    ((∀ x, 0 ≤ p x) ∧ total p = 1) → 0 < targetMass p z →
      0 < weights (conditioned p z) z b → 0 < weights p z b

def informative_inverse_identification : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T),
    ((∀ x, 0 ≤ p x) ∧ total p = 1) → 0 < fullSourceMass p z →
      ∃ a : Node I → ℝ,
        (∀ alpha, cumulative a alpha = -Real.log (sourceMass p z alpha)) ∧
        LogModel (weights p z) a ∧
        ∀ b : Node I → ℝ,
          (∀ alpha, cumulative b alpha = -Real.log (sourceMass p z alpha)) → b = a

def misinformative_inverse_identification : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T),
    ((∀ x, 0 ≤ p x) ∧ total p = 1) → 0 < p z →
      ∃ a : Node I → ℝ,
        (∀ alpha, cumulative a alpha =
          Real.log (targetMass p z / restrictedMass p z alpha)) ∧
        LogModel (weights (conditioned p z) z) a ∧
        ∀ b : Node I → ℝ,
          (∀ alpha, cumulative b alpha =
            Real.log (targetMass p z / restrictedMass p z alpha)) → b = a

def component_nonnegative_strict_support : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T) (aPlus aMinus : Node I → ℝ),
    ((∀ x, 0 ≤ p x) ∧ total p = 1) → 0 < p z →
      (∀ a, cumulative aPlus a = -Real.log (sourceMass p z a)) →
      (∀ a, cumulative aMinus a = Real.log (targetMass p z / restrictedMass p z a)) →
      ∀ a : Node I, 0 ≤ aPlus a ∧ 0 ≤ aMinus a ∧
        (0 < aPlus a ↔ Generated (weights p z) a) ∧
        (0 < aMinus a ↔ Generated (weights (conditioned p z) z) a)

def signed_mgw_cumulative : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T) (aPlus aMinus : Node I → ℝ),
    ((∀ x, 0 ≤ p x) ∧ total p = 1) → 0 < p z →
      (∀ a, cumulative aPlus a = -Real.log (sourceMass p z a)) →
      (∀ a, cumulative aMinus a = Real.log (targetMass p z / restrictedMass p z a)) →
      ∀ a : Node I, cumulative (aPlus - aMinus) a =
        Real.log (restrictedMass p z a / (sourceMass p z a * targetMass p z))

end PidMgwBridgeRawTargets
