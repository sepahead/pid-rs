import PidPrefixProbability.Contract

set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal
open MeasureTheory
open ProbabilityTheory
open PidPrefixProbabilityContract
open PidMgwBridgeContract
universe u v w
namespace PidPrefixProbabilityCandidate

private lemma weighted_integral {K : Type u} [Fintype K] [MeasurableSpace K]
    [MeasurableSingletonClass K] (r : K → ℝ) (hr : ∀ x, 0 ≤ r x) (f : K → ℝ) :
    Integrable f (∑ x, ENNReal.ofReal (r x) • Measure.dirac x) ∧
      (∫ x, f x ∂(∑ x, ENNReal.ofReal (r x) • Measure.dirac x)) =
        ∑ x, r x * f x := by
  classical
  have hi : ∀ x : K, Integrable f (ENNReal.ofReal (r x) • Measure.dirac x) := by
    intro x
    exact (integrable_dirac (by simp)).smul_measure ENNReal.ofReal_ne_top
  refine ⟨integrable_finsetSum_measure.mpr (fun x _ => hi x), ?_⟩
  rw [integral_finsetSum_measure (fun x _ => hi x)]
  apply Finset.sum_congr rfl
  intro x _
  simp [ENNReal.toReal_ofReal (hr x)]

private lemma finite_integrable {K : Type u} [Fintype K] [MeasurableSpace K]
    [MeasurableSingletonClass K] (μ : Measure K) [IsFiniteMeasure μ] (f : K → ℝ) :
    Integrable f μ := by
  classical
  have hm : μ = ∑ x, μ {x} • Measure.dirac x := by
    rw [← Measure.sum_fintype, Measure.sum_smul_dirac]
  rw [hm]
  apply integrable_finsetSum_measure.mpr
  intro x _
  exact (integrable_dirac (by simp)).smul_measure (measure_ne_top μ {x})

private lemma finite_measure_eq {K : Type u} [Fintype K] [MeasurableSpace K]
    [MeasurableSingletonClass K] (μ ν : Measure K)
    (h : ∀ x, μ {x} = ν {x}) : μ = ν := by
  rw [← Measure.sum_smul_dirac μ, ← Measure.sum_smul_dirac ν]
  congr 1
  funext x
  rw [h x]

private lemma proof_finite_law_measure : finite_law_measure_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p hp
  classical
  let : MeasurableSpace (Key I X T) := ⊤
  have hprob : IsProbabilityMeasure (keyMeasure p) := by
    constructor
    simp only [keyMeasure, Measure.finsetSum_apply, Measure.smul_apply,
      Measure.dirac_apply_of_mem (Set.mem_univ _), smul_eq_mul, mul_one]
    rw [← ENNReal.ofReal_sum_of_nonneg (fun x _ => hp.1 x)]
    change ENNReal.ofReal (PidMgwBridgeContract.total p) = 1
    rw [hp.2, ENNReal.ofReal_one]
  refine ⟨hprob, ?_, ?_⟩
  · intro x
    change (∑ a, ENNReal.ofReal (p a) • Measure.dirac a) {x} = ENNReal.ofReal (p x)
    rw [← Measure.sum_fintype]
    exact Measure.sum_smul_dirac_singleton
  · intro f
    exact weighted_integral p hp.1 f

private lemma proof_finite_product_law : finite_product_law_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p count hp
  classical
  let : MeasurableSpace (Key I X T) := ⊤
  have base := proof_finite_law_measure I X T p hp
  let : IsProbabilityMeasure (keyMeasure p) := base.1
  have hprob : IsProbabilityMeasure (rowLaw p count) := by
    unfold rowLaw
    infer_instance
  have hs : ∀ word, rowLaw p count {word} = ENNReal.ofReal (∏ i, p (word i)) := by
    intro word
    rw [rowLaw, Measure.pi_singleton]
    simp only [base.2.1]
    exact (ENNReal.ofReal_prod_of_nonneg (fun i _ => hp.1 (word i))).symm
  refine ⟨hprob, hs, ?_⟩
  intro f
  have hm : rowLaw p count = ∑ word, ENNReal.ofReal (∏ i, p (word i)) •
      Measure.dirac word := by
    conv_lhs => rw [← Measure.sum_smul_dirac (rowLaw p count), Measure.sum_fintype]
    simp only [hs]
  rw [hm]
  exact weighted_integral _ (fun word => Finset.prod_nonneg (fun i _ => hp.1 (word i))) f

