import PidFiniteConvergence
import Lean.Util.CollectAxioms

/-!
# Semantic contract for the exact two-source component and Mobius-atom bridge

This separately checked file pins the concrete two-source node, atom, component, and 24-coordinate
orders; the integer Mobius signs and zeta reconstruction; and an asymmetric finite count witness
whose local rational arguments and weighted products distinguish the informative,
misinformative, and signed-net components.  These examples concern exact supplied-count
mathematics only and do not widen the residual-scope boundary in the imported bridge.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators

open PidFiniteConvergence
open Lean

/-! The public finite orders and the full coordinate cardinality are exact. -/
example :
    sxPid2NodeOrder =
        [.sourceOne, .sourceTwo, .jointSources, .redundancy] ∧
      sxPid2AtomOrder =
        [.uniqueOne, .uniqueTwo, .synergy, .redundancy] ∧
      sxPid2ComponentOrder =
        [.informative, .misinformative, .net] ∧
      sxPid2CoordinateOrder.length = 24 ∧
      sxPid2CoordinateOrder.Nodup ∧
      Fintype.card SxPid2Coordinate = 24 := by
  exact
    ⟨rfl, rfl, rfl, sx_pid2_coordinate_order_length,
      sx_pid2_coordinate_order_nodup, sx_pid2_coordinate_card⟩

/-! The exact 24-coordinate order is cumulative-first and atom-second. -/
example :
    sxPid2CoordinateOrder =
      [
        .cumulative .informative .sourceOne,
        .cumulative .informative .sourceTwo,
        .cumulative .informative .jointSources,
        .cumulative .informative .redundancy,
        .cumulative .misinformative .sourceOne,
        .cumulative .misinformative .sourceTwo,
        .cumulative .misinformative .jointSources,
        .cumulative .misinformative .redundancy,
        .cumulative .net .sourceOne,
        .cumulative .net .sourceTwo,
        .cumulative .net .jointSources,
        .cumulative .net .redundancy,
        .atom .informative .uniqueOne,
        .atom .informative .uniqueTwo,
        .atom .informative .synergy,
        .atom .informative .redundancy,
        .atom .misinformative .uniqueOne,
        .atom .misinformative .uniqueTwo,
        .atom .misinformative .synergy,
        .atom .misinformative .redundancy,
        .atom .net .uniqueOne,
        .atom .net .uniqueTwo,
        .atom .net .synergy,
        .atom .net .redundancy
      ] := by
  rfl

/-! All sixteen entries of the concrete Mobius matrix are pinned, including structural zeros. -/
example :
    sxPid2MobiusCoefficient .uniqueOne .sourceOne = 1 ∧
      sxPid2MobiusCoefficient .uniqueOne .sourceTwo = 0 ∧
      sxPid2MobiusCoefficient .uniqueOne .jointSources = 0 ∧
      sxPid2MobiusCoefficient .uniqueOne .redundancy = -1 ∧
      sxPid2MobiusCoefficient .uniqueTwo .sourceOne = 0 ∧
      sxPid2MobiusCoefficient .uniqueTwo .sourceTwo = 1 ∧
      sxPid2MobiusCoefficient .uniqueTwo .jointSources = 0 ∧
      sxPid2MobiusCoefficient .uniqueTwo .redundancy = -1 ∧
      sxPid2MobiusCoefficient .synergy .sourceOne = -1 ∧
      sxPid2MobiusCoefficient .synergy .sourceTwo = -1 ∧
      sxPid2MobiusCoefficient .synergy .jointSources = 1 ∧
      sxPid2MobiusCoefficient .synergy .redundancy = 1 ∧
      sxPid2MobiusCoefficient .redundancy .sourceOne = 0 ∧
      sxPid2MobiusCoefficient .redundancy .sourceTwo = 0 ∧
      sxPid2MobiusCoefficient .redundancy .jointSources = 0 ∧
      sxPid2MobiusCoefficient .redundancy .redundancy = 1 := by
  norm_num [sxPid2MobiusCoefficient]

