import PidPrefixMgwGradient.Candidate
import PidPrefixMgwGradient.RawTargets
import PidPrefixMgwGradient.AliasTargets
import MgwBridgeDepsV1.SxDnf.JudgeCore

/-!
Reviewer-owned eleven-export inspection source. The accepted JudgeCore is reused unchanged.
This file awaits source admission and later elaboration; its result prefix is not a receipt.
-/
set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command
namespace PidPrefixMgwGradientJudge

private def checkPublicRoster (expected : List Name) : MetaM Unit := do
  let environment ← getEnv
  let observed := environment.constants.toList.filterMap fun (name, _) =>
    if name.toString.startsWith "PidPrefixMgwGradientCandidate." then some name else none
  unless observed.length == expected.length &&
      observed.all expected.contains && expected.all observed.contains do
    throwError "PREFIX_MGW_GRADIENT_JUDGE_EXPORT_ROSTER: expected exactly {expected.length} public declarations"

private def emitExport (declaration raw aliasView : Name) : MetaM Unit := do
  let result ← PidSxDnfOrderJudge.checkExport declaration raw aliasView
  IO.println ("PREFIX_MGW_GRADIENT_JUDGE_RESULT " ++ result.compress)

end PidPrefixMgwGradientJudge

example : PidPrefixMgwGradientRawTargets.full_inverse_row :=
  @PidPrefixMgwGradientCandidate.full_inverse_row
example : PidPrefixMgwGradientAliasTargets.full_inverse_row :=
  @PidPrefixMgwGradientCandidate.full_inverse_row

example : PidPrefixMgwGradientRawTargets.scalar_remainder_calculus :=
  @PidPrefixMgwGradientCandidate.scalar_remainder_calculus
example : PidPrefixMgwGradientAliasTargets.scalar_remainder_calculus :=
  @PidPrefixMgwGradientCandidate.scalar_remainder_calculus

example : PidPrefixMgwGradientRawTargets.native_cumulative_increments :=
  @PidPrefixMgwGradientCandidate.native_cumulative_increments
example : PidPrefixMgwGradientAliasTargets.native_cumulative_increments :=
  @PidPrefixMgwGradientCandidate.native_cumulative_increments

example : PidPrefixMgwGradientRawTargets.actual_atom_remainder :=
  @PidPrefixMgwGradientCandidate.actual_atom_remainder
example : PidPrefixMgwGradientAliasTargets.actual_atom_remainder :=
  @PidPrefixMgwGradientCandidate.actual_atom_remainder

example : PidPrefixMgwGradientRawTargets.finite_block_score_derivative :=
  @PidPrefixMgwGradientCandidate.finite_block_score_derivative
example : PidPrefixMgwGradientAliasTargets.finite_block_score_derivative :=
  @PidPrefixMgwGradientCandidate.finite_block_score_derivative

example : PidPrefixMgwGradientRawTargets.actual_atom_score_bias :=
  @PidPrefixMgwGradientCandidate.actual_atom_score_bias
example : PidPrefixMgwGradientAliasTargets.actual_atom_score_bias :=
  @PidPrefixMgwGradientCandidate.actual_atom_score_bias

example : PidPrefixMgwGradientRawTargets.finite_latent_pushforward :=
  @PidPrefixMgwGradientCandidate.finite_latent_pushforward
example : PidPrefixMgwGradientAliasTargets.finite_latent_pushforward :=
  @PidPrefixMgwGradientCandidate.finite_latent_pushforward

example : PidPrefixMgwGradientRawTargets.finite_latent_score_derivative :=
  @PidPrefixMgwGradientCandidate.finite_latent_score_derivative
example : PidPrefixMgwGradientAliasTargets.finite_latent_score_derivative :=
  @PidPrefixMgwGradientCandidate.finite_latent_score_derivative

example : PidPrefixMgwGradientRawTargets.finite_encoder_score :=
  @PidPrefixMgwGradientCandidate.finite_encoder_score
example : PidPrefixMgwGradientAliasTargets.finite_encoder_score :=
  @PidPrefixMgwGradientCandidate.finite_encoder_score

example : PidPrefixMgwGradientRawTargets.score_second_moment :=
  @PidPrefixMgwGradientCandidate.score_second_moment
example : PidPrefixMgwGradientAliasTargets.score_second_moment :=
  @PidPrefixMgwGradientCandidate.score_second_moment

