import PidPrefixMgwMean.Candidate

/-!
UNEXECUTED SOURCE PROPOSAL against the immutable accepted attempt-017 module closure.
Definitions and complete proposition types only: no theorem proof, axiom, or sorry.
The accepted three-target mean bridge is unchanged. These new targets are unproved.
-/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal Topology
open MeasureTheory
open PidMgwBridgeContract
open PidPrefixProbabilityContract
universe u v w x

namespace PidPrefixMgwBiasSource

/-- Only the domain 0 < q ≤ 1 has the stated logarithmic-tail interpretation. -/
noncomputable def logRemainder (q : ℝ) (h : ℕ) : ℝ :=
  -Real.log q - ∑ n ∈ Finset.range h, (1 - q) ^ (n + 1) / ((n : ℝ) + 1)

/-- Off-support values of f do not contribute or receive a scientific interpretation. -/
noncomputable def supportedAverage {K : Type u} [Fintype K]
    (p f : K → ℝ) : ℝ := by
  classical
  exact ∑ z, if 0 < p z then p z * f z else 0

noncomputable def inverseMoment {K : Type u} [Fintype K]
    (p q : K → ℝ) : ℝ := supportedAverage p (fun z => 1 / q z)

noncomputable def surprisalMoment {K : Type u} [Fintype K]
    (p q : K → ℝ) : ℝ := supportedAverage p (fun z => -Real.log (q z))

noncomputable def positiveSupportCard {K : Type u} [Fintype K]
    (p : K → ℝ) : ℕ := by
  classical
  exact (Finset.univ.filter fun z => 0 < p z).card

noncomputable def fiberMass {K : Type u} {Q : Type v} [Fintype K]
    (p : K → ℝ) (f : K → Q) (y : Q) : ℝ := by
  classical
  exact ∑ z, if f z = y then p z else 0

abbrev scalar_remainder_target : Prop :=
  ∀ (q : ℝ), 0 < q → q ≤ 1 → ∀ h : ℕ,
    HasSum (fun n : ℕ =>
      (1 - q) ^ (n + h + 1) / (((n + h : ℕ) : ℝ) + 1)) (logRemainder q h) ∧
    0 ≤ logRemainder q h ∧
    logRemainder q h ≤ -Real.log q ∧
    logRemainder q h ≤ (1 - q) ^ (h + 1) / (((h : ℝ) + 1) * q) ∧
    logRemainder q h ≤ (1 / q - 1) / ((h : ℝ) + 1)

abbrev scalar_difference_remainder_target : Prop :=
  ∀ (q v : ℝ), 0 < q → q ≤ v → v ≤ 1 → ∀ h : ℕ,
    0 ≤ logRemainder q h - logRemainder v h ∧
    logRemainder q h - logRemainder v h ≤
      ((1 - q) ^ (h + 1) / q - (1 - v) ^ (h + 1) / v) / ((h : ℝ) + 1) ∧
    logRemainder q h - logRemainder v h ≤
      (1 / q - 1 / v) / ((h : ℝ) + 1)

/-- Generic new envelope; no total-mass-less-than-one assumption is needed. -/
abbrev join_power_coordinate_envelope_target : Prop :=
  ∀ (L : Type u) [Fintype L] [SemilatticeSup L] [DecidableEq L] [DecidableLE L]
      (weight : L → ℝ),
    (∀ a, 0 ≤ weight a) → ∀ (n : ℕ) (a : L),
      0 ≤ PidJoinLogContract.joinPower weight n a ∧
      PidJoinLogContract.joinPower weight n a ≤
        PidJoinLogContract.cumulative weight a ^ (n + 1)

/-- Generic finite partition identity used for practical support-cardinality bounds. -/
abbrev fiber_inverse_moment_target : Prop :=
  ∀ (K : Type u) (Q : Type v) [Fintype K] [Fintype Q]
      (p : K → ℝ) (f : K → Q),
    Law p →
      inverseMoment p (fun z => fiberMass p f (f z)) =
        (positiveSupportCard (fiberMass p f) : ℝ)

