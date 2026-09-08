import PidPrefixMgwMean.Contract
import PidMgwBridge.Candidate
import PidPrefixProbability.Candidate

/- Source-only successor proposal. No compiler or kernel has checked these revised bodies.
   This file supplies only private helpers and the first frozen target body.
   It is not a complete three-target candidate and is not acceptance evidence. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators
open PidMgwBridgeContract
open PidPrefixProbabilityContract
open PidPrefixMgwMeanContract
universe u v w
namespace PidPrefixMgwMeanCandidate

private lemma valid_generator {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (z x : Key I X T)
    (h : (mismatches z x).Nonempty) : Valid (singles (mismatches z x)) :=
  (PidMgwBridgeCandidate.mismatch_generator_and_exclusion.{u,v,w}.1 I (mismatches z x)) h

private lemma fold_valid_and_lub {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (z : Key I X T) (rows : List (Key I X T))
    (a : Node I) (hm : ∀ x ∈ rows, (mismatches z x).Nonempty) :
    Valid (rows.foldl (fun family row => rawJoin family (singles (mismatches z row))) a.val) ∧
      ∀ b : Node I,
        rawLE (rows.foldl (fun family row => rawJoin family (singles (mismatches z row))) a.val)
          b.val ↔
          rawLE a.val b.val ∧ ∀ x ∈ rows, rawLE (singles (mismatches z x)) b.val := by
  classical
  revert a hm
  induction rows with
  | nil =>
      intro a hm
      refine ⟨a.property, ?_⟩
      intro b
      simp
  | cons x xs ih =>
      intro a hm
      let g : Node I := ⟨singles (mismatches z x), valid_generator z x (hm x (by simp))⟩
      have hj := (PidMgwBridgeCandidate.actual_join_lub I).1 a g
      let j : Node I := ⟨rawJoin a.val g.val, hj.1⟩
      have ht := ih j (fun y hy => hm y (List.mem_cons_of_mem x hy))
      refine ⟨ht.1, ?_⟩
      intro b
      change rawLE (xs.foldl (fun family row => rawJoin family (singles (mismatches z row)))
        j.val) b.val ↔ _
      rw [ht.2 b]
      change (rawLE (rawJoin a.val g.val) b.val ∧
        ∀ y ∈ xs, rawLE (singles (mismatches z y)) b.val) ↔ _
      rw [hj.2 b]
      simp only [List.forall_mem_cons]
      change ((rawLE a.val b.val ∧ rawLE (singles (mismatches z x)) b.val) ∧
        ∀ y ∈ xs, rawLE (singles (mismatches z y)) b.val) ↔ _
      tauto

private lemma prefix_valid_and_lub {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (z : Key I X T) (rows : List (Key I X T))
    (hne : rows ≠ []) (hm : ∀ x ∈ rows, (mismatches z x).Nonempty) :
    Valid (rawPrefixFamily z rows) ∧
      ∀ b : Node I, rawLE (rawPrefixFamily z rows) b.val ↔
        ∀ x ∈ rows, rawLE (singles (mismatches z x)) b.val := by
  classical
  cases rows with
  | nil => exact False.elim (hne rfl)
  | cons x xs =>
      let g : Node I := ⟨singles (mismatches z x), valid_generator z x (hm x (by simp))⟩
      have ht := fold_valid_and_lub z xs g (fun y hy => hm y (List.mem_cons_of_mem x hy))
      refine ⟨ht.1, ?_⟩
      intro b
      change rawLE (xs.foldl (fun family row => rawJoin family (singles (mismatches z row)))
        g.val) b.val ↔ _
      simpa only [List.forall_mem_cons] using ht.2 b

private lemma prefix_cumulative_indicator {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (z : Key I X T) (rows : List (Key I X T))
    (hne : rows ≠ []) (b : Node I) : (by
      classical
      let := nodeFintype I
      exact (∑ a : Node I, if rawLE a.val b.val then
        (if prefixEvent z a rows then (1 : ℝ) else 0) else 0) =
          if ∀ x ∈ rows, x ∉ PidFiniteConvergence.sxSourceEvent b.val z then 1 else 0) := by
  classical
  let := nodeFintype I
  by_cases hm : ∀ x ∈ rows, (mismatches z x).Nonempty
  · have hf := prefix_valid_and_lub z rows hne hm
    let a0 : Node I := ⟨rawPrefixFamily z rows, hf.1⟩
    have he (a : Node I) : prefixEvent z a rows ↔ a = a0 := by
      constructor
      · intro h
        exact Subtype.ext h.2.2.symm
      · intro h
        subst a
        exact ⟨hne, hm, rfl⟩
    have hc : (∀ x ∈ rows, x ∉ PidFiniteConvergence.sxSourceEvent b.val z) ↔
        rawLE a0.val b.val := by
      constructor
      · intro hall
        apply (hf.2 b).mpr
        intro x hx
        exact ((PidMgwBridgeCandidate.mismatch_generator_and_exclusion.2 I X T z x b).mp
          (hall x hx)).2
      · intro h x hx
        apply (PidMgwBridgeCandidate.mismatch_generator_and_exclusion.2 I X T z x b).mpr
        exact ⟨hm x hx, (hf.2 b).mp h x hx⟩
    rw [Finset.sum_eq_single a0]
    · simp [he, hc]
    · intro a _ha hne_a
      simp [he, hne_a]
    · simp
  · have he (a : Node I) : ¬prefixEvent z a rows := fun h => hm h.2.1
    have hc : ¬(∀ x ∈ rows, x ∉ PidFiniteConvergence.sxSourceEvent b.val z) := by
      intro h
      apply hm
      intro x hx
      exact ((PidMgwBridgeCandidate.mismatch_generator_and_exclusion.2 I X T z x b).mp
        (h x hx)).1
    simp [he, hc]

private lemma excluded_mass {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (r : Key I X T → ℝ) (z : Key I X T) (b : Node I) :
    (∑ x, if x ∉ PidFiniteConvergence.sxSourceEvent b.val z then r x else 0) =
      cumulative (weights r z) b := by
  classical
  rw [PidMgwBridgeCandidate.generator_lower_cumulative I X T r z b]
  have hs : sourceMass r z b =
      ∑ x, if x ∈ PidFiniteConvergence.sxSourceEvent b.val z then r x else 0 := by
    unfold sourceMass
    rw [← Finset.sum_filter]
    simp [PidFiniteConvergence.finiteEventMass]
  rw [hs]
  change _ = (∑ x, r x) - _
  rw [← Finset.sum_sub_distrib]
  apply Finset.sum_congr rfl
  intro x _hx
  by_cases hx : x ∈ PidFiniteConvergence.sxSourceEvent b.val z <;> simp [hx]

private lemma weighted_words_predicate {K : Type u} [Fintype K]
    (r : K → ℝ) (P : K → Prop) [DecidablePred P] (n : ℕ) :
    (∑ word : Fin n → K, (∏ i, r (word i)) *
      (if ∀ x ∈ List.ofFn word, P x then 1 else 0)) =
        (∑ x, if P x then r x else 0) ^ n := by
  classical
  rw [Fintype.sum_pow]
  apply Finset.sum_congr rfl
  intro word _hw
  simp only [List.forall_mem_ofFn_iff]
  by_cases hp : ∀ i, P (word i)
  · rw [if_pos hp, mul_one]
    apply Finset.prod_congr rfl
    intro i _hi
    rw [if_pos (hp i)]
  · rw [if_neg hp, mul_zero]
    obtain ⟨i, hi⟩ := not_forall.mp hp
    symm
    exact Finset.prod_eq_zero (Finset.mem_univ i) (if_neg hi)

private lemma weighted_lower_sum {A : Type u} {W : Type v}
    [Fintype A] [Fintype W]
    (R : A → Prop) [DecidablePred R] (f : W → ℝ) (g : A → W → ℝ) :
    (∑ a, if R a then ∑ word, f word * g a word else 0) =
      ∑ word, f word * ∑ a, if R a then g a word else 0 := by
  classical
  calc
    _ = ∑ a, ∑ word, if R a then f word * g a word else 0 := by
      apply Finset.sum_congr rfl
      intro a _ha
      by_cases ha : R a
      · simp only [if_pos ha]
      · simp only [if_neg ha, Finset.sum_const_zero]
    _ = ∑ word, ∑ a, if R a then f word * g a word else 0 :=
      Finset.sum_comm
    _ = _ := by
      apply Finset.sum_congr rfl
      intro word _hw
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro a _ha
      by_cases ha : R a
      · simp only [if_pos ha]
      · simp only [if_neg ha, mul_zero]

private lemma word_cumulative {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (r : Key I X T → ℝ) (z : Key I X T)
    (n : ℕ) (b : Node I) :
    cumulative (fun a => wordCoefficient r z a (n + 1)) b =
      cumulative (weights r z) b ^ (n + 1) := by
  classical
  let := nodeFintype I
  calc
    _ = ∑ word : Fin (n + 1) → Key I X T, (∏ i, r (word i)) *
        (∑ a : Node I, if rawLE a.val b.val then
          (if prefixEvent z a (List.ofFn word) then (1 : ℝ) else 0) else 0) := by
      exact weighted_lower_sum (fun a : Node I => rawLE a.val b.val)
        (fun word : Fin (n + 1) → Key I X T => ∏ i, r (word i))
        (fun a word => if prefixEvent z a (List.ofFn word) then 1 else 0)
    _ = ∑ word : Fin (n + 1) → Key I X T, (∏ i, r (word i)) *
        (if ∀ x ∈ List.ofFn word, x ∉ PidFiniteConvergence.sxSourceEvent b.val z
          then 1 else 0) := by
      apply Finset.sum_congr rfl
      intro word _hw
      have hne : List.ofFn word ≠ [] := by
        intro h
        have hl := congrArg List.length h
        simp at hl
      rw [prefix_cumulative_indicator z (List.ofFn word) hne b]
    _ = (∑ x, if x ∉ PidFiniteConvergence.sxSourceEvent b.val z then r x else 0) ^ (n + 1) :=
      weighted_words_predicate r (fun x => x ∉ PidFiniteConvergence.sxSourceEvent b.val z) (n + 1)
    _ = _ := by rw [excluded_mass r z b]

private lemma actual_cumulative_as_order {I : Type u} [Fintype I] [DecidableEq I]
    (sigma : SemilatticeSup (Node I)) (hsigma : ExactOps sigma)
    (r : Node I → ℝ) (a : Node I) :
    cumulative r a = @PidJoinLogContract.cumulative (Node I) (nodeFintype I)
      sigma.toLE (Classical.decRel sigma.le) r a := by
  classical
  unfold cumulative PidJoinLogContract.cumulative
  apply Finset.sum_congr rfl
  intro x _hx
  simp only [hsigma.1 x a]

private lemma signed_power_cumulative {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] (r : L → ℝ) (n : ℕ) (a : L) :
    PidJoinLogContract.cumulative (PidJoinLogContract.joinPower r n) a =
      PidJoinLogContract.cumulative r a ^ (n + 1) := by
  induction n with
  | zero => simp [PidJoinLogContract.joinPower]
  | succ n ih =>
      rw [PidJoinLogContract.joinPower, PidJoinLogCandidate.join_convolution_cumulative L, ih]
      simp only [pow_succ]

private lemma proposed_word_coefficient_join_power :
    word_coefficient_join_power_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ r z alpha n sigma hsigma
  classical
  let := nodeFintype I
  let : SemilatticeSup (Node I) := sigma
  have he := @PidJoinLogCandidate.lower_cumulative_unique (Node I) (nodeFintype I)
    sigma.toPartialOrder (Classical.decRel sigma.le)
    (fun a => wordCoefficient r z a (n + 1))
    (@PidJoinLogContract.joinPower (Node I) (nodeFintype I) sigma
      (Classical.decEq (Node I)) (weights r z) n)
  apply congrFun (he ?_) alpha
  intro b
  calc
    _ = cumulative (fun a => wordCoefficient r z a (n + 1)) b :=
      (actual_cumulative_as_order sigma hsigma
        (fun a => wordCoefficient r z a (n + 1)) b).symm
    _ = cumulative (weights r z) b ^ (n + 1) := word_cumulative r z n b
    _ = (@PidJoinLogContract.cumulative (Node I) (nodeFintype I)
        sigma.toLE (Classical.decRel sigma.le) (weights r z) b) ^ (n + 1) :=
      congrArg (fun q : ℝ => q ^ (n + 1))
        (actual_cumulative_as_order sigma hsigma (weights r z) b)
    _ = _ := (@signed_power_cumulative (Node I) (nodeFintype I) sigma
      (Classical.decEq (Node I)) (Classical.decRel sigma.le) (weights r z) n b).symm

end PidPrefixMgwMeanCandidate
