import PidPrefixMgwGradient.Contract

set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal Topology
open MeasureTheory
open PidMgwBridgeContract
open PidPrefixProbabilityContract
open PidPrefixMgwBiasSource
open PidPrefixMgwGradientContract
universe u v w x
namespace PidPrefixMgwGradientCandidate

private lemma tangent_law_at {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) : Law (p t0) := by
  obtain ⟨U, _hU, ht, hall⟩ := hp.2.1
  exact (hall t0 ht).1

private lemma tangent_law_eventually {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) : ∀ᶠ t in 𝓝 t0, Law (p t) := by
  obtain ⟨U, hU, ht, hall⟩ := hp.2.1
  filter_upwards [hU.mem_nhds ht] with t htU
  exact (hall t htU).1

private lemma tangent_zero_off_support {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) (z : K) (hz : p t0 z = 0) :
    dp z = 0 := by
  have hb : |dp z| ≤ 0 := by simpa only [hz, mul_zero] using hp.2.2.2 z
  exact abs_eq_zero.mp (le_antisymm hb (abs_nonneg _))

private lemma tangent_score_weight {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) (z : K) :
    p t0 z * score (p t0) dp z = dp z := by
  classical
  by_cases hz : 0 < p t0 z
  · simp only [score, if_pos hz]
    field_simp
  · have hz0 : p t0 z = 0 :=
      le_antisymm (le_of_not_gt hz) ((tangent_law_at p dp t0 L hp).1 z)
    rw [tangent_zero_off_support p dp t0 L hp z hz0, hz0, zero_mul]

private lemma tangent_score_abs {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) (z : K) :
    |score (p t0) dp z| ≤ L := by
  classical
  by_cases hz : 0 < p t0 z
  · simp only [score, if_pos hz, abs_div, abs_of_pos hz]
    exact (div_le_iff₀ hz).2 (hp.2.2.2 z)
  · simpa only [score, if_neg hz, abs_zero] using hp.1

private lemma tangent_score_square {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) (z : K) :
    (score (p t0) dp z) ^ 2 ≤ L ^ 2 := by
  have hs := (sq_le_sq₀ (abs_nonneg (score (p t0) dp z)) hp.1).2
    (tangent_score_abs p dp t0 L hp z)
  simpa only [sq_abs] using hs

private lemma tangent_total_zero {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) : total dp = 0 := by
  classical
  have hd : HasDerivAt (fun t => ∑ z, p t z) (∑ z, dp z) t0 :=
    HasDerivAt.fun_sum (fun z _ => hp.2.2.1 z)
  have hc : HasDerivAt (fun t => ∑ z, p t z) 0 t0 := by
    apply (hasDerivAt_const t0 (1 : ℝ)).congr_of_eventuallyEq
    filter_upwards [tangent_law_eventually p dp t0 L hp] with t ht
    exact ht.2
  exact hd.unique hc

private lemma tangent_weighted_score_zero {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) :
    (∑ z, p t0 z * score (p t0) dp z) = 0 := by
  classical
  simp_rw [tangent_score_weight p dp t0 L hp]
  exact tangent_total_zero p dp t0 L hp

private lemma tangent_weighted_score_square {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) :
    (∑ z, p t0 z * (score (p t0) dp z) ^ 2) ≤ L ^ 2 := by
  classical
  have h0 := tangent_law_at p dp t0 L hp
  calc
    _ ≤ ∑ z, p t0 z * L ^ 2 := Finset.sum_le_sum (fun z _ =>
      mul_le_mul_of_nonneg_left (tangent_score_square p dp t0 L hp z) (h0.1 z))
    _ = (∑ z, p t0 z) * L ^ 2 := (Finset.sum_mul ..).symm
    _ = L ^ 2 := by rw [show (∑ z, p t0 z) = 1 from h0.2, one_mul]

