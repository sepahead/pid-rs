import Contract
import Candidate
import JudgeCore
import JudgeTargets
import JudgeAliases

set_option autoImplicit false
set_option warningAsError true

open Lean Elab Command
universe u v w

example : PidSxDnfOrderJudgeTargets.order_iff_dnf := @PidSxDnfOrderCandidate.order_iff_dnf
example : PidSxDnfOrderJudgeAliases.order_iff_dnf := @PidSxDnfOrderCandidate.order_iff_dnf
example : PidSxDnfOrderJudgeTargets.antichain_antisymm := @PidSxDnfOrderCandidate.antichain_antisymm
example : PidSxDnfOrderJudgeAliases.antichain_antisymm := @PidSxDnfOrderCandidate.antichain_antisymm
example : PidSxDnfOrderJudgeTargets.dnf_injective_on_antichains := @PidSxDnfOrderCandidate.dnf_injective_on_antichains
example : PidSxDnfOrderJudgeAliases.dnf_injective_on_antichains := @PidSxDnfOrderCandidate.dnf_injective_on_antichains
example : PidSxDnfOrderJudgeTargets.source_event_iff_dnf := @PidSxDnfOrderCandidate.source_event_iff_dnf
example : PidSxDnfOrderJudgeAliases.source_event_iff_dnf := @PidSxDnfOrderCandidate.source_event_iff_dnf
example : PidSxDnfOrderJudgeTargets.order_implies_source_event_subset := @PidSxDnfOrderCandidate.order_implies_source_event_subset
example : PidSxDnfOrderJudgeAliases.order_implies_source_event_subset := @PidSxDnfOrderCandidate.order_implies_source_event_subset
example : PidSxDnfOrderJudgeTargets.order_iff_implication_on_realizing_domain := @PidSxDnfOrderCandidate.order_iff_implication_on_realizing_domain
example : PidSxDnfOrderJudgeAliases.order_iff_implication_on_realizing_domain := @PidSxDnfOrderCandidate.order_iff_implication_on_realizing_domain
example : PidSxDnfOrderJudgeTargets.alternate_values_realize_all_patterns := @PidSxDnfOrderCandidate.alternate_values_realize_all_patterns
example : PidSxDnfOrderJudgeAliases.alternate_values_realize_all_patterns := @PidSxDnfOrderCandidate.alternate_values_realize_all_patterns
example : PidSxDnfOrderJudgeTargets.source_event_injective_on_realizing_domain := @PidSxDnfOrderCandidate.source_event_injective_on_realizing_domain
example : PidSxDnfOrderJudgeAliases.source_event_injective_on_realizing_domain := @PidSxDnfOrderCandidate.source_event_injective_on_realizing_domain
example : PidSxDnfOrderJudgeTargets.order_implies_target_restricted_subset := @PidSxDnfOrderCandidate.order_implies_target_restricted_subset
example : PidSxDnfOrderJudgeAliases.order_implies_target_restricted_subset := @PidSxDnfOrderCandidate.order_implies_target_restricted_subset
example : PidSxDnfOrderJudgeTargets.singleton_event_collision := @PidSxDnfOrderCandidate.singleton_event_collision
example : PidSxDnfOrderJudgeAliases.singleton_event_collision := @PidSxDnfOrderCandidate.singleton_event_collision
example : PidSxDnfOrderJudgeTargets.singleton_not_all_patterns := @PidSxDnfOrderCandidate.singleton_not_all_patterns
example : PidSxDnfOrderJudgeAliases.singleton_not_all_patterns := @PidSxDnfOrderCandidate.singleton_not_all_patterns
example : PidSxDnfOrderJudgeTargets.binary_diagonal_collision := @PidSxDnfOrderCandidate.binary_diagonal_collision
example : PidSxDnfOrderJudgeAliases.binary_diagonal_collision := @PidSxDnfOrderCandidate.binary_diagonal_collision
example : PidSxDnfOrderJudgeTargets.antichain_premise_is_load_bearing := @PidSxDnfOrderCandidate.antichain_premise_is_load_bearing
example : PidSxDnfOrderJudgeAliases.antichain_premise_is_load_bearing := @PidSxDnfOrderCandidate.antichain_premise_is_load_bearing

