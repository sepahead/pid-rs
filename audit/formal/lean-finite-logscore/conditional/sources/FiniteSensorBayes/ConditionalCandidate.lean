import FiniteSensorBayes.Contract
import FiniteSensorBayes.RawTargets
import FiniteSensorBayes.FiniteLogScoreTarget
import FiniteSensorBayes.Candidate
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

/-!
Finite conditional Bayes and information-gain proof candidate.
Source author: Sepehr Mahmoudian. The target propositions and their PMF,
measure, support, logarithm, and natural-logarithm units are fixed by the
owner modules. This candidate is development evidence until root review,
the exact-type judge, and the fresh kernel replay all succeed.
-/

set_option autoImplicit false
set_option warningAsError true

universe u v w x

open scoped BigOperators ENNReal Classical
open MeasureTheory
open FiniteSensorBayes

namespace FiniteSensorBayesConditionalCandidate

private theorem mass_pos_iff {A : Type u} (p : PMF A) (a : A) :
    0 < mass p a ↔ a ∈ p.support := by
  constructor
  · intro h
    exact (p.apply_pos_iff a).mp (ENNReal.toReal_pos_iff.mp h).1
  · intro h
    exact ENNReal.toReal_pos ((p.mem_support_iff a).mp h) (p.apply_ne_top a)

private theorem mass_zero_of_not_support {A : Type u} (p : PMF A) (a : A)
    (h : a ∉ p.support) : mass p a = 0 := by
  change (p a).toReal = 0
  rw [(p.apply_eq_zero_iff a).2 h, ENNReal.toReal_zero]

private theorem mass_map_eq_sum {A : Type u} {B : Type v} [Fintype A]
    (p : PMF A) (f : A → B) (b : B) :
    mass (p.map f) b = ∑ a, if f a = b then mass p a else 0 := by
  classical
  calc
    mass (p.map f) b = (∑ a, if b = f a then p a else 0).toReal := by
      change ((p.map f) b).toReal = _
      rw [PMF.map_apply, tsum_fintype]
    _ = ∑ a, (if b = f a then p a else 0).toReal := by
      apply ENNReal.toReal_sum
      intro a _
      split_ifs <;> simp [p.apply_ne_top]
    _ = ∑ a, if f a = b then mass p a else 0 := by
      apply Finset.sum_congr rfl
      intro a _
      by_cases h : f a = b
      · simp [h]
        rfl
      · have hb : b ≠ f a := Ne.symm h
        simp [h, hb]

private theorem discrete_map {A : Type u} {B : Type v}
    (p : PMF A) (f : A → B) :
    discreteMeasure (p.map f) = mappedMeasure p f := by
  classical
  let : MeasurableSpace A := ⊤
  let : MeasurableSpace B := ⊤
  change (p.map f).toMeasure = p.toMeasure.map f
  exact (PMF.toMeasure_map f p (Measurable.of_discrete)).symm

private theorem mass_joint_eq_sum {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] (p : PMF K) (target : K → Y) (obs : K → O) (o : O) (y : Y) :
    mass (jointLaw p target obs) (o, y) =
      ∑ k, if obs k = o ∧ target k = y then mass p k else 0 := by
  change mass (p.map (fun k => (obs k, target k))) (o, y) = _
  rw [mass_map_eq_sum]
  apply Finset.sum_congr rfl
  intro k _
  by_cases h : obs k = o ∧ target k = y
  · obtain ⟨ho, hy⟩ := h
    cases ho
    cases hy
    rw [if_pos rfl, if_pos ⟨rfl, rfl⟩]
  · have hpair : (obs k, target k) ≠ (o, y) := by
      intro h'
      exact h ⟨congrArg Prod.fst h', congrArg Prod.snd h'⟩
    rw [if_neg hpair, if_neg h]

private theorem mass_observation_eq_sum {K : Type u} {O : Type w}
    [Fintype K] (p : PMF K) (obs : K → O) (o : O) :
    mass (observationLaw p obs) o = ∑ k, if obs k = o then mass p k else 0 := by
  exact mass_map_eq_sum p obs o

private theorem mass_target_eq_sum {K : Type u} {Y : Type v}
    [Fintype K] (p : PMF K) (target : K → Y) (y : Y) :
    mass (targetLaw p target) y = ∑ k, if target k = y then mass p k else 0 := by
  exact mass_map_eq_sum p target y

private theorem joint_sum_observation {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Fintype Y]
    (p : PMF K) (target : K → Y) (obs : K → O) (o : O) :
    (∑ y, mass (jointLaw p target obs) (o, y)) = mass (observationLaw p obs) o := by
  classical
  calc
    (∑ y, mass (jointLaw p target obs) (o, y)) =
        ∑ y, ∑ k, if obs k = o ∧ target k = y then mass p k else 0 := by
          simp_rw [mass_joint_eq_sum]
    _ = ∑ k, ∑ y, if obs k = o ∧ target k = y then mass p k else 0 := by
      rw [Finset.sum_comm]
    _ = ∑ k, if obs k = o then mass p k else 0 := by
      apply Finset.sum_congr rfl
      intro k _
      by_cases ho : obs k = o
      · rw [if_pos ho]
        calc
          (∑ y, if obs k = o ∧ target k = y then mass p k else 0) =
              ∑ y, if target k = y then mass p k else 0 := by
            apply Finset.sum_congr rfl
            intro y _
            by_cases hy : target k = y
            · rw [if_pos ⟨ho, hy⟩, if_pos hy]
            · rw [if_neg (fun h => hy h.2), if_neg hy]
          _ = mass p k := by simp only [Fintype.sum_ite_eq]
      · rw [if_neg ho]
        apply Finset.sum_eq_zero
        intro y _
        rw [if_neg (fun h => ho h.1)]
    _ = mass (observationLaw p obs) o := (mass_observation_eq_sum p obs o).symm

