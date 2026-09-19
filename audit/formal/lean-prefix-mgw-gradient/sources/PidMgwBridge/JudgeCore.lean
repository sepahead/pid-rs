import MgwBridgeDepsV1.SxDnf.JudgeCore

/-! Inspection functions only. These functions supply no MGW proof.
The complete type and axiom checks reuse the byte-preserved DNF inspection module.
Its diagnostic prefix remains DNF_JUDGE for those shared failure predicates. -/
set_option autoImplicit false
set_option warningAsError true
open Lean Meta

namespace PidMgwBridgeJudge

def rosterMatches (expected observed : List Name) : Bool :=
  observed.length == expected.length &&
    observed.all expected.contains && expected.all observed.contains

def checkPublicRoster (expected : List Name) : MetaM Unit := do
  let environment ← getEnv
  let observed := environment.constants.toList.filterMap fun (name, _) =>
    if name.toString.startsWith "PidMgwBridgeCandidate." then some name else none
  unless rosterMatches expected observed do
    throwError "MGW_JUDGE_EXPORT_ROSTER: expected exactly {expected.length} public declarations"

def emitExport (declaration raw aliasView : Name) : MetaM Unit := do
  let result ← PidSxDnfOrderJudge.checkExport declaration raw aliasView
  IO.println ("MGW_BRIDGE_JUDGE_RESULT " ++ result.compress)

end PidMgwBridgeJudge