private lemma finite_product_score_derivative {K : Type u} {R : Type v}
    [Fintype K] [DecidableEq R]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) (s : Finset R) (rows : R → K) :
    HasDerivAt (fun t => ∏ i ∈ s, p t (rows i))
      ((∏ i ∈ s, p t0 (rows i)) * ∑ i ∈ s, score (p t0) dp (rows i)) t0 := by
  classical
  have hd := HasDerivAt.fun_finsetProd
    (fun i (_hi : i ∈ s) => hp.2.2.1 (rows i))
  apply hd.congr_deriv
  simp only [smul_eq_mul, Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro i hi
  calc
    (∏ j ∈ s.erase i, p t0 (rows j)) * dp (rows i) =
        (p t0 (rows i) * ∏ j ∈ s.erase i, p t0 (rows j)) *
          score (p t0) dp (rows i) := by
      rw [← tangent_score_weight p dp t0 L hp (rows i)]
      ring
    _ = (∏ j ∈ s, p t0 (rows j)) * score (p t0) dp (rows i) := by
      rw [Finset.mul_prod_erase s (fun j => p t0 (rows j)) hi]

private lemma proof_finite_block_score_derivative :
    finite_block_score_derivative_target.{u, v, w} := by
  intro I X T _ _ _ _ _ _ _ p dp t0 L alpha h hp
  classical
  let : MeasurableSpace (Key I X T) := ⊤
  have h0 := tangent_law_at p dp t0 L hp
  have hbase := PidPrefixProbabilityCandidate.finite_law_measure I X T (p t0) h0
  have hprod := PidPrefixProbabilityCandidate.finite_product_law I X T (p t0) (h + 1) h0
  refine ⟨tangent_total_zero p dp t0 L hp, ?_, ?_⟩
  · rw [(hbase.2.2 (score (p t0) dp)).2]
    exact tangent_weighted_score_zero p dp t0 L hp
  · have hd : HasDerivAt
        (fun t => ∑ rows : Fin (h + 1) → Key I X T,
          (∏ i, p t (rows i)) * blockStatistic alpha h rows)
        (∑ rows : Fin (h + 1) → Key I X T,
          ((∏ i, p t0 (rows i)) * ∑ i, score (p t0) dp (rows i)) *
            blockStatistic alpha h rows) t0 := by
      exact HasDerivAt.fun_sum (fun rows _ =>
        (finite_product_score_derivative p dp t0 L hp Finset.univ rows).mul_const
          (blockStatistic alpha h rows))
    have he : (fun t => actualBlockMean (p t) alpha h) =ᶠ[𝓝 t0]
        (fun t => ∑ rows : Fin (h + 1) → Key I X T,
          (∏ i, p t (rows i)) * blockStatistic alpha h rows) := by
      filter_upwards [tangent_law_eventually p dp t0 L hp] with t ht
      exact (PidPrefixProbabilityCandidate.finite_product_law I X T (p t) (h + 1) ht).2.2
        (blockStatistic alpha h) |>.2
    apply (hd.congr_of_eventuallyEq he).congr_deriv
    rw [meanScoreGradient, (hprod.2.2 (scoreGradient (p t0) dp alpha h)).2]
    apply Finset.sum_congr rfl
    intro rows _
    simp only [scoreGradient, blockScore]
    ring

private lemma encoder_law {B : Type u} {D : Type v} {C : Type w}
    [Fintype B] [Fintype C] (base : B → ℝ) (input : B → D)
    (q : D → C → ℝ) (hb : Law base) (hq : ∀ d, Law (q d)) :
    Law (encoderMass base input q) := by
  classical
  refine ⟨fun z => mul_nonneg (hb.1 z.1) ((hq (input z.1)).1 z.2), ?_⟩
  change (∑ z : B × C, base z.1 * q (input z.1) z.2) = 1
  rw [Fintype.sum_prod_type]
  calc
    _ = ∑ b, base b * (∑ c, q (input b) c) := by
      apply Finset.sum_congr rfl
      intro b _
      exact (Finset.mul_sum Finset.univ (fun c : C => q (input b) c) (base b)).symm
    _ = ∑ b, base b := by
      apply Finset.sum_congr rfl
      intro b _
      rw [show (∑ c, q (input b) c) = 1 from (hq (input b)).2, mul_one]
    _ = 1 := hb.2

private lemma proof_finite_encoder_score :
    finite_encoder_score_target.{u, v, w} := by
  intro B D C _ _ _ base input q dq t0 L hb hq
  classical
  have hbpos : ∃ b, 0 < base b := by
    by_contra hn
    have hz : ∀ b, base b = 0 := by
      intro b
      exact le_antisymm (le_of_not_gt (fun h => hn ⟨b, h⟩)) (hb.1 b)
    have hzero : total base = 0 := by simp only [total, hz, Finset.sum_const_zero]
    have hone := hb.2
    linarith
  obtain ⟨b0, _hb0⟩ := hbpos
  have hL : 0 ≤ L := (hq (input b0)).1
  have hnear : ∀ᶠ t in 𝓝 t0, ∀ d,
      Law (q t d) ∧ ∀ c, (0 < q t d c ↔ 0 < q t0 d c) := by
    apply Filter.eventually_all.2
    intro d
    obtain ⟨U, hU, ht0, h⟩ := (hq d).2.1
    filter_upwards [hU.mem_nhds ht0] with t ht
    exact h t ht
  have hencnear : ∀ᶠ t in 𝓝 t0,
      Law (encoderMass base input (q t)) ∧
        ∀ z, (0 < encoderMass base input (q t) z ↔
          0 < encoderMass base input (q t0) z) := by
    filter_upwards [hnear] with t ht
    refine ⟨encoder_law base input (q t) hb (fun d => (ht d).1), ?_⟩
    intro z
    by_cases hbase : 0 < base z.1
    · simpa only [encoderMass, mul_pos_iff_of_pos_left hbase] using (ht (input z.1)).2 z.2
    · have hz : base z.1 = 0 := le_antisymm (le_of_not_gt hbase) (hb.1 z.1)
      simp only [encoderMass, hz, zero_mul]
  refine ⟨⟨hL, ?_, ?_, ?_⟩, ?_⟩
  · obtain ⟨U, hsub, hU, ht0⟩ := mem_nhds_iff.mp hencnear
    exact ⟨U, hU, ht0, fun t ht => hsub ht⟩
  · intro z
    exact ((hq (input z.1)).2.2.1 z.2).const_mul (base z.1)
  · intro z
    change |base z.1 * dq (input z.1) z.2| ≤ L * (base z.1 * q t0 (input z.1) z.2)
    rw [abs_mul, abs_of_nonneg (hb.1 z.1)]
    have h := mul_le_mul_of_nonneg_left ((hq (input z.1)).2.2.2 z.2) (hb.1 z.1)
    nlinarith only [h]
  · intro z hz
    have hbase : 0 < base z.1 := by
      by_contra hn
      have he : base z.1 = 0 := le_antisymm (le_of_not_gt hn) (hb.1 z.1)
      simp only [encoderMass, he, zero_mul, lt_self_iff_false] at hz
    have hqpos : 0 < q t0 (input z.1) z.2 :=
      (mul_pos_iff_of_pos_left hbase).mp hz
    rw [score, if_pos hz]
    change (base z.1 * dq (input z.1) z.2) /
      (base z.1 * q t0 (input z.1) z.2) = dq (input z.1) z.2 / q t0 (input z.1) z.2
    field_simp


/-
Unelaborated source fragment. Insert inside PidPrefixMgwGradientCandidate after
the tangent helpers of Candidate68525c. This file has no imports or public
exports and is not a standalone checked module. No new target is introduced.
-/

private lemma moment_iid_factor {K : Type u} {J : Type v}
    [Fintype K] [Fintype J] [DecidableEq J] (p : K → ℝ) (f : J → K → ℝ) :
    (∑ rows : J → K, (∏ i, p (rows i)) * ∏ i, f i (rows i)) =
      ∏ i, ∑ z, p z * f i z := by
  classical
  rw [Fintype.prod_sum]
  apply Finset.sum_congr rfl
  intro rows _
  exact (Finset.prod_mul_distrib).symm

private lemma moment_prod_selector {J : Type u} [Fintype J] [DecidableEq J]
    (r : J) (f : J → ℝ) :
    (∏ i, if i = r then f i else 1) = f r := by
  classical
  calc
    _ = (if r = r then f r else 1) := by
      apply Finset.prod_eq_single_of_mem r (Finset.mem_univ r)
      intro i _ hir
      exact if_neg hir
    _ = f r := if_pos rfl

private lemma moment_iid_one {K : Type u} {J : Type v}
    [Fintype K] [Fintype J] [DecidableEq J] (p : K → ℝ) (hp : (∑ z, p z) = 1)
    (r : J) (g : K → ℝ) :
    (∑ rows : J → K, (∏ i, p (rows i)) * g (rows r)) =
      ∑ z, p z * g z := by
  classical
  let f : J → K → ℝ := fun i z => if i = r then g z else 1
  have hpoint (rows : J → K) : (∏ i, f i (rows i)) = g (rows r) := by
    exact moment_prod_selector r (fun i => g (rows i))
  have hsingle (i : J) :
      (∑ z, p z * f i z) = if i = r then (∑ z, p z * g z) else 1 := by
    by_cases hir : i = r
    · simp only [f, if_pos hir]
    · simp only [f, if_neg hir, mul_one]
      exact hp
  calc
    _ = ∑ rows : J → K, (∏ i, p (rows i)) * ∏ i, f i (rows i) := by
      apply Finset.sum_congr rfl
      intro rows _
      rw [hpoint rows]
    _ = ∏ i, ∑ z, p z * f i z := moment_iid_factor p f
    _ = ∏ i, if i = r then (∑ z, p z * g z) else 1 := by
      apply Finset.prod_congr rfl
      intro i _
      exact hsingle i
    _ = ∑ z, p z * g z :=
      moment_prod_selector r (fun _ => ∑ z, p z * g z)

private lemma moment_iid_cross {K : Type u} {J : Type v}
    [Fintype K] [Fintype J] [DecidableEq J] (p s : K → ℝ)
    (hs : (∑ z, p z * s z) = 0) (r j : J) (hrj : r ≠ j) :
    (∑ rows : J → K,
      (∏ i, p (rows i)) * (s (rows r) * s (rows j))) = 0 := by
  classical
  let f : J → K → ℝ := fun i z =>
    (if i = r then s z else 1) * (if i = j then s z else 1)
  have hpoint (rows : J → K) :
      (∏ i, f i (rows i)) = s (rows r) * s (rows j) := by
    dsimp only [f]
    rw [Finset.prod_mul_distrib,
      moment_prod_selector r (fun i => s (rows i)),
      moment_prod_selector j (fun i => s (rows i))]
  have hzero : (∑ z, p z * f r z) = 0 := by
    simpa [f, hrj] using hs
  calc
    _ = ∑ rows : J → K, (∏ i, p (rows i)) * ∏ i, f i (rows i) := by
      apply Finset.sum_congr rfl
      intro rows _
      rw [hpoint rows]
    _ = ∏ i, ∑ z, p z * f i z := moment_iid_factor p f
    _ = 0 := Finset.prod_eq_zero (Finset.mem_univ r) hzero

private lemma moment_iid_pair {K : Type u} {J : Type v}
    [Fintype K] [Fintype J] [DecidableEq J] (p s : K → ℝ)
    (hp : (∑ z, p z) = 1) (hs : (∑ z, p z * s z) = 0) (r j : J) :
    (∑ rows : J → K,
      (∏ i, p (rows i)) * (s (rows r) * s (rows j))) =
      if r = j then (∑ z, p z * (s z) ^ 2) else 0 := by
  classical
  by_cases hrj : r = j
  · subst j
    rw [if_pos rfl]
    have hdiag := moment_iid_one p hp r (fun z => (s z) ^ 2)
    simpa only [pow_two] using hdiag
  · rw [if_neg hrj]
    exact moment_iid_cross p s hs r j hrj

private lemma moment_iid_score_square {K : Type u} {J : Type v}
    [Fintype K] [Fintype J] [DecidableEq J] (p s : K → ℝ)
    (hp : (∑ z, p z) = 1) (hs : (∑ z, p z * s z) = 0) :
    (∑ rows : J → K,
      (∏ i, p (rows i)) * (∑ i, s (rows i)) ^ 2) =
      (Fintype.card J : ℝ) * ∑ z, p z * (s z) ^ 2 := by
  classical
  have hexpand (rows : J → K) :
      (∑ i, s (rows i)) ^ 2 = ∑ r, ∑ j, s (rows r) * s (rows j) := by
    rw [pow_two, Finset.sum_mul]
    apply Finset.sum_congr rfl
    intro r _
    rw [Finset.mul_sum]
  have hinner (r : J) :
      (∑ j, if r = j then (∑ z, p z * (s z) ^ 2) else 0) =
        ∑ z, p z * (s z) ^ 2 := by
    calc
      _ = (if r = r then (∑ z, p z * (s z) ^ 2) else 0) := by
        apply Finset.sum_eq_single_of_mem r (Finset.mem_univ r)
        intro j _ hjr
        exact if_neg (Ne.symm hjr)
      _ = ∑ z, p z * (s z) ^ 2 := if_pos rfl
  calc
    _ = ∑ rows : J → K, ∑ r, ∑ j,
        (∏ i, p (rows i)) * (s (rows r) * s (rows j)) := by
      apply Finset.sum_congr rfl
      intro rows _
      rw [hexpand rows]
      simp_rw [Finset.mul_sum]
    _ = ∑ r, ∑ j, ∑ rows : J → K,
        (∏ i, p (rows i)) * (s (rows r) * s (rows j)) := by
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro r _
      rw [Finset.sum_comm]
    _ = ∑ r, ∑ j, if r = j then (∑ z, p z * (s z) ^ 2) else 0 := by
      apply Finset.sum_congr rfl
      intro r _
      apply Finset.sum_congr rfl
      intro j _
      exact moment_iid_pair p s hp hs r j
    _ = (Fintype.card J : ℝ) * ∑ z, p z * (s z) ^ 2 := by
      simp_rw [hinner]
      simp only [Finset.sum_const, Finset.card_univ, nsmul_eq_mul]

private lemma moment_weighted_statistic {K : Type u} {J : Type v}
    [Fintype K] [Fintype J] [DecidableEq J] (p s : K → ℝ)
    (hp : ∀ z, 0 ≤ p z) (htotal : (∑ z, p z) = 1)
    (hs : (∑ z, p z * s z) = 0) (g : (J → K) → ℝ) (H : ℝ)
    (hH : 0 ≤ H) (hg : ∀ rows, |g rows| ≤ H) :
    (∑ rows : J → K,
      (∏ i, p (rows i)) * (g rows * ∑ i, s (rows i)) ^ 2) ≤
      (Fintype.card J : ℝ) * H ^ 2 * ∑ z, p z * (s z) ^ 2 := by
  classical
  have hpoint (rows : J → K) :
      (g rows * ∑ i, s (rows i)) ^ 2 ≤ H ^ 2 * (∑ i, s (rows i)) ^ 2 := by
    have hg2 : (g rows) ^ 2 ≤ H ^ 2 := by
      simpa only [sq_abs] using (sq_le_sq₀ (abs_nonneg (g rows)) hH).2 (hg rows)
    simpa only [mul_pow] using
      mul_le_mul_of_nonneg_right hg2 (sq_nonneg (∑ i, s (rows i)))
  calc
    _ ≤ ∑ rows : J → K,
        (∏ i, p (rows i)) * (H ^ 2 * (∑ i, s (rows i)) ^ 2) := by
      apply Finset.sum_le_sum
      intro rows _
      exact mul_le_mul_of_nonneg_left (hpoint rows)
        (Finset.prod_nonneg (fun i _ => hp (rows i)))
    _ = H ^ 2 * (∑ rows : J → K,
        (∏ i, p (rows i)) * (∑ i, s (rows i)) ^ 2) := by
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro rows _
      ring
    _ = (Fintype.card J : ℝ) * H ^ 2 * ∑ z, p z * (s z) ^ 2 := by
      rw [moment_iid_score_square p s htotal hs]
      ring

private lemma moment_harmonic_nonneg (h : ℕ) : 0 ≤ harmonic h := by
  unfold harmonic
  apply Finset.sum_nonneg
  intro i _
  positivity

private lemma proof_score_second_moment : score_second_moment_target.{u, v, w} := by
  intro I X T _ _ _ _ _ _ _ p dp t0 L alpha h hp
  classical
  let : MeasurableSpace (Key I X T) := ⊤
  have h0 := tangent_law_at p dp t0 L hp
  have hbase := PidPrefixProbabilityCandidate.finite_law_measure I X T (p t0) h0
  have hprod := PidPrefixProbabilityCandidate.finite_product_law I X T (p t0) (h + 1) h0
  have ib := hbase.2.2 (fun z => (score (p t0) dp z) ^ 2)
  have ig := hprod.2.2 (fun rows => (scoreGradient (p t0) dp alpha h rows) ^ 2)
  refine ⟨ig.1, ib.1, ?_, ?_⟩
  · rw [ig.2, ib.2]
    have hg (rows : Fin (h + 1) → Key I X T) :
        |blockStatistic alpha h rows| ≤ harmonic h :=
      abs_le.mpr (PidPrefixProbabilityCandidate.block_range I X T alpha h rows)
    have hb := moment_weighted_statistic (p t0) (score (p t0) dp) h0.1
      (show (∑ z, p t0 z) = 1 from h0.2)
      (tangent_weighted_score_zero p dp t0 L hp)
      (blockStatistic alpha h) (harmonic h) (moment_harmonic_nonneg h) hg
    simpa only [scoreGradient, blockScore, Fintype.card_fin, Nat.cast_add, Nat.cast_one]
      using hb
  · rw [ib.2]
    exact tangent_weighted_score_square p dp t0 L hp

/- The following generic finite-measure helper rederives the small public-library
   argument used inside the accepted probability source. It calls no imported
   private declaration. -/
private lemma moment_weighted_integral {K : Type u} [Fintype K] [MeasurableSpace K]
    [MeasurableSingletonClass K] (p : K → ℝ) (hp : ∀ z, 0 ≤ p z) (f : K → ℝ) :
    Integrable f (∑ z, ENNReal.ofReal (p z) • Measure.dirac z) ∧
      (∫ z, f z ∂(∑ z, ENNReal.ofReal (p z) • Measure.dirac z)) =
        ∑ z, p z * f z := by
  classical
  have hi : ∀ z : K, Integrable f (ENNReal.ofReal (p z) • Measure.dirac z) := by
    intro z
    exact (integrable_dirac (by simp)).smul_measure ENNReal.ofReal_ne_top
  refine ⟨integrable_finsetSum_measure.mpr (fun z _ => hi z), ?_⟩
  rw [integral_finsetSum_measure (fun z _ => hi z)]
  apply Finset.sum_congr rfl
  intro z _
  simp [ENNReal.toReal_ofReal (hp z)]

private lemma moment_latent_law_measure {K : Type u} [Fintype K] [DecidableEq K]
    (p : K → ℝ) (hp : Law p) :
    let : MeasurableSpace K := ⊤;
    IsProbabilityMeasure (latentMeasure p) ∧
      (∀ z, latentMeasure p {z} = ENNReal.ofReal (p z)) ∧
      ∀ f : K → ℝ, Integrable f (latentMeasure p) ∧
        (∫ z, f z ∂latentMeasure p) = ∑ z, p z * f z := by
  classical
  let : MeasurableSpace K := ⊤
  have hprob : IsProbabilityMeasure (latentMeasure p) := by
    constructor
    simp only [latentMeasure, Measure.finsetSum_apply, Measure.smul_apply,
      Measure.dirac_apply_of_mem (Set.mem_univ _), smul_eq_mul, mul_one]
    rw [← ENNReal.ofReal_sum_of_nonneg (fun z _ => hp.1 z)]
    change ENNReal.ofReal (total p) = 1
    rw [hp.2, ENNReal.ofReal_one]
  refine ⟨hprob, ?_, ?_⟩
  · intro z
    change (∑ a, ENNReal.ofReal (p a) • Measure.dirac a) {z} = ENNReal.ofReal (p z)
    rw [← Measure.sum_fintype]
    exact Measure.sum_smul_dirac_singleton
  · intro f
    exact moment_weighted_integral p hp.1 f

private lemma moment_latent_product_law {K : Type u} [Fintype K] [DecidableEq K]
    (p : K → ℝ) (count : ℕ) (hp : Law p) :
    let : MeasurableSpace K := ⊤;
    IsProbabilityMeasure (latentRowLaw p count) ∧
      (∀ rows, latentRowLaw p count {rows} = ENNReal.ofReal (∏ i, p (rows i))) ∧
      ∀ f : (Fin count → K) → ℝ, Integrable f (latentRowLaw p count) ∧
        (∫ rows, f rows ∂latentRowLaw p count) =
          ∑ rows, (∏ i, p (rows i)) * f rows := by
  classical
  let : MeasurableSpace K := ⊤
  have base := moment_latent_law_measure p hp
  let : IsProbabilityMeasure (latentMeasure p) := base.1
  have hprob : IsProbabilityMeasure (latentRowLaw p count) := by
    unfold latentRowLaw
    infer_instance
  have hs : ∀ rows, latentRowLaw p count {rows} =
      ENNReal.ofReal (∏ i, p (rows i)) := by
    intro rows
    rw [latentRowLaw, Measure.pi_singleton]
    simp only [base.2.1]
    exact (ENNReal.ofReal_prod_of_nonneg (fun i _ => hp.1 (rows i))).symm
  refine ⟨hprob, hs, ?_⟩
  intro f
  have hm : latentRowLaw p count =
      ∑ rows, ENNReal.ofReal (∏ i, p (rows i)) • Measure.dirac rows := by
    conv_lhs => rw [← Measure.sum_smul_dirac (latentRowLaw p count), Measure.sum_fintype]
    simp only [hs]
  rw [hm]
  exact moment_weighted_integral _ (fun rows =>
    Finset.prod_nonneg (fun i _ => hp.1 (rows i))) f

private lemma proof_latent_score_second_moment :
    latent_score_second_moment_target.{u, v, w, x} := by
  intro I X T W _ _ _ _ _ _ _ _ _ rho drho t0 L phi alpha h hp
  classical
  let : MeasurableSpace W := ⊤
  have h0 := tangent_law_at rho drho t0 L hp
  have hbase := moment_latent_law_measure (rho t0) h0
  have hprod := moment_latent_product_law (rho t0) (h + 1) h0
  have ib := hbase.2.2 (fun z => (score (rho t0) drho z) ^ 2)
  have ig := hprod.2.2 (fun rows => (latentScoreGradient (rho t0) drho phi alpha h rows) ^ 2)
  refine ⟨ig.1, ib.1, ?_, ?_⟩
  · rw [ig.2, ib.2]
    have hg (rows : Fin (h + 1) → W) :
        |blockStatistic alpha h (mapBlock phi (h + 1) rows)| ≤ harmonic h :=
      abs_le.mpr (PidPrefixProbabilityCandidate.block_range I X T alpha h
        (mapBlock phi (h + 1) rows))
    have hb := moment_weighted_statistic (rho t0) (score (rho t0) drho) h0.1
      (show (∑ z, rho t0 z) = 1 from h0.2)
      (tangent_weighted_score_zero rho drho t0 L hp)
      (fun rows => blockStatistic alpha h (mapBlock phi (h + 1) rows))
      (harmonic h) (moment_harmonic_nonneg h) hg
    simpa only [latentScoreGradient, Fintype.card_fin, Nat.cast_add, Nat.cast_one]
      using hb
  · rw [ib.2]
    exact tangent_weighted_score_square rho drho t0 L hp

/-
Unelaborated private source fragment for the unchanged full_inverse_row_target.
Insert inside PidPrefixMgwGradientCandidate; the existing Contract import and
BigOperators scope suffice. No earlier Candidate helper is required.
-/

private lemma invrow_generic_exists {L : Type u} [Fintype L] [PartialOrder L]
    [DecidableLE L] (alpha : L) :
    ∃ c : L → ℝ,
      (∀ beta, ¬ beta ≤ alpha → c beta = 0) ∧
      ∀ f : L → ℝ,
        (∑ beta, c beta * PidJoinLogContract.cumulative f beta) = f alpha := by
  classical
  let step : ∀ delta : L, (∀ beta : L, delta < beta → ℝ) → ℝ :=
    fun delta ih => (if delta = alpha then 1 else 0) -
      ∑ beta, if h : delta < beta then ih beta h else 0
  let c : L → ℝ := WellFoundedGT.fix (motive := fun _ : L => ℝ) step
  have hc (delta : L) : c delta = (if delta = alpha then 1 else 0) -
      ∑ beta, if delta < beta then c beta else 0 := by
    calc
      c delta = step delta (fun beta _ => c beta) :=
        WellFoundedGT.fix_eq step delta
      _ = (if delta = alpha then 1 else 0) -
          ∑ beta, if delta < beta then c beta else 0 :=
        congrArg (fun q : ℝ => (if delta = alpha then 1 else 0) - q)
          (Finset.sum_congr rfl (fun beta _ => by
            by_cases h : delta < beta <;> simp [h]))
  have hsupport : ∀ delta, ¬ delta ≤ alpha → c delta = 0 := by
    intro delta
    induction delta using WellFoundedGT.induction with
    | ind delta ih =>
      intro hnot
      have hne : delta ≠ alpha := fun heq => hnot (le_of_eq heq)
      have hzero : (∑ beta, if delta < beta then c beta else 0) = 0 := by
        apply Finset.sum_eq_zero
        intro beta _
        by_cases hlt : delta < beta
        · rw [if_pos hlt]
          exact ih beta hlt (fun hba => hnot (le_trans (le_of_lt hlt) hba))
        · exact if_neg hlt
      rw [hc delta, if_neg hne, hzero, sub_zero]
  have hupper (delta : L) :
      (∑ beta, if delta ≤ beta then c beta else 0) =
        if delta = alpha then 1 else 0 := by
    have hstrict (beta : L) (hne : beta ≠ delta) :
        (if delta ≤ beta then c beta else 0) =
          if delta < beta then c beta else 0 := by
      by_cases hle : delta ≤ beta
      · have hlt : delta < beta := lt_of_le_of_ne hle (Ne.symm hne)
        simp only [if_pos hle, if_pos hlt]
      · have hnlt : ¬ delta < beta := fun hlt => hle (le_of_lt hlt)
        simp only [if_neg hle, if_neg hnlt]
    have hrest :
        (∑ beta ∈ Finset.univ.erase delta, if delta ≤ beta then c beta else 0) =
          ∑ beta, if delta < beta then c beta else 0 := by
      calc
        _ = ∑ beta ∈ Finset.univ.erase delta,
            if delta < beta then c beta else 0 := by
          apply Finset.sum_congr rfl
          intro beta hbeta
          exact hstrict beta (Finset.ne_of_mem_erase hbeta)
        _ = ∑ beta, if delta < beta then c beta else 0 := by
          simpa only [if_neg (lt_irrefl delta), add_zero] using
            (Finset.sum_erase_add Finset.univ
              (fun beta => if delta < beta then c beta else 0) (Finset.mem_univ delta))
    calc
      _ = (∑ beta ∈ Finset.univ.erase delta,
          if delta ≤ beta then c beta else 0) + c delta := by
        rw [← Finset.sum_erase_add Finset.univ
          (fun beta => if delta ≤ beta then c beta else 0) (Finset.mem_univ delta)]
        simp only [le_refl, ite_true]
      _ = (∑ beta, if delta < beta then c beta else 0) + c delta := by rw [hrest]
      _ = if delta = alpha then 1 else 0 := by
        rw [hc delta]
        ring
  refine ⟨c, hsupport, ?_⟩
  intro f
  unfold PidJoinLogContract.cumulative
  simp_rw [Finset.mul_sum]
  rw [Finset.sum_comm]
  calc
    _ = ∑ delta, f delta * (∑ beta, if delta ≤ beta then c beta else 0) := by
      apply Finset.sum_congr rfl
      intro delta _
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro beta _
      by_cases h : delta ≤ beta <;> simp [h, mul_comm]
    _ = ∑ delta, f delta * (if delta = alpha then 1 else 0) := by
      simp_rw [hupper]
    _ = f alpha := by
      rw [Finset.sum_eq_single alpha]
      · simp
      · intro delta _ hne
        simp only [if_neg hne, mul_zero]
      · simp

private lemma invrow_coordinate_cumulative {L : Type u} [Fintype L] [PartialOrder L]
    [DecidableLE L] [DecidableEq L] (x a : L) :
    PidJoinLogContract.cumulative (fun y => if y = x then 1 else 0) a =
      if x ≤ a then 1 else 0 := by
  classical
  unfold PidJoinLogContract.cumulative
  rw [Finset.sum_eq_single x]
  · by_cases h : x ≤ a <;> simp [h]
  · intro y _ hne
    by_cases h : y ≤ a <;> simp [h, hne]
  · simp

private lemma invrow_generic_unique {L : Type u} [Fintype L] [PartialOrder L]
    [DecidableLE L] (alpha : L) (c d : L → ℝ)
    (hc : ∀ f : L → ℝ,
      (∑ beta, c beta * PidJoinLogContract.cumulative f beta) = f alpha)
    (hd : ∀ f : L → ℝ,
      (∑ beta, d beta * PidJoinLogContract.cumulative f beta) = f alpha) :
    c = d := by
  classical
  funext x
  induction x using WellFoundedGT.induction with
  | ind x ih =>
    have hu : (∑ beta, (c beta - d beta) *
        PidJoinLogContract.cumulative (fun y => if y = x then 1 else 0) beta) = 0 := by
      simp_rw [sub_mul, Finset.sum_sub_distrib, hc, hd, sub_self]
    have he : (∑ beta, (c beta - d beta) *
        PidJoinLogContract.cumulative (fun y => if y = x then 1 else 0) beta) =
        c x - d x := by
      rw [Finset.sum_eq_single x]
      · simp [invrow_coordinate_cumulative]
      · intro beta _ hne
        rw [invrow_coordinate_cumulative]
        by_cases hle : x ≤ beta
        · rw [if_pos hle, ih beta (lt_of_le_of_ne hle (Ne.symm hne)), sub_self, zero_mul]
        · rw [if_neg hle, mul_zero]
      · simp
    rw [he] at hu
    exact sub_eq_zero.mp hu

/- Reprove the native/generic equality from ExactOps. No imported private
   cumulative-model helper is referenced. The Fintype and LE arguments are
   explicit so the ambient subtype inclusion order cannot be substituted. -/
private lemma invrow_native_cumulative {I : Type u} [Fintype I] [DecidableEq I]
    (sigma : SemilatticeSup (Node I)) (hsigma : ExactOps sigma)
    (f : Node I → ℝ) (alpha : Node I) :
    PidMgwBridgeContract.cumulative f alpha =
      @PidJoinLogContract.cumulative (Node I) (nodeFintype I)
        sigma.toLE (Classical.decRel sigma.le) f alpha := by
  classical
  unfold PidMgwBridgeContract.cumulative PidJoinLogContract.cumulative
  apply Finset.sum_congr rfl
  intro beta _
  simp only [hsigma.1 beta alpha]

private lemma invrow_proof_full_inverse_row : full_inverse_row_target.{u} := by
  intro I _ _ _ alpha
  classical
  obtain ⟨sigma, hsigma⟩ := (PidMgwBridgeCandidate.actual_join_lub I).2
  let : Fintype (Node I) := nodeFintype I
  obtain ⟨c, hsupport, hinverse⟩ :=
    @invrow_generic_exists (Node I) (nodeFintype I) sigma.toPartialOrder
      (Classical.decRel sigma.le) alpha
  refine ⟨c, ?_, ?_⟩
  · constructor
    · intro beta hraw
      exact hsupport beta (fun hle => hraw ((hsigma.1 beta alpha).1 hle))
    · intro f
      calc
        (∑ beta, c beta * PidMgwBridgeContract.cumulative f beta) =
            ∑ beta, c beta * @PidJoinLogContract.cumulative (Node I) (nodeFintype I)
              sigma.toLE (Classical.decRel sigma.le) f beta := by
          apply Finset.sum_congr rfl
          intro beta _
          rw [invrow_native_cumulative sigma hsigma f beta]
        _ = f alpha := hinverse f
  · intro d hd
    have hdgeneric : ∀ f : Node I → ℝ,
        (∑ beta, d beta * @PidJoinLogContract.cumulative (Node I) (nodeFintype I)
          sigma.toLE (Classical.decRel sigma.le) f beta) = f alpha := by
      intro f
      calc
        (∑ beta, d beta * @PidJoinLogContract.cumulative (Node I) (nodeFintype I)
          sigma.toLE (Classical.decRel sigma.le) f beta) =
            ∑ beta, d beta * PidMgwBridgeContract.cumulative f beta := by
          apply Finset.sum_congr rfl
          intro beta _
          rw [invrow_native_cumulative sigma hsigma f beta]
        _ = f alpha := hd.2 f
    exact @invrow_generic_unique (Node I) (nodeFintype I) sigma.toPartialOrder
      (Classical.decRel sigma.le) alpha d c hdgeneric hinverse

private lemma scalarFrag_shifted_hasSum (f : ℕ → ℝ) (s : ℝ) (hf : HasSum f s) (h : ℕ) :
    HasSum (fun n => f (n + h)) (s - ∑ n ∈ Finset.range h, f n) := by
  have ht := (summable_nat_add_iff h).mpr hf.summable
  have he := hf.summable.sum_add_tsum_nat_add h
  rw [hf.tsum_eq] at he
  have hv : s - ∑ n ∈ Finset.range h, f n = ∑' n : ℕ, f (n + h) := by linarith
  rw [hv]
  exact ht.hasSum

private lemma scalarFrag_log_hasSum (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1) :
    HasSum (fun n : ℕ => (1 - q) ^ (n + 1) / ((n : ℝ) + 1)) (-Real.log q) := by
  have hsmall : |1 - q| < 1 := by
    rw [abs_of_nonneg (sub_nonneg.mpr hq1)]
    linarith
  simpa only [show 1 - (1 - q) = q by ring] using
    Real.hasSum_pow_div_log_of_abs_lt_one hsmall

private lemma scalarFrag_remainder_hasSum (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1) (h : ℕ) :
    HasSum (fun n : ℕ =>
      (1 - q) ^ (n + h + 1) / (((n + h : ℕ) : ℝ) + 1)) (logRemainder q h) := by
  exact scalarFrag_shifted_hasSum _ _ (scalarFrag_log_hasSum q hq hq1) h

private lemma scalarFrag_geometric_tail_hasSum (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1) (h : ℕ) :
    HasSum (fun n : ℕ => (1 - q) ^ (n + h + 1)) ((1 - q) ^ (h + 1) / q) := by
  have hg := (hasSum_geometric_of_lt_one (sub_nonneg.mpr hq1)
    (show 1 - q < 1 by linarith)).mul_left ((1 - q) ^ (h + 1))
  rw [show 1 - (1 - q) = q by ring] at hg
  simpa only [div_eq_mul_inv] using hg.congr_fun (fun n => by
    rw [show n + h + 1 = (h + 1) + n by omega, pow_add])

private lemma scalarFrag_remainder_difference (q v : ℝ) (hq : 0 < q) (hqv : q ≤ v)
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
      (scalarFrag_remainder_hasSum q hq hq1 h).sub (scalarFrag_remainder_hasSum v hv hv1 h)
  have hg := (scalarFrag_geometric_tail_hasSum q hq hq1 h).sub
    (scalarFrag_geometric_tail_hasSum v hv hv1 h)
  have hb : logRemainder q h - logRemainder v h ≤
      ((1 - q) ^ (h + 1) / q - (1 - v) ^ (h + 1) / v) / ((h : ℝ) + 1) := by
    apply hasSum_le _ hr (hg.div_const ((h : ℝ) + 1))
    intro n
    apply div_le_div_of_nonneg_left (hp _) (by positivity)
    push_cast
    linarith [show (0 : ℝ) ≤ n by positivity]
  have hfull := (scalarFrag_geometric_tail_hasSum q hq hq1 0).sub
    (scalarFrag_geometric_tail_hasSum v hv hv1 0)
  have ht := scalarFrag_shifted_hasSum _ _ hfull h
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

private lemma scalarFrag_remainder_succ (q : ℝ) (h : ℕ) :
    logRemainder q (h + 1) = logRemainder q h -
      (1 - q) ^ (h + 1) / ((h : ℝ) + 1) := by
  simp only [logRemainder, Finset.sum_range_succ]
  ring

private lemma scalarFrag_remainder_derivative (q : ℝ) (hq : 0 < q) (h : ℕ) :
    HasDerivAt (fun r : ℝ => logRemainder r h) (-((1 - q) ^ h) / q) q := by
  induction h with
  | zero =>
      simpa [logRemainder, div_eq_mul_inv] using! (Real.hasDerivAt_log (ne_of_gt hq)).neg
  | succ h ih =>
      have hn : 0 < (h : ℝ) + 1 := by positivity
      have hraw : HasDerivAt
          (fun r : ℝ => (1 - r) ^ (h + 1) / ((h : ℝ) + 1))
          ((((h + 1 : ℕ) : ℝ) * (1 - q) ^ ((h + 1) - 1) * (-1)) /
            ((h : ℝ) + 1)) q :=
        (((hasDerivAt_id q).const_sub (1 : ℝ)).pow (h + 1)).div_const ((h : ℝ) + 1)
      have hc :
          (((h + 1 : ℕ) : ℝ) * (1 - q) ^ ((h + 1) - 1) * (-1)) /
            ((h : ℝ) + 1) = -((1 - q) ^ h) := by
        simp only [Nat.add_sub_cancel, Nat.cast_add, Nat.cast_one]
        field_simp [ne_of_gt hn]
      rw [hc] at hraw
      have hd := ih.sub hraw
      have he : -((1 - q) ^ h) / q - -((1 - q) ^ h) =
          -((1 - q) ^ (h + 1)) / q := by
        rw [pow_succ]
        field_simp [ne_of_gt hq]; ring
      rw [he] at hd
      simpa only [scalarFrag_remainder_succ] using! hd

private lemma scalarFrag_power_envelope (q : ℝ) (hq : 0 ≤ q) (hq1 : q ≤ 1)
    (h : ℕ) : ((h : ℝ) + 1) * q * (1 - q) ^ h ≤ 1 := by
  have hx0 : 0 ≤ 1 - q := sub_nonneg.mpr hq1
  have hx1 : 1 - q ≤ 1 := by linarith
  have hsum : ((h : ℝ) + 1) * (1 - q) ^ h ≤
      ∑ i ∈ Finset.range (h + 1), (1 - q) ^ i := by
    calc
      _ = ∑ _i ∈ Finset.range (h + 1), (1 - q) ^ h := by
        simp only [Finset.sum_const, Finset.card_range, nsmul_eq_mul,
          Nat.cast_add, Nat.cast_one]
      _ ≤ _ := Finset.sum_le_sum (fun i hi =>
        pow_le_pow_of_le_one hx0 hx1 (Nat.le_of_lt_succ (Finset.mem_range.mp hi)))
  have hgeom : (∑ i ∈ Finset.range (h + 1), (1 - q) ^ i) * q =
      1 - (1 - q) ^ (h + 1) := by
    simpa only [show 1 - (1 - q) = q by ring] using geom_sum_mul_neg (1 - q) (h + 1)
  calc
    ((h : ℝ) + 1) * q * (1 - q) ^ h =
        (((h : ℝ) + 1) * (1 - q) ^ h) * q := by ring
    _ ≤ (∑ i ∈ Finset.range (h + 1), (1 - q) ^ i) * q :=
      mul_le_mul_of_nonneg_right hsum hq
    _ = 1 - (1 - q) ^ (h + 1) := hgeom
    _ ≤ 1 := sub_le_self 1 (pow_nonneg hx0 _)

private theorem proof_scalar_remainder_calculus : scalar_remainder_calculus_target := by
  refine ⟨?_, ?_, ?_⟩
  · intro q hq h
    exact scalarFrag_remainder_derivative q hq h
  · intro q a hq hqa ha1 h
    have hd := scalarFrag_remainder_difference q a hq hqa ha1 h
    exact ⟨hd.1, hd.2.2⟩
  · intro q hq hq1 h
    exact scalarFrag_power_envelope q hq hq1 h



/-! Unelaborated private insertable source for frozen targets 3 and 4.
Finite algebra reconstructed locally from the accepted Mean/Bias source;
all imported theorem calls use public exports. No import or namespace wrapper. -/

private lemma corrFrag_choose_div (n k : ℕ) :
    (Nat.choose n k : ℝ) / ((k : ℝ) + 1) =
      (Nat.choose (n + 1) (k + 1) : ℝ) / ((n : ℝ) + 1) := by
  apply (div_eq_div_iff (by positivity) (by positivity)).2
  have h : ((n : ℝ) + 1) * (Nat.choose n k : ℝ) =
      (Nat.choose (n + 1) (k + 1) : ℝ) * ((k : ℝ) + 1) := by
    exact_mod_cast Nat.add_one_mul_choose_eq n k
  nlinarith [h]

private lemma corrFrag_binomial_cancel (b w : ℝ) (n : ℕ) :
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
            (w ^ (k + 1) * b ^ (n - k)) := by rw [corrFrag_choose_div]
        _ = _ := by ring
    _ = _ := by
      congr 1
      linarith [hbin]

private lemma corrFrag_binomial_thinning (q v : ℝ) (hv : v ≠ 0) (n : ℕ) :
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
        ((n : ℝ) + 1) := corrFrag_binomial_cancel (1 - v) (v - q) n
    _ = _ := by rw [show (v - q) + (1 - v) = 1 - q by ring]



private lemma corrFrag_cumulative_model {I : Type u} [Fintype I] [DecidableEq I]
    (sigma : SemilatticeSup (Node I)) (hsigma : ExactOps sigma)
    (r : Node I → ℝ) (a : Node I) :
    cumulative r a = @PidJoinLogContract.cumulative (Node I) (nodeFintype I)
      sigma.toLE (Classical.decRel sigma.le) r a := by
  classical
  unfold cumulative PidJoinLogContract.cumulative
  apply Finset.sum_congr rfl
  intro x _hx
  simp only [hsigma.1 x a]


private lemma corrFrag_power_cumulative {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] (weight : L → ℝ) (n : ℕ) (a : L) :
    PidJoinLogContract.cumulative (PidJoinLogContract.joinPower weight n) a =
      PidJoinLogContract.cumulative weight a ^ (n + 1) := by
  induction n with
  | zero => simp [PidJoinLogContract.joinPower]
  | succ n ih =>
    rw [PidJoinLogContract.joinPower, PidJoinLogCandidate.join_convolution_cumulative L, ih]
    simp only [pow_succ]

private lemma corrFrag_word_cumulative
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
  rw [heq, corrFrag_cumulative_model sigma hsigma]
  rw [@corrFrag_power_cumulative (Node I) (nodeFintype I) sigma
    (Classical.decEq (Node I)) (Classical.decRel sigma.le) (weights r z) n a]
  rw [← corrFrag_cumulative_model sigma hsigma]

private lemma corrFrag_cumulative_div {I : Type u} [Fintype I]
    (r : Node I → ℝ) (c : ℝ) (a : Node I) :
    cumulative (fun b => r b / c) a = cumulative r a / c := by
  classical
  unfold cumulative
  rw [Finset.sum_div]
  apply Finset.sum_congr rfl
  intro b _hb
  by_cases hba : rawLE b.val a.val <;> simp [hba]

private lemma corrFrag_cumulative_combination {I : Type u} {A : Type v} [Fintype I]
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

private lemma corrFrag_positive_cumulative
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
  rw [heq, corrFrag_cumulative_div, corrFrag_word_cumulative hword]
  rw [PidMgwBridgeCandidate.generator_lower_cumulative I X T p z a, hp.2]

private lemma corrFrag_negative_cumulative
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
  rw [heq, corrFrag_cumulative_combination]
  calc
    _ = ∑ k ∈ Finset.range (n + 1),
        (Nat.choose n k : ℝ) * (targetMass p z) ^ (k + 1) *
          (1 - targetMass p z) ^ (n - k) *
            (1 - restrictedMass p z a / targetMass p z) ^ (k + 1) /
              ((k : ℝ) + 1) := by
      apply Finset.sum_congr rfl
      intro k _hk
      rw [corrFrag_word_cumulative hword, hcw]
      ring
    _ = _ := corrFrag_binomial_thinning (restrictedMass p z a) (targetMass p z) (ne_of_gt hv) n

private lemma corrFrag_proof_native_cumulative_increments :
    native_cumulative_increments_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p z alpha n hp hz
  exact ⟨corrFrag_positive_cumulative
    PidPrefixMgwMeanCandidate.word_coefficient_join_power p z hp n alpha,
    corrFrag_negative_cumulative
      PidPrefixMgwMeanCandidate.word_coefficient_join_power p z hp hz n alpha⟩

private lemma corrFrag_cumulative_sub {I : Type u} [Fintype I]
    (f g : Node I → ℝ) (a : Node I) :
    cumulative (fun b => f b - g b) a = cumulative f a - cumulative g a := by
  classical
  unfold cumulative
  rw [← Finset.sum_sub_distrib]
  apply Finset.sum_congr rfl
  intro b _hb
  by_cases hba : rawLE b.val a.val <;> simp [hba]

private lemma corrFrag_cumulative_sum {I : Type u} {A : Type v} [Fintype I]
    (s : Finset A) (f : A → Node I → ℝ) (a : Node I) :
    cumulative (fun b => ∑ k ∈ s, f k b) a = ∑ k ∈ s, cumulative (f k) a := by
  simpa only [one_mul] using
    corrFrag_cumulative_combination s (fun _ => (1 : ℝ)) f a

private lemma corrFrag_supported_remainder
    {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (z : Key I X T) (plus minus : Node I → ℝ)
    (hp : Law p) (hz : 0 < p z) (hplus : InfInverse p z plus)
    (hminus : MisInverse p z minus) (a : Node I) (h : ℕ) :
    cumulative (fun b => plus b - minus b -
      ∑ n ∈ Finset.range h,
        ((∫ rows, positiveOnPrefix z b (List.ofFn rows) ∂rowLaw p (n + 1)) -
          (∫ rows, negativeOnPrefix z b (List.ofFn rows) ∂rowLaw p (n + 1)))) a =
      logRemainder (sourceMass p z a) h - logRemainder (restrictedMass p z a) h +
        logRemainder (targetMass p z) h := by
  classical
  rcases PidMgwBridgeCandidate.supported_anchor_domains I X T p z hp hz with
    ⟨_hfull, _hfull1, hv, _hv1, _hcondz, _hcondpos, _ht, _ht0, _ht1,
      _hct, _hct0, _hct1, hlocal⟩
  have hqv := (hlocal a).2.2.1
  have hq : 0 < restrictedMass p z a :=
    ((div_pos_iff.mp hqv).resolve_right
      (fun hn => (not_lt_of_ge hv.le) hn.2)).1
  rw [corrFrag_cumulative_sub, corrFrag_cumulative_sub, hplus a, hminus a,
    corrFrag_cumulative_sum]
  have hinc (n : ℕ) := corrFrag_proof_native_cumulative_increments
    I X T p z a n hp hz
  have hpos (n : ℕ) := (hinc n).1
  have hneg (n : ℕ) := (hinc n).2
  simp_rw [corrFrag_cumulative_sub, hpos, hneg]
  rw [Real.log_div (ne_of_gt hv) (ne_of_gt hq)]
  simp only [logRemainder, sub_div, Finset.sum_sub_distrib]
  ring

private lemma corrFrag_proof_actual_atom_remainder :
    actual_atom_remainder_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p plus minus alpha h hp hpair
  classical
  let : Fintype (Node I) := nodeFintype I
  have hactual (b : Node I) : actualBlockMean p b h =
      ∑ z, p z * ∑ n ∈ Finset.range h,
        ((∫ rows, positiveOnPrefix z b (List.ofFn rows) ∂rowLaw p (n + 1)) -
          (∫ rows, negativeOnPrefix z b (List.ofFn rows) ∂rowLaw p (n + 1))) := by
    exact (PidPrefixMgwMeanCandidate.finite_block_expectation I X T p b h hp).2.2.1
  have hdiff : (fun b => jointAtomMean p plus minus b - actualBlockMean p b h) =
      (fun b => ∑ z, p z * (plus z b - minus z b -
        ∑ n ∈ Finset.range h,
          ((∫ rows, positiveOnPrefix z b (List.ofFn rows) ∂rowLaw p (n + 1)) -
            (∫ rows, negativeOnPrefix z b (List.ofFn rows) ∂rowLaw p (n + 1))))) := by
    funext b
    rw [hactual b, jointAtomMean, ← Finset.sum_sub_distrib]
    apply Finset.sum_congr rfl
    intro z _hz
    ring
  have hcum (a : Node I) :
      cumulative (fun b => jointAtomMean p plus minus b - actualBlockMean p b h) a =
        cumulativeRemainder p a h := by
    rw [hdiff, corrFrag_cumulative_combination]
    unfold cumulativeRemainder supportedAverage
    apply Finset.sum_congr rfl
    intro z _hz
    by_cases hz : 0 < p z
    · simp only [hz, if_true]
      rw [corrFrag_supported_remainder p z (plus z) (minus z) hp hz
        (hpair.2 z hz).1 (hpair.2 z hz).2.1 a h]
    · have hz0 : p z = 0 := le_antisymm (le_of_not_gt hz) (hp.1 z)
      simp [hz0]
  refine ⟨hcum alpha, ?_⟩
  intro c hc
  calc
    jointAtomMean p plus minus alpha - actualBlockMean p alpha h =
        ∑ b, c b * cumulative
          (fun d => jointAtomMean p plus minus d - actualBlockMean p d h) b :=
      (hc.2 (fun d => jointAtomMean p plus minus d - actualBlockMean p d h)).symm
    _ = ∑ b, c b * cumulativeRemainder p b h := by simp_rw [hcum]
    _ = cumulative (fun b => c b * cumulativeRemainder p b h) alpha := by
      unfold cumulative
      apply Finset.sum_congr rfl
      intro b _hb
      by_cases hba : rawLE b.val alpha.val
      · simp only [hba, if_true]
      · simp only [hba, if_false, hc.1 b hba, zero_mul]


private lemma latentFrag_fiber_law {K : Type u} {Q : Type v}
    [Fintype K] [Fintype Q] (p : K → ℝ) (phi : K → Q) (hp : Law p) :
    Law (fiberMass p phi) := by
  classical
  refine ⟨?_, ?_⟩
  · intro z
    exact Finset.sum_nonneg (fun k _ => by
      change 0 ≤ if phi k = z then p k else 0
      split_ifs
      · exact hp.1 k
      · exact le_rfl)
  · change (∑ z, ∑ k, if phi k = z then p k else 0) = 1
    calc
      _ = ∑ k, p k := by
        rw [Finset.sum_comm]
        apply Finset.sum_congr rfl
        intro k _
        simp
      _ = 1 := hp.2

private lemma latentFrag_fiber_pos {K : Type u} {Q : Type v}
    [Fintype K] (p : K → ℝ) (phi : K → Q) (hp : ∀ k, 0 ≤ p k) (z : Q) :
    0 < fiberMass p phi z ↔ ∃ k, phi k = z ∧ 0 < p k := by
  classical
  unfold fiberMass
  rw [Finset.sum_pos_iff_of_nonneg (fun k _ => by
    split_ifs
    · exact hp k
    · exact le_rfl)]
  constructor
  · rintro ⟨k, _hk, hkpos⟩
    by_cases he : phi k = z
    · exact ⟨k, he, by simpa only [if_pos he] using hkpos⟩
    · simp only [if_neg he, lt_self_iff_false] at hkpos
  · rintro ⟨k, he, hkpos⟩
    exact ⟨k, Finset.mem_univ k, by simpa only [if_pos he] using hkpos⟩

private lemma latentFrag_fiber_tangent {K : Type u} {Q : Type v}
    [Fintype K] [Fintype Q] (p : ℝ → K → ℝ) (dp : K → ℝ)
    (t0 L : ℝ) (phi : K → Q) (hp : LocalLawTangent p dp t0 L) :
    LocalLawTangent (fun t => fiberMass (p t) phi) (fiberMass dp phi) t0 L := by
  classical
  have h0 := tangent_law_at p dp t0 L hp
  obtain ⟨U, hU, ht0, hnear⟩ := hp.2.1
  refine ⟨hp.1, ⟨U, hU, ht0, ?_⟩, ?_, ?_⟩
  · intro t ht
    refine ⟨latentFrag_fiber_law (p t) phi (hnear t ht).1, ?_⟩
    intro z
    rw [latentFrag_fiber_pos (p t) phi (hnear t ht).1.1,
      latentFrag_fiber_pos (p t0) phi h0.1]
    constructor
    · rintro ⟨k, hk, hpos⟩
      exact ⟨k, hk, ((hnear t ht).2 k).mp hpos⟩
    · rintro ⟨k, hk, hpos⟩
      exact ⟨k, hk, ((hnear t ht).2 k).mpr hpos⟩
  · intro z
    change HasDerivAt (fun t => ∑ k, if phi k = z then p t k else 0)
      (∑ k, if phi k = z then dp k else 0) t0
    apply HasDerivAt.fun_sum
    intro k _
    by_cases he : phi k = z
    · simpa only [if_pos he] using hp.2.2.1 k
    · simpa only [if_neg he] using hasDerivAt_const t0 (0 : ℝ)
  · intro z
    change |∑ k, if phi k = z then dp k else 0| ≤
      L * (∑ k, if phi k = z then p t0 k else 0)
    calc
      _ ≤ ∑ k, |if phi k = z then dp k else 0| :=
        Finset.abs_sum_le_sum_abs _ _
      _ ≤ ∑ k, L * (if phi k = z then p t0 k else 0) := by
        apply Finset.sum_le_sum
        intro k _
        by_cases he : phi k = z
        · simpa only [if_pos he] using hp.2.2.2 k
        · simp only [if_neg he, abs_zero, mul_zero, le_refl]
      _ = _ := (Finset.mul_sum ..).symm

private lemma latentFrag_induced_eq_fiber
    {I : Type u} {X : I → Type v} {T : Type w} {W : Type x}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T] [Fintype W]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T] [DecidableEq W]
    (p : W → ℝ) (phi : W → Key I X T) :
    inducedMass phi p = fiberMass p phi := by
  classical
  funext z
  unfold inducedMass fiberMass
  apply Finset.sum_congr rfl
  intro k _
  by_cases he : phi k = z
  · simp only [if_pos he]
  · simp only [if_neg he]

