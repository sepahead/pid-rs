import PidPrefixMgwBias.Contract

/-! Complete closed proposition views. These repeat every quantifier and conclusion,
expand Law and the supported inverse pair, and expose the native integral and joint mean.
They are definitions only and supply no bias proof. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal Topology
open MeasureTheory
open PidMgwBridgeContract PidPrefixProbabilityContract PidPrefixMgwBiasSource
universe u v w
namespace PidPrefixMgwBiasRawTargets
local instance keySpace {I : Type u} {X : I → Type v} {T : Type w} :
    MeasurableSpace (Key I X T) := ⊤
noncomputable local instance propositionDecidable (P : Prop) : Decidable P := Classical.propDecidable P

def actual_finite_bias : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ),
    ((∀ z, 0 ≤ p z) ∧ PidMgwBridgeContract.total p = 1) → ∃ plus minus : Key I X T → Node I → ℝ,
      ((∀ z, p z = 0 → plus z = 0 ∧ minus z = 0) ∧
      (∀ z, 0 < p z →
        (∀ beta, cumulative (plus z) beta = -Real.log (sourceMass p z beta)) ∧
        (∀ beta, cumulative (minus z) beta = Real.log (targetMass p z / restrictedMass p z beta)) ∧
        (∀ other : Node I → ℝ,
          (∀ beta, cumulative other beta = -Real.log (sourceMass p z beta)) → other = plus z) ∧
        (∀ other : Node I → ℝ,
          (∀ beta, cumulative other beta = Real.log (targetMass p z / restrictedMass p z beta)) → other = minus z))) ∧
      (∀ z, 0 < p z → ∀ (alpha : Node I) (h : ℕ),
        0 ≤ plus z alpha - positiveMeanPartial p z alpha h ∧
        plus z alpha - positiveMeanPartial p z alpha h ≤
          logRemainder (sourceMass p z alpha) h ∧
        0 ≤ minus z alpha - negativeMeanPartial p z alpha h ∧
        minus z alpha - negativeMeanPartial p z alpha h ≤
          logRemainder (restrictedMass p z alpha) h - logRemainder (targetMass p z) h) ∧
      (∀ (alpha : Node I) (h : ℕ),
        (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1)) = supportedAverage p (fun z =>
          positiveMeanPartial p z alpha h - negativeMeanPartial p z alpha h) ∧
        -negativeEnvelope p alpha h ≤ (∑ z, p z * (plus z alpha - minus z alpha)) - (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1)) ∧
        (∑ z, p z * (plus z alpha - minus z alpha)) - (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1)) ≤ positiveEnvelope p alpha h ∧
        |(∑ z, p z * (plus z alpha - minus z alpha)) - (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1))| ≤
          max (positiveEnvelope p alpha h) (negativeEnvelope p alpha h) ∧
        |(∑ z, p z * (plus z alpha - minus z alpha)) - (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1))| ≤
          supportedAverage p (fun z => logRemainder (restrictedMass p z alpha) h) ∧
        |(∑ z, p z * (plus z alpha - minus z alpha)) - (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1))| ≤
          min (querySurprisal p alpha) ((queryMoment p alpha - 1) / ((h : ℝ) + 1)) ∧
        -(queryMoment p alpha - targetMoment p) / ((h : ℝ) + 1) ≤
          (∑ z, p z * (plus z alpha - minus z alpha)) - (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1)) ∧
        (∑ z, p z * (plus z alpha - minus z alpha)) - (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1)) ≤
          (sourceMoment p alpha - 1) / ((h : ℝ) + 1))

def fiber_inverse_moment : Prop :=
  ∀ (K : Type u) (Q : Type v) [Fintype K] [Fintype Q]
      (p : K → ℝ) (f : K → Q),
    ((∀ z, 0 ≤ p z) ∧ PidMgwBridgeContract.total p = 1) →
      inverseMoment p (fun z => fiberMass p f (f z)) =
        (positiveSupportCard (fiberMass p f) : ℝ)

