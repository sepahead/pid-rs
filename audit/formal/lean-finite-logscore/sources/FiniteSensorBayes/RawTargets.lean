import FiniteSensorBayes.Contract

/-!
Uncompiled, fully quantified owner-side proposition proposal.
Every declaration below DEFINES a Prop; none asserts or proves that proposition.
Intended module after a separately reviewed freeze: FiniteSensorBayes.RawTargets.
The future judge must bind these bodies and Contract.lean, not only export names.
-/

set_option autoImplicit false
open scoped BigOperators Classical ENNReal
open MeasureTheory

universe u v w x

namespace FiniteSensorBayes.Raw

open FiniteSensorBayes

noncomputable section

def FiniteMassTarget : Prop :=
  ∀ (K : Type u) [Fintype K] [Nonempty K] (p : PMF K),
    letI : MeasurableSpace K := ⊤
    IsProbabilityMeasure (discreteMeasure p) ∧
      (∑ k, mass p k) = 1 ∧
      (∀ k, 0 ≤ mass p k ∧ mass p k ≤ 1) ∧
      (∀ k, (0 < mass p k ↔ k ∈ p.support)) ∧
      (∀ k, discreteMeasure p {k} = p k)

def FiniteExpectationTarget : Prop :=
  ∀ (K : Type u) [Fintype K] [Nonempty K] (p : PMF K) (f : K → ℝ),
    letI : MeasurableSpace K := ⊤
    Integrable f (discreteMeasure p) ∧
      (∫ k, f k ∂discreteMeasure p) = ∑ k, mass p k * f k

def ObservationSemanticsTarget : Prop :=
  ∀ (K : Type u) (Y : Type v) (O : Type w)
      [Fintype K] [Fintype Y] [Fintype O]
      [Nonempty K] [Nonempty Y] [Nonempty O]
      (p : PMF K) (target : K → Y) (obs : K → O),
    discreteMeasure (jointLaw p target obs) = mappedMeasure p (fun k => (obs k, target k)) ∧
      discreteMeasure (observationLaw p obs) = mappedMeasure p obs ∧
      discreteMeasure (targetLaw p target) = mappedMeasure p target ∧
      (∀ o y, mass (jointLaw p target obs) (o, y) =
        (discreteMeasure p {k | obs k = o ∧ target k = y}).toReal) ∧
      (∀ o y, mass (jointLaw p target obs) (o, y) =
        ∑ k, if obs k = o ∧ target k = y then mass p k else 0) ∧
      (∀ o, (∑ y, mass (jointLaw p target obs) (o, y)) = mass (observationLaw p obs) o) ∧
      (∀ y, (∑ o, mass (jointLaw p target obs) (o, y)) = mass (targetLaw p target) y) ∧
      (∀ o, (∃ k ∈ fiber obs o, k ∈ p.support) ↔ 0 < mass (observationLaw p obs) o)

def PosteriorSemanticsTarget : Prop :=
  ∀ (K : Type u) (Y : Type v) (O : Type w)
      [Fintype K] [Fintype Y] [Fintype O]
      [Nonempty K] [Nonempty Y] [Nonempty O]
      (p : PMF K) (target : K → Y) (obs : K → O) (fallback : O → PMF Y),
    Admissible p target obs (posteriorWithFallback p target obs fallback) ∧
      (∀ o, 0 < mass (observationLaw p obs) o →
        ∀ y, mass (posteriorWithFallback p target obs fallback o) y =
          mass (jointLaw p target obs) (o, y) / mass (observationLaw p obs) o) ∧
      (∀ o, 0 < mass (observationLaw p obs) o →
        discreteMeasure (posteriorWithFallback p target obs fallback o) =
          conditionalTargetMeasure p target obs o) ∧
      (∀ o y, (o, y) ∈ (jointLaw p target obs).support ↔
        0 < mass (observationLaw p obs) o ∧
          y ∈ (posteriorWithFallback p target obs fallback o).support)