private lemma latentFrag_measure_eq {K : Type u} [Fintype K]
    [MeasurableSpace K] [MeasurableSingletonClass K] (mu nu : Measure K)
    (h : ∀ z, mu {z} = nu {z}) : mu = nu := by
  rw [← Measure.sum_smul_dirac mu, ← Measure.sum_smul_dirac nu]
  congr 1
  funext z
  rw [h z]

private lemma latentFrag_latent_map {K : Type u} {Q : Type v}
    [Fintype K] [Fintype Q] [DecidableEq K] [DecidableEq Q]
    (p : K → ℝ) (phi : K → Q) (hp : Law p) :
    let : MeasurableSpace K := ⊤;
    let : MeasurableSpace Q := ⊤;
    (latentMeasure p).map phi = latentMeasure (fiberMass p phi) := by
  classical
  let : MeasurableSpace K := ⊤
  let : MeasurableSpace Q := ⊤
  have himage := moment_latent_law_measure (fiberMass p phi)
    (latentFrag_fiber_law p phi hp)
  apply latentFrag_measure_eq
  intro z
  calc
    ((latentMeasure p).map phi) {z} =
        ∑ k, if phi k = z then ENNReal.ofReal (p k) else 0 := by
      rw [Measure.map_apply (measurable_of_finite phi) (measurableSet_singleton z)]
      simp only [latentMeasure, Measure.finsetSum_apply, Measure.smul_apply,
        smul_eq_mul, Measure.dirac_apply, Set.indicator_apply, Set.mem_preimage,
        Set.mem_singleton_iff, Pi.one_apply, mul_ite, mul_one, mul_zero]
    _ = ∑ k, ENNReal.ofReal (if phi k = z then p k else 0) := by
      apply Finset.sum_congr rfl
      intro k _
      by_cases he : phi k = z <;> simp only [he, if_true, if_false, ENNReal.ofReal_zero]
    _ = ENNReal.ofReal (fiberMass p phi z) := by
      symm
      unfold fiberMass
      calc
        _ = ∑ k : K, ENNReal.ofReal
            (@ite ℝ (phi k = z) (Classical.propDecidable _) (p k) 0) := by
          exact ENNReal.ofReal_sum_of_nonneg
            (s := Finset.univ)
            (f := fun k : K => @ite ℝ (phi k = z) (Classical.propDecidable _) (p k) 0)
            (fun k _ => by
              split_ifs
              · exact hp.1 k
              · exact le_rfl)
        _ = _ := by
          apply Finset.sum_congr rfl
          intro k _
          by_cases he : phi k = z <;> simp only [if_pos, he]
    _ = latentMeasure (fiberMass p phi) {z} := (himage.2.1 z).symm

