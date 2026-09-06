import Contract

/-! Reviewer-owned receiver-free raw propositions. No candidate proof is imported here. -/
set_option autoImplicit false
set_option warningAsError true

namespace PidSxDnfOrderJudgeTargets
universe u v w

def order_iff_dnf : Prop :=
  ∀ (S : Type u) [DecidableEq S] (alpha beta : Finset (Finset S)),
    (∀ b ∈ beta, ∃ a ∈ alpha, a ⊆ b) ↔
    ∀ e : S → Bool,
      (∃ b ∈ beta, ∀ i ∈ b, e i = true) →
      (∃ a ∈ alpha, ∀ i ∈ a, e i = true)

def antichain_antisymm : Prop :=
  ∀ (S : Type u) [DecidableEq S] (alpha beta : Finset (Finset S)),
    (∀ a ∈ alpha, ∀ b ∈ alpha, a ⊆ b → a = b) →
    (∀ a ∈ beta, ∀ b ∈ beta, a ⊆ b → a = b) →
    (∀ b ∈ beta, ∃ a ∈ alpha, a ⊆ b) →
    (∀ a ∈ alpha, ∃ b ∈ beta, b ⊆ a) → alpha = beta

def dnf_injective_on_antichains : Prop :=
  ∀ (S : Type u) [DecidableEq S] (alpha beta : Finset (Finset S)),
    (∀ a ∈ alpha, ∀ b ∈ alpha, a ⊆ b → a = b) →
    (∀ a ∈ beta, ∀ b ∈ beta, a ⊆ b → a = b) →
    (∀ e : S → Bool,
      (∃ a ∈ alpha, ∀ i ∈ a, e i = true) ↔
      (∃ b ∈ beta, ∀ i ∈ b, e i = true)) → alpha = beta

def source_event_iff_dnf : Prop :=
  ∀ (S : Type u) (V : S → Type v) (T : Type w)
    [Fintype S] [∀ i, Fintype (V i)] [Fintype T]
    [DecidableEq S] [∀ i, DecidableEq (V i)] [DecidableEq T],
  ∀ (alpha : Finset (Finset S)) (x y : PidFiniteConvergence.CategoricalKey S V T),
    y ∈ PidFiniteConvergence.sxSourceEvent alpha x ↔
    ∃ a ∈ alpha, ∀ i ∈ a, decide (x.1 i = y.1 i) = true

def order_implies_source_event_subset : Prop :=
  ∀ (S : Type u) (V : S → Type v) (T : Type w)
    [Fintype S] [∀ i, Fintype (V i)] [Fintype T]
    [DecidableEq S] [∀ i, DecidableEq (V i)] [DecidableEq T],
  ∀ (alpha beta : Finset (Finset S)) (x : PidFiniteConvergence.CategoricalKey S V T),
    (∀ b ∈ beta, ∃ a ∈ alpha, a ⊆ b) →
    PidFiniteConvergence.sxSourceEvent beta x ⊆ PidFiniteConvergence.sxSourceEvent alpha x

def order_iff_implication_on_realizing_domain : Prop :=
  ∀ (S : Type u) (V : S → Type v) (T : Type w)
    [Fintype S] [∀ i, Fintype (V i)] [Fintype T]
    [DecidableEq S] [∀ i, DecidableEq (V i)] [DecidableEq T],
  ∀ (alpha beta : Finset (Finset S)) (x : PidFiniteConvergence.CategoricalKey S V T)
    (domain : Set (PidFiniteConvergence.CategoricalKey S V T)),
    (∀ e : S → Bool, ∃ y ∈ domain, (fun i => decide (x.1 i = y.1 i)) = e) →
    ((∀ b ∈ beta, ∃ a ∈ alpha, a ⊆ b) ↔
      ∀ y ∈ domain, y ∈ PidFiniteConvergence.sxSourceEvent beta x →
        y ∈ PidFiniteConvergence.sxSourceEvent alpha x)

def alternate_values_realize_all_patterns : Prop :=
  ∀ (S : Type u) (V : S → Type v) (T : Type w)
    [Fintype S] [∀ i, Fintype (V i)] [Fintype T]
    [DecidableEq S] [∀ i, DecidableEq (V i)] [DecidableEq T],
  ∀ (x : PidFiniteConvergence.CategoricalKey S V T) (alternate : (i : S) → V i),
    (∀ i, alternate i ≠ x.1 i) →
    ∀ e : S → Bool, ∃ y ∈ (Set.univ : Set (PidFiniteConvergence.CategoricalKey S V T)),
      (fun i => decide (x.1 i = y.1 i)) = e