def NullFallbackRiskTarget : Prop :=
  ∀ (K : Type u) (Y : Type v) (O : Type w)
      [Fintype K] [Fintype Y] [Fintype O]
      [Nonempty K] [Nonempty Y] [Nonempty O]
      (p : PMF K) (target : K → Y) (obs : K → O)
      (fallback₁ fallback₂ : O → PMF Y),
    (∀ k ∈ p.support,
      posteriorWithFallback p target obs fallback₁ (obs k) =
        posteriorWithFallback p target obs fallback₂ (obs k)) ∧
      expectedLogLoss p target obs (posteriorWithFallback p target obs fallback₁) =
        expectedLogLoss p target obs (posteriorWithFallback p target obs fallback₂) ∧
      expectedLogLoss p target obs (posteriorWithFallback p target obs fallback₁) =
        bayesRisk p target obs

def AdmissibilityOnStatesTarget : Prop :=
  ∀ (K : Type u) (Y : Type v) (O : Type w)
      [Fintype K] [Fintype Y] [Fintype O]
      [Nonempty K] [Nonempty Y] [Nonempty O]
      (p : PMF K) (target : K → Y) (obs : K → O) (q : O → PMF Y),
    Admissible p target obs q ↔
      ∀ k ∈ p.support, 0 < mass (q (obs k)) (target k)

def ExpectedLossSumTarget : Prop :=
  ∀ (K : Type u) (Y : Type v) (O : Type w)
      [Fintype K] [Fintype Y] [Fintype O]
      [Nonempty K] [Nonempty Y] [Nonempty O]
      (p : PMF K) (target : K → Y) (obs : K → O) (q : O → PMF Y),
    Admissible p target obs q →
      letI : MeasurableSpace K := ⊤
      Integrable (logLossAt target obs q) (discreteMeasure p) ∧
        (∀ k ∈ p.support, 0 < mass (q (obs k)) (target k)) ∧
        expectedLogLoss p target obs q = stateLossSum p target obs q ∧
        expectedLogLoss p target obs q = jointLossSum p target obs q

def GibbsTarget : Prop :=
  ∀ (Y : Type v) [Fintype Y] [Nonempty Y] (r q : PMF Y),
    (∀ y ∈ r.support, 0 < mass q y) → 0 ≤ kl r q

def PredictiveKLTarget : Prop :=
  ∀ (K : Type u) (Y : Type v) (O : Type w)
      [Fintype K] [Fintype Y] [Fintype O]
      [Nonempty K] [Nonempty Y] [Nonempty O]
      (p : PMF K) (target : K → Y) (obs : K → O) (q : O → PMF Y),
    Admissible p target obs q →
      0 ≤ predictiveKL p target obs q ∧
        predictiveKL p target obs (posterior p target obs) = 0

def LogScoreDecompositionTarget : Prop :=
  ∀ (K : Type u) (Y : Type v) (O : Type w)
      [Fintype K] [Fintype Y] [Fintype O]
      [Nonempty K] [Nonempty Y] [Nonempty O]
      (p : PMF K) (target : K → Y) (obs : K → O) (q : O → PMF Y),
    Admissible p target obs q →
      expectedLogLoss p target obs q =
        conditionalEntropy p target obs + predictiveKL p target obs q

def BayesAttainmentMinimalityTarget : Prop :=
  ∀ (K : Type u) (Y : Type v) (O : Type w)
      [Fintype K] [Fintype Y] [Fintype O]
      [Nonempty K] [Nonempty Y] [Nonempty O]
      (p : PMF K) (target : K → Y) (obs : K → O),
    Admissible p target obs (posterior p target obs) ∧
      bayesRisk p target obs = conditionalEntropy p target obs ∧
      (∀ q : O → PMF Y, Admissible p target obs q →
        bayesRisk p target obs ≤ expectedLogLoss p target obs q)

