import PidPrefixMgwMean.Contract
import PidMgwBridge.Candidate
import PidPrefixProbability.Candidate

/-! Exploratory private source helpers. No Lean/compiler/kernel execution has occurred for
this file. No frozen target proof or public alias is supplied. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal Topology
open MeasureTheory
open PidMgwBridgeContract
open PidPrefixProbabilityContract
universe u v w
namespace PidPrefixMgwMeanCandidate

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

end PidPrefixMgwMeanCandidate
