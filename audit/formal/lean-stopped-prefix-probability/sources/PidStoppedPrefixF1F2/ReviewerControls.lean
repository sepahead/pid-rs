import PidStoppedPrefixStageA.RawTargets
import PidStoppedPrefixStageA.AliasTargets
import PidStoppedPrefixF1F2.HostileTargets
import MgwBridgeDepsV1.SxDnf.JudgeCore

/- Reviewer calibration only. No value of F1 or F2 is supplied. -/
set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command
universe u
namespace PidStoppedPrefixF1F2ReviewerControls

def miniRaw : Prop := ∀ (L : Type u) (x : L), x = x
def miniAlias : Prop := miniRaw.{u}
def badAlias : Prop := False
def monomorphic : Prop := ∀ (L : Type) (x : L), x = x
theorem miniProof (L : Type u) (x : L) : x = x := rfl
set_option linter.defProp false in
def miniDefinition (L : Type u) (x : L) : x = x := rfl
theorem explicitReceiver (h : miniRaw.{u}) : miniRaw.{u} := h
theorem implicitReceiver {h : miniRaw.{u}} : miniRaw.{u} := h
theorem wrongProof : True := by trivial

private def emit (name layer : String) : MetaM Unit :=
  IO.println ("STOPPED_PREFIX_F1F2_CONTROL_RESULT " ++
    (Json.mkObj [("id", Json.str name), ("layer", Json.str layer),
      ("status", Json.str "expected_control_observed")]).compress)

private def different (name : String) (wrong right : Name) : MetaM Unit := do
  let w ← getConstInfoDefn wrong
  let r ← getConstInfoDefn right
  if ← PidSxDnfOrderJudge.hasExactType w.value w.levelParams r.value r.levelParams then
    throwError "CONTROL_FALSE_ACCEPT: {wrong}"
  emit name "complete_type"

private def rejected (name tag : String) (action : MetaM Unit) : MetaM Unit := do
  let mut observed := false
  try action
  catch error =>
    let message ← error.toMessageData.toString
    unless (message.splitOn tag).length > 1 do
      throwError "CONTROL_WRONG_REJECTION: {name}: {message}"
    observed := true
  unless observed do throwError "CONTROL_FALSE_ACCEPT: {name}"
  emit name tag

run_cmd liftTermElabM do
  let _ ← PidSxDnfOrderJudge.checkExport ``miniProof ``miniRaw ``miniAlias
  emit "miniature_positive" "exact_theorem_type_and_axioms"
  rejected "definition_kind" "DNF_JUDGE_DECLARATION_KIND" do
    let _ ← PidSxDnfOrderJudge.checkExport ``miniDefinition ``miniRaw ``miniAlias
    pure ()
  rejected "explicit_receiver" "DNF_JUDGE_TARGET_TYPE" do
    let _ ← PidSxDnfOrderJudge.checkExport ``explicitReceiver ``miniRaw ``miniAlias
    pure ()
  rejected "implicit_receiver" "DNF_JUDGE_TARGET_TYPE" do
    let _ ← PidSxDnfOrderJudge.checkExport ``implicitReceiver ``miniRaw ``miniAlias
    pure ()
  rejected "wrong_theorem" "DNF_JUDGE_TARGET_TYPE" do
    let _ ← PidSxDnfOrderJudge.checkExport ``wrongProof ``miniRaw ``miniAlias
    pure ()
  rejected "alias_mismatch" "DNF_JUDGE_CONTRACT_VIEW" do
    PidSxDnfOrderJudge.checkContractView ``miniRaw ``badAlias
  different "universe_specialization" ``monomorphic ``miniRaw
  different "factorization_final_hit_only" ``PidStoppedPrefixF1F2HostileTargets.factorization_final_hit_only ``PidStoppedPrefixStageARawTargets.first_hit_factorization
  different "factorization_unmasked_prefix" ``PidStoppedPrefixF1F2HostileTargets.factorization_unmasked_prefix ``PidStoppedPrefixStageARawTargets.first_hit_factorization
  different "factorization_wrong_final_mask" ``PidStoppedPrefixF1F2HostileTargets.factorization_wrong_final_mask ``PidStoppedPrefixStageARawTargets.first_hit_factorization
  different "factorization_normalized_masks" ``PidStoppedPrefixF1F2HostileTargets.factorization_normalized_masks ``PidStoppedPrefixStageARawTargets.first_hit_factorization
  different "mass_shifted_exponent" ``PidStoppedPrefixF1F2HostileTargets.mass_shifted_exponent ``PidStoppedPrefixStageARawTargets.first_hit_mass
  different "mass_swapped_probabilities" ``PidStoppedPrefixF1F2HostileTargets.mass_swapped_probabilities ``PidStoppedPrefixStageARawTargets.first_hit_mass
  different "mass_positive_event_only" ``PidStoppedPrefixF1F2HostileTargets.mass_positive_event_only ``PidStoppedPrefixStageARawTargets.first_hit_mass
  different "mass_nonempty_prefix_only" ``PidStoppedPrefixF1F2HostileTargets.mass_nonempty_prefix_only ``PidStoppedPrefixStageARawTargets.first_hit_mass
  different "factorization_explicit_receiver" ``PidStoppedPrefixF1F2HostileTargets.factorization_explicit_receiver ``PidStoppedPrefixStageARawTargets.first_hit_factorization
  different "factorization_implicit_receiver" ``PidStoppedPrefixF1F2HostileTargets.factorization_implicit_receiver ``PidStoppedPrefixStageARawTargets.first_hit_factorization
  different "mass_explicit_receiver" ``PidStoppedPrefixF1F2HostileTargets.mass_explicit_receiver ``PidStoppedPrefixStageARawTargets.first_hit_mass
  different "mass_implicit_receiver" ``PidStoppedPrefixF1F2HostileTargets.mass_implicit_receiver ``PidStoppedPrefixStageARawTargets.first_hit_mass

end PidStoppedPrefixF1F2ReviewerControls