private theorem joint_sum_target {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Fintype O]
    (p : PMF K) (target : K → Y) (obs : K → O) (y : Y) :
    (∑ o, mass (jointLaw p target obs) (o, y)) = mass (targetLaw p target) y := by
  classical
  calc
    (∑ o, mass (jointLaw p target obs) (o, y)) =
        ∑ o, ∑ k, if obs k = o ∧ target k = y then mass p k else 0 := by
          simp_rw [mass_joint_eq_sum]
    _ = ∑ k, ∑ o, if obs k = o ∧ target k = y then mass p k else 0 := by
      rw [Finset.sum_comm]
    _ = ∑ k, if target k = y then mass p k else 0 := by
      apply Finset.sum_congr rfl
      intro k _
      by_cases hy : target k = y
      · rw [if_pos hy]
        calc
          (∑ o, if obs k = o ∧ target k = y then mass p k else 0) =
              ∑ o, if obs k = o then mass p k else 0 := by
            apply Finset.sum_congr rfl
            intro o _
            by_cases ho : obs k = o
            · rw [if_pos ⟨ho, hy⟩, if_pos ho]
            · rw [if_neg (fun h => ho h.1), if_neg ho]
          _ = mass p k := by simp only [Fintype.sum_ite_eq]
      · rw [if_neg hy]
        apply Finset.sum_eq_zero
        intro o _
        rw [if_neg (fun h => hy h.2)]
    _ = mass (targetLaw p target) y := (mass_target_eq_sum p target y).symm