section Categorical
variable {I : Type u} {X : I → Type v} {T : Type w}
variable [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
variable [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]

local instance keySpace : MeasurableSpace (Key I X T) := ⊤

noncomputable def positiveMeanIncrement (p : Key I X T → ℝ) (z : Key I X T)
    (alpha : Node I) (n : ℕ) : ℝ :=
  wordCoefficient p z alpha (n + 1) / ((n : ℝ) + 1)

/-- Exact raw-time/retained-rank expression from the accepted contract. -/
noncomputable def negativeMeanIncrement (p : Key I X T → ℝ) (z : Key I X T)
    (alpha : Node I) (n : ℕ) : ℝ :=
  ∑ k ∈ Finset.range (n + 1),
    (Nat.choose n k : ℝ) * (targetMass p z) ^ (k + 1) *
      (1 - targetMass p z) ^ (n - k) *
      wordCoefficient (conditioned p z) z alpha (k + 1) / ((k : ℝ) + 1)

noncomputable def positiveMeanPartial (p : Key I X T → ℝ) (z : Key I X T)
    (alpha : Node I) (h : ℕ) : ℝ :=
  ∑ n ∈ Finset.range h, positiveMeanIncrement p z alpha n

noncomputable def negativeMeanPartial (p : Key I X T → ℝ) (z : Key I X T)
    (alpha : Node I) (h : ℕ) : ℝ :=
  ∑ n ∈ Finset.range h, negativeMeanIncrement p z alpha n

noncomputable def actualBlockMean (p : Key I X T → ℝ) (alpha : Node I) (h : ℕ) : ℝ :=
  ∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1)

noncomputable def jointAtomMean (p : Key I X T → ℝ)
    (plus minus : Key I X T → Node I → ℝ) (alpha : Node I) : ℝ :=
  ∑ z, p z * (plus z alpha - minus z alpha)

noncomputable def positiveEnvelope (p : Key I X T → ℝ) (alpha : Node I) (h : ℕ) : ℝ :=
  supportedAverage p (fun z => logRemainder (sourceMass p z alpha) h)

noncomputable def negativeEnvelope (p : Key I X T → ℝ) (alpha : Node I) (h : ℕ) : ℝ :=
  supportedAverage p (fun z =>
    logRemainder (restrictedMass p z alpha) h - logRemainder (targetMass p z) h)

noncomputable def queryMoment (p : Key I X T → ℝ) (alpha : Node I) : ℝ :=
  inverseMoment p (fun z => restrictedMass p z alpha)

noncomputable def sourceMoment (p : Key I X T → ℝ) (alpha : Node I) : ℝ :=
  inverseMoment p (fun z => sourceMass p z alpha)

noncomputable def targetMoment (p : Key I X T → ℝ) : ℝ :=
  inverseMoment p (targetMass p)

noncomputable def querySurprisal (p : Key I X T → ℝ) (alpha : Node I) : ℝ :=
  surprisalMoment p (fun z => restrictedMass p z alpha)

noncomputable def SupportedInversePair (p : Key I X T → ℝ)
    (plus minus : Key I X T → Node I → ℝ) : Prop :=
  (∀ z, p z = 0 → plus z = 0 ∧ minus z = 0) ∧
  (∀ z, 0 < p z →
    InfInverse p z (plus z) ∧ MisInverse p z (minus z) ∧
    (∀ other : Node I → ℝ, InfInverse p z other → other = plus z) ∧
    (∀ other : Node I → ℝ, MisInverse p z other → other = minus z))

