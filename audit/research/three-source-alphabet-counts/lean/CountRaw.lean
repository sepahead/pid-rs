import Contract
import Mathlib.Algebra.Order.BigOperators.Group.Finset

set_option autoImplicit false
set_option warningAsError true

-- SOURCE ONLY. Independent authority definitions; never import AlphabetCounts.
-- Shared Contract remains separately byte-bound; these imports are unqualified.
namespace PidFin3CountRaw
open PidFin3Contract
universe u v z

abbrev Observation (Alpha : Source → Type u) := (i : Source) → Alpha i

def sourceEvent {Alpha : Source → Type u} {J : Type z}
    (A : Family) (s : J → Observation Alpha) (key cell : J) : Prop :=
  ∃ branch : Branch, branch ∈ A ∧
    ∀ index : Source, index ∈ branch → s cell index = s key index

def eqPattern {Alpha : Source → Type u} {J : Type z}
    [∀ i : Source, DecidableEq (Alpha i)]
    (s : J → Observation Alpha) (key cell : J) : Source → Bool :=
  fun i => decide (s cell i = s key i)

instance sourceEventDecidable {Alpha : Source → Type u} {J : Type z}
    [∀ i : Source, DecidableEq (Alpha i)]
    (A : Family) (s : J → Observation Alpha) (key cell : J) :
    Decidable (sourceEvent A s key cell) :=
  inferInstanceAs (Decidable (∃ branch : Branch, branch ∈ A ∧
    ∀ index : Source, index ∈ branch → s cell index = s key index))

def mass {J : Type z} [DecidableEq J] (K : Finset J) (w : J → Nat)
    (E : J → Prop) [DecidablePred E] : Nat :=
  Finset.sum (Finset.filter E K) w

def N {J : Type z} [DecidableEq J] (K : Finset J) (w : J → Nat) : Nat :=
  Finset.sum K w