run_cmd liftTermElabM do
  let roster : List Name := [
    ``PidSxDnfOrderCandidate.order_iff_dnf,
    ``PidSxDnfOrderCandidate.antichain_antisymm,
    ``PidSxDnfOrderCandidate.dnf_injective_on_antichains,
    ``PidSxDnfOrderCandidate.source_event_iff_dnf,
    ``PidSxDnfOrderCandidate.order_implies_source_event_subset,
    ``PidSxDnfOrderCandidate.order_iff_implication_on_realizing_domain,
    ``PidSxDnfOrderCandidate.alternate_values_realize_all_patterns,
    ``PidSxDnfOrderCandidate.source_event_injective_on_realizing_domain,
    ``PidSxDnfOrderCandidate.order_implies_target_restricted_subset,
    ``PidSxDnfOrderCandidate.singleton_event_collision,
    ``PidSxDnfOrderCandidate.singleton_not_all_patterns,
    ``PidSxDnfOrderCandidate.binary_diagonal_collision,
    ``PidSxDnfOrderCandidate.antichain_premise_is_load_bearing]
  PidSxDnfOrderJudge.checkPublicRoster roster
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.order_iff_dnf ``PidSxDnfOrderJudgeTargets.order_iff_dnf ``PidSxDnfOrderJudgeAliases.order_iff_dnf
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.antichain_antisymm ``PidSxDnfOrderJudgeTargets.antichain_antisymm ``PidSxDnfOrderJudgeAliases.antichain_antisymm
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.dnf_injective_on_antichains ``PidSxDnfOrderJudgeTargets.dnf_injective_on_antichains ``PidSxDnfOrderJudgeAliases.dnf_injective_on_antichains
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.source_event_iff_dnf ``PidSxDnfOrderJudgeTargets.source_event_iff_dnf ``PidSxDnfOrderJudgeAliases.source_event_iff_dnf
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.order_implies_source_event_subset ``PidSxDnfOrderJudgeTargets.order_implies_source_event_subset ``PidSxDnfOrderJudgeAliases.order_implies_source_event_subset
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.order_iff_implication_on_realizing_domain ``PidSxDnfOrderJudgeTargets.order_iff_implication_on_realizing_domain ``PidSxDnfOrderJudgeAliases.order_iff_implication_on_realizing_domain
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.alternate_values_realize_all_patterns ``PidSxDnfOrderJudgeTargets.alternate_values_realize_all_patterns ``PidSxDnfOrderJudgeAliases.alternate_values_realize_all_patterns
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.source_event_injective_on_realizing_domain ``PidSxDnfOrderJudgeTargets.source_event_injective_on_realizing_domain ``PidSxDnfOrderJudgeAliases.source_event_injective_on_realizing_domain
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.order_implies_target_restricted_subset ``PidSxDnfOrderJudgeTargets.order_implies_target_restricted_subset ``PidSxDnfOrderJudgeAliases.order_implies_target_restricted_subset
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.singleton_event_collision ``PidSxDnfOrderJudgeTargets.singleton_event_collision ``PidSxDnfOrderJudgeAliases.singleton_event_collision
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.singleton_not_all_patterns ``PidSxDnfOrderJudgeTargets.singleton_not_all_patterns ``PidSxDnfOrderJudgeAliases.singleton_not_all_patterns
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.binary_diagonal_collision ``PidSxDnfOrderJudgeTargets.binary_diagonal_collision ``PidSxDnfOrderJudgeAliases.binary_diagonal_collision
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
  let result ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderCandidate.antichain_premise_is_load_bearing ``PidSxDnfOrderJudgeTargets.antichain_premise_is_load_bearing ``PidSxDnfOrderJudgeAliases.antichain_premise_is_load_bearing
  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)