private lemma latentFrag_latent_product_map {K : Type u} {Q : Type v}
    [Fintype K] [Fintype Q] [DecidableEq K] [DecidableEq Q]
    (p : K → ℝ) (phi : K → Q) (count : ℕ) (hp : Law p) :
    let : MeasurableSpace K := ⊤;
    let : MeasurableSpace Q := ⊤;
    (latentRowLaw p count).map (fun rows i => phi (rows i)) =
      latentRowLaw (fiberMass p phi) count := by
  classical
  let : MeasurableSpace K := ⊤
  let : MeasurableSpace Q := ⊤
  have hmap := latentFrag_latent_map p phi hp
  let : IsProbabilityMeasure (latentMeasure p) := (moment_latent_law_measure p hp).1
  have hphi : Measurable phi := measurable_of_finite phi
  let : IsProbabilityMeasure ((latentMeasure p).map phi) :=
    (latentMeasure p).isProbabilityMeasure_map hphi.aemeasurable
  have hpi := Measure.pi_map_pi
    (μ := fun _ : Fin count => latentMeasure p)
    (f := fun _ : Fin count => phi) (fun _ => hphi.aemeasurable)
  simpa only [latentRowLaw, hmap] using hpi

private lemma latentFrag_key_product_map
    {I : Type u} {X : I → Type v} {T : Type w} {W : Type x}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T] [Fintype W]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T] [DecidableEq W]
    (p : W → ℝ) (phi : W → Key I X T) (count : ℕ) (hp : Law p) :
    let : MeasurableSpace W := ⊤;
    let : MeasurableSpace (Key I X T) := ⊤;
    (latentRowLaw p count).map (mapBlock phi count) =
      rowLaw (inducedMass phi p) count := by
  classical
  let : MeasurableSpace W := ⊤
  let : MeasurableSpace (Key I X T) := ⊤
  have hmap := latentFrag_latent_product_map p phi count hp
  rw [← latentFrag_induced_eq_fiber p phi] at hmap
  simpa only [latentRowLaw, rowLaw, mapBlock, latentMeasure, keyMeasure] using! hmap

