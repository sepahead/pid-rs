import FiniteSensorBayes.Contract
import FiniteSensorBayes.RawTargets
import FiniteSensorBayes.FiniteLogScoreTarget
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

set_option autoImplicit false
set_option warningAsError true

universe u

open scoped BigOperators ENNReal Classical
open MeasureTheory
open FiniteSensorBayes

namespace FiniteSensorBayesCandidate

private theorem mass_sum {A : Type u} [Fintype A] (p : PMF A) :
    (∑ a, mass p a) = 1 := by
  classical
  have hp : (∑ a, p a) = 1 := by
    simpa only [tsum_fintype] using p.tsum_coe
  calc
    (∑ a, mass p a) = (∑ a, p a).toReal :=
      (ENNReal.toReal_sum (fun a _ => p.apply_ne_top a)).symm
    _ = 1 := by rw [hp, ENNReal.toReal_one]

private theorem mass_positive_iff {A : Type u} (p : PMF A) (a : A) :
    0 < mass p a ↔ a ∈ p.support := by
  constructor
  · intro h
    exact (p.apply_pos_iff a).mp (ENNReal.toReal_pos_iff.mp h).1
  · intro h
    exact ENNReal.toReal_pos ((p.mem_support_iff a).mp h) (p.apply_ne_top a)

theorem finiteMass : FiniteSensorBayes.Raw.FiniteMassTarget.{u} := by
  classical
  intro K _ _ p
  let : MeasurableSpace K := ⊤
  refine ⟨?_, mass_sum p, ?_, mass_positive_iff p, ?_⟩
  · change IsProbabilityMeasure p.toMeasure
    infer_instance
  · intro k
    refine ⟨ENNReal.toReal_nonneg, ?_⟩
    change (p k).toReal ≤ 1
    simpa only [ENNReal.toReal_one] using
      ENNReal.toReal_mono ENNReal.one_ne_top (p.coe_le_one k)
  · intro k
    exact p.toMeasure_apply_singleton k (MeasurableSet.singleton k)

theorem finiteExpectation : FiniteSensorBayes.Raw.FiniteExpectationTarget.{u} := by
  classical
  intro K _ _ p f
  let : MeasurableSpace K := ⊤
  constructor
  · change Integrable f p.toMeasure
    exact Integrable.of_finite
  · change (∫ k, f k ∂p.toMeasure) = ∑ k, (p k).toReal * f k
    simpa only [smul_eq_mul] using
      (PMF.integral_eq_sum p f)

theorem gibbs : FiniteSensorBayes.Raw.GibbsTarget.{u} := by
  classical
  intro Y _ _ r q hsupport
  have hpoint (y : Y) : mass r y - mass q y ≤
      (if y ∈ r.support then mass r y * Real.log (mass r y / mass q y) else 0) := by
    by_cases hy : y ∈ r.support
    · rw [if_pos hy]
      have hr : 0 < mass r y := (mass_positive_iff r y).2 hy
      have hq : 0 < mass q y := hsupport y hy
      have hlog := Real.one_sub_inv_le_log_of_pos (div_pos hr hq)
      have hmul := mul_le_mul_of_nonneg_left hlog (le_of_lt hr)
      rw [inv_div, mul_sub, mul_one, mul_div_cancel₀ _ (ne_of_gt hr)] at hmul
      exact hmul
    · rw [if_neg hy]
      have hz : mass r y = 0 := by
        change (r y).toReal = 0
        rw [(r.apply_eq_zero_iff y).2 hy, ENNReal.toReal_zero]
      rw [hz, zero_sub]
      exact neg_nonpos.mpr ENNReal.toReal_nonneg
  have hsum : (∑ y, (mass r y - mass q y)) ≤ kl r q := by
    change (∑ y, (mass r y - mass q y)) ≤
      ∑ y, if y ∈ r.support then mass r y * Real.log (mass r y / mass q y) else 0
    exact Finset.sum_le_sum (fun y _ => hpoint y)
  simpa only [Finset.sum_sub_distrib, mass_sum r, mass_sum q, sub_self] using hsum

private theorem log_score_sum_decomposition {Y : Type u} [Fintype Y]
    (r q : PMF Y) (hsupport : ∀ y ∈ r.support, 0 < mass q y) :
    (∑ y, mass r y * (-Real.log (mass q y))) = entropy r + kl r q := by
  classical
  unfold entropy kl
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro y _
  by_cases hy : y ∈ r.support
  · simp only [if_pos hy]
    have hr : 0 < mass r y := (mass_positive_iff r y).2 hy
    have hq : 0 < mass q y := hsupport y hy
    rw [Real.log_div (ne_of_gt hr) (ne_of_gt hq)]
    ring
  · have hz : mass r y = 0 := by
      change (r y).toReal = 0
      rw [(r.apply_eq_zero_iff y).2 hy, ENNReal.toReal_zero]
    simp only [if_neg hy, hz, zero_mul, zero_add]

private theorem kl_self_zero {Y : Type u} [Fintype Y] (r : PMF Y) :
    kl r r = 0 := by
  classical
  unfold kl
  apply Finset.sum_eq_zero
  intro y _
  by_cases hy : y ∈ r.support
  · rw [if_pos hy, Real.log_div_self, mul_zero]
  · rw [if_neg hy]

theorem logScore : FiniteSensorBayes.LogScoreOwner.FiniteLogScoreTarget.{u} := by
  classical
  intro Y _ _ r q hsupport
  let : MeasurableSpace Y := ⊤
  have hintegral (s : PMF Y) :
      (∫ y, -Real.log (mass s y) ∂discreteMeasure r) =
        ∑ y, mass r y * (-Real.log (mass s y)) := by
    exact (finiteExpectation Y r (fun y => -Real.log (mass s y))).2
  have hdecomposition :
      (∫ y, -Real.log (mass q y) ∂discreteMeasure r) = entropy r + kl r q :=
    (hintegral q).trans (log_score_sum_decomposition r q hsupport)
  have hnonneg : 0 ≤ kl r q := gibbs Y r q hsupport
  refine ⟨hdecomposition, ?_, ?_⟩
  · calc
      entropy r ≤ entropy r + kl r q := le_add_of_nonneg_right hnonneg
      _ = ∫ y, -Real.log (mass q y) ∂discreteMeasure r := hdecomposition.symm
  · calc
      (∫ y, -Real.log (mass r y) ∂discreteMeasure r) =
          ∑ y, mass r y * (-Real.log (mass r y)) := hintegral r
      _ = entropy r + kl r r := log_score_sum_decomposition r r
        (fun y hy => (mass_positive_iff r y).2 hy)
      _ = entropy r := by rw [kl_self_zero, add_zero]

end FiniteSensorBayesCandidate
