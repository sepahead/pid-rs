import Mathlib.Analysis.Calculus.Deriv.Basic
import PidFiniteConvergence.SxEventBridge

/-!
# Fixed-source-marginal invariance of finite categorical informative shared exclusions

This module proves an algebraic fact for one fixed finite source product alphabet.  The categorical
shared-exclusions source event depends only on source coordinates.  Consequently, the complete-law
average of its negative log mass factors through the complete source marginal.  Two real mass
functions with the same source marginal therefore have equal averaged informative cumulatives,
even when their finite target alphabets differ.  Applying any one fixed finite linear transform --
in particular, a separately justified Mobius inverse -- preserves that equality coordinatewise.
Exact constancy along a fixed-source-marginal path is the primary result; its zero-derivative
statement is only a calculus corollary and says nothing about paths that change the source
marginal.

The theorem is deliberately narrower than a paper-correspondence or implementation theorem.  It
does not prove that a supplied collection family is the Makkeh--Gutknecht--Wibral redundancy
lattice, that supplied coefficients are its Mobius inverse, that a parser or Rust implementation
computes these definitions, or that any misinformative, signed-net, continuous, sampling, causal,
or estimator claim is invariant.  For probability semantics, callers additionally establish
nonnegativity and total mass one; the equalities below are algebraic and need neither premise.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators

namespace PidFiniteConvergence

universe u v w x y z

/-- The heterogeneous finite source tuple, without a target coordinate. -/
abbrev CategoricalSourceKey (sourceIndex : Type u) (sourceValue : sourceIndex -> Type v) :=
  (source : sourceIndex) -> sourceValue source

