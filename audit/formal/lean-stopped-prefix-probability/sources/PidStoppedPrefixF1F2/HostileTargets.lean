import PidStoppedPrefixStageA.Contract

/- Reviewer-owned probability target mutations only, with no proof candidates.
   False mathematical replacements and true-but-weaker premise additions are
   distinguished in CONTROL_RATIONALE.md. Not yet elaborated or executed. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal
open MeasureTheory
open PidMgwBridgeContract (Key Law)
open PidPrefixProbabilityContract
open PidStoppedPrefixStageAContract
universe u v w
namespace PidStoppedPrefixF1F2HostileTargets

noncomputable local instance propositionDecidable (P : Prop) : Decidable P :=
  Classical.propDecidable P
local instance keySpace {I : Type u} {X : I → Type v} {T : Type w} :
    MeasurableSpace (Key I X T) := ⊤

abbrev factorization_final_hit_only : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (A : Set (Key I X T)) (n : ℕ),
    Law p →
      @Measure.map _ _
        (inferInstance : MeasurableSpace (Fin (n + 1) → Key I X T))
        (@Prod.instMeasurableSpace (Fin n → Key I X T) (Key I X T)
          inferInstance inferInstance)
        (splitLast n) ((rowLaw p (n + 1)).restrict {word | word (Fin.last n) ∈ A}) =
        (rowLaw (maskedMass p Aᶜ) n).prod (keyMeasure (maskedMass p A))

abbrev factorization_unmasked_prefix : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (A : Set (Key I X T)) (n : ℕ),
    Law p →
      @Measure.map _ _
        (inferInstance : MeasurableSpace (Fin (n + 1) → Key I X T))
        (@Prod.instMeasurableSpace (Fin n → Key I X T) (Key I X T)
          inferInstance inferInstance)
        (splitLast n) ((rowLaw p (n + 1)).restrict (firstHitWord A n)) =
        (rowLaw p n).prod (keyMeasure (maskedMass p A))

abbrev factorization_wrong_final_mask : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (A : Set (Key I X T)) (n : ℕ),
    Law p →
      @Measure.map _ _
        (inferInstance : MeasurableSpace (Fin (n + 1) → Key I X T))
        (@Prod.instMeasurableSpace (Fin n → Key I X T) (Key I X T)
          inferInstance inferInstance)
        (splitLast n) ((rowLaw p (n + 1)).restrict (firstHitWord A n)) =
        (rowLaw (maskedMass p Aᶜ) n).prod (keyMeasure (maskedMass p Aᶜ))

abbrev factorization_normalized_masks : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (A : Set (Key I X T)) (n : ℕ),
    Law p →
      @Measure.map _ _
        (inferInstance : MeasurableSpace (Fin (n + 1) → Key I X T))
        (@Prod.instMeasurableSpace (Fin n → Key I X T) (Key I X T)
          inferInstance inferInstance)
        (splitLast n) ((rowLaw p (n + 1)).restrict (firstHitWord A n)) =
        (rowLaw (fun x => maskedMass p Aᶜ x / (1 - eventMass p A)) n).prod
          (keyMeasure (fun x => maskedMass p A x / eventMass p A))

abbrev mass_shifted_exponent : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (A : Set (Key I X T)) (n : ℕ),
    Law p →
      0 ≤ eventMass p A ∧ eventMass p A ≤ 1 ∧
      rowLaw p (n + 1) (firstHitWord A n) =
        ENNReal.ofReal ((1 - eventMass p A) ^ (n + 1) * eventMass p A)

abbrev mass_swapped_probabilities : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (A : Set (Key I X T)) (n : ℕ),
    Law p →
      0 ≤ eventMass p A ∧ eventMass p A ≤ 1 ∧
      rowLaw p (n + 1) (firstHitWord A n) =
        ENNReal.ofReal (eventMass p A ^ n * (1 - eventMass p A))

abbrev mass_positive_event_only : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (A : Set (Key I X T)) (n : ℕ),
    Law p → 0 < eventMass p A → eventMass p A < 1 →
      0 ≤ eventMass p A ∧ eventMass p A ≤ 1 ∧
      rowLaw p (n + 1) (firstHitWord A n) =
        ENNReal.ofReal ((1 - eventMass p A) ^ n * eventMass p A)

abbrev mass_nonempty_prefix_only : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (A : Set (Key I X T)) (n : ℕ),
    Law p → 0 < n →
      0 ≤ eventMass p A ∧ eventMass p A ≤ 1 ∧
      rowLaw p (n + 1) (firstHitWord A n) =
        ENNReal.ofReal ((1 - eventMass p A) ^ n * eventMass p A)

abbrev factorization_explicit_receiver : Prop :=
  first_hit_factorization_target.{u, v, w} → first_hit_factorization_target.{u, v, w}
abbrev factorization_implicit_receiver : Prop :=
  ∀ {_h : first_hit_factorization_target.{u, v, w}}, first_hit_factorization_target.{u, v, w}

abbrev mass_explicit_receiver : Prop :=
  first_hit_mass_target.{u, v, w} → first_hit_mass_target.{u, v, w}
abbrev mass_implicit_receiver : Prop :=
  ∀ {_h : first_hit_mass_target.{u, v, w}}, first_hit_mass_target.{u, v, w}

end PidStoppedPrefixF1F2HostileTargets
