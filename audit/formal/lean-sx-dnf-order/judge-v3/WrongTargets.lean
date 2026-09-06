import Contract

/-! Valid proofs of the wrong types. None is a candidate export. -/
set_option autoImplicit false
set_option warningAsError true
namespace PidSxDnfOrderWrongTargets
open PidSxDnfOrderContract
universe u

theorem fin3_only (alpha beta : Finset (Finset (Fin 3))) :
    RedundancyLE alpha beta ↔ ∀ e : Fin 3 → Bool, DNF beta e → DNF alpha e := by
  constructor
  · intro h e he
    obtain ⟨b, hb, hbe⟩ := he
    obtain ⟨a, ha, hab⟩ := h b hb
    exact ⟨a, ha, fun i hi => hbe i (hab hi)⟩
  · intro h b hb
    have witness : DNF beta (fun i => decide (i ∈ b)) :=
      ⟨b, hb, fun _ hi => decide_eq_true hi⟩
    obtain ⟨a, ha, hab⟩ := h _ witness
    exact ⟨a, ha, fun i hi => of_decide_eq_true (hab i hi)⟩

theorem explicit_receiver (S : Type u) [DecidableEq S] (receiver : GenericObligations S) :
    order_iff_dnf_target S := receiver.order_iff_dnf

theorem implicit_receiver (S : Type u) [DecidableEq S] {receiver : GenericObligations S} :
    order_iff_dnf_target S := receiver.order_iff_dnf

theorem assumed_conclusion (S : Type u) [DecidableEq S] (assumption : order_iff_dnf_target S) :
    order_iff_dnf_target S := assumption

def EquivalentPremise (S : Type u) [DecidableEq S] : Prop := order_iff_dnf_target S

theorem renamed_premise (S : Type u) [DecidableEq S] (renamed : EquivalentPremise S) :
    order_iff_dnf_target S := renamed

end PidSxDnfOrderWrongTargets
