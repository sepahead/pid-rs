import Mathlib.Analysis.SpecialFunctions.Log.NegMulLog

/-!
# Deterministic finite-alphabet convergence core

This module proves exact-real lemmas used by a finite-alphabet plug-in convergence argument:

* a sequence with a positive limit is eventually positive;
* a mass over a fixed finite event converges when every cell mass converges;
* a finite event that contains a positive cell has positive mass;
* logarithms and logarithms of ratios converge at positive limits;
* fixed finite linear combinations preserve convergence;
* fixed finite weighted sums preserve convergence;
* finite minima preserve convergence, including at ties; and
* the entropy summand `-x * log x` is continuous, including at zero.

The encoded statements are deterministic. They assume coordinatewise convergence. This module
does not encode an empirical PMF, an i.i.d. sampling model, an almost-sure strong law, the
shared-exclusions event construction, a redundancy lattice, an `I_min` definition, or a Rust
implementation. It therefore does not prove sampling assumptions, a complete categorical PID
theorem, binary64 behavior, or refinement between these definitions and pid-rs code.

Mathlib defines `Real.log` on every real number. The logarithm lemmas below are limit statements.
They do not assert that a finite-sample estimator accepts an early zero mass. The separate
eventual-positivity lemmas establish a positive tail when their assumptions hold.
-/

set_option autoImplicit false
set_option warningAsError true

open Filter
open scoped Topology

namespace PidFiniteConvergence

variable {ι : Type*}

/-- A real sequence that converges to a positive value is eventually positive. -/
theorem eventually_positive_of_tendsto {u : ℕ → ℝ} {x : ℝ}
    (hu : Tendsto u atTop (𝓝 x)) (hx : 0 < x) :
    ∀ᶠ n in atTop, 0 < u n := by
  exact hu.eventually (Ioi_mem_nhds hx)

/-- Coordinatewise convergence gives convergence of the mass of any fixed finite event. -/
theorem tendsto_event_mass (event : Finset ι) {mass : ℕ → ι → ℝ} {limitMass : ι → ℝ}
    (hcoord : ∀ i, Tendsto (fun n => mass n i) atTop (𝓝 (limitMass i))) :
    Tendsto (fun n => ∑ i ∈ event, mass n i) atTop (𝓝 (∑ i ∈ event, limitMass i)) := by
  classical
  induction event using Finset.induction_on with
  | empty => simp
  | @insert i event hi ih =>
      simp only [Finset.sum_insert hi]
      exact (hcoord i).add ih

/-- A finite nonnegative event mass is positive if the event contains a positive cell. -/
theorem event_mass_positive_of_mem {event : Finset ι} {mass : ι → ℝ} {cell : ι}
    (hnonneg : ∀ i, 0 ≤ mass i) (hcell : cell ∈ event) (hpositive : 0 < mass cell) :
    0 < ∑ i ∈ event, mass i := by
  classical
  have hle : mass cell ≤ ∑ i ∈ event, mass i := by
    exact Finset.single_le_sum (fun i _ => hnonneg i) hcell
  exact hpositive.trans_le hle

/-- A convergent finite event mass is eventually positive when its limit contains a positive
cell. -/
theorem event_mass_eventually_positive_of_mem {event : Finset ι} {mass : ℕ → ι → ℝ}
    {limitMass : ι → ℝ} {cell : ι}
    (hcoord : ∀ i, Tendsto (fun n => mass n i) atTop (𝓝 (limitMass i)))
    (hnonneg : ∀ i, 0 ≤ limitMass i) (hcell : cell ∈ event)
    (hpositive : 0 < limitMass cell) :
    ∀ᶠ n in atTop, 0 < ∑ i ∈ event, mass n i := by
  apply eventually_positive_of_tendsto (tendsto_event_mass event hcoord)
  exact event_mass_positive_of_mem hnonneg hcell hpositive

