import FiniteSensorBayes.Contract

/-!
Unadmitted owner-side statement preparation, 23 September 2026.
Intended module name: FiniteSensorBayes.FiniteLogScoreTarget.

This file defines one proposition. It contains no candidate proof and asserts no theorem.
It uses the unchanged native-PMF, measure, entropy and supported-KL definitions in Contract.
No old campaign, target roster or judge is revised by this preparation.
-/

set_option autoImplicit false

open MeasureTheory
open FiniteSensorBayes

universe u

namespace FiniteSensorBayes.LogScoreOwner

noncomputable section

/-- Finite-PMF logarithmic-score decomposition, lower bound and attainment in nats.
The actual measure integral is scored only when q is positive on r's support.
Zero mass of q outside r's support and positive q mass outside that support are allowed.
No extended-real loss claim is made for inadmissible predictors. -/
def FiniteLogScoreTarget : Prop :=
  ∀ (Y : Type u) [Fintype Y] [Nonempty Y] (r q : PMF Y),
    (∀ y ∈ r.support, 0 < mass q y) →
      letI : MeasurableSpace Y := ⊤
      ((∫ y, -Real.log (mass q y) ∂discreteMeasure r) = entropy r + kl r q) ∧
        (entropy r ≤ ∫ y, -Real.log (mass q y) ∂discreteMeasure r) ∧
        ((∫ y, -Real.log (mass r y) ∂discreteMeasure r) = entropy r)

end

end FiniteSensorBayes.LogScoreOwner