/-! All sixteen entries of the concrete zeta matrix are pinned, including structural zeros. -/
example :
    sxPid2ZetaCoefficient .sourceOne .uniqueOne = 1 ∧
      sxPid2ZetaCoefficient .sourceOne .uniqueTwo = 0 ∧
      sxPid2ZetaCoefficient .sourceOne .synergy = 0 ∧
      sxPid2ZetaCoefficient .sourceOne .redundancy = 1 ∧
      sxPid2ZetaCoefficient .sourceTwo .uniqueOne = 0 ∧
      sxPid2ZetaCoefficient .sourceTwo .uniqueTwo = 1 ∧
      sxPid2ZetaCoefficient .sourceTwo .synergy = 0 ∧
      sxPid2ZetaCoefficient .sourceTwo .redundancy = 1 ∧
      sxPid2ZetaCoefficient .jointSources .uniqueOne = 1 ∧
      sxPid2ZetaCoefficient .jointSources .uniqueTwo = 1 ∧
      sxPid2ZetaCoefficient .jointSources .synergy = 1 ∧
      sxPid2ZetaCoefficient .jointSources .redundancy = 1 ∧
      sxPid2ZetaCoefficient .redundancy .uniqueOne = 0 ∧
      sxPid2ZetaCoefficient .redundancy .uniqueTwo = 0 ∧
      sxPid2ZetaCoefficient .redundancy .synergy = 0 ∧
      sxPid2ZetaCoefficient .redundancy .redundancy = 1 := by
  norm_num [sxPid2ZetaCoefficient]

private def asymmetricCumulative : SxPid2Node → ℤ
  | .sourceOne => 17
  | .sourceTwo => 11
  | .jointSources => 31
  | .redundancy => 5

/-!
The concrete transform maps `[17, 11, 31, 5]` in node order to `[12, 6, 8, 5]` in atom order.
This simultaneously distinguishes both unique rows, both negative synergy entries, the positive
joint/redundancy synergy entries, and the bottom-row identity.
-/
example :
    sxPid2MobiusTransform asymmetricCumulative .uniqueOne = 12 ∧
      sxPid2MobiusTransform asymmetricCumulative .uniqueTwo = 6 ∧
      sxPid2MobiusTransform asymmetricCumulative .synergy = 8 ∧
      sxPid2MobiusTransform asymmetricCumulative .redundancy = 5 := by
  norm_num [sxPid2MobiusTransform, asymmetricCumulative]

/-! Zeta reconstruction returns all four asymmetric cumulative values. -/
example :
    sxPid2ZetaTransform (sxPid2MobiusTransform asymmetricCumulative) .sourceOne = 17 ∧
      sxPid2ZetaTransform (sxPid2MobiusTransform asymmetricCumulative) .sourceTwo = 11 ∧
      sxPid2ZetaTransform (sxPid2MobiusTransform asymmetricCumulative) .jointSources = 31 ∧
      sxPid2ZetaTransform (sxPid2MobiusTransform asymmetricCumulative) .redundancy = 5 := by
  norm_num [sxPid2ZetaTransform, sxPid2MobiusTransform, asymmetricCumulative]

private def weightedAsymmetricCount
    (key : CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2)) : ℕ :=
  match (key.1 0).val, (key.1 1).val, key.2.val with
  | 0, 0, 0 => 1
  | 0, 1, 0 => 2
  | 1, 0, 1 => 1
  | _, _, _ => 0

private def weightedAnchorZeroZero :
    CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2) :=
  (![0, 0], 0)

private def weightedAnchorZeroOne :
    CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2) :=
  (![0, 1], 0)

private def weightedAnchorOneZero :
    CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2) :=
  (![1, 0], 1)

private def allBinaryKeys :
    Finset (CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2)) :=
  {(![0, 0], 0), (![0, 0], 1), (![0, 1], 0), (![0, 1], 1),
    (![1, 0], 0), (![1, 0], 1), (![1, 1], 0), (![1, 1], 1)}