def NoObservationRiskTarget : Prop :=
  ∀ (K : Type u) (Y : Type v)
      [Fintype K] [Fintype Y] [Nonempty K] [Nonempty Y]
      (p : PMF K) (target : K → Y),
    bayesRisk p target noObservation = entropy (targetLaw p target)

/-- Every logarithmic ratio in the independent MI/CMI formulas has positive
numerator and denominator on its selected support. -/
def InformationDomainsTarget : Prop :=
  ∀ (K : Type u) (Y : Type v) (O : Type w) (V : Type x)
      [Fintype K] [Fintype Y] [Fintype O] [Fintype V]
      [Nonempty K] [Nonempty Y] [Nonempty O] [Nonempty V]
      (p : PMF K) (target : K → Y) (obs : K → O) (extra : K → V),
    (∀ o y, (o, y) ∈ (jointLaw p target obs).support →
      0 < mass (jointLaw p target obs) (o, y) ∧
        0 < mass (observationLaw p obs) o * mass (targetLaw p target) y) ∧
      (∀ o a y, ((o, a), y) ∈ (jointLaw p target (pairedObservation obs extra)).support →
        0 < mass (jointLaw p target (pairedObservation obs extra)) ((o, a), y) *
          mass (observationLaw p obs) o ∧
        0 < mass (observationLaw p (pairedObservation obs extra)) (o, a) *
          mass (jointLaw p target obs) (o, y))

def MutualInformationGainTarget : Prop :=
  ∀ (K : Type u) (Y : Type v) (O : Type w)
      [Fintype K] [Fintype Y] [Fintype O]
      [Nonempty K] [Nonempty Y] [Nonempty O]
      (p : PMF K) (target : K → Y) (obs : K → O),
    bayesRisk p target noObservation - bayesRisk p target obs =
      mutualInformation p target obs ∧
      mutualInformation p target obs = entropy (targetLaw p target) -
        conditionalEntropy p target obs ∧
      0 ≤ mutualInformation p target obs

def ConditionalInformationGainTarget : Prop :=
  ∀ (K : Type u) (Y : Type v) (O : Type w) (V : Type x)
      [Fintype K] [Fintype Y] [Fintype O] [Fintype V]
      [Nonempty K] [Nonempty Y] [Nonempty O] [Nonempty V]
      (p : PMF K) (target : K → Y) (obs : K → O) (extra : K → V),
    bayesRisk p target obs - bayesRisk p target (pairedObservation obs extra) =
      conditionalMutualInformation p target obs extra ∧
      conditionalMutualInformation p target obs extra =
        conditionalEntropy p target obs - conditionalEntropy p target (pairedObservation obs extra) ∧
      conditionalMutualInformation p target obs extra =
        mutualInformation p target (pairedObservation obs extra) - mutualInformation p target obs ∧
      0 ≤ conditionalMutualInformation p target obs extra

/-- Both predictors are evaluated on the same p and target. No positivity of
the learned gain, training guarantee, or relation between observation maps is assumed. -/
def LearnedLossGapTarget : Prop :=
  ∀ (K : Type u) (Y : Type v) (O : Type w) (V : Type x)
      [Fintype K] [Fintype Y] [Fintype O] [Fintype V]
      [Nonempty K] [Nonempty Y] [Nonempty O] [Nonempty V]
      (p : PMF K) (target : K → Y) (baseObs : K → O) (augObs : K → V)
      (qBase : O → PMF Y) (qAug : V → PMF Y),
    Admissible p target baseObs qBase → Admissible p target augObs qAug →
      expectedLogLoss p target baseObs qBase - expectedLogLoss p target augObs qAug =
        (bayesRisk p target baseObs - bayesRisk p target augObs) +
          predictiveKL p target baseObs qBase - predictiveKL p target augObs qAug

end

end FiniteSensorBayes.Raw
