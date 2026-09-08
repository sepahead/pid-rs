import PidPrefixMgwMean.RawTargets
import PidPrefixMgwMean.AliasTargets
import MgwBridgeDepsV1.SxDnf.JudgeCore

/-! Proposition mutations only; no value of a mean target is supplied. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal Topology
open Lean Meta Elab Command MeasureTheory
open PidMgwBridgeContract PidPrefixProbabilityContract
universe u v w
namespace PidPrefixMgwMeanPreparationControls
local instance keySpace {I : Type u} {X : I → Type v} {T : Type w} :
    MeasurableSpace (Key I X T) := ⊤
noncomputable local instance propositionDecidable (P : Prop) : Decidable P := Classical.propDecidable P

def wrong_degree_offset : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (r : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (n : ℕ)
      (sigma : SemilatticeSup (Node I)),
    ((∀ a b : Node I, sigma.le a b ↔ rawLE a.val b.val) ∧
      (∀ a b : Node I, (sigma.sup a b).val = rawJoin a.val b.val)) →
      wordCoefficient r z alpha (n + 1) =
        @PidJoinLogContract.joinPower (Node I) (nodeFintype I) sigma
          (Classical.decEq (Node I)) (weights r z) (n + 1) alpha

def received_nonnegative_mass : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (r : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (n : ℕ)
      (sigma : SemilatticeSup (Node I)),
    (∀ x, 0 ≤ r x) →
    ((∀ a b : Node I, sigma.le a b ↔ rawLE a.val b.val) ∧
      (∀ a b : Node I, (sigma.sup a b).val = rawJoin a.val b.val)) →
      wordCoefficient r z alpha (n + 1) =
        @PidJoinLogContract.joinPower (Node I) (nodeFintype I) sigma
          (Classical.decEq (Node I)) (weights r z) n alpha

def wrong_raw_time_rank : Prop :=
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
                  wordCoefficient (conditioned p z) z alpha (k + 1) / ((n : ℝ) + 1))
          else 0))

def received_log_model : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ),
    ((∀ x, 0 ≤ p x) ∧ PidMgwBridgeContract.total p = 1) →
      (∀ z, 0 < p z → ∃ a : Node I → ℝ, LogModel (weights p z) a) →
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

def received_mean_outcome : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ),
    ((∀ x, 0 ≤ p x) ∧ PidMgwBridgeContract.total p = 1) →
      PidPrefixMgwMeanRawTargets.prefix_expectations_to_mgw_mean.{u, v, w} →
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

private def record (label : String) (condition : Bool) : MetaM Unit := do
  unless condition do
    throwError "PREFIX_MGW_MEAN_CONTROL: {label} failed"
  IO.println ((Json.mkObj [("control", Json.str label),
    ("status", Json.str "expected_type_result_observed")]).compress)

private def rejectView (label : String) (actual expected : Name) : MetaM Unit := do
  let a ← getConstInfoDefn actual
  let e ← getConstInfoDefn expected
  record label (!(← PidSxDnfOrderJudge.hasExactType a.value a.levelParams e.value e.levelParams))

end PidPrefixMgwMeanPreparationControls

