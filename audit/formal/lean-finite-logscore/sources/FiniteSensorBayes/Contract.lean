import Mathlib.Probability.ProbabilityMassFunction.Constructions
import Mathlib.Probability.ProbabilityMassFunction.Integrals
import Mathlib.Probability.ConditionalProbability
import Mathlib.Analysis.SpecialFunctions.Log.Basic

/-!
Uncompiled owner-side definition proposal, 23 September 2026.
Intended module name after a separately reviewed freeze: FiniteSensorBayes.Contract.
This private preparation is neither a candidate proof nor an accepted trusted packet.
There are no theorem declarations in this file. All information units are nats.
Raw targets restrict the law and alphabets to finite nonempty types.
-/

set_option autoImplicit false
open scoped BigOperators Classical ENNReal
open MeasureTheory

universe u v w x

namespace FiniteSensorBayes

noncomputable section

/-- The exact real coordinate of a normalized native PMF. -/
def mass {A : Type u} (p : PMF A) (a : A) : ℝ := (p a).toReal

/-- Fix the discrete sigma-algebra explicitly, without a global instance. -/
def discreteMeasure {A : Type u} (p : PMF A) : @Measure A ⊤ :=
  @PMF.toMeasure A ⊤ p

/-- Actual measure pushforward between the explicitly discrete spaces. -/
def mappedMeasure {A : Type u} {B : Type v} (p : PMF A) (f : A → B) :
    @Measure B ⊤ :=
  letI : MeasurableSpace A := ⊤
  letI : MeasurableSpace B := ⊤
  (discreteMeasure p).map f

def targetLaw {K : Type u} {Y : Type v} (p : PMF K) (target : K → Y) : PMF Y :=
  p.map target

def observationLaw {K : Type u} {O : Type w} (p : PMF K) (obs : K → O) : PMF O :=
  p.map obs

/-- Coordinate order is observation first, target second. -/
def jointLaw {K : Type u} {Y : Type v} {O : Type w}
    (p : PMF K) (target : K → Y) (obs : K → O) : PMF (O × Y) :=
  p.map fun k => (obs k, target k)

def fiber {K : Type u} {O : Type w} (obs : K → O) (o : O) : Set K :=
  {k | obs k = o}

/-- Native normalized restriction followed by target pushforward on a supported fiber.
The arbitrary normalized fallback is used only when that fiber misses the law's support.
Normalization is supplied by Mathlib's PMF.filter, not by a future candidate proof. -/
def posteriorWithFallback {K : Type u} {Y : Type v} {O : Type w}
    (p : PMF K) (target : K → Y) (obs : K → O) (fallback : O → PMF Y)
    (o : O) : PMF Y :=
  if h : ∃ k ∈ fiber obs o, k ∈ p.support then
    (p.filter (fiber obs o) h).map target
  else fallback o

/-- A canonical null-fiber choice: the actual target marginal of the same law. -/
def posterior {K : Type u} {Y : Type v} {O : Type w}
    (p : PMF K) (target : K → Y) (obs : K → O) : O → PMF Y :=
  posteriorWithFallback p target obs (fun _ => targetLaw p target)

/-- Actual target pushforward of Mathlib's conditional measure. Agreement with the
posterior is required only on positive observation fibers; at a null fiber this
conditional measure is zero, whereas the posterior fallback is a probability law. -/
def conditionalTargetMeasure {K : Type u} {Y : Type v} {O : Type w}
    (p : PMF K) (target : K → Y) (obs : K → O) (o : O) : @Measure Y ⊤ :=
  letI : MeasurableSpace K := ⊤
  letI : MeasurableSpace Y := ⊤
  (ProbabilityTheory.cond (discreteMeasure p) (fiber obs o)).map target

/-- Every predictor row is normalized by its PMF type. Positivity is required only
at positive true joint mass, not at all labels or at unreachable observations. -/
def Admissible {K : Type u} {Y : Type v} {O : Type w}
    (p : PMF K) (target : K → Y) (obs : K → O) (q : O → PMF Y) : Prop :=
  ∀ o y, 0 < mass (jointLaw p target obs) (o, y) → 0 < mass (q o) y

/-- Total real formula. Its interpretation as logarithmic prediction loss is
restricted to Admissible predictors in every scoring target. No assertion about
infinite loss or an inadmissible zero prediction is made by this definition. -/
def logLossAt {K : Type u} {Y : Type v} {O : Type w}
    (target : K → Y) (obs : K → O) (q : O → PMF Y) (k : K) : ℝ :=
  -Real.log (mass (q (obs k)) (target k))

