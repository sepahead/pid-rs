import PidMgwTargetCopyJudge.JudgeCore
import PidMgwTargetCopyCandidate.L5
import PidMgwTargetCopyCandidate.Identities

/-!
Unexecuted fixed judge proposal for the original source projection and four identity targets.
Only explicit declaration bindings differ from the existing four-target judge. Candidate
sources are exposed development inputs; no candidate-inaccessible confirmation is claimed.
The qualified JudgeCore enforces the original complete types and allowed transitive axioms.
-/

set_option autoImplicit false
set_option warningAsError true

open Lean Meta

run_cmd do
  let reports ← Lean.Elab.Command.liftCoreM <| MetaM.run' do
    let checks : Array (Name × Name) := #[
      (`PidMgwTargetCopyCandidate.sourceProjection, ``PidMgwTargetCopy.SourceProjectionTarget),
      (`PidMgwTargetCopyCandidate.localIdentity, ``PidMgwTargetCopy.LocalIdentityTarget),
      (`PidMgwTargetCopyCandidate.worldLocalIdentity, ``PidMgwTargetCopy.WorldLocalIdentityTarget),
      (`PidMgwTargetCopyCandidate.averagedIdentity, ``PidMgwTargetCopy.AveragedIdentityTarget),
      (`PidMgwTargetCopyCandidate.sameSourceLaw, ``PidMgwTargetCopy.SameSourceLawTarget)]
    unless checks.size == 5 do
      throwError "MGW_COPY_ROSTER: exactly five bindings required"
    let mut seenCandidates : NameSet := {}
    let mut seenTargets : NameSet := {}
    let mut reports : Array Json := #[]
    for (candidate, target) in checks do
      if seenCandidates.contains candidate || seenTargets.contains target then
        throwError "MGW_COPY_ROSTER: duplicate candidate or target"
      seenCandidates := seenCandidates.insert candidate
      seenTargets := seenTargets.insert target
      reports := reports.push (← PidMgwTargetCopyJudge.checkExport candidate target)
    return reports
  let report := Json.mkObj [
    ("schema", Json.str "pid-rs-mgw-target-copy-identities-judge-report-v1"),
    ("status", Json.str "type-and-axiom-checks-passed-pending-actual-outcome-and-root-review"),
    ("count", toJson reports.size),
    ("theorems", Json.arr reports)]
  IO.println ("MGW_TARGET_COPY_JUDGE " ++ report.compress)
