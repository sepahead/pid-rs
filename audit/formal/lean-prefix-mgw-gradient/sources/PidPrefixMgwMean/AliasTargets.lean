import PidPrefixMgwMean.Contract

/-! SOURCE-ONLY aliases of the three proposed closed proposition types. -/
set_option autoImplicit false
set_option warningAsError true
universe u v w
namespace PidPrefixMgwMeanAliasTargets

def word_coefficient_join_power : Prop :=
  PidPrefixMgwMeanContract.word_coefficient_join_power_target.{u, v, w}

def finite_block_expectation : Prop :=
  PidPrefixMgwMeanContract.finite_block_expectation_target.{u, v, w}

def prefix_expectations_to_mgw_mean : Prop :=
  PidPrefixMgwMeanContract.prefix_expectations_to_mgw_mean_target.{u, v, w}

end PidPrefixMgwMeanAliasTargets