private theorem measure_fiber_eq_observation {K : Type u} {O : Type w}
    (p : PMF K) (obs : K → O) (o : O) :
    discreteMeasure p (fiber obs o) = (observationLaw p obs) o := by
  classical
  let : MeasurableSpace K := ⊤
  let : MeasurableSpace O := ⊤
  have hmap := PMF.toMeasure_map_apply obs p ({o} : Set O)
    (Measurable.of_discrete) (MeasurableSet.of_discrete)
  calc
    discreteMeasure p (fiber obs o) = p.toMeasure (obs ⁻¹' {o}) := by
      congr 1
    _ = (p.map obs).toMeasure {o} := hmap.symm
    _ = (p.map obs) o := (p.map obs).toMeasure_apply_singleton o
      (MeasurableSet.of_discrete)

private theorem positive_fiber {K : Type u} {O : Type w}
    (p : PMF K) (obs : K → O) (o : O)
    (h : 0 < mass (observationLaw p obs) o) :
    ∃ k ∈ fiber obs o, k ∈ p.support := by
  have hs : o ∈ (p.map obs).support :=
    (mass_pos_iff (observationLaw p obs) o).1 h
  obtain ⟨k, hk, hko⟩ := (PMF.mem_support_map_iff obs p o).1 hs
  exact ⟨k, hko, hk⟩

theorem observationSemantics : FiniteSensorBayes.Raw.ObservationSemanticsTarget.{u, v, w} := by
  classical
  intro K Y O _ _ _ _ _ _ p target obs
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact discrete_map p (fun k => (obs k, target k))
  · exact discrete_map p obs
  · exact discrete_map p target
  · intro o y
    let : MeasurableSpace K := ⊤
    let : MeasurableSpace (O × Y) := ⊤
    have hmap := PMF.toMeasure_map_apply (fun k => (obs k, target k)) p
      ({(o, y)} : Set (O × Y)) (Measurable.of_discrete) (MeasurableSet.of_discrete)
    have hsingle := (p.map fun k => (obs k, target k)).toMeasure_apply_singleton
      (o, y) (MeasurableSet.of_discrete)
    have heq : (p.map fun k => (obs k, target k)) (o, y) =
        p.toMeasure {k | obs k = o ∧ target k = y} := by
      calc
        _ = (p.map fun k => (obs k, target k)).toMeasure {(o, y)} := hsingle.symm
        _ = p.toMeasure ((fun k => (obs k, target k)) ⁻¹' {(o, y)}) := hmap
        _ = p.toMeasure {k | obs k = o ∧ target k = y} := by
          congr 1
          ext k
          simp [Prod.mk.injEq]
    exact congrArg ENNReal.toReal heq
  · intro o y
    exact mass_joint_eq_sum p target obs o y
  · intro o
    exact joint_sum_observation p target obs o
  · intro y
    exact joint_sum_target p target obs y
  · intro o
    constructor
    · rintro ⟨k, hk, hs⟩
      have hobs : o ∈ (observationLaw p obs).support := by
        change o ∈ (p.map obs).support
        exact (PMF.mem_support_map_iff obs p o).2 ⟨k, hs, hk⟩
      exact (mass_pos_iff (observationLaw p obs) o).2 hobs
    · exact positive_fiber p obs o

private theorem joint_support_iff_state {K : Type u} {Y : Type v} {O : Type w}
    (p : PMF K) (target : K → Y) (obs : K → O) (o : O) (y : Y) :
    (o, y) ∈ (jointLaw p target obs).support ↔
      ∃ k ∈ p.support, obs k = o ∧ target k = y := by
  change (o, y) ∈ (p.map (fun k => (obs k, target k))).support ↔ _
  constructor
  · intro h
    obtain ⟨k, hk, hpair⟩ :=
      (PMF.mem_support_map_iff (fun k => (obs k, target k)) p (o, y)).1 h
    exact ⟨k, hk, congrArg Prod.fst hpair, congrArg Prod.snd hpair⟩
  · rintro ⟨k, hk, ho, hy⟩
    apply (PMF.mem_support_map_iff (fun k => (obs k, target k)) p (o, y)).2
    refine ⟨k, hk, ?_⟩
    cases ho
    cases hy
    rfl

private theorem joint_support_observation {K : Type u} {Y : Type v} {O : Type w}
    (p : PMF K) (target : K → Y) (obs : K → O) (o : O) (y : Y)
    (h : (o, y) ∈ (jointLaw p target obs).support) :
    0 < mass (observationLaw p obs) o := by
  obtain ⟨k, hk, hko, _⟩ := (joint_support_iff_state p target obs o y).1 h
  apply (mass_pos_iff (observationLaw p obs) o).2
  change o ∈ (p.map obs).support
  exact (PMF.mem_support_map_iff obs p o).2 ⟨k, hk, hko⟩

private theorem measure_filter_eq_cond {A : Type u} [Fintype A]
    (p : PMF A) (s : Set A) (hs : ∃ a ∈ s, a ∈ p.support) :
    discreteMeasure (p.filter s hs) = ProbabilityTheory.cond (discreteMeasure p) s := by
  classical
  let : MeasurableSpace A := ⊤
  change (p.filter s hs).toMeasure = ProbabilityTheory.cond p.toMeasure s
  apply Measure.ext_of_singleton
  intro a
  rw [(p.filter s hs).toMeasure_apply_singleton a (MeasurableSet.of_discrete)]
  rw [ProbabilityTheory.cond_apply (MeasurableSet.of_discrete)]
  rw [PMF.filter_apply, ← p.toMeasure_apply_eq_tsum s]
  by_cases ha : a ∈ s
  · rw [Set.inter_singleton_of_mem ha,
        p.toMeasure_apply_singleton a (MeasurableSet.of_discrete)]
    simp [Set.indicator_of_mem ha, mul_comm]
  · rw [Set.inter_singleton_of_notMem ha, measure_empty]
    simp [Set.indicator_of_notMem ha]

private theorem posterior_measure_on_positive_fiber
    {K : Type u} {Y : Type v} {O : Type w} [Fintype K]
    (p : PMF K) (target : K → Y) (obs : K → O)
    (fallback : O → PMF Y) (o : O)
    (h : 0 < mass (observationLaw p obs) o) :
    discreteMeasure (posteriorWithFallback p target obs fallback o) =
      conditionalTargetMeasure p target obs o := by
  classical
  let : MeasurableSpace K := ⊤
  let : MeasurableSpace Y := ⊤
  have hs := positive_fiber p obs o h
  have hpost : posteriorWithFallback p target obs fallback o =
      (p.filter (fiber obs o) hs).map target := by
    unfold posteriorWithFallback
    rw [dif_pos hs]
  calc
    discreteMeasure (posteriorWithFallback p target obs fallback o) =
        discreteMeasure ((p.filter (fiber obs o) hs).map target) := by rw [hpost]
    _ = mappedMeasure (p.filter (fiber obs o) hs) target := discrete_map _ _
    _ = conditionalTargetMeasure p target obs o := by
      unfold mappedMeasure conditionalTargetMeasure
      rw [measure_filter_eq_cond]

private theorem posterior_mass_on_positive_fiber
    {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Fintype Y] [Fintype O]
    [Nonempty K] [Nonempty Y] [Nonempty O]
    (p : PMF K) (target : K → Y) (obs : K → O)
    (fallback : O → PMF Y) (o : O) (y : Y)
    (h : 0 < mass (observationLaw p obs) o) :
    mass (posteriorWithFallback p target obs fallback o) y =
      mass (jointLaw p target obs) (o, y) / mass (observationLaw p obs) o := by
  classical
  let : MeasurableSpace K := ⊤
  let : MeasurableSpace Y := ⊤
  have hcoord : (posteriorWithFallback p target obs fallback o) y =
      (discreteMeasure p (fiber obs o))⁻¹ *
        discreteMeasure p {k | obs k = o ∧ target k = y} := by
    calc
      _ = discreteMeasure (posteriorWithFallback p target obs fallback o) {y} :=
        ((posteriorWithFallback p target obs fallback o).toMeasure_apply_singleton y
          (MeasurableSet.of_discrete)).symm
      _ = conditionalTargetMeasure p target obs o {y} :=
        congrArg (fun μ : @Measure Y ⊤ => μ {y})
          (posterior_measure_on_positive_fiber p target obs fallback o h)
      _ = (discreteMeasure p (fiber obs o))⁻¹ *
            discreteMeasure p {k | obs k = o ∧ target k = y} := by
        unfold conditionalTargetMeasure
        rw [Measure.map_apply (Measurable.of_discrete) (MeasurableSet.of_discrete)]
        rw [ProbabilityTheory.cond_apply (MeasurableSet.of_discrete)]
        congr 1
  have hreal := congrArg ENNReal.toReal hcoord
  have hden : (discreteMeasure p (fiber obs o)).toReal =
      mass (observationLaw p obs) o := by
    exact congrArg ENNReal.toReal (measure_fiber_eq_observation p obs o)
  have hnum : (discreteMeasure p {k | obs k = o ∧ target k = y}).toReal =
      mass (jointLaw p target obs) (o, y) := by
    exact ((observationSemantics K Y O p target obs).2.2.2.1 o y).symm
  rw [ENNReal.toReal_mul, ENNReal.toReal_inv] at hreal
  change mass (posteriorWithFallback p target obs fallback o) y =
    (discreteMeasure p (fiber obs o)).toReal⁻¹ *
      (discreteMeasure p {k | obs k = o ∧ target k = y}).toReal at hreal
  rw [hden, hnum] at hreal
  simpa only [div_eq_mul_inv, mul_comm] using hreal

theorem posteriorSemantics : FiniteSensorBayes.Raw.PosteriorSemanticsTarget.{u, v, w} := by
  classical
  intro K Y O _ _ _ _ _ _ p target obs fallback
  have hcoord (o : O) (y : Y)
      (ho : 0 < mass (observationLaw p obs) o) :=
    posterior_mass_on_positive_fiber p target obs fallback o y ho
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro o y hj
    have ho := joint_support_observation p target obs o y
      ((mass_pos_iff (jointLaw p target obs) (o, y)).1 hj)
    rw [hcoord o y ho]
    exact div_pos hj ho
  · intro o ho y
    exact hcoord o y ho
  · intro o ho
    exact posterior_measure_on_positive_fiber p target obs fallback o ho
  · intro o y
    constructor
    · intro hj
      have ho := joint_support_observation p target obs o y hj
      refine ⟨ho, (mass_pos_iff (posteriorWithFallback p target obs fallback o) y).1 ?_⟩
      rw [hcoord o y ho]
      exact div_pos ((mass_pos_iff (jointLaw p target obs) (o, y)).2 hj) ho
    · rintro ⟨ho, hy⟩
      apply (mass_pos_iff (jointLaw p target obs) (o, y)).1
      have hq := (mass_pos_iff (posteriorWithFallback p target obs fallback o) y).2 hy
      rw [hcoord o y ho] at hq
      exact (div_pos_iff_of_pos_right ho).1 hq

private theorem expected_eq_of_support {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Nonempty K] (p : PMF K) (target : K → Y) (obs : K → O)
    (q₁ q₂ : O → PMF Y)
    (h : ∀ k ∈ p.support, q₁ (obs k) = q₂ (obs k)) :
    expectedLogLoss p target obs q₁ = expectedLogLoss p target obs q₂ := by
  classical
  let : MeasurableSpace K := ⊤
  have hsum (q : O → PMF Y) : expectedLogLoss p target obs q =
      ∑ k, mass p k * logLossAt target obs q k := by
    exact (FiniteSensorBayesCandidate.finiteExpectation K p
      (logLossAt target obs q)).2
  rw [hsum q₁, hsum q₂]
  apply Finset.sum_congr rfl
  intro k _
  by_cases hk : k ∈ p.support
  · unfold logLossAt
    rw [h k hk]
  · rw [mass_zero_of_not_support p k hk]
    simp

private theorem posterior_fallback_eq_on_support
    {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Fintype Y] [Fintype O]
    [Nonempty K] [Nonempty Y] [Nonempty O]
    (p : PMF K) (target : K → Y) (obs : K → O)
    (fallback₁ fallback₂ : O → PMF Y) (k : K) (hk : k ∈ p.support) :
    posteriorWithFallback p target obs fallback₁ (obs k) =
      posteriorWithFallback p target obs fallback₂ (obs k) := by
  have ho : 0 < mass (observationLaw p obs) (obs k) := by
    apply (mass_pos_iff (observationLaw p obs) (obs k)).2
    change obs k ∈ (p.map obs).support
    exact (PMF.mem_support_map_iff obs p (obs k)).2 ⟨k, hk, rfl⟩
  have hf := positive_fiber p obs (obs k) ho
  unfold posteriorWithFallback
  rw [dif_pos hf, dif_pos hf]

theorem nullFallbackRisk : FiniteSensorBayes.Raw.NullFallbackRiskTarget.{u, v, w} := by
  classical
  intro K Y O _ _ _ _ _ _ p target obs fallback₁ fallback₂
  have hpoint : ∀ k ∈ p.support,
      posteriorWithFallback p target obs fallback₁ (obs k) =
        posteriorWithFallback p target obs fallback₂ (obs k) := by
    intro k hk
    exact posterior_fallback_eq_on_support p target obs fallback₁ fallback₂ k hk
  refine ⟨hpoint, ?_, ?_⟩
  · exact expected_eq_of_support p target obs _ _ hpoint
  · change expectedLogLoss p target obs (posteriorWithFallback p target obs fallback₁) =
      expectedLogLoss p target obs (posterior p target obs)
    apply expected_eq_of_support
    intro k hk
    exact posterior_fallback_eq_on_support p target obs fallback₁
      (fun _ => targetLaw p target) k hk

theorem admissibilityOnStates :
    FiniteSensorBayes.Raw.AdmissibilityOnStatesTarget.{u, v, w} := by
  classical
  intro K Y O _ _ _ _ _ _ p target obs q
  constructor
  · intro hadm k hk
    apply hadm (obs k) (target k)
    apply (mass_pos_iff (jointLaw p target obs) (obs k, target k)).2
    exact (joint_support_iff_state p target obs (obs k) (target k)).2
      ⟨k, hk, rfl, rfl⟩
  · intro hstate o y hj
    obtain ⟨k, hk, hko, hky⟩ :=
      (joint_support_iff_state p target obs o y).1
        ((mass_pos_iff (jointLaw p target obs) (o, y)).1 hj)
    simpa [hko, hky] using hstate k hk

private theorem weighted_joint_sum {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Fintype Y] [Fintype O]
    (p : PMF K) (target : K → Y) (obs : K → O) (g : O → Y → ℝ) :
    (∑ o, ∑ y, mass (jointLaw p target obs) (o, y) * g o y) =
      ∑ k, mass p k * g (obs k) (target k) := by
  classical
  calc
    (∑ o, ∑ y, mass (jointLaw p target obs) (o, y) * g o y) =
        ∑ o, ∑ y, ∑ k,
          if obs k = o ∧ target k = y then mass p k * g o y else 0 := by
      apply Finset.sum_congr rfl
      intro o _
      apply Finset.sum_congr rfl
      intro y _
      rw [mass_joint_eq_sum, Finset.sum_mul]
      apply Finset.sum_congr rfl
      intro k _
      split_ifs <;> ring
    _ = ∑ o, ∑ k, ∑ y,
          if obs k = o ∧ target k = y then mass p k * g o y else 0 := by
      apply Finset.sum_congr rfl
      intro o _
      rw [Finset.sum_comm]
    _ = ∑ k, ∑ o, ∑ y,
          if obs k = o ∧ target k = y then mass p k * g o y else 0 := by
      rw [Finset.sum_comm]
    _ = ∑ k, mass p k * g (obs k) (target k) := by
      apply Finset.sum_congr rfl
      intro k _
      calc
        (∑ o, ∑ y, if obs k = o ∧ target k = y then
            mass p k * g o y else 0) =
            ∑ o, if obs k = o then
              ∑ y, if target k = y then mass p k * g o y else 0 else 0 := by
          apply Finset.sum_congr rfl
          intro o _
          by_cases ho : obs k = o <;> simp [ho]
        _ = mass p k * g (obs k) (target k) := by
          simp only [Fintype.sum_ite_eq]

private theorem expected_eq_state_and_joint_sum
    {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Fintype Y] [Fintype O]
    [Nonempty K] (p : PMF K) (target : K → Y) (obs : K → O)
    (q : O → PMF Y) :
    expectedLogLoss p target obs q = stateLossSum p target obs q ∧
      expectedLogLoss p target obs q = jointLossSum p target obs q := by
  classical
  let : MeasurableSpace K := ⊤
  have hsum : expectedLogLoss p target obs q =
      ∑ k, mass p k * logLossAt target obs q k :=
    (FiniteSensorBayesCandidate.finiteExpectation K p
      (logLossAt target obs q)).2
  constructor
  · rw [hsum]
    unfold stateLossSum
    apply Finset.sum_congr rfl
    intro k _
    by_cases hk : k ∈ p.support
    · simp [hk]
    · simp [hk, mass_zero_of_not_support p k hk]
  · rw [hsum]
    unfold jointLossSum
    have hmask (o : O) (y : Y) :
        (if (o, y) ∈ (jointLaw p target obs).support then
          mass (jointLaw p target obs) (o, y) * (-Real.log (mass (q o) y)) else 0) =
          mass (jointLaw p target obs) (o, y) * (-Real.log (mass (q o) y)) := by
      by_cases h : (o, y) ∈ (jointLaw p target obs).support
      · simp [h]
      · simp [h, mass_zero_of_not_support (jointLaw p target obs) (o, y) h]
    simp_rw [hmask]
    exact (weighted_joint_sum p target obs
      (fun o y => -Real.log (mass (q o) y))).symm

theorem expectedLossSum : FiniteSensorBayes.Raw.ExpectedLossSumTarget.{u, v, w} := by
  classical
  intro K Y O _ _ _ _ _ _ p target obs q hadm
  let : MeasurableSpace K := ⊤
  have hfinite := FiniteSensorBayesCandidate.finiteExpectation K p
    (logLossAt target obs q)
  have hstate := (admissibilityOnStates K Y O p target obs q).1 hadm
  have hsums := expected_eq_state_and_joint_sum p target obs q
  exact ⟨hfinite.1, hstate, hsums.1, hsums.2⟩

private theorem posterior_support_is_admissible
    {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Fintype Y] [Fintype O]
    [Nonempty K] [Nonempty Y] [Nonempty O]
    (p : PMF K) (target : K → Y) (obs : K → O) (q : O → PMF Y)
    (hadm : Admissible p target obs q) (o : O)
    (ho : 0 < mass (observationLaw p obs) o) :
    ∀ y ∈ (posterior p target obs o).support, 0 < mass (q o) y := by
  intro y hy
  have hr : 0 < mass (posterior p target obs o) y :=
    (mass_pos_iff (posterior p target obs o) y).2 hy
  change 0 < mass
    (posteriorWithFallback p target obs (fun _ => targetLaw p target) o) y at hr
  rw [posterior_mass_on_positive_fiber p target obs
    (fun _ => targetLaw p target) o y ho] at hr
  exact hadm o y ((div_pos_iff_of_pos_right ho).1 hr)

private theorem kl_self_zero {A : Type u} [Fintype A] (r : PMF A) :
    kl r r = 0 := by
  classical
  unfold kl
  apply Finset.sum_eq_zero
  intro a _
  by_cases ha : a ∈ r.support
  · rw [if_pos ha, Real.log_div_self, mul_zero]
  · rw [if_neg ha]

private theorem finite_row_score_decomposition {A : Type u}
    [Fintype A] [Nonempty A] (r q : PMF A)
    (h : ∀ a ∈ r.support, 0 < mass q a) :
    (∑ a, mass r a * (-Real.log (mass q a))) = entropy r + kl r q := by
  classical
  let : MeasurableSpace A := ⊤
  have hint := (FiniteSensorBayesCandidate.finiteExpectation A r
    (fun a => -Real.log (mass q a))).2
  have hscore := (FiniteSensorBayesCandidate.logScore A r q h).1
  exact hint.symm.trans hscore

theorem predictiveKL : FiniteSensorBayes.Raw.PredictiveKLTarget.{u, v, w} := by
  classical
  intro K Y O _ _ _ _ _ _ p target obs q hadm
  constructor
  · unfold FiniteSensorBayes.predictiveKL
    apply Finset.sum_nonneg
    intro o _
    by_cases ho : o ∈ (observationLaw p obs).support
    · rw [if_pos ho]
      have hb : 0 < mass (observationLaw p obs) o :=
        (mass_pos_iff (observationLaw p obs) o).2 ho
      have hsupport := posterior_support_is_admissible p target obs q hadm o hb
      exact mul_nonneg ENNReal.toReal_nonneg
        (FiniteSensorBayesCandidate.gibbs Y (posterior p target obs o) (q o) hsupport)
    · rw [if_neg ho]
  · unfold FiniteSensorBayes.predictiveKL
    apply Finset.sum_eq_zero
    intro o _
    by_cases ho : o ∈ (observationLaw p obs).support
    · rw [if_pos ho, kl_self_zero, mul_zero]
    · rw [if_neg ho]

private theorem joint_mass_eq_posterior_weight
    {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Fintype Y] [Fintype O]
    [Nonempty K] [Nonempty Y] [Nonempty O]
    (p : PMF K) (target : K → Y) (obs : K → O)
    (o : O) (y : Y) (ho : 0 < mass (observationLaw p obs) o) :
    mass (jointLaw p target obs) (o, y) =
      mass (observationLaw p obs) o * mass (posterior p target obs o) y := by
  have hr := posterior_mass_on_positive_fiber p target obs
    (fun _ => targetLaw p target) o y ho
  change mass (posterior p target obs o) y =
    mass (jointLaw p target obs) (o, y) / mass (observationLaw p obs) o at hr
  calc
    mass (jointLaw p target obs) (o, y) =
        (mass (jointLaw p target obs) (o, y) /
          mass (observationLaw p obs) o) * mass (observationLaw p obs) o :=
      (div_mul_cancel₀ _ (ne_of_gt ho)).symm
    _ = mass (observationLaw p obs) o * mass (posterior p target obs o) y := by
      rw [← hr]
      ring

private theorem expected_eq_joint_unmasked
    {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Fintype Y] [Fintype O]
    [Nonempty K] (p : PMF K) (target : K → Y) (obs : K → O)
    (q : O → PMF Y) :
    expectedLogLoss p target obs q =
      ∑ o, ∑ y, mass (jointLaw p target obs) (o, y) *
        (-Real.log (mass (q o) y)) := by
  classical
  let : MeasurableSpace K := ⊤
  calc
    expectedLogLoss p target obs q =
        ∑ k, mass p k * logLossAt target obs q k :=
      (FiniteSensorBayesCandidate.finiteExpectation K p
        (logLossAt target obs q)).2
    _ = ∑ k, mass p k * (-Real.log (mass (q (obs k)) (target k))) := rfl
    _ = ∑ o, ∑ y, mass (jointLaw p target obs) (o, y) *
          (-Real.log (mass (q o) y)) :=
      (weighted_joint_sum p target obs
        (fun o y => -Real.log (mass (q o) y))).symm

private theorem supported_row_score
    {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Fintype Y] [Fintype O]
    [Nonempty K] [Nonempty Y] [Nonempty O]
    (p : PMF K) (target : K → Y) (obs : K → O) (q : O → PMF Y)
    (hadm : Admissible p target obs q) (o : O) :
    (∑ y, mass (jointLaw p target obs) (o, y) *
      (-Real.log (mass (q o) y))) =
      (if o ∈ (observationLaw p obs).support then
        mass (observationLaw p obs) o * entropy (posterior p target obs o) else 0) +
      (if o ∈ (observationLaw p obs).support then
        mass (observationLaw p obs) o * kl (posterior p target obs o) (q o) else 0) := by
  classical
  by_cases ho : o ∈ (observationLaw p obs).support
  · have hb : 0 < mass (observationLaw p obs) o :=
      (mass_pos_iff (observationLaw p obs) o).2 ho
    rw [if_pos ho, if_pos ho]
    calc
      (∑ y, mass (jointLaw p target obs) (o, y) *
          (-Real.log (mass (q o) y))) =
          mass (observationLaw p obs) o *
            ∑ y, mass (posterior p target obs o) y *
              (-Real.log (mass (q o) y)) := by
        rw [Finset.mul_sum]
        apply Finset.sum_congr rfl
        intro y _
        rw [joint_mass_eq_posterior_weight p target obs o y hb]
        ring
      _ = mass (observationLaw p obs) o *
          (entropy (posterior p target obs o) +
            kl (posterior p target obs o) (q o)) := by
        rw [finite_row_score_decomposition (posterior p target obs o) (q o)
          (posterior_support_is_admissible p target obs q hadm o hb)]
      _ = _ := by ring
  · have hz (y : Y) : mass (jointLaw p target obs) (o, y) = 0 := by
      apply mass_zero_of_not_support
      intro hj
      exact ho ((mass_pos_iff (observationLaw p obs) o).1
        (joint_support_observation p target obs o y hj))
    simp [ho, hz]

theorem logScoreDecomposition :
    FiniteSensorBayes.Raw.LogScoreDecompositionTarget.{u, v, w} := by
  classical
  intro K Y O _ _ _ _ _ _ p target obs q hadm
  rw [expected_eq_joint_unmasked p target obs q]
  unfold conditionalEntropy FiniteSensorBayes.predictiveKL
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro o _
  exact supported_row_score p target obs q hadm o

theorem bayesAttainmentMinimality :
    FiniteSensorBayes.Raw.BayesAttainmentMinimalityTarget.{u, v, w} := by
  classical
  intro K Y O _ _ _ _ _ _ p target obs
  have hadm : Admissible p target obs (posterior p target obs) := by
    exact (posteriorSemantics K Y O p target obs
      (fun _ => targetLaw p target)).1
  have hself := (predictiveKL K Y O p target obs
    (posterior p target obs) hadm).2
  have hattain : bayesRisk p target obs = conditionalEntropy p target obs := by
    change expectedLogLoss p target obs (posterior p target obs) = _
    rw [(logScoreDecomposition K Y O p target obs
      (posterior p target obs) hadm), hself, add_zero]
  refine ⟨hadm, hattain, ?_⟩
  intro q hq
  have hdecomp := logScoreDecomposition K Y O p target obs q hq
  have hnonneg := (predictiveKL K Y O p target obs q hq).1
  rw [hattain, hdecomp]
  exact le_add_of_nonneg_right hnonneg

private theorem no_observation_mass_one {K : Type u} [Fintype K] [Nonempty K]
    (p : PMF K) : mass (observationLaw p noObservation) () = 1 := by
  have hsum := (FiniteSensorBayesCandidate.finiteMass Unit
    (observationLaw p noObservation)).2.1
  simpa using hsum

private theorem no_observation_posterior_mass
    {K : Type u} {Y : Type v} [Fintype K] [Fintype Y]
    [Nonempty K] [Nonempty Y] (p : PMF K) (target : K → Y) (y : Y) :
    mass (posterior p target noObservation ()) y = mass (targetLaw p target) y := by
  have hb : 0 < mass (observationLaw p noObservation) () := by
    rw [no_observation_mass_one p]
    norm_num
  have hj := joint_sum_target p target noObservation y
  have hj' : mass (jointLaw p target noObservation) ((), y) =
      mass (targetLaw p target) y := by simpa using hj
  have hp := posterior_mass_on_positive_fiber p target noObservation
    (fun _ => targetLaw p target) () y hb
  rw [no_observation_mass_one p, hj', div_one] at hp
  exact hp

theorem noObservationRisk : FiniteSensorBayes.Raw.NoObservationRiskTarget.{u, v} := by
  classical
  intro K Y _ _ _ _ p target
  have hr := (bayesAttainmentMinimality K Y Unit p target noObservation).2.1
  rw [hr]
  unfold conditionalEntropy
  have hb : () ∈ (observationLaw p noObservation).support :=
    (mass_pos_iff (observationLaw p noObservation) ()).1 (by
      rw [no_observation_mass_one p]
      norm_num)
  simp only [Fintype.sum_unique]
  rw [if_pos hb, no_observation_mass_one p, one_mul]
  unfold entropy
  apply Finset.sum_congr rfl
  intro y _
  have hm := no_observation_posterior_mass p target y
  have hs : y ∈ (posterior p target noObservation ()).support ↔
      y ∈ (targetLaw p target).support := by
    rw [← mass_pos_iff, ← mass_pos_iff, hm]
  by_cases hy : y ∈ (targetLaw p target).support <;> simp [hy, hs, hm]

private theorem target_support_of_joint {K : Type u} {Y : Type v} {O : Type w}
    (p : PMF K) (target : K → Y) (obs : K → O) (o : O) (y : Y)
    (h : (o, y) ∈ (jointLaw p target obs).support) :
    0 < mass (targetLaw p target) y := by
  obtain ⟨k, hk, _, hky⟩ := (joint_support_iff_state p target obs o y).1 h
  apply (mass_pos_iff (targetLaw p target) y).2
  change y ∈ (p.map target).support
  exact (PMF.mem_support_map_iff target p y).2 ⟨k, hk, hky⟩

private theorem base_joint_of_paired_joint
    {K : Type u} {Y : Type v} {O : Type w} {V : Type x}
    (p : PMF K) (target : K → Y) (obs : K → O) (extra : K → V)
    (o : O) (a : V) (y : Y)
    (h : ((o, a), y) ∈
      (jointLaw p target (pairedObservation obs extra)).support) :
    (o, y) ∈ (jointLaw p target obs).support := by
  obtain ⟨k, hk, hpair, hky⟩ :=
    (joint_support_iff_state p target (pairedObservation obs extra) (o, a) y).1 h
  exact (joint_support_iff_state p target obs o y).2
    ⟨k, hk, congrArg Prod.fst hpair, hky⟩

theorem informationDomains :
    FiniteSensorBayes.Raw.InformationDomainsTarget.{u, v, w, x} := by
  classical
  intro K Y O V _ _ _ _ _ _ _ _ p target obs extra
  constructor
  · intro o y hj
    refine ⟨(mass_pos_iff (jointLaw p target obs) (o, y)).2 hj, ?_⟩
    exact mul_pos (joint_support_observation p target obs o y hj)
      (target_support_of_joint p target obs o y hj)
  · intro o a y ht
    have hb := base_joint_of_paired_joint p target obs extra o a y ht
    have hp : 0 < mass (observationLaw p (pairedObservation obs extra)) (o, a) :=
      joint_support_observation p target (pairedObservation obs extra) (o, a) y ht
    refine ⟨mul_pos ((mass_pos_iff _ _).2 ht)
      (joint_support_observation p target obs o y hb), ?_⟩
    exact mul_pos hp ((mass_pos_iff _ _).2 hb)

private theorem entropy_eq_unmasked {A : Type u} [Fintype A]
    (r : PMF A) :
    entropy r = ∑ a, mass r a * (-Real.log (mass r a)) := by
  classical
  unfold entropy
  apply Finset.sum_congr rfl
  intro a _
  by_cases ha : a ∈ r.support
  · simp [ha]
  · rw [if_neg ha, mass_zero_of_not_support r a ha]
    simp

private theorem constant_target_loss_eq_entropy
    {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Fintype Y] [Fintype O]
    [Nonempty K] (p : PMF K) (target : K → Y) (obs : K → O) :
    expectedLogLoss p target obs (fun _ => targetLaw p target) =
      entropy (targetLaw p target) := by
  classical
  rw [expected_eq_joint_unmasked, entropy_eq_unmasked]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro y _
  calc
    (∑ o, mass (jointLaw p target obs) (o, y) *
      -Real.log (mass (targetLaw p target) y)) =
        (∑ o, mass (jointLaw p target obs) (o, y)) *
          -Real.log (mass (targetLaw p target) y) := by rw [Finset.sum_mul]
    _ = _ := by rw [joint_sum_target]

private theorem constant_target_admissible
    {K : Type u} {Y : Type v} {O : Type w}
    (p : PMF K) (target : K → Y) (obs : K → O) :
    Admissible p target obs (fun _ => targetLaw p target) := by
  intro o y hj
  exact target_support_of_joint p target obs o y
    ((mass_pos_iff (jointLaw p target obs) (o, y)).1 hj)

private theorem mutual_information_eq_predictive_kl
    {K : Type u} {Y : Type v} {O : Type w}
    [Fintype K] [Fintype Y] [Fintype O]
    [Nonempty K] [Nonempty Y] [Nonempty O]
    (p : PMF K) (target : K → Y) (obs : K → O) :
    mutualInformation p target obs =
      FiniteSensorBayes.predictiveKL p target obs (fun _ => targetLaw p target) := by
  classical
  unfold mutualInformation FiniteSensorBayes.predictiveKL kl
  apply Finset.sum_congr rfl
  intro o _
  by_cases ho : o ∈ (observationLaw p obs).support
  · rw [if_pos ho, Finset.mul_sum]
    have hb : 0 < mass (observationLaw p obs) o :=
      (mass_pos_iff (observationLaw p obs) o).2 ho
    apply Finset.sum_congr rfl
    intro y _
    have hs := (posteriorSemantics K Y O p target obs
      (fun _ => targetLaw p target)).2.2.2 o y
    by_cases hj : (o, y) ∈ (jointLaw p target obs).support
    · have hy : y ∈ (posterior p target obs o).support :=
        (hs.mp hj).2
      rw [if_pos hj, if_pos hy]
      have hweight := joint_mass_eq_posterior_weight p target obs o y hb
      have hratio : mass (jointLaw p target obs) (o, y) /
          (mass (observationLaw p obs) o * mass (targetLaw p target) y) =
          mass (posterior p target obs o) y / mass (targetLaw p target) y := by
        rw [hweight]
        exact mul_div_mul_left _ _ (ne_of_gt hb)
      rw [hratio, hweight]
      ring
    · have hy : y ∉ (posterior p target obs o).support := by
        intro h
        exact hj (hs.mpr ⟨hb, h⟩)
      simp [hj, hy]
  · rw [if_neg ho]
    have hz (y : Y) : (o, y) ∉ (jointLaw p target obs).support := by
      intro hj
      exact ho ((mass_pos_iff (observationLaw p obs) o).1
        (joint_support_observation p target obs o y hj))
    simp [hz]

theorem mutualInformationGain :
    FiniteSensorBayes.Raw.MutualInformationGainTarget.{u, v, w} := by
  classical
  intro K Y O _ _ _ _ _ _ p target obs
  have hadm := constant_target_admissible p target obs
  have hdecomp := logScoreDecomposition K Y O p target obs
    (fun _ => targetLaw p target) hadm
  have hmi := mutual_information_eq_predictive_kl p target obs
  have hkl := (predictiveKL K Y O p target obs
    (fun _ => targetLaw p target) hadm).1
  have hrisk := (bayesAttainmentMinimality K Y O p target obs).2.1
  have hno := noObservationRisk K Y p target
  have hidentity : mutualInformation p target obs =
      entropy (targetLaw p target) - conditionalEntropy p target obs := by
    rw [hmi]
    rw [constant_target_loss_eq_entropy] at hdecomp
    linarith
  refine ⟨?_, hidentity, ?_⟩
  · rw [hno, hrisk]
    exact hidentity.symm
  · rw [hmi]
    exact hkl

private theorem base_posterior_admissible_for_pair
    {K : Type u} {Y : Type v} {O : Type w} {V : Type x}
    [Fintype K] [Fintype Y] [Fintype O]
    [Nonempty K] [Nonempty Y] [Nonempty O]
    (p : PMF K) (target : K → Y) (obs : K → O) (extra : K → V) :
    Admissible p target (pairedObservation obs extra)
      (fun oa => posterior p target obs oa.1) := by
  intro oa y ht
  obtain ⟨o, a⟩ := oa
  have hj : (o, y) ∈ (jointLaw p target obs).support :=
    base_joint_of_paired_joint p target obs extra o a y
      ((mass_pos_iff _ _).1 ht)
  have hy := ((posteriorSemantics K Y O p target obs
    (fun _ => targetLaw p target)).2.2.2 o y).mp hj
  exact (mass_pos_iff (posterior p target obs o) y).2 hy.2

private theorem conditional_information_eq_predictive_kl
    {K : Type u} {Y : Type v} {O : Type w} {V : Type x}
    [Fintype K] [Fintype Y] [Fintype O] [Fintype V]
    [Nonempty K] [Nonempty Y] [Nonempty O] [Nonempty V]
    (p : PMF K) (target : K → Y) (obs : K → O) (extra : K → V) :
    conditionalMutualInformation p target obs extra =
      FiniteSensorBayes.predictiveKL p target (pairedObservation obs extra)
        (fun oa => posterior p target obs oa.1) := by
  classical
  unfold conditionalMutualInformation FiniteSensorBayes.predictiveKL kl
  rw [Fintype.sum_prod_type]
  apply Finset.sum_congr rfl
  intro o _
  apply Finset.sum_congr rfl
  intro a _
  by_cases hp : (o, a) ∈
      (observationLaw p (pairedObservation obs extra)).support
  · rw [if_pos hp, Finset.mul_sum]
    have hP : 0 < mass (observationLaw p (pairedObservation obs extra)) (o, a) :=
      (mass_pos_iff _ _).2 hp
    apply Finset.sum_congr rfl
    intro y _
    have hs := (posteriorSemantics K Y (O × V) p target
      (pairedObservation obs extra) (fun _ => targetLaw p target)).2.2.2 (o, a) y
    by_cases ht : ((o, a), y) ∈
        (jointLaw p target (pairedObservation obs extra)).support
    · have hy : y ∈
          (posterior p target (pairedObservation obs extra) (o, a)).support :=
        (hs.mp ht).2
      rw [if_pos ht, if_pos hy]
      have hJ : (o, y) ∈ (jointLaw p target obs).support :=
        base_joint_of_paired_joint p target obs extra o a y ht
      have hO : 0 < mass (observationLaw p obs) o :=
        joint_support_observation p target obs o y hJ
      have hweight := joint_mass_eq_posterior_weight p target
        (pairedObservation obs extra) (o, a) y hP
      have hpair := posterior_mass_on_positive_fiber p target
        (pairedObservation obs extra) (fun _ => targetLaw p target)
        (o, a) y hP
      have hbase := posterior_mass_on_positive_fiber p target obs
        (fun _ => targetLaw p target) o y hO
      have hratio :
          (mass (jointLaw p target (pairedObservation obs extra)) ((o, a), y) *
            mass (observationLaw p obs) o) /
            (mass (observationLaw p (pairedObservation obs extra)) (o, a) *
              mass (jointLaw p target obs) (o, y)) =
          mass (posterior p target (pairedObservation obs extra) (o, a)) y /
            mass (posterior p target obs o) y := by
        rw [show mass (posterior p target
          (pairedObservation obs extra) (o, a)) y =
            mass (jointLaw p target (pairedObservation obs extra)) ((o, a), y) /
              mass (observationLaw p (pairedObservation obs extra)) (o, a)
          from hpair]
        rw [show mass (posterior p target obs o) y =
            mass (jointLaw p target obs) (o, y) /
              mass (observationLaw p obs) o from hbase]
        calc
          _ =
              (mass (jointLaw p target (pairedObservation obs extra)) ((o, a), y) /
                mass (observationLaw p (pairedObservation obs extra)) (o, a)) *
                (mass (observationLaw p obs) o /
                  mass (jointLaw p target obs) (o, y)) :=
            (div_mul_div_comm _ _ _ _).symm
          _ =
              (mass (jointLaw p target (pairedObservation obs extra)) ((o, a), y) /
                mass (observationLaw p (pairedObservation obs extra)) (o, a)) *
                (mass (jointLaw p target obs) (o, y) /
                  mass (observationLaw p obs) o)⁻¹ := by rw [inv_div]
          _ = _ := (div_eq_mul_inv _ _).symm
      rw [hratio, hweight]
      ring
    · have hy : y ∉
          (posterior p target (pairedObservation obs extra) (o, a)).support := by
        intro h
        exact ht (hs.mpr ⟨hP, h⟩)
      simp [ht, hy]
  · rw [if_neg hp]
    have hz (y : Y) : ((o, a), y) ∉
        (jointLaw p target (pairedObservation obs extra)).support := by
      intro ht
      exact hp ((mass_pos_iff _ _).1
        (joint_support_observation p target (pairedObservation obs extra)
          (o, a) y ht))
    simp [hz]

private theorem base_posterior_pair_loss_eq_base_risk
    {K : Type u} {Y : Type v} {O : Type w} {V : Type x}
    (p : PMF K) (target : K → Y) (obs : K → O) (extra : K → V) :
    expectedLogLoss p target (pairedObservation obs extra)
      (fun oa => posterior p target obs oa.1) =
      bayesRisk p target obs := by
  rfl

theorem conditionalInformationGain :
    FiniteSensorBayes.Raw.ConditionalInformationGainTarget.{u, v, w, x} := by
  classical
  intro K Y O V _ _ _ _ _ _ _ _ p target obs extra
  have hadm := base_posterior_admissible_for_pair p target obs extra
  have hdecomp := logScoreDecomposition K Y (O × V) p target
    (pairedObservation obs extra) (fun oa => posterior p target obs oa.1) hadm
  have hkl := (predictiveKL K Y (O × V) p target
    (pairedObservation obs extra) (fun oa => posterior p target obs oa.1) hadm).1
  have hcmi := conditional_information_eq_predictive_kl p target obs extra
  have hbase := (bayesAttainmentMinimality K Y O p target obs).2.1
  have hpair := (bayesAttainmentMinimality K Y (O × V) p target
    (pairedObservation obs extra)).2.1
  have hmiBase := (mutualInformationGain K Y O p target obs).2.1
  have hmiPair := (mutualInformationGain K Y (O × V) p target
    (pairedObservation obs extra)).2.1
  have hidentity : conditionalMutualInformation p target obs extra =
      conditionalEntropy p target obs -
        conditionalEntropy p target (pairedObservation obs extra) := by
    rw [hcmi]
    rw [base_posterior_pair_loss_eq_base_risk, hbase] at hdecomp
    linarith
  refine ⟨?_, hidentity, ?_, ?_⟩
  · rw [hbase, hpair]
    exact hidentity.symm
  · linarith
  · rw [hcmi]
    exact hkl

theorem learnedLossGap : FiniteSensorBayes.Raw.LearnedLossGapTarget.{u, v, w, x} := by
  classical
  intro K Y O V _ _ _ _ _ _ _ _ p target baseObs augObs qBase qAug hbase haug
  have hb := logScoreDecomposition K Y O p target baseObs qBase hbase
  have ha := logScoreDecomposition K Y V p target augObs qAug haug
  have hbr := (bayesAttainmentMinimality K Y O p target baseObs).2.1
  have har := (bayesAttainmentMinimality K Y V p target augObs).2.1
  rw [hb, ha, hbr, har]
  ring

end FiniteSensorBayesConditionalCandidate
