import PidPrefixMgwBias.Contract
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal Topology
open MeasureTheory
open PidPrefixMgwBiasSource
open PidMgwBridgeContract
open PidPrefixProbabilityContract
universe u v w
namespace PidPrefixMgwBiasCandidate

private lemma shifted_hasSum (f : ℕ → ℝ) (s : ℝ) (hf : HasSum f s) (h : ℕ) :
    HasSum (fun n => f (n + h)) (s - ∑ n ∈ Finset.range h, f n) := by
  have ht := (summable_nat_add_iff h).mpr hf.summable
  have he := hf.summable.sum_add_tsum_nat_add h
  rw [hf.tsum_eq] at he
  have hv : s - ∑ n ∈ Finset.range h, f n = ∑' n : ℕ, f (n + h) := by linarith
  rw [hv]
  exact ht.hasSum

private lemma log_hasSum (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1) :
    HasSum (fun n : ℕ => (1 - q) ^ (n + 1) / ((n : ℝ) + 1)) (-Real.log q) := by
  have hsmall : |1 - q| < 1 := by
    rw [abs_of_nonneg (sub_nonneg.mpr hq1)]
    linarith
  simpa only [show 1 - (1 - q) = q by ring] using
    Real.hasSum_pow_div_log_of_abs_lt_one hsmall

private lemma remainder_hasSum (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1) (h : ℕ) :
    HasSum (fun n : ℕ =>
      (1 - q) ^ (n + h + 1) / (((n + h : ℕ) : ℝ) + 1)) (logRemainder q h) := by
  exact shifted_hasSum _ _ (log_hasSum q hq hq1) h

private lemma geometric_tail_hasSum (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1) (h : ℕ) :
    HasSum (fun n : ℕ => (1 - q) ^ (n + h + 1)) ((1 - q) ^ (h + 1) / q) := by
  have hg := (hasSum_geometric_of_lt_one (sub_nonneg.mpr hq1)
    (show 1 - q < 1 by linarith)).mul_left ((1 - q) ^ (h + 1))
  rw [show 1 - (1 - q) = q by ring] at hg
  simpa only [div_eq_mul_inv] using hg.congr_fun (fun n => by
    rw [show n + h + 1 = (h + 1) + n by omega, pow_add])

private lemma remainder_basic (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1) (h : ℕ) :
    0 ≤ logRemainder q h ∧ logRemainder q h ≤ -Real.log q ∧
    logRemainder q h ≤ (1 - q) ^ (h + 1) / (((h : ℝ) + 1) * q) ∧
    logRemainder q h ≤ (1 / q - 1) / ((h : ℝ) + 1) := by
  have hr := remainder_hasSum q hq hq1 h
  have hnon : 0 ≤ logRemainder q h := hr.nonneg (fun n => by positivity)
  have hlog : logRemainder q h ≤ -Real.log q := by
    unfold logRemainder
    have hh : 0 ≤ ∑ n ∈ Finset.range h, (1 - q) ^ (n + 1) / ((n : ℝ) + 1) :=
      Finset.sum_nonneg (fun n _ => by positivity)
    linarith
  have hg := (geometric_tail_hasSum q hq hq1 h).div_const ((h : ℝ) + 1)
  have hbound : logRemainder q h ≤
      ((1 - q) ^ (h + 1) / q) / ((h : ℝ) + 1) := by
    apply hasSum_le _ hr hg
    intro n
    apply div_le_div_of_nonneg_left (pow_nonneg (sub_nonneg.mpr hq1) _) (by positivity)
    push_cast
    linarith [show (0 : ℝ) ≤ n by positivity]
  have hgeom : logRemainder q h ≤ (1 - q) ^ (h + 1) / (((h : ℝ) + 1) * q) := by
    simpa only [div_div, mul_comm] using hbound
  have hpow : (1 - q) ^ (h + 1) ≤ 1 - q := by
    calc
      _ = (1 - q) ^ h * (1 - q) := pow_succ _ _
      _ ≤ 1 * (1 - q) := mul_le_mul_of_nonneg_right
        (pow_le_one₀ (sub_nonneg.mpr hq1) (by linarith)) (sub_nonneg.mpr hq1)
      _ = _ := one_mul _
  refine ⟨hnon, hlog, hgeom, hgeom.trans ?_⟩
  calc
    _ ≤ (1 - q) / (((h : ℝ) + 1) * q) :=
      div_le_div_of_nonneg_right hpow (by positivity)
    _ = _ := by field_simp

