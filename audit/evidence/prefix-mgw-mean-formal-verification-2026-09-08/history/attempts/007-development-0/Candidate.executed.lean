import PidPrefixMgwMean.Contract
import PidMgwBridge.Candidate
import PidPrefixProbability.Candidate

/- Source-only proposal for the second frozen target. No compiler or kernel has
   checked this source. Every declaration is private development material.
   The first target and the infinite mean target are not supplied here. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal
open MeasureTheory
open PidMgwBridgeContract
open PidPrefixProbabilityContract
open PidPrefixMgwMeanContract
universe u v w
namespace PidPrefixMgwMeanCandidate

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
  simpa only [Nat.add_sub_cancel' hmh] using
    mean_weighted_prefix_add p hp F m (h - m)

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
      ∑ j : Fin h, positiveOnPrefix z alpha (rows.take (j.val + 1)) -
        negativeOnPrefix z alpha (rows.take (j.val + 1))) h]
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
