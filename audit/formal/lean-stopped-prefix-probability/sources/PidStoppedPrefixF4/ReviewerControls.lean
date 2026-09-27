import PidStoppedPrefixStageA.RawTargets
import PidStoppedPrefixStageA.AliasTargets
import PidStoppedPrefixF4.HostileTargets
import MgwBridgeDepsV1.SxDnf.JudgeCore

/- Reviewer calibration only. No value of F1, F2 or F4 is supplied. -/
set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command
universe u
namespace PidStoppedPrefixStageAReviewerControls

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
  IO.println ("STOPPED_PREFIX_STAGE_A_CONTROL_RESULT " ++
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
  different "target_only" ``PidStoppedPrefixStageAHostileTargets.target_only_kills ``PidStoppedPrefixStageARawTargets.native_return_kills
  different "source_only" ``PidStoppedPrefixStageAHostileTargets.source_only_kills ``PidStoppedPrefixStageARawTargets.native_return_kills
  different "last_only" ``PidStoppedPrefixStageAHostileTargets.last_only_kills ``PidStoppedPrefixStageARawTargets.native_return_kills
  different "stage_explicit_receiver" ``PidStoppedPrefixStageAHostileTargets.explicit_receiver ``PidStoppedPrefixStageARawTargets.native_return_kills
  different "stage_implicit_receiver" ``PidStoppedPrefixStageAHostileTargets.implicit_receiver ``PidStoppedPrefixStageARawTargets.native_return_kills

end PidStoppedPrefixStageAReviewerControls
