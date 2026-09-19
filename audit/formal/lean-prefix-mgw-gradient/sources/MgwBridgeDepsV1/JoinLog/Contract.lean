import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Data.Finset.Lattice.Fold

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators

universe u

namespace PidJoinLogContract

noncomputable def cumulative {L : Type u} [Fintype L] [LE L] [DecidableLE L]
    (weight : L → ℝ) (a : L) : ℝ :=
  ∑ x, if x ≤ a then weight x else 0

noncomputable def joinConvolution {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (left right : L → ℝ) (a : L) : ℝ :=
  ∑ x, ∑ y, if x ⊔ y = a then left x * right y else 0

noncomputable def joinPower {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (weight : L → ℝ) : ℕ → L → ℝ
  | 0 => weight
  | n + 1 => joinConvolution (joinPower weight n) weight

noncomputable def logAtoms {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (weight : L → ℝ) (a : L) : ℝ :=
  ∑' n : ℕ, joinPower weight n a / ((n : ℝ) + 1)

noncomputable def truncatedLogAtoms {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (weight : L → ℝ) (count : ℕ) (a : L) : ℝ :=
  ∑ n ∈ Finset.range count, joinPower weight n a / ((n : ℝ) + 1)

def nonemptyGeneratorJoin {L : Type u} [SemilatticeSup L]
    [DecidableEq L] (weight : L → ℝ) (a : L) : Prop :=
  ∃ support : Finset L, ∃ h : support.Nonempty,
    (∀ x ∈ support, 0 < weight x) ∧ support.sup' h id = a

abbrev lower_cumulative_unique_target
    (L : Type u) [Fintype L] [PartialOrder L] [DecidableLE L] : Prop :=
  ∀ (left right : L → ℝ),
    (∀ a, cumulative left a = cumulative right a) → left = right

abbrev join_convolution_cumulative_target
    (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] : Prop :=
  ∀ (left right : L → ℝ) (a : L),
    cumulative (joinConvolution left right) a =
      cumulative left a * cumulative right a

abbrev join_power_nonnegative_target
    (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] : Prop :=
  ∀ (weight : L → ℝ), (∀ a, 0 ≤ weight a) →
    ∀ (n : ℕ) (a : L), 0 ≤ joinPower weight n a

abbrev join_power_total_target
    (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] : Prop :=
  ∀ (weight : L → ℝ) (n : ℕ),
    (∑ a, joinPower weight n a) = (∑ a, weight a) ^ (n + 1)

abbrev log_atoms_cumulative_target
    (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] : Prop :=
  ∀ (weight : L → ℝ),
    (∀ a, 0 ≤ weight a) → (∑ a, weight a) < 1 →
    ∀ a, cumulative (logAtoms weight) a =
      -Real.log (1 - cumulative weight a)

abbrev supplied_log_inverse_nonnegative_target
    (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] : Prop :=
  ∀ (weight atoms : L → ℝ),
    (∀ a, 0 ≤ weight a) → (∑ a, weight a) < 1 →
    (∀ a, cumulative atoms a = -Real.log (1 - cumulative weight a)) →
    ∀ a, 0 ≤ atoms a

abbrev log_atoms_strict_support_target
    (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] : Prop :=
  ∀ (weight : L → ℝ),
    (∀ a, 0 ≤ weight a) → (∑ a, weight a) < 1 →
    ∀ a, 0 < logAtoms weight a ↔ nonemptyGeneratorJoin weight a

abbrev log_atoms_truncation_target
    (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] : Prop :=
  ∀ (weight : L → ℝ),
    (∀ a, 0 ≤ weight a) → (∑ a, weight a) < 1 →
    ∀ count : ℕ,
      let rho := ∑ a, weight a
      let error := ∑ a, |logAtoms weight a - truncatedLogAtoms weight count a|
      (∀ a, truncatedLogAtoms weight count a ≤ logAtoms weight a) ∧
      error = -Real.log (1 - rho) -
        ∑ n ∈ Finset.range count, rho ^ (n + 1) / ((n : ℝ) + 1) ∧
      error ≤ rho ^ (count + 1) / (((count : ℝ) + 1) * (1 - rho))

end PidJoinLogContract
