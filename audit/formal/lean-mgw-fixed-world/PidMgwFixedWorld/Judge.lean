import PidMgwFixedWorld.RawTargets
import PidMgwFixedWorld.Candidate
import Lean
import Lean.Util.CollectAxioms

/-!
Prospective exact-type/axiom judge; Candidate.lean is intentionally absent.
This source has not been elaborated. Fresh kernel replay and frozen-source custody
are separate mandatory future observations. No process containment is provided here.
-/

set_option autoImplicit false
set_option warningAsError true

open Lean Meta

run_cmd do
  let allowed :=
    ({} : NameSet)
      |>.insert ``propext
      |>.insert ``Classical.choice
      |>.insert ``Quot.sound
  let checks : Array (Name × Name) := #[
    (`PidMgwFixedWorld.Candidate.world_normalization, ``PidMgwFixedWorld.RawTargets.WorldNormalization),
    (`PidMgwFixedWorld.Candidate.world_marginals, ``PidMgwFixedWorld.RawTargets.WorldMarginals),
    (`PidMgwFixedWorld.Candidate.world_factorization, ``PidMgwFixedWorld.RawTargets.WorldFactorization),
    (`PidMgwFixedWorld.Candidate.observation_identity, ``PidMgwFixedWorld.RawTargets.ObservationIdentity),
    (`PidMgwFixedWorld.Candidate.count_table, ``PidMgwFixedWorld.RawTargets.CountTable),
    (`PidMgwFixedWorld.Candidate.totals, ``PidMgwFixedWorld.RawTargets.Totals),
    (`PidMgwFixedWorld.Candidate.nonnegative, ``PidMgwFixedWorld.RawTargets.Nonnegative),
    (`PidMgwFixedWorld.Candidate.normalization, ``PidMgwFixedWorld.RawTargets.Normalization),
    (`PidMgwFixedWorld.Candidate.pushforward, ``PidMgwFixedWorld.RawTargets.Pushforward),
    (`PidMgwFixedWorld.Candidate.source_masses, ``PidMgwFixedWorld.RawTargets.SourceMasses),
    (`PidMgwFixedWorld.Candidate.event_counts, ``PidMgwFixedWorld.RawTargets.EventCounts),
    (`PidMgwFixedWorld.Candidate.net_arguments, ``PidMgwFixedWorld.RawTargets.NetArguments),
    (`PidMgwFixedWorld.Candidate.irrelevant_averages, ``PidMgwFixedWorld.RawTargets.IrrelevantAverages),
    (`PidMgwFixedWorld.Candidate.completing_averages, ``PidMgwFixedWorld.RawTargets.CompletingAverages),
    (`PidMgwFixedWorld.Candidate.irrelevant_synergy, ``PidMgwFixedWorld.RawTargets.IrrelevantSynergy),
    (`PidMgwFixedWorld.Candidate.completing_synergy, ``PidMgwFixedWorld.RawTargets.CompletingSynergy),
    (`PidMgwFixedWorld.Candidate.conditional_ratio, ``PidMgwFixedWorld.RawTargets.ConditionalRatio),
    (`PidMgwFixedWorld.Candidate.irrelevant_cmi, ``PidMgwFixedWorld.RawTargets.IrrelevantCmi),
    (`PidMgwFixedWorld.Candidate.completing_cmi, ``PidMgwFixedWorld.RawTargets.CompletingCmi),
    (`PidMgwFixedWorld.Candidate.synergy_equal, ``PidMgwFixedWorld.RawTargets.SynergyEqual),
    (`PidMgwFixedWorld.Candidate.cmi_different, ``PidMgwFixedWorld.RawTargets.CmiDifferent)
  ]
  unless checks.size == 21 do
    throwError "Fixed-world MGW judge requires exactly 21 target bindings"
  let mut seenCandidates : NameSet := {}
  let mut seenTargets : NameSet := {}
  let mut reports : Array Json := #[]
  for (candidate, target) in checks do
    if seenCandidates.contains candidate || seenTargets.contains target then
      throwError "Duplicate fixed-world MGW candidate or target binding"
    seenCandidates := seenCandidates.insert candidate
    seenTargets := seenTargets.insert target
    let env ← getEnv
    let some (.thmInfo proofInfo) := env.find? candidate
      | throwError m!"Missing theorem declaration {candidate}"
    unless proofInfo.levelParams.isEmpty do
      throwError m!"Unexpected universe parameters on {candidate}"
    let some targetInfo := env.find? target
      | throwError m!"Missing frozen target declaration {target}"
    unless targetInfo.levelParams.isEmpty do
      throwError m!"Unexpected universe parameters on target {target}"
    unless ← Lean.Elab.Command.liftCoreM <| MetaM.run' <| withTransparency .all <|
        isDefEq proofInfo.type (mkConst target) do
      throwError m!"Elaborated theorem type differs from frozen target: {candidate}"
    let candidateAxioms ← collectAxioms candidate
    let targetAxioms ← collectAxioms target
    for (declaration, used) in #[(candidate, candidateAxioms), (target, targetAxioms)] do
      for assumption in used do
        unless allowed.contains assumption do
          throwError m!"Forbidden axiom {assumption} in {declaration}"
    let some targetValue := targetInfo.value?
      | throwError m!"Frozen target has no reportable definition value: {target}"
    let (actualType, targetType, targetBody) ← Lean.Elab.Command.liftCoreM <| MetaM.run' do
      withOptions (fun opts =>
          opts.setBool `pp.universes true
            |>.setBool `pp.explicit true
            |>.setBool `pp.fullNames true
            |>.setBool `pp.notation false) do
        let actualType ← ppExpr proofInfo.type
        let targetType ← ppExpr targetInfo.type
        let targetBody ← ppExpr targetValue
        return (toString actualType, toString targetType, toString targetBody)
    let candidateNames := (candidateAxioms.map Name.toString).qsortOrd
    let targetNames := (targetAxioms.map Name.toString).qsortOrd
    reports := reports.push <| Json.mkObj [
      ("candidate_fqn", Json.str candidate.toString),
      ("target_fqn", Json.str target.toString),
      ("candidate_kind", Json.str "theorem"),
      ("target_kind", Json.str "definition"),
      ("candidate_universes", Json.arr (proofInfo.levelParams.toArray.map (fun n => Json.str n.toString))),
      ("target_universes", Json.arr (targetInfo.levelParams.toArray.map (fun n => Json.str n.toString))),
      ("candidate_type", Json.str actualType),
      ("target_type", Json.str targetType),
      ("target_value", Json.str targetBody),
      ("type_defeq", Json.bool true),
      ("candidate_axioms", Json.arr (candidateNames.map Json.str)),
      ("target_axioms", Json.arr (targetNames.map Json.str))
    ]
  let report := Json.mkObj [
    ("schema", Json.str "pid-rs-mgw-fixed-world-judge-report-v1"),
    ("claim", Json.str "MGW-FIXED-WORLD-COUNTEREXAMPLE-001/v1"),
    ("status", Json.str "type-and-axiom-checks-passed"),
    ("count", toJson reports.size),
    ("theorems", Json.arr reports)
  ]
  IO.println report.compress
