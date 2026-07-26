import Mathlib.Data.Rat.BigOperators
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Tactic.Ring

set_option autoImplicit false
set_option warningAsError true

/-!
# Exact positive-integer arithmetic behind the KSG harmonic rewrite

This file checks only the finite-sum, cancellation, index, range, and source-symmetry obligations
named by `KSG-INTEGER-HARMONIC-001` revision 2.

The special-function bridge is deliberately a typed premise:
`PositiveIntegerDigammaPremise ψ eulerConstant` states the positive-integer identity needed at
each argument. The file does not construct the analytic digamma function and does not establish
that premise. It also does not formalize neighbor geometry, count production, binary64 evaluation,
KSG consistency, continuous-support assumptions, shared-exclusions event semantics, any PID atom,
or Rust refinement.
-/

namespace PidKsgIntegerHarmonic

open scoped BigOperators

noncomputable section

/-- The exact rational harmonic number `H_m = ∑_{i=0}^{m-1} 1/(i+1)`. -/
def harmonic (m : ℕ) : ℚ :=
  ∑ i ∈ Finset.range m, (((i + 1 : ℕ) : ℚ)⁻¹)

@[simp]
theorem harmonic_zero : harmonic 0 = 0 := by
  simp [harmonic]

theorem harmonic_succ (m : ℕ) :
    harmonic (m + 1) = harmonic m + (((m + 1 : ℕ) : ℚ)⁻¹) := by
  simp [harmonic, Finset.sum_range_succ]

/-- Exact-real embedding of the rational finite sum. -/
def harmonicReal (m : ℕ) : ℝ :=
  harmonic m

/-- The direct four-harmonic combination after positive-integer digamma cancellation. -/
def directHarmonicTerm (k n x y : ℕ) : ℚ :=
  harmonic (k - 1) + harmonic (n - 1) - harmonic (x - 1) - harmonic (y - 1)

/-- The source-symmetric, two-nonnegative-range association used by the selected implementation. -/
def symmetricRangeTerm (k n x y : ℕ) : ℚ :=
  (harmonic (n - 1) - harmonic (max x y - 1)) -
    (harmonic (min x y - 1) - harmonic (k - 1))

/--
The exact range identity is algebraic and holds for any natural indices. The hypotheses below bind
the theorem to the positive-integer estimator domain rather than supplying hidden proof power.
-/
theorem direct_eq_symmetric_range
    (k n x y : ℕ)
    (_hk : 1 ≤ k)
    (_hkn : k ≤ n)
    (_hkx : k ≤ x)
    (_hky : k ≤ y)
    (_hxn : x ≤ n)
    (_hyn : y ≤ n) :
    directHarmonicTerm k n x y = symmetricRangeTerm k n x y := by
  rcases le_total x y with hxy | hyx
  · simp [directHarmonicTerm, symmetricRangeTerm, Nat.max_eq_right hxy,
      Nat.min_eq_left hxy]
    ring
  · simp [directHarmonicTerm, symmetricRangeTerm, Nat.max_eq_left hyx,
      Nat.min_eq_right hyx]
    ring

theorem direct_source_swap (k n x y : ℕ) :
    directHarmonicTerm k n x y = directHarmonicTerm k n y x := by
  simp [directHarmonicTerm]
  ring

theorem symmetric_range_source_swap (k n x y : ℕ) :
    symmetricRangeTerm k n x y = symmetricRangeTerm k n y x := by
  simp [symmetricRangeTerm, Nat.max_comm, Nat.min_comm]

/--
Typed analytic seam. This is a premise about a supplied function on positive integers, not a
construction or verification of the analytic digamma function.
-/
def PositiveIntegerDigammaPremise (psi : ℕ → ℝ) (eulerConstant : ℝ) : Prop :=
  ∀ m : ℕ, 1 ≤ m → psi m = harmonicReal (m - 1) - eulerConstant

/-- The four copies of the typed constant cancel with coefficients `(+1,+1,-1,-1)`. -/
theorem digamma_four_term_cancellation
    (psi : ℕ → ℝ)
    (eulerConstant : ℝ)
    (hpsi : PositiveIntegerDigammaPremise psi eulerConstant)
    (k n x y : ℕ)
    (hk : 1 ≤ k)
    (hn : 1 ≤ n)
    (hx : 1 ≤ x)
    (hy : 1 ≤ y) :
    psi k + psi n - psi x - psi y =
      harmonicReal (k - 1) + harmonicReal (n - 1) -
        harmonicReal (x - 1) - harmonicReal (y - 1) := by
  rw [hpsi k hk, hpsi n hn, hpsi x hx, hpsi y hy]
  ring

