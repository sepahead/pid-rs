import Contract
import Mathlib.Algebra.Order.BigOperators.Group.Finset

-- SOURCE ONLY: no compilation, import closure, or acceptance claimed.
-- Original Contract SHA256:
-- 61c8d92c30a934c91aa025c27d24468619f6974fdc9154edba57d5deb701a55e
-- No dependency on the original nineteen-target Candidate proofs.

namespace PidFin3AlphabetCounts
open PidFin3Contract

universe u v z

abbrev Observation (Alpha : Source → Type u) := (i : Source) → Alpha i

variable {Alpha : Source → Type u} {Beta : Type v} {J : Type z}

def sourceEvent (A : Family) (s : J → Observation Alpha) (key cell : J) : Prop :=
  ∃ a ∈ A, ∀ i ∈ a, s cell i = s key i

theorem sourceEvent_antitone (A B : Family)
    (hAB : PidFin3Contract.LE A B) (s : J → Observation Alpha) (key cell : J) :
    sourceEvent B s key cell → sourceEvent A s key cell := by
  intro hB
  rcases hB with ⟨b, hb, hEq⟩
  rcases hAB b hb with ⟨a, ha, hab⟩
  exact ⟨a, ha, fun i hi => hEq i (hab hi)⟩

theorem sourceEvent_key_iff (A : Family) (s : J → Observation Alpha) (key : J) :
    sourceEvent A s key key ↔ A.Nonempty := by
  constructor
  · rintro ⟨a, ha, _⟩
    exact ⟨a, ha⟩
  · rintro ⟨a, ha⟩
    exact ⟨a, ha, fun _ _ => rfl⟩

