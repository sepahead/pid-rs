import PidMgwBridge.Candidate
import PidMgwBridge.RawTargets
import PidMgwBridge.AliasTargets
import PidMgwBridge.JudgeCore

/-! Inert future replay module. No MGW candidate exists in this preparation stage.
A later adopted freeze and campaign must instantiate and execute this module. -/
set_option autoImplicit false
set_option warningAsError true
open Lean Elab Command

example : PidMgwBridgeRawTargets.actual_join_lub := @PidMgwBridgeCandidate.actual_join_lub
example : PidMgwBridgeAliasTargets.actual_join_lub := @PidMgwBridgeCandidate.actual_join_lub
example : PidMgwBridgeRawTargets.mismatch_generator_and_exclusion := @PidMgwBridgeCandidate.mismatch_generator_and_exclusion
example : PidMgwBridgeAliasTargets.mismatch_generator_and_exclusion := @PidMgwBridgeCandidate.mismatch_generator_and_exclusion
example : PidMgwBridgeRawTargets.generator_nonnegative_and_total := @PidMgwBridgeCandidate.generator_nonnegative_and_total
example : PidMgwBridgeAliasTargets.generator_nonnegative_and_total := @PidMgwBridgeCandidate.generator_nonnegative_and_total
example : PidMgwBridgeRawTargets.generator_lower_cumulative := @PidMgwBridgeCandidate.generator_lower_cumulative
example : PidMgwBridgeAliasTargets.generator_lower_cumulative := @PidMgwBridgeCandidate.generator_lower_cumulative
example : PidMgwBridgeRawTargets.target_conditioning_mass := @PidMgwBridgeCandidate.target_conditioning_mass
example : PidMgwBridgeAliasTargets.target_conditioning_mass := @PidMgwBridgeCandidate.target_conditioning_mass
example : PidMgwBridgeRawTargets.supported_anchor_domains := @PidMgwBridgeCandidate.supported_anchor_domains
example : PidMgwBridgeAliasTargets.supported_anchor_domains := @PidMgwBridgeCandidate.supported_anchor_domains
example : PidMgwBridgeRawTargets.conditional_generator_support := @PidMgwBridgeCandidate.conditional_generator_support
example : PidMgwBridgeAliasTargets.conditional_generator_support := @PidMgwBridgeCandidate.conditional_generator_support
example : PidMgwBridgeRawTargets.informative_inverse_identification := @PidMgwBridgeCandidate.informative_inverse_identification
example : PidMgwBridgeAliasTargets.informative_inverse_identification := @PidMgwBridgeCandidate.informative_inverse_identification
example : PidMgwBridgeRawTargets.misinformative_inverse_identification := @PidMgwBridgeCandidate.misinformative_inverse_identification
example : PidMgwBridgeAliasTargets.misinformative_inverse_identification := @PidMgwBridgeCandidate.misinformative_inverse_identification
example : PidMgwBridgeRawTargets.component_nonnegative_strict_support := @PidMgwBridgeCandidate.component_nonnegative_strict_support
example : PidMgwBridgeAliasTargets.component_nonnegative_strict_support := @PidMgwBridgeCandidate.component_nonnegative_strict_support
example : PidMgwBridgeRawTargets.signed_mgw_cumulative := @PidMgwBridgeCandidate.signed_mgw_cumulative
example : PidMgwBridgeAliasTargets.signed_mgw_cumulative := @PidMgwBridgeCandidate.signed_mgw_cumulative

run_cmd liftTermElabM do
  let roster : List Name := [
    ``PidMgwBridgeCandidate.actual_join_lub,
    ``PidMgwBridgeCandidate.mismatch_generator_and_exclusion,
    ``PidMgwBridgeCandidate.generator_nonnegative_and_total,
    ``PidMgwBridgeCandidate.generator_lower_cumulative,
    ``PidMgwBridgeCandidate.target_conditioning_mass,
    ``PidMgwBridgeCandidate.supported_anchor_domains,
    ``PidMgwBridgeCandidate.conditional_generator_support,
    ``PidMgwBridgeCandidate.informative_inverse_identification,
    ``PidMgwBridgeCandidate.misinformative_inverse_identification,
    ``PidMgwBridgeCandidate.component_nonnegative_strict_support,
    ``PidMgwBridgeCandidate.signed_mgw_cumulative]
  PidMgwBridgeJudge.checkPublicRoster roster
  PidMgwBridgeJudge.emitExport ``PidMgwBridgeCandidate.actual_join_lub ``PidMgwBridgeRawTargets.actual_join_lub ``PidMgwBridgeAliasTargets.actual_join_lub
  PidMgwBridgeJudge.emitExport ``PidMgwBridgeCandidate.mismatch_generator_and_exclusion ``PidMgwBridgeRawTargets.mismatch_generator_and_exclusion ``PidMgwBridgeAliasTargets.mismatch_generator_and_exclusion
  PidMgwBridgeJudge.emitExport ``PidMgwBridgeCandidate.generator_nonnegative_and_total ``PidMgwBridgeRawTargets.generator_nonnegative_and_total ``PidMgwBridgeAliasTargets.generator_nonnegative_and_total
  PidMgwBridgeJudge.emitExport ``PidMgwBridgeCandidate.generator_lower_cumulative ``PidMgwBridgeRawTargets.generator_lower_cumulative ``PidMgwBridgeAliasTargets.generator_lower_cumulative
  PidMgwBridgeJudge.emitExport ``PidMgwBridgeCandidate.target_conditioning_mass ``PidMgwBridgeRawTargets.target_conditioning_mass ``PidMgwBridgeAliasTargets.target_conditioning_mass
  PidMgwBridgeJudge.emitExport ``PidMgwBridgeCandidate.supported_anchor_domains ``PidMgwBridgeRawTargets.supported_anchor_domains ``PidMgwBridgeAliasTargets.supported_anchor_domains
  PidMgwBridgeJudge.emitExport ``PidMgwBridgeCandidate.conditional_generator_support ``PidMgwBridgeRawTargets.conditional_generator_support ``PidMgwBridgeAliasTargets.conditional_generator_support
  PidMgwBridgeJudge.emitExport ``PidMgwBridgeCandidate.informative_inverse_identification ``PidMgwBridgeRawTargets.informative_inverse_identification ``PidMgwBridgeAliasTargets.informative_inverse_identification
  PidMgwBridgeJudge.emitExport ``PidMgwBridgeCandidate.misinformative_inverse_identification ``PidMgwBridgeRawTargets.misinformative_inverse_identification ``PidMgwBridgeAliasTargets.misinformative_inverse_identification
  PidMgwBridgeJudge.emitExport ``PidMgwBridgeCandidate.component_nonnegative_strict_support ``PidMgwBridgeRawTargets.component_nonnegative_strict_support ``PidMgwBridgeAliasTargets.component_nonnegative_strict_support
  PidMgwBridgeJudge.emitExport ``PidMgwBridgeCandidate.signed_mgw_cumulative ``PidMgwBridgeRawTargets.signed_mgw_cumulative ``PidMgwBridgeAliasTargets.signed_mgw_cumulative
