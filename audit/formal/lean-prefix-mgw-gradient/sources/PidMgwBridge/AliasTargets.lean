import PidMgwBridge.Contract

/-! Alias view of complete closed target types. No theorem values. -/
set_option autoImplicit false
set_option warningAsError true
universe u v w
namespace PidMgwBridgeAliasTargets

def actual_join_lub : Prop := PidMgwBridgeContract.actual_join_lub_target.{u}

def mismatch_generator_and_exclusion : Prop := PidMgwBridgeContract.mismatch_generator_and_exclusion_target.{u, v, w}

def generator_nonnegative_and_total : Prop := PidMgwBridgeContract.generator_nonnegative_and_total_target.{u, v, w}

def generator_lower_cumulative : Prop := PidMgwBridgeContract.generator_lower_cumulative_target.{u, v, w}

def target_conditioning_mass : Prop := PidMgwBridgeContract.target_conditioning_mass_target.{u, v, w}

def supported_anchor_domains : Prop := PidMgwBridgeContract.supported_anchor_domains_target.{u, v, w}

def conditional_generator_support : Prop := PidMgwBridgeContract.conditional_generator_support_target.{u, v, w}

def informative_inverse_identification : Prop := PidMgwBridgeContract.informative_inverse_identification_target.{u, v, w}

def misinformative_inverse_identification : Prop := PidMgwBridgeContract.misinformative_inverse_identification_target.{u, v, w}

def component_nonnegative_strict_support : Prop := PidMgwBridgeContract.component_nonnegative_strict_support_target.{u, v, w}

def signed_mgw_cumulative : Prop := PidMgwBridgeContract.signed_mgw_cumulative_target.{u, v, w}

end PidMgwBridgeAliasTargets