private lemma latentFrag_image_expectation
    {I : Type u} {X : I → Type v} {T : Type w} {W : Type x}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T] [Fintype W]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T] [DecidableEq W]
    (p : W → ℝ) (phi : W → Key I X T) (count : ℕ) (hp : Law p)
    (f : (Fin count → Key I X T) → ℝ) :
    let : MeasurableSpace W := ⊤;
    let : MeasurableSpace (Key I X T) := ⊤;
    (∫ rows, f rows ∂rowLaw (inducedMass phi p) count) =
      ∫ rows, f (mapBlock phi count rows) ∂latentRowLaw p count := by
  classical
  let : MeasurableSpace W := ⊤
  let : MeasurableSpace (Key I X T) := ⊤
  have himage : Law (inducedMass phi p) := by
    rw [latentFrag_induced_eq_fiber p phi]
    exact latentFrag_fiber_law p phi hp
  have hprod := PidPrefixProbabilityCandidate.finite_product_law I X T
    (inducedMass phi p) count himage
  have hmap := latentFrag_key_product_map p phi count hp
  have hi : Integrable f ((latentRowLaw p count).map (mapBlock phi count)) := by
    rw [hmap]
    exact (hprod.2.2 f).1
  calc
    _ = ∫ rows, f rows ∂((latentRowLaw p count).map (mapBlock phi count)) := by
      rw [hmap]
    _ = _ := integral_map (measurable_of_finite (mapBlock phi count)).aemeasurable
      hi.aestronglyMeasurable