/-- The real logarithm preserves convergence at a positive limit. -/
theorem tendsto_log_of_positive {u : ℕ → ℝ} {x : ℝ}
    (hu : Tendsto u atTop (𝓝 x)) (hx : 0 < x) :
    Tendsto (fun n => Real.log (u n)) atTop (𝓝 (Real.log x)) := by
  exact (Real.continuousAt_log hx.ne').tendsto.comp hu

/-- The negative logarithm preserves convergence at a positive limit. -/
theorem tendsto_neg_log_of_positive {u : ℕ → ℝ} {x : ℝ}
    (hu : Tendsto u atTop (𝓝 x)) (hx : 0 < x) :
    Tendsto (fun n => -Real.log (u n)) atTop (𝓝 (-Real.log x)) := by
  exact (tendsto_log_of_positive hu hx).neg

/-- The entropy summand `-x * log x` preserves convergence. This includes the removable value
zero at `x = 0`. -/
theorem tendsto_neg_mul_log {u : ℕ → ℝ} {x : ℝ}
    (hu : Tendsto u atTop (𝓝 x)) :
    Tendsto (fun n => -u n * Real.log (u n)) atTop (𝓝 (-x * Real.log x)) := by
  change Tendsto (Real.negMulLog ∘ u) atTop (𝓝 (Real.negMulLog x))
  exact Real.continuous_negMulLog.continuousAt.tendsto.comp hu

/-- The entropy summand converges to zero when its argument converges to zero. -/
theorem tendsto_neg_mul_log_zero {u : ℕ → ℝ}
    (hu : Tendsto u atTop (𝓝 0)) :
    Tendsto (fun n => -u n * Real.log (u n)) atTop (𝓝 0) := by
  simpa using tendsto_neg_mul_log hu

/-- The logarithm of a ratio preserves convergence when both limits are positive. -/
theorem tendsto_log_ratio_of_positive {numerator denominator : ℕ → ℝ} {x y : ℝ}
    (hnum : Tendsto numerator atTop (𝓝 x))
    (hden : Tendsto denominator atTop (𝓝 y))
    (hx : 0 < x) (hy : 0 < y) :
    Tendsto (fun n => Real.log (numerator n / denominator n)) atTop
      (𝓝 (Real.log (x / y))) := by
  have hratio : Tendsto (fun n => numerator n / denominator n) atTop (𝓝 (x / y)) :=
    hnum.div hden hy.ne'
  exact tendsto_log_of_positive hratio (div_pos hx hy)

/-- A fixed finite real linear combination preserves coordinatewise convergence. -/
theorem tendsto_finite_linear_combination (indices : Finset ι) {coefficient : ι → ℝ}
    {value : ℕ → ι → ℝ} {limitValue : ι → ℝ}
    (hcoord : ∀ i, Tendsto (fun n => value n i) atTop (𝓝 (limitValue i))) :
    Tendsto (fun n => ∑ i ∈ indices, coefficient i * value n i) atTop
      (𝓝 (∑ i ∈ indices, coefficient i * limitValue i)) := by
  classical
  apply tendsto_event_mass indices
  intro i
  exact tendsto_const_nhds.mul (hcoord i)

/-- A fixed finite weighted sum preserves coordinatewise convergence. A probability-weighted
average is one instance of this result. -/
theorem tendsto_finite_weighted_sum (indices : Finset ι)
    {weight value : ℕ → ι → ℝ} {limitWeight limitValue : ι → ℝ}
    (hweight : ∀ i, Tendsto (fun n => weight n i) atTop (𝓝 (limitWeight i)))
    (hvalue : ∀ i, Tendsto (fun n => value n i) atTop (𝓝 (limitValue i))) :
    Tendsto (fun n => ∑ i ∈ indices, weight n i * value n i) atTop
      (𝓝 (∑ i ∈ indices, limitWeight i * limitValue i)) := by
  classical
  apply tendsto_event_mass indices
  intro i
  exact (hweight i).mul (hvalue i)

/-- The minimum of a fixed nonempty finite list preserves coordinatewise convergence. The list
can contain ties and repeated indices. -/
theorem tendsto_finite_minimum (head : ι) (tail : List ι)
    {value : ℕ → ι → ℝ} {limitValue : ι → ℝ}
    (hcoord : ∀ i, Tendsto (fun n => value n i) atTop (𝓝 (limitValue i))) :
    Tendsto
      (fun n => tail.foldr (fun i minimum => min (value n i) minimum) (value n head))
      atTop
      (𝓝 (tail.foldr (fun i minimum => min (limitValue i) minimum) (limitValue head))) := by
  induction tail with
  | nil => simpa using hcoord head
  | cons i tail ih =>
      simpa only [List.foldr_cons] using (hcoord i).min ih

/-- A finite weighted sum of fixed linear combinations of positive-limit log ratios preserves
convergence. An external finite Möbius transform can supply `coefficient`; no lattice is encoded. -/
theorem tendsto_finite_weighted_log_ratio_linear_combination
    {κ : Type*} [Fintype ι] [Fintype κ] {coefficient : κ → ℝ}
    {weight : ℕ → ι → ℝ} {limitWeight : ι → ℝ}
    {numerator denominator : ℕ → ι → κ → ℝ}
    {limitNumerator limitDenominator : ι → κ → ℝ}
    (hweight : ∀ cell, Tendsto (fun n => weight n cell) atTop (𝓝 (limitWeight cell)))
    (hnumerator : ∀ cell coordinate,
      Tendsto (fun n => numerator n cell coordinate) atTop
        (𝓝 (limitNumerator cell coordinate)))
    (hdenominator : ∀ cell coordinate,
      Tendsto (fun n => denominator n cell coordinate) atTop
        (𝓝 (limitDenominator cell coordinate)))
    (hnumerator_positive : ∀ cell coordinate, 0 < limitNumerator cell coordinate)
    (hdenominator_positive : ∀ cell coordinate, 0 < limitDenominator cell coordinate) :
    Tendsto
      (fun n => ∑ cell, weight n cell *
        ∑ coordinate, coefficient coordinate *
          Real.log (numerator n cell coordinate / denominator n cell coordinate))
      atTop
      (𝓝 (∑ cell, limitWeight cell *
        ∑ coordinate, coefficient coordinate *
          Real.log (limitNumerator cell coordinate / limitDenominator cell coordinate))) := by
  apply tendsto_finite_weighted_sum Finset.univ hweight
  intro cell
  apply tendsto_finite_linear_combination Finset.univ
  intro coordinate
  exact tendsto_log_ratio_of_positive
    (hnumerator cell coordinate) (hdenominator cell coordinate)
    (hnumerator_positive cell coordinate) (hdenominator_positive cell coordinate)

end PidFiniteConvergence
