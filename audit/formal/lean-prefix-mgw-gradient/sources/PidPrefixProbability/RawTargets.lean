import PidPrefixProbability.Contract

/-! Independent complete proposition view. These are types, not proofs. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal
open MeasureTheory
open PidMgwBridgeContract (Key Node Law targetMass conditioned)
open PidPrefixProbabilityContract
universe u v w
namespace PidPrefixProbabilityRawTargets

local instance keySpace {I : Type u} {X : I → Type v} {T : Type w} :
    MeasurableSpace (Key I X T) := ⊤

def finite_law_measure : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ),
    ((∀ x, 0 ≤ mass x) ∧ PidMgwBridgeContract.total mass = 1) →
      IsProbabilityMeasure (keyMeasure mass) ∧
      (∀ x, keyMeasure mass {x} = ENNReal.ofReal (mass x)) ∧
      ∀ observable : Key I X T → ℝ,
        Integrable observable (keyMeasure mass) ∧
          (∫ x, observable x ∂keyMeasure mass) = ∑ x, mass x * observable x

def finite_product_law : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (count : ℕ),
    ((∀ x, 0 ≤ mass x) ∧ PidMgwBridgeContract.total mass = 1) →
      IsProbabilityMeasure (rowLaw mass count) ∧
      (∀ word, rowLaw mass count {word} = ENNReal.ofReal (∏ i, mass (word i))) ∧
      ∀ observable : (Fin count → Key I X T) → ℝ,
        Integrable observable (rowLaw mass count) ∧
          (∫ word, observable word ∂rowLaw mass count) =
            ∑ word, (∏ i, mass (word i)) * observable word

def positive_increment_expectation : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (anchor : Key I X T) (query : Node I) (n : ℕ),
    ((∀ x, 0 ≤ mass x) ∧ PidMgwBridgeContract.total mass = 1) →
      (∫ rows, positiveOnPrefix anchor query (List.ofFn rows) ∂rowLaw mass (n + 1)) =
        wordCoefficient mass anchor query (n + 1) / ((n : ℝ) + 1)

def negative_increment_expectation : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (anchor : Key I X T) (query : Node I) (n : ℕ),
    ((∀ x, 0 ≤ mass x) ∧ PidMgwBridgeContract.total mass = 1) →
      0 < targetMass mass anchor →
      (∫ rows, negativeOnPrefix anchor query (List.ofFn rows) ∂rowLaw mass (n + 1)) =
        ∑ k ∈ Finset.range (n + 1),
          (Nat.choose n k : ℝ) * (targetMass mass anchor) ^ (k + 1) *
            (1 - targetMass mass anchor) ^ (n - k) *
            wordCoefficient (conditioned mass anchor) anchor query (k + 1) /
              ((k : ℝ) + 1)

def block_range : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (query : Node I) (h : ℕ) (block : Fin (h + 1) → Key I X T),
    -harmonic h ≤ blockStatistic query h block ∧ blockStatistic query h block ≤ harmonic h

def block_product_independence : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (query : Node I) (B h : ℕ),
    ((∀ x, 0 ≤ mass x) ∧ PidMgwBridgeContract.total mass = 1) →
      IsProbabilityMeasure (experimentLaw mass B h) ∧
      (∀ b : Fin B,
        (experimentLaw mass B h).map (blockProjection B h b) = rowLaw mass (h + 1)) ∧
      (∀ b : Fin B, Measurable (sampleStatistic (X := X) (T := T) query B h b)) ∧
      (∀ b : Fin B, Integrable (sampleStatistic query B h b) (experimentLaw mass B h)) ∧
      ProbabilityTheory.iIndepFun (sampleStatistic query B h) (experimentLaw mass B h)

end PidPrefixProbabilityRawTargets