private lemma proof_finite_latent_pushforward :
    finite_latent_pushforward_target.{u, v, w, x} := by
  intro I X T W _ _ _ _ _ _ _ _ _ rho drho t0 L phi hp
  classical
  let : MeasurableSpace W := ⊤
  let : MeasurableSpace (Key I X T) := ⊤
  have h0 := tangent_law_at rho drho t0 L hp
  refine ⟨?_, ?_, ?_, ?_⟩
  · have hfun : (fun t => inducedMass phi (rho t)) =
        (fun t => fiberMass (rho t) phi) := by
      funext t
      exact latentFrag_induced_eq_fiber (rho t) phi
    rw [hfun, latentFrag_induced_eq_fiber drho phi]
    exact latentFrag_fiber_tangent rho drho t0 L phi hp
  · have hmap := latentFrag_latent_map (rho t0) phi h0
    rw [← latentFrag_induced_eq_fiber (rho t0) phi] at hmap
    simpa only [latentMeasure, keyMeasure] using hmap
  · intro count
    exact latentFrag_key_product_map (rho t0) phi count h0
  · intro z hz
    rw [score, if_pos hz]
    simp only [inducedMass, tangent_score_weight rho drho t0 L hp]

private lemma proof_finite_latent_score_derivative :
    finite_latent_score_derivative_target.{u, v, w, x} := by
  intro I X T W _ _ _ _ _ _ _ _ _ rho drho t0 L phi alpha h hp
  classical
  let : MeasurableSpace W := ⊤
  let : MeasurableSpace (Key I X T) := ⊤
  have h0 := tangent_law_at rho drho t0 L hp
  have hprod := moment_latent_product_law (rho t0) (h + 1) h0
  have himage := (proof_finite_latent_pushforward I X T W rho drho t0 L phi hp).1
  have hd : HasDerivAt
      (fun t => actualBlockMean (inducedMass phi (rho t)) alpha h)
      (meanLatentScoreGradient (rho t0) drho phi alpha h) t0 := by
    have hsum : HasDerivAt
        (fun t => ∑ rows : Fin (h + 1) → W,
          (∏ i, rho t (rows i)) * blockStatistic alpha h (mapBlock phi (h + 1) rows))
        (∑ rows : Fin (h + 1) → W,
          ((∏ i, rho t0 (rows i)) * ∑ i, score (rho t0) drho (rows i)) *
            blockStatistic alpha h (mapBlock phi (h + 1) rows)) t0 := by
      exact HasDerivAt.fun_sum (fun rows _ =>
        (finite_product_score_derivative rho drho t0 L hp Finset.univ rows).mul_const
          (blockStatistic alpha h (mapBlock phi (h + 1) rows)))
    have he : (fun t => actualBlockMean (inducedMass phi (rho t)) alpha h) =ᶠ[𝓝 t0]
        (fun t => ∑ rows : Fin (h + 1) → W,
          (∏ i, rho t (rows i)) * blockStatistic alpha h (mapBlock phi (h + 1) rows)) := by
      filter_upwards [tangent_law_eventually rho drho t0 L hp] with t ht
      calc
        _ = ∫ rows, blockStatistic alpha h (mapBlock phi (h + 1) rows)
            ∂latentRowLaw (rho t) (h + 1) :=
          latentFrag_image_expectation (rho t) phi (h + 1) ht (blockStatistic alpha h)
        _ = _ := (moment_latent_product_law (rho t) (h + 1) ht).2.2
          (fun rows => blockStatistic alpha h (mapBlock phi (h + 1) rows)) |>.2
    apply (hsum.congr_of_eventuallyEq he).congr_deriv
    rw [meanLatentScoreGradient, (hprod.2.2 (latentScoreGradient (rho t0) drho phi alpha h)).2]
    apply Finset.sum_congr rfl
    intro rows _
    simp only [latentScoreGradient]
    ring
  refine ⟨(hprod.2.2 (latentScoreGradient (rho t0) drho phi alpha h)).1, ?_, hd⟩
  exact hd.unique ((proof_finite_block_score_derivative I X T
    (fun t => inducedMass phi (rho t)) (inducedMass phi drho) t0 L alpha h himage).2.2)

