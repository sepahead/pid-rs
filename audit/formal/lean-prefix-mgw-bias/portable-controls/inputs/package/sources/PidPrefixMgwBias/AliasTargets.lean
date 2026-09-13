import PidPrefixMgwBias.Contract
set_option autoImplicit false
set_option warningAsError true
universe u v w
namespace PidPrefixMgwBiasAliasTargets

def actual_finite_bias : Prop :=
  PidPrefixMgwBiasSource.actual_finite_bias_target.{u, v, w}

def fiber_inverse_moment : Prop :=
  PidPrefixMgwBiasSource.fiber_inverse_moment_target.{u, v}

def support_moment_bounds : Prop :=
  PidPrefixMgwBiasSource.support_moment_bounds_target.{u, v, w}

def projected_support_bias : Prop :=
  PidPrefixMgwBiasSource.projected_support_bias_target.{u, v, w}

def mass_floor_bias : Prop :=
  PidPrefixMgwBiasSource.mass_floor_bias_target.{u, v, w}

end PidPrefixMgwBiasAliasTargets