private lemma proof_positive_increment_expectation :
    positive_increment_expectation_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p z alpha n hp
  classical
  rw [(proof_finite_product_law I X T p (n + 1) hp).2.2
    (fun rows => positiveOnPrefix z alpha (List.ofFn rows)) |>.2]
  simp only [positiveOnPrefix, List.length_ofFn, Nat.cast_add, Nat.cast_one,
    wordCoefficient, div_eq_mul_inv, Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro word _
  split_ifs <;> ring

private lemma word_sum_cons {K : Type u} [Fintype K] (r : K → ℝ)
    (F : List K → ℝ) (n : ℕ) :
    (∑ word : Fin (n + 1) → K, (∏ i, r (word i)) * F (List.ofFn word)) =
      ∑ x, r x * ∑ word : Fin n → K, (∏ i, r (word i)) * F (x :: List.ofFn word) := by
  classical
  rw [← (Fin.consEquiv (fun _ : Fin (n + 1) => K)).sum_comp]
  rw [Fintype.sum_prod_type]
  simp only [Fin.consEquiv_apply, List.ofFn_succ, Fin.cons_zero, Fin.cons_succ,
    Fin.prod_univ_succ, Finset.mul_sum, mul_assoc]

private lemma word_sum_snoc {K : Type u} [Fintype K] (r : K → ℝ)
    (F : List K → ℝ) (n : ℕ) :
    (∑ word : Fin (n + 1) → K, (∏ i, r (word i)) * F (List.ofFn word)) =
      ∑ x, r x * ∑ word : Fin n → K, (∏ i, r (word i)) * F (List.ofFn word ++ [x]) := by
  classical
  rw [← (Fin.snocEquiv (fun _ : Fin (n + 1) => K)).sum_comp]
  rw [Fintype.sum_prod_type]
  simp only [Fin.snocEquiv_apply]
  simp_rw [List.ofFn_succ_last, Fin.prod_univ_castSucc]
  simp only [Fin.snocEquiv_apply, Fin.snoc_castSucc, Fin.snoc_last]
  simp only [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro x _
  apply Finset.sum_congr rfl
  intro word _
  ring

private lemma filter_recurrence {K : Type u} [Fintype K] (p : K → ℝ)
    (b : K → Bool) (F : List K → ℝ) (n : ℕ) :
    (∑ word : Fin (n + 1) → K, (∏ i, p (word i)) * F ((List.ofFn word).filter b)) =
      (∑ x, if b x then 0 else p x) *
        (∑ word : Fin n → K, (∏ i, p (word i)) * F ((List.ofFn word).filter b)) +
      ∑ word : Fin n → K, (∏ i, p (word i)) *
        (∑ x, (if b x then p x else 0) * F (x :: (List.ofFn word).filter b)) := by
  classical
  rw [word_sum_cons p (fun rows => F (rows.filter b)) n]
  simp only [Finset.sum_mul, Finset.mul_sum]
  rw [Finset.sum_comm (s := Finset.univ) (t := Finset.univ)]
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro word _
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro x _
  cases hx : b x <;> simp [hx, mul_assoc, mul_comm, mul_left_comm]

private lemma choose_succ_sum (f : ℕ → ℕ → ℝ) (n : ℕ) :
    (∑ i ∈ Finset.range (n + 2), ((n + 1).choose i : ℝ) * f i (n + 1 - i)) =
      (∑ i ∈ Finset.range (n + 1), (n.choose i : ℝ) * f i (n + 1 - i)) +
        ∑ i ∈ Finset.range (n + 1), (n.choose i : ℝ) * f (i + 1) (n - i) := by
  have ha : (∑ i ∈ Finset.range (n + 1), (n.choose (i + 1) : ℝ) * f (i + 1) (n - i)) +
      f 0 (n + 1) = ∑ i ∈ Finset.range (n + 1), (n.choose i : ℝ) * f i (n + 1 - i) := by
    rw [Finset.sum_range_succ, Finset.sum_range_succ']
    simp
  rw [Finset.sum_range_succ']
  simpa [Nat.choose_succ_succ, Nat.cast_add, add_mul, Finset.sum_add_distrib, ha, add_assoc]
    using add_comm
      (∑ i ∈ Finset.range (n + 1), (n.choose i : ℝ) * f (i + 1) (n - i))
      ((∑ i ∈ Finset.range (n + 1), (n.choose (i + 1) : ℝ) * f (i + 1) (n - i)) + f 0 (n + 1))

private lemma filtered_word_sum {K : Type u} [Fintype K] (p : K → ℝ)
    (b : K → Bool) (n : ℕ) (F : List K → ℝ) :
    (∑ word : Fin n → K, (∏ i, p (word i)) * F ((List.ofFn word).filter b)) =
      ∑ k ∈ Finset.range (n + 1), (Nat.choose n k : ℝ) *
        (∑ x, if b x then 0 else p x) ^ (n - k) *
        ∑ word : Fin k → K, (∏ i, if b (word i) then p (word i) else 0) *
          F (List.ofFn word) := by
  classical
  induction n generalizing F with
  | zero => simp
  | succ n ih =>
    rw [filter_recurrence, ih F, ih (fun rows => ∑ x, (if b x then p x else 0) * F (x :: rows))]
    have hs : ∀ k : ℕ,
        (∑ word : Fin k → K, (∏ i, if b (word i) then p (word i) else 0) *
          (∑ x, (if b x then p x else 0) * F (x :: List.ofFn word))) =
        ∑ word : Fin (k + 1) → K, (∏ i, if b (word i) then p (word i) else 0) *
          F (List.ofFn word) := by
      intro k
      rw [word_sum_cons (fun x => if b x then p x else 0) F k]
      simp only [Finset.mul_sum]
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro x _
      apply Finset.sum_congr rfl
      intro word _
      ring
    simp only [hs]
    have pascal := choose_succ_sum
      (fun k j => (∑ x, if b x then 0 else p x) ^ j *
        ∑ word : Fin k → K, (∏ i, if b (word i) then p (word i) else 0) *
          F (List.ofFn word)) n
    simp only [← mul_assoc] at pascal
    rw [pascal]
    congr 1
    rw [Finset.mul_sum]
    apply Finset.sum_congr rfl
    intro k hk
    have hk' : k ≤ n := Nat.le_of_lt_succ (Finset.mem_range.mp hk)
    rw [show n + 1 - k = (n - k) + 1 by omega, pow_succ]
    ring

private lemma proof_negative_increment_expectation :
    negative_increment_expectation_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p z alpha n hp hv
  classical
  let b : Key I X T → Bool := fun x => decide (x.2 = z.2)
  let r : Key I X T → ℝ := fun x => if b x then p x else 0
  have hmem : ∀ x : Key I X T, x ∈ PidFiniteConvergence.targetBranchEvent z ↔ x.2 = z.2 := by
    intro x
    exact (PidFiniteConvergence.target_branch_is_equivalence_class.2 z x).trans eq_comm
  have hr : ∀ x, r x = targetMass p z * conditioned p z x := by
    intro x
    by_cases hx : x.2 = z.2
    · simp [r, b, conditioned, hmem, hx, hv.ne', mul_div_cancel₀]
    · simp [r, b, conditioned, hmem, hx]
  have hw : (∑ x, if b x then 0 else p x) = 1 - targetMass p z := by
    have ht : targetMass p z = ∑ x, if b x then p x else 0 := by
      unfold targetMass PidFiniteConvergence.finiteEventMass
      rw [← Finset.sum_filter]
      congr 1
      ext x
      simp [b, hmem]
    rw [ht]
    have ht' : ∑ x, p x = 1 := hp.2
    rw [← ht', ← Finset.sum_sub_distrib]
    apply Finset.sum_congr rfl
    intro x _
    cases b x <;> simp
  have happ : ∀ (rows : List (Key I X T)) x,
      negativeOnPrefix z alpha (rows ++ [x]) =
        if b x then positiveOnPrefix z alpha (rows.filter b ++ [x]) else 0 := by
    intro rows x
    by_cases hx : x.2 = z.2 <;>
      simp [negativeOnPrefix, positiveOnPrefix, List.filter_append, b, hx]
  rw [(proof_finite_product_law I X T p (n + 1) hp).2.2
    (fun rows => negativeOnPrefix z alpha (List.ofFn rows)) |>.2]
  rw [word_sum_snoc]
  simp only [happ]
  have rearrange :
      (∑ x, p x * ∑ word : Fin n → Key I X T, (∏ i, p (word i)) *
        if b x then positiveOnPrefix z alpha ((List.ofFn word).filter b ++ [x]) else 0) =
      ∑ word : Fin n → Key I X T, (∏ i, p (word i)) *
        (∑ x, r x * positiveOnPrefix z alpha ((List.ofFn word).filter b ++ [x])) := by
    simp only [Finset.mul_sum]
    rw [Finset.sum_comm]
    apply Finset.sum_congr rfl
    intro word _
    apply Finset.sum_congr rfl
    intro x _
    cases hb : b x <;> simp [r, hb, mul_comm, mul_left_comm]
  rw [rearrange, filtered_word_sum p b n (fun rows => ∑ x, r x * positiveOnPrefix z alpha (rows ++ [x])), hw]
  apply Finset.sum_congr rfl
  intro k _
  have hs : (∑ word : Fin k → Key I X T, (∏ i, r (word i)) *
      (∑ x, r x * positiveOnPrefix z alpha (List.ofFn word ++ [x]))) =
      ∑ word : Fin (k + 1) → Key I X T, (∏ i, r (word i)) *
        positiveOnPrefix z alpha (List.ofFn word) := by
    rw [word_sum_snoc]
    simp only [Finset.mul_sum]
    rw [Finset.sum_comm]
    apply Finset.sum_congr rfl
    intro x _
    apply Finset.sum_congr rfl
    intro word _
    ring
  change _ * _ * (∑ word : Fin k → Key I X T, (∏ i, r (word i)) *
    (∑ x, r x * positiveOnPrefix z alpha (List.ofFn word ++ [x]))) = _
  rw [hs]
  simp only [hr, Finset.prod_mul_distrib, Finset.prod_const, Finset.card_univ,
    Fintype.card_fin, positiveOnPrefix, List.length_ofFn, Nat.cast_add, Nat.cast_one,
    wordCoefficient, div_eq_mul_inv]
  simp only [Finset.mul_sum, Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro word _
  split_ifs <;> ring

private lemma list_retained_bound {K : Type u} (b : K → Bool) (g : List K → ℝ)
    (hg : ∀ rows x, g (rows ++ [x]) ≤
      if b x then 1 / (((rows.filter b).length : ℝ) + 1) else 0)
    (rows : List K) :
    (∑ j ∈ Finset.range rows.length, g (rows.take (j + 1))) ≤
      ∑ j ∈ Finset.range (rows.filter b).length, 1 / ((j : ℝ) + 1) := by
  classical
  induction rows using List.reverseRecOn with
  | nil => simp
  | append_singleton rows x ih =>
    simp only [List.length_append, List.length_singleton, Finset.sum_range_succ]
    have hearly :
        (∑ j ∈ Finset.range rows.length, g ((rows ++ [x]).take (j + 1))) =
        ∑ j ∈ Finset.range rows.length, g (rows.take (j + 1)) := by
      apply Finset.sum_congr rfl
      intro j hj
      rw [List.take_append_of_le_length (by simpa using Finset.mem_range.mp hj)]
    rw [hearly, show (rows ++ [x]).take (rows.length + 1) = rows ++ [x] by simp]
    have h := hg rows x
    cases hx : b x
    · simpa [List.filter_append, hx] using add_le_add ih h
    · simpa [List.filter_append, hx, Finset.sum_range_succ] using add_le_add ih h

private lemma positive_bounds {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (z : Key I X T) (alpha : Node I) (rows : List (Key I X T)) :
    0 ≤ positiveOnPrefix z alpha rows ∧
      positiveOnPrefix z alpha rows ≤ 1 / (rows.length : ℝ) := by
  classical
  unfold positiveOnPrefix
  split_ifs
  · exact ⟨by positivity, le_rfl⟩
  · exact ⟨le_rfl, by positivity⟩

private lemma negative_nonnegative {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (z : Key I X T) (alpha : Node I) (rows : List (Key I X T)) :
    0 ≤ negativeOnPrefix z alpha rows := by
  classical
  unfold negativeOnPrefix
  split
  · exact le_rfl
  · split_ifs <;> positivity

private lemma proof_block_range : block_range_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ alpha horizon block
  classical
  let z := block 0
  let rows := List.ofFn fun i : Fin horizon => block i.succ
  let b : Key I X T → Bool := fun x => decide (x.2 = z.2)
  have hlen : rows.length = horizon := List.length_ofFn
  have hpos0 : 0 ≤ ∑ j ∈ Finset.range horizon,
      positiveOnPrefix z alpha (rows.take (j + 1)) := by
    apply Finset.sum_nonneg
    intro j _
    exact (positive_bounds z alpha _).1
  have hneg0 : 0 ≤ ∑ j ∈ Finset.range horizon,
      negativeOnPrefix z alpha (rows.take (j + 1)) := by
    apply Finset.sum_nonneg
    intro j _
    exact negative_nonnegative z alpha _
  have hpos : (∑ j ∈ Finset.range horizon,
      positiveOnPrefix z alpha (rows.take (j + 1))) ≤
      ∑ j ∈ Finset.range horizon, 1 / ((j : ℝ) + 1) := by
    apply Finset.sum_le_sum
    intro j hj
    have hj' : j + 1 ≤ rows.length := by rw [hlen]; exact Finset.mem_range.mp hj
    simpa [List.length_take_of_le hj'] using (positive_bounds z alpha (rows.take (j + 1))).2
  have hneg : (∑ j ∈ Finset.range horizon,
      negativeOnPrefix z alpha (rows.take (j + 1))) ≤
      ∑ j ∈ Finset.range horizon, 1 / ((j : ℝ) + 1) := by
    have hg : ∀ (xs : List (Key I X T)) x,
        negativeOnPrefix z alpha (xs ++ [x]) ≤
          if b x then 1 / (((xs.filter b).length : ℝ) + 1) else 0 := by
      intro xs x
      by_cases hx : x.2 = z.2
      · have h := (positive_bounds z alpha (xs.filter b ++ [x])).2
        simpa [negativeOnPrefix, positiveOnPrefix, List.filter_append, b, hx] using h
      · simp [negativeOnPrefix, b, hx]
    have hh := list_retained_bound b (negativeOnPrefix z alpha) hg rows
    rw [hlen] at hh
    apply hh.trans
    apply Finset.sum_le_sum_of_subset_of_nonneg
    · exact Finset.range_mono (by simpa [hlen] using List.length_filter_le b rows)
    · intro j _ _
      positivity
  have hstat : blockStatistic alpha horizon block =
      (∑ j ∈ Finset.range horizon, positiveOnPrefix z alpha (rows.take (j + 1))) -
      (∑ j ∈ Finset.range horizon, negativeOnPrefix z alpha (rows.take (j + 1))) := by
    change (∑ j : Fin horizon, (positiveOnPrefix z alpha (rows.take (j.val + 1)) -
      negativeOnPrefix z alpha (rows.take (j.val + 1)))) = _
    rw [← Finset.sum_range (fun j => positiveOnPrefix z alpha (rows.take (j + 1)) -
      negativeOnPrefix z alpha (rows.take (j + 1))), Finset.sum_sub_distrib]
  have hh : harmonic horizon = ∑ j ∈ Finset.range horizon, 1 / ((j : ℝ) + 1) := by
    exact (Finset.sum_range (fun j : ℕ => (1 : ℝ) / ((j : ℝ) + 1))).symm
  rw [hstat, hh]
  constructor <;> linarith

private lemma curry_product_measure {A : Type u} {B : Type v} {K : Type w}
    [Fintype A] [Fintype B] [Fintype K] [MeasurableSpace K]
    [MeasurableSingletonClass K] (μ : Measure K) [IsProbabilityMeasure μ] :
    (Measure.pi (fun _ : A × B => μ)).map (fun sample a b => sample (a, b)) =
      Measure.pi (fun _ : A => Measure.pi (fun _ : B => μ)) := by
  classical
  apply finite_measure_eq
  intro word
  rw [Measure.map_apply (measurable_of_finite _) (measurableSet_singleton word)]
  have he : (fun (sample : A × B → K) a b => sample (a, b)) ⁻¹' {word} =
      {fun ab : A × B => word ab.1 ab.2} := by
    ext sample
    simp only [Set.mem_preimage, Set.mem_singleton_iff]
    constructor
    · intro h
      funext ab
      exact congrFun (congrFun h ab.1) ab.2
    · intro h
      subst sample
      rfl
  rw [he]
  simp only [Measure.pi_singleton]
  exact Fintype.prod_prod_type (fun ab : A × B => μ {word ab.1 ab.2})

private lemma proof_block_product_independence :
    block_product_independence_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p alpha blocks horizon hp
  classical
  let : MeasurableSpace (Key I X T) := ⊤
  have base := proof_finite_law_measure I X T p hp
  let : IsProbabilityMeasure (keyMeasure p) := base.1
  have hprob : IsProbabilityMeasure (experimentLaw p blocks horizon) := by
    unfold experimentLaw
    infer_instance
  let : IsProbabilityMeasure (experimentLaw p blocks horizon) := hprob
  let : IsProbabilityMeasure (rowLaw p (horizon + 1)) :=
    (proof_finite_product_law I X T p (horizon + 1) hp).1
  let c := fun (sample : Fin blocks × Fin (horizon + 1) → Key I X T)
    (b : Fin blocks) (j : Fin (horizon + 1)) => sample (b, j)
  have hc : (experimentLaw p blocks horizon).map c =
      Measure.pi (fun _ : Fin blocks => rowLaw p (horizon + 1)) :=
    curry_product_measure (keyMeasure p)
  have hm : ∀ b : Fin blocks,
      (experimentLaw p blocks horizon).map (blockProjection blocks horizon b) =
        rowLaw p (horizon + 1) := by
    intro b
    calc
      _ = ((experimentLaw p blocks horizon).map c).map (Function.eval b) := by
        rw [Measure.map_map (measurable_of_finite _) (measurable_of_finite _)]
        rfl
      _ = rowLaw p (horizon + 1) := by
        rw [hc]
        exact (measurePreserving_eval (fun _ : Fin blocks => rowLaw p (horizon + 1)) b).map_eq
  refine ⟨hprob, hm, ?_, ?_, ?_⟩
  · intro b
    exact measurable_of_finite _
  · intro b
    exact finite_integrable _ _
  · have hind : iIndepFun (blockProjection (X := X) (T := T) blocks horizon)
        (experimentLaw p blocks horizon) := by
      apply (iIndepFun_iff_map_fun_eq_pi_map (fun b =>
        (measurable_of_finite (blockProjection (X := X) (T := T) blocks horizon b)).aemeasurable)).mpr
      change (experimentLaw p blocks horizon).map c = _
      rw [hc]
      congr 1
      funext b
      exact (hm b).symm
    exact hind.comp (fun _ => blockStatistic alpha horizon) (fun _ => measurable_of_finite _)

theorem finite_law_measure : finite_law_measure_target.{u,v,w} :=
  proof_finite_law_measure

theorem finite_product_law : finite_product_law_target.{u,v,w} :=
  proof_finite_product_law

theorem positive_increment_expectation : positive_increment_expectation_target.{u,v,w} :=
  proof_positive_increment_expectation

theorem negative_increment_expectation : negative_increment_expectation_target.{u,v,w} :=
  proof_negative_increment_expectation

theorem block_range : block_range_target.{u,v,w} :=
  proof_block_range

theorem block_product_independence : block_product_independence_target.{u,v,w} :=
  proof_block_product_independence

end PidPrefixProbabilityCandidate