abbrev CollectionValue (C : Finset I) := (i : {i // i ∈ C}) → X i.val

def sourceProjection (C : Finset I) (z : Key I X T) : CollectionValue (X := X) C :=
  fun i => z.1 i.val

def jointProjection (C : Finset I) (z : Key I X T) : CollectionValue (X := X) C × T :=
  (sourceProjection C z, z.2)

end Categorical

abbrev word_coordinate_envelope_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (n : ℕ),
    Law p →
      0 ≤ wordCoefficient p z alpha (n + 1) ∧
      wordCoefficient p z alpha (n + 1) ≤ (1 - sourceMass p z alpha) ^ (n + 1)

abbrev raw_increment_envelopes_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (n : ℕ),
    Law p → 0 < p z →
      0 ≤ positiveMeanIncrement p z alpha n ∧
      positiveMeanIncrement p z alpha n ≤
        (1 - sourceMass p z alpha) ^ (n + 1) / ((n : ℝ) + 1) ∧
      0 ≤ negativeMeanIncrement p z alpha n ∧
      negativeMeanIncrement p z alpha n ≤
        ((1 - restrictedMass p z alpha) ^ (n + 1) -
          (1 - targetMass p z) ^ (n + 1)) / ((n : ℝ) + 1)

abbrev finite_horizon_increment_bounds_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (h m : ℕ),
    Law p → 0 < p z → h ≤ m →
      0 ≤ positiveMeanPartial p z alpha m - positiveMeanPartial p z alpha h ∧
      positiveMeanPartial p z alpha m - positiveMeanPartial p z alpha h ≤
        logRemainder (sourceMass p z alpha) h - logRemainder (sourceMass p z alpha) m ∧
      0 ≤ negativeMeanPartial p z alpha m - negativeMeanPartial p z alpha h ∧
      negativeMeanPartial p z alpha m - negativeMeanPartial p z alpha h ≤
        (logRemainder (restrictedMass p z alpha) h - logRemainder (targetMass p z) h) -
          (logRemainder (restrictedMass p z alpha) m - logRemainder (targetMass p z) m)

/-- Main end-to-end target: inverse families and bias bounds are conclusions. -/
abbrev actual_finite_bias_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ),
    Law p → ∃ plus minus : Key I X T → Node I → ℝ,
      SupportedInversePair p plus minus ∧
      (∀ z, 0 < p z → ∀ (alpha : Node I) (h : ℕ),
        0 ≤ plus z alpha - positiveMeanPartial p z alpha h ∧
        plus z alpha - positiveMeanPartial p z alpha h ≤
          logRemainder (sourceMass p z alpha) h ∧
        0 ≤ minus z alpha - negativeMeanPartial p z alpha h ∧
        minus z alpha - negativeMeanPartial p z alpha h ≤
          logRemainder (restrictedMass p z alpha) h - logRemainder (targetMass p z) h) ∧
      (∀ (alpha : Node I) (h : ℕ),
        actualBlockMean p alpha h = supportedAverage p (fun z =>
          positiveMeanPartial p z alpha h - negativeMeanPartial p z alpha h) ∧
        -negativeEnvelope p alpha h ≤ jointAtomMean p plus minus alpha - actualBlockMean p alpha h ∧
        jointAtomMean p plus minus alpha - actualBlockMean p alpha h ≤ positiveEnvelope p alpha h ∧
        |jointAtomMean p plus minus alpha - actualBlockMean p alpha h| ≤
          max (positiveEnvelope p alpha h) (negativeEnvelope p alpha h) ∧
        |jointAtomMean p plus minus alpha - actualBlockMean p alpha h| ≤
          supportedAverage p (fun z => logRemainder (restrictedMass p z alpha) h) ∧
        |jointAtomMean p plus minus alpha - actualBlockMean p alpha h| ≤
          min (querySurprisal p alpha) ((queryMoment p alpha - 1) / ((h : ℝ) + 1)) ∧
        -(queryMoment p alpha - targetMoment p) / ((h : ℝ) + 1) ≤
          jointAtomMean p plus minus alpha - actualBlockMean p alpha h ∧
        jointAtomMean p plus minus alpha - actualBlockMean p alpha h ≤
          (sourceMoment p alpha - 1) / ((h : ℝ) + 1))

abbrev support_moment_bounds_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (alpha : Node I),
    Law p →
      1 ≤ sourceMoment p alpha ∧ sourceMoment p alpha ≤ queryMoment p alpha ∧
      targetMoment p = (positiveSupportCard (fiberMass p (fun z : Key I X T => z.2)) : ℝ) ∧
      1 ≤ targetMoment p ∧ targetMoment p ≤ queryMoment p alpha ∧
      queryMoment p alpha ≤ (positiveSupportCard p : ℝ) ∧
      (∀ C ∈ alpha.val,
        sourceMoment p alpha ≤
          (positiveSupportCard (fiberMass p (sourceProjection (X := X) (T := T) C)) : ℝ) ∧
        queryMoment p alpha ≤
          (positiveSupportCard (fiberMass p (jointProjection (X := X) (T := T) C)) : ℝ))

abbrev mass_floor_bias_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (plus minus : Key I X T → Node I → ℝ)
      (alpha : Node I) (eta : ℝ),
    Law p → SupportedInversePair p plus minus → 0 < eta → eta ≤ 1 →
    (∀ z, 0 < p z → eta ≤ restrictedMass p z alpha) → ∀ h : ℕ,
      |jointAtomMean p plus minus alpha - actualBlockMean p alpha h| ≤ logRemainder eta h ∧
      |jointAtomMean p plus minus alpha - actualBlockMean p alpha h| ≤
        (1 - eta) ^ (h + 1) / (((h : ℝ) + 1) * eta)

abbrev projected_support_bias_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (plus minus : Key I X T → Node I → ℝ)
      (alpha : Node I) (C : Finset I),
    Law p → SupportedInversePair p plus minus → C ∈ alpha.val → ∀ h : ℕ,
      -((positiveSupportCard (fiberMass p (jointProjection (X := X) (T := T) C)) : ℝ) -
          (positiveSupportCard (fiberMass p (fun z : Key I X T => z.2)) : ℝ)) /
          ((h : ℝ) + 1) ≤
        jointAtomMean p plus minus alpha - actualBlockMean p alpha h ∧
      jointAtomMean p plus minus alpha - actualBlockMean p alpha h ≤
        ((positiveSupportCard (fiberMass p (sourceProjection (X := X) (T := T) C)) : ℝ) - 1) /
          ((h : ℝ) + 1) ∧
      |jointAtomMean p plus minus alpha - actualBlockMean p alpha h| ≤
        ((positiveSupportCard (fiberMass p (jointProjection (X := X) (T := T) C)) : ℝ) - 1) /
          ((h : ℝ) + 1)

end PidPrefixMgwBiasSource