example : PidPrefixMgwGradientRawTargets.latent_score_second_moment :=
  @PidPrefixMgwGradientCandidate.latent_score_second_moment
example : PidPrefixMgwGradientAliasTargets.latent_score_second_moment :=
  @PidPrefixMgwGradientCandidate.latent_score_second_moment

run_cmd liftTermElabM do
  let roster : List Name := [
    ``PidPrefixMgwGradientCandidate.full_inverse_row,
    ``PidPrefixMgwGradientCandidate.scalar_remainder_calculus,
    ``PidPrefixMgwGradientCandidate.native_cumulative_increments,
    ``PidPrefixMgwGradientCandidate.actual_atom_remainder,
    ``PidPrefixMgwGradientCandidate.finite_block_score_derivative,
    ``PidPrefixMgwGradientCandidate.actual_atom_score_bias,
    ``PidPrefixMgwGradientCandidate.finite_latent_pushforward,
    ``PidPrefixMgwGradientCandidate.finite_latent_score_derivative,
    ``PidPrefixMgwGradientCandidate.finite_encoder_score,
    ``PidPrefixMgwGradientCandidate.score_second_moment,
    ``PidPrefixMgwGradientCandidate.latent_score_second_moment]
  PidPrefixMgwGradientJudge.checkPublicRoster roster
  PidPrefixMgwGradientJudge.emitExport
    ``PidPrefixMgwGradientCandidate.full_inverse_row
    ``PidPrefixMgwGradientRawTargets.full_inverse_row
    ``PidPrefixMgwGradientAliasTargets.full_inverse_row
  PidPrefixMgwGradientJudge.emitExport
    ``PidPrefixMgwGradientCandidate.scalar_remainder_calculus
    ``PidPrefixMgwGradientRawTargets.scalar_remainder_calculus
    ``PidPrefixMgwGradientAliasTargets.scalar_remainder_calculus
  PidPrefixMgwGradientJudge.emitExport
    ``PidPrefixMgwGradientCandidate.native_cumulative_increments
    ``PidPrefixMgwGradientRawTargets.native_cumulative_increments
    ``PidPrefixMgwGradientAliasTargets.native_cumulative_increments
  PidPrefixMgwGradientJudge.emitExport
    ``PidPrefixMgwGradientCandidate.actual_atom_remainder
    ``PidPrefixMgwGradientRawTargets.actual_atom_remainder
    ``PidPrefixMgwGradientAliasTargets.actual_atom_remainder
  PidPrefixMgwGradientJudge.emitExport
    ``PidPrefixMgwGradientCandidate.finite_block_score_derivative
    ``PidPrefixMgwGradientRawTargets.finite_block_score_derivative
    ``PidPrefixMgwGradientAliasTargets.finite_block_score_derivative
  PidPrefixMgwGradientJudge.emitExport
    ``PidPrefixMgwGradientCandidate.actual_atom_score_bias
    ``PidPrefixMgwGradientRawTargets.actual_atom_score_bias
    ``PidPrefixMgwGradientAliasTargets.actual_atom_score_bias
  PidPrefixMgwGradientJudge.emitExport
    ``PidPrefixMgwGradientCandidate.finite_latent_pushforward
    ``PidPrefixMgwGradientRawTargets.finite_latent_pushforward
    ``PidPrefixMgwGradientAliasTargets.finite_latent_pushforward
  PidPrefixMgwGradientJudge.emitExport
    ``PidPrefixMgwGradientCandidate.finite_latent_score_derivative
    ``PidPrefixMgwGradientRawTargets.finite_latent_score_derivative
    ``PidPrefixMgwGradientAliasTargets.finite_latent_score_derivative
  PidPrefixMgwGradientJudge.emitExport
    ``PidPrefixMgwGradientCandidate.finite_encoder_score
    ``PidPrefixMgwGradientRawTargets.finite_encoder_score
    ``PidPrefixMgwGradientAliasTargets.finite_encoder_score
  PidPrefixMgwGradientJudge.emitExport
    ``PidPrefixMgwGradientCandidate.score_second_moment
    ``PidPrefixMgwGradientRawTargets.score_second_moment
    ``PidPrefixMgwGradientAliasTargets.score_second_moment
  PidPrefixMgwGradientJudge.emitExport
    ``PidPrefixMgwGradientCandidate.latent_score_second_moment
    ``PidPrefixMgwGradientRawTargets.latent_score_second_moment
    ``PidPrefixMgwGradientAliasTargets.latent_score_second_moment