/-- KSG exclusive marginal counts are shifted once before entering the positive-integer formula. -/
def exclusiveArgument (count : ℕ) : ℕ :=
  count + 1

/-- Ehrlich anchor-inclusive counts already are positive-integer formula arguments. -/
def inclusiveArgument (count : ℕ) : ℕ :=
  count

theorem exclusive_argument_predecessor (count : ℕ) :
    exclusiveArgument count - 1 = count := by
  simp [exclusiveArgument]

theorem exclusive_argument_bounds
    (n k count : ℕ)
    (hk : 1 ≤ k)
    (_hkn : k < n)
    (hlower : k - 1 ≤ count)
    (hupper : count < n) :
    k ≤ exclusiveArgument count ∧ exclusiveArgument count ≤ n := by
  simp only [exclusiveArgument]
  constructor <;> omega

theorem inclusive_argument_identity (count : ℕ) :
    inclusiveArgument count = count := by
  rfl

theorem inclusive_argument_bounds
    (n k count : ℕ)
    (_hk : 1 ≤ k)
    (_hkn : k < n)
    (hlower : k ≤ count)
    (hupper : count ≤ n) :
    k ≤ inclusiveArgument count ∧ inclusiveArgument count ≤ n := by
  simpa [inclusiveArgument] using And.intro hlower hupper

/-- Exact KSG exclusive-count index map, before the symmetric range reassociation. -/
theorem exclusive_direct_index_map (k n nx ny : ℕ) :
    directHarmonicTerm k n (exclusiveArgument nx) (exclusiveArgument ny) =
      harmonic (k - 1) + harmonic (n - 1) - harmonic nx - harmonic ny := by
  simp [directHarmonicTerm, exclusiveArgument]

/-- Exact KSG exclusive-count formula in source-symmetric range form. -/
theorem exclusive_symmetric_range
    (n k nx ny : ℕ)
    (hk : 1 ≤ k)
    (hkn : k < n)
    (hnxLower : k - 1 ≤ nx)
    (hnyLower : k - 1 ≤ ny)
    (hnxUpper : nx < n)
    (hnyUpper : ny < n) :
    harmonic (k - 1) + harmonic (n - 1) - harmonic nx - harmonic ny =
      (harmonic (n - 1) - harmonic (max nx ny)) -
        (harmonic (min nx ny) - harmonic (k - 1)) := by
  have hx := exclusive_argument_bounds n k nx hk hkn hnxLower hnxUpper
  have hy := exclusive_argument_bounds n k ny hk hkn hnyLower hnyUpper
  rw [← exclusive_direct_index_map k n nx ny]
  rw [direct_eq_symmetric_range k n (exclusiveArgument nx) (exclusiveArgument ny)
    hk (Nat.le_of_lt hkn) hx.1 hy.1 hx.2 hy.2]
  rcases le_total nx ny with hnxy | hnyx
  · simp [symmetricRangeTerm, exclusiveArgument, Nat.max_eq_right hnxy,
      Nat.min_eq_left hnxy]
  · simp [symmetricRangeTerm, exclusiveArgument, Nat.max_eq_left hnyx,
      Nat.min_eq_right hnyx]

/-- Exact anchor-inclusive index map; no additional successor is introduced. -/
theorem inclusive_direct_index_map (k n x y : ℕ) :
    directHarmonicTerm k n (inclusiveArgument x) (inclusiveArgument y) =
      harmonic (k - 1) + harmonic (n - 1) - harmonic (x - 1) - harmonic (y - 1) := by
  rfl

/-- Exact anchor-inclusive formula in source-symmetric range form. -/
theorem inclusive_symmetric_range
    (n k x y : ℕ)
    (hk : 1 ≤ k)
    (hkn : k < n)
    (hxLower : k ≤ x)
    (hyLower : k ≤ y)
    (hxUpper : x ≤ n)
    (hyUpper : y ≤ n) :
    directHarmonicTerm k n (inclusiveArgument x) (inclusiveArgument y) =
      symmetricRangeTerm k n x y := by
  simpa [inclusiveArgument] using
    direct_eq_symmetric_range k n x y hk (Nat.le_of_lt hkn)
      hxLower hyLower hxUpper hyUpper

end

end PidKsgIntegerHarmonic
