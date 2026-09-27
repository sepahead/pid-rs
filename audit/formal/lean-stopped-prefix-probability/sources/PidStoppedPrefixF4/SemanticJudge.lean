import PidStoppedPrefixF4.Candidate
import PidStoppedPrefixStageA.RawTargets
import PidStoppedPrefixStageA.AliasTargets
import MgwBridgeDepsV1.SxDnf.JudgeCore

/- Reviewer comparison proposal only; root must independently adopt before use. -/
set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command
universe u v w

example : PidStoppedPrefixStageARawTargets.native_return_kills.{u, v, w} :=
  @PidStoppedPrefixF4Candidate.native_return_kills

example : PidStoppedPrefixStageAAliasTargets.native_return_kills.{u, v, w} :=
  @PidStoppedPrefixF4Candidate.native_return_kills

run_cmd liftTermElabM do
  let expected := ``PidStoppedPrefixF4Candidate.native_return_kills
  let environment ← getEnv
  let observed := environment.constants.toList.filterMap fun (name, _) =>
    if name.toString.startsWith "PidStoppedPrefixF4Candidate." then some name else none
  unless observed == [expected] do
    throwError "F4_JUDGE_EXPORT_ROSTER: expected one universal F4 theorem"
  let result ← PidSxDnfOrderJudge.checkExport expected
    ``PidStoppedPrefixStageARawTargets.native_return_kills
    ``PidStoppedPrefixStageAAliasTargets.native_return_kills
  IO.println ("STOPPED_PREFIX_F4_JUDGE_RESULT " ++ result.compress)
