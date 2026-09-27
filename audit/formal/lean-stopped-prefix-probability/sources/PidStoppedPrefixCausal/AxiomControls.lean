/- Author: Sepehr Mahmoudian.
   Uncompiled negative fixture for the frozen export axiom gate.
   This module is deliberately excluded from the candidate and fresh-kernel roots. -/
import MgwBridgeDepsV1.SxDnf.JudgeCore

set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command

namespace PidStoppedPrefixAxiomControls

def raw : Prop := True
def aliasView : Prop := raw
axiom forbiddenFixture : True
theorem contaminated : True := forbiddenFixture

run_cmd liftTermElabM do
  let mut rejected := false
  try
    let _ ← PidSxDnfOrderJudge.checkExport ``contaminated ``raw ``aliasView
    pure ()
  catch error =>
    let message ← error.toMessageData.toString
    unless (message.splitOn "DNF_JUDGE_AXIOM").length > 1 do
      throwError "AXIOM_CONTROL_WRONG_REJECTION: {message}"
    rejected := true
  unless rejected do
    throwError "AXIOM_CONTROL_FALSE_ACCEPT: forbidden fixture axiom"
  IO.println ("STOPPED_PREFIX_AXIOM_CONTROL_RESULT " ++ (Json.mkObj [
    ("id", Json.str "forbidden_axiom_rejected"),
    ("layer", Json.str "DNF_JUDGE_AXIOM"),
    ("status", Json.str "expected_control_observed")]).compress)

end PidStoppedPrefixAxiomControls
