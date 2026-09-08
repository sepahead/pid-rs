/- Statement-preserving formatting control. -/

import PidPrefixMgwMean.Contract
import PidMgwBridge.Candidate
import PidPrefixProbability.Candidate

/-! Finite-categorical MGW prefix expectation candidate. The exact three proof targets
are checked separately by the frozen semantic judge and fresh kernel. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal Topology
open MeasureTheory
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
      exact cumulative (fun a : Node I => if prefixEvent z a rows then (1 : ℝ) else 0) b =
        if ∀ x ∈ rows, x ∉ PidFiniteConvergence.sxSourceEvent b.val z then 1 else 0) := by
  classical
  let := nodeFintype I
  change (∑ a : Node I, if rawLE a.val b.val then
    (if prefixEvent z a rows then (1 : ℝ) else 0) else 0) =
      if ∀ x ∈ rows, x ∉ PidFiniteConvergence.sxSourceEvent b.val z then 1 else 0
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
    · by_cases hle : rawLE a0.val b.val
      · rw [if_pos hle, if_pos ((he a0).mpr rfl), if_pos (hc.mpr hle)]
      · rw [if_neg hle, if_neg (fun h => hle (hc.mp h))]
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
    simp only [he, if_false, ite_self, Finset.sum_const_zero, if_neg hc]