/- Source-only insertion inside PidPrefixMgwGradientCandidate.
   Uses existing same-file tangent helpers, target 5, and explicitly passed
   exact target 2/4 values. No new import, axiom, generated private name or
   weakening of actual_atom_score_bias_target. Unelaborated. -/

private lemma scoreBias_event_derivative {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) (s : Finset K) :
    HasDerivAt (fun t => PidFiniteConvergence.finiteEventMass (p t) s)
      (PidFiniteConvergence.finiteEventMass dp s) t0 := by
  classical
  exact HasDerivAt.fun_sum (fun z _ => hp.2.2.1 z)

private lemma scoreBias_event_bound {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) (s : Finset K) :
    |PidFiniteConvergence.finiteEventMass dp s| ≤
      L * PidFiniteConvergence.finiteEventMass (p t0) s := by
  classical
  unfold PidFiniteConvergence.finiteEventMass
  calc
    |∑ z ∈ s, dp z| ≤ ∑ z ∈ s, |dp z| := Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ z ∈ s, L * p t0 z := Finset.sum_le_sum (fun z _ => hp.2.2.2 z)
    _ = L * ∑ z ∈ s, p t0 z := (Finset.mul_sum ..).symm

private lemma scoreBias_supported_derivative {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) (F : ℝ → K → ℝ) (dF : K → ℝ)
    (hF : ∀ z, 0 < p t0 z → HasDerivAt (fun t => F t z) (dF z) t0) :
    HasDerivAt (fun t => supportedAverage (p t) (F t))
      (∑ z, if 0 < p t0 z then dp z * F t0 z + p t0 z * dF z else 0) t0 := by
  classical
  have hd : HasDerivAt
      (fun t => ∑ z, if 0 < p t0 z then p t z * F t z else 0)
      (∑ z, if 0 < p t0 z then dp z * F t0 z + p t0 z * dF z else 0) t0 := by
    apply HasDerivAt.fun_sum
    intro z _
    by_cases hz : 0 < p t0 z
    · simpa only [if_pos hz] using! (hp.2.2.1 z).mul (hF z hz)
    · simpa only [if_neg hz] using hasDerivAt_const t0 (0 : ℝ)
  apply hd.congr_of_eventuallyEq
  obtain ⟨U, hU, ht, hall⟩ := hp.2.1
  filter_upwards [hU.mem_nhds ht] with t htU
  unfold supportedAverage
  apply Finset.sum_congr rfl
  intro z _
  simp only [(hall t htU).2 z]

private lemma scoreBias_kernel_bound
    (hsc : scalar_remainder_calculus_target) (q dq L : ℝ) (h : ℕ)
    (hq : 0 < q) (hq1 : q ≤ 1) (hL : 0 ≤ L) (hdq : |dq| ≤ L * q) :
    |(-((1 - q) ^ h) / q) * dq| ≤ (L / ((h : ℝ) + 1)) * (1 / q) := by
  have hm : 0 < (h : ℝ) + 1 := by positivity
  have hu : 0 ≤ (1 - q) ^ h := pow_nonneg (sub_nonneg.mpr hq1) _
  have huB : (1 - q) ^ h ≤ 1 / (((h : ℝ) + 1) * q) := by
    apply (le_div_iff₀ (mul_pos hm hq)).2
    nlinarith [hsc.2.2 q (le_of_lt hq) hq1 h]
  have hk : |-((1 - q) ^ h) / q| = (1 - q) ^ h / q := by
    rw [abs_div, abs_neg, abs_of_nonneg hu, abs_of_pos hq]
  calc
    _ = ((1 - q) ^ h / q) * |dq| := by rw [abs_mul, hk]
    _ ≤ ((1 - q) ^ h / q) * (L * q) :=
      mul_le_mul_of_nonneg_left hdq (div_nonneg hu (le_of_lt hq))
    _ = L * (1 - q) ^ h := by field_simp [ne_of_gt hq]
    _ ≤ L * (1 / (((h : ℝ) + 1) * q)) := mul_le_mul_of_nonneg_left huB hL
    _ = _ := by field_simp [ne_of_gt hm, ne_of_gt hq]

private lemma scoreBias_anchor_bound
    (hsc : scalar_remainder_calculus_target) (w dw a da q dq L : ℝ) (h : ℕ)
    (hw : 0 ≤ w) (hq : 0 < q) (hqa : q ≤ a) (ha1 : a ≤ 1) (hL : 0 ≤ L)
    (hdw : |dw| ≤ L * w) (hda : |da| ≤ L * a) (hdq : |dq| ≤ L * q) :
    |dw * (logRemainder a h - logRemainder q h) +
      w * ((-((1 - a) ^ h) / a) * da - (-((1 - q) ^ h) / q) * dq)| ≤
      (2 * L / ((h : ℝ) + 1)) * (w / q) := by
  have ha : 0 < a := hq.trans_le hqa
  have hm : 0 < (h : ℝ) + 1 := by positivity
  have hr := hsc.2.1 q a hq hqa ha1 h
  have hanchor : |dw * (logRemainder a h - logRemainder q h)| ≤
      (L * w) * ((1 / q - 1 / a) / ((h : ℝ) + 1)) := by
    calc
      _ = |dw| * (logRemainder q h - logRemainder a h) := by
        rw [abs_mul, abs_sub_comm, abs_of_nonneg hr.1]
      _ ≤ (L * w) * (logRemainder q h - logRemainder a h) :=
        mul_le_mul_of_nonneg_right hdw hr.1
      _ ≤ _ := mul_le_mul_of_nonneg_left hr.2 (mul_nonneg hL hw)
  have hmass :
      |w * ((-((1 - a) ^ h) / a) * da - (-((1 - q) ^ h) / q) * dq)| ≤
      w * ((L / ((h : ℝ) + 1)) * (1 / a) +
        (L / ((h : ℝ) + 1)) * (1 / q)) := by
    rw [abs_mul, abs_of_nonneg hw]
    apply mul_le_mul_of_nonneg_left _ hw
    have htri :
        |(-((1 - a) ^ h) / a) * da - (-((1 - q) ^ h) / q) * dq| ≤
          |(-((1 - a) ^ h) / a) * da| + |(-((1 - q) ^ h) / q) * dq| := by
      simpa only [sub_eq_add_neg, abs_neg] using
        abs_add_le ((-((1 - a) ^ h) / a) * da) (-((-((1 - q) ^ h) / q) * dq))
    exact htri.trans (add_le_add
      (scoreBias_kernel_bound hsc a da L h ha ha1 hL hda)
      (scoreBias_kernel_bound hsc q dq L h hq (hqa.trans ha1) hL hdq))
  calc
    _ ≤ |dw * (logRemainder a h - logRemainder q h)| +
        |w * ((-((1 - a) ^ h) / a) * da - (-((1 - q) ^ h) / q) * dq)| :=
      abs_add_le _ _
    _ ≤ (L * w) * ((1 / q - 1 / a) / ((h : ℝ) + 1)) +
        w * ((L / ((h : ℝ) + 1)) * (1 / a) +
          (L / ((h : ℝ) + 1)) * (1 / q)) := add_le_add hanchor hmass
    _ = _ := by field_simp [ne_of_gt hm, ne_of_gt hq, ne_of_gt ha]; ring

