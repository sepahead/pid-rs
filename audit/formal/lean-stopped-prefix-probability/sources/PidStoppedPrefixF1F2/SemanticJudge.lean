import PidStoppedPrefixF1F2.Candidate
import PidStoppedPrefixStageA.RawTargets
import PidStoppedPrefixStageA.AliasTargets
import MgwBridgeDepsV1.SxDnf.JudgeCore

/- Source-only reviewer proposal. Root must independently freeze this judge before use.
   Exactly F1 and F2; no F4, full Stage A, or stopped-process acceptance. -/
set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command
universe u v w

example : PidStoppedPrefixStageARawTargets.first_hit_factorization.{u, v, w} :=
  @PidStoppedPrefixF1F2Candidate.first_hit_factorization

example : PidStoppedPrefixStageAAliasTargets.first_hit_factorization.{u, v, w} :=
  @PidStoppedPrefixF1F2Candidate.first_hit_factorization

example : PidStoppedPrefixStageARawTargets.first_hit_mass.{u, v, w} :=
  @PidStoppedPrefixF1F2Candidate.first_hit_mass

example : PidStoppedPrefixStageAAliasTargets.first_hit_mass.{u, v, w} :=
  @PidStoppedPrefixF1F2Candidate.first_hit_mass

run_cmd liftTermElabM do
  let expected : List Name := [
    ``PidStoppedPrefixF1F2Candidate.first_hit_factorization,
    ``PidStoppedPrefixF1F2Candidate.first_hit_mass]
  let environment ← getEnv
  let observed := environment.constants.toList.filterMap fun (name, _) =>
    if name.toString.startsWith "PidStoppedPrefixF1F2Candidate." then some name else none
  unless observed.length == expected.length &&
      observed.all expected.contains && expected.all observed.contains do
    throwError "F1F2_JUDGE_EXPORT_ROSTER: expected exactly two universal F1/F2 theorems"
  let factorization ← PidSxDnfOrderJudge.checkExport
    ``PidStoppedPrefixF1F2Candidate.first_hit_factorization
    ``PidStoppedPrefixStageARawTargets.first_hit_factorization
    ``PidStoppedPrefixStageAAliasTargets.first_hit_factorization
  IO.println ("STOPPED_PREFIX_F1F2_JUDGE_RESULT " ++ factorization.compress)
  let mass ← PidSxDnfOrderJudge.checkExport
    ``PidStoppedPrefixF1F2Candidate.first_hit_mass
    ``PidStoppedPrefixStageARawTargets.first_hit_mass
    ``PidStoppedPrefixStageAAliasTargets.first_hit_mass
  IO.println ("STOPPED_PREFIX_F1F2_JUDGE_RESULT " ++ mass.compress)
