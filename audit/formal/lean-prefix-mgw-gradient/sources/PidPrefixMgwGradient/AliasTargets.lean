import PidPrefixMgwGradient.Contract

/-! Contract-facing closed views only. No theorem proof or execution is supplied. -/
set_option autoImplicit false
set_option warningAsError true
universe u v w x
namespace PidPrefixMgwGradientAliasTargets

def full_inverse_row : Prop :=
  PidPrefixMgwGradientContract.full_inverse_row_target.{u}

def scalar_remainder_calculus : Prop :=
  PidPrefixMgwGradientContract.scalar_remainder_calculus_target

def native_cumulative_increments : Prop :=
  PidPrefixMgwGradientContract.native_cumulative_increments_target.{u, v, w}

def actual_atom_remainder : Prop :=
  PidPrefixMgwGradientContract.actual_atom_remainder_target.{u, v, w}

def finite_block_score_derivative : Prop :=
  PidPrefixMgwGradientContract.finite_block_score_derivative_target.{u, v, w}

def actual_atom_score_bias : Prop :=
  PidPrefixMgwGradientContract.actual_atom_score_bias_target.{u, v, w}

def finite_latent_pushforward : Prop :=
  PidPrefixMgwGradientContract.finite_latent_pushforward_target.{u, v, w, x}

def finite_latent_score_derivative : Prop :=
  PidPrefixMgwGradientContract.finite_latent_score_derivative_target.{u, v, w, x}

def finite_encoder_score : Prop :=
  PidPrefixMgwGradientContract.finite_encoder_score_target.{u, v, w}

def score_second_moment : Prop :=
  PidPrefixMgwGradientContract.score_second_moment_target.{u, v, w}

def latent_score_second_moment : Prop :=
  PidPrefixMgwGradientContract.latent_score_second_moment_target.{u, v, w, x}

end PidPrefixMgwGradientAliasTargets