private def weightedPositiveKeys :
    Finset (CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2)) :=
  {weightedAnchorZeroZero, weightedAnchorZeroOne, weightedAnchorOneZero}

private theorem weighted_count_facts :
    totalCount weightedAsymmetricCount = 4 ∧
      eventCount weightedAsymmetricCount (targetBranchEvent weightedAnchorZeroZero) = 3 ∧
      eventCount weightedAsymmetricCount
          (sxPid2SourceEvent .sourceOne weightedAnchorZeroZero) = 3 ∧
      eventCount weightedAsymmetricCount
          (sxPid2SourceEvent .sourceTwo weightedAnchorZeroZero) = 2 ∧
      eventCount weightedAsymmetricCount
          (sxPid2SourceEvent .jointSources weightedAnchorZeroZero) = 1 ∧
      eventCount weightedAsymmetricCount
          (sxPid2SourceEvent .redundancy weightedAnchorZeroZero) = 4 ∧
      eventCount weightedAsymmetricCount
          (sxPid2TargetRestrictedEvent .sourceOne weightedAnchorZeroZero) = 3 ∧
      eventCount weightedAsymmetricCount
          (sxPid2TargetRestrictedEvent .sourceTwo weightedAnchorZeroZero) = 1 ∧
      eventCount weightedAsymmetricCount
          (sxPid2TargetRestrictedEvent .jointSources weightedAnchorZeroZero) = 1 ∧
      eventCount weightedAsymmetricCount
          (sxPid2TargetRestrictedEvent .redundancy weightedAnchorZeroZero) = 3 ∧
      eventCount weightedAsymmetricCount (targetBranchEvent weightedAnchorZeroOne) = 3 ∧
      eventCount weightedAsymmetricCount
          (sxPid2SourceEvent .sourceOne weightedAnchorZeroOne) = 3 ∧
      eventCount weightedAsymmetricCount
          (sxPid2SourceEvent .sourceTwo weightedAnchorZeroOne) = 2 ∧
      eventCount weightedAsymmetricCount
          (sxPid2SourceEvent .jointSources weightedAnchorZeroOne) = 2 ∧
      eventCount weightedAsymmetricCount
          (sxPid2SourceEvent .redundancy weightedAnchorZeroOne) = 3 ∧
      eventCount weightedAsymmetricCount
          (sxPid2TargetRestrictedEvent .sourceOne weightedAnchorZeroOne) = 3 ∧
      eventCount weightedAsymmetricCount
          (sxPid2TargetRestrictedEvent .sourceTwo weightedAnchorZeroOne) = 2 ∧
      eventCount weightedAsymmetricCount
          (sxPid2TargetRestrictedEvent .jointSources weightedAnchorZeroOne) = 2 ∧
      eventCount weightedAsymmetricCount
          (sxPid2TargetRestrictedEvent .redundancy weightedAnchorZeroOne) = 3 ∧
      eventCount weightedAsymmetricCount (targetBranchEvent weightedAnchorOneZero) = 1 ∧
      eventCount weightedAsymmetricCount
          (sxPid2SourceEvent .sourceOne weightedAnchorOneZero) = 1 ∧
      eventCount weightedAsymmetricCount
          (sxPid2SourceEvent .sourceTwo weightedAnchorOneZero) = 2 ∧
      eventCount weightedAsymmetricCount
          (sxPid2SourceEvent .jointSources weightedAnchorOneZero) = 1 ∧
      eventCount weightedAsymmetricCount
          (sxPid2SourceEvent .redundancy weightedAnchorOneZero) = 2 ∧
      eventCount weightedAsymmetricCount
          (sxPid2TargetRestrictedEvent .sourceOne weightedAnchorOneZero) = 1 ∧
      eventCount weightedAsymmetricCount
          (sxPid2TargetRestrictedEvent .sourceTwo weightedAnchorOneZero) = 1 ∧
      eventCount weightedAsymmetricCount
          (sxPid2TargetRestrictedEvent .jointSources weightedAnchorOneZero) = 1 ∧
      eventCount weightedAsymmetricCount
          (sxPid2TargetRestrictedEvent .redundancy weightedAnchorOneZero) = 1 :=
  set_option backward.isDefEq.respectTransparency.types false in by
  have h_univ :
      (Finset.univ : Finset (CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2))) =
        allBinaryKeys := by
    decide
  constructor
  · rw [totalCount, h_univ]
    decide
  simp only [eventCount, targetBranchEvent, targetEquivalent, sxPid2SourceEvent,
    sxPid2TargetRestrictedEvent, sxPid2Collections, sxSourceEvent,
    sxTargetRestrictedEvent, sourceBranchEvent, sourceTargetBranchEvent,
    sourceTargetCollectionEquivalent, sourceCollectionEquivalent]
  rw [h_univ]
  decide

