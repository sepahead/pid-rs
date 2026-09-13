import PidPrefixProbability.Contract
import Mathlib.Topology.Algebra.InfiniteSum.NatInt

/-! SOURCE-ONLY PROPOSAL. These are complete proposition types, not proofs.
No type elaboration or new target execution has occurred in this preparation. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal Topology
open MeasureTheory
open PidMgwBridgeContract
open PidPrefixProbabilityContract
universe u v w
namespace PidPrefixMgwMeanContract

local instance keySpace {I : Type u} {X : I → Type v} {T : Type w} :
    MeasurableSpace (Key I X T) := ⊤

noncomputable local instance propositionDecidable (P : Prop) : Decidable P := Classical.propDecidable P

abbrev word_coefficient_join_power_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (r : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (n : ℕ)
      (sigma : SemilatticeSup (Node I)),
    ExactOps sigma →
      wordCoefficient r z alpha (n + 1) =
        @PidJoinLogContract.joinPower (Node I) (nodeFintype I) sigma
          (Classical.decEq (Node I)) (weights r z) n alpha

abbrev finite_block_expectation_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (alpha : Node I) (h : ℕ),
    Law p →
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

abbrev prefix_expectations_to_mgw_mean_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ),
    Law p →
      ∃ plus minus : Key I X T → Node I → ℝ,
        (∀ z, p z = 0 → plus z = 0 ∧ minus z = 0) ∧
        (∀ z, 0 < p z →
          InfInverse p z (plus z) ∧ MisInverse p z (minus z) ∧
          (∀ other : Node I → ℝ, InfInverse p z other → other = plus z) ∧
          (∀ other : Node I → ℝ, MisInverse p z other → other = minus z) ∧
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

end PidPrefixMgwMeanContract
