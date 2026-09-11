import PidMgwTargetCopyJudge.JudgeCore
import PidMgwTargetCopyCandidate.L1
import PidMgwTargetCopyCandidate.L2
import PidMgwTargetCopy.SourceUnionMassCandidate
import PidMgwTargetCopyCandidate.L4

/-!
UNCOMPILED SOURCE PROPOSAL. Exactly four existing theorem/Interface bindings.
A printed report is pending actual terminal, source/object custody and root review.
L4 itself imports L2 and SourceUnionMassCandidate; all three sources stay separately pinned.
-/

set_option autoImplicit false
set_option warningAsError true

open Lean Meta

run_cmd do
  let reports ← Lean.Elab.Command.liftCoreM <| MetaM.run' do
    let checks : Array (Name × Name) := #[
      (`PidMgwTargetCopyCandidate.worldBridge, ``PidMgwTargetCopy.WorldBridgeTarget),
      (`PidMgwTargetCopyCandidate.copyEventMasses, ``PidMgwTargetCopy.CopyEventMassesTarget),
      (`PidMgwTargetCopy.sourceUnionMassTarget_candidate, ``PidMgwTargetCopy.SourceUnionMassTarget),
      (`PidMgwTargetCopyCandidate.localCumulatives, ``PidMgwTargetCopy.LocalCumulativesTarget)]
    unless checks.size == 4 do
      throwError "MGW_COPY_ROSTER: exactly four bindings required"
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
    ("schema", Json.str "pid-rs-mgw-target-copy-l1-l4-judge-report-v1"),
    ("status", Json.str "type-and-axiom-checks-passed-pending-actual-outcome-and-root-review"),
    ("count", toJson reports.size),
    ("theorems", Json.arr reports)]
  IO.println ("MGW_TARGET_COPY_JUDGE " ++ report.compress)