private theorem weighted_total_positive : 0 < totalCount weightedAsymmetricCount := by
  rw [weighted_count_facts.1]
  decide

/-!
The three positive anchors pin all local component arguments.  The count-two anchor is retained so
the later product example distinguishes the exact empirical exponent from unweighted products.
-/
private theorem weighted_count_argument_facts :
    countComponentArgument weightedAsymmetricCount .informative .sourceOne
        weightedAnchorZeroZero = 4 / 3 ∧
      countComponentArgument weightedAsymmetricCount .informative .sourceTwo
          weightedAnchorZeroZero = 2 ∧
      countComponentArgument weightedAsymmetricCount .informative .jointSources
          weightedAnchorZeroZero = 4 ∧
      countComponentArgument weightedAsymmetricCount .informative .redundancy
          weightedAnchorZeroZero = 1 ∧
      countComponentArgument weightedAsymmetricCount .misinformative .sourceOne
          weightedAnchorZeroZero = 1 ∧
      countComponentArgument weightedAsymmetricCount .misinformative .sourceTwo
          weightedAnchorZeroZero = 3 ∧
      countComponentArgument weightedAsymmetricCount .misinformative .jointSources
          weightedAnchorZeroZero = 3 ∧
      countComponentArgument weightedAsymmetricCount .misinformative .redundancy
          weightedAnchorZeroZero = 1 ∧
      countComponentArgument weightedAsymmetricCount .net .sourceOne
          weightedAnchorZeroZero = 4 / 3 ∧
      countComponentArgument weightedAsymmetricCount .net .sourceTwo
          weightedAnchorZeroZero = 2 / 3 ∧
      countComponentArgument weightedAsymmetricCount .net .jointSources
          weightedAnchorZeroZero = 4 / 3 ∧
      countComponentArgument weightedAsymmetricCount .net .redundancy
          weightedAnchorZeroZero = 1 ∧
      countComponentArgument weightedAsymmetricCount .informative .sourceOne
          weightedAnchorZeroOne = 4 / 3 ∧
      countComponentArgument weightedAsymmetricCount .informative .sourceTwo
          weightedAnchorZeroOne = 2 ∧
      countComponentArgument weightedAsymmetricCount .informative .jointSources
          weightedAnchorZeroOne = 2 ∧
      countComponentArgument weightedAsymmetricCount .informative .redundancy
          weightedAnchorZeroOne = 4 / 3 ∧
      countComponentArgument weightedAsymmetricCount .misinformative .sourceOne
          weightedAnchorZeroOne = 1 ∧
      countComponentArgument weightedAsymmetricCount .misinformative .sourceTwo
          weightedAnchorZeroOne = 3 / 2 ∧
      countComponentArgument weightedAsymmetricCount .misinformative .jointSources
          weightedAnchorZeroOne = 3 / 2 ∧
      countComponentArgument weightedAsymmetricCount .misinformative .redundancy
          weightedAnchorZeroOne = 1 ∧
      countComponentArgument weightedAsymmetricCount .net .sourceOne
        weightedAnchorZeroOne = 4 / 3 ∧
      countComponentArgument weightedAsymmetricCount .net .sourceTwo
          weightedAnchorZeroOne = 4 / 3 ∧
      countComponentArgument weightedAsymmetricCount .net .jointSources
          weightedAnchorZeroOne = 4 / 3 ∧
      countComponentArgument weightedAsymmetricCount .net .redundancy
          weightedAnchorZeroOne = 4 / 3 ∧
      countComponentArgument weightedAsymmetricCount .informative .sourceOne
          weightedAnchorOneZero = 4 ∧
      countComponentArgument weightedAsymmetricCount .informative .sourceTwo
          weightedAnchorOneZero = 2 ∧
      countComponentArgument weightedAsymmetricCount .informative .jointSources
          weightedAnchorOneZero = 4 ∧
      countComponentArgument weightedAsymmetricCount .informative .redundancy
          weightedAnchorOneZero = 2 ∧
      countComponentArgument weightedAsymmetricCount .misinformative .sourceOne
          weightedAnchorOneZero = 1 ∧
      countComponentArgument weightedAsymmetricCount .misinformative .sourceTwo
          weightedAnchorOneZero = 1 ∧
      countComponentArgument weightedAsymmetricCount .misinformative .jointSources
          weightedAnchorOneZero = 1 ∧
      countComponentArgument weightedAsymmetricCount .misinformative .redundancy
          weightedAnchorOneZero = 1 ∧
      countComponentArgument weightedAsymmetricCount .net .sourceOne
          weightedAnchorOneZero = 4 ∧
      countComponentArgument weightedAsymmetricCount .net .sourceTwo
          weightedAnchorOneZero = 2 ∧
      countComponentArgument weightedAsymmetricCount .net .jointSources
          weightedAnchorOneZero = 4 ∧
      countComponentArgument weightedAsymmetricCount .net .redundancy
          weightedAnchorOneZero = 2 := by
  rcases weighted_count_facts with
    ⟨htotal, ht00, hs001, hs002, hs0012, hs00r, hr001, hr002, hr0012, hr00r,
      ht01, hs011, hs012, hs0112, hs01r, hr011, hr012, hr0112, hr01r,
      ht10, hs101, hs102, hs1012, hs10r, hr101, hr102, hr1012, hr10r⟩
  simp only [countComponentArgument, countInformativeArgument,
    countMisinformativeArgument, countNetArgument]
  rw [htotal, ht00, hs001, hs002, hs0012, hs00r, hr001, hr002, hr0012, hr00r,
    ht01, hs011, hs012, hs0112, hs01r, hr011, hr012, hr0112, hr01r,
    ht10, hs101, hs102, hs1012, hs10r, hr101, hr102, hr1012, hr10r]
  norm_num