private lemma remainder_difference (q v : ℝ) (hq : 0 < q) (hqv : q ≤ v)
    (hv1 : v ≤ 1) (h : ℕ) :
    0 ≤ logRemainder q h - logRemainder v h ∧
    logRemainder q h - logRemainder v h ≤
      ((1 - q) ^ (h + 1) / q - (1 - v) ^ (h + 1) / v) / ((h : ℝ) + 1) ∧
    logRemainder q h - logRemainder v h ≤
      (1 / q - 1 / v) / ((h : ℝ) + 1) := by
  have hv : 0 < v := hq.trans_le hqv
  have hq1 : q ≤ 1 := hqv.trans hv1
  have hp (n : ℕ) : 0 ≤ (1 - q) ^ n - (1 - v) ^ n :=
    sub_nonneg.mpr (pow_le_pow_left₀ (sub_nonneg.mpr hv1) (by linarith) n)
  have hr : HasSum (fun n : ℕ =>
      ((1 - q) ^ (n + h + 1) - (1 - v) ^ (n + h + 1)) /
        (((n + h : ℕ) : ℝ) + 1)) (logRemainder q h - logRemainder v h) := by
    simpa only [sub_div] using
      (remainder_hasSum q hq hq1 h).sub (remainder_hasSum v hv hv1 h)
  have hg := (geometric_tail_hasSum q hq hq1 h).sub
    (geometric_tail_hasSum v hv hv1 h)
  have hb : logRemainder q h - logRemainder v h ≤
      ((1 - q) ^ (h + 1) / q - (1 - v) ^ (h + 1) / v) / ((h : ℝ) + 1) := by
    apply hasSum_le _ hr (hg.div_const ((h : ℝ) + 1))
    intro n
    apply div_le_div_of_nonneg_left (hp _) (by positivity)
    push_cast
    linarith [show (0 : ℝ) ≤ n by positivity]
  have hfull := (geometric_tail_hasSum q hq hq1 0).sub
    (geometric_tail_hasSum v hv hv1 0)
  have ht := shifted_hasSum _ _ hfull h
  have hvalue : (1 - q) ^ (h + 1) / q - (1 - v) ^ (h + 1) / v =
      ((1 - q) ^ (0 + 1) / q - (1 - v) ^ (0 + 1) / v) -
        ∑ n ∈ Finset.range h, ((1 - q) ^ (n + 0 + 1) - (1 - v) ^ (n + 0 + 1)) := by
    apply hg.unique
    simpa only [Nat.add_zero] using ht
  have hfin : 0 ≤ ∑ n ∈ Finset.range h,
      ((1 - q) ^ (n + 0 + 1) - (1 - v) ^ (n + 0 + 1)) :=
    Finset.sum_nonneg (fun n _ => hp _)
  have he : (1 - q) ^ (0 + 1) / q - (1 - v) ^ (0 + 1) / v = 1 / q - 1 / v := by
    simp only [zero_add, pow_one]
    field_simp
    ring
  refine ⟨hr.nonneg (fun n => div_nonneg (hp _) (by positivity)), hb, hb.trans ?_⟩
  apply div_le_div_of_nonneg_right _ (by positivity)
  rw [hvalue, he]
  linarith

private lemma dominated_tail (f g : ℕ → ℝ) (s t : ℝ)
    (hf : HasSum f s) (hg : HasSum g t)
    (hf0 : ∀ n, 0 ≤ f n) (hfg : ∀ n, f n ≤ g n) (h : ℕ) :
    0 ≤ s - ∑ n ∈ Finset.range h, f n ∧
      s - ∑ n ∈ Finset.range h, f n ≤ t - ∑ n ∈ Finset.range h, g n := by
  have hft := shifted_hasSum f s hf h
  have hgt := shifted_hasSum g t hg h
  exact ⟨hft.nonneg (fun n => hf0 _), hasSum_le (fun n => hfg _) hft hgt⟩

/- Binomial algebra copied from the accepted mean source (17fc2d8f...), rechecked here. -/
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


private lemma power_cumulative {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] (weight : L → ℝ) (n : ℕ) (a : L) :
    PidJoinLogContract.cumulative (PidJoinLogContract.joinPower weight n) a =
      PidJoinLogContract.cumulative weight a ^ (n + 1) := by
  induction n with
  | zero => simp [PidJoinLogContract.joinPower]
  | succ n ih =>
    rw [PidJoinLogContract.joinPower, PidJoinLogCandidate.join_convolution_cumulative L, ih]
    simp only [pow_succ]

private lemma join_envelope {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] (weight : L → ℝ)
    (hw : ∀ a, 0 ≤ weight a) (n : ℕ) (a : L) :
    0 ≤ PidJoinLogContract.joinPower weight n a ∧
      PidJoinLogContract.joinPower weight n a ≤
        PidJoinLogContract.cumulative weight a ^ (n + 1) := by
  have hn := PidJoinLogCandidate.join_power_nonnegative L weight hw n
  refine ⟨hn a, ?_⟩
  rw [← power_cumulative]
  unfold PidJoinLogContract.cumulative
  have hs := Finset.single_le_sum
    (s := Finset.univ) (f := fun x => if x ≤ a then PidJoinLogContract.joinPower weight n x else 0)
    (fun x _ => by split_ifs <;> first | exact hn x | exact le_rfl) (Finset.mem_univ a)
  simpa only [le_refl, if_true] using hs

