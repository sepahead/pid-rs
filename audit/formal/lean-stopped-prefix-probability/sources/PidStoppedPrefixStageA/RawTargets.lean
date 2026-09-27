/- Author: Sepehr Mahmoudian. Source-only canonical-decision repair proposal,
   2026-09-26; uncompiled and unaccepted. Historical F4 sources are unchanged. -/

import PidStoppedPrefixStageA.Contract

/- INERT SOURCE PROPOSAL. Intended future module: PidStoppedPrefixStageA.RawTargets.
   Raw views independently spell out the new definitions. Aliases are separate.
   The inherited native definitions and their imports must also be byte-frozen. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal
open MeasureTheory
open PidMgwBridgeContract (Key Node Law)
open PidPrefixProbabilityContract
universe u v w
namespace PidStoppedPrefixStageARawTargets

noncomputable local instance propositionDecidable (P : Prop) : Decidable P :=
  Classical.propDecidable P
local instance keySpace {I : Type u} {X : I → Type v} {T : Type w} :
    MeasurableSpace (Key I X T) := ⊤


abbrev first_hit_factorization : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (A : Set (Key I X T)) (n : ℕ),
    Law p →
      @Measure.map _ _
        (inferInstance : MeasurableSpace (Fin (n + 1) → Key I X T))
        (@Prod.instMeasurableSpace (Fin n → Key I X T) (Key I X T)
          inferInstance inferInstance)
        (fun word : Fin (n + 1) → Key I X T =>
          ((fun i : Fin n => word i.castSucc), word (Fin.last n)))
        ((rowLaw p (n + 1)).restrict
          {word | (∀ i : Fin n, word i.castSucc ∉ A) ∧ word (Fin.last n) ∈ A}) =
        (rowLaw (fun x => @ite ℝ (x ∈ Aᶜ) (Classical.propDecidable (x ∈ Aᶜ)) (p x) 0) n).prod
          (keyMeasure (fun x => @ite ℝ (x ∈ A) (Classical.propDecidable (x ∈ A)) (p x) 0))

abbrev first_hit_mass : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (A : Set (Key I X T)) (n : ℕ),
    Law p →
      0 ≤ (∑ x, @ite ℝ (x ∈ A) (Classical.propDecidable (x ∈ A)) (p x) 0) ∧
      (∑ x, @ite ℝ (x ∈ A) (Classical.propDecidable (x ∈ A)) (p x) 0) ≤ 1 ∧
      rowLaw p (n + 1)
        {word | (∀ i : Fin n, word i.castSucc ∉ A) ∧ word (Fin.last n) ∈ A} =
        ENNReal.ofReal
          ((1 - (∑ x, @ite ℝ (x ∈ A) (Classical.propDecidable (x ∈ A)) (p x) 0)) ^ n *
            (∑ x, @ite ℝ (x ∈ A) (Classical.propDecidable (x ∈ A)) (p x) 0))

abbrev native_return_kills : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (z : Key I X T) (alpha : Node I) (rows : List (Key I X T)),
    z ∈ rows →
      positiveOnPrefix z alpha rows = 0 ∧ negativeOnPrefix z alpha rows = 0

end PidStoppedPrefixStageARawTargets

