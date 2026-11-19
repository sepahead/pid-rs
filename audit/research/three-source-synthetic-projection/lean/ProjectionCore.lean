import W02Semantics

namespace ArchivedProjection
open SmtW02

/-- An evaluation which successfully returns the values of both assertions and refutes their conjunction. -/
def RefutesTwo (result : Option (List Bool)) : Prop :=
  ∃ p q : Bool, result = some [p,q] ∧ (p = false ∨ q = false)

instance (result : Option (List Bool)) : Decidable (RefutesTwo result) := by
  unfold RefutesTwo
  infer_instance

/-- Replace one dependent typed assignment, without converting any other sort or value. -/
def put (s : List Cmd) (idx : Fin (declarations s).length)
    (v : ((declarations s).get idx).2.carrier) (ρ : Valuation s) : Valuation s :=
  fun i => if same : idx = i then same ▸ v else ρ i

@[simp] theorem put_here (s : List Cmd) (i : Fin (declarations s).length) (v) (ρ : Valuation s) :
    put s i v ρ i = v := by simp [put]

theorem put_elsewhere (s : List Cmd) (i j : Fin (declarations s).length) (v) (ρ : Valuation s)
    (hne : i ≠ j) : put s i v ρ j = ρ j := by simp [put,hne]

/-- Proof-producing interface. Completeness is certified against the unmodified evaluator
for every full valuation, including integers and same-width variables that were omitted. -/
structure Projection (s : List Cmd) (A : Type) where
  project : Valuation s → A
  extend : A → Valuation s
  rightInverse : ∀ a, project (extend a) = a
  preserves : ∀ ρ, evaluate s ρ = evaluate s (extend (project ρ))

/-- A source-bound compositional expression may replace the archived evaluator only with this equality. -/
structure Reification (s : List Cmd) (A : Type) (p : Projection s A) where
  observe : A → Option (List Bool)
  agrees : ∀ a, evaluate s (p.extend a) = observe a

theorem fullEvaluation {s : List Cmd} {A : Type} (p : Projection s A) (r : Reification s A p)
    (ρ : Valuation s) : evaluate s ρ = r.observe (p.project ρ) :=
  (p.preserves ρ).trans (r.agrees (p.project ρ))

theorem refutesAll {s : List Cmd} {A : Type} (p : Projection s A) (r : Reification s A p)
    (h : ∀ a, RefutesTwo (r.observe a)) : ∀ ρ : Valuation s, RefutesTwo (evaluate s ρ) := by
  intro ρ
  rw [fullEvaluation p r ρ]
  exact h (p.project ρ)

theorem noModelOfSuccessfulRefutation (s : List Cmd)
    (h : ∀ ρ : Valuation s, RefutesTwo (evaluate s ρ)) : ¬ ∃ ρ : Valuation s, Satisfies s ρ := by
  rintro ⟨ρ, hs⟩
  obtain ⟨p,q,he,hbad⟩ := h ρ
  unfold Satisfies at hs
  rw [he] at hs
  rcases hbad with h | h <;> cases h <;> cases hs

/-- Enumerate all bounded natural indices for a certified expression; no external Boolean is assumed. -/
theorem enumerateOne {n : Nat} {test : Nat → Bool}
    (cert : (List.range n).all test = true) (i : Fin n) : test i.val = true :=
  (List.all_eq_true.mp cert) i.val (List.mem_range.mpr i.isLt)

theorem enumeratePair {n m : Nat} {test : Nat → Nat → Bool}
    (cert : (List.range n).all (fun x => (List.range m).all (test x)) = true)
    (i : Fin n) (j : Fin m) : test i.val j.val = true :=
  enumerateOne (enumerateOne cert i) j

end ArchivedProjection
