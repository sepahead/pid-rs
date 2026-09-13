import PidPrefixProbability.Contract

set_option autoImplicit false
set_option warningAsError true
universe u v w
namespace PidPrefixProbabilityAliasTargets

def finite_law_measure : Prop := PidPrefixProbabilityContract.finite_law_measure_target.{u, v, w}

def finite_product_law : Prop := PidPrefixProbabilityContract.finite_product_law_target.{u, v, w}

def positive_increment_expectation : Prop := PidPrefixProbabilityContract.positive_increment_expectation_target.{u, v, w}

def negative_increment_expectation : Prop := PidPrefixProbabilityContract.negative_increment_expectation_target.{u, v, w}

def block_range : Prop := PidPrefixProbabilityContract.block_range_target.{u, v, w}

def block_product_independence : Prop := PidPrefixProbabilityContract.block_product_independence_target.{u, v, w}

end PidPrefixProbabilityAliasTargets
