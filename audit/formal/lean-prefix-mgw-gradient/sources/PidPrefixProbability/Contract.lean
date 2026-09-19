import PidMgwBridge.Contract
import Mathlib.MeasureTheory.Constructions.Pi
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.Probability.Independence.Basic

/-! Concrete finite product experiment and raw prefix statistic.
This module defines objects and proposition types only. It proves no probability theorem. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal
open MeasureTheory
open PidMgwBridgeContract (Key Node Law mismatches singles rawJoin targetMass conditioned)
universe u v w
namespace PidPrefixProbabilityContract

local instance keyMeasurable {I : Type u} {X : I → Type v} {T : Type w} :
    MeasurableSpace (Key I X T) := ⊤

section Categorical
variable {I : Type u} {X : I → Type v} {T : Type w}
variable [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
variable [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]

noncomputable def keyMeasure (p : Key I X T → ℝ) : Measure (Key I X T) :=
  ∑ x, ENNReal.ofReal (p x) • Measure.dirac x

noncomputable def rowLaw (p : Key I X T → ℝ) (count : ℕ) :
    Measure (Fin count → Key I X T) :=
  Measure.pi fun _ : Fin count => keyMeasure p

noncomputable def experimentLaw (p : Key I X T → ℝ) (blocks horizon : ℕ) :
    Measure (Fin blocks × Fin (horizon + 1) → Key I X T) :=
  Measure.pi fun _ : Fin blocks × Fin (horizon + 1) => keyMeasure p

noncomputable def rawPrefixFamily (z : Key I X T) :
    List (Key I X T) → Finset (Finset I)
  | [] => ∅
  | x :: xs => xs.foldl (fun family row => rawJoin family (singles (mismatches z row)))
      (singles (mismatches z x))

noncomputable def prefixEvent (z : Key I X T) (alpha : Node I)
    (rows : List (Key I X T)) : Prop :=
  rows ≠ [] ∧ (∀ x ∈ rows, (mismatches z x).Nonempty) ∧
    rawPrefixFamily z rows = alpha.val

noncomputable def positiveOnPrefix (z : Key I X T) (alpha : Node I)
    (rows : List (Key I X T)) : ℝ := by
  classical
  exact if prefixEvent z alpha rows then 1 / (rows.length : ℝ) else 0

noncomputable def negativeOnPrefix (z : Key I X T) (alpha : Node I)
    (rows : List (Key I X T)) : ℝ := by
  classical
  exact match rows.getLast? with
  | none => 0
  | some current =>
    if current.2 = z.2 then
      let retained := rows.filter fun x => decide (x.2 = z.2)
      if prefixEvent z alpha retained then 1 / (retained.length : ℝ) else 0
    else 0

noncomputable def wordCoefficient (r : Key I X T → ℝ) (z : Key I X T)
    (alpha : Node I) (count : ℕ) : ℝ := by
  classical
  exact ∑ word : Fin count → Key I X T,
    (∏ i, r (word i)) * if prefixEvent z alpha (List.ofFn word) then 1 else 0

noncomputable def harmonic (horizon : ℕ) : ℝ :=
  ∑ i : Fin horizon, 1 / ((i.val : ℝ) + 1)

noncomputable def blockStatistic (alpha : Node I) (horizon : ℕ)
    (block : Fin (horizon + 1) → Key I X T) : ℝ :=
  let anchor := block 0
  let draws := List.ofFn fun i : Fin horizon => block i.succ
  ∑ j : Fin horizon,
    (positiveOnPrefix anchor alpha (draws.take (j.val + 1)) -
      negativeOnPrefix anchor alpha (draws.take (j.val + 1)))

def blockProjection (blocks horizon : ℕ) (b : Fin blocks)
    (sample : Fin blocks × Fin (horizon + 1) → Key I X T) :
    Fin (horizon + 1) → Key I X T :=
  fun row => sample (b, row)

noncomputable def sampleStatistic (alpha : Node I) (blocks horizon : ℕ) (b : Fin blocks)
    (sample : Fin blocks × Fin (horizon + 1) → Key I X T) : ℝ :=
  blockStatistic alpha horizon (blockProjection blocks horizon b sample)

end Categorical

abbrev finite_law_measure_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ),
    Law p → IsProbabilityMeasure (keyMeasure p) ∧
      (∀ x, keyMeasure p {x} = ENNReal.ofReal (p x)) ∧
      ∀ f : Key I X T → ℝ,
        Integrable f (keyMeasure p) ∧ (∫ x, f x ∂keyMeasure p) = ∑ x, p x * f x

abbrev finite_product_law_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (count : ℕ),
    Law p → IsProbabilityMeasure (rowLaw p count) ∧
      (∀ word, rowLaw p count {word} = ENNReal.ofReal (∏ i, p (word i))) ∧
      ∀ f : (Fin count → Key I X T) → ℝ,
        Integrable f (rowLaw p count) ∧
          (∫ word, f word ∂rowLaw p count) = ∑ word, (∏ i, p (word i)) * f word

abbrev positive_increment_expectation_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (n : ℕ),
    Law p →
      (∫ rows, positiveOnPrefix z alpha (List.ofFn rows) ∂rowLaw p (n + 1)) =
        wordCoefficient p z alpha (n + 1) / ((n : ℝ) + 1)

abbrev negative_increment_expectation_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (n : ℕ),
    Law p → 0 < targetMass p z →
      (∫ rows, negativeOnPrefix z alpha (List.ofFn rows) ∂rowLaw p (n + 1)) =
        ∑ k ∈ Finset.range (n + 1),
          (Nat.choose n k : ℝ) * (targetMass p z) ^ (k + 1) *
            (1 - targetMass p z) ^ (n - k) *
            wordCoefficient (conditioned p z) z alpha (k + 1) / ((k : ℝ) + 1)

abbrev block_range_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (alpha : Node I) (horizon : ℕ) (block : Fin (horizon + 1) → Key I X T),
    -harmonic horizon ≤ blockStatistic alpha horizon block ∧
      blockStatistic alpha horizon block ≤ harmonic horizon

abbrev block_product_independence_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (alpha : Node I) (blocks horizon : ℕ),
    Law p →
      IsProbabilityMeasure (experimentLaw p blocks horizon) ∧
      (∀ b : Fin blocks,
        (experimentLaw p blocks horizon).map (blockProjection blocks horizon b) =
          rowLaw p (horizon + 1)) ∧
      (∀ b : Fin blocks, Measurable (sampleStatistic (X := X) (T := T) alpha blocks horizon b)) ∧
      (∀ b : Fin blocks,
        Integrable (sampleStatistic alpha blocks horizon b) (experimentLaw p blocks horizon)) ∧
      ProbabilityTheory.iIndepFun (sampleStatistic alpha blocks horizon)
        (experimentLaw p blocks horizon)

end PidPrefixProbabilityContract