private theorem weighted_positive_product
    (factor : CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2) → ℚ) :
    ∏ anchor ∈ weightedPositiveKeys, factor anchor =
      factor weightedAnchorZeroZero * factor weightedAnchorZeroOne *
        factor weightedAnchorOneZero := by
  classical
  simp [weightedPositiveKeys, weightedAnchorZeroZero, weightedAnchorZeroOne,
    weightedAnchorOneZero]
  ring

/-!
The exact rational cumulative products include the count-two exponent.  Values are listed in node
order for each component.
-/
private theorem weighted_cumulative_products :
    countCumulativeRationalProduct weightedAsymmetricCount .informative .sourceOne = 256 / 27 ∧
      countCumulativeRationalProduct weightedAsymmetricCount .informative .sourceTwo = 16 ∧
      countCumulativeRationalProduct weightedAsymmetricCount .informative .jointSources = 64 ∧
      countCumulativeRationalProduct weightedAsymmetricCount .informative .redundancy = 32 / 9 ∧
      countCumulativeRationalProduct weightedAsymmetricCount .misinformative .sourceOne = 1 ∧
      countCumulativeRationalProduct weightedAsymmetricCount .misinformative .sourceTwo = 27 / 4 ∧
      countCumulativeRationalProduct weightedAsymmetricCount .misinformative .jointSources = 27 / 4 ∧
      countCumulativeRationalProduct weightedAsymmetricCount .misinformative .redundancy = 1 ∧
      countCumulativeRationalProduct weightedAsymmetricCount .net .sourceOne = 256 / 27 ∧
      countCumulativeRationalProduct weightedAsymmetricCount .net .sourceTwo = 64 / 27 ∧
      countCumulativeRationalProduct weightedAsymmetricCount .net .jointSources = 256 / 27 ∧
      countCumulativeRationalProduct weightedAsymmetricCount .net .redundancy = 32 / 9 := by
  have h_univ :
      (Finset.univ : Finset (CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2))) =
        allBinaryKeys := by
    decide
  have h_support : positiveSupport weightedAsymmetricCount = weightedPositiveKeys := by
    unfold positiveSupport
    rw [h_univ]
    decide
  rcases weighted_count_argument_facts with
    ⟨hi001, hi002, hi0012, hi00r, hm001, hm002, hm0012, hm00r,
      hn001, hn002, hn0012, hn00r, hi011, hi012, hi0112, hi01r,
      hm011, hm012, hm0112, hm01r, hn011, hn012, hn0112, hn01r,
      hi101, hi102, hi1012, hi10r, hm101, hm102, hm1012, hm10r,
      hn101, hn102, hn1012, hn10r⟩
  simp only [countCumulativeRationalProduct, h_support]
  simp_rw [weighted_positive_product]
  rw [hi001, hi002, hi0012, hi00r, hm001, hm002, hm0012, hm00r,
    hn001, hn002, hn0012, hn00r, hi011, hi012, hi0112, hi01r,
    hm011, hm012, hm0112, hm01r, hn011, hn012, hn0112, hn01r,
    hi101, hi102, hi1012, hi10r, hm101, hm102, hm1012, hm10r,
    hn101, hn102, hn1012, hn10r]
  norm_num [weightedAsymmetricCount, weightedAnchorZeroZero,
    weightedAnchorZeroOne, weightedAnchorOneZero]

