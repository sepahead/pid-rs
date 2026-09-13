import PidPrefixMgwBias.Candidate
import PidPrefixMgwBias.RawTargets
import PidPrefixMgwBias.AliasTargets
import MgwBridgeDepsV1.SxDnf.JudgeCore
set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command
namespace PidPrefixMgwBiasJudge
private def checkPublicRoster (expected : List Name) : MetaM Unit := do
  let environment ← getEnv
  let observed := environment.constants.toList.filterMap fun (name, _) =>
    if name.toString.startsWith "PidPrefixMgwBiasCandidate." then some name else none
  unless observed.length == expected.length && observed.all expected.contains && expected.all observed.contains do
    throwError "PREFIX_MGW_BIAS_JUDGE_EXPORT_ROSTER: expected exactly {expected.length} public declarations"
private def emitExport (declaration raw aliasView : Name) : MetaM Unit := do
  let result ← PidSxDnfOrderJudge.checkExport declaration raw aliasView
  IO.println ("PREFIX_MGW_BIAS_JUDGE_RESULT " ++ result.compress)
end PidPrefixMgwBiasJudge

example : PidPrefixMgwBiasRawTargets.actual_finite_bias := @PidPrefixMgwBiasCandidate.actual_finite_bias
example : PidPrefixMgwBiasAliasTargets.actual_finite_bias := @PidPrefixMgwBiasCandidate.actual_finite_bias

example : PidPrefixMgwBiasRawTargets.fiber_inverse_moment := @PidPrefixMgwBiasCandidate.fiber_inverse_moment
example : PidPrefixMgwBiasAliasTargets.fiber_inverse_moment := @PidPrefixMgwBiasCandidate.fiber_inverse_moment

example : PidPrefixMgwBiasRawTargets.support_moment_bounds := @PidPrefixMgwBiasCandidate.support_moment_bounds
example : PidPrefixMgwBiasAliasTargets.support_moment_bounds := @PidPrefixMgwBiasCandidate.support_moment_bounds

example : PidPrefixMgwBiasRawTargets.projected_support_bias := @PidPrefixMgwBiasCandidate.projected_support_bias
example : PidPrefixMgwBiasAliasTargets.projected_support_bias := @PidPrefixMgwBiasCandidate.projected_support_bias

example : PidPrefixMgwBiasRawTargets.mass_floor_bias := @PidPrefixMgwBiasCandidate.mass_floor_bias
example : PidPrefixMgwBiasAliasTargets.mass_floor_bias := @PidPrefixMgwBiasCandidate.mass_floor_bias

run_cmd liftTermElabM do
  let roster : List Name := [
    ``PidPrefixMgwBiasCandidate.actual_finite_bias,
    ``PidPrefixMgwBiasCandidate.fiber_inverse_moment,
    ``PidPrefixMgwBiasCandidate.support_moment_bounds,
    ``PidPrefixMgwBiasCandidate.projected_support_bias,
    ``PidPrefixMgwBiasCandidate.mass_floor_bias]
  PidPrefixMgwBiasJudge.checkPublicRoster roster
  PidPrefixMgwBiasJudge.emitExport ``PidPrefixMgwBiasCandidate.actual_finite_bias ``PidPrefixMgwBiasRawTargets.actual_finite_bias ``PidPrefixMgwBiasAliasTargets.actual_finite_bias
  PidPrefixMgwBiasJudge.emitExport ``PidPrefixMgwBiasCandidate.fiber_inverse_moment ``PidPrefixMgwBiasRawTargets.fiber_inverse_moment ``PidPrefixMgwBiasAliasTargets.fiber_inverse_moment
  PidPrefixMgwBiasJudge.emitExport ``PidPrefixMgwBiasCandidate.support_moment_bounds ``PidPrefixMgwBiasRawTargets.support_moment_bounds ``PidPrefixMgwBiasAliasTargets.support_moment_bounds
  PidPrefixMgwBiasJudge.emitExport ``PidPrefixMgwBiasCandidate.projected_support_bias ``PidPrefixMgwBiasRawTargets.projected_support_bias ``PidPrefixMgwBiasAliasTargets.projected_support_bias
  PidPrefixMgwBiasJudge.emitExport ``PidPrefixMgwBiasCandidate.mass_floor_bias ``PidPrefixMgwBiasRawTargets.mass_floor_bias ``PidPrefixMgwBiasAliasTargets.mass_floor_bias
