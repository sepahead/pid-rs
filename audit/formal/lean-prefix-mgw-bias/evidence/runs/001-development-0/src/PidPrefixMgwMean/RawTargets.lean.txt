import PidPrefixMgwMean.Contract

/-! SOURCE-ONLY PROPOSAL. These are complete proposition types, not proofs.
No type elaboration or new target execution has occurred in this preparation. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal Topology
open MeasureTheory
open PidMgwBridgeContract
open PidPrefixProbabilityContract
universe u v w
namespace PidPrefixMgwMeanRawTargets

local instance keySpace {I : Type u} {X : I → Type v} {T : Type w} :
    MeasurableSpace (Key I X T) := ⊤

noncomputable local instance propositionDecidable (P : Prop) : Decidable P := Classical.propDecidable P

def word_coefficient_join_power : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (r : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (n : ℕ)
      (sigma : SemilatticeSup (Node I)),
    ((∀ a b : Node I, sigma.le a b ↔ rawLE a.val b.val) ∧
      (∀ a b : Node I, (sigma.sup a b).val = rawJoin a.val b.val)) →
      wordCoefficient r z alpha (n + 1) =
        @PidJoinLogContract.joinPower (Node I) (nodeFintype I) sigma
          (Classical.decEq (Node I)) (weights r z) n alpha

def finite_block_expectation : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (alpha : Node I) (h : ℕ),
    ((∀ x, 0 ≤ p x) ∧ PidMgwBridgeContract.total p = 1) →
      Integrable (blockStatistic alpha h) (rowLaw p (h + 1)) ∧
      (∀ (z : Key I X T) (n : ℕ),
        Integrable (fun rows => positiveOnPrefix z alpha (List.ofFn rows))
          (rowLaw p (n + 1)) ∧
        Integrable (fun rows => negativeOnPrefix z alpha (List.ofFn rows))
          (rowLaw p (n + 1))) ∧
      ((∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1)) =
        ∑ z, p z * ∑ n ∈ Finset.range h,
          ((∫ rows, positiveOnPrefix z alpha (List.ofFn rows) ∂rowLaw p (n + 1)) -
            (∫ rows, negativeOnPrefix z alpha (List.ofFn rows) ∂rowLaw p (n + 1)))) ∧
      ((∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1)) =
        ∑ z, p z * (if 0 < p z then
          ∑ n ∈ Finset.range h,
            (wordCoefficient p z alpha (n + 1) / ((n : ℝ) + 1) -
              ∑ k ∈ Finset.range (n + 1),
                (Nat.choose n k : ℝ) * (targetMass p z) ^ (k + 1) *
                  (1 - targetMass p z) ^ (n - k) *
                  wordCoefficient (conditioned p z) z alpha (k + 1) / ((k : ℝ) + 1))
          else 0))

def prefix_expectations_to_mgw_mean : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ),
    ((∀ x, 0 ≤ p x) ∧ PidMgwBridgeContract.total p = 1) →
      ∃ plus minus : Key I X T → Node I → ℝ,
        (∀ z, p z = 0 → plus z = 0 ∧ minus z = 0) ∧
        (∀ z, 0 < p z →
          (∀ beta, cumulative (plus z) beta = -Real.log (sourceMass p z beta)) ∧
          (∀ beta, cumulative (minus z) beta =
            Real.log (targetMass p z / restrictedMass p z beta)) ∧
          (∀ other : Node I → ℝ,
            (∀ beta, cumulative other beta = -Real.log (sourceMass p z beta)) →
              other = plus z) ∧
          (∀ other : Node I → ℝ,
            (∀ beta, cumulative other beta =
              Real.log (targetMass p z / restrictedMass p z beta)) → other = minus z) ∧
          (∀ alpha : Node I,
            (∀ n : ℕ,
              Integrable (fun rows => positiveOnPrefix z alpha (List.ofFn rows))
                (rowLaw p (n + 1)) ∧
              Integrable (fun rows => negativeOnPrefix z alpha (List.ofFn rows))
                (rowLaw p (n + 1))) ∧
            HasSum (fun n : ℕ =>
              ∫ rows, positiveOnPrefix z alpha (List.ofFn rows) ∂rowLaw p (n + 1))
              (plus z alpha) ∧
            HasSum (fun n : ℕ =>
              ∫ rows, negativeOnPrefix z alpha (List.ofFn rows) ∂rowLaw p (n + 1))
              (minus z alpha))) ∧
        (∀ (alpha : Node I) (h : ℕ),
          Integrable (blockStatistic alpha h) (rowLaw p (h + 1))) ∧
        (∀ alpha : Node I,
          Filter.Tendsto
            (fun h : ℕ => ∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1))
            Filter.atTop (𝓝 (∑ z, p z * (plus z alpha - minus z alpha))))

end PidPrefixMgwMeanRawTargets
