import PidPrefixMgwMean.RawTargets
import PidPrefixMgwMean.AliasTargets
import MgwBridgeDepsV1.SxDnf.JudgeCore

/-! Check proposition definitions. This module does not prove any probability target. -/
set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command
namespace PidPrefixMgwMeanTypeJudge

private def checkView (label : String) (raw aliasView : Name) : MetaM Json := do
  let rawInfo ← getConstInfoDefn raw
  let aliasInfo ← getConstInfoDefn aliasView
  unless rawInfo.type == mkSort Level.zero && aliasInfo.type == mkSort Level.zero do
    throwError "PREFIX_MGW_MEAN_TYPE_JUDGE_CLOSED_PROP: target views must be closed Prop definitions"
  PidSxDnfOrderJudge.checkContractView raw aliasView
  let allowed : List Name := [``propext, ``Classical.choice, ``Quot.sound]
  let assumptions ← collectAxioms raw
  for assumption in assumptions do
    unless allowed.contains assumption do
      throwError "PREFIX_MGW_MEAN_TYPE_JUDGE_DEFINITION_AXIOM: {raw} uses {assumption}"
  let rendered ← withOptions (fun options =>
    options.setBool `pp.all true |>.setBool `pp.universes true |>.set `pp.width (160 : Nat)) <|
      ppExpr rawInfo.value
  let ordered := assumptions.toList.mergeSort (fun left right => left.toString ≤ right.toString)
  return Json.mkObj [
    ("target", Json.str label),
    ("raw_target", Json.str raw.toString),
    ("alias_target", Json.str aliasView.toString),
    ("universes", Json.arr (rawInfo.levelParams.map (Json.str ∘ Name.toString)).toArray),
    ("full_elaborated_type", Json.str rendered.pretty),
    ("definition_axioms", Json.arr (ordered.map (Json.str ∘ Name.toString)).toArray),
    ("status", Json.str "types_agree_not_proved")]

end PidPrefixMgwMeanTypeJudge

run_cmd liftTermElabM do
  let result ← PidPrefixMgwMeanTypeJudge.checkView "word_coefficient_join_power" ``PidPrefixMgwMeanRawTargets.word_coefficient_join_power ``PidPrefixMgwMeanAliasTargets.word_coefficient_join_power
  IO.println ("PREFIX_MGW_MEAN_TYPE_RESULT " ++ result.compress)
  let result ← PidPrefixMgwMeanTypeJudge.checkView "finite_block_expectation" ``PidPrefixMgwMeanRawTargets.finite_block_expectation ``PidPrefixMgwMeanAliasTargets.finite_block_expectation
  IO.println ("PREFIX_MGW_MEAN_TYPE_RESULT " ++ result.compress)
  let result ← PidPrefixMgwMeanTypeJudge.checkView "prefix_expectations_to_mgw_mean" ``PidPrefixMgwMeanRawTargets.prefix_expectations_to_mgw_mean ``PidPrefixMgwMeanAliasTargets.prefix_expectations_to_mgw_mean
  IO.println ("PREFIX_MGW_MEAN_TYPE_RESULT " ++ result.compress)