def U {Alpha : Source → Type u} {J : Type z}
    [DecidableEq J] [∀ i : Source, DecidableEq (Alpha i)]
    (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (key : J) (A : Family) : Nat :=
  mass K w (sourceEvent A s key)

def V {Alpha : Source → Type u} {Beta : Type v} {J : Type z}
    [DecidableEq J] [∀ i : Source, DecidableEq (Alpha i)] [DecidableEq Beta]
    (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A : Family) : Nat :=
  mass K w (fun cell => sourceEvent A s key cell ∧ t cell = t key)

def T {Beta : Type v} {J : Type z} [DecidableEq J] [DecidableEq Beta]
    (K : Finset J) (w : J → Nat) (t : J → Beta) (key : J) : Nat :=
  mass K w (fun cell => t cell = t key)

-- Raw declarations have type Prop. All data/instances are quantified in values.
-- Underscore names suppress unused-binder warnings, not logical hypotheses.
def sourceEvent_antitone : Prop :=
  ∀ {Alpha : Source → Type u} {J : Type z}
    (A B : Family) (_hAB : PidFin3Contract.LE A B)
    (s : J → Observation Alpha) (key cell : J),
    sourceEvent B s key cell → sourceEvent A s key cell

def sourceEvent_key_iff : Prop :=
  ∀ {Alpha : Source → Type u} {J : Type z}
    (A : Family) (s : J → Observation Alpha) (key : J),
    sourceEvent A s key key ↔ A.Nonempty

def sourceEvent_data_congr : Prop :=
  ∀ {Alpha : Source → Type u} {J : Type z}
    (A : Family) (s s' : J → Observation Alpha) (key cell : J)
    (_hKey : s key = s' key) (_hCell : s cell = s' cell),
    sourceEvent A s key cell ↔ sourceEvent A s' key cell

def dnf_eq_sourceEvent : Prop :=
  ∀ {Alpha : Source → Type u} {J : Type z}
    [∀ i : Source, DecidableEq (Alpha i)]
    (A : Family) (s : J → Observation Alpha) (key cell : J),
    PidFin3Contract.DNF A (eqPattern s key cell) ↔ sourceEvent A s key cell

def mass_mono : Prop :=
  ∀ {J : Type z} [DecidableEq J]
    (K : Finset J) (w : J → Nat) (E F : J → Prop)
    [DecidablePred E] [DecidablePred F]
    (_hEF : ∀ cell ∈ K, E cell → F cell),
    mass K w E ≤ mass K w F

def mass_le_total : Prop :=
  ∀ {J : Type z} [DecidableEq J]
    (K : Finset J) (w : J → Nat) (E : J → Prop) [DecidablePred E],
    mass K w E ≤ N K w

def key_weight_le_mass : Prop :=
  ∀ {J : Type z} [DecidableEq J]
    (K : Finset J) (w : J → Nat) (E : J → Prop) [DecidablePred E]
    (key : J) (_hK : key ∈ K) (_hE : E key),
    w key ≤ mass K w E

def mass_congr : Prop :=
  ∀ {J : Type z} [DecidableEq J]
    (K : Finset J) (w w' : J → Nat) (E F : J → Prop)
    [DecidablePred E] [DecidablePred F]
    (_hWeights : ∀ cell ∈ K, w cell = w' cell)
    (_hEvents : ∀ cell ∈ K, E cell ↔ F cell),
    mass K w E = mass K w' F

def total_congr : Prop :=
  ∀ {J : Type z} [DecidableEq J] (K : Finset J) (w w' : J → Nat)
    (_hWeights : ∀ cell ∈ K, w cell = w' cell),
    N K w = N K w'

-- Finset.filter/membership require no DecidableEq J; do not add that premise.
def supported_key_source_mem : Prop :=
  ∀ {Alpha : Source → Type u} {J : Type z}
    [∀ i : Source, DecidableEq (Alpha i)]
    (K : Finset J) (s : J → Observation Alpha) (key : J) (A : Family)
    (_hK : key ∈ K) (_hA : A.Nonempty),
    key ∈ K.filter (sourceEvent A s key)

def supported_key_joint_mem : Prop :=
  ∀ {Alpha : Source → Type u} {Beta : Type v} {J : Type z}
    [∀ i : Source, DecidableEq (Alpha i)] [DecidableEq Beta]
    (K : Finset J) (s : J → Observation Alpha) (t : J → Beta)
    (key : J) (A : Family) (_hK : key ∈ K) (_hA : A.Nonempty),
    key ∈ K.filter (fun cell => sourceEvent A s key cell ∧ t cell = t key)

def supported_key_target_mem : Prop :=
  ∀ {Beta : Type v} {J : Type z} [DecidableEq Beta]
    (K : Finset J) (t : J → Beta) (key : J) (_hK : key ∈ K),
    key ∈ K.filter (fun cell => t cell = t key)

def V_le_U : Prop :=
  ∀ {Alpha : Source → Type u} {Beta : Type v} {J : Type z}
    [DecidableEq J] [∀ i : Source, DecidableEq (Alpha i)] [DecidableEq Beta]
    (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A : Family),
    V K w s t key A ≤ U K w s key A

def U_le_N : Prop :=
  ∀ {Alpha : Source → Type u} {J : Type z}
    [DecidableEq J] [∀ i : Source, DecidableEq (Alpha i)]
    (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (key : J) (A : Family),
    U K w s key A ≤ N K w

def V_le_T : Prop :=
  ∀ {Alpha : Source → Type u} {Beta : Type v} {J : Type z}
    [DecidableEq J] [∀ i : Source, DecidableEq (Alpha i)] [DecidableEq Beta]
    (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A : Family),
    V K w s t key A ≤ T K w t key

def T_le_N : Prop :=
  ∀ {Beta : Type v} {J : Type z} [DecidableEq J] [DecidableEq Beta]
    (K : Finset J) (w : J → Nat) (t : J → Beta) (key : J),
    T K w t key ≤ N K w

def key_le_V : Prop :=
  ∀ {Alpha : Source → Type u} {Beta : Type v} {J : Type z}
    [DecidableEq J] [∀ i : Source, DecidableEq (Alpha i)] [DecidableEq Beta]
    (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A : Family)
    (_hK : key ∈ K) (_hA : A.Nonempty),
    w key ≤ V K w s t key A

def supported_key_bounds : Prop :=
  ∀ {Alpha : Source → Type u} {Beta : Type v} {J : Type z}
    [DecidableEq J] [∀ i : Source, DecidableEq (Alpha i)] [DecidableEq Beta]
    (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A : Family)
    (_hK : key ∈ K) (_hA : A.Nonempty) (_hPositive : 0 < w key),
    w key ≤ V K w s t key A ∧
    V K w s t key A ≤ U K w s key A ∧ U K w s key A ≤ N K w ∧
    V K w s t key A ≤ T K w t key ∧ T K w t key ≤ N K w ∧
    0 < V K w s t key A

def counts_positive : Prop :=
  ∀ {Alpha : Source → Type u} {Beta : Type v} {J : Type z}
    [DecidableEq J] [∀ i : Source, DecidableEq (Alpha i)] [DecidableEq Beta]
    (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A : Family)
    (_hK : key ∈ K) (_hA : A.Nonempty) (_hPositive : 0 < w key),
    0 < V K w s t key A ∧ 0 < U K w s key A ∧
    0 < T K w t key ∧ 0 < N K w

def U_antitone : Prop :=
  ∀ {Alpha : Source → Type u} {J : Type z}
    [DecidableEq J] [∀ i : Source, DecidableEq (Alpha i)]
    (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (key : J) (A B : Family) (_hAB : PidFin3Contract.LE A B),
    U K w s key B ≤ U K w s key A

def V_antitone : Prop :=
  ∀ {Alpha : Source → Type u} {Beta : Type v} {J : Type z}
    [DecidableEq J] [∀ i : Source, DecidableEq (Alpha i)] [DecidableEq Beta]
    (K : Finset J) (w : J → Nat) (s : J → Observation Alpha)
    (t : J → Beta) (key : J) (A B : Family) (_hAB : PidFin3Contract.LE A B),
    V K w s t key B ≤ V K w s t key A

def counts_congr_on_support : Prop :=
  ∀ {Alpha : Source → Type u} {Beta : Type v} {J : Type z}
    [DecidableEq J] [∀ i : Source, DecidableEq (Alpha i)] [DecidableEq Beta]
    (K : Finset J) (w w' : J → Nat)
    (s s' : J → Observation Alpha) (t t' : J → Beta)
    (key : J) (A : Family) (_hK : key ∈ K)
    (_hWeights : ∀ cell ∈ K, w cell = w' cell)
    (_hSources : ∀ cell ∈ K, s cell = s' cell)
    (_hTargets : ∀ cell ∈ K, t cell = t' cell),
    U K w s key A = U K w' s' key A ∧
    V K w s t key A = V K w' s' t' key A ∧
    T K w t key = T K w' t' key ∧ N K w = N K w'

end PidFin3CountRaw
