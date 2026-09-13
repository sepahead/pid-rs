import PidPrefixMgwMean.Candidate
import PidPrefixMgwMean.RawTargets
import PidPrefixMgwMean.AliasTargets
import MgwBridgeDepsV1.SxDnf.JudgeCore
set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command
namespace PidPrefixMgwMeanJudge
private def checkPublicRoster (expected : List Name) : MetaM Unit := do
  let environment ← getEnv
  let observed := environment.constants.toList.filterMap fun (name, _) =>
    if name.toString.startsWith "PidPrefixMgwMeanCandidate." then some name else none
  unless observed.length == expected.length && observed.all expected.contains && expected.all observed.contains do
    throwError "PREFIX_MGW_MEAN_JUDGE_EXPORT_ROSTER: expected exactly {expected.length} public declarations"
private def emitExport (declaration raw aliasView : Name) : MetaM Unit := do
  let result ← PidSxDnfOrderJudge.checkExport declaration raw aliasView
  IO.println ("PREFIX_MGW_MEAN_JUDGE_RESULT " ++ result.compress)
end PidPrefixMgwMeanJudge

example : PidPrefixMgwMeanRawTargets.word_coefficient_join_power := @PidPrefixMgwMeanCandidate.word_coefficient_join_power
example : PidPrefixMgwMeanAliasTargets.word_coefficient_join_power := @PidPrefixMgwMeanCandidate.word_coefficient_join_power

example : PidPrefixMgwMeanRawTargets.finite_block_expectation := @PidPrefixMgwMeanCandidate.finite_block_expectation
example : PidPrefixMgwMeanAliasTargets.finite_block_expectation := @PidPrefixMgwMeanCandidate.finite_block_expectation

example : PidPrefixMgwMeanRawTargets.prefix_expectations_to_mgw_mean := @PidPrefixMgwMeanCandidate.prefix_expectations_to_mgw_mean
example : PidPrefixMgwMeanAliasTargets.prefix_expectations_to_mgw_mean := @PidPrefixMgwMeanCandidate.prefix_expectations_to_mgw_mean

run_cmd liftTermElabM do
  let roster : List Name := [
    ``PidPrefixMgwMeanCandidate.word_coefficient_join_power,
    ``PidPrefixMgwMeanCandidate.finite_block_expectation,
    ``PidPrefixMgwMeanCandidate.prefix_expectations_to_mgw_mean]
  PidPrefixMgwMeanJudge.checkPublicRoster roster
  PidPrefixMgwMeanJudge.emitExport ``PidPrefixMgwMeanCandidate.word_coefficient_join_power ``PidPrefixMgwMeanRawTargets.word_coefficient_join_power ``PidPrefixMgwMeanAliasTargets.word_coefficient_join_power
  PidPrefixMgwMeanJudge.emitExport ``PidPrefixMgwMeanCandidate.finite_block_expectation ``PidPrefixMgwMeanRawTargets.finite_block_expectation ``PidPrefixMgwMeanAliasTargets.finite_block_expectation
  PidPrefixMgwMeanJudge.emitExport ``PidPrefixMgwMeanCandidate.prefix_expectations_to_mgw_mean ``PidPrefixMgwMeanRawTargets.prefix_expectations_to_mgw_mean ``PidPrefixMgwMeanAliasTargets.prefix_expectations_to_mgw_mean