/-- Actual PMF.toMeasure expectation, not a renamed finite expression. -/
def expectedLogLoss {K : Type u} {Y : Type v} {O : Type w}
    (p : PMF K) (target : K → Y) (obs : K → O) (q : O → PMF Y) : ℝ :=
  letI : MeasurableSpace K := ⊤
  ∫ k, logLossAt target obs q k ∂discreteMeasure p

def stateLossSum {K : Type u} {Y : Type v} {O : Type w} [Fintype K]
    (p : PMF K) (target : K → Y) (obs : K → O) (q : O → PMF Y) : ℝ :=
  ∑ k, if k ∈ p.support then mass p k * logLossAt target obs q k else 0

def jointLossSum {K : Type u} {Y : Type v} {O : Type w} [Fintype Y] [Fintype O]
    (p : PMF K) (target : K → Y) (obs : K → O) (q : O → PMF Y) : ℝ :=
  ∑ o, ∑ y, if (o, y) ∈ (jointLaw p target obs).support then
    mass (jointLaw p target obs) (o, y) * (-Real.log (mass (q o) y)) else 0

/-- Supported finite Shannon entropy, in nats. -/
def entropy {A : Type u} [Fintype A] (p : PMF A) : ℝ :=
  ∑ a, if a ∈ p.support then -(mass p a * Real.log (mass p a)) else 0

/-- Supported finite KL formula. Its nonnegativity target requires positive q
mass on p.support; values outside that domain are not extended-real KL values. -/
def kl {A : Type u} [Fintype A] (p q : PMF A) : ℝ :=
  ∑ a, if a ∈ p.support then mass p a * Real.log (mass p a / mass q a) else 0

def conditionalEntropy {K : Type u} {Y : Type v} {O : Type w}
    [Fintype Y] [Fintype O] (p : PMF K) (target : K → Y) (obs : K → O) : ℝ :=
  ∑ o, if o ∈ (observationLaw p obs).support then
    mass (observationLaw p obs) o * entropy (posterior p target obs o) else 0

def predictiveKL {K : Type u} {Y : Type v} {O : Type w}
    [Fintype Y] [Fintype O] (p : PMF K) (target : K → Y) (obs : K → O)
    (q : O → PMF Y) : ℝ :=
  ∑ o, if o ∈ (observationLaw p obs).support then
    mass (observationLaw p obs) o * kl (posterior p target obs o) (q o) else 0

/-- Risk of the actual posterior. Attainment and minimality are raw theorem
targets, not assumptions or definitional consequences of the name. -/
def bayesRisk {K : Type u} {Y : Type v} {O : Type w}
    (p : PMF K) (target : K → Y) (obs : K → O) : ℝ :=
  expectedLogLoss p target obs (posterior p target obs)

def noObservation {K : Type u} : K → Unit := fun _ => ()

def pairedObservation {K : Type u} {O : Type w} {V : Type x}
    (obs : K → O) (extra : K → V) : K → O × V := fun k => (obs k, extra k)

/-- Independent joint/marginal-ratio definition, never a risk difference. -/
def mutualInformation {K : Type u} {Y : Type v} {O : Type w}
    [Fintype Y] [Fintype O] (p : PMF K) (target : K → Y) (obs : K → O) : ℝ :=
  ∑ o, ∑ y, if (o, y) ∈ (jointLaw p target obs).support then
    mass (jointLaw p target obs) (o, y) *
      Real.log (mass (jointLaw p target obs) (o, y) /
        (mass (observationLaw p obs) o * mass (targetLaw p target) y))
    else 0

/-- Independent actual triple/marginal-ratio definition. The conditioning
coordinate is obs; extra is the added observation. Triple order is ((o,v),y). -/
def conditionalMutualInformation {K : Type u} {Y : Type v} {O : Type w} {V : Type x}
    [Fintype Y] [Fintype O] [Fintype V]
    (p : PMF K) (target : K → Y) (obs : K → O) (extra : K → V) : ℝ :=
  ∑ o, ∑ a, ∑ y,
    if ((o, a), y) ∈ (jointLaw p target (pairedObservation obs extra)).support then
      mass (jointLaw p target (pairedObservation obs extra)) ((o, a), y) *
        Real.log ((mass (jointLaw p target (pairedObservation obs extra)) ((o, a), y) *
          mass (observationLaw p obs) o) /
          (mass (observationLaw p (pairedObservation obs extra)) (o, a) *
            mass (jointLaw p target obs) (o, y)))
    else 0

end

end FiniteSensorBayes
