import Contract

set_option autoImplicit false
set_option warningAsError true

namespace PidSxDnfOrderJudgeAliases
universe u v w

def order_iff_dnf : Prop :=
  ∀ (S : Type u) [DecidableEq S], PidSxDnfOrderContract.order_iff_dnf_target S

def antichain_antisymm : Prop :=
  ∀ (S : Type u) [DecidableEq S], PidSxDnfOrderContract.antichain_antisymm_target S

def dnf_injective_on_antichains : Prop :=
  ∀ (S : Type u) [DecidableEq S], PidSxDnfOrderContract.dnf_injective_on_antichains_target S

def source_event_iff_dnf : Prop :=
  ∀ (S : Type u) (V : S → Type v) (T : Type w)
    [Fintype S] [∀ i, Fintype (V i)] [Fintype T]
    [DecidableEq S] [∀ i, DecidableEq (V i)] [DecidableEq T],
    PidSxDnfOrderContract.source_event_iff_dnf_target S V T

def order_implies_source_event_subset : Prop :=
  ∀ (S : Type u) (V : S → Type v) (T : Type w)
    [Fintype S] [∀ i, Fintype (V i)] [Fintype T]
    [DecidableEq S] [∀ i, DecidableEq (V i)] [DecidableEq T],
    PidSxDnfOrderContract.order_implies_source_event_subset_target S V T

def order_iff_implication_on_realizing_domain : Prop :=
  ∀ (S : Type u) (V : S → Type v) (T : Type w)
    [Fintype S] [∀ i, Fintype (V i)] [Fintype T]
    [DecidableEq S] [∀ i, DecidableEq (V i)] [DecidableEq T],
    PidSxDnfOrderContract.order_iff_implication_on_realizing_domain_target S V T

def alternate_values_realize_all_patterns : Prop :=
  ∀ (S : Type u) (V : S → Type v) (T : Type w)
    [Fintype S] [∀ i, Fintype (V i)] [Fintype T]
    [DecidableEq S] [∀ i, DecidableEq (V i)] [DecidableEq T],
    PidSxDnfOrderContract.alternate_values_realize_all_patterns_target S V T

def source_event_injective_on_realizing_domain : Prop :=
  ∀ (S : Type u) (V : S → Type v) (T : Type w)
    [Fintype S] [∀ i, Fintype (V i)] [Fintype T]
    [DecidableEq S] [∀ i, DecidableEq (V i)] [DecidableEq T],
    PidSxDnfOrderContract.source_event_injective_on_realizing_domain_target S V T

def order_implies_target_restricted_subset : Prop :=
  ∀ (S : Type u) (V : S → Type v) (T : Type w)
    [Fintype S] [∀ i, Fintype (V i)] [Fintype T]
    [DecidableEq S] [∀ i, DecidableEq (V i)] [DecidableEq T],
    PidSxDnfOrderContract.order_implies_target_restricted_subset_target S V T

def singleton_event_collision : Prop :=
  PidSxDnfOrderContract.singleton_event_collision_target

def singleton_not_all_patterns : Prop :=
  PidSxDnfOrderContract.singleton_not_all_patterns_target

def binary_diagonal_collision : Prop :=
  PidSxDnfOrderContract.binary_diagonal_collision_target

def antichain_premise_is_load_bearing : Prop :=
  PidSxDnfOrderContract.antichain_premise_is_load_bearing_target

end PidSxDnfOrderJudgeAliases