/-! The multiplicative Mobius transform of those products has the exact atom values below. -/
private theorem weighted_atom_products :
    countAtomRationalProduct weightedAsymmetricCount .informative .uniqueOne = 8 / 3 ∧
      countAtomRationalProduct weightedAsymmetricCount .informative .uniqueTwo = 9 / 2 ∧
      countAtomRationalProduct weightedAsymmetricCount .informative .synergy = 3 / 2 ∧
      countAtomRationalProduct weightedAsymmetricCount .informative .redundancy = 32 / 9 ∧
      countAtomRationalProduct weightedAsymmetricCount .misinformative .uniqueOne = 1 ∧
      countAtomRationalProduct weightedAsymmetricCount .misinformative .uniqueTwo = 27 / 4 ∧
      countAtomRationalProduct weightedAsymmetricCount .misinformative .synergy = 1 ∧
      countAtomRationalProduct weightedAsymmetricCount .misinformative .redundancy = 1 ∧
      countAtomRationalProduct weightedAsymmetricCount .net .uniqueOne = 8 / 3 ∧
      countAtomRationalProduct weightedAsymmetricCount .net .uniqueTwo = 2 / 3 ∧
      countAtomRationalProduct weightedAsymmetricCount .net .synergy = 3 / 2 ∧
      countAtomRationalProduct weightedAsymmetricCount .net .redundancy = 32 / 9 := by
  rcases weighted_cumulative_products with
    ⟨hi1, hi2, hi12, hir, hm1, hm2, hm12, hmr, hn1, hn2, hn12, hnr⟩
  simp only [countAtomRationalProduct]
  rw [hi1, hi2, hi12, hir, hm1, hm2, hm12, hmr, hn1, hn2, hn12, hnr]
  norm_num

