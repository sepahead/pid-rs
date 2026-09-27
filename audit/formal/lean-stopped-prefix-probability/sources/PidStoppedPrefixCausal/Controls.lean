/- Author: Sepehr Mahmoudian.
   Uncompiled reviewer control proposal. Exact expected comparisons are assertions,
   not merely printed diagnostics. No probability proof is supplied here. -/
import PidStoppedPrefixStageA.RawTargets
import PidStoppedPrefixStageA.AliasTargets
import PidStoppedPrefixLegacyStageA.RawTargets
import MgwBridgeDepsV1.SxDnf.JudgeCore

set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command
open PidMgwBridgeContract (Key)
universe u v w

namespace PidStoppedPrefixCausalControls

noncomputable local instance propositionDecidable (P : Prop) : Decidable P :=
  Classical.propDecidable P

noncomputable def legacyViaMask {I : Type u} {X : I → Type v} {T : Type w}
    (p : Key I X T → ℝ) (A : Set (Key I X T)) (x : Key I X T) : ℝ :=
  PidStoppedPrefixLegacyStageAContract.maskedMass p Aᶜ x

noncomputable def legacyExpanded {I : Type u} {X : I → Type v} {T : Type w}
    (p : Key I X T → ℝ) (A : Set (Key I X T)) (x : Key I X T) : ℝ :=
  if x ∈ Aᶜ then p x else 0

noncomputable def canonicalViaMask {I : Type u} {X : I → Type v} {T : Type w}
    (p : Key I X T → ℝ) (A : Set (Key I X T)) (x : Key I X T) : ℝ :=
  PidStoppedPrefixStageAContract.maskedMass p Aᶜ x

noncomputable def canonicalExpanded {I : Type u} {X : I → Type v} {T : Type w}
    (p : Key I X T → ℝ) (A : Set (Key I X T)) (x : Key I X T) : ℝ :=
  @ite ℝ (x ∈ Aᶜ) (Classical.propDecidable (x ∈ Aᶜ)) (p x) 0

private def requireComparison (label : String) (left right : Name)
    (expected : Bool) : MetaM Unit := do
  let l ← getConstInfoDefn left
  let r ← getConstInfoDefn right
  let observed ← PidSxDnfOrderJudge.hasExactType l.value l.levelParams r.value r.levelParams
  unless observed == expected do
    throwError "STOPPED_PREFIX_CAUSAL_PREDICATE: {label}: expected {expected}, observed {observed}"
  IO.println ("STOPPED_PREFIX_CAUSAL_RESULT " ++ (Json.mkObj [
    ("id", Json.str label), ("left", Json.str left.toString),
    ("right", Json.str right.toString), ("expected", Json.bool expected),
    ("observed", Json.bool observed),
    ("status", Json.str "expected_comparison_observed")]).compress)

run_cmd liftTermElabM do
  requireComparison "legacy_complement_unequal" ``legacyViaMask ``legacyExpanded false
  requireComparison "canonical_complement_equal" ``canonicalViaMask ``canonicalExpanded true
  requireComparison "legacy_f1_unequal"
    ``PidStoppedPrefixLegacyStageARawTargets.first_hit_factorization
    ``PidStoppedPrefixLegacyStageAContract.first_hit_factorization_target false
  requireComparison "canonical_f1_equal"
    ``PidStoppedPrefixStageARawTargets.first_hit_factorization
    ``PidStoppedPrefixStageAAliasTargets.first_hit_factorization true
  requireComparison "legacy_f2_equal"
    ``PidStoppedPrefixLegacyStageARawTargets.first_hit_mass
    ``PidStoppedPrefixLegacyStageAContract.first_hit_mass_target true
  requireComparison "canonical_f2_equal"
    ``PidStoppedPrefixStageARawTargets.first_hit_mass
    ``PidStoppedPrefixStageAAliasTargets.first_hit_mass true

end PidStoppedPrefixCausalControls
