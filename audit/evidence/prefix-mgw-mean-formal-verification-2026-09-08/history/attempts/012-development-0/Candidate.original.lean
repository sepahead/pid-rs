import PidPrefixMgwMean.Contract
import PidMgwBridge.Candidate
import PidPrefixProbability.Candidate

/- Source-only successor proposal. No compiler or kernel has checked these revised bodies.
   This file supplies only private helpers and the first frozen target body.
   It is not a complete three-target candidate and is not acceptance evidence. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal
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

private lemma weighted_words_predicate {K : Type u} [Fintype K] [DecidableEq K]
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
  exact hs.trans (hi.trans (hp.trans hm))

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


end PidPrefixMgwMeanCandidate