/-- The complete source marginal of a real mass function on the fixed product alphabet. -/
noncomputable def categoricalSourceMarginal
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype targetValue]
    (law : CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (sourceKey : CategoricalSourceKey sourceIndex sourceValue) : Real :=
  ∑ target, law (sourceKey, target)

/-- One source-collection branch on source tuples, with no target coordinate. -/
noncomputable def sourceOnlyBranchEvent
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    (collection : Finset sourceIndex)
    (anchor : CategoricalSourceKey sourceIndex sourceValue) :
    Finset (CategoricalSourceKey sourceIndex sourceValue) := by
  classical
  exact Finset.univ.filter fun candidate =>
    ∀ source ∈ collection, anchor source = candidate source

/-- The source-only union of source-collection branches. -/
noncomputable def sxSourceOnlyEvent
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    (collections : Finset (Finset sourceIndex))
    (anchor : CategoricalSourceKey sourceIndex sourceValue) :
    Finset (CategoricalSourceKey sourceIndex sourceValue) :=
  collections.biUnion fun collection => sourceOnlyBranchEvent collection anchor

/-- Lifting a source-only event by every target value recovers the complete-key source event.
This is the load-bearing semantic bridge: target coordinates are absent from source-event
membership, rather than merely cancelling numerically later. -/
theorem sx_source_event_eq_source_only_product
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (collections : Finset (Finset sourceIndex))
    (sourceAnchor : CategoricalSourceKey sourceIndex sourceValue)
    (targetAnchor : targetValue) :
    sxSourceEvent collections (sourceAnchor, targetAnchor) =
      (sxSourceOnlyEvent collections sourceAnchor).product Finset.univ := by
  classical
  ext candidate
  constructor
  · intro hCandidate
    unfold sxSourceEvent at hCandidate
    rcases Finset.mem_biUnion.mp hCandidate with
      ⟨collection, hCollection, hBranch⟩
    have hMatch :=
      ((source_branch_is_equivalence_class collection).2
        (sourceAnchor, targetAnchor) candidate).mp hBranch
    apply Finset.mem_product.mpr
    constructor
    · unfold sxSourceOnlyEvent
      apply Finset.mem_biUnion.mpr
      refine ⟨collection, hCollection, ?_⟩
      unfold sourceOnlyBranchEvent
      exact Finset.mem_filter.mpr ⟨Finset.mem_univ _, hMatch⟩
    · exact Finset.mem_univ _
  · intro hCandidate
    rcases Finset.mem_product.mp hCandidate with ⟨hSource, _⟩
    unfold sxSourceOnlyEvent at hSource
    rcases Finset.mem_biUnion.mp hSource with
      ⟨collection, hCollection, hBranch⟩
    unfold sourceOnlyBranchEvent at hBranch
    have hMatch := (Finset.mem_filter.mp hBranch).2
    unfold sxSourceEvent
    apply Finset.mem_biUnion.mpr
    refine ⟨collection, hCollection, ?_⟩
    exact
      ((source_branch_is_equivalence_class collection).2
        (sourceAnchor, targetAnchor) candidate).mpr hMatch

/-- Mass of a target-cylinder event is the mass of its source base under the complete source
marginal. -/
theorem finite_event_mass_source_product_eq_marginal_mass
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (law : CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (sourceEvent : Finset (CategoricalSourceKey sourceIndex sourceValue)) :
    finiteEventMass law (sourceEvent.product Finset.univ) =
      ∑ sourceKey ∈ sourceEvent, categoricalSourceMarginal law sourceKey := by
  classical
  simp [finiteEventMass, categoricalSourceMarginal, Finset.sum_product]

/-- The mass of a categorical shared-exclusions source event is determined by the complete source
marginal and is independent of the anchor's target value. -/
theorem sx_source_event_mass_eq_source_marginal_mass
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (law : CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (collections : Finset (Finset sourceIndex))
    (sourceAnchor : CategoricalSourceKey sourceIndex sourceValue)
    (targetAnchor : targetValue) :
    finiteEventMass law (sxSourceEvent collections (sourceAnchor, targetAnchor)) =
      ∑ sourceKey ∈ sxSourceOnlyEvent collections sourceAnchor,
        categoricalSourceMarginal law sourceKey := by
  rw [sx_source_event_eq_source_only_product]
  exact finite_event_mass_source_product_eq_marginal_mass law _

/-- Averaged informative cumulative on the complete finite product alphabet, in nats.  On a
probability law, zero-mass complete keys contribute zero; positivity of source-event mass on
positive support is supplied separately by `sx_source_event_mass_positive`. -/
noncomputable def averagedInformativeCumulative
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (law : CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (collections : Finset (Finset sourceIndex)) : Real :=
  ∑ anchor, law anchor *
    (-Real.log (finiteEventMass law (sxSourceEvent collections anchor)))

/-- The source-marginal functional through which the averaged informative cumulative factors.
It has no target type or target kernel parameter. -/
noncomputable def averagedInformativeCumulativeFromSourceMarginal
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    (sourceMass : CategoricalSourceKey sourceIndex sourceValue -> Real)
    (collections : Finset (Finset sourceIndex)) : Real :=
  ∑ sourceAnchor,
    sourceMass sourceAnchor *
      (-Real.log
        (∑ sourceKey ∈ sxSourceOnlyEvent collections sourceAnchor,
          sourceMass sourceKey))

/-- The complete-law average factors exactly through the complete source marginal. -/
theorem averaged_informative_cumulative_eq_source_marginal_sum
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (law : CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (collections : Finset (Finset sourceIndex)) :
    averagedInformativeCumulative law collections =
      ∑ sourceAnchor,
        categoricalSourceMarginal law sourceAnchor *
          (-Real.log
            (∑ sourceKey ∈ sxSourceOnlyEvent collections sourceAnchor,
              categoricalSourceMarginal law sourceKey)) := by
  classical
  unfold averagedInformativeCumulative
  rw [Fintype.sum_prod_type]
  apply Finset.sum_congr rfl
  intro sourceAnchor _
  simp_rw [sx_source_event_mass_eq_source_marginal_mass]
  rw [← Finset.sum_mul]
  rfl

/-- Strong factorization form: the complete-law expression is exactly one application of a
functional whose input is only the complete source marginal. -/
theorem averaged_informative_cumulative_factors_through_source_marginal
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (law : CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (collections : Finset (Finset sourceIndex)) :
    averagedInformativeCumulative law collections =
      averagedInformativeCumulativeFromSourceMarginal
        (categoricalSourceMarginal law) collections := by
  simpa [averagedInformativeCumulativeFromSourceMarginal] using
    averaged_informative_cumulative_eq_source_marginal_sum law collections

/-- Fixed complete source marginal implies equality of every averaged informative cumulative for
the same source-collection event on the same finite product alphabet. -/
theorem averaged_informative_cumulative_invariant_of_source_marginal_eq
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (leftLaw rightLaw : CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (collections : Finset (Finset sourceIndex))
    (hSourceMarginal :
      ∀ sourceKey,
        categoricalSourceMarginal leftLaw sourceKey =
          categoricalSourceMarginal rightLaw sourceKey) :
    averagedInformativeCumulative leftLaw collections =
      averagedInformativeCumulative rightLaw collections := by
  rw [averaged_informative_cumulative_eq_source_marginal_sum]
  rw [averaged_informative_cumulative_eq_source_marginal_sum]
  simp_rw [hSourceMarginal]

/-- Equal complete source marginals imply equal averaged informative cumulatives even when the
two laws have different finite target types.  This is stronger than changing a target kernel on
one fixed target alphabet, but it still compares one fixed source alphabet and one fixed source
event family. -/
theorem averaged_informative_cumulative_invariant_of_source_marginal_eq_heterogeneous_target
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v}
    {leftTargetValue : Type w} {rightTargetValue : Type x}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)]
    [Fintype leftTargetValue] [Fintype rightTargetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq leftTargetValue] [DecidableEq rightTargetValue]
    (leftLaw : CategoricalKey sourceIndex sourceValue leftTargetValue -> Real)
    (rightLaw : CategoricalKey sourceIndex sourceValue rightTargetValue -> Real)
    (collections : Finset (Finset sourceIndex))
    (hSourceMarginal :
      ∀ sourceKey,
        categoricalSourceMarginal leftLaw sourceKey =
          categoricalSourceMarginal rightLaw sourceKey) :
    averagedInformativeCumulative leftLaw collections =
      averagedInformativeCumulative rightLaw collections := by
  rw [averaged_informative_cumulative_factors_through_source_marginal]
  rw [averaged_informative_cumulative_factors_through_source_marginal]
  unfold averagedInformativeCumulativeFromSourceMarginal
  simp_rw [hSourceMarginal]

/-- Exact path invariance precedes calculus: along any parameterized family with one fixed
complete source marginal, the averaged informative cumulative is a constant function of the
parameter.  No differentiability of the law path is assumed or needed. -/
theorem averaged_informative_cumulative_constant_on_fixed_source_marginal
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    {parameter : Type x}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (law : parameter -> CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (collections : Finset (Finset sourceIndex))
    (hSourceMarginal :
      ∀ leftParameter rightParameter sourceKey,
        categoricalSourceMarginal (law leftParameter) sourceKey =
          categoricalSourceMarginal (law rightParameter) sourceKey) :
    ∀ leftParameter rightParameter,
      averagedInformativeCumulative (law leftParameter) collections =
        averagedInformativeCumulative (law rightParameter) collections := by
  intro leftParameter rightParameter
  exact averaged_informative_cumulative_invariant_of_source_marginal_eq
    (law leftParameter) (law rightParameter) collections
    (hSourceMarginal leftParameter rightParameter)

/-- Zero derivative for a globally fixed-source-marginal real path is only a calculus corollary
of exact path constancy above.  It is not a derivative formula for changing source marginals.  A
local interior version follows by the same argument when fixed-marginal equality is available on
a neighborhood of the evaluation point. -/
theorem averaged_informative_cumulative_hasDerivAt_zero_of_fixed_source_marginal
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (law : Real -> CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (collections : Finset (Finset sourceIndex))
    (hSourceMarginal :
      ∀ leftParameter rightParameter sourceKey,
        categoricalSourceMarginal (law leftParameter) sourceKey =
          categoricalSourceMarginal (law rightParameter) sourceKey)
    (pathParameter : Real) :
    HasDerivAt
      (fun parameter => averagedInformativeCumulative (law parameter) collections)
      0 pathParameter := by
  let value := averagedInformativeCumulative (law pathParameter) collections
  have hFunction :
      (fun parameter => averagedInformativeCumulative (law parameter) collections) =
        fun _ => value := by
    funext parameter
    exact averaged_informative_cumulative_invariant_of_source_marginal_eq
      (law parameter) (law pathParameter) collections
      (hSourceMarginal parameter pathParameter)
  rw [hFunction]
  exact hasDerivAt_const pathParameter value

/-- Complete keys carrying strictly positive mass.  This makes the paper-facing support convention
explicit instead of relying on Lean's totalized value of `Real.log 0`. -/
noncomputable def positiveCategoricalSupport
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (law : CategoricalKey sourceIndex sourceValue targetValue -> Real) :
    Finset (CategoricalKey sourceIndex sourceValue targetValue) :=
  Finset.univ.filter fun key => 0 < law key

/-- Probability-semantic premise bundle for a real mass function on one fixed finite product
alphabet. -/
def IsCategoricalProbabilityLaw
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (law : CategoricalKey sourceIndex sourceValue targetValue -> Real) : Prop :=
  (∀ key, 0 ≤ law key) ∧ ∑ key, law key = 1

/-- The support-restricted averaged informative cumulative used for probability semantics. -/
noncomputable def averagedInformativeCumulativeOnPositiveSupport
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (law : CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (collections : Finset (Finset sourceIndex)) : Real :=
  ∑ anchor ∈ positiveCategoricalSupport law,
    law anchor * (-Real.log (finiteEventMass law (sxSourceEvent collections anchor)))

/-- For a nonnegative law, filtering the informative average to positive support changes no term.
This bridge is what prevents totalized `Real.log 0` from becoming an implicit scientific
convention. -/
theorem averaged_informative_on_positive_support_eq_full
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (law : CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (collections : Finset (Finset sourceIndex))
    (hNonnegative : ∀ key, 0 ≤ law key) :
    averagedInformativeCumulativeOnPositiveSupport law collections =
      averagedInformativeCumulative law collections := by
  unfold averagedInformativeCumulativeOnPositiveSupport averagedInformativeCumulative
  apply Finset.sum_subset (Finset.subset_univ (positiveCategoricalSupport law))
  intro anchor _ hOutside
  have hNotPositive : ¬ 0 < law anchor := by
    intro hPositive
    exact hOutside (by simp [positiveCategoricalSupport, hPositive])
  have hZero : law anchor = 0 :=
    le_antisymm (le_of_not_gt hNotPositive) (hNonnegative anchor)
  simp [hZero]

/-- Probability-semantic corollary.  Both laws are nonnegative and normalized, the collection
family is nonempty, and every positive-support source-event mass is strictly positive.  Under
equal complete source marginals, their support-restricted averaged informative cumulatives are
equal. -/
theorem probability_averaged_informative_invariant_of_source_marginal_eq
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    (leftLaw rightLaw : CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (collections : Finset (Finset sourceIndex))
    (hCollections : collections.Nonempty)
    (hLeftProbability : IsCategoricalProbabilityLaw leftLaw)
    (hRightProbability : IsCategoricalProbabilityLaw rightLaw)
    (hSourceMarginal :
      ∀ sourceKey,
        categoricalSourceMarginal leftLaw sourceKey =
          categoricalSourceMarginal rightLaw sourceKey) :
    averagedInformativeCumulativeOnPositiveSupport leftLaw collections =
        averagedInformativeCumulativeOnPositiveSupport rightLaw collections ∧
      (∀ anchor ∈ positiveCategoricalSupport leftLaw,
        0 < finiteEventMass leftLaw (sxSourceEvent collections anchor)) ∧
      (∀ anchor ∈ positiveCategoricalSupport rightLaw,
        0 < finiteEventMass rightLaw (sxSourceEvent collections anchor)) := by
  constructor
  · rw [averaged_informative_on_positive_support_eq_full
      leftLaw collections hLeftProbability.1]
    rw [averaged_informative_on_positive_support_eq_full
      rightLaw collections hRightProbability.1]
    exact averaged_informative_cumulative_invariant_of_source_marginal_eq
      leftLaw rightLaw collections hSourceMarginal
  · constructor
    · intro anchor hAnchor
      exact sx_source_event_mass_positive hCollections leftLaw hLeftProbability.1 anchor
        (by simpa [positiveCategoricalSupport] using hAnchor)
    · intro anchor hAnchor
      exact sx_source_event_mass_positive hCollections rightLaw hRightProbability.1 anchor
        (by simpa [positiveCategoricalSupport] using hAnchor)

/-- Probability-semantic heterogeneous-target corollary.  The two finite target alphabets may
differ; the source alphabet, source-event family, and complete source marginal remain fixed. -/
theorem probability_averaged_informative_invariant_of_source_marginal_eq_heterogeneous_target
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v}
    {leftTargetValue : Type w} {rightTargetValue : Type x}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)]
    [Fintype leftTargetValue] [Fintype rightTargetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq leftTargetValue] [DecidableEq rightTargetValue]
    (leftLaw : CategoricalKey sourceIndex sourceValue leftTargetValue -> Real)
    (rightLaw : CategoricalKey sourceIndex sourceValue rightTargetValue -> Real)
    (collections : Finset (Finset sourceIndex))
    (hCollections : collections.Nonempty)
    (hLeftProbability : IsCategoricalProbabilityLaw leftLaw)
    (hRightProbability : IsCategoricalProbabilityLaw rightLaw)
    (hSourceMarginal :
      ∀ sourceKey,
        categoricalSourceMarginal leftLaw sourceKey =
          categoricalSourceMarginal rightLaw sourceKey) :
    averagedInformativeCumulativeOnPositiveSupport leftLaw collections =
        averagedInformativeCumulativeOnPositiveSupport rightLaw collections ∧
      (∀ anchor ∈ positiveCategoricalSupport leftLaw,
        0 < finiteEventMass leftLaw (sxSourceEvent collections anchor)) ∧
      (∀ anchor ∈ positiveCategoricalSupport rightLaw,
        0 < finiteEventMass rightLaw (sxSourceEvent collections anchor)) := by
  constructor
  · rw [averaged_informative_on_positive_support_eq_full
      leftLaw collections hLeftProbability.1]
    rw [averaged_informative_on_positive_support_eq_full
      rightLaw collections hRightProbability.1]
    exact averaged_informative_cumulative_invariant_of_source_marginal_eq_heterogeneous_target
      leftLaw rightLaw collections hSourceMarginal
  · constructor
    · intro anchor hAnchor
      exact sx_source_event_mass_positive hCollections leftLaw hLeftProbability.1 anchor
        (by simpa [positiveCategoricalSupport] using hAnchor)
    · intro anchor hAnchor
      exact sx_source_event_mass_positive hCollections rightLaw hRightProbability.1 anchor
        (by simpa [positiveCategoricalSupport] using hAnchor)

/-- A fixed finite linear transform of cumulative coordinates.  A separately justified Mobius
inverse is one admissible instance; this definition does not assert that arbitrary coefficients
are a Mobius inverse. -/
noncomputable def fixedLinearTransform
    {node : Type x} {atom : Type y}
    [Fintype node]
    (coefficient : atom -> node -> Real)
    (cumulative : node -> Real)
    (atomKey : atom) : Real :=
  ∑ nodeKey, coefficient atomKey nodeKey * cumulative nodeKey

/-- A fixed linear transform preserves fixed-source-marginal informative invariance
coordinatewise.  No invertibility premise is needed. -/
theorem informative_fixed_linear_transform_invariant_of_source_marginal_eq
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    {node : Type x} {atom : Type y}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    [Fintype node]
    (leftLaw rightLaw : CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (collections : node -> Finset (Finset sourceIndex))
    (coefficient : atom -> node -> Real)
    (atomKey : atom)
    (hSourceMarginal :
      ∀ sourceKey,
        categoricalSourceMarginal leftLaw sourceKey =
          categoricalSourceMarginal rightLaw sourceKey) :
    fixedLinearTransform coefficient
        (fun nodeKey => averagedInformativeCumulative leftLaw (collections nodeKey)) atomKey =
      fixedLinearTransform coefficient
        (fun nodeKey => averagedInformativeCumulative rightLaw (collections nodeKey)) atomKey := by
  unfold fixedLinearTransform
  apply Finset.sum_congr rfl
  intro nodeKey _
  exact congrArg (fun value => coefficient atomKey nodeKey * value)
    (averaged_informative_cumulative_invariant_of_source_marginal_eq
      leftLaw rightLaw (collections nodeKey) hSourceMarginal)

/-- A fixed finite linear transform preserves informative invariance across different finite
target alphabets.  The coefficients are shared literally between the two sides; identifying them
as the intended Mobius inverse remains a separate proof obligation. -/
theorem informative_fixed_linear_transform_invariant_of_source_marginal_eq_heterogeneous_target
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v}
    {leftTargetValue : Type w} {rightTargetValue : Type x}
    {node : Type y} {atom : Type z}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)]
    [Fintype leftTargetValue] [Fintype rightTargetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq leftTargetValue] [DecidableEq rightTargetValue]
    [Fintype node]
    (leftLaw : CategoricalKey sourceIndex sourceValue leftTargetValue -> Real)
    (rightLaw : CategoricalKey sourceIndex sourceValue rightTargetValue -> Real)
    (collections : node -> Finset (Finset sourceIndex))
    (coefficient : atom -> node -> Real)
    (atomKey : atom)
    (hSourceMarginal :
      ∀ sourceKey,
        categoricalSourceMarginal leftLaw sourceKey =
          categoricalSourceMarginal rightLaw sourceKey) :
    fixedLinearTransform coefficient
        (fun nodeKey => averagedInformativeCumulative leftLaw (collections nodeKey)) atomKey =
      fixedLinearTransform coefficient
        (fun nodeKey => averagedInformativeCumulative rightLaw (collections nodeKey)) atomKey := by
  unfold fixedLinearTransform
  apply Finset.sum_congr rfl
  intro nodeKey _
  exact congrArg (fun value => coefficient atomKey nodeKey * value)
    (averaged_informative_cumulative_invariant_of_source_marginal_eq_heterogeneous_target
      leftLaw rightLaw (collections nodeKey) hSourceMarginal)

/-- Probability-semantic atom corollary.  Every node family is nonempty, both laws are finite
probability laws on the same alphabet, and the complete source marginals agree.  Therefore any one
fixed linear transform of the support-restricted informative cumulatives agrees at every supplied
atom key.  Calling the coefficients a Mobius inverse remains a separate proof obligation. -/
theorem probability_informative_fixed_linear_transform_invariant_of_source_marginal_eq
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v} {targetValue : Type w}
    {node : Type x} {atom : Type y}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue]
    [Fintype node]
    (leftLaw rightLaw : CategoricalKey sourceIndex sourceValue targetValue -> Real)
    (collections : node -> Finset (Finset sourceIndex))
    (coefficient : atom -> node -> Real)
    (atomKey : atom)
    (hCollections : ∀ nodeKey, (collections nodeKey).Nonempty)
    (hLeftProbability : IsCategoricalProbabilityLaw leftLaw)
    (hRightProbability : IsCategoricalProbabilityLaw rightLaw)
    (hSourceMarginal :
      ∀ sourceKey,
        categoricalSourceMarginal leftLaw sourceKey =
          categoricalSourceMarginal rightLaw sourceKey) :
    fixedLinearTransform coefficient
        (fun nodeKey =>
          averagedInformativeCumulativeOnPositiveSupport leftLaw (collections nodeKey)) atomKey =
      fixedLinearTransform coefficient
        (fun nodeKey =>
          averagedInformativeCumulativeOnPositiveSupport rightLaw (collections nodeKey)) atomKey := by
  unfold fixedLinearTransform
  apply Finset.sum_congr rfl
  intro nodeKey _
  exact congrArg (fun value => coefficient atomKey nodeKey * value)
    (probability_averaged_informative_invariant_of_source_marginal_eq
      leftLaw rightLaw (collections nodeKey) (hCollections nodeKey)
      hLeftProbability hRightProbability hSourceMarginal).1

/-- Probability-semantic fixed-linear-transform corollary across different finite target
alphabets.  It establishes support-safe equality, not paper correspondence of the event family or
Mobius coefficients. -/
theorem probability_informative_fixed_linear_transform_invariant_of_source_marginal_eq_heterogeneous_target
    {sourceIndex : Type u} {sourceValue : sourceIndex -> Type v}
    {leftTargetValue : Type w} {rightTargetValue : Type x}
    {node : Type y} {atom : Type z}
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)]
    [Fintype leftTargetValue] [Fintype rightTargetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq leftTargetValue] [DecidableEq rightTargetValue]
    [Fintype node]
    (leftLaw : CategoricalKey sourceIndex sourceValue leftTargetValue -> Real)
    (rightLaw : CategoricalKey sourceIndex sourceValue rightTargetValue -> Real)
    (collections : node -> Finset (Finset sourceIndex))
    (coefficient : atom -> node -> Real)
    (atomKey : atom)
    (hCollections : ∀ nodeKey, (collections nodeKey).Nonempty)
    (hLeftProbability : IsCategoricalProbabilityLaw leftLaw)
    (hRightProbability : IsCategoricalProbabilityLaw rightLaw)
    (hSourceMarginal :
      ∀ sourceKey,
        categoricalSourceMarginal leftLaw sourceKey =
          categoricalSourceMarginal rightLaw sourceKey) :
    fixedLinearTransform coefficient
        (fun nodeKey =>
          averagedInformativeCumulativeOnPositiveSupport leftLaw (collections nodeKey)) atomKey =
      fixedLinearTransform coefficient
        (fun nodeKey =>
          averagedInformativeCumulativeOnPositiveSupport rightLaw (collections nodeKey)) atomKey := by
  unfold fixedLinearTransform
  apply Finset.sum_congr rfl
  intro nodeKey _
  exact congrArg (fun value => coefficient atomKey nodeKey * value)
    (probability_averaged_informative_invariant_of_source_marginal_eq_heterogeneous_target
      leftLaw rightLaw (collections nodeKey) (hCollections nodeKey)
      hLeftProbability hRightProbability hSourceMarginal).1

end PidFiniteConvergence