private lemma cumulative_model {I : Type u} [Fintype I] [DecidableEq I]
    (sigma : SemilatticeSup (Node I)) (hsigma : ExactOps sigma)
    (r : Node I → ℝ) (a : Node I) :
    cumulative r a = @PidJoinLogContract.cumulative (Node I) (nodeFintype I)
      sigma.toLE (Classical.decRel sigma.le) r a := by
  classical
  unfold cumulative PidJoinLogContract.cumulative
  apply Finset.sum_congr rfl
  intro x _hx
  simp only [hsigma.1 x a]

private lemma word_envelope : word_coordinate_envelope_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p z alpha n hp
  classical
  obtain ⟨sigma, hsigma⟩ := (PidMgwBridgeCandidate.actual_join_lub I).2
  have hw := (PidMgwBridgeCandidate.generator_nonnegative_and_total I X T p z hp.1).1
  have he := @join_envelope (Node I) (nodeFintype I) sigma
    (Classical.decEq (Node I)) (Classical.decRel sigma.le) (weights p z) hw n alpha
  rw [← PidPrefixMgwMeanCandidate.word_coefficient_join_power I X T p z alpha n sigma hsigma,
    ← cumulative_model sigma hsigma,
    PidMgwBridgeCandidate.generator_lower_cumulative I X T p z alpha, hp.2] at he
  exact he