private lemma scoreBias_anchor_domains {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (hp : Law p) (z : Key I X T) (hz : 0 < p z) (beta : Node I) :
    p z ≤ restrictedMass p z beta ∧
    restrictedMass p z beta ≤ sourceMass p z beta ∧
    restrictedMass p z beta ≤ targetMass p z ∧
    sourceMass p z beta ≤ 1 ∧ targetMass p z ≤ 1 := by
  classical
  have hd := PidMgwBridgeCandidate.supported_anchor_domains I X T p z hp hz
  refine ⟨?_, ?_, ?_, (hd.2.2.2.2.2.2.2.2.2.2.2.2 beta).2.1, hd.2.2.2.1⟩
  · exact Finset.single_le_sum (fun x _ => hp.1 x)
      (PidFiniteConvergence.sx_target_restricted_event_anchor_mem beta.property.1 z)
  · unfold restrictedMass sourceMass PidFiniteConvergence.finiteEventMass
    rw [PidFiniteConvergence.sx_target_restricted_event_eq_inter]
    exact Finset.sum_le_sum_of_subset_of_nonneg Finset.inter_subset_left
      (fun x _ _ => hp.1 x)
  · unfold restrictedMass targetMass PidFiniteConvergence.finiteEventMass
    rw [PidFiniteConvergence.sx_target_restricted_event_eq_inter]
    exact Finset.sum_le_sum_of_subset_of_nonneg Finset.inter_subset_right
      (fun x _ _ => hp.1 x)

private lemma scoreBias_target_fiber {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : Key I X T → ℝ) (z : Key I X T) :
    targetMass p z = fiberMass p (fun x : Key I X T => x.2) z.2 := by
  classical
  unfold targetMass PidFiniteConvergence.finiteEventMass PidFiniteConvergence.targetBranchEvent
    PidFiniteConvergence.targetEquivalent fiberMass
  rw [Finset.sum_filter]
  apply Finset.sum_congr rfl
  intro x _
  by_cases he : z.2 = x.2 <;> simp [he, eq_comm]

private lemma scoreBias_target_weight_zero {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (dp : Key I X T → ℝ) (hzero : TargetTangentZero dp) (F : T → ℝ) :
    (∑ z, dp z * F z.2) = 0 := by
  classical
  have he : (∑ y : T, fiberMass dp (fun z : Key I X T => z.2) y * F y) =
      ∑ z, dp z * F z.2 := by
    unfold fiberMass
    simp_rw [Finset.sum_mul]
    rw [Finset.sum_comm]
    apply Finset.sum_congr rfl
    intro z _
    rw [Finset.sum_eq_single z.2]
    · simp
    · intro y _ hy
      simp [Ne.symm hy]
    · simp
  rw [← he]
  apply Finset.sum_eq_zero
  intro y _
  rw [hzero y, zero_mul]

private lemma scoreBias_cumulative_derivative
    (hsc : scalar_remainder_calculus_target)
    {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (p : ℝ → Key I X T → ℝ) (dp : Key I X T → ℝ) (t0 L : ℝ)
    (hp : LocalLawTangent p dp t0 L) (htarget : TargetTangentZero dp)
    (beta : Node I) (h : ℕ) :
    ∃ d : ℝ, HasDerivAt (fun t => cumulativeRemainder (p t) beta h) d t0 ∧
      |d| ≤ (2 * L / ((h : ℝ) + 1)) * queryMoment (p t0) beta := by
  classical
  have h0 := tangent_law_at p dp t0 L hp
  let A : Key I X T → ℝ := fun z => sourceMass (p t0) z beta
  let Q : Key I X T → ℝ := fun z => restrictedMass (p t0) z beta
  let dA : Key I X T → ℝ := fun z => sourceMass dp z beta
  let dQ : Key I X T → ℝ := fun z => restrictedMass dp z beta
  let K : Key I X T → ℝ := fun z =>
    (-((1 - A z) ^ h) / A z) * dA z - (-((1 - Q z) ^ h) / Q z) * dQ z
  let F : ℝ → Key I X T → ℝ := fun t z =>
    logRemainder (sourceMass (p t) z beta) h -
      logRemainder (restrictedMass (p t) z beta) h + logRemainder (targetMass (p t) z) h
  let G : Key I X T → ℝ := fun z => if 0 < p t0 z then
    dp z * (logRemainder (A z) h - logRemainder (Q z) h) + p t0 z * K z else 0
  have hF (z : Key I X T) (hz : 0 < p t0 z) :
      HasDerivAt (fun t => F t z) (K z) t0 := by
    have hdom := scoreBias_anchor_domains (p t0) h0 z hz beta
    have hq : 0 < restrictedMass (p t0) z beta := hz.trans_le hdom.1
    have ha : 0 < sourceMass (p t0) z beta := hq.trans_le hdom.2.1
    have hb : 0 < targetMass (p t0) z := hq.trans_le hdom.2.2.1
    have hdA : HasDerivAt (fun t => sourceMass (p t) z beta) (dA z) t0 := by
      exact scoreBias_event_derivative p dp t0 L hp
        (PidFiniteConvergence.sxSourceEvent beta.val z)
    have hdQ : HasDerivAt (fun t => restrictedMass (p t) z beta) (dQ z) t0 := by
      exact scoreBias_event_derivative p dp t0 L hp
        (PidFiniteConvergence.sxTargetRestrictedEvent beta.val z)
    have hdB : HasDerivAt (fun t => targetMass (p t) z) (targetMass dp z) t0 := by
      exact scoreBias_event_derivative p dp t0 L hp
        (PidFiniteConvergence.targetBranchEvent z)
    have hb0 : targetMass dp z = 0 := by
      rw [scoreBias_target_fiber]
      exact htarget z.2
    rw [hb0] at hdB
    have hla := (hsc.1 _ ha h).comp t0 hdA
    have hlq := (hsc.1 _ hq h).comp t0 hdQ
    have hlb := (hsc.1 _ hb h).comp t0 hdB
    simpa only [F, K, A, Q, mul_zero, add_zero] using! (hla.sub hlq).add hlb
  have hd := scoreBias_supported_derivative p dp t0 L hp F K hF
  have htzero : (∑ z, dp z * logRemainder (targetMass (p t0) z) h) = 0 := by
    simp_rw [scoreBias_target_fiber]
    exact scoreBias_target_weight_zero dp htarget
      (fun y => logRemainder (fiberMass (p t0) (fun z : Key I X T => z.2) y) h)
  have hsplit :
      (∑ z, if 0 < p t0 z then dp z * F t0 z + p t0 z * K z else 0) =
        (∑ z, G z) + ∑ z, dp z * logRemainder (targetMass (p t0) z) h := by
    rw [← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro z _
    by_cases hz : 0 < p t0 z
    · simp only [G, F, A, Q, if_pos hz]
      ring
    · have hz0 : p t0 z = 0 := le_antisymm (le_of_not_gt hz) (h0.1 z)
      have hd0 := tangent_zero_off_support p dp t0 L hp z hz0
      simp only [G, if_neg hz, hd0, zero_mul, add_zero]
  rw [hsplit, htzero, add_zero] at hd
  refine ⟨∑ z, G z, ?_, ?_⟩
  · exact hd
  · calc
      |∑ z, G z| ≤ ∑ z, |G z| := Finset.abs_sum_le_sum_abs _ _
      _ ≤ ∑ z, if 0 < p t0 z then
          (2 * L / ((h : ℝ) + 1)) * (p t0 z / Q z) else 0 := by
        apply Finset.sum_le_sum
        intro z _
        by_cases hz : 0 < p t0 z
        · simp only [G, if_pos hz]
          have hdom := scoreBias_anchor_domains (p t0) h0 z hz beta
          have haB : |dA z| ≤ L * A z :=
            scoreBias_event_bound p dp t0 L hp (PidFiniteConvergence.sxSourceEvent beta.val z)
          have hqB : |dQ z| ≤ L * Q z :=
            scoreBias_event_bound p dp t0 L hp
              (PidFiniteConvergence.sxTargetRestrictedEvent beta.val z)
          exact scoreBias_anchor_bound hsc (p t0 z) (dp z) (A z) (dA z) (Q z) (dQ z) L h
            (h0.1 z) (hz.trans_le hdom.1) hdom.2.1 hdom.2.2.2.1 hp.1
            (hp.2.2.2 z) haB hqB
        · simp [G, hz]
      _ = (2 * L / ((h : ℝ) + 1)) * queryMoment (p t0) beta := by
        unfold queryMoment inverseMoment supportedAverage
        rw [Finset.mul_sum]
        apply Finset.sum_congr rfl
        intro z _
        by_cases hz : 0 < p t0 z <;> simp [Q, hz, div_eq_mul_inv, mul_assoc]

private lemma scoreBias_full_row_sum {I : Type u} [Fintype I] [DecidableEq I]
    (alpha : Node I) (c f : Node I → ℝ) (hc : FullInverseRow alpha c) :
    let : Fintype (Node I) := nodeFintype I;
    cumulative (fun beta => c beta * f beta) alpha = ∑ beta, c beta * f beta := by
  classical
  let : Fintype (Node I) := nodeFintype I
  unfold cumulative
  apply Finset.sum_congr rfl
  intro beta _
  by_cases hb : rawLE beta.val alpha.val
  · simp only [if_pos hb]
  · simp only [if_neg hb, hc.1 beta hb, zero_mul]

private lemma scoreBias_from_exact_remainder
    (hsc : scalar_remainder_calculus_target)
    (hrem : actual_atom_remainder_target.{u, v, w}) :
    actual_atom_score_bias_target.{u, v, w} := by
  intro I X T _ _ _ _ _ _ _ p dp t0 L plus minus alpha c h hp htarget hpair hc
  classical
  let : Fintype (Node I) := nodeFintype I
  have hprefix := (proof_finite_block_score_derivative I X T p dp t0 L alpha h hp).2.2
  choose d hd hbound using
    (fun beta : Node I => scoreBias_cumulative_derivative hsc p dp t0 L hp htarget beta h)
  have hsum : HasDerivAt (fun t => ∑ beta, c beta * cumulativeRemainder (p t) beta h)
      (∑ beta, c beta * d beta) t0 :=
    HasDerivAt.fun_sum (fun beta _ => (hd beta).const_mul (c beta))
  have he : (fun t => jointAtomMean (p t) (plus t) (minus t) alpha) =ᶠ[𝓝 t0]
      (fun t => actualBlockMean (p t) alpha h +
        ∑ beta, c beta * cumulativeRemainder (p t) beta h) := by
    filter_upwards [tangent_law_eventually p dp t0 L hp, hpair] with t ht hpt
    have hr := (hrem I X T (p t) (plus t) (minus t) alpha h ht hpt).2 c hc
    rw [scoreBias_full_row_sum alpha c (fun beta => cumulativeRemainder (p t) beta h) hc] at hr
    linarith
  refine ⟨meanScoreGradient (p t0) dp alpha h + ∑ beta, c beta * d beta,
    (hprefix.add hsum).congr_of_eventuallyEq he, hprefix, ?_⟩
  rw [add_sub_cancel_left]
  calc
    |∑ beta, c beta * d beta| ≤ ∑ beta, |c beta * d beta| :=
      Finset.abs_sum_le_sum_abs _ _
    _ = ∑ beta, |c beta| * |d beta| := by simp_rw [abs_mul]
    _ ≤ ∑ beta, |c beta| * ((2 * L / ((h : ℝ) + 1)) * queryMoment (p t0) beta) := by
      apply Finset.sum_le_sum
      intro beta _
      exact mul_le_mul_of_nonneg_left (hbound beta) (abs_nonneg _)
    _ = (2 * L / ((h : ℝ) + 1)) * rowQueryMoment (p t0) c := by
      unfold rowQueryMoment
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro beta _
      ring

private lemma proof_actual_atom_score_bias : actual_atom_score_bias_target.{u, v, w} :=
  scoreBias_from_exact_remainder proof_scalar_remainder_calculus corrFrag_proof_actual_atom_remainder

theorem full_inverse_row :
    PidPrefixMgwGradientContract.full_inverse_row_target.{u} :=
  invrow_proof_full_inverse_row

theorem scalar_remainder_calculus :
    PidPrefixMgwGradientContract.scalar_remainder_calculus_target :=
  proof_scalar_remainder_calculus

theorem native_cumulative_increments :
    PidPrefixMgwGradientContract.native_cumulative_increments_target.{u, v, w} :=
  corrFrag_proof_native_cumulative_increments

theorem actual_atom_remainder :
    PidPrefixMgwGradientContract.actual_atom_remainder_target.{u, v, w} :=
  corrFrag_proof_actual_atom_remainder

theorem finite_block_score_derivative :
    PidPrefixMgwGradientContract.finite_block_score_derivative_target.{u, v, w} :=
  proof_finite_block_score_derivative

theorem actual_atom_score_bias :
    PidPrefixMgwGradientContract.actual_atom_score_bias_target.{u, v, w} :=
  proof_actual_atom_score_bias

theorem finite_latent_pushforward :
    PidPrefixMgwGradientContract.finite_latent_pushforward_target.{u, v, w, x} :=
  proof_finite_latent_pushforward

theorem finite_latent_score_derivative :
    PidPrefixMgwGradientContract.finite_latent_score_derivative_target.{u, v, w, x} :=
  proof_finite_latent_score_derivative

theorem finite_encoder_score :
    PidPrefixMgwGradientContract.finite_encoder_score_target.{u, v, w} :=
  proof_finite_encoder_score

theorem score_second_moment :
    PidPrefixMgwGradientContract.score_second_moment_target.{u, v, w} :=
  proof_score_second_moment

theorem latent_score_second_moment :
    PidPrefixMgwGradientContract.latent_score_second_moment_target.{u, v, w, x} :=
  proof_latent_score_second_moment

end PidPrefixMgwGradientCandidate
