import PidPrefixProbability.Candidate
import PidPrefixProbability.RawTargets
import PidPrefixProbability.AliasTargets
import MgwBridgeDepsV1.SxDnf.JudgeCore
set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command
namespace PidPrefixProbabilityJudge
private def checkPublicRoster (expected : List Name) : MetaM Unit := do
  let environment ← getEnv
  let observed := environment.constants.toList.filterMap fun (name, _) =>
    if name.toString.startsWith "PidPrefixProbabilityCandidate." then some name else none
  unless observed.length == expected.length && observed.all expected.contains && expected.all observed.contains do
    throwError "PREFIX_PROBABILITY_JUDGE_EXPORT_ROSTER: expected exactly {expected.length} public declarations"
private def emitExport (declaration raw aliasView : Name) : MetaM Unit := do
  let result ← PidSxDnfOrderJudge.checkExport declaration raw aliasView
  IO.println ("PREFIX_PROBABILITY_JUDGE_RESULT " ++ result.compress)
end PidPrefixProbabilityJudge

example : PidPrefixProbabilityRawTargets.finite_law_measure := @PidPrefixProbabilityCandidate.finite_law_measure
example : PidPrefixProbabilityAliasTargets.finite_law_measure := @PidPrefixProbabilityCandidate.finite_law_measure

example : PidPrefixProbabilityRawTargets.finite_product_law := @PidPrefixProbabilityCandidate.finite_product_law
example : PidPrefixProbabilityAliasTargets.finite_product_law := @PidPrefixProbabilityCandidate.finite_product_law

example : PidPrefixProbabilityRawTargets.positive_increment_expectation := @PidPrefixProbabilityCandidate.positive_increment_expectation
example : PidPrefixProbabilityAliasTargets.positive_increment_expectation := @PidPrefixProbabilityCandidate.positive_increment_expectation

example : PidPrefixProbabilityRawTargets.negative_increment_expectation := @PidPrefixProbabilityCandidate.negative_increment_expectation
example : PidPrefixProbabilityAliasTargets.negative_increment_expectation := @PidPrefixProbabilityCandidate.negative_increment_expectation

example : PidPrefixProbabilityRawTargets.block_range := @PidPrefixProbabilityCandidate.block_range
example : PidPrefixProbabilityAliasTargets.block_range := @PidPrefixProbabilityCandidate.block_range

example : PidPrefixProbabilityRawTargets.block_product_independence := @PidPrefixProbabilityCandidate.block_product_independence
example : PidPrefixProbabilityAliasTargets.block_product_independence := @PidPrefixProbabilityCandidate.block_product_independence

run_cmd liftTermElabM do
  let roster : List Name := [
    ``PidPrefixProbabilityCandidate.finite_law_measure,
    ``PidPrefixProbabilityCandidate.finite_product_law,
    ``PidPrefixProbabilityCandidate.positive_increment_expectation,
    ``PidPrefixProbabilityCandidate.negative_increment_expectation,
    ``PidPrefixProbabilityCandidate.block_range,
    ``PidPrefixProbabilityCandidate.block_product_independence]
  PidPrefixProbabilityJudge.checkPublicRoster roster
  PidPrefixProbabilityJudge.emitExport ``PidPrefixProbabilityCandidate.finite_law_measure ``PidPrefixProbabilityRawTargets.finite_law_measure ``PidPrefixProbabilityAliasTargets.finite_law_measure
  PidPrefixProbabilityJudge.emitExport ``PidPrefixProbabilityCandidate.finite_product_law ``PidPrefixProbabilityRawTargets.finite_product_law ``PidPrefixProbabilityAliasTargets.finite_product_law
  PidPrefixProbabilityJudge.emitExport ``PidPrefixProbabilityCandidate.positive_increment_expectation ``PidPrefixProbabilityRawTargets.positive_increment_expectation ``PidPrefixProbabilityAliasTargets.positive_increment_expectation
  PidPrefixProbabilityJudge.emitExport ``PidPrefixProbabilityCandidate.negative_increment_expectation ``PidPrefixProbabilityRawTargets.negative_increment_expectation ``PidPrefixProbabilityAliasTargets.negative_increment_expectation
  PidPrefixProbabilityJudge.emitExport ``PidPrefixProbabilityCandidate.block_range ``PidPrefixProbabilityRawTargets.block_range ``PidPrefixProbabilityAliasTargets.block_range
  PidPrefixProbabilityJudge.emitExport ``PidPrefixProbabilityCandidate.block_product_independence ``PidPrefixProbabilityRawTargets.block_product_independence ``PidPrefixProbabilityAliasTargets.block_product_independence
