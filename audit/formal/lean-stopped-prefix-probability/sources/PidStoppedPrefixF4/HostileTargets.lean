import PidStoppedPrefixStageA.Contract

/- INERT reviewer-owned hostile proposition definitions. No proof candidates.
   These are complete Lean source proposals, not a claim of checked elaboration.
   Wrong mathematical statements and true-but-weaker statements are distinguished
   in CONTROLS.md. Literal pair swap is intentionally avoided: its codomain is wrong. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal
open MeasureTheory
open PidMgwBridgeContract (Key Node Law)
open PidPrefixProbabilityContract
open PidStoppedPrefixStageAContract
universe u v w
namespace PidStoppedPrefixStageAHostileTargets

noncomputable local instance propositionDecidable (P : Prop) : Decidable P :=
  Classical.propDecidable P
local instance keySpace {I : Type u} {X : I → Type v} {T : Type w} :
    MeasurableSpace (Key I X T) := ⊤

abbrev target_only_kills : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (z : Key I X T) (alpha : Node I) (rows : List (Key I X T)),
    (∃ x ∈ rows, x.2 = z.2) →
      positiveOnPrefix z alpha rows = 0 ∧ negativeOnPrefix z alpha rows = 0

abbrev source_only_kills : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (z : Key I X T) (alpha : Node I) (rows : List (Key I X T)),
    (∃ x ∈ rows, x.1 = z.1) →
      positiveOnPrefix z alpha rows = 0 ∧ negativeOnPrefix z alpha rows = 0

/-- Mathematically true weaker scope; rejection must come from complete type comparison. -/
abbrev last_only_kills : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (z : Key I X T) (alpha : Node I) (rows : List (Key I X T)),
    rows.getLast? = some z →
      positiveOnPrefix z alpha rows = 0 ∧ negativeOnPrefix z alpha rows = 0

/-- True tautology with an extra receiver, not F4. -/
abbrev explicit_receiver : Prop :=
  native_return_kills_target.{u, v, w} → native_return_kills_target.{u, v, w}
abbrev implicit_receiver : Prop :=
  ∀ {_h : native_return_kills_target.{u, v, w}}, native_return_kills_target.{u, v, w}

end PidStoppedPrefixStageAHostileTargets