def support_moment_bounds : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (alpha : Node I),
    ((∀ z, 0 ≤ p z) ∧ PidMgwBridgeContract.total p = 1) →
      1 ≤ sourceMoment p alpha ∧ sourceMoment p alpha ≤ queryMoment p alpha ∧
      targetMoment p = (positiveSupportCard (fiberMass p (fun z : Key I X T => z.2)) : ℝ) ∧
      1 ≤ targetMoment p ∧ targetMoment p ≤ queryMoment p alpha ∧
      queryMoment p alpha ≤ (positiveSupportCard p : ℝ) ∧
      (∀ C ∈ alpha.val,
        sourceMoment p alpha ≤
          (positiveSupportCard (fiberMass p (sourceProjection (X := X) (T := T) C)) : ℝ) ∧
        queryMoment p alpha ≤
          (positiveSupportCard (fiberMass p (jointProjection (X := X) (T := T) C)) : ℝ))

def projected_support_bias : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (plus minus : Key I X T → Node I → ℝ)
      (alpha : Node I) (C : Finset I),
    ((∀ z, 0 ≤ p z) ∧ PidMgwBridgeContract.total p = 1) → ((∀ z, p z = 0 → plus z = 0 ∧ minus z = 0) ∧
      (∀ z, 0 < p z →
        (∀ beta, cumulative (plus z) beta = -Real.log (sourceMass p z beta)) ∧
        (∀ beta, cumulative (minus z) beta = Real.log (targetMass p z / restrictedMass p z beta)) ∧
        (∀ other : Node I → ℝ,
          (∀ beta, cumulative other beta = -Real.log (sourceMass p z beta)) → other = plus z) ∧
        (∀ other : Node I → ℝ,
          (∀ beta, cumulative other beta = Real.log (targetMass p z / restrictedMass p z beta)) → other = minus z))) → C ∈ alpha.val → ∀ h : ℕ,
      -((positiveSupportCard (fiberMass p (jointProjection (X := X) (T := T) C)) : ℝ) -
          (positiveSupportCard (fiberMass p (fun z : Key I X T => z.2)) : ℝ)) /
          ((h : ℝ) + 1) ≤
        (∑ z, p z * (plus z alpha - minus z alpha)) - (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1)) ∧
      (∑ z, p z * (plus z alpha - minus z alpha)) - (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1)) ≤
        ((positiveSupportCard (fiberMass p (sourceProjection (X := X) (T := T) C)) : ℝ) - 1) /
          ((h : ℝ) + 1) ∧
      |(∑ z, p z * (plus z alpha - minus z alpha)) - (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1))| ≤
        ((positiveSupportCard (fiberMass p (jointProjection (X := X) (T := T) C)) : ℝ) - 1) /
          ((h : ℝ) + 1)

def mass_floor_bias : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (plus minus : Key I X T → Node I → ℝ)
      (alpha : Node I) (eta : ℝ),
    ((∀ z, 0 ≤ p z) ∧ PidMgwBridgeContract.total p = 1) → ((∀ z, p z = 0 → plus z = 0 ∧ minus z = 0) ∧
      (∀ z, 0 < p z →
        (∀ beta, cumulative (plus z) beta = -Real.log (sourceMass p z beta)) ∧
        (∀ beta, cumulative (minus z) beta = Real.log (targetMass p z / restrictedMass p z beta)) ∧
        (∀ other : Node I → ℝ,
          (∀ beta, cumulative other beta = -Real.log (sourceMass p z beta)) → other = plus z) ∧
        (∀ other : Node I → ℝ,
          (∀ beta, cumulative other beta = Real.log (targetMass p z / restrictedMass p z beta)) → other = minus z))) → 0 < eta → eta ≤ 1 →
    (∀ z, 0 < p z → eta ≤ restrictedMass p z alpha) → ∀ h : ℕ,
      |(∑ z, p z * (plus z alpha - minus z alpha)) - (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1))| ≤ logRemainder eta h ∧
      |(∑ z, p z * (plus z alpha - minus z alpha)) - (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1))| ≤
        (1 - eta) ^ (h + 1) / (((h : ℝ) + 1) * eta)

end PidPrefixMgwBiasRawTargets