/-! The exact rational-to-real product bridge is instantiated on every fixture coordinate. -/
example (coordinate : SxPid2Coordinate) :
    countCoordinateRealProduct weightedAsymmetricCount coordinate =
      ((countCoordinateRationalProduct weightedAsymmetricCount coordinate : ℚ) : ℝ) := by
  exact count_coordinate_real_product_eq_rational_cast weightedAsymmetricCount coordinate

/-! The informative unique-one product `8/3` gives a strictly positive averaged coordinate. -/
example :
    0 < averagedSxPid2Coordinate (empiricalLaw weightedAsymmetricCount)
      (.atom .informative .uniqueOne) := by
  rcases weighted_atom_products with ⟨hiu1, _, _, _, _, _, _, _, _, _, _, _⟩
  apply (all_24_averaged_coordinates_positive_iff_product_gt_one
    weightedAsymmetricCount (.atom .informative .uniqueOne) weighted_total_positive).2
  rw [count_coordinate_real_product_eq_rational_cast]
  simp only [countCoordinateRationalProduct]
  rw [hiu1]
  norm_num

/-! The signed-net unique-two product `2/3` gives a strictly negative averaged coordinate. -/
example :
    averagedSxPid2Coordinate (empiricalLaw weightedAsymmetricCount)
        (.atom .net .uniqueTwo) < 0 := by
  rcases weighted_atom_products with ⟨_, _, _, _, _, _, _, _, _, hnu2, _, _⟩
  apply (all_24_averaged_coordinates_negative_iff_product_lt_one
    weightedAsymmetricCount (.atom .net .uniqueTwo) weighted_total_positive).2
  rw [count_coordinate_real_product_eq_rational_cast]
  simp only [countCoordinateRationalProduct]
  rw [hnu2]
  norm_num

/-! The misinformative unique-one product `1` gives an exactly zero averaged coordinate. -/
example :
    averagedSxPid2Coordinate (empiricalLaw weightedAsymmetricCount)
        (.atom .misinformative .uniqueOne) = 0 := by
  rcases weighted_atom_products with ⟨_, _, _, _, hmu1, _, _, _, _, _, _, _⟩
  apply (all_24_averaged_coordinates_zero_iff_product_eq_one
    weightedAsymmetricCount (.atom .misinformative .uniqueOne) weighted_total_positive).2
  rw [count_coordinate_real_product_eq_rational_cast]
  simp only [countCoordinateRationalProduct]
  rw [hmu1]
  norm_num

/-!
The imported theorem binds every coordinate to `1 / totalCount` times the logarithm of its exact
weighted product; no unscaled or differently weighted interpretation is admitted here.
-/
example
    (coordinate : SxPid2Coordinate) :
    averagedSxPid2Coordinate (empiricalLaw weightedAsymmetricCount) coordinate =
      (1 / (totalCount weightedAsymmetricCount : ℝ)) *
        Real.log (countCoordinateRealProduct weightedAsymmetricCount coordinate) := by
  apply all_24_averaged_coordinates_eq_scaled_log_product
  have h_univ :
      (Finset.univ : Finset (CategoricalKey (Fin 2) (fun _ => Fin 2) (Fin 2))) =
        allBinaryKeys := by
    decide
  rw [totalCount, h_univ]
  decide

/-! The six named fixture helpers use only the proof project's permitted logical basis. -/
run_cmd do
  let allowed :=
    ({} : NameSet)
      |>.insert ``propext
      |>.insert ``Classical.choice
      |>.insert ``Quot.sound
  let declarations : Array Name := #[
    ``weighted_count_facts,
    ``weighted_total_positive,
    ``weighted_count_argument_facts,
    ``weighted_positive_product,
    ``weighted_cumulative_products,
    ``weighted_atom_products,
  ]
  unless declarations.size == 6 do
    throwError
      m!"fixture-helper logical-basis inventory has {declarations.size} entries, expected 6"
  for declaration in declarations do
    let used ← collectAxioms declaration
    for assumption in used do
      unless allowed.contains assumption do
        throwError
          m!"unexpected logical assumption {assumption} used by fixture helper {declaration}"