run_cmd liftTermElabM do
  let raw ← getConstInfoDefn ``PidPrefixMgwMeanRawTargets.word_coefficient_join_power
  let aliasView ← getConstInfoDefn ``PidPrefixMgwMeanAliasTargets.word_coefficient_join_power
  PidPrefixMgwMeanPreparationControls.record "exact-word_coefficient_join_power" (← PidSxDnfOrderJudge.hasExactType aliasView.value aliasView.levelParams raw.value raw.levelParams)
  PidPrefixMgwMeanPreparationControls.record "explicit-receiver-word_coefficient_join_power" (!(← PidSxDnfOrderJudge.hasExactType (mkForall `obligation .default raw.value raw.value) raw.levelParams raw.value raw.levelParams))
  PidPrefixMgwMeanPreparationControls.record "implicit-receiver-word_coefficient_join_power" (!(← PidSxDnfOrderJudge.hasExactType (mkForall `obligation .implicit raw.value raw.value) raw.levelParams raw.value raw.levelParams))
  PidPrefixMgwMeanPreparationControls.record "extra-universe-word_coefficient_join_power" (!(← PidSxDnfOrderJudge.hasExactType raw.value (raw.levelParams ++ [`unused_level]) raw.value raw.levelParams))
  let raw ← getConstInfoDefn ``PidPrefixMgwMeanRawTargets.finite_block_expectation
  let aliasView ← getConstInfoDefn ``PidPrefixMgwMeanAliasTargets.finite_block_expectation
  PidPrefixMgwMeanPreparationControls.record "exact-finite_block_expectation" (← PidSxDnfOrderJudge.hasExactType aliasView.value aliasView.levelParams raw.value raw.levelParams)
  PidPrefixMgwMeanPreparationControls.record "explicit-receiver-finite_block_expectation" (!(← PidSxDnfOrderJudge.hasExactType (mkForall `obligation .default raw.value raw.value) raw.levelParams raw.value raw.levelParams))
  PidPrefixMgwMeanPreparationControls.record "implicit-receiver-finite_block_expectation" (!(← PidSxDnfOrderJudge.hasExactType (mkForall `obligation .implicit raw.value raw.value) raw.levelParams raw.value raw.levelParams))
  PidPrefixMgwMeanPreparationControls.record "extra-universe-finite_block_expectation" (!(← PidSxDnfOrderJudge.hasExactType raw.value (raw.levelParams ++ [`unused_level]) raw.value raw.levelParams))
  let raw ← getConstInfoDefn ``PidPrefixMgwMeanRawTargets.prefix_expectations_to_mgw_mean
  let aliasView ← getConstInfoDefn ``PidPrefixMgwMeanAliasTargets.prefix_expectations_to_mgw_mean
  PidPrefixMgwMeanPreparationControls.record "exact-prefix_expectations_to_mgw_mean" (← PidSxDnfOrderJudge.hasExactType aliasView.value aliasView.levelParams raw.value raw.levelParams)
  PidPrefixMgwMeanPreparationControls.record "explicit-receiver-prefix_expectations_to_mgw_mean" (!(← PidSxDnfOrderJudge.hasExactType (mkForall `obligation .default raw.value raw.value) raw.levelParams raw.value raw.levelParams))
  PidPrefixMgwMeanPreparationControls.record "implicit-receiver-prefix_expectations_to_mgw_mean" (!(← PidSxDnfOrderJudge.hasExactType (mkForall `obligation .implicit raw.value raw.value) raw.levelParams raw.value raw.levelParams))
  PidPrefixMgwMeanPreparationControls.record "extra-universe-prefix_expectations_to_mgw_mean" (!(← PidSxDnfOrderJudge.hasExactType raw.value (raw.levelParams ++ [`unused_level]) raw.value raw.levelParams))
  PidPrefixMgwMeanPreparationControls.rejectView "wrong_degree_offset" ``PidPrefixMgwMeanPreparationControls.wrong_degree_offset ``PidPrefixMgwMeanRawTargets.word_coefficient_join_power
  PidPrefixMgwMeanPreparationControls.rejectView "received_nonnegative_mass" ``PidPrefixMgwMeanPreparationControls.received_nonnegative_mass ``PidPrefixMgwMeanRawTargets.word_coefficient_join_power
  PidPrefixMgwMeanPreparationControls.rejectView "wrong_raw_time_rank" ``PidPrefixMgwMeanPreparationControls.wrong_raw_time_rank ``PidPrefixMgwMeanRawTargets.finite_block_expectation
  PidPrefixMgwMeanPreparationControls.rejectView "received_log_model" ``PidPrefixMgwMeanPreparationControls.received_log_model ``PidPrefixMgwMeanRawTargets.prefix_expectations_to_mgw_mean
  PidPrefixMgwMeanPreparationControls.rejectView "received_mean_outcome" ``PidPrefixMgwMeanPreparationControls.received_mean_outcome ``PidPrefixMgwMeanRawTargets.prefix_expectations_to_mgw_mean