private lemma weighted_prefix_cumulative_indicator {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (z : Key I X T) (rows : List (Key I X T)) (hne : rows ≠ [])
    (b : Node I) (c : ℝ) : (by
      classical
      exact c * cumulative (fun a : Node I =>
          if prefixEvent z a rows then (1 : ℝ) else 0) b =
        c * (if ∀ x ∈ rows, x ∉ PidFiniteConvergence.sxSourceEvent b.val z
          then 1 else 0)) := by
  classical
  exact congrArg (fun t : ℝ => c * t)
    (prefix_cumulative_indicator (I := I) (X := X) (T := T) z rows hne b)

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

private lemma weighted_indicator_sum_decision_irrel {W : Type u} [Fintype W]
    (f : W → ℝ) (P : W → Prop)
    (d1 d2 : (x : W) → Decidable (P x)) :
    (∑ x, f x * @ite ℝ (P x) (d1 x) 1 0) =
      ∑ x, f x * @ite ℝ (P x) (d2 x) 1 0 := by
  apply Finset.sum_congr rfl
  intro x _hx
  exact congrArg
    (fun d : Decidable (P x) => f x * @ite ℝ (P x) d 1 0)
    (Subsingleton.elim (d1 x) (d2 x))

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

private lemma word_cumulative_as_sum {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (r : Key I X T → ℝ) (z : Key I X T) (n : ℕ) (b : Node I) : (by
      classical
      exact cumulative (fun a => wordCoefficient r z a (n + 1)) b =
        ∑ word : Fin (n + 1) → Key I X T, (∏ i, r (word i)) *
          cumulative (fun a => if prefixEvent z a (List.ofFn word) then (1 : ℝ) else 0) b) := by
  classical
  let := nodeFintype I
  exact weighted_lower_sum (fun a : Node I => rawLE a.val b.val)
    (fun word : Fin (n + 1) → Key I X T => ∏ i, r (word i))
    (fun a word => if prefixEvent z a (List.ofFn word) then 1 else 0)

private lemma word_indicator_sum {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (r : Key I X T → ℝ) (z : Key I X T) (n : ℕ) (b : Node I) : (by
      classical
      exact (∑ word : Fin (n + 1) → Key I X T, (∏ i, r (word i)) *
          cumulative (fun a => if prefixEvent z a (List.ofFn word) then (1 : ℝ) else 0) b) =
        ∑ word : Fin (n + 1) → Key I X T, (∏ i, r (word i)) *
          (if ∀ x ∈ List.ofFn word, x ∉ PidFiniteConvergence.sxSourceEvent b.val z
            then 1 else 0)) := by
  classical
  apply Finset.sum_congr rfl
  intro word _hw
  have hne : List.ofFn word ≠ [] := by
    intro h
    have hl := congrArg List.length h
    simp at hl
  exact weighted_prefix_cumulative_indicator (I := I) (X := X) (T := T)
    z (List.ofFn word) hne b (∏ i, r (word i))

private lemma word_cumulative {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (r : Key I X T → ℝ) (z : Key I X T)
    (n : ℕ) (b : Node I) :
    cumulative (fun a => wordCoefficient r z a (n + 1)) b =
      cumulative (weights r z) b ^ (n + 1) := by
  classical
  have hs := word_cumulative_as_sum r z n b
  have hi := word_indicator_sum r z n b
  have hp := weighted_words_predicate r
    (fun x => x ∉ PidFiniteConvergence.sxSourceEvent b.val z) (n + 1)
  have hm := congrArg (fun t : ℝ => t ^ (n + 1)) (excluded_mass r z b)
  apply hs.trans
  apply hi.trans
  refine Eq.trans ?_ (hp.trans hm)
  exact weighted_indicator_sum_decision_irrel
    (fun word : Fin (n + 1) → Key I X T => ∏ i, r (word i))
    (fun word => ∀ x ∈ List.ofFn word,
      x ∉ PidFiniteConvergence.sxSourceEvent b.val z) _ _

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


private lemma mean_finite_word_integral {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (count : ℕ)
    (f : (Fin count → Key I X T) → ℝ) (hp : Law p) : (by
      let : MeasurableSpace (Key I X T) := ⊤
      exact Integrable f (rowLaw p count) ∧
        (∫ word, f word ∂rowLaw p count) =
          ∑ word, (∏ i, p (word i)) * f word) := by
  exact (PidPrefixProbabilityCandidate.finite_product_law I X T p count hp).2.2 f

private lemma mean_positive_prefix_integral {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (n : ℕ)
    (hp : Law p) : (by
      let : MeasurableSpace (Key I X T) := ⊤
      exact Integrable (fun rows => positiveOnPrefix z alpha (List.ofFn rows))
          (rowLaw p (n + 1)) ∧
        (∫ rows, positiveOnPrefix z alpha (List.ofFn rows) ∂rowLaw p (n + 1)) =
          wordCoefficient p z alpha (n + 1) / ((n : ℝ) + 1)) := by
  exact ⟨(mean_finite_word_integral p (n + 1)
    (fun rows => positiveOnPrefix z alpha (List.ofFn rows)) hp).1,
    PidPrefixProbabilityCandidate.positive_increment_expectation I X T p z alpha n hp⟩

private lemma mean_weighted_word_snoc {K : Type u} [Fintype K] (p : K → ℝ)
    (F : List K → ℝ) (n : ℕ) :
    (∑ word : Fin (n + 1) → K, (∏ i, p (word i)) * F (List.ofFn word)) =
      ∑ x, p x * ∑ word : Fin n → K,
        (∏ i, p (word i)) * F (List.ofFn word ++ [x]) := by
  classical
  rw [← (Fin.snocEquiv (fun _ : Fin (n + 1) => K)).sum_comp]
  rw [Fintype.sum_prod_type]
  simp only [Fin.snocEquiv_apply]
  simp_rw [List.ofFn_succ_last, Fin.prod_univ_castSucc]
  simp only [Fin.snocEquiv_apply, Fin.snoc_castSucc, Fin.snoc_last]
  simp only [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro x _hx
  apply Finset.sum_congr rfl
  intro word _hw
  ring

private lemma mean_weighted_prefix_add {K : Type u} [Fintype K]
    (p : K → ℝ) (hp : (∑ x, p x) = 1) (F : List K → ℝ) (m k : ℕ) :
    (∑ word : Fin (m + k) → K,
      (∏ i, p (word i)) * F ((List.ofFn word).take m)) =
      ∑ word : Fin m → K, (∏ i, p (word i)) * F (List.ofFn word) := by
  classical
  induction k with
  | zero =>
      simp only [Nat.add_zero]
      apply Finset.sum_congr rfl
      intro word _hw
      rw [List.take_of_length_le (by simp)]
  | succ k ih =>
      change (∑ word : Fin ((m + k) + 1) → K,
        (∏ i, p (word i)) * F ((List.ofFn word).take m)) = _
      rw [mean_weighted_word_snoc p (fun rows => F (rows.take m)) (m + k)]
      have ht (word : Fin (m + k) → K) (x : K) :
          (List.ofFn word ++ [x]).take m = (List.ofFn word).take m :=
        List.take_append_of_le_length (by simp)
      simp_rw [ht]
      rw [← Finset.sum_mul, hp, one_mul]
      exact ih

private lemma mean_weighted_prefix {K : Type u} [Fintype K]
    (p : K → ℝ) (hp : (∑ x, p x) = 1) (F : List K → ℝ)
    (m h : ℕ) (hmh : m ≤ h) :
    (∑ word : Fin h → K,
      (∏ i, p (word i)) * F ((List.ofFn word).take m)) =
      ∑ word : Fin m → K, (∏ i, p (word i)) * F (List.ofFn word) := by
  obtain ⟨k, rfl⟩ := Nat.exists_eq_add_of_le hmh
  exact mean_weighted_prefix_add p hp F m k

private lemma mean_weighted_anchor_split {K : Type u} [Fintype K]
    (p : K → ℝ) (F : K → List K → ℝ) (h : ℕ) :
    (∑ block : Fin (h + 1) → K, (∏ i, p (block i)) *
      F (block 0) (List.ofFn (fun i : Fin h => block i.succ))) =
      ∑ z, p z * ∑ word : Fin h → K, (∏ i, p (word i)) * F z (List.ofFn word) := by
  classical
  rw [← (Fin.consEquiv (fun _ : Fin (h + 1) => K)).sum_comp]
  rw [Fintype.sum_prod_type]
  simp only [Fin.consEquiv_apply, Fin.cons_zero, Fin.cons_succ,
    Fin.prod_univ_succ, Finset.mul_sum, mul_assoc]

private lemma mean_weighted_prefix_sum {K : Type u} [Fintype K]
    (p : K → ℝ) (hp : (∑ x, p x) = 1) (F : ℕ → List K → ℝ) (h : ℕ) :
    (∑ word : Fin h → K, (∏ i, p (word i)) *
      ∑ j : Fin h, F j.val ((List.ofFn word).take (j.val + 1))) =
      ∑ j : Fin h, ∑ word : Fin (j.val + 1) → K,
        (∏ i, p (word i)) * F j.val (List.ofFn word) := by
  classical
  simp_rw [Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _hj
  exact mean_weighted_prefix p hp (F j.val) (j.val + 1) h
    (Nat.succ_le_of_lt j.isLt)

private lemma proposed_finite_block_expectation :
    finite_block_expectation_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p alpha h hp
  classical
  let : MeasurableSpace (Key I X T) := ⊤
  have htotal : (∑ z, p z) = 1 := hp.2
  have hblock :
      (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1)) =
        ∑ z, p z * ∑ n ∈ Finset.range h,
          ((∫ rows, positiveOnPrefix z alpha (List.ofFn rows) ∂rowLaw p (n + 1)) -
            (∫ rows, negativeOnPrefix z alpha (List.ofFn rows) ∂rowLaw p (n + 1))) := by
    rw [(mean_finite_word_integral p (h + 1) (blockStatistic alpha h) hp).2]
    change (∑ block : Fin (h + 1) → Key I X T, (∏ i, p (block i)) *
      ∑ j : Fin h,
        (positiveOnPrefix (block 0) alpha
          ((List.ofFn (fun i : Fin h => block i.succ)).take (j.val + 1)) -
        negativeOnPrefix (block 0) alpha
          ((List.ofFn (fun i : Fin h => block i.succ)).take (j.val + 1)))) = _
    rw [mean_weighted_anchor_split p (fun z rows =>
      ∑ j : Fin h, (positiveOnPrefix z alpha (rows.take (j.val + 1)) -
        negativeOnPrefix z alpha (rows.take (j.val + 1)))) h]
    apply Finset.sum_congr rfl
    intro z _hz
    apply congrArg (fun q : ℝ => p z * q)
    rw [mean_weighted_prefix_sum p htotal
      (fun _ rows => positiveOnPrefix z alpha rows - negativeOnPrefix z alpha rows) h]
    rw [← Finset.sum_range (fun n =>
      ∑ rows : Fin (n + 1) → Key I X T, (∏ i, p (rows i)) *
        (positiveOnPrefix z alpha (List.ofFn rows) -
          negativeOnPrefix z alpha (List.ofFn rows)))]
    apply Finset.sum_congr rfl
    intro n _hn
    rw [(mean_finite_word_integral p (n + 1)
      (fun rows => positiveOnPrefix z alpha (List.ofFn rows)) hp).2,
      (mean_finite_word_integral p (n + 1)
      (fun rows => negativeOnPrefix z alpha (List.ofFn rows)) hp).2]
    simp only [mul_sub, Finset.sum_sub_distrib]
  refine ⟨(mean_finite_word_integral p (h + 1) (blockStatistic alpha h) hp).1,
    ?_, hblock, ?_⟩
  · intro z n
    exact ⟨(mean_positive_prefix_integral p z alpha n hp).1,
      (mean_finite_word_integral p (n + 1)
        (fun rows => negativeOnPrefix z alpha (List.ofFn rows)) hp).1⟩
  · rw [hblock]
    apply Finset.sum_congr rfl
    intro z _hz
    by_cases hz : 0 < p z
    · rw [if_pos hz]
      apply congrArg (fun q : ℝ => p z * q)
      apply Finset.sum_congr rfl
      intro n _hn
      have ht : 0 < targetMass p z :=
        (PidMgwBridgeCandidate.supported_anchor_domains I X T p z hp hz).2.2.1
      rw [(mean_positive_prefix_integral p z alpha n hp).2,
        PidPrefixProbabilityCandidate.negative_increment_expectation I X T p z alpha n hp ht]
    · have hzero : p z = 0 := le_antisymm (le_of_not_gt hz) (hp.1 z)
      simp only [hzero, zero_mul]



private lemma mean_cumulative_split {L : Type u} [Fintype L] [PartialOrder L]
    [DecidableLE L] [DecidableEq L] (f : L → ℝ) (a : L) :
    PidJoinLogContract.cumulative f a =
      (∑ x ∈ Finset.univ.erase a, if x ≤ a then f x else 0) + f a := by
  classical
  unfold PidJoinLogContract.cumulative
  rw [← Finset.sum_erase_add Finset.univ (fun x => if x ≤ a then f x else 0)
    (Finset.mem_univ a)]
  simp only [le_refl, ite_true]

private lemma mean_hasSum_of_cumulative {L : Type u} [Fintype L] [PartialOrder L]
    [DecidableLE L] (terms : ℕ → L → ℝ) (limit : L → ℝ)
    (h : ∀ a, HasSum (fun n => PidJoinLogContract.cumulative (terms n) a)
      (PidJoinLogContract.cumulative limit a)) :
    ∀ a, HasSum (fun n => terms n a) (limit a) := by
  classical
  intro a
  induction a using WellFoundedLT.induction with
  | ind a ih =>
    have hs (x : L) (hx : x ∈ Finset.univ.erase a) :
        HasSum (fun n => if x ≤ a then terms n x else 0)
          (if x ≤ a then limit x else 0) := by
      by_cases hxa : x ≤ a
      · simpa only [hxa, ite_true] using
          ih x (lt_of_le_of_ne hxa (Finset.ne_of_mem_erase hx))
      · simp only [hxa, ite_false]
        exact hasSum_zero
    have hrest := hasSum_sum (s := Finset.univ.erase a) (fun x hx => hs x hx)
    have hdifference := (h a).sub hrest
    have hvalue : PidJoinLogContract.cumulative limit a -
        (∑ x ∈ Finset.univ.erase a, if x ≤ a then limit x else 0) = limit a := by
      rw [mean_cumulative_split]
      ring
    rw [hvalue] at hdifference
    exact hdifference.congr_fun (fun n => by
      rw [mean_cumulative_split]
      ring)

private lemma mean_cumulative_model {I : Type u} [Fintype I] [DecidableEq I]
    (sigma : SemilatticeSup (Node I)) (hsigma : ExactOps sigma)
    (r : Node I → ℝ) (a : Node I) :
    cumulative r a = @PidJoinLogContract.cumulative (Node I) (nodeFintype I)
      sigma.toLE (Classical.decRel sigma.le) r a := by
  classical
  unfold cumulative PidJoinLogContract.cumulative
  apply Finset.sum_congr rfl
  intro x _hx
  simp only [hsigma.1 x a]

private lemma mean_hasSum_of_raw_cumulative {I : Type u} [Fintype I] [Nonempty I]
    [DecidableEq I] (terms : ℕ → Node I → ℝ) (limit : Node I → ℝ)
    (h : ∀ a, HasSum (fun n => cumulative (terms n) a) (cumulative limit a)) :
    ∀ a, HasSum (fun n => terms n a) (limit a) := by
  classical
  obtain ⟨sigma, hsigma⟩ := (PidMgwBridgeCandidate.actual_join_lub I).2
  apply @mean_hasSum_of_cumulative (Node I) (nodeFintype I)
    sigma.toPartialOrder (Classical.decRel sigma.le) terms limit
  intro a
  have ha := h a
  simp_rw [mean_cumulative_model sigma hsigma] at ha
  exact ha

private lemma mean_log_hasSum (x : ℝ) (hx : 0 < x) (hx1 : x ≤ 1) :
    HasSum (fun n : ℕ => (1 - x) ^ (n + 1) / ((n : ℝ) + 1)) (-Real.log x) := by
  have hsmall : |1 - x| < 1 := by
    rw [abs_of_nonneg (sub_nonneg.mpr hx1)]
    linarith
  have hsub : 1 - (1 - x) = x := by ring
  simpa only [hsub] using Real.hasSum_pow_div_log_of_abs_lt_one hsmall

private lemma mean_negative_log_hasSum (q v : ℝ)
    (hq : 0 < q) (hq1 : q ≤ 1) (hv : 0 < v) (hv1 : v ≤ 1) :
    HasSum (fun n : ℕ =>
      ((1 - q) ^ (n + 1) - (1 - v) ^ (n + 1)) / ((n : ℝ) + 1))
      (Real.log (v / q)) := by
  have h := (mean_log_hasSum q hq hq1).sub (mean_log_hasSum v hv hv1)
  have hvalue : -Real.log q - -Real.log v = Real.log (v / q) := by
    rw [Real.log_div (ne_of_gt hv) (ne_of_gt hq)]
    ring
  rw [hvalue] at h
  simpa only [sub_div] using h

private lemma mean_choose_div (n k : ℕ) :
    (Nat.choose n k : ℝ) / ((k : ℝ) + 1) =
      (Nat.choose (n + 1) (k + 1) : ℝ) / ((n : ℝ) + 1) := by
  apply (div_eq_div_iff (by positivity) (by positivity)).2
  have h : ((n : ℝ) + 1) * (Nat.choose n k : ℝ) =
      (Nat.choose (n + 1) (k + 1) : ℝ) * ((k : ℝ) + 1) := by
    exact_mod_cast Nat.add_one_mul_choose_eq n k
  nlinarith [h]

private lemma mean_binomial_cancel (b w : ℝ) (n : ℕ) :
    (∑ k ∈ Finset.range (n + 1),
      (Nat.choose n k : ℝ) * w ^ (k + 1) * b ^ (n - k) / ((k : ℝ) + 1)) =
      ((w + b) ^ (n + 1) - b ^ (n + 1)) / ((n : ℝ) + 1) := by
  have hbin := add_pow w b (n + 1)
  rw [Finset.sum_range_succ'] at hbin
  simp only [Nat.add_sub_add_right, pow_zero, Nat.sub_zero, Nat.choose_zero_right,
    Nat.cast_one, mul_one, one_mul] at hbin
  calc
    _ = (∑ k ∈ Finset.range (n + 1),
        w ^ (k + 1) * b ^ (n - k) * (Nat.choose (n + 1) (k + 1) : ℝ)) /
        ((n : ℝ) + 1) := by
      rw [Finset.sum_div]
      apply Finset.sum_congr rfl
      intro k _hk
      calc
        _ = ((Nat.choose n k : ℝ) / ((k : ℝ) + 1)) *
            (w ^ (k + 1) * b ^ (n - k)) := by ring
        _ = ((Nat.choose (n + 1) (k + 1) : ℝ) / ((n : ℝ) + 1)) *
            (w ^ (k + 1) * b ^ (n - k)) := by rw [mean_choose_div]
        _ = _ := by ring
    _ = _ := by
      congr 1
      linarith [hbin]

private lemma mean_binomial_thinning (q v : ℝ) (hv : v ≠ 0) (n : ℕ) :
    (∑ k ∈ Finset.range (n + 1),
      (Nat.choose n k : ℝ) * v ^ (k + 1) * (1 - v) ^ (n - k) *
        (1 - q / v) ^ (k + 1) / ((k : ℝ) + 1)) =
      ((1 - q) ^ (n + 1) - (1 - v) ^ (n + 1)) / ((n : ℝ) + 1) := by
  have hmul : v * (1 - q / v) = v - q := by
    field_simp [hv]
  have hp (k : ℕ) :
      v ^ (k + 1) * (1 - q / v) ^ (k + 1) = (v - q) ^ (k + 1) := by
    rw [← mul_pow, hmul]
  calc
    _ = ∑ k ∈ Finset.range (n + 1),
        (Nat.choose n k : ℝ) * (v - q) ^ (k + 1) * (1 - v) ^ (n - k) /
          ((k : ℝ) + 1) := by
      apply Finset.sum_congr rfl
      intro k _hk
      calc
        _ = (Nat.choose n k : ℝ) *
            (v ^ (k + 1) * (1 - q / v) ^ (k + 1)) * (1 - v) ^ (n - k) /
              ((k : ℝ) + 1) := by ring
        _ = _ := by rw [hp]
    _ = (((v - q) + (1 - v)) ^ (n + 1) - (1 - v) ^ (n + 1)) /
        ((n : ℝ) + 1) := mean_binomial_cancel (1 - v) (v - q) n
    _ = _ := by rw [show (v - q) + (1 - v) = 1 - q by ring]

private lemma mean_power_cumulative {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] (weight : L → ℝ) (n : ℕ) (a : L) :
    PidJoinLogContract.cumulative (PidJoinLogContract.joinPower weight n) a =
      PidJoinLogContract.cumulative weight a ^ (n + 1) := by
  induction n with
  | zero => simp [PidJoinLogContract.joinPower]
  | succ n ih =>
    rw [PidJoinLogContract.joinPower, PidJoinLogCandidate.join_convolution_cumulative L, ih]
    simp only [pow_succ]

private lemma mean_word_cumulative
    (hword : PidPrefixMgwMeanContract.word_coefficient_join_power_target.{u,v,w})
    {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (r : Key I X T → ℝ) (z : Key I X T) (n : ℕ) (a : Node I) :
    cumulative (fun b => wordCoefficient r z b (n + 1)) a =
      cumulative (weights r z) a ^ (n + 1) := by
  classical
  obtain ⟨sigma, hsigma⟩ := (PidMgwBridgeCandidate.actual_join_lub I).2
  have heq : (fun b => wordCoefficient r z b (n + 1)) =
      @PidJoinLogContract.joinPower (Node I) (nodeFintype I) sigma
        (Classical.decEq (Node I)) (weights r z) n := by
    funext b
    exact hword I X T r z b n sigma hsigma
  rw [heq, mean_cumulative_model sigma hsigma]
  rw [@mean_power_cumulative (Node I) (nodeFintype I) sigma
    (Classical.decEq (Node I)) (Classical.decRel sigma.le) (weights r z) n a]
  rw [← mean_cumulative_model sigma hsigma]

private lemma mean_cumulative_div {I : Type u} [Fintype I]
    (r : Node I → ℝ) (c : ℝ) (a : Node I) :
    cumulative (fun b => r b / c) a = cumulative r a / c := by
  classical
  unfold cumulative
  rw [Finset.sum_div]
  apply Finset.sum_congr rfl
  intro b _hb
  by_cases hba : rawLE b.val a.val <;> simp [hba]

private lemma mean_cumulative_combination {I : Type u} {A : Type v} [Fintype I]
    (s : Finset A) (c : A → ℝ) (r : A → Node I → ℝ) (a : Node I) :
    cumulative (fun b => ∑ k ∈ s, c k * r k b) a =
      ∑ k ∈ s, c k * cumulative (r k) a := by
  classical
  let : Fintype (Node I) := nodeFintype I
  unfold cumulative
  calc
    _ = ∑ b : Node I, ∑ k ∈ s, if rawLE b.val a.val then c k * r k b else 0 := by
      apply Finset.sum_congr rfl
      intro b _hb
      by_cases hba : rawLE b.val a.val <;> simp [hba]
    _ = ∑ k ∈ s, ∑ b : Node I, if rawLE b.val a.val then c k * r k b else 0 := by
      rw [Finset.sum_comm]
    _ = _ := by
      apply Finset.sum_congr rfl
      intro k _hk
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro b _hb
      by_cases hba : rawLE b.val a.val <;> simp [hba]

private lemma mean_positive_cumulative
    (hword : PidPrefixMgwMeanContract.word_coefficient_join_power_target.{u,v,w})
    {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (z : Key I X T) (hp : Law p)
    (n : ℕ) (a : Node I) :
    cumulative (fun b =>
      ∫ rows, positiveOnPrefix z b (List.ofFn rows) ∂rowLaw p (n + 1)) a =
      (1 - sourceMass p z a) ^ (n + 1) / ((n : ℝ) + 1) := by
  have heq : (fun b =>
      ∫ rows, positiveOnPrefix z b (List.ofFn rows) ∂rowLaw p (n + 1)) =
      (fun b => wordCoefficient p z b (n + 1) / ((n : ℝ) + 1)) := by
    funext b
    exact PidPrefixProbabilityCandidate.positive_increment_expectation I X T p z b n hp
  rw [heq, mean_cumulative_div, mean_word_cumulative hword]
  rw [PidMgwBridgeCandidate.generator_lower_cumulative I X T p z a, hp.2]

private lemma mean_negative_cumulative
    (hword : PidPrefixMgwMeanContract.word_coefficient_join_power_target.{u,v,w})
    {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (z : Key I X T) (hp : Law p) (hz : 0 < p z)
    (n : ℕ) (a : Node I) :
    cumulative (fun b =>
      ∫ rows, negativeOnPrefix z b (List.ofFn rows) ∂rowLaw p (n + 1)) a =
      ((1 - restrictedMass p z a) ^ (n + 1) -
        (1 - targetMass p z) ^ (n + 1)) / ((n : ℝ) + 1) := by
  classical
  rcases PidMgwBridgeCandidate.supported_anchor_domains I X T p z hp hz with
    ⟨_hfull, _hfull1, hv, _hv1, _hcondz, _hcondpos, _ht, _ht0, _ht1,
      _hct, _hct0, _hct1, hlocal⟩
  rcases hlocal a with ⟨_ha, _ha1, _hqv, _hqv1, _hw, hcw⟩
  have heq : (fun b =>
      ∫ rows, negativeOnPrefix z b (List.ofFn rows) ∂rowLaw p (n + 1)) =
      (fun b => ∑ k ∈ Finset.range (n + 1),
        ((Nat.choose n k : ℝ) * (targetMass p z) ^ (k + 1) *
          (1 - targetMass p z) ^ (n - k) / ((k : ℝ) + 1)) *
            wordCoefficient (conditioned p z) z b (k + 1)) := by
    funext b
    rw [PidPrefixProbabilityCandidate.negative_increment_expectation I X T p z b n hp hv]
    apply Finset.sum_congr rfl
    intro k _hk
    ring
  rw [heq, mean_cumulative_combination]
  calc
    _ = ∑ k ∈ Finset.range (n + 1),
        (Nat.choose n k : ℝ) * (targetMass p z) ^ (k + 1) *
          (1 - targetMass p z) ^ (n - k) *
            (1 - restrictedMass p z a / targetMass p z) ^ (k + 1) /
              ((k : ℝ) + 1) := by
      apply Finset.sum_congr rfl
      intro k _hk
      rw [mean_word_cumulative hword, hcw]
      ring
    _ = _ := mean_binomial_thinning (restrictedMass p z a) (targetMass p z) (ne_of_gt hv) n

private lemma mean_supported_components
    (hword : PidPrefixMgwMeanContract.word_coefficient_join_power_target.{u,v,w})
    {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (z : Key I X T) (hp : Law p) (hz : 0 < p z) :
    ∃ plus minus : Node I → ℝ,
      InfInverse p z plus ∧ MisInverse p z minus ∧
      (∀ other : Node I → ℝ, InfInverse p z other → other = plus) ∧
      (∀ other : Node I → ℝ, MisInverse p z other → other = minus) ∧
      (∀ a : Node I,
        (∀ n : ℕ,
          Integrable (fun rows => positiveOnPrefix z a (List.ofFn rows))
            (rowLaw p (n + 1)) ∧
          Integrable (fun rows => negativeOnPrefix z a (List.ofFn rows))
            (rowLaw p (n + 1))) ∧
        HasSum (fun n : ℕ =>
          ∫ rows, positiveOnPrefix z a (List.ofFn rows) ∂rowLaw p (n + 1)) (plus a) ∧
        HasSum (fun n : ℕ =>
          ∫ rows, negativeOnPrefix z a (List.ofFn rows) ∂rowLaw p (n + 1)) (minus a)) := by
  classical
  rcases PidMgwBridgeCandidate.supported_anchor_domains I X T p z hp hz with
    ⟨hfull, _hfull1, hv, hv1, _hcondz, _hcondpos, _ht, _ht0, _ht1,
      _hct, _hct0, _hct1, hlocal⟩
  obtain ⟨plus, hplus, _hplusModel, hplusUnique⟩ :=
    PidMgwBridgeCandidate.informative_inverse_identification I X T p z hp hfull
  obtain ⟨minus, hminus, _hminusModel, hminusUnique⟩ :=
    PidMgwBridgeCandidate.misinformative_inverse_identification I X T p z hp hz
  have hpseries : ∀ a : Node I, HasSum (fun n : ℕ =>
      ∫ rows, positiveOnPrefix z a (List.ofFn rows) ∂rowLaw p (n + 1)) (plus a) := by
    apply mean_hasSum_of_raw_cumulative
    intro a
    rw [hplus a]
    rcases hlocal a with ⟨ha, ha1, _hqv, _hqv1, _hw, _hcw⟩
    exact (mean_log_hasSum (sourceMass p z a) ha ha1).congr_fun
      (fun n => mean_positive_cumulative hword p z hp n a)
  have hmseries : ∀ a : Node I, HasSum (fun n : ℕ =>
      ∫ rows, negativeOnPrefix z a (List.ofFn rows) ∂rowLaw p (n + 1)) (minus a) := by
    apply mean_hasSum_of_raw_cumulative
    intro a
    rw [hminus a]
    rcases hlocal a with ⟨_ha, _ha1, hqv, hqv1, _hw, _hcw⟩
    have hq : 0 < restrictedMass p z a := (div_pos_iff_of_pos_right hv).mp hqv
    have hq1 : restrictedMass p z a ≤ 1 :=
      le_trans ((div_le_one hv).mp hqv1) hv1
    exact (mean_negative_log_hasSum (restrictedMass p z a) (targetMass p z)
      hq hq1 hv hv1).congr_fun (fun n => mean_negative_cumulative hword p z hp hz n a)
  refine ⟨plus, minus, hplus, hminus, hplusUnique, hminusUnique, ?_⟩
  intro a
  refine ⟨?_, hpseries a, hmseries a⟩
  intro n
  exact ⟨((PidPrefixProbabilityCandidate.finite_product_law I X T p (n + 1) hp).2.2
    (fun rows => positiveOnPrefix z a (List.ofFn rows))).1,
    ((PidPrefixProbabilityCandidate.finite_product_law I X T p (n + 1) hp).2.2
    (fun rows => negativeOnPrefix z a (List.ofFn rows))).1⟩

private lemma mean_inverse_families
    (hword : PidPrefixMgwMeanContract.word_coefficient_join_power_target.{u,v,w})
    {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (hp : Law p) :
    ∃ plus minus : Key I X T → Node I → ℝ,
      (∀ z, p z = 0 → plus z = 0 ∧ minus z = 0) ∧
      (∀ z, 0 < p z →
        InfInverse p z (plus z) ∧ MisInverse p z (minus z) ∧
        (∀ other : Node I → ℝ, InfInverse p z other → other = plus z) ∧
        (∀ other : Node I → ℝ, MisInverse p z other → other = minus z) ∧
        (∀ a : Node I,
          (∀ n : ℕ,
            Integrable (fun rows => positiveOnPrefix z a (List.ofFn rows))
              (rowLaw p (n + 1)) ∧
            Integrable (fun rows => negativeOnPrefix z a (List.ofFn rows))
              (rowLaw p (n + 1))) ∧
          HasSum (fun n : ℕ =>
            ∫ rows, positiveOnPrefix z a (List.ofFn rows) ∂rowLaw p (n + 1)) (plus z a) ∧
          HasSum (fun n : ℕ =>
            ∫ rows, negativeOnPrefix z a (List.ofFn rows) ∂rowLaw p (n + 1)) (minus z a))) := by
  classical
  have hlocal (z : Key I X T) : ∃ plus minus : Node I → ℝ,
      (p z = 0 → plus = 0 ∧ minus = 0) ∧
      (0 < p z →
        InfInverse p z plus ∧ MisInverse p z minus ∧
        (∀ other : Node I → ℝ, InfInverse p z other → other = plus) ∧
        (∀ other : Node I → ℝ, MisInverse p z other → other = minus) ∧
        (∀ a : Node I,
          (∀ n : ℕ,
            Integrable (fun rows => positiveOnPrefix z a (List.ofFn rows))
              (rowLaw p (n + 1)) ∧
            Integrable (fun rows => negativeOnPrefix z a (List.ofFn rows))
              (rowLaw p (n + 1))) ∧
          HasSum (fun n : ℕ =>
            ∫ rows, positiveOnPrefix z a (List.ofFn rows) ∂rowLaw p (n + 1)) (plus a) ∧
          HasSum (fun n : ℕ =>
            ∫ rows, negativeOnPrefix z a (List.ofFn rows) ∂rowLaw p (n + 1)) (minus a))) := by
    by_cases hz : 0 < p z
    · obtain ⟨plus, minus, h⟩ := mean_supported_components hword p z hp hz
      refine ⟨plus, minus, ?_, fun _ => h⟩
      intro hz0
      exact (ne_of_gt hz hz0).elim
    · exact ⟨0, 0, (fun _ => ⟨rfl, rfl⟩), (fun h => (hz h).elim)⟩
  choose plus minus hzero hsupported using hlocal
  exact ⟨plus, minus, hzero, hsupported⟩

private lemma mean_target_from_first_two
    (hword : PidPrefixMgwMeanContract.word_coefficient_join_power_target.{u,v,w})
    (hblock : PidPrefixMgwMeanContract.finite_block_expectation_target.{u,v,w}) :
    PidPrefixMgwMeanContract.prefix_expectations_to_mgw_mean_target.{u,v,w} := by
  classical
  intro I X T _ _ _ _ _ _ _ p hp
  obtain ⟨plus, minus, hzero, hsupported⟩ := mean_inverse_families hword p hp
  refine ⟨plus, minus, hzero, hsupported, ?_, ?_⟩
  · intro a h
    exact (hblock I X T p a h hp).1
  · intro a
    have hanchor (z : Key I X T) : Filter.Tendsto
        (fun h : ℕ => p z * ∑ n ∈ Finset.range h,
          ((∫ rows, positiveOnPrefix z a (List.ofFn rows) ∂rowLaw p (n + 1)) -
            (∫ rows, negativeOnPrefix z a (List.ofFn rows) ∂rowLaw p (n + 1))))
        Filter.atTop (𝓝 (p z * (plus z a - minus z a))) := by
      by_cases hz : 0 < p z
      · have hs := (hsupported z hz).2.2.2.2 a
        exact (hs.2.1.sub hs.2.2).tendsto_sum_nat.const_mul (p z)
      · have hpz : p z = 0 := le_antisymm (le_of_not_gt hz) (hp.1 z)
        simp only [hpz, zero_mul]
        exact tendsto_const_nhds
    have hsum := tendsto_finsetSum Finset.univ (fun z _hz => hanchor z)
    convert hsum using 1
    funext h
    exact (hblock I X T p a h hp).2.2.1


private lemma proposed_prefix_expectations_to_mgw_mean :
    prefix_expectations_to_mgw_mean_target.{u,v,w} :=
  mean_target_from_first_two proposed_word_coefficient_join_power proposed_finite_block_expectation

theorem word_coefficient_join_power : word_coefficient_join_power_target.{u,v,w} :=
  proposed_word_coefficient_join_power

theorem finite_block_expectation : finite_block_expectation_target.{u,v,w} :=
  proposed_finite_block_expectation

theorem prefix_expectations_to_mgw_mean : prefix_expectations_to_mgw_mean_target.{u,v,w} :=
  proposed_prefix_expectations_to_mgw_mean

end PidPrefixMgwMeanCandidate