private lemma anchor_domains {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (hp : Law p) (z : Key I X T) (hz : 0 < p z) (alpha : Node I) :
    p z ≤ restrictedMass p z alpha ∧
    restrictedMass p z alpha ≤ sourceMass p z alpha ∧
    restrictedMass p z alpha ≤ targetMass p z ∧
    sourceMass p z alpha ≤ 1 ∧ targetMass p z ≤ 1 := by
  classical
  have hd := PidMgwBridgeCandidate.supported_anchor_domains I X T p z hp hz
  refine ⟨?_, ?_, ?_, (hd.2.2.2.2.2.2.2.2.2.2.2.2 alpha).2.1, hd.2.2.2.1⟩
  · exact Finset.single_le_sum (fun x _ => hp.1 x)
      (PidFiniteConvergence.sx_target_restricted_event_anchor_mem alpha.property.1 z)
  · unfold restrictedMass sourceMass PidFiniteConvergence.finiteEventMass
    rw [PidFiniteConvergence.sx_target_restricted_event_eq_inter]
    exact Finset.sum_le_sum_of_subset_of_nonneg Finset.inter_subset_left
      (fun x _ _ => hp.1 x)
  · unfold restrictedMass targetMass PidFiniteConvergence.finiteEventMass
    rw [PidFiniteConvergence.sx_target_restricted_event_eq_inter]
    exact Finset.sum_le_sum_of_subset_of_nonneg Finset.inter_subset_right
      (fun x _ _ => hp.1 x)

private lemma raw_envelopes : raw_increment_envelopes_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p z alpha n hp hz
  classical
  have hd := anchor_domains p hp z hz alpha
  have hq : 0 < restrictedMass p z alpha := hz.trans_le hd.1
  have hv : 0 < targetMass p z := hq.trans_le hd.2.2.1
  have hw := word_envelope I X T p z alpha n hp
  have hc := PidMgwBridgeCandidate.target_conditioning_mass I X T p z hp hv
  have hcs : sourceMass (conditioned p z) z alpha =
      restrictedMass p z alpha / targetMass p z := by
    unfold sourceMass
    rw [hc.2]
    rw [← PidFiniteConvergence.sx_target_restricted_event_eq_inter]
    rfl
  have hcw (k : ℕ) := word_envelope I X T (conditioned p z) z alpha k hc.1
  have hcw' (k : ℕ) : wordCoefficient (conditioned p z) z alpha (k + 1) ≤
      (1 - restrictedMass p z alpha / targetMass p z) ^ (k + 1) := by
    simpa only [hcs] using (hcw k).2
  refine ⟨div_nonneg hw.1 (by positivity),
    div_le_div_of_nonneg_right hw.2 (by positivity), ?_, ?_⟩
  · unfold negativeMeanIncrement
    exact Finset.sum_nonneg (fun k _ => div_nonneg
      (mul_nonneg (mul_nonneg (mul_nonneg (Nat.cast_nonneg _) (pow_nonneg hv.le _))
        (pow_nonneg (sub_nonneg.mpr hd.2.2.2.2) _)) (hcw k).1) (by positivity))
  · unfold negativeMeanIncrement
    rw [← mean_binomial_thinning (restrictedMass p z alpha) (targetMass p z) (ne_of_gt hv) n]
    apply Finset.sum_le_sum
    intro k _hk
    apply div_le_div_of_nonneg_right _ (by positivity)
    apply mul_le_mul_of_nonneg_left (hcw' k)
    exact mul_nonneg (mul_nonneg (Nat.cast_nonneg _) (pow_nonneg hv.le _))
      (pow_nonneg (sub_nonneg.mpr hd.2.2.2.2) _)

private lemma average_eq_sum {K : Type u} [Fintype K] (p f : K → ℝ)
    (hp : ∀ z, 0 ≤ p z) : supportedAverage p f = ∑ z, p z * f z := by
  classical
  unfold supportedAverage
  apply Finset.sum_congr rfl
  intro z _hz
  by_cases hz : 0 < p z
  · simp only [hz, if_true]
  · have he : p z = 0 := le_antisymm (le_of_not_gt hz) (hp z)
    simp only [he, lt_self_iff_false, if_false, zero_mul]

private lemma average_mono {K : Type u} [Fintype K] (p f g : K → ℝ)
    (hfg : ∀ z, 0 < p z → f z ≤ g z) : supportedAverage p f ≤ supportedAverage p g := by
  classical
  unfold supportedAverage
  apply Finset.sum_le_sum
  intro z _hz
  by_cases hz : 0 < p z
  · simp only [hz, if_true]
    exact mul_le_mul_of_nonneg_left (hfg z hz) hz.le
  · simp only [hz, if_false, le_refl]

private lemma average_const {K : Type u} [Fintype K] (p : K → ℝ) (hp : Law p) (c : ℝ) :
    supportedAverage p (fun _ => c) = c := by
  rw [average_eq_sum p _ hp.1, ← Finset.sum_mul]
  change total p * c = c
  rw [hp.2, one_mul]

private lemma average_sub {K : Type u} [Fintype K] (p f g : K → ℝ) :
    supportedAverage p (fun z => f z - g z) = supportedAverage p f - supportedAverage p g := by
  classical
  unfold supportedAverage
  rw [← Finset.sum_sub_distrib]
  apply Finset.sum_congr rfl
  intro z _hz
  by_cases hz : 0 < p z <;> simp [hz, mul_sub]

private lemma average_div {K : Type u} [Fintype K] (p f : K → ℝ) (c : ℝ) :
    supportedAverage p (fun z => f z / c) = supportedAverage p f / c := by
  classical
  unfold supportedAverage
  rw [Finset.sum_div]
  apply Finset.sum_congr rfl
  intro z _hz
  by_cases hz : 0 < p z <;> simp [hz, mul_div_assoc]

private lemma fiber_nonneg {K : Type u} {Q : Type v} [Fintype K]
    (p : K → ℝ) (hp : ∀ z, 0 ≤ p z) (f : K → Q) (y : Q) : 0 ≤ fiberMass p f y := by
  classical
  unfold fiberMass
  exact Finset.sum_nonneg (fun z _ => by split_ifs <;> first | exact hp z | exact le_rfl)

private lemma fiber_anchor_le {K : Type u} {Q : Type v} [Fintype K]
    (p : K → ℝ) (hp : ∀ z, 0 ≤ p z) (f : K → Q) (z : K) :
    p z ≤ fiberMass p f (f z) := by
  classical
  unfold fiberMass
  have hs := Finset.single_le_sum (s := Finset.univ)
    (f := fun x => if f x = f z then p x else 0)
    (fun x _ => by split_ifs <;> first | exact hp x | exact le_rfl) (Finset.mem_univ z)
  simpa only [if_true] using hs

private lemma proof_fiber_inverse : fiber_inverse_moment_target.{u,v} := by
  intro K Q _ _ p f hp
  classical
  rw [inverseMoment, average_eq_sum p _ hp.1]
  calc
    _ = ∑ z, ∑ y : Q, if f z = y then p z / fiberMass p f y else 0 := by
      apply Finset.sum_congr rfl
      intro z _hz
      simp only [Finset.sum_ite_eq, Finset.mem_univ, if_true, mul_one_div]
    _ = ∑ y : Q, ∑ z, if f z = y then p z / fiberMass p f y else 0 := Finset.sum_comm
    _ = ∑ y : Q, fiberMass p f y / fiberMass p f y := by
      apply Finset.sum_congr rfl
      intro y _hy
      unfold fiberMass
      rw [Finset.sum_div]
      apply Finset.sum_congr rfl
      intro z _hz
      by_cases hz : f z = y <;> simp [hz]
    _ = ∑ y : Q, if 0 < fiberMass p f y then (1 : ℝ) else 0 := by
      apply Finset.sum_congr rfl
      intro y _hy
      by_cases hy : 0 < fiberMass p f y
      · simp [hy, ne_of_gt hy]
      · have hzero : fiberMass p f y = 0 :=
          le_antisymm (le_of_not_gt hy) (fiber_nonneg p hp.1 f y)
        simp [hzero]
    _ = _ := by simp only [Finset.sum_boole, positiveSupportCard]

private lemma inverse_antitone {K : Type u} [Fintype K] (p q r : K → ℝ)
    (hq : ∀ z, 0 < p z → 0 < q z) (hqr : ∀ z, 0 < p z → q z ≤ r z) :
    inverseMoment p r ≤ inverseMoment p q := by
  apply average_mono
  intro z hz
  exact one_div_le_one_div_of_le (hq z hz) (hqr z hz)

private lemma inverse_lower {K : Type u} [Fintype K] (p q : K → ℝ) (hp : Law p)
    (hq : ∀ z, 0 < p z → 0 < q z ∧ q z ≤ 1) : 1 ≤ inverseMoment p q := by
  rw [← average_const p hp 1]
  apply average_mono
  intro z hz
  exact (le_div_iff₀ (hq z hz).1).mpr (by simpa using (hq z hz).2)

private lemma inverse_self {K : Type u} [Fintype K] (p : K → ℝ) :
    inverseMoment p p = (positiveSupportCard p : ℝ) := by
  classical
  unfold inverseMoment supportedAverage positiveSupportCard
  rw [← Finset.sum_boole]
  apply Finset.sum_congr rfl
  intro z _hz
  by_cases hz : 0 < p z
  · simp [hz, ne_of_gt hz]
  · simp only [hz, if_false]

private lemma target_fiber {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (z : Key I X T) :
    targetMass p z = fiberMass p (fun x : Key I X T => x.2) z.2 := by
  classical
  unfold targetMass PidFiniteConvergence.finiteEventMass PidFiniteConvergence.targetBranchEvent
    PidFiniteConvergence.targetEquivalent fiberMass
  rw [Finset.sum_filter]
  apply Finset.sum_congr rfl
  intro x _hx
  by_cases he : z.2 = x.2 <;> simp [he, eq_comm]

private lemma source_fiber {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (z : Key I X T) (C : Finset I) :
    fiberMass p (sourceProjection (X := X) (T := T) C) (sourceProjection C z) =
      PidFiniteConvergence.finiteEventMass p (PidFiniteConvergence.sourceBranchEvent C z) := by
  classical
  unfold fiberMass PidFiniteConvergence.finiteEventMass PidFiniteConvergence.sourceBranchEvent
  rw [Finset.sum_filter]
  apply Finset.sum_congr rfl
  intro x _hx
  have he : sourceProjection C x = sourceProjection C z ↔
      PidFiniteConvergence.sourceCollectionEquivalent C z x := by
    constructor
    · intro h i hi
      exact (congrFun h ⟨i, hi⟩).symm
    · intro h
      funext i
      exact (h i.val i.property).symm
  simp only [he]

private lemma joint_fiber {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (z : Key I X T) (C : Finset I) :
    fiberMass p (jointProjection (X := X) (T := T) C) (jointProjection C z) =
      PidFiniteConvergence.finiteEventMass p (PidFiniteConvergence.sourceTargetBranchEvent C z) := by
  classical
  unfold fiberMass PidFiniteConvergence.finiteEventMass PidFiniteConvergence.sourceTargetBranchEvent
  rw [Finset.sum_filter]
  apply Finset.sum_congr rfl
  intro x _hx
  have he : jointProjection C x = jointProjection C z ↔
      PidFiniteConvergence.sourceTargetCollectionEquivalent C z x := by
    change (sourceProjection C x, x.2) = (sourceProjection C z, z.2) ↔ _
    rw [Prod.mk.injEq]
    constructor
    · rintro ⟨hs, ht⟩
      exact ⟨fun i hi => (congrFun hs ⟨i, hi⟩).symm, ht.symm⟩
    · rintro ⟨hs, ht⟩
      exact ⟨funext (fun i => (hs i.val i.property).symm), ht.symm⟩
  simp only [he]

private lemma proof_support_moments : support_moment_bounds_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p alpha hp
  classical
  have hd (z) (hz : 0 < p z) := anchor_domains p hp z hz alpha
  have hq (z) (hz : 0 < p z) : 0 < restrictedMass p z alpha := hz.trans_le (hd z hz).1
  have hs : 1 ≤ sourceMoment p alpha := inverse_lower p _ hp (fun z hz =>
    ⟨(hq z hz).trans_le (hd z hz).2.1, (hd z hz).2.2.2.1⟩)
  have ht : 1 ≤ targetMoment p := inverse_lower p _ hp (fun z hz =>
    ⟨(hq z hz).trans_le (hd z hz).2.2.1, (hd z hz).2.2.2.2⟩)
  have htf : targetMoment p =
      (positiveSupportCard (fiberMass p (fun z : Key I X T => z.2)) : ℝ) := by
    change inverseMoment p (fun z => targetMass p z) = _
    simp_rw [target_fiber]
    exact proof_fiber_inverse (Key I X T) T p (fun z => z.2) hp
  refine ⟨hs, inverse_antitone p _ _ hq (fun z hz => (hd z hz).2.1), htf,
    ht, inverse_antitone p _ _ hq (fun z hz => (hd z hz).2.2.1), ?_, ?_⟩
  · rw [← inverse_self p]
    exact inverse_antitone p p _ (fun _ hz => hz) (fun z hz => (hd z hz).1)
  · intro C hC
    have hsf : sourceMoment p alpha ≤
        inverseMoment p (fun z => fiberMass p (sourceProjection (X := X) (T := T) C)
          (sourceProjection C z)) := by
      apply inverse_antitone
      · intro z hz
        exact hz.trans_le (fiber_anchor_le p hp.1 _ z)
      · intro z _hz
        rw [source_fiber]
        exact Finset.sum_le_sum_of_subset_of_nonneg
          (Finset.subset_biUnion_of_mem (fun D => PidFiniteConvergence.sourceBranchEvent D z) hC)
          (fun x _ _ => hp.1 x)
    have hqf : queryMoment p alpha ≤
        inverseMoment p (fun z => fiberMass p (jointProjection (X := X) (T := T) C)
          (jointProjection C z)) := by
      apply inverse_antitone
      · intro z hz
        exact hz.trans_le (fiber_anchor_le p hp.1 _ z)
      · intro z _hz
        rw [joint_fiber]
        exact Finset.sum_le_sum_of_subset_of_nonneg
          (Finset.subset_biUnion_of_mem (fun D => PidFiniteConvergence.sourceTargetBranchEvent D z) hC)
          (fun x _ _ => hp.1 x)
    rw [proof_fiber_inverse (Key I X T) _ p _ hp] at hsf hqf
    exact ⟨hsf, hqf⟩

private lemma actual_block_average {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (hp : Law p) (alpha : Node I) (h : ℕ) :
    actualBlockMean p alpha h = supportedAverage p (fun z =>
      positiveMeanPartial p z alpha h - negativeMeanPartial p z alpha h) := by
  classical
  have he := (PidPrefixMgwMeanCandidate.finite_block_expectation I X T p alpha h hp).2.2.2
  rw [actualBlockMean, he]
  unfold supportedAverage
  apply Finset.sum_congr rfl
  intro z _hz
  by_cases hz : 0 < p z
  · simp only [hz, if_true, positiveMeanPartial, negativeMeanPartial,
      positiveMeanIncrement, negativeMeanIncrement, Finset.sum_sub_distrib]
  · simp only [hz, if_false, mul_zero]

private lemma proof_actual_bias : actual_finite_bias_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p hp
  classical
  obtain ⟨plus, minus, hzero, hsup, _hInt, _hlim⟩ :=
    PidPrefixMgwMeanCandidate.prefix_expectations_to_mgw_mean I X T p hp
  have hpair : SupportedInversePair p plus minus :=
    ⟨hzero, fun z hz => ⟨(hsup z hz).1, (hsup z hz).2.1,
      (hsup z hz).2.2.1, (hsup z hz).2.2.2.1⟩⟩
  have htail : ∀ z, 0 < p z → ∀ (alpha : Node I) (h : ℕ),
      0 ≤ plus z alpha - positiveMeanPartial p z alpha h ∧
      plus z alpha - positiveMeanPartial p z alpha h ≤ logRemainder (sourceMass p z alpha) h ∧
      0 ≤ minus z alpha - negativeMeanPartial p z alpha h ∧
      minus z alpha - negativeMeanPartial p z alpha h ≤
        logRemainder (restrictedMass p z alpha) h - logRemainder (targetMass p z) h := by
    intro z hz alpha h
    have hd := anchor_domains p hp z hz alpha
    have hq : 0 < restrictedMass p z alpha := hz.trans_le hd.1
    have ha : 0 < sourceMass p z alpha := hq.trans_le hd.2.1
    have hv : 0 < targetMass p z := hq.trans_le hd.2.2.1
    have hq1 : restrictedMass p z alpha ≤ 1 := hd.2.1.trans hd.2.2.2.1
    have hs := (hsup z hz).2.2.2.2 alpha
    have hsplus : HasSum (positiveMeanIncrement p z alpha) (plus z alpha) :=
      hs.2.1.congr_fun (fun n =>
        (PidPrefixProbabilityCandidate.positive_increment_expectation I X T p z alpha n hp).symm)
    have hsminus : HasSum (negativeMeanIncrement p z alpha) (minus z alpha) :=
      hs.2.2.congr_fun (fun n =>
        (PidPrefixProbabilityCandidate.negative_increment_expectation I X T p z alpha n hp hv).symm)
    have hb (n) := raw_envelopes I X T p z alpha n hp hz
    have hpt := dominated_tail _ _ _ _ hsplus (log_hasSum _ ha hd.2.2.2.1)
      (fun n => (hb n).1) (fun n => (hb n).2.1) h
    have hnegseries : HasSum (fun n : ℕ =>
        ((1 - restrictedMass p z alpha) ^ (n + 1) - (1 - targetMass p z) ^ (n + 1)) /
          ((n : ℝ) + 1)) (-Real.log (restrictedMass p z alpha) - -Real.log (targetMass p z)) := by
      simpa only [sub_div] using
        (log_hasSum _ hq hq1).sub (log_hasSum _ hv hd.2.2.2.2)
    have hmt := dominated_tail _ _ _ _ hsminus hnegseries
      (fun n => (hb n).2.2.1) (fun n => (hb n).2.2.2) h
    have he : (-Real.log (restrictedMass p z alpha) - -Real.log (targetMass p z)) -
        ∑ n ∈ Finset.range h,
          ((1 - restrictedMass p z alpha) ^ (n + 1) - (1 - targetMass p z) ^ (n + 1)) /
            ((n : ℝ) + 1) =
        logRemainder (restrictedMass p z alpha) h - logRemainder (targetMass p z) h := by
      simp only [logRemainder, sub_div, Finset.sum_sub_distrib]
      ring
    rw [he] at hmt
    exact ⟨hpt.1, hpt.2, hmt.1, hmt.2⟩
  refine ⟨plus, minus, hpair, htail, ?_⟩
  intro alpha h
  have he := actual_block_average p hp alpha h
  have hbias : jointAtomMean p plus minus alpha - actualBlockMean p alpha h =
      supportedAverage p (fun z => plus z alpha - positiveMeanPartial p z alpha h) -
        supportedAverage p (fun z => minus z alpha - negativeMeanPartial p z alpha h) := by
    rw [he, jointAtomMean, ← average_eq_sum p _ hp.1, ← average_sub, ← average_sub]
    congr 1
    funext z
    ring
  have hp0 : 0 ≤ supportedAverage p (fun z => plus z alpha - positiveMeanPartial p z alpha h) := by
    rw [← average_const p hp 0]
    exact average_mono p _ _ (fun z hz => (htail z hz alpha h).1)
  have hm0 : 0 ≤ supportedAverage p (fun z => minus z alpha - negativeMeanPartial p z alpha h) := by
    rw [← average_const p hp 0]
    exact average_mono p _ _ (fun z hz => (htail z hz alpha h).2.2.1)
  have hpB : supportedAverage p (fun z => plus z alpha - positiveMeanPartial p z alpha h) ≤
      positiveEnvelope p alpha h := average_mono p _ _ (fun z hz => (htail z hz alpha h).2.1)
  have hmB : supportedAverage p (fun z => minus z alpha - negativeMeanPartial p z alpha h) ≤
      negativeEnvelope p alpha h := average_mono p _ _ (fun z hz => (htail z hz alpha h).2.2.2)
  have hlow : -negativeEnvelope p alpha h ≤
      jointAtomMean p plus minus alpha - actualBlockMean p alpha h := by rw [hbias]; linarith
  have hupp : jointAtomMean p plus minus alpha - actualBlockMean p alpha h ≤
      positiveEnvelope p alpha h := by rw [hbias]; linarith
  have habs : |jointAtomMean p plus minus alpha - actualBlockMean p alpha h| ≤
      max (positiveEnvelope p alpha h) (negativeEnvelope p alpha h) := abs_le.mpr
        ⟨(neg_le_neg (le_max_right _ _)).trans hlow, hupp.trans (le_max_left _ _)⟩
  have hpq : positiveEnvelope p alpha h ≤
      supportedAverage p (fun z => logRemainder (restrictedMass p z alpha) h) := by
    apply average_mono
    intro z hz
    have hd := anchor_domains p hp z hz alpha
    have hr := (remainder_difference _ _ (hz.trans_le hd.1) hd.2.1 hd.2.2.2.1 h).1
    linarith
  have hmq : negativeEnvelope p alpha h ≤
      supportedAverage p (fun z => logRemainder (restrictedMass p z alpha) h) := by
    apply average_mono
    intro z hz
    have hd := anchor_domains p hp z hz alpha
    have hr := (remainder_basic _ ((hz.trans_le hd.1).trans_le hd.2.2.1) hd.2.2.2.2 h).1
    linarith
  have habsq := habs.trans (max_le hpq hmq)
  have hqs : supportedAverage p (fun z => logRemainder (restrictedMass p z alpha) h) ≤
      querySurprisal p alpha := by
    apply average_mono
    intro z hz
    have hd := anchor_domains p hp z hz alpha
    exact (remainder_basic _ (hz.trans_le hd.1) (hd.2.1.trans hd.2.2.2.1) h).2.1
  have hqi : supportedAverage p (fun z => logRemainder (restrictedMass p z alpha) h) ≤
      (queryMoment p alpha - 1) / ((h : ℝ) + 1) := by
    calc
      _ ≤ supportedAverage p (fun z => (1 / restrictedMass p z alpha - 1) / ((h : ℝ) + 1)) := by
        apply average_mono
        intro z hz
        have hd := anchor_domains p hp z hz alpha
        exact (remainder_basic _ (hz.trans_le hd.1) (hd.2.1.trans hd.2.2.2.1) h).2.2.2
      _ = _ := by rw [average_div, average_sub, average_const p hp]; rfl
  have hpi : positiveEnvelope p alpha h ≤ (sourceMoment p alpha - 1) / ((h : ℝ) + 1) := by
    calc
      _ ≤ supportedAverage p (fun z => (1 / sourceMass p z alpha - 1) / ((h : ℝ) + 1)) := by
        apply average_mono
        intro z hz
        have hd := anchor_domains p hp z hz alpha
        exact (remainder_basic _ ((hz.trans_le hd.1).trans_le hd.2.1) hd.2.2.2.1 h).2.2.2
      _ = _ := by rw [average_div, average_sub, average_const p hp]; rfl
  have hmi : negativeEnvelope p alpha h ≤ (queryMoment p alpha - targetMoment p) / ((h : ℝ) + 1) := by
    calc
      _ ≤ supportedAverage p (fun z =>
          (1 / restrictedMass p z alpha - 1 / targetMass p z) / ((h : ℝ) + 1)) := by
        apply average_mono
        intro z hz
        have hd := anchor_domains p hp z hz alpha
        exact (remainder_difference _ _ (hz.trans_le hd.1) hd.2.2.1 hd.2.2.2.2 h).2.2
      _ = _ := by rw [average_div, average_sub]; rfl
  exact ⟨he, hlow, hupp, habs, habsq, le_min (habsq.trans hqs) (habsq.trans hqi),
    by simpa only [neg_div] using (neg_le_neg hmi).trans hlow, hupp.trans hpi⟩

private lemma pair_unique {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (hp : Law p)
    (plus minus otherPlus otherMinus : Key I X T → Node I → ℝ)
    (hpair : SupportedInversePair p plus minus)
    (hother : SupportedInversePair p otherPlus otherMinus) :
    plus = otherPlus ∧ minus = otherMinus := by
  have hzpair (z : Key I X T) : plus z = otherPlus z ∧ minus z = otherMinus z := by
    by_cases hz : 0 < p z
    · exact ⟨(hother.2 z hz).2.2.1 (plus z) (hpair.2 z hz).1,
        (hother.2 z hz).2.2.2 (minus z) (hpair.2 z hz).2.1⟩
    · have hzero : p z = 0 := le_antisymm (le_of_not_gt hz) (hp.1 z)
      exact ⟨(hpair.1 z hzero).1.trans (hother.1 z hzero).1.symm,
        (hpair.1 z hzero).2.trans (hother.1 z hzero).2.symm⟩
  exact ⟨funext (fun z => (hzpair z).1), funext (fun z => (hzpair z).2)⟩

private lemma proof_projected_bias : projected_support_bias_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p plus minus alpha C hp hpair hC h
  classical
  obtain ⟨otherPlus, otherMinus, hother, _htail, hb⟩ := proof_actual_bias I X T p hp
  obtain ⟨rfl, rfl⟩ := pair_unique p hp plus minus otherPlus otherMinus hpair hother
  rcases proof_support_moments I X T p alpha hp with
    ⟨_hs1, _hsq, hteq, _ht1, _htq, _hqcard, hproj⟩
  rcases hproj C hC with ⟨hsC, hqC⟩
  rcases hb alpha h with ⟨_mean, _low, _upp, _abs, _query, hinverse, hlower, hupper⟩
  have hd : 0 ≤ (h : ℝ) + 1 := by positivity
  refine ⟨?_, ?_, ?_⟩
  · apply le_trans _ hlower
    apply div_le_div_of_nonneg_right _ hd
    rw [← hteq]
    linarith
  · apply hupper.trans
    apply div_le_div_of_nonneg_right _ hd
    linarith
  · apply (hinverse.trans (min_le_right _ _)).trans
    apply div_le_div_of_nonneg_right _ hd
    linarith

private lemma proof_floor_bias : mass_floor_bias_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p plus minus alpha eta hp hpair heta heta1 hfloor h
  classical
  obtain ⟨otherPlus, otherMinus, hother, _htail, hb⟩ := proof_actual_bias I X T p hp
  obtain ⟨rfl, rfl⟩ := pair_unique p hp plus minus otherPlus otherMinus hpair hother
  have hquery := (hb alpha h).2.2.2.2.1
  have henvelope : supportedAverage p (fun z => logRemainder (restrictedMass p z alpha) h) ≤
      logRemainder eta h := by
    rw [← average_const p hp (logRemainder eta h)]
    apply average_mono
    intro z hz
    have hd := anchor_domains p hp z hz alpha
    have hm := (remainder_difference eta (restrictedMass p z alpha) heta
      (hfloor z hz) (hd.2.1.trans hd.2.2.2.1) h).1
    linarith
  have hbound := hquery.trans henvelope
  exact ⟨hbound, hbound.trans (remainder_basic eta heta heta1 h).2.2.1⟩

theorem actual_finite_bias : actual_finite_bias_target.{u,v,w} :=
  proof_actual_bias

theorem fiber_inverse_moment : fiber_inverse_moment_target.{u,v} :=
  proof_fiber_inverse

theorem support_moment_bounds : support_moment_bounds_target.{u,v,w} :=
  proof_support_moments

theorem projected_support_bias : projected_support_bias_target.{u,v,w} :=
  proof_projected_bias

theorem mass_floor_bias : mass_floor_bias_target.{u,v,w} :=
  proof_floor_bias

end PidPrefixMgwBiasCandidate
