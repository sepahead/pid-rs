import PidStoppedPrefixStageA.Contract
/- INERT reviewer-owned alias view. F3 is intentionally absent. -/
set_option autoImplicit false
set_option warningAsError true
universe u v w
namespace PidStoppedPrefixStageAAliasTargets
def first_hit_factorization : Prop := PidStoppedPrefixStageAContract.first_hit_factorization_target.{u, v, w}
def first_hit_mass : Prop := PidStoppedPrefixStageAContract.first_hit_mass_target.{u, v, w}
def native_return_kills : Prop := PidStoppedPrefixStageAContract.native_return_kills_target.{u, v, w}
end PidStoppedPrefixStageAAliasTargets