theorem sourceEvent_data_congr (A : Family) (s s' : J → Observation Alpha)
    (key cell : J) (hKey : s key = s' key) (hCell : s cell = s' cell) :
    sourceEvent A s key cell ↔ sourceEvent A s' key cell := by
  constructor
  · rintro ⟨a, ha, hEq⟩
    refine ⟨a, ha, ?_⟩
    intro i hi
    have hk : s key i = s' key i :=
      congrArg (fun observation : Observation Alpha => observation i) hKey
    have hc : s cell i = s' cell i :=
      congrArg (fun observation : Observation Alpha => observation i) hCell
    exact hc.symm.trans ((hEq i hi).trans hk)
  · rintro ⟨a, ha, hEq⟩
    refine ⟨a, ha, ?_⟩
    intro i hi
    have hk : s key i = s' key i :=
      congrArg (fun observation : Observation Alpha => observation i) hKey
    have hc : s cell i = s' cell i :=
      congrArg (fun observation : Observation Alpha => observation i) hCell
    exact hc.trans ((hEq i hi).trans hk.symm)

section DecidableEvents
variable [∀ i : Source, DecidableEq (Alpha i)]

def eqPattern (s : J → Observation Alpha) (key cell : J) : Source → Bool :=
  fun i => decide (s cell i = s key i)

instance sourceEventDecidable (A : Family) (s : J → Observation Alpha)
    (key cell : J) : Decidable (sourceEvent A s key cell) :=
  inferInstanceAs (Decidable (∃ a ∈ A, ∀ i ∈ a, s cell i = s key i))

theorem dnf_eq_sourceEvent (A : Family) (s : J → Observation Alpha)
    (key cell : J) :
    PidFin3Contract.DNF A (eqPattern s key cell) ↔ sourceEvent A s key cell := by
  unfold PidFin3Contract.DNF eqPattern sourceEvent
  constructor
  · rintro ⟨a, ha, hEq⟩
    exact ⟨a, ha, fun i hi => of_decide_eq_true (hEq i hi)⟩
  · rintro ⟨a, ha, hEq⟩
    exact ⟨a, ha, fun i hi => decide_eq_true (hEq i hi)⟩

end DecidableEvents

-- Natural weights make every summand nonnegative. Finiteness is only in K.
def mass [DecidableEq J] (K : Finset J) (w : J → Nat) (E : J → Prop)
    [DecidablePred E] : Nat :=
  (K.filter E).sum w

def N [DecidableEq J] (K : Finset J) (w : J → Nat) : Nat :=
  K.sum w

section GenericMass
variable [DecidableEq J]

theorem mass_mono (K : Finset J) (w : J → Nat) (E F : J → Prop)
    [DecidablePred E] [DecidablePred F] (hEF : ∀ cell ∈ K, E cell → F cell) :
    mass K w E ≤ mass K w F := by
  unfold mass
  apply Finset.sum_le_sum_of_subset
  intro cell hCell
  rcases Finset.mem_filter.mp hCell with ⟨hK, hE⟩
  exact Finset.mem_filter.mpr ⟨hK, hEF cell hK hE⟩

theorem mass_le_total (K : Finset J) (w : J → Nat) (E : J → Prop)
    [DecidablePred E] : mass K w E ≤ N K w := by
  unfold mass N
  apply Finset.sum_le_sum_of_subset
  intro cell hCell
  exact (Finset.mem_filter.mp hCell).1

theorem key_weight_le_mass (K : Finset J) (w : J → Nat) (E : J → Prop)
    [DecidablePred E] (key : J) (hK : key ∈ K) (hE : E key) :
    w key ≤ mass K w E := by
  unfold mass
  exact Finset.single_le_sum (fun cell _ => Nat.zero_le (w cell))
    (Finset.mem_filter.mpr ⟨hK, hE⟩)

theorem mass_congr (K : Finset J) (w w' : J → Nat) (E F : J → Prop)
    [DecidablePred E] [DecidablePred F]
    (hWeights : ∀ cell ∈ K, w cell = w' cell)
    (hEvents : ∀ cell ∈ K, E cell ↔ F cell) :
    mass K w E = mass K w' F := by
  have hFilter : K.filter E = K.filter F := by
    apply Finset.ext
    intro cell
    constructor
    · intro hCell
      rcases Finset.mem_filter.mp hCell with ⟨hK, hE⟩
      exact Finset.mem_filter.mpr ⟨hK, (hEvents cell hK).1 hE⟩
    · intro hCell
      rcases Finset.mem_filter.mp hCell with ⟨hK, hF⟩
      exact Finset.mem_filter.mpr ⟨hK, (hEvents cell hK).2 hF⟩
  unfold mass
  exact Finset.sum_congr hFilter
    (fun cell hCell => hWeights cell (Finset.mem_filter.mp hCell).1)

theorem total_congr (K : Finset J) (w w' : J → Nat)
    (hWeights : ∀ cell ∈ K, w cell = w' cell) : N K w = N K w' := by
  unfold N
  exact Finset.sum_congr rfl hWeights

end GenericMass

section Counts
variable [DecidableEq J] [∀ i : Source, DecidableEq (Alpha i)] [DecidableEq Beta]

def U (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (key : J) (A : Family) : Nat :=
  mass K w (sourceEvent A s key)

def V (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A : Family) : Nat :=
  mass K w (fun cell => sourceEvent A s key cell ∧ t cell = t key)

def T (K : Finset J) (w : J → Nat) (t : J → Beta) (key : J) : Nat :=
  mass K w (fun cell => t cell = t key)

omit [DecidableEq J] in
theorem supported_key_source_mem (K : Finset J) (s : J → Observation Alpha)
    (key : J) (A : Family) (hK : key ∈ K) (hA : A.Nonempty) :
    key ∈ K.filter (sourceEvent A s key) := by
  exact Finset.mem_filter.mpr ⟨hK, (sourceEvent_key_iff A s key).2 hA⟩

omit [DecidableEq J] in
theorem supported_key_joint_mem (K : Finset J) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A : Family)
    (hK : key ∈ K) (hA : A.Nonempty) :
    key ∈ K.filter (fun cell => sourceEvent A s key cell ∧ t cell = t key) := by
  exact Finset.mem_filter.mpr ⟨hK, (sourceEvent_key_iff A s key).2 hA, rfl⟩

omit [DecidableEq J] in
theorem supported_key_target_mem (K : Finset J) (t : J → Beta)
    (key : J) (hK : key ∈ K) :
    key ∈ K.filter (fun cell => t cell = t key) := by
  exact Finset.mem_filter.mpr ⟨hK, rfl⟩

theorem V_le_U (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A : Family) :
    V K w s t key A ≤ U K w s key A := by
  unfold V U
  apply mass_mono
  intro cell _ hCell
  exact hCell.1

theorem U_le_N (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (key : J) (A : Family) : U K w s key A ≤ N K w := by
  unfold U
  exact mass_le_total K w (sourceEvent A s key)

theorem V_le_T (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A : Family) :
    V K w s t key A ≤ T K w t key := by
  unfold V T
  apply mass_mono
  intro cell _ hCell
  exact hCell.2

theorem T_le_N (K : Finset J) (w : J → Nat) (t : J → Beta) (key : J) :
    T K w t key ≤ N K w := by
  unfold T
  exact mass_le_total K w (fun cell => t cell = t key)

theorem key_le_V (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A : Family)
    (hK : key ∈ K) (hA : A.Nonempty) : w key ≤ V K w s t key A := by
  unfold V
  exact key_weight_le_mass K w
    (fun cell => sourceEvent A s key cell ∧ t cell = t key) key hK
    ⟨(sourceEvent_key_iff A s key).2 hA, rfl⟩

theorem supported_key_bounds (K : Finset J) (w : J → Nat)
    (s : J → Observation Alpha) (t : J → Beta) (key : J) (A : Family)
    (hK : key ∈ K) (hA : A.Nonempty) (hPositive : 0 < w key) :
    w key ≤ V K w s t key A ∧
    V K w s t key A ≤ U K w s key A ∧ U K w s key A ≤ N K w ∧
    V K w s t key A ≤ T K w t key ∧ T K w t key ≤ N K w ∧
    0 < V K w s t key A := by
  have hLower := key_le_V K w s t key A hK hA
  refine ⟨hLower, V_le_U K w s t key A, U_le_N K w s key A,
    V_le_T K w s t key A, T_le_N K w t key, ?_⟩
  calc
    0 < w key := hPositive
    _ ≤ V K w s t key A := hLower

theorem counts_positive (K : Finset J) (w : J → Nat)
    (s : J → Observation Alpha) (t : J → Beta) (key : J) (A : Family)
    (hK : key ∈ K) (hA : A.Nonempty) (hPositive : 0 < w key) :
    0 < V K w s t key A ∧ 0 < U K w s key A ∧
    0 < T K w t key ∧ 0 < N K w := by
  have hV : 0 < V K w s t key A := by
    calc
      0 < w key := hPositive
      _ ≤ V K w s t key A := key_le_V K w s t key A hK hA
  refine ⟨hV, ?_, ?_, ?_⟩
  · calc
      0 < V K w s t key A := hV
      _ ≤ U K w s key A := V_le_U K w s t key A
  · calc
      0 < V K w s t key A := hV
      _ ≤ T K w t key := V_le_T K w s t key A
  · calc
      0 < V K w s t key A := hV
      _ ≤ T K w t key := V_le_T K w s t key A
      _ ≤ N K w := T_le_N K w t key

theorem U_antitone (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (key : J) (A B : Family) (hAB : PidFin3Contract.LE A B) :
    U K w s key B ≤ U K w s key A := by
  unfold U
  apply mass_mono
  intro cell _ hB
  exact sourceEvent_antitone A B hAB s key cell hB

theorem V_antitone (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A B : Family) (hAB : PidFin3Contract.LE A B) :
    V K w s t key B ≤ V K w s t key A := by
  unfold V
  apply mass_mono
  intro cell _ hB
  exact ⟨sourceEvent_antitone A B hAB s key cell hB.1, hB.2⟩

theorem counts_congr_on_support (K : Finset J) (w w' : J → Nat)
    (s s' : J → Observation Alpha) (t t' : J → Beta) (key : J) (A : Family)
    (hK : key ∈ K) (hWeights : ∀ cell ∈ K, w cell = w' cell)
    (hSources : ∀ cell ∈ K, s cell = s' cell)
    (hTargets : ∀ cell ∈ K, t cell = t' cell) :
    U K w s key A = U K w' s' key A ∧
    V K w s t key A = V K w' s' t' key A ∧
    T K w t key = T K w' t' key ∧ N K w = N K w' := by
  have hSource : ∀ cell ∈ K,
      sourceEvent A s key cell ↔ sourceEvent A s' key cell := by
    intro cell hCell
    exact sourceEvent_data_congr A s s' key cell
      (hSources key hK) (hSources cell hCell)
  have hTarget : ∀ cell ∈ K, (t cell = t key) ↔ (t' cell = t' key) := by
    intro cell hCell
    constructor
    · intro hEq
      exact (hTargets cell hCell).symm.trans (hEq.trans (hTargets key hK))
    · intro hEq
      exact (hTargets cell hCell).trans (hEq.trans (hTargets key hK).symm)
  refine ⟨?_, ?_, ?_, total_congr K w w' hWeights⟩
  · unfold U
    exact mass_congr K w w' (sourceEvent A s key) (sourceEvent A s' key)
      hWeights hSource
  · unfold V
    apply mass_congr K w w'
      (fun cell => sourceEvent A s key cell ∧ t cell = t key)
      (fun cell => sourceEvent A s' key cell ∧ t' cell = t' key) hWeights
    intro cell hCell
    constructor
    · intro hEvent
      exact ⟨(hSource cell hCell).1 hEvent.1, (hTarget cell hCell).1 hEvent.2⟩
    · intro hEvent
      exact ⟨(hSource cell hCell).2 hEvent.1, (hTarget cell hCell).2 hEvent.2⟩
  · unfold T
    exact mass_congr K w w' (fun cell => t cell = t key)
      (fun cell => t' cell = t' key) hWeights hTarget

end Counts
end PidFin3AlphabetCounts