def source_event_injective_on_realizing_domain : Prop :=
  ∀ (S : Type u) (V : S → Type v) (T : Type w)
    [Fintype S] [∀ i, Fintype (V i)] [Fintype T]
    [DecidableEq S] [∀ i, DecidableEq (V i)] [DecidableEq T],
  ∀ (alpha beta : Finset (Finset S)),
    (∀ a ∈ alpha, ∀ b ∈ alpha, a ⊆ b → a = b) →
    (∀ a ∈ beta, ∀ b ∈ beta, a ⊆ b → a = b) →
    ∀ (x : PidFiniteConvergence.CategoricalKey S V T)
      (domain : Set (PidFiniteConvergence.CategoricalKey S V T)),
    (∀ e : S → Bool, ∃ y ∈ domain, (fun i => decide (x.1 i = y.1 i)) = e) →
    (∀ y ∈ domain,
      y ∈ PidFiniteConvergence.sxSourceEvent alpha x ↔
      y ∈ PidFiniteConvergence.sxSourceEvent beta x) → alpha = beta

def order_implies_target_restricted_subset : Prop :=
  ∀ (S : Type u) (V : S → Type v) (T : Type w)
    [Fintype S] [∀ i, Fintype (V i)] [Fintype T]
    [DecidableEq S] [∀ i, DecidableEq (V i)] [DecidableEq T],
  ∀ (alpha beta : Finset (Finset S)) (x : PidFiniteConvergence.CategoricalKey S V T),
    (∀ b ∈ beta, ∃ a ∈ alpha, a ⊆ b) →
    PidFiniteConvergence.sxTargetRestrictedEvent beta x ⊆
      PidFiniteConvergence.sxTargetRestrictedEvent alpha x


def singleton_event_collision : Prop :=
  (∀ a ∈ ({{0}} : Finset (Finset (Fin 3))), ∀ b ∈ ({{0}} : Finset (Finset (Fin 3))),
    a ⊆ b → a = b) ∧
  (∀ a ∈ ({{1}} : Finset (Finset (Fin 3))), ∀ b ∈ ({{1}} : Finset (Finset (Fin 3))),
    a ⊆ b → a = b) ∧
  ({{0}} : Finset (Finset (Fin 3))) ≠ {{1}} ∧
  ¬ (∀ b ∈ ({{1}} : Finset (Finset (Fin 3))), ∃ a ∈ ({{0}} : Finset (Finset (Fin 3))), a ⊆ b) ∧
  ¬ (∀ b ∈ ({{0}} : Finset (Finset (Fin 3))), ∃ a ∈ ({{1}} : Finset (Finset (Fin 3))), a ⊆ b) ∧
  PidFiniteConvergence.sxSourceEvent ({{0}} : Finset (Finset (Fin 3)))
      (fun _ => (), ()) =
    PidFiniteConvergence.sxSourceEvent ({{1}} : Finset (Finset (Fin 3)))
      (fun _ => (), ())

def singleton_not_all_patterns : Prop :=
  ¬ (∀ e : Fin 3 → Bool,
    ∃ y ∈ (Set.univ : Set (PidFiniteConvergence.CategoricalKey (Fin 3) (fun _ => Unit) Unit)),
      (fun i => decide (() = y.1 i)) = e)

def binary_diagonal_collision : Prop :=
  (∀ y : PidFiniteConvergence.CategoricalKey (Fin 3) (fun _ => Bool) Unit,
    (y.1 0 = y.1 1 ∧ y.1 1 = y.1 2) →
    (y ∈ PidFiniteConvergence.sxSourceEvent ({{0}} : Finset (Finset (Fin 3))) (fun _ => false, ()) ↔
      y ∈ PidFiniteConvergence.sxSourceEvent ({{1}} : Finset (Finset (Fin 3))) (fun _ => false, ()))) ∧
  PidFiniteConvergence.sxSourceEvent ({{0}} : Finset (Finset (Fin 3))) (fun _ => false, ()) ≠
    PidFiniteConvergence.sxSourceEvent ({{1}} : Finset (Finset (Fin 3))) (fun _ => false, ()) ∧
  ¬ (∀ e : Fin 3 → Bool,
    ∃ y : PidFiniteConvergence.CategoricalKey (Fin 3) (fun _ => Bool) Unit,
      (y.1 0 = y.1 1 ∧ y.1 1 = y.1 2) ∧
      (fun i => decide (false = y.1 i)) = e)

def antichain_premise_is_load_bearing : Prop :=
  ¬ (∀ a ∈ ({{0}, {0, 1}} : Finset (Finset (Fin 3))),
      ∀ b ∈ ({{0}, {0, 1}} : Finset (Finset (Fin 3))), a ⊆ b → a = b) ∧
  ({{0}, {0, 1}} : Finset (Finset (Fin 3))) ≠ {{0}} ∧
  (∀ b ∈ ({{0}} : Finset (Finset (Fin 3))),
    ∃ a ∈ ({{0}, {0, 1}} : Finset (Finset (Fin 3))), a ⊆ b) ∧
  (∀ b ∈ ({{0}, {0, 1}} : Finset (Finset (Fin 3))),
    ∃ a ∈ ({{0}} : Finset (Finset (Fin 3))), a ⊆ b) ∧
  (∀ e : Fin 3 → Bool,
    (∃ a ∈ ({{0}, {0, 1}} : Finset (Finset (Fin 3))), ∀ i ∈ a, e i = true) ↔
    (∃ a ∈ ({{0}} : Finset (Finset (Fin 3))), ∀ i ∈ a, e i = true))

end PidSxDnfOrderJudgeTargets
