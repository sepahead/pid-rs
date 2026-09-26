import Mathlib.Algebra.Order.BigOperators.Ring.Finset
import Mathlib.Algebra.Order.Field.Basic
import Mathlib.Data.Fintype.Pi
import Mathlib.Data.Fintype.Prod
import Mathlib.Data.Fintype.Powerset
import Mathlib.Data.Real.Basic

/-!
# Shared-exclusion events as fault-consistency sets

Finite, law-free core of the fault-tolerance reading of the Makkeh–Gutknecht–Wibral
shared-exclusion events, plus the probability bound that makes the corresponding forecaster
valid under tolerated faults.

* `mgwEvent α r s` : the state `s` agrees with the report `r` on at least one collection
  `a ∈ α` (OR across collections, AND inside a collection).
* `disagree r s`   : the set of coordinates where `s` and `r` differ.
* `Tolerates α F`  : some collection of `α` avoids the fault set `F`.
-/

open Finset

namespace FaultTolerantInformation

variable {n : ℕ} {σ : Fin n → Type*} [∀ i, DecidableEq (σ i)]

/-- The MGW shared-exclusion event of the antichain `α` around the report `r`. -/
def mgwEvent (α : Finset (Finset (Fin n))) (r s : ∀ i, σ i) : Prop :=
  ∃ a ∈ α, ∀ i ∈ a, s i = r i

/-- Coordinates at which the state `s` differs from the report `r`. -/
def disagree (r s : ∀ i, σ i) : Finset (Fin n) :=
  univ.filter fun i => s i ≠ r i

/-- `α` tolerates the fault set `F` when at least one collection of `α` avoids `F`. -/
def Tolerates (α : Finset (Finset (Fin n))) (F : Finset (Fin n)) : Prop :=
  ∃ a ∈ α, Disjoint a F

/-- **Theorem 1.** A state lies in the shared-exclusion event exactly when its disagreement set
with the report is a fault set that the antichain tolerates. -/
theorem mgwEvent_iff_tolerates (α : Finset (Finset (Fin n))) (r s : ∀ i, σ i) :
    mgwEvent α r s ↔ Tolerates α (disagree r s) := by
  constructor
  · rintro ⟨a, ha, h⟩
    refine ⟨a, ha, Finset.disjoint_left.mpr ?_⟩
    intro i hia hid
    simp only [disagree, mem_filter, mem_univ, true_and] at hid
    exact hid (h i hia)
  · rintro ⟨a, ha, hdis⟩
    refine ⟨a, ha, fun i hia => ?_⟩
    by_contra hne
    exact Finset.disjoint_left.mp hdis hia (by simp [disagree, hne])

/-- Disagreement is symmetric, so "the truth lies in the event around the report" and
"the report lies in the event around the truth" are the same statement. -/
theorem disagree_comm (r s : ∀ i, σ i) : disagree r s = disagree s r := by
  ext i
  simp [disagree, ne_comm]

/-- **Corollary 1 (threshold antichains).** The antichain of all `(n - f)`-subsets tolerates
exactly the fault sets with at most `f` elements. -/
theorem tolerates_powersetCard_iff (f : ℕ) (hf : f < n) (F : Finset (Fin n)) :
    Tolerates (univ.powersetCard (n - f)) F ↔ F.card ≤ f := by
  constructor
  · rintro ⟨a, ha, hdis⟩
    rw [mem_powersetCard] at ha
    have hsub : a ⊆ Fᶜ := fun i hi => by
      rw [mem_compl]
      exact Finset.disjoint_left.mp hdis hi
    have hcard := card_le_card hsub
    rw [card_compl, Fintype.card_fin, ha.2] at hcard
    have hF : F.card ≤ n := by simpa using card_le_univ F
    omega
  · intro hF
    have hbound : n - f ≤ (Fᶜ).card := by
      rw [card_compl, Fintype.card_fin]
      omega
    obtain ⟨a, haF, hacard⟩ := exists_subset_card_eq hbound
    refine ⟨a, ?_, ?_⟩
    · rw [mem_powersetCard]
      exact ⟨subset_univ a, hacard⟩
    · rw [Finset.disjoint_left]
      intro i hia hiF
      exact (mem_compl.mp (haF hia)) hiF

/-- **Corollary 1, event form.** For the threshold antichain, the shared-exclusion event
around a report is the Hamming ball of radius `f`. -/
theorem mgwEvent_powersetCard_iff (f : ℕ) (hf : f < n) (r s : ∀ i, σ i) :
    mgwEvent (univ.powersetCard (n - f)) r s ↔ (disagree r s).card ≤ f := by
  rw [mgwEvent_iff_tolerates, tolerates_powersetCard_iff f hf]

/-- The redundancy order: `α ⪯ β` when every collection of `β` contains a collection of `α`. -/
def RedLE (α β : Finset (Finset (Fin n))) : Prop :=
  ∀ b ∈ β, ∃ a ∈ α, a ⊆ b

omit [∀ i, DecidableEq (σ i)] in
/-- **Monotonicity.** A lower node has a larger event: `α ⪯ β` implies that the event of `β`
is contained in the event of `α`. Hence the informative term `-log P(event)` is monotone. -/
theorem mgwEvent_mono {α β : Finset (Finset (Fin n))} (h : RedLE α β) {r s : ∀ i, σ i}
    (hs : mgwEvent β r s) : mgwEvent α r s := by
  obtain ⟨b, hb, hbs⟩ := hs
  obtain ⟨a, ha, hab⟩ := h b hb
  exact ⟨a, ha, fun i hi => hbs i (hab hi)⟩

omit [∀ i, DecidableEq (σ i)] in
/-- A lower node tolerates every fault set that a higher node tolerates. -/
theorem tolerates_mono {α β : Finset (Finset (Fin n))} (h : RedLE α β) {F : Finset (Fin n)}
    (hF : Tolerates β F) : Tolerates α F := by
  obtain ⟨b, hb, hdis⟩ := hF
  obtain ⟨a, ha, hab⟩ := h b hb
  exact ⟨a, ha, Finset.disjoint_of_subset_left hab hdis⟩

section Probability

variable [∀ i, Fintype (σ i)] {τ : Type*} [Fintype τ] [DecidableEq τ]

/-- A finite joint law of sources and target, as a nonnegative mass function with total one. -/
structure FiniteLaw (σ : Fin n → Type*) [∀ i, Fintype (σ i)] (τ : Type*) [Fintype τ] where
  mass : (∀ i, σ i) × τ → ℝ
  nonneg : ∀ z, 0 ≤ mass z
  total : ∑ z, mass z = 1

variable (P : FiniteLaw σ τ)

open Classical in
/-- Mass of `{S ∈ event(α, r)} × {T = t}`. -/
noncomputable def eventTargetMass (α : Finset (Finset (Fin n))) (r : ∀ i, σ i) (t : τ) : ℝ :=
  ∑ z ∈ univ.filter (fun z : (∀ i, σ i) × τ => mgwEvent α r z.1 ∧ z.2 = t), P.mass z

open Classical in
/-- Mass of `{S ∈ event(α, r)}`. -/
noncomputable def eventMass (α : Finset (Finset (Fin n))) (r : ∀ i, σ i) : ℝ :=
  ∑ z ∈ univ.filter (fun z : (∀ i, σ i) × τ => mgwEvent α r z.1), P.mass z

omit [∀ i, DecidableEq (σ i)] [DecidableEq τ] in
/-- The event mass is at most one. -/
theorem eventMass_le_one (α : Finset (Finset (Fin n))) (r : ∀ i, σ i) :
    eventMass P α r ≤ 1 := by
  classical
  unfold eventMass
  calc ∑ z ∈ univ.filter _, P.mass z ≤ ∑ z, P.mass z :=
        sum_le_sum_of_subset_of_nonneg (subset_univ _) (fun z _ _ => P.nonneg z)
    _ = 1 := P.total

omit [∀ i, DecidableEq (σ i)] in
/-- **Theorem 2 (validity).** If the true realization `(s', t)` lies in the event around the
report, then the event-conditioned forecast gives the true target at least the true joint mass:
`q(t | r) = eventTargetMass / eventMass ≥ P(s', t)`. Consequently its log loss is at most
`-log P(s', t)`, whatever report inside the tolerated fault sets an adversary chooses. -/
theorem forecast_ge_true_mass (α : Finset (Finset (Fin n))) (r s' : ∀ i, σ i) (t : τ)
    (hs' : mgwEvent α r s') (hpos : 0 < P.mass (s', t)) :
    P.mass (s', t) ≤ eventTargetMass P α r t / eventMass P α r := by
  classical
  have hmem_t : (s', t) ∈ univ.filter
      (fun z : (∀ i, σ i) × τ => mgwEvent α r z.1 ∧ z.2 = t) := by
    simp [hs']
  have hmem : (s', t) ∈ univ.filter (fun z : (∀ i, σ i) × τ => mgwEvent α r z.1) := by
    simp [hs']
  have hnum : P.mass (s', t) ≤ eventTargetMass P α r t := by
    unfold eventTargetMass
    exact single_le_sum (fun z _ => P.nonneg z) hmem_t
  have hden_pos : 0 < eventMass P α r := by
    unfold eventMass
    exact lt_of_lt_of_le hpos (single_le_sum (fun z _ => P.nonneg z) hmem)
  have hden_le : eventMass P α r ≤ 1 := eventMass_le_one P α r
  rw [le_div_iff₀ hden_pos]
  calc P.mass (s', t) * eventMass P α r ≤ P.mass (s', t) * 1 :=
        mul_le_mul_of_nonneg_left hden_le (P.nonneg _)
    _ = P.mass (s', t) := mul_one _
    _ ≤ eventTargetMass P α r t := hnum

/-- **Theorem 2, fault form.** For every tolerated fault pattern between the truth `s'` and the
report `r`, the forecast of the true target is at least the true joint mass. -/
theorem forecast_valid_under_tolerated_faults (α : Finset (Finset (Fin n)))
    (r s' : ∀ i, σ i) (t : τ) (hfault : Tolerates α (disagree r s'))
    (hpos : 0 < P.mass (s', t)) :
    P.mass (s', t) ≤ eventTargetMass P α r t / eventMass P α r :=
  forecast_ge_true_mass P α r s' t ((mgwEvent_iff_tolerates α r s').mpr hfault) hpos

end Probability

section ParityExample

/-! ### Three-bit parity: exact counts behind the profile `(log 2, -log 2, log (8/7))`

The sources are three independent uniform bits and the target is their parity, so each of the
eight source states has mass `1/8` and fixes the target. The counts below give every event
probability in the example: a Hamming ball of radius `f` around `r` has mass `card / 8`. -/

/-- Parity of three bits. -/
def parity3 (s : Fin 3 → Bool) : Bool := xor (s 0) (xor (s 1) (s 2))

/-- Number of coordinates at which `s` differs from `r`. -/
def hamming3 (r s : Fin 3 → Bool) : ℕ := (univ.filter fun i => s i ≠ r i).card

/-- Radius one: the ball holds 4 states, and only the center has the center's parity. -/
theorem parity_ball_one (r : Fin 3 → Bool) :
    (univ.filter fun s : Fin 3 → Bool => hamming3 r s ≤ 1).card = 4 ∧
    (univ.filter fun s : Fin 3 → Bool =>
      hamming3 r s ≤ 1 ∧ parity3 s = parity3 r).card = 1 := by
  revert r
  decide

/-- Radius two: the ball holds 7 states, and 4 of them have the center's parity. -/
theorem parity_ball_two (r : Fin 3 → Bool) :
    (univ.filter fun s : Fin 3 → Bool => hamming3 r s ≤ 2).card = 7 ∧
    (univ.filter fun s : Fin 3 → Bool =>
      hamming3 r s ≤ 2 ∧ parity3 s = parity3 r).card = 4 := by
  revert r
  decide

/-- Each parity value is taken by exactly 4 of the 8 states. -/
theorem parity_class_size (t : Bool) :
    (univ.filter fun s : Fin 3 → Bool => parity3 s = t).card = 4 := by
  revert t
  decide

end ParityExample

end FaultTolerantInformation
