import PidFiniteConvergence.Dependence

/-!
# Algebraic core for sharper finite-discrete local-continuity bounds

This module proves exact-real algebraic obligations for a sharper finite-discrete SxPID
local-continuity argument:

* a zero-total signed vector acts on a bounded function through one half of its oscillation;
* the gradients of a negative event log, a nested-event log ratio, and an intersection
  pointwise-mutual-information expression have diameter at most the reciprocal mass of their
  smallest event;
* the four ordinary-diamond gradient coordinates have an exact max-exclusive diameter that is
  attained;
* the five conditioned-nested lifted coordinates have exact candidate extrema and an attained
  closed-form diameter;
* the eight conditioned-diamond lifted coordinates have exact candidate extrema, a sharp
  union-reciprocal diameter bound, and its normalized-mass corollary;
* the ordinary-diamond ratio lies between one and its floor-dependent algebraic ceiling;
* nonnegative coordinates whose sum is a bounded top value lie in the same bounded interval;
* an arbitrary fixed linear row transfers coordinatewise perturbation bounds through its
  absolute row sum;
* component and signed-net ranges give their respective half-range and full-range weight terms;
* the linear-row and weight bounds compose for finite averages; and
* every event mass along a line segment has a factorized lower bound.

The Boolean arguments below are only event-membership indicators. The module does not formalize
probability laws, event construction, differentiation, a path integral, or the analytic step that
integrates a gradient bound. It does not identify the generic rows or coordinates with the SxPID
redundancy lattice, formalize Makkeh--Gutknecht--Wibral Theorem IV.3, or prove refinement to the
pid-rs Rust implementation or binary64 arithmetic. It does not identify the conditioned-diamond
lifted gradient with net SxPID synergy. Those boundaries require separate evidence.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators

namespace PidFiniteConvergence

variable {ι κ : Type*}

/-- A zero-total finite signed vector acts on a function through at most one half of the
function's stated oscillation. The interval endpoints need not be attained. -/
theorem abs_zero_sum_weighted_sum_le_half_oscillation
    (indices : Finset ι) (signedWeight value : ι → ℝ)
    {lower upper l1Bound : ℝ}
    (hzero : ∑ i ∈ indices, signedWeight i = 0)
    (hlowerUpper : lower ≤ upper)
    (_hl1Nonnegative : 0 ≤ l1Bound)
    (hvalueRange : ∀ i ∈ indices, lower ≤ value i ∧ value i ≤ upper)
    (hl1 : ∑ i ∈ indices, |signedWeight i| ≤ l1Bound) :
    |∑ i ∈ indices, signedWeight i * value i| ≤
      l1Bound * (upper - lower) / 2 := by
  have hcenteredValue :
      ∀ i ∈ indices,
        |value i - (lower + upper) / 2| ≤ (upper - lower) / 2 := by
    intro i hi
    rw [abs_le]
    constructor <;> linarith [hvalueRange i hi]
  have hhalfRangeNonnegative : 0 ≤ (upper - lower) / 2 := by
    linarith
  have hcenter :
      (∑ i ∈ indices, signedWeight i * value i) =
        ∑ i ∈ indices,
          signedWeight i * (value i - (lower + upper) / 2) := by
    calc
      (∑ i ∈ indices, signedWeight i * value i) =
          ∑ i ∈ indices,
            (signedWeight i * (value i - (lower + upper) / 2) +
              signedWeight i * ((lower + upper) / 2)) := by
        apply Finset.sum_congr rfl
        intro i _
        ring
      _ =
          (∑ i ∈ indices,
            signedWeight i * (value i - (lower + upper) / 2)) +
          ∑ i ∈ indices, signedWeight i * ((lower + upper) / 2) :=
        Finset.sum_add_distrib
      _ =
          (∑ i ∈ indices,
            signedWeight i * (value i - (lower + upper) / 2)) +
          (∑ i ∈ indices, signedWeight i) * ((lower + upper) / 2) := by
        rw [Finset.sum_mul]
      _ =
          ∑ i ∈ indices,
            signedWeight i * (value i - (lower + upper) / 2) := by
        rw [hzero, zero_mul, add_zero]
  rw [hcenter]
  calc
    |∑ i ∈ indices,
        signedWeight i * (value i - (lower + upper) / 2)|
        ≤ ∑ i ∈ indices,
            |signedWeight i * (value i - (lower + upper) / 2)| :=
          Finset.abs_sum_le_sum_abs
            (f := fun i =>
              signedWeight i * (value i - (lower + upper) / 2)) indices
    _ =
        ∑ i ∈ indices,
          |signedWeight i| * |value i - (lower + upper) / 2| := by
      apply Finset.sum_congr rfl
      intro i _
      exact abs_mul (signedWeight i) (value i - (lower + upper) / 2)
    _ ≤
        ∑ i ∈ indices,
          |signedWeight i| * ((upper - lower) / 2) := by
      apply Finset.sum_le_sum
      intro i hi
      exact mul_le_mul_of_nonneg_left
        (hcenteredValue i hi) (abs_nonneg (signedWeight i))
    _ =
        (∑ i ∈ indices, |signedWeight i|) *
          ((upper - lower) / 2) := by
      rw [Finset.sum_mul]
    _ ≤ l1Bound * ((upper - lower) / 2) :=
      mul_le_mul_of_nonneg_right hl1 hhalfRangeNonnegative
    _ = l1Bound * (upper - lower) / 2 := by ring

/-- The derivative-shaped value for `-log eventMass` at one Boolean membership pattern. -/
noncomputable def negativeLogEventGradient
    (inside : Bool) (eventMass : ℝ) : ℝ :=
  match inside with
  | false => 0
  | true => -(1 / eventMass)

/-- Two negative-event-log gradient values differ by at most the reciprocal event mass. -/
theorem negative_log_event_gradient_diameter_le
    (insideX insideY : Bool) {eventMass : ℝ}
    (hevent : 0 < eventMass) :
    |negativeLogEventGradient insideX eventMass -
        negativeLogEventGradient insideY eventMass| ≤
      1 / eventMass := by
  have hreciprocalPositive : 0 < 1 / eventMass :=
    one_div_pos.mpr hevent
  rw [abs_le]
  constructor <;>
    cases insideX <;> cases insideY <;>
    simp only [negativeLogEventGradient] <;> linarith

/-- The derivative-shaped value for `log (largeMass / smallMass)` at one Boolean membership
pattern. The definition is algebraic and does not assert that the masses come from events. -/
noncomputable def nestedLogRatioGradient
    (inSmall inLarge : Bool) (smallMass largeMass : ℝ) : ℝ :=
  match inSmall, inLarge with
  | false, false => 0
  | false, true => 1 / largeMass
  | true, false => -(1 / smallMass)
  | true, true => 1 / largeMass - 1 / smallMass

/-- When the small membership implies the large membership, every nested-log-ratio gradient value
lies in an interval of width exactly `1 / smallMass`. -/
theorem nested_log_ratio_gradient_bounds
    (inSmall inLarge : Bool) {smallMass largeMass : ℝ}
    (hsmall : 0 < smallMass) (hsmallLarge : smallMass ≤ largeMass)
    (hnested : inSmall = true → inLarge = true) :
    1 / largeMass - 1 / smallMass ≤
        nestedLogRatioGradient inSmall inLarge smallMass largeMass ∧
      nestedLogRatioGradient inSmall inLarge smallMass largeMass ≤
        1 / largeMass := by
  have hlarge : 0 < largeMass := hsmall.trans_le hsmallLarge
  have hlargeReciprocalNonnegative : 0 ≤ 1 / largeMass :=
    (one_div_pos.mpr hlarge).le
  have hlargeReciprocalLe :
      1 / largeMass ≤ 1 / smallMass :=
    one_div_le_one_div_of_le hsmall hsmallLarge
  cases inSmall <;> cases inLarge
  · change
      1 / largeMass - 1 / smallMass ≤ 0 ∧
        0 ≤ 1 / largeMass
    constructor <;> linarith
  · change
      1 / largeMass - 1 / smallMass ≤ 1 / largeMass ∧
        1 / largeMass ≤ 1 / largeMass
    constructor <;> linarith
  · cases hnested rfl
  · change
      1 / largeMass - 1 / smallMass ≤
          1 / largeMass - 1 / smallMass ∧
        1 / largeMass - 1 / smallMass ≤ 1 / largeMass
    constructor <;> linarith

/-- Two valid membership patterns for nested events have log-ratio gradient values separated by
at most the reciprocal mass of the smaller event. -/
theorem nested_log_ratio_gradient_diameter_le
    (smallX largeX smallY largeY : Bool) {smallMass largeMass : ℝ}
    (hsmall : 0 < smallMass) (hsmallLarge : smallMass ≤ largeMass)
    (hnestedX : smallX = true → largeX = true)
    (hnestedY : smallY = true → largeY = true) :
    |nestedLogRatioGradient smallX largeX smallMass largeMass -
        nestedLogRatioGradient smallY largeY smallMass largeMass| ≤
      1 / smallMass := by
  have hx := nested_log_ratio_gradient_bounds
    smallX largeX hsmall hsmallLarge hnestedX
  have hy := nested_log_ratio_gradient_bounds
    smallY largeY hsmall hsmallLarge hnestedY
  rw [abs_le]
  constructor <;> linarith

/-- The derivative-shaped value for
`log intersectionMass - log leftMass - log rightMass` at one pair of Boolean memberships. -/
noncomputable def intersectionPmiGradient
    (inLeft inRight : Bool)
    (intersectionMass leftMass rightMass : ℝ) : ℝ :=
  match inLeft, inRight with
  | false, false => 0
  | false, true => -(1 / rightMass)
  | true, false => -(1 / leftMass)
  | true, true =>
      1 / intersectionMass - 1 / leftMass - 1 / rightMass

/-- Any two intersection-PMI gradient values differ by at most the reciprocal intersection mass.
Only positivity and the two marginal-mass order relations are used. -/
theorem intersection_pmi_gradient_diameter_le
    (leftX rightX leftY rightY : Bool)
    {intersectionMass leftMass rightMass : ℝ}
    (hintersection : 0 < intersectionMass)
    (hintersectionLeft : intersectionMass ≤ leftMass)
    (hintersectionRight : intersectionMass ≤ rightMass) :
    |intersectionPmiGradient leftX rightX
          intersectionMass leftMass rightMass -
        intersectionPmiGradient leftY rightY
          intersectionMass leftMass rightMass| ≤
      1 / intersectionMass := by
  have hleft : 0 < leftMass := hintersection.trans_le hintersectionLeft
  have hright : 0 < rightMass := hintersection.trans_le hintersectionRight
  have hintersectionReciprocalPositive : 0 < 1 / intersectionMass :=
    one_div_pos.mpr hintersection
  have hleftReciprocalPositive : 0 < 1 / leftMass :=
    one_div_pos.mpr hleft
  have hrightReciprocalPositive : 0 < 1 / rightMass :=
    one_div_pos.mpr hright
  have hleftReciprocalLe :
      1 / leftMass ≤ 1 / intersectionMass :=
    one_div_le_one_div_of_le hintersection hintersectionLeft
  have hrightReciprocalLe :
      1 / rightMass ≤ 1 / intersectionMass :=
    one_div_le_one_div_of_le hintersection hintersectionRight
  rw [abs_le]
  constructor <;>
    cases leftX <;> cases rightX <;> cases leftY <;> cases rightY <;>
    simp only [intersectionPmiGradient] <;> linarith

/-- The four algebraic coordinate classes of an ordinary two-source diamond. The names do not
encode a probability partition. -/
inductive DiamondCoordinate where
  | common
  | leftExclusive
  | rightExclusive
  | outside

/-- The ordinary-diamond gradient written in terms of four reciprocal masses:
`1/a`, `1/(a+b)`, `1/(a+c)`, and `1/(a+b+c)`. -/
noncomputable def ordinaryDiamondGradientFromReciprocals
    (coordinate : DiamondCoordinate)
    (reciprocalA reciprocalAB reciprocalAC reciprocalABC : ℝ) : ℝ :=
  match coordinate with
  | .common =>
      reciprocalAB + reciprocalAC - reciprocalA - reciprocalABC
  | .leftExclusive => reciprocalAB - reciprocalABC
  | .rightExclusive => reciprocalAC - reciprocalABC
  | .outside => 0

/-- Reciprocal order and reciprocal supermodularity give the exact ordinary-diamond coordinate
diameter `reciprocalA - min reciprocalAB reciprocalAC`. -/
theorem ordinary_diamond_gradient_exact_diameter_of_reciprocal_bounds
    (coordinateX coordinateY : DiamondCoordinate)
    {reciprocalA reciprocalAB reciprocalAC reciprocalABC : ℝ}
    (hABCAB : reciprocalABC ≤ reciprocalAB)
    (hABCAC : reciprocalABC ≤ reciprocalAC)
    (hABA : reciprocalAB ≤ reciprocalA)
    (hACA : reciprocalAC ≤ reciprocalA)
    (hSupermodular :
      reciprocalAB + reciprocalAC ≤ reciprocalA + reciprocalABC) :
    |ordinaryDiamondGradientFromReciprocals coordinateX
          reciprocalA reciprocalAB reciprocalAC reciprocalABC -
        ordinaryDiamondGradientFromReciprocals coordinateY
          reciprocalA reciprocalAB reciprocalAC reciprocalABC| ≤
      reciprocalA - min reciprocalAB reciprocalAC := by
  rw [abs_le]
  constructor <;>
    cases coordinateX <;> cases coordinateY <;>
    simp only [ordinaryDiamondGradientFromReciprocals] <;>
    by_cases hABAC : reciprocalAB ≤ reciprocalAC <;>
    simp [min_def, hABAC] <;> linarith

/-- Explicit reciprocal order inequalities force every pair of ordinary-diamond gradient
coordinates to differ by at most `reciprocalA - reciprocalABC`. This subtracts the union-mass
reciprocal that the coarser reciprocal-common-mass radius discards. -/
theorem ordinary_diamond_gradient_refined_diameter_of_reciprocal_bounds
    (coordinateX coordinateY : DiamondCoordinate)
    {reciprocalA reciprocalAB reciprocalAC reciprocalABC : ℝ}
    (hABCAB : reciprocalABC ≤ reciprocalAB)
    (hABCAC : reciprocalABC ≤ reciprocalAC)
    (hABA : reciprocalAB ≤ reciprocalA)
    (hACA : reciprocalAC ≤ reciprocalA) :
    |ordinaryDiamondGradientFromReciprocals coordinateX
          reciprocalA reciprocalAB reciprocalAC reciprocalABC -
        ordinaryDiamondGradientFromReciprocals coordinateY
          reciprocalA reciprocalAB reciprocalAC reciprocalABC| ≤
      reciprocalA - reciprocalABC := by
  rw [abs_le]
  constructor <;>
    cases coordinateX <;> cases coordinateY <;>
    simp only [ordinaryDiamondGradientFromReciprocals] <;> linarith

/-- The coarser reciprocal-mass ordinary-diamond bound follows from the refined diameter when
`reciprocalABC` is nonnegative. -/
theorem ordinary_diamond_gradient_diameter_of_reciprocal_bounds
    (coordinateX coordinateY : DiamondCoordinate)
    {reciprocalA reciprocalAB reciprocalAC reciprocalABC : ℝ}
    (hABCNonnegative : 0 ≤ reciprocalABC)
    (hABCAB : reciprocalABC ≤ reciprocalAB)
    (hABCAC : reciprocalABC ≤ reciprocalAC)
    (hABA : reciprocalAB ≤ reciprocalA)
    (hACA : reciprocalAC ≤ reciprocalA) :
    |ordinaryDiamondGradientFromReciprocals coordinateX
          reciprocalA reciprocalAB reciprocalAC reciprocalABC -
        ordinaryDiamondGradientFromReciprocals coordinateY
          reciprocalA reciprocalAB reciprocalAC reciprocalABC| ≤
      reciprocalA := by
  refine
    (ordinary_diamond_gradient_refined_diameter_of_reciprocal_bounds
      coordinateX coordinateY hABCAB hABCAC hABA hACA).trans ?_
  linarith

/-- Reciprocal supermodularity and nesting give the ordinary-diamond gradient sign pattern. -/
theorem ordinary_diamond_gradient_signs_of_reciprocal_bounds
    {reciprocalA reciprocalAB reciprocalAC reciprocalABC : ℝ}
    (hABCAB : reciprocalABC ≤ reciprocalAB)
    (hABCAC : reciprocalABC ≤ reciprocalAC)
    (hsupermodular :
      reciprocalAB + reciprocalAC ≤ reciprocalA + reciprocalABC) :
    ordinaryDiamondGradientFromReciprocals .common
          reciprocalA reciprocalAB reciprocalAC reciprocalABC ≤ 0 ∧
      0 ≤ ordinaryDiamondGradientFromReciprocals .leftExclusive
          reciprocalA reciprocalAB reciprocalAC reciprocalABC ∧
      0 ≤ ordinaryDiamondGradientFromReciprocals .rightExclusive
          reciprocalA reciprocalAB reciprocalAC reciprocalABC ∧
      ordinaryDiamondGradientFromReciprocals .outside
          reciprocalA reciprocalAB reciprocalAC reciprocalABC = 0 := by
  simp only [ordinaryDiamondGradientFromReciprocals]
  constructor
  · linarith
  · constructor
    · linarith
    · constructor
      · linarith
      · trivial

/-- Reciprocal mass is supermodular on the ordinary diamond. The exact difference is a
nonnegative rational expression with numerator `b * c * (2 * a + b + c)`. -/
theorem ordinary_diamond_reciprocal_supermodular
    {a b c : ℝ} (ha : 0 < a) (hb : 0 ≤ b) (hc : 0 ≤ c) :
    1 / (a + b) + 1 / (a + c) ≤
      1 / a + 1 / (a + b + c) := by
  have hab : 0 < a + b := by linarith
  have hac : 0 < a + c := by linarith
  have habc : 0 < a + b + c := by linarith
  have hidentity :
      (1 / a + 1 / (a + b + c)) -
          (1 / (a + b) + 1 / (a + c)) =
        b * c * (2 * a + b + c) /
          (a * (a + b) * (a + c) * (a + b + c)) := by
    field_simp
    ring
  apply sub_nonneg.mp
  rw [hidentity]
  exact div_nonneg
    (mul_nonneg
      (mul_nonneg hb hc)
      (by linarith))
    (mul_nonneg
      (mul_nonneg
        (mul_nonneg ha.le hab.le)
        hac.le)
      habc.le)

/-- The ordinary-diamond gradient evaluated from positive masses. -/
noncomputable def ordinaryDiamondGradient
    (coordinate : DiamondCoordinate) (a b c : ℝ) : ℝ :=
  ordinaryDiamondGradientFromReciprocals coordinate
    (1 / a) (1 / (a + b)) (1 / (a + c)) (1 / (a + b + c))

/-- Every pair of ordinary-diamond gradient coordinates differs by at most the exact coordinate
diameter `1 / a - 1 / (a + max b c)`. -/
theorem ordinary_diamond_gradient_exact_coordinate_diameter_le
    (coordinateX coordinateY : DiamondCoordinate)
    {a b c : ℝ} (ha : 0 < a) (hb : 0 ≤ b) (hc : 0 ≤ c) :
    |ordinaryDiamondGradient coordinateX a b c -
        ordinaryDiamondGradient coordinateY a b c| ≤
      1 / a - 1 / (a + max b c) := by
  have hab : 0 < a + b := by linarith
  have hac : 0 < a + c := by linarith
  have hreciprocal :=
    ordinary_diamond_gradient_exact_diameter_of_reciprocal_bounds
      coordinateX coordinateY
      (one_div_le_one_div_of_le hab (by linarith : a + b ≤ a + b + c))
      (one_div_le_one_div_of_le hac (by linarith : a + c ≤ a + b + c))
      (one_div_le_one_div_of_le ha (by linarith : a ≤ a + b))
      (one_div_le_one_div_of_le ha (by linarith : a ≤ a + c))
      (ordinary_diamond_reciprocal_supermodular ha hb hc)
  calc
    |ordinaryDiamondGradient coordinateX a b c -
        ordinaryDiamondGradient coordinateY a b c| ≤
        1 / a - min (1 / (a + b)) (1 / (a + c)) := hreciprocal
    _ = 1 / a - 1 / (a + max b c) := by
      rcases le_total b c with hbc | hcb
      · have hreciprocalOrder :
            1 / (a + c) ≤ 1 / (a + b) :=
          one_div_le_one_div_of_le hab (by linarith)
        rw [max_eq_right hbc, min_eq_right hreciprocalOrder]
      · have hreciprocalOrder :
            1 / (a + b) ≤ 1 / (a + c) :=
          one_div_le_one_div_of_le hac (by linarith)
        rw [max_eq_left hcb, min_eq_left hreciprocalOrder]

/-- If `b ≤ c`, the left-exclusive and common coordinates attain the exact ordinary-diamond
diameter. -/
theorem ordinary_diamond_gradient_exact_coordinate_diameter_attained_of_left_le_right
    {a b c : ℝ} (ha : 0 < a) (hc : 0 ≤ c)
    (hbc : b ≤ c) :
    |ordinaryDiamondGradient .leftExclusive a b c -
        ordinaryDiamondGradient .common a b c| =
      1 / a - 1 / (a + max b c) := by
  have hac : 0 < a + c := by linarith
  have hnonnegative : 0 ≤ 1 / a - 1 / (a + c) := by
    exact sub_nonneg.mpr (one_div_le_one_div_of_le ha (by linarith))
  rw [max_eq_right hbc]
  simp only [ordinaryDiamondGradient, ordinaryDiamondGradientFromReciprocals]
  have hidentity :
      1 / (a + b) - 1 / (a + b + c) -
          (1 / (a + b) + 1 / (a + c) - 1 / a - 1 / (a + b + c)) =
        1 / a - 1 / (a + c) := by
    ring
  rw [hidentity, abs_of_nonneg hnonnegative]

/-- If `c ≤ b`, the right-exclusive and common coordinates attain the exact ordinary-diamond
diameter. -/
theorem ordinary_diamond_gradient_exact_coordinate_diameter_attained_of_right_le_left
    {a b c : ℝ} (ha : 0 < a) (hb : 0 ≤ b)
    (hcb : c ≤ b) :
    |ordinaryDiamondGradient .rightExclusive a b c -
        ordinaryDiamondGradient .common a b c| =
      1 / a - 1 / (a + max b c) := by
  have hab : 0 < a + b := by linarith
  have hnonnegative : 0 ≤ 1 / a - 1 / (a + b) := by
    exact sub_nonneg.mpr (one_div_le_one_div_of_le ha (by linarith))
  rw [max_eq_left hcb]
  simp only [ordinaryDiamondGradient, ordinaryDiamondGradientFromReciprocals]
  have hidentity :
      1 / (a + c) - 1 / (a + b + c) -
          (1 / (a + b) + 1 / (a + c) - 1 / a - 1 / (a + b + c)) =
        1 / a - 1 / (a + b) := by
    ring
  rw [hidentity, abs_of_nonneg hnonnegative]

/-- Some ordered pair of ordinary-diamond coordinates attains the exact coordinate diameter. -/
theorem ordinary_diamond_gradient_exact_coordinate_diameter_attained
    {a b c : ℝ} (ha : 0 < a) (hb : 0 ≤ b) (hc : 0 ≤ c) :
    ∃ coordinateX coordinateY : DiamondCoordinate,
      |ordinaryDiamondGradient coordinateX a b c -
          ordinaryDiamondGradient coordinateY a b c| =
        1 / a - 1 / (a + max b c) := by
  rcases le_total b c with hbc | hcb
  · exact ⟨.leftExclusive, .common,
      ordinary_diamond_gradient_exact_coordinate_diameter_attained_of_left_le_right
        ha hc hbc⟩
  · exact ⟨.rightExclusive, .common,
      ordinary_diamond_gradient_exact_coordinate_diameter_attained_of_right_le_left
        ha hb hcb⟩

/-- Every pair of ordinary-diamond gradient coordinates differs by at most
`1 / a - 1 / (a + b + c)`. -/
theorem ordinary_diamond_gradient_refined_coordinate_diameter_le
    (coordinateX coordinateY : DiamondCoordinate)
    {a b c : ℝ} (ha : 0 < a) (hb : 0 ≤ b) (hc : 0 ≤ c) :
    |ordinaryDiamondGradient coordinateX a b c -
        ordinaryDiamondGradient coordinateY a b c| ≤
      1 / a - 1 / (a + b + c) := by
  refine
    (ordinary_diamond_gradient_exact_coordinate_diameter_le
      coordinateX coordinateY ha hb hc).trans ?_
  rcases le_total b c with hbc | hcb
  · rw [max_eq_right hbc]
    have hac : 0 < a + c := by linarith
    have hreciprocal :
        1 / (a + b + c) ≤ 1 / (a + c) :=
      one_div_le_one_div_of_le hac (by linarith)
    linarith
  · rw [max_eq_left hcb]
    have hab : 0 < a + b := by linarith
    have hreciprocal :
        1 / (a + b + c) ≤ 1 / (a + b) :=
      one_div_le_one_div_of_le hab (by linarith)
    linarith

/-- The coarser `1 / a` ordinary-diamond bound follows from the refined mass bound. -/
theorem ordinary_diamond_gradient_coordinate_diameter_le
    (coordinateX coordinateY : DiamondCoordinate)
    {a b c : ℝ} (ha : 0 < a) (hb : 0 ≤ b) (hc : 0 ≤ c) :
    |ordinaryDiamondGradient coordinateX a b c -
        ordinaryDiamondGradient coordinateY a b c| ≤
      1 / a := by
  have habc : 0 < a + b + c := by linarith
  refine
    (ordinary_diamond_gradient_refined_coordinate_diameter_le
      coordinateX coordinateY ha hb hc).trans ?_
  exact sub_le_self _ (one_div_pos.mpr habc).le

/-- The positive ratio inside the ordinary-diamond logarithm. -/
noncomputable def ordinaryDiamondRatio (a b c : ℝ) : ℝ :=
  ((a + b) * (a + c)) / (a * (a + b + c))

/-- The ordinary-diamond ratio bounds in denominator-cleared form. The upper inequality is the
algebraic form of the floor-dependent `L - 2h` ceiling after taking logarithms. -/
theorem ordinary_diamond_ratio_cross_multiplication_bounds
    {floorMass a b c : ℝ}
    (hfloor : 0 < floorMass)
    (hfloorA : floorMass ≤ a)
    (hb : 0 ≤ b) (hc : 0 ≤ c)
    (htotal : a + b + c ≤ 1) :
    a * (a + b + c) ≤ (a + b) * (a + c) ∧
      4 * floorMass * ((a + b) * (a + c)) ≤
        (1 + floorMass) ^ 2 * (a * (a + b + c)) := by
  have ha : 0 < a := hfloor.trans_le hfloorA
  have haNonnegative : 0 ≤ a := ha.le
  have hsumPositive : 0 < a + b + c := by linarith
  have haSum : a ≤ a + b + c := by linarith
  have hfloorOne : floorMass ≤ 1 :=
    hfloorA.trans (haSum.trans htotal)
  have hfloorMulALeA : floorMass * a ≤ a := by
    nlinarith [mul_nonneg (sub_nonneg.mpr hfloorOne) haNonnegative]
  have hfloorMulALeSum :
      floorMass * a ≤ a + b + c :=
    hfloorMulALeA.trans haSum
  have hfloorMulSumLeFloor :
      floorMass * (a + b + c) ≤ floorMass := by
    nlinarith [mul_nonneg hfloor.le (sub_nonneg.mpr htotal)]
  have hfloorMulSumLeA :
      floorMass * (a + b + c) ≤ a :=
    hfloorMulSumLeFloor.trans hfloorA
  have hfactorNonnegative :
      0 ≤
        ((a + b + c) - floorMass * a) *
          (a - floorMass * (a + b + c)) :=
    mul_nonneg
      (sub_nonneg.mpr hfloorMulALeSum)
      (sub_nonneg.mpr hfloorMulSumLeA)
  have hmiddle :
      floorMass * (a + (a + b + c)) ^ 2 ≤
        (1 + floorMass) ^ 2 * (a * (a + b + c)) := by
    nlinarith [hfactorNonnegative]
  have hamgm :
      4 * ((a + b) * (a + c)) ≤
        (2 * a + b + c) ^ 2 := by
    nlinarith [sq_nonneg (b - c)]
  constructor
  · nlinarith [mul_nonneg hb hc]
  · calc
      4 * floorMass * ((a + b) * (a + c)) =
          floorMass * (4 * ((a + b) * (a + c))) := by ring
      _ ≤ floorMass * (2 * a + b + c) ^ 2 :=
        mul_le_mul_of_nonneg_left hamgm hfloor.le
      _ = floorMass * (a + (a + b + c)) ^ 2 := by ring
      _ ≤ (1 + floorMass) ^ 2 * (a * (a + b + c)) :=
        hmiddle

/-- The ordinary-diamond ratio lies between one and
`(1 + floorMass)^2 / (4 * floorMass)`. -/
theorem ordinary_diamond_ratio_bounds
    {floorMass a b c : ℝ}
    (hfloor : 0 < floorMass)
    (hfloorA : floorMass ≤ a)
    (hb : 0 ≤ b) (hc : 0 ≤ c)
    (htotal : a + b + c ≤ 1) :
    1 ≤ ordinaryDiamondRatio a b c ∧
      ordinaryDiamondRatio a b c ≤
        (1 + floorMass) ^ 2 / (4 * floorMass) := by
  have ha : 0 < a := hfloor.trans_le hfloorA
  have hsumPositive : 0 < a + b + c := by linarith
  have hdenominator : 0 < a * (a + b + c) :=
    mul_pos ha hsumPositive
  have hfloorDenominator : 0 < 4 * floorMass := by positivity
  have hcross :=
    ordinary_diamond_ratio_cross_multiplication_bounds
      hfloor hfloorA hb hc htotal
  constructor
  · apply (le_div_iff₀ hdenominator).2
    simpa [ordinaryDiamondRatio] using hcross.1
  · change
      ((a + b) * (a + c)) / (a * (a + b + c)) ≤
        (1 + floorMass) ^ 2 / (4 * floorMass)
    apply (div_le_div_iff₀ hdenominator hfloorDenominator).2
    simpa only [mul_assoc, mul_comm, mul_left_comm] using hcross.2

/-- The logarithmic ordinary-diamond value. -/
noncomputable def ordinaryDiamondPhi (a b c : ℝ) : ℝ :=
  Real.log (ordinaryDiamondRatio a b c)

/-- The ordinary-diamond logarithmic value is nonnegative. -/
theorem ordinary_diamond_phi_nonnegative
    {a b c : ℝ} (ha : 0 < a) (hb : 0 ≤ b) (hc : 0 ≤ c) :
    0 ≤ ordinaryDiamondPhi a b c := by
  have hsumPositive : 0 < a + b + c := by linarith
  have hdenominator : 0 < a * (a + b + c) :=
    mul_pos ha hsumPositive
  apply Real.log_nonneg
  change 1 ≤ ((a + b) * (a + c)) / (a * (a + b + c))
  apply (le_div_iff₀ hdenominator).2
  nlinarith [mul_nonneg hb hc]

/-- The ordinary-diamond logarithmic value is at most the logarithm of the algebraic
floor-dependent ceiling. -/
theorem ordinary_diamond_phi_le_floor_log_ceiling
    {floorMass a b c : ℝ}
    (hfloor : 0 < floorMass)
    (hfloorA : floorMass ≤ a)
    (hb : 0 ≤ b) (hc : 0 ≤ c)
    (htotal : a + b + c ≤ 1) :
    ordinaryDiamondPhi a b c ≤
      Real.log ((1 + floorMass) ^ 2 / (4 * floorMass)) := by
  have hratio :=
    ordinary_diamond_ratio_bounds hfloor hfloorA hb hc htotal
  exact Real.log_le_log
    (zero_lt_one.trans_le hratio.1) hratio.2

/-- The logarithm of the algebraic floor ceiling is exactly `L - 2h` when
`L = -log floorMass` and `h = log (2 / (1 + floorMass))`. -/
theorem ordinary_diamond_floor_log_ceiling_eq
    {floorMass : ℝ} (hfloor : 0 < floorMass) :
    Real.log ((1 + floorMass) ^ 2 / (4 * floorMass)) =
      -Real.log floorMass -
        2 * Real.log (2 / (1 + floorMass)) := by
  have honeFloor : 1 + floorMass ≠ 0 := by linarith
  have hfloorNe : floorMass ≠ 0 := hfloor.ne'
  have hfourNe : (4 : ℝ) ≠ 0 := by norm_num
  have htwoNe : (2 : ℝ) ≠ 0 := by norm_num
  have hlogFour :
      Real.log (4 : ℝ) = 2 * Real.log (2 : ℝ) := by
    calc
      Real.log (4 : ℝ) = Real.log ((2 : ℝ) * 2) := by norm_num
      _ = Real.log (2 : ℝ) + Real.log (2 : ℝ) :=
        Real.log_mul htwoNe htwoNe
      _ = 2 * Real.log (2 : ℝ) := by ring
  rw [Real.log_div (pow_ne_zero 2 honeFloor) (mul_ne_zero hfourNe hfloorNe)]
  rw [Real.log_pow]
  rw [Real.log_mul hfourNe hfloorNe]
  rw [Real.log_div htwoNe honeFloor]
  rw [hlogFour]
  norm_num
  ring

/-- The ordinary-diamond value obeys the floor-dependent `L - 2h` upper bound. -/
theorem ordinary_diamond_phi_le_floor_radius_sub_twice_correction
    {floorMass a b c : ℝ}
    (hfloor : 0 < floorMass)
    (hfloorA : floorMass ≤ a)
    (hb : 0 ≤ b) (hc : 0 ≤ c)
    (htotal : a + b + c ≤ 1) :
    ordinaryDiamondPhi a b c ≤
      -Real.log floorMass -
        2 * Real.log (2 / (1 + floorMass)) := by
  rw [← ordinary_diamond_floor_log_ceiling_eq hfloor]
  exact ordinary_diamond_phi_le_floor_log_ceiling
    hfloor hfloorA hb hc htotal

/-- The ordinary-diamond value lies between zero and the floor-dependent `L - 2h` ceiling. -/
theorem ordinary_diamond_phi_floor_bounds
    {floorMass a b c : ℝ}
    (hfloor : 0 < floorMass)
    (hfloorA : floorMass ≤ a)
    (hb : 0 ≤ b) (hc : 0 ≤ c)
    (htotal : a + b + c ≤ 1) :
    0 ≤ ordinaryDiamondPhi a b c ∧
      ordinaryDiamondPhi a b c ≤
        -Real.log floorMass -
          2 * Real.log (2 / (1 + floorMass)) := by
  constructor
  · exact ordinary_diamond_phi_nonnegative
      (hfloor.trans_le hfloorA) hb hc
  · exact ordinary_diamond_phi_le_floor_radius_sub_twice_correction
      hfloor hfloorA hb hc htotal

/-- The floor-dependent `L - 2h` algebraic expression is nonnegative for every positive input. -/
theorem ordinary_diamond_floor_radius_sub_twice_correction_nonnegative
    {floorMass : ℝ} (hfloor : 0 < floorMass) :
    0 ≤ -Real.log floorMass -
      2 * Real.log (2 / (1 + floorMass)) := by
  have hdenominator : 0 < 4 * floorMass := by positivity
  have hratio :
      1 ≤ (1 + floorMass) ^ 2 / (4 * floorMass) := by
    apply (le_div_iff₀ hdenominator).2
    nlinarith [sq_nonneg (1 - floorMass)]
  rw [← ordinary_diamond_floor_log_ceiling_eq hfloor]
  exact Real.log_nonneg hratio

/-- The five coordinate classes in the lifted gradient of a conditioned nested-event
difference. The labels describe algebraic positions only. -/
inductive ConditionedNestedCoordinate where
  | totalSmall
  | totalExclusive
  | conditionedSmall
  | conditionedExclusive
  | outside

/-- The conditioned-nested lifted gradient written in terms of
`1/x_a`, `1/(x_a+x_b)`, `1/(x_a+y_a)`, and
`1/(x_a+x_b+y_a+y_b)`. -/
noncomputable def conditionedNestedLiftedGradientFromReciprocals
    (coordinate : ConditionedNestedCoordinate)
    (reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB : ℝ) : ℝ :=
  match coordinate with
  | .totalSmall => reciprocalTotalAB - reciprocalTotalA
  | .totalExclusive => reciprocalTotalAB
  | .conditionedSmall =>
      reciprocalTotalAB - reciprocalTotalA - reciprocalXAB + reciprocalXA
  | .conditionedExclusive => reciprocalTotalAB - reciprocalXAB
  | .outside => 0

/-- The lower candidate among the full-event small coordinate and the conditioned exclusive
coordinate. -/
noncomputable def conditionedNestedLiftedGradientLowerFromReciprocals
    (reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB : ℝ) : ℝ :=
  min
    (conditionedNestedLiftedGradientFromReciprocals .totalSmall
      reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB)
    (conditionedNestedLiftedGradientFromReciprocals .conditionedExclusive
      reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB)

/-- The upper candidate among the full-event exclusive coordinate and the conditioned small
coordinate. -/
noncomputable def conditionedNestedLiftedGradientUpperFromReciprocals
    (reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB : ℝ) : ℝ :=
  max
    (conditionedNestedLiftedGradientFromReciprocals .totalExclusive
      reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB)
    (conditionedNestedLiftedGradientFromReciprocals .conditionedSmall
      reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB)

/-- The candidate-maximum minus candidate-minimum expression has a closed form independent of
the full-union reciprocal. This is an unconditional identity between exact real expressions. -/
theorem conditioned_nested_lifted_gradient_candidate_diameter_eq_of_reciprocals
    (reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB : ℝ) :
    conditionedNestedLiftedGradientUpperFromReciprocals
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB -
        conditionedNestedLiftedGradientLowerFromReciprocals
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB =
      max
        (max reciprocalTotalA reciprocalXAB)
        (max
          (reciprocalXA - reciprocalXAB)
          (reciprocalXA - reciprocalTotalA)) := by
  simp only [
    conditionedNestedLiftedGradientUpperFromReciprocals,
    conditionedNestedLiftedGradientLowerFromReciprocals,
    conditionedNestedLiftedGradientFromReciprocals
  ]
  apply le_antisymm
  · rcases le_total
      (reciprocalTotalAB - reciprocalTotalA - reciprocalXAB + reciprocalXA)
      reciprocalTotalAB with hUpper | hUpper
    · rcases le_total
        (reciprocalTotalAB - reciprocalTotalA)
        (reciprocalTotalAB - reciprocalXAB) with hLower | hLower
      · rw [max_eq_left hUpper, min_eq_left hLower]
        calc
          reciprocalTotalAB -
                (reciprocalTotalAB - reciprocalTotalA) =
              reciprocalTotalA := by ring
          _ ≤ max reciprocalTotalA reciprocalXAB := le_max_left _ _
          _ ≤ max
                (max reciprocalTotalA reciprocalXAB)
                (max
                  (reciprocalXA - reciprocalXAB)
                  (reciprocalXA - reciprocalTotalA)) :=
            le_max_left _ _
      · rw [max_eq_left hUpper, min_eq_right hLower]
        calc
          reciprocalTotalAB -
                (reciprocalTotalAB - reciprocalXAB) =
              reciprocalXAB := by ring
          _ ≤ max reciprocalTotalA reciprocalXAB := le_max_right _ _
          _ ≤ max
                (max reciprocalTotalA reciprocalXAB)
                (max
                  (reciprocalXA - reciprocalXAB)
                  (reciprocalXA - reciprocalTotalA)) :=
            le_max_left _ _
    · rcases le_total
        (reciprocalTotalAB - reciprocalTotalA)
        (reciprocalTotalAB - reciprocalXAB) with hLower | hLower
      · rw [max_eq_right hUpper, min_eq_left hLower]
        calc
          reciprocalTotalAB - reciprocalTotalA - reciprocalXAB + reciprocalXA -
                (reciprocalTotalAB - reciprocalTotalA) =
              reciprocalXA - reciprocalXAB := by ring
          _ ≤ max
                (reciprocalXA - reciprocalXAB)
                (reciprocalXA - reciprocalTotalA) :=
            le_max_left _ _
          _ ≤ max
                (max reciprocalTotalA reciprocalXAB)
                (max
                  (reciprocalXA - reciprocalXAB)
                  (reciprocalXA - reciprocalTotalA)) :=
            le_max_right _ _
      · rw [max_eq_right hUpper, min_eq_right hLower]
        calc
          reciprocalTotalAB - reciprocalTotalA - reciprocalXAB + reciprocalXA -
                (reciprocalTotalAB - reciprocalXAB) =
              reciprocalXA - reciprocalTotalA := by ring
          _ ≤ max
                (reciprocalXA - reciprocalXAB)
                (reciprocalXA - reciprocalTotalA) :=
            le_max_right _ _
          _ ≤ max
                (max reciprocalTotalA reciprocalXAB)
                (max
                  (reciprocalXA - reciprocalXAB)
                  (reciprocalXA - reciprocalTotalA)) :=
            le_max_right _ _
  · apply max_le
    · apply max_le
      · have hUpper := le_max_left
          reciprocalTotalAB
          (reciprocalTotalAB - reciprocalTotalA -
            reciprocalXAB + reciprocalXA)
        have hLower := min_le_left
          (reciprocalTotalAB - reciprocalTotalA)
          (reciprocalTotalAB - reciprocalXAB)
        linarith
      · have hUpper := le_max_left
          reciprocalTotalAB
          (reciprocalTotalAB - reciprocalTotalA -
            reciprocalXAB + reciprocalXA)
        have hLower := min_le_right
          (reciprocalTotalAB - reciprocalTotalA)
          (reciprocalTotalAB - reciprocalXAB)
        linarith
    · apply max_le
      · have hUpper := le_max_right
          reciprocalTotalAB
          (reciprocalTotalAB - reciprocalTotalA -
            reciprocalXAB + reciprocalXA)
        have hLower := min_le_left
          (reciprocalTotalAB - reciprocalTotalA)
          (reciprocalTotalAB - reciprocalXAB)
        linarith
      · have hUpper := le_max_right
          reciprocalTotalAB
          (reciprocalTotalAB - reciprocalTotalA -
            reciprocalXAB + reciprocalXA)
        have hLower := min_le_right
          (reciprocalTotalAB - reciprocalTotalA)
          (reciprocalTotalAB - reciprocalXAB)
        linarith

/-- Reciprocal order places every conditioned-nested coordinate between the two stated lower and
upper candidates. -/
theorem conditioned_nested_lifted_gradient_between_candidate_extrema_of_reciprocal_bounds
    (coordinate : ConditionedNestedCoordinate)
    {reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB : ℝ}
    (hTotalABNonnegative : 0 ≤ reciprocalTotalAB)
    (hTotalABTotalA : reciprocalTotalAB ≤ reciprocalTotalA)
    (hTotalABXAB : reciprocalTotalAB ≤ reciprocalXAB)
    (hXABXA : reciprocalXAB ≤ reciprocalXA) :
    conditionedNestedLiftedGradientLowerFromReciprocals
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB ≤
        conditionedNestedLiftedGradientFromReciprocals coordinate
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB ∧
      conditionedNestedLiftedGradientFromReciprocals coordinate
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB ≤
        conditionedNestedLiftedGradientUpperFromReciprocals
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB := by
  have hLowerTotalSmall :
      conditionedNestedLiftedGradientLowerFromReciprocals
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB ≤
        conditionedNestedLiftedGradientFromReciprocals .totalSmall
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB :=
    min_le_left _ _
  have hLowerConditionedExclusive :
      conditionedNestedLiftedGradientLowerFromReciprocals
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB ≤
        conditionedNestedLiftedGradientFromReciprocals .conditionedExclusive
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB :=
    min_le_right _ _
  have hUpperTotalExclusive :
      conditionedNestedLiftedGradientFromReciprocals .totalExclusive
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB ≤
        conditionedNestedLiftedGradientUpperFromReciprocals
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB :=
    le_max_left _ _
  have hUpperConditionedSmall :
      conditionedNestedLiftedGradientFromReciprocals .conditionedSmall
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB ≤
        conditionedNestedLiftedGradientUpperFromReciprocals
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB :=
    le_max_right _ _
  constructor <;>
    cases coordinate <;>
    simp only [
      conditionedNestedLiftedGradientLowerFromReciprocals,
      conditionedNestedLiftedGradientUpperFromReciprocals,
      conditionedNestedLiftedGradientFromReciprocals
    ] at * <;>
    linarith

/-- The reciprocal partial order for a conditioned nested-event difference bounds every pair of
lifted gradient coordinates by `reciprocalXA`. -/
theorem conditioned_nested_lifted_gradient_diameter_of_reciprocal_bounds
    (coordinateX coordinateY : ConditionedNestedCoordinate)
    {reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB : ℝ}
    (hTotalABNonnegative : 0 ≤ reciprocalTotalAB)
    (hTotalABTotalA : reciprocalTotalAB ≤ reciprocalTotalA)
    (hTotalAXA : reciprocalTotalA ≤ reciprocalXA)
    (hTotalABXAB : reciprocalTotalAB ≤ reciprocalXAB)
    (hXABXA : reciprocalXAB ≤ reciprocalXA) :
    |conditionedNestedLiftedGradientFromReciprocals coordinateX
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB -
        conditionedNestedLiftedGradientFromReciprocals coordinateY
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB| ≤
      reciprocalXA := by
  rw [abs_le]
  constructor <;>
    cases coordinateX <;> cases coordinateY <;>
    simp only [conditionedNestedLiftedGradientFromReciprocals] <;> linarith

/-- The conditioned-nested lifted gradient evaluated from four nonnegative region masses. -/
noncomputable def conditionedNestedLiftedGradient
    (coordinate : ConditionedNestedCoordinate)
    (xA xB yA yB : ℝ) : ℝ :=
  conditionedNestedLiftedGradientFromReciprocals coordinate
    (1 / xA)
    (1 / (xA + xB))
    (1 / (xA + yA))
    (1 / (xA + xB + yA + yB))

/-- The minimum candidate among the full-event small coordinate and the conditioned exclusive
coordinate. -/
noncomputable def conditionedNestedLiftedGradientLower
    (xA xB yA yB : ℝ) : ℝ :=
  min
    (conditionedNestedLiftedGradient .totalSmall xA xB yA yB)
    (conditionedNestedLiftedGradient .conditionedExclusive xA xB yA yB)

/-- The maximum candidate among the full-event exclusive coordinate and the conditioned small
coordinate. -/
noncomputable def conditionedNestedLiftedGradientUpper
    (xA xB yA yB : ℝ) : ℝ :=
  max
    (conditionedNestedLiftedGradient .totalExclusive xA xB yA yB)
    (conditionedNestedLiftedGradient .conditionedSmall xA xB yA yB)

/-- Under the natural mass assumptions, every conditioned-nested lifted coordinate lies between
the candidate minimum and maximum. -/
theorem conditioned_nested_lifted_gradient_between_candidate_extrema
    (coordinate : ConditionedNestedCoordinate)
    {xA xB yA yB : ℝ}
    (hxA : 0 < xA) (hxB : 0 ≤ xB) (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) :
    conditionedNestedLiftedGradientLower xA xB yA yB ≤
        conditionedNestedLiftedGradient coordinate xA xB yA yB ∧
      conditionedNestedLiftedGradient coordinate xA xB yA yB ≤
        conditionedNestedLiftedGradientUpper xA xB yA yB := by
  have hxAB : 0 < xA + xB := by linarith
  have htotalA : 0 < xA + yA := by linarith
  have htotalAB : 0 < xA + xB + yA + yB := by linarith
  simpa only [
    conditionedNestedLiftedGradientLower,
    conditionedNestedLiftedGradientUpper,
    conditionedNestedLiftedGradient,
    conditionedNestedLiftedGradientLowerFromReciprocals,
    conditionedNestedLiftedGradientUpperFromReciprocals
  ] using
    conditioned_nested_lifted_gradient_between_candidate_extrema_of_reciprocal_bounds
      coordinate
      (one_div_pos.mpr htotalAB).le
      (one_div_le_one_div_of_le htotalA (by linarith))
      (one_div_le_one_div_of_le hxAB (by linarith))
      (one_div_le_one_div_of_le hxA (by linarith))

/-- One of the full-event small and conditioned exclusive coordinates attains the candidate
minimum. This finite selection identity needs no mass assumptions. -/
theorem conditioned_nested_lifted_gradient_lower_attained
    (xA xB yA yB : ℝ) :
    ∃ coordinate : ConditionedNestedCoordinate,
      conditionedNestedLiftedGradient coordinate xA xB yA yB =
        conditionedNestedLiftedGradientLower xA xB yA yB := by
  by_cases hSmall :
      conditionedNestedLiftedGradient .totalSmall xA xB yA yB ≤
        conditionedNestedLiftedGradient .conditionedExclusive xA xB yA yB
  · exact ⟨.totalSmall, by
      rw [conditionedNestedLiftedGradientLower, min_eq_left hSmall]⟩
  · have hExclusive :
        conditionedNestedLiftedGradient .conditionedExclusive xA xB yA yB ≤
          conditionedNestedLiftedGradient .totalSmall xA xB yA yB :=
      le_of_not_ge hSmall
    exact ⟨.conditionedExclusive, by
      rw [conditionedNestedLiftedGradientLower, min_eq_right hExclusive]⟩

/-- One of the full-event exclusive and conditioned small coordinates attains the candidate
maximum. This finite selection identity needs no mass assumptions. -/
theorem conditioned_nested_lifted_gradient_upper_attained
    (xA xB yA yB : ℝ) :
    ∃ coordinate : ConditionedNestedCoordinate,
      conditionedNestedLiftedGradient coordinate xA xB yA yB =
        conditionedNestedLiftedGradientUpper xA xB yA yB := by
  by_cases hSmall :
      conditionedNestedLiftedGradient .conditionedSmall xA xB yA yB ≤
        conditionedNestedLiftedGradient .totalExclusive xA xB yA yB
  · exact ⟨.totalExclusive, by
      rw [conditionedNestedLiftedGradientUpper, max_eq_left hSmall]⟩
  · have hExclusive :
        conditionedNestedLiftedGradient .totalExclusive xA xB yA yB ≤
          conditionedNestedLiftedGradient .conditionedSmall xA xB yA yB :=
      le_of_not_ge hSmall
    exact ⟨.conditionedSmall, by
      rw [conditionedNestedLiftedGradientUpper, max_eq_right hExclusive]⟩

/-- The difference between the candidate maximum and minimum bounds every ordered pair of the five
conditioned-nested lifted coordinates. -/
theorem conditioned_nested_lifted_gradient_exact_coordinate_diameter_le
    (coordinateX coordinateY : ConditionedNestedCoordinate)
    {xA xB yA yB : ℝ}
    (hxA : 0 < xA) (hxB : 0 ≤ xB) (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) :
    |conditionedNestedLiftedGradient coordinateX xA xB yA yB -
        conditionedNestedLiftedGradient coordinateY xA xB yA yB| ≤
      conditionedNestedLiftedGradientUpper xA xB yA yB -
        conditionedNestedLiftedGradientLower xA xB yA yB := by
  have hX :=
    conditioned_nested_lifted_gradient_between_candidate_extrema
      coordinateX hxA hxB hyA hyB
  have hY :=
    conditioned_nested_lifted_gradient_between_candidate_extrema
      coordinateY hxA hxB hyA hyB
  rw [abs_le]
  constructor <;> linarith

/-- An ordered pair of the five conditioned-nested coordinates attains the candidate-maximum minus
candidate-minimum diameter. -/
theorem conditioned_nested_lifted_gradient_exact_coordinate_diameter_attained
    {xA xB yA yB : ℝ}
    (hxA : 0 < xA) (hxB : 0 ≤ xB) (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) :
    ∃ lowerCoordinate upperCoordinate : ConditionedNestedCoordinate,
      |conditionedNestedLiftedGradient upperCoordinate xA xB yA yB -
          conditionedNestedLiftedGradient lowerCoordinate xA xB yA yB| =
        conditionedNestedLiftedGradientUpper xA xB yA yB -
          conditionedNestedLiftedGradientLower xA xB yA yB := by
  obtain ⟨lowerCoordinate, hLower⟩ :=
    conditioned_nested_lifted_gradient_lower_attained xA xB yA yB
  obtain ⟨upperCoordinate, hUpper⟩ :=
    conditioned_nested_lifted_gradient_upper_attained xA xB yA yB
  have hOutside :=
    conditioned_nested_lifted_gradient_between_candidate_extrema
      .outside hxA hxB hyA hyB
  have hLowerUpper :
      conditionedNestedLiftedGradientLower xA xB yA yB ≤
        conditionedNestedLiftedGradientUpper xA xB yA yB := by
    have hOutsideZero :
        conditionedNestedLiftedGradient .outside xA xB yA yB = 0 := by
      simp only [
        conditionedNestedLiftedGradient,
        conditionedNestedLiftedGradientFromReciprocals
      ]
    rw [hOutsideZero] at hOutside
    linarith
  refine ⟨lowerCoordinate, upperCoordinate, ?_⟩
  rw [hLower, hUpper, abs_of_nonneg (sub_nonneg.mpr hLowerUpper)]

/-- The candidate diameter has the closed form given by the four possible
maximum-minus-minimum differences. -/
theorem conditioned_nested_lifted_gradient_candidate_diameter_eq
    (xA xB yA yB : ℝ) :
    conditionedNestedLiftedGradientUpper xA xB yA yB -
        conditionedNestedLiftedGradientLower xA xB yA yB =
      max
        (max (1 / (xA + yA)) (1 / (xA + xB)))
        (max
          (1 / xA - 1 / (xA + xB))
          (1 / xA - 1 / (xA + yA))) := by
  simpa only [
    conditionedNestedLiftedGradientUpper,
    conditionedNestedLiftedGradientLower,
    conditionedNestedLiftedGradient,
    conditionedNestedLiftedGradientUpperFromReciprocals,
    conditionedNestedLiftedGradientLowerFromReciprocals
  ] using
    conditioned_nested_lifted_gradient_candidate_diameter_eq_of_reciprocals
      (1 / xA)
      (1 / (xA + xB))
      (1 / (xA + yA))
      (1 / (xA + xB + yA + yB))

/-- Every pair of conditioned-nested coordinates is bounded by the exact closed-form diameter. -/
theorem conditioned_nested_lifted_gradient_closed_form_coordinate_diameter_le
    (coordinateX coordinateY : ConditionedNestedCoordinate)
    {xA xB yA yB : ℝ}
    (hxA : 0 < xA) (hxB : 0 ≤ xB) (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) :
    |conditionedNestedLiftedGradient coordinateX xA xB yA yB -
        conditionedNestedLiftedGradient coordinateY xA xB yA yB| ≤
      max
        (max (1 / (xA + yA)) (1 / (xA + xB)))
        (max
          (1 / xA - 1 / (xA + xB))
          (1 / xA - 1 / (xA + yA))) := by
  rw [← conditioned_nested_lifted_gradient_candidate_diameter_eq]
  exact conditioned_nested_lifted_gradient_exact_coordinate_diameter_le
    coordinateX coordinateY hxA hxB hyA hyB

/-- An ordered pair of conditioned-nested coordinates attains the exact closed-form diameter. -/
theorem conditioned_nested_lifted_gradient_closed_form_coordinate_diameter_attained
    {xA xB yA yB : ℝ}
    (hxA : 0 < xA) (hxB : 0 ≤ xB) (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) :
    ∃ lowerCoordinate upperCoordinate : ConditionedNestedCoordinate,
      |conditionedNestedLiftedGradient upperCoordinate xA xB yA yB -
          conditionedNestedLiftedGradient lowerCoordinate xA xB yA yB| =
        max
          (max (1 / (xA + yA)) (1 / (xA + xB)))
          (max
            (1 / xA - 1 / (xA + xB))
            (1 / xA - 1 / (xA + yA))) := by
  obtain ⟨lowerCoordinate, upperCoordinate, hDiameter⟩ :=
    conditioned_nested_lifted_gradient_exact_coordinate_diameter_attained
      hxA hxB hyA hyB
  refine ⟨lowerCoordinate, upperCoordinate, ?_⟩
  rw [hDiameter, conditioned_nested_lifted_gradient_candidate_diameter_eq]

/-- Every pair of conditioned-nested lifted gradient coordinates differs by at most `1 / xA`. -/
theorem conditioned_nested_lifted_gradient_coordinate_diameter_le
    (coordinateX coordinateY : ConditionedNestedCoordinate)
    {xA xB yA yB : ℝ}
    (hxA : 0 < xA) (hxB : 0 ≤ xB) (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) :
    |conditionedNestedLiftedGradient coordinateX xA xB yA yB -
        conditionedNestedLiftedGradient coordinateY xA xB yA yB| ≤
      1 / xA := by
  have hxAB : 0 < xA + xB := by linarith
  have htotalA : 0 < xA + yA := by linarith
  have htotalAB : 0 < xA + xB + yA + yB := by linarith
  apply conditioned_nested_lifted_gradient_diameter_of_reciprocal_bounds
  · exact (one_div_pos.mpr htotalAB).le
  · exact one_div_le_one_div_of_le htotalA (by linarith)
  · exact one_div_le_one_div_of_le hxA (by linarith)
  · exact one_div_le_one_div_of_le hxAB (by linarith)
  · exact one_div_le_one_div_of_le hxA (by linarith)

/-- With every represented side mass zero, the full-event exclusive coordinate and the outside
coordinate differ by exactly `1 / xA`. The represented masses satisfy all nonnegativity premises. -/
theorem conditioned_nested_lifted_gradient_zero_side_mass_witness
    {xA : ℝ} (hxA : 0 < xA) :
    |conditionedNestedLiftedGradient .totalExclusive xA 0 0 0 -
        conditionedNestedLiftedGradient .outside xA 0 0 0| =
      1 / xA := by
  have hreciprocalNonnegative : 0 ≤ 1 / xA := (one_div_pos.mpr hxA).le
  simp only [
    conditionedNestedLiftedGradient,
    conditionedNestedLiftedGradientFromReciprocals,
    add_zero,
    sub_zero,
    abs_of_nonneg hreciprocalNonnegative
  ]

/-- The five-coordinate diameter at the zero-side-mass witness is exactly `1 / xA`: every pair is
bounded by that value, and the displayed pair attains it. -/
theorem conditioned_nested_lifted_gradient_zero_side_mass_exact_diameter
    {xA : ℝ} (hxA : 0 < xA) :
    (∀ coordinateX coordinateY : ConditionedNestedCoordinate,
      |conditionedNestedLiftedGradient coordinateX xA 0 0 0 -
          conditionedNestedLiftedGradient coordinateY xA 0 0 0| ≤
        1 / xA) ∧
      ∃ coordinateX coordinateY : ConditionedNestedCoordinate,
        |conditionedNestedLiftedGradient coordinateX xA 0 0 0 -
            conditionedNestedLiftedGradient coordinateY xA 0 0 0| =
          1 / xA := by
  constructor
  · intro coordinateX coordinateY
    exact conditioned_nested_lifted_gradient_coordinate_diameter_le
      coordinateX coordinateY hxA (le_refl 0) (le_refl 0) (le_refl 0)
  · exact ⟨.totalExclusive, .outside,
      conditioned_nested_lifted_gradient_zero_side_mass_witness hxA⟩

/-- No positive amount can be subtracted uniformly from `1 / xA` over all nonnegative
conditioned-nested side masses. The zero-side-mass witness already attains `1 / xA`. -/
theorem conditioned_nested_lifted_gradient_no_positive_uniform_subtraction
    {xA subtraction : ℝ} (hxA : 0 < xA) (hsubtraction : 0 < subtraction) :
    ¬ (∀ (xB yA yB : ℝ),
      0 ≤ xB → 0 ≤ yA → 0 ≤ yB →
      ∀ coordinateX coordinateY : ConditionedNestedCoordinate,
        |conditionedNestedLiftedGradient coordinateX xA xB yA yB -
            conditionedNestedLiftedGradient coordinateY xA xB yA yB| ≤
          1 / xA - subtraction) := by
  intro hbound
  have hwitness :=
    hbound 0 0 0 (le_refl 0) (le_refl 0) (le_refl 0)
      .totalExclusive .outside
  rw [conditioned_nested_lifted_gradient_zero_side_mass_witness hxA] at hwitness
  linarith

/-- The eight coordinate classes in the lifted gradient of a conditioned ordinary-diamond
difference. `total` coordinates are derivatives with respect to the complement-region masses.
`conditioned` coordinates are derivatives with respect to the target-region masses. The labels
describe algebraic positions only. -/
inductive ConditionedDiamondCoordinate where
  | totalCommon
  | totalLeftExclusive
  | totalRightExclusive
  | totalOutside
  | conditionedCommon
  | conditionedLeftExclusive
  | conditionedRightExclusive
  | conditionedOutside

/-- The conditioned-diamond lifted gradient written in terms of the four reciprocal masses for
the target-region diamond and the four reciprocal masses for the full-event diamond. -/
noncomputable def conditionedDiamondLiftedGradientFromReciprocals
    (coordinate : ConditionedDiamondCoordinate)
    (reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC : ℝ)
    (reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC : ℝ) : ℝ :=
  match coordinate with
  | .totalCommon =>
      ordinaryDiamondGradientFromReciprocals .common
        reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC
  | .totalLeftExclusive =>
      ordinaryDiamondGradientFromReciprocals .leftExclusive
        reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC
  | .totalRightExclusive =>
      ordinaryDiamondGradientFromReciprocals .rightExclusive
        reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC
  | .totalOutside =>
      ordinaryDiamondGradientFromReciprocals .outside
        reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC
  | .conditionedCommon =>
      ordinaryDiamondGradientFromReciprocals .common
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC -
        ordinaryDiamondGradientFromReciprocals .common
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
  | .conditionedLeftExclusive =>
      ordinaryDiamondGradientFromReciprocals .leftExclusive
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC -
        ordinaryDiamondGradientFromReciprocals .leftExclusive
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
  | .conditionedRightExclusive =>
      ordinaryDiamondGradientFromReciprocals .rightExclusive
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC -
        ordinaryDiamondGradientFromReciprocals .rightExclusive
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
  | .conditionedOutside =>
      ordinaryDiamondGradientFromReciprocals .outside
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC -
      ordinaryDiamondGradientFromReciprocals .outside
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC

/-- The lower candidate among the full-event common coordinate and the two conditioned exclusive
coordinates. -/
noncomputable def conditionedDiamondLiftedGradientLowerFromReciprocals
    (reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC : ℝ)
    (reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC : ℝ) : ℝ :=
  min
    (conditionedDiamondLiftedGradientFromReciprocals .totalCommon
      reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
      reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC)
    (min
      (conditionedDiamondLiftedGradientFromReciprocals .conditionedLeftExclusive
        reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
        reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC)
      (conditionedDiamondLiftedGradientFromReciprocals .conditionedRightExclusive
        reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
        reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC))

/-- The upper candidate among the two full-event exclusive coordinates and the conditioned common
coordinate. -/
noncomputable def conditionedDiamondLiftedGradientUpperFromReciprocals
    (reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC : ℝ)
    (reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC : ℝ) : ℝ :=
  max
    (conditionedDiamondLiftedGradientFromReciprocals .totalLeftExclusive
      reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
      reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC)
    (max
      (conditionedDiamondLiftedGradientFromReciprocals .totalRightExclusive
        reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
        reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC)
      (conditionedDiamondLiftedGradientFromReciprocals .conditionedCommon
        reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
        reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC))

/-- Selected reciprocal-order inequalities and the two ordinary-diamond supermodularity
inequalities place every lifted coordinate between the three stated lower and upper candidates. -/
theorem conditioned_diamond_lifted_gradient_between_candidate_extrema_of_reciprocal_bounds
    (coordinate : ConditionedDiamondCoordinate)
    {reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC : ℝ}
    {reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC : ℝ}
    (hTotalABCAB : reciprocalTotalABC ≤ reciprocalTotalAB)
    (hTotalABA : reciprocalTotalAB ≤ reciprocalTotalA)
    (hTotalACA : reciprocalTotalAC ≤ reciprocalTotalA)
    (hXABCAB : reciprocalXABC ≤ reciprocalXAB)
    (hXABCAC : reciprocalXABC ≤ reciprocalXAC)
    (hXSupermodular :
      reciprocalXAB + reciprocalXAC ≤ reciprocalXA + reciprocalXABC)
    (hTotalSupermodular :
      reciprocalTotalAB + reciprocalTotalAC ≤
        reciprocalTotalA + reciprocalTotalABC) :
    conditionedDiamondLiftedGradientLowerFromReciprocals
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC ≤
        conditionedDiamondLiftedGradientFromReciprocals coordinate
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC ∧
      conditionedDiamondLiftedGradientFromReciprocals coordinate
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC ≤
        conditionedDiamondLiftedGradientUpperFromReciprocals
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC := by
  have hLowerTotalCommon :
      conditionedDiamondLiftedGradientLowerFromReciprocals
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC ≤
        conditionedDiamondLiftedGradientFromReciprocals .totalCommon
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC :=
    min_le_left _ _
  have hLowerConditionedLeft :
      conditionedDiamondLiftedGradientLowerFromReciprocals
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC ≤
        conditionedDiamondLiftedGradientFromReciprocals .conditionedLeftExclusive
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC :=
    (min_le_right _ _).trans (min_le_left _ _)
  have hLowerConditionedRight :
      conditionedDiamondLiftedGradientLowerFromReciprocals
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC ≤
        conditionedDiamondLiftedGradientFromReciprocals .conditionedRightExclusive
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC :=
    (min_le_right _ _).trans (min_le_right _ _)
  have hUpperTotalLeft :
      conditionedDiamondLiftedGradientFromReciprocals .totalLeftExclusive
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC ≤
        conditionedDiamondLiftedGradientUpperFromReciprocals
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC :=
    le_max_left _ _
  have hUpperTotalRight :
      conditionedDiamondLiftedGradientFromReciprocals .totalRightExclusive
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC ≤
        conditionedDiamondLiftedGradientUpperFromReciprocals
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC :=
    (le_max_left _ _).trans (le_max_right _ _)
  have hUpperConditionedCommon :
      conditionedDiamondLiftedGradientFromReciprocals .conditionedCommon
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC ≤
        conditionedDiamondLiftedGradientUpperFromReciprocals
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC :=
    (le_max_right _ _).trans (le_max_right _ _)
  constructor <;>
    cases coordinate <;>
    simp only [
      conditionedDiamondLiftedGradientLowerFromReciprocals,
      conditionedDiamondLiftedGradientUpperFromReciprocals,
      conditionedDiamondLiftedGradientFromReciprocals,
      ordinaryDiamondGradientFromReciprocals
    ] at * <;>
    linarith

/-- Reciprocal order, reciprocal supermodularity, and cross-diamond nesting bound every pair of
conditioned-diamond lifted coordinates by `reciprocalXA - reciprocalTotalABC`.

The proof audits all 64 ordered coordinate pairs. The case split compares the two full-event
exclusive reciprocals. It closes the crossed left--right pairs that do not follow from an
individual-coordinate magnitude bound. -/
theorem conditioned_diamond_lifted_gradient_refined_diameter_of_reciprocal_bounds
    (coordinateX coordinateY : ConditionedDiamondCoordinate)
    {reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC : ℝ}
    {reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC : ℝ}
    (hTotalABCAB : reciprocalTotalABC ≤ reciprocalTotalAB)
    (hTotalABCAC : reciprocalTotalABC ≤ reciprocalTotalAC)
    (hTotalABA : reciprocalTotalAB ≤ reciprocalTotalA)
    (hTotalACA : reciprocalTotalAC ≤ reciprocalTotalA)
    (hTotalAXA : reciprocalTotalA ≤ reciprocalXA)
    (hTotalABXAB : reciprocalTotalAB ≤ reciprocalXAB)
    (hTotalACXAC : reciprocalTotalAC ≤ reciprocalXAC)
    (hXABCAB : reciprocalXABC ≤ reciprocalXAB)
    (hXABCAC : reciprocalXABC ≤ reciprocalXAC)
    (hXABXA : reciprocalXAB ≤ reciprocalXA)
    (hXACXA : reciprocalXAC ≤ reciprocalXA)
    (hXSupermodular :
      reciprocalXAB + reciprocalXAC ≤ reciprocalXA + reciprocalXABC) :
    |conditionedDiamondLiftedGradientFromReciprocals coordinateX
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC -
        conditionedDiamondLiftedGradientFromReciprocals coordinateY
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC| ≤
      reciprocalXA - reciprocalTotalABC := by
  rw [abs_le]
  constructor <;>
    cases coordinateX <;> cases coordinateY <;>
    simp only [
      conditionedDiamondLiftedGradientFromReciprocals,
      ordinaryDiamondGradientFromReciprocals
    ] <;>
    by_cases hExclusive :
      reciprocalTotalAB ≤ reciprocalTotalAC <;> linarith

/-- The coarser reciprocal-mass conditioned-diamond bound follows from the refined diameter when
`reciprocalTotalABC` is nonnegative. -/
theorem conditioned_diamond_lifted_gradient_diameter_of_reciprocal_bounds
    (coordinateX coordinateY : ConditionedDiamondCoordinate)
    {reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC : ℝ}
    {reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC : ℝ}
    (hTotalABCNonnegative : 0 ≤ reciprocalTotalABC)
    (hTotalABCAB : reciprocalTotalABC ≤ reciprocalTotalAB)
    (hTotalABCAC : reciprocalTotalABC ≤ reciprocalTotalAC)
    (hTotalABA : reciprocalTotalAB ≤ reciprocalTotalA)
    (hTotalACA : reciprocalTotalAC ≤ reciprocalTotalA)
    (hTotalAXA : reciprocalTotalA ≤ reciprocalXA)
    (hTotalABXAB : reciprocalTotalAB ≤ reciprocalXAB)
    (hTotalACXAC : reciprocalTotalAC ≤ reciprocalXAC)
    (hXABCAB : reciprocalXABC ≤ reciprocalXAB)
    (hXABCAC : reciprocalXABC ≤ reciprocalXAC)
    (hXABXA : reciprocalXAB ≤ reciprocalXA)
    (hXACXA : reciprocalXAC ≤ reciprocalXA)
    (hXSupermodular :
      reciprocalXAB + reciprocalXAC ≤ reciprocalXA + reciprocalXABC) :
    |conditionedDiamondLiftedGradientFromReciprocals coordinateX
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC -
        conditionedDiamondLiftedGradientFromReciprocals coordinateY
          reciprocalXA reciprocalXAB reciprocalXAC reciprocalXABC
          reciprocalTotalA reciprocalTotalAB reciprocalTotalAC reciprocalTotalABC| ≤
      reciprocalXA := by
  refine
    (conditioned_diamond_lifted_gradient_refined_diameter_of_reciprocal_bounds
      coordinateX coordinateY hTotalABCAB hTotalABCAC hTotalABA hTotalACA
      hTotalAXA hTotalABXAB hTotalACXAC hXABCAB hXABCAC hXABXA hXACXA
      hXSupermodular).trans ?_
  linarith

/-- The conditioned-diamond lifted gradient evaluated from nonnegative target-region and
complement-region masses. Outside-region masses do not occur in the diamond logarithm and are
therefore omitted. -/
noncomputable def conditionedDiamondLiftedGradient
    (coordinate : ConditionedDiamondCoordinate)
    (xA xB xC yA yB yC : ℝ) : ℝ :=
  conditionedDiamondLiftedGradientFromReciprocals coordinate
    (1 / xA)
    (1 / (xA + xB))
    (1 / (xA + xC))
    (1 / (xA + xB + xC))
    (1 / (xA + yA))
    (1 / (xA + xB + yA + yB))
    (1 / (xA + xC + yA + yC))
    (1 / (xA + xB + xC + yA + yB + yC))

/-- The minimum candidate among `F_a`, `X_b`, and `X_c`. -/
noncomputable def conditionedDiamondLiftedGradientLower
    (xA xB xC yA yB yC : ℝ) : ℝ :=
  min
    (conditionedDiamondLiftedGradient .totalCommon xA xB xC yA yB yC)
    (min
      (conditionedDiamondLiftedGradient
        .conditionedLeftExclusive xA xB xC yA yB yC)
      (conditionedDiamondLiftedGradient
        .conditionedRightExclusive xA xB xC yA yB yC))

/-- The maximum candidate among `F_b`, `F_c`, and `X_a`. -/
noncomputable def conditionedDiamondLiftedGradientUpper
    (xA xB xC yA yB yC : ℝ) : ℝ :=
  max
    (conditionedDiamondLiftedGradient .totalLeftExclusive xA xB xC yA yB yC)
    (max
      (conditionedDiamondLiftedGradient .totalRightExclusive xA xB xC yA yB yC)
      (conditionedDiamondLiftedGradient .conditionedCommon xA xB xC yA yB yC))

/-- Under the natural mass assumptions, every conditioned-diamond lifted coordinate lies between
the candidate minimum and maximum. -/
theorem conditioned_diamond_lifted_gradient_between_candidate_extrema
    (coordinate : ConditionedDiamondCoordinate)
    {xA xB xC yA yB yC : ℝ}
    (hxA : 0 < xA)
    (hxB : 0 ≤ xB) (hxC : 0 ≤ xC)
    (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) (hyC : 0 ≤ yC) :
    conditionedDiamondLiftedGradientLower xA xB xC yA yB yC ≤
        conditionedDiamondLiftedGradient coordinate xA xB xC yA yB yC ∧
      conditionedDiamondLiftedGradient coordinate xA xB xC yA yB yC ≤
        conditionedDiamondLiftedGradientUpper xA xB xC yA yB yC := by
  have hxAB : 0 < xA + xB := by linarith
  have hxAC : 0 < xA + xC := by linarith
  have htotalA : 0 < xA + yA := by linarith
  have htotalAB : 0 < xA + xB + yA + yB := by linarith
  have hTotalSupermodular :
      1 / (xA + xB + yA + yB) + 1 / (xA + xC + yA + yC) ≤
        1 / (xA + yA) + 1 / (xA + xB + xC + yA + yB + yC) := by
    convert
      ordinary_diamond_reciprocal_supermodular
        (a := xA + yA) (b := xB + yB) (c := xC + yC)
        htotalA (by linarith) (by linarith) using 1 <;>
      ring
  simpa only [
    conditionedDiamondLiftedGradientLower,
    conditionedDiamondLiftedGradientUpper,
    conditionedDiamondLiftedGradient,
    conditionedDiamondLiftedGradientLowerFromReciprocals,
    conditionedDiamondLiftedGradientUpperFromReciprocals
  ] using
    conditioned_diamond_lifted_gradient_between_candidate_extrema_of_reciprocal_bounds
      coordinate
      (one_div_le_one_div_of_le htotalAB (by linarith))
      (one_div_le_one_div_of_le htotalA (by linarith))
      (one_div_le_one_div_of_le htotalA (by linarith))
      (one_div_le_one_div_of_le hxAB (by linarith))
      (one_div_le_one_div_of_le hxAC (by linarith))
      (ordinary_diamond_reciprocal_supermodular hxA hxB hxC)
      hTotalSupermodular

/-- One of `F_a`, `X_b`, and `X_c` attains the candidate minimum. This algebraic selection needs
no mass assumptions. -/
theorem conditioned_diamond_lifted_gradient_lower_attained
    (xA xB xC yA yB yC : ℝ) :
    ∃ coordinate : ConditionedDiamondCoordinate,
      conditionedDiamondLiftedGradient coordinate xA xB xC yA yB yC =
        conditionedDiamondLiftedGradientLower xA xB xC yA yB yC := by
  by_cases hCommon :
      conditionedDiamondLiftedGradient .totalCommon xA xB xC yA yB yC ≤
        min
          (conditionedDiamondLiftedGradient
            .conditionedLeftExclusive xA xB xC yA yB yC)
          (conditionedDiamondLiftedGradient
            .conditionedRightExclusive xA xB xC yA yB yC)
  · refine ⟨.totalCommon, ?_⟩
    rw [conditionedDiamondLiftedGradientLower, min_eq_left hCommon]
  · have hInnerCommon :
        min
            (conditionedDiamondLiftedGradient
              .conditionedLeftExclusive xA xB xC yA yB yC)
            (conditionedDiamondLiftedGradient
              .conditionedRightExclusive xA xB xC yA yB yC) ≤
          conditionedDiamondLiftedGradient .totalCommon xA xB xC yA yB yC :=
      le_of_not_ge hCommon
    by_cases hLeftRight :
        conditionedDiamondLiftedGradient
            .conditionedLeftExclusive xA xB xC yA yB yC ≤
          conditionedDiamondLiftedGradient
            .conditionedRightExclusive xA xB xC yA yB yC
    · refine ⟨.conditionedLeftExclusive, ?_⟩
      rw [
        conditionedDiamondLiftedGradientLower,
        min_eq_right hInnerCommon,
        min_eq_left hLeftRight
      ]
    · have hRightLeft :
          conditionedDiamondLiftedGradient
              .conditionedRightExclusive xA xB xC yA yB yC ≤
            conditionedDiamondLiftedGradient
              .conditionedLeftExclusive xA xB xC yA yB yC :=
        le_of_not_ge hLeftRight
      refine ⟨.conditionedRightExclusive, ?_⟩
      rw [
        conditionedDiamondLiftedGradientLower,
        min_eq_right hInnerCommon,
        min_eq_right hRightLeft
      ]

/-- One of `F_b`, `F_c`, and `X_a` attains the candidate maximum. This algebraic selection needs
no mass assumptions. -/
theorem conditioned_diamond_lifted_gradient_upper_attained
    (xA xB xC yA yB yC : ℝ) :
    ∃ coordinate : ConditionedDiamondCoordinate,
      conditionedDiamondLiftedGradient coordinate xA xB xC yA yB yC =
        conditionedDiamondLiftedGradientUpper xA xB xC yA yB yC := by
  by_cases hInnerLeft :
      max
          (conditionedDiamondLiftedGradient
            .totalRightExclusive xA xB xC yA yB yC)
          (conditionedDiamondLiftedGradient
            .conditionedCommon xA xB xC yA yB yC) ≤
        conditionedDiamondLiftedGradient
          .totalLeftExclusive xA xB xC yA yB yC
  · refine ⟨.totalLeftExclusive, ?_⟩
    rw [conditionedDiamondLiftedGradientUpper, max_eq_left hInnerLeft]
  · have hLeftInner :
        conditionedDiamondLiftedGradient
            .totalLeftExclusive xA xB xC yA yB yC ≤
          max
            (conditionedDiamondLiftedGradient
              .totalRightExclusive xA xB xC yA yB yC)
            (conditionedDiamondLiftedGradient
              .conditionedCommon xA xB xC yA yB yC) :=
      le_of_not_ge hInnerLeft
    by_cases hCommonRight :
        conditionedDiamondLiftedGradient .conditionedCommon xA xB xC yA yB yC ≤
          conditionedDiamondLiftedGradient
            .totalRightExclusive xA xB xC yA yB yC
    · refine ⟨.totalRightExclusive, ?_⟩
      rw [
        conditionedDiamondLiftedGradientUpper,
        max_eq_right hLeftInner,
        max_eq_left hCommonRight
      ]
    · have hRightCommon :
          conditionedDiamondLiftedGradient
              .totalRightExclusive xA xB xC yA yB yC ≤
            conditionedDiamondLiftedGradient
              .conditionedCommon xA xB xC yA yB yC :=
        le_of_not_ge hCommonRight
      refine ⟨.conditionedCommon, ?_⟩
      rw [
        conditionedDiamondLiftedGradientUpper,
        max_eq_right hLeftInner,
        max_eq_right hRightCommon
      ]

/-- The difference between the candidate maximum and minimum bounds every ordered pair of lifted
coordinates. -/
theorem conditioned_diamond_lifted_gradient_exact_coordinate_diameter_le
    (coordinateX coordinateY : ConditionedDiamondCoordinate)
    {xA xB xC yA yB yC : ℝ}
    (hxA : 0 < xA)
    (hxB : 0 ≤ xB) (hxC : 0 ≤ xC)
    (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) (hyC : 0 ≤ yC) :
    |conditionedDiamondLiftedGradient coordinateX xA xB xC yA yB yC -
        conditionedDiamondLiftedGradient coordinateY xA xB xC yA yB yC| ≤
      conditionedDiamondLiftedGradientUpper xA xB xC yA yB yC -
        conditionedDiamondLiftedGradientLower xA xB xC yA yB yC := by
  have hX :=
    conditioned_diamond_lifted_gradient_between_candidate_extrema
      coordinateX hxA hxB hxC hyA hyB hyC
  have hY :=
    conditioned_diamond_lifted_gradient_between_candidate_extrema
      coordinateY hxA hxB hxC hyA hyB hyC
  rw [abs_le]
  constructor <;> linarith

/-- An ordered pair of lifted coordinates attains the candidate-maximum minus candidate-minimum
diameter. -/
theorem conditioned_diamond_lifted_gradient_exact_coordinate_diameter_attained
    {xA xB xC yA yB yC : ℝ}
    (hxA : 0 < xA)
    (hxB : 0 ≤ xB) (hxC : 0 ≤ xC)
    (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) (hyC : 0 ≤ yC) :
    ∃ lowerCoordinate upperCoordinate : ConditionedDiamondCoordinate,
      |conditionedDiamondLiftedGradient upperCoordinate xA xB xC yA yB yC -
          conditionedDiamondLiftedGradient lowerCoordinate xA xB xC yA yB yC| =
        conditionedDiamondLiftedGradientUpper xA xB xC yA yB yC -
          conditionedDiamondLiftedGradientLower xA xB xC yA yB yC := by
  obtain ⟨lowerCoordinate, hLower⟩ :=
    conditioned_diamond_lifted_gradient_lower_attained xA xB xC yA yB yC
  obtain ⟨upperCoordinate, hUpper⟩ :=
    conditioned_diamond_lifted_gradient_upper_attained xA xB xC yA yB yC
  have hOutside :=
    conditioned_diamond_lifted_gradient_between_candidate_extrema
      .totalOutside hxA hxB hxC hyA hyB hyC
  have hLowerUpper :
      conditionedDiamondLiftedGradientLower xA xB xC yA yB yC ≤
        conditionedDiamondLiftedGradientUpper xA xB xC yA yB yC := by
    have hOutsideZero :
        conditionedDiamondLiftedGradient .totalOutside xA xB xC yA yB yC = 0 := by
      simp only [
        conditionedDiamondLiftedGradient,
        conditionedDiamondLiftedGradientFromReciprocals,
        ordinaryDiamondGradientFromReciprocals
      ]
    rw [hOutsideZero] at hOutside
    linarith
  refine ⟨lowerCoordinate, upperCoordinate, ?_⟩
  rw [hLower, hUpper, abs_of_nonneg (sub_nonneg.mpr hLowerUpper)]

/-- Every pair of conditioned-diamond lifted gradient coordinates differs by at most the common
target-region reciprocal minus the full-event-union reciprocal. The only strict premise is
positivity of the common target-region mass. Every other represented region mass can be zero. -/
theorem conditioned_diamond_lifted_gradient_refined_coordinate_diameter_le
    (coordinateX coordinateY : ConditionedDiamondCoordinate)
    {xA xB xC yA yB yC : ℝ}
    (hxA : 0 < xA)
    (hxB : 0 ≤ xB) (hxC : 0 ≤ xC)
    (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) (hyC : 0 ≤ yC) :
    |conditionedDiamondLiftedGradient coordinateX xA xB xC yA yB yC -
        conditionedDiamondLiftedGradient coordinateY xA xB xC yA yB yC| ≤
      1 / xA - 1 / (xA + xB + xC + yA + yB + yC) := by
  have hxAB : 0 < xA + xB := by linarith
  have hxAC : 0 < xA + xC := by linarith
  have htotalA : 0 < xA + yA := by linarith
  have htotalAB : 0 < xA + xB + yA + yB := by linarith
  have htotalAC : 0 < xA + xC + yA + yC := by linarith
  apply conditioned_diamond_lifted_gradient_refined_diameter_of_reciprocal_bounds
  · exact one_div_le_one_div_of_le htotalAB (by linarith)
  · exact one_div_le_one_div_of_le htotalAC (by linarith)
  · exact one_div_le_one_div_of_le htotalA (by linarith)
  · exact one_div_le_one_div_of_le htotalA (by linarith)
  · exact one_div_le_one_div_of_le hxA (by linarith)
  · exact one_div_le_one_div_of_le hxAB (by linarith)
  · exact one_div_le_one_div_of_le hxAC (by linarith)
  · exact one_div_le_one_div_of_le hxAB (by linarith)
  · exact one_div_le_one_div_of_le hxAC (by linarith)
  · exact one_div_le_one_div_of_le hxA (by linarith)
  · exact one_div_le_one_div_of_le hxA (by linarith)
  · exact ordinary_diamond_reciprocal_supermodular hxA hxB hxC

/-- In the family `x = (xA, 0, 0)` and `y = (0, 0, total - xA)`, the oriented crossed-coordinate
difference is exactly the refined union-reciprocal bound. The assumptions make the represented
lift mass nonnegative. -/
theorem conditioned_diamond_lifted_gradient_refined_bound_attained_ordered
    {xA total : ℝ} (hxA : 0 < xA) (hxATotal : xA ≤ total) :
    conditionedDiamondLiftedGradient
          .totalLeftExclusive xA 0 0 0 0 (total - xA) -
        conditionedDiamondLiftedGradient
          .conditionedRightExclusive xA 0 0 0 0 (total - xA) =
      1 / xA - 1 / total := by
  have htotal : 0 < total := hxA.trans_le hxATotal
  have htotal_eq : xA + (total - xA) = total := by ring
  simp only [
    conditionedDiamondLiftedGradient,
    conditionedDiamondLiftedGradientFromReciprocals,
    ordinaryDiamondGradientFromReciprocals,
    add_zero,
    htotal_eq
  ]
  field_simp [hxA.ne', htotal.ne']
  ring

/-- The refined conditioned-diamond union-reciprocal bound is attained by the valid family
`x = (xA, 0, 0)` and `y = (0, 0, total - xA)`. -/
theorem conditioned_diamond_lifted_gradient_refined_bound_attained
    {xA total : ℝ} (hxA : 0 < xA) (hxATotal : xA ≤ total) :
    |conditionedDiamondLiftedGradient
          .totalLeftExclusive xA 0 0 0 0 (total - xA) -
        conditionedDiamondLiftedGradient
          .conditionedRightExclusive xA 0 0 0 0 (total - xA)| =
      1 / xA - 1 / total := by
  have hnonnegative : 0 ≤ 1 / xA - 1 / total :=
    sub_nonneg.mpr (one_div_le_one_div_of_le hxA hxATotal)
  rw [
    conditioned_diamond_lifted_gradient_refined_bound_attained_ordered
      hxA hxATotal,
    abs_of_nonneg hnonnegative
  ]

/-- On the normalized mass domain, every conditioned-diamond coordinate pair differs by at most
`1 / xA - 1`. This corollary encodes only nonnegative masses and a displayed total at most one; it
does not construct or identify a probability law. -/
theorem conditioned_diamond_lifted_gradient_probability_domain_coordinate_diameter_le
    (coordinateX coordinateY : ConditionedDiamondCoordinate)
    {xA xB xC yA yB yC : ℝ}
    (hxA : 0 < xA)
    (hxB : 0 ≤ xB) (hxC : 0 ≤ xC)
    (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) (hyC : 0 ≤ yC)
    (htotal : xA + xB + xC + yA + yB + yC ≤ 1) :
    |conditionedDiamondLiftedGradient coordinateX xA xB xC yA yB yC -
        conditionedDiamondLiftedGradient coordinateY xA xB xC yA yB yC| ≤
      1 / xA - 1 := by
  have htotalPositive : 0 < xA + xB + xC + yA + yB + yC := by
    linarith
  have hOneLeReciprocal :
      1 ≤ 1 / (xA + xB + xC + yA + yB + yC) := by
    rw [le_div_iff₀ htotalPositive]
    simpa using htotal
  refine
    (conditioned_diamond_lifted_gradient_refined_coordinate_diameter_le
      coordinateX coordinateY hxA hxB hxC hyA hyB hyC).trans ?_
  linarith

/-- On the normalized mass domain, the magnitude of each conditioned-diamond coordinate is at
most `1 / xA - 1`. The zero outside coordinate supplies the second endpoint. -/
theorem conditioned_diamond_lifted_gradient_probability_domain_absolute_coordinate_le
    (coordinate : ConditionedDiamondCoordinate)
    {xA xB xC yA yB yC : ℝ}
    (hxA : 0 < xA)
    (hxB : 0 ≤ xB) (hxC : 0 ≤ xC)
    (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) (hyC : 0 ≤ yC)
    (htotal : xA + xB + xC + yA + yB + yC ≤ 1) :
    |conditionedDiamondLiftedGradient coordinate xA xB xC yA yB yC| ≤
      1 / xA - 1 := by
  have hbound :=
    conditioned_diamond_lifted_gradient_probability_domain_coordinate_diameter_le
      coordinate .totalOutside hxA hxB hxC hyA hyB hyC htotal
  have hOutsideZero :
      conditionedDiamondLiftedGradient .totalOutside xA xB xC yA yB yC = 0 := by
    rfl
  rw [hOutsideZero, sub_zero] at hbound
  exact hbound

/-- The coarser `1 / xA` conditioned-diamond bound follows from the refined mass bound. -/
theorem conditioned_diamond_lifted_gradient_coordinate_diameter_le
    (coordinateX coordinateY : ConditionedDiamondCoordinate)
    {xA xB xC yA yB yC : ℝ}
    (hxA : 0 < xA)
    (hxB : 0 ≤ xB) (hxC : 0 ≤ xC)
    (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) (hyC : 0 ≤ yC) :
    |conditionedDiamondLiftedGradient coordinateX xA xB xC yA yB yC -
        conditionedDiamondLiftedGradient coordinateY xA xB xC yA yB yC| ≤
      1 / xA := by
  have htotalABC : 0 < xA + xB + xC + yA + yB + yC := by linarith
  refine
    (conditioned_diamond_lifted_gradient_refined_coordinate_diameter_le
      coordinateX coordinateY hxA hxB hxC hyA hyB hyC).trans ?_
  exact sub_le_self _ (one_div_pos.mpr htotalABC).le

/-- A nonnegative coordinate is bounded by the stated upper bound on the top sum. The equality
premise records the external identification of that sum with the top cumulative component. -/
theorem component_coordinate_bounds_of_nonnegative_top_sum
    (indices : Finset ι) (component : ι → ℝ) {coordinate : ι}
    {topValue upperBound : ℝ}
    (hcoordinate : coordinate ∈ indices)
    (hnonnegative : ∀ i ∈ indices, 0 ≤ component i)
    (htopSum : ∑ i ∈ indices, component i = topValue)
    (htopBound : topValue ≤ upperBound) :
    0 ≤ component coordinate ∧ component coordinate ≤ upperBound := by
  constructor
  · exact hnonnegative coordinate hcoordinate
  · have hcoordinateLe :
        component coordinate ≤ ∑ i ∈ indices, component i :=
      Finset.single_le_sum
        (fun i hi => hnonnegative i hi) hcoordinate
    linarith

/-- A fixed external linear row transfers uniform coordinatewise changes through its absolute row
sum. The coefficients are arbitrary; no lattice is encoded. -/
theorem abs_mobius_row_change_le_abs_row_sum
    (indices : Finset κ) (coefficient valueP valueQ : κ → ℝ)
    {coordinateBound : ℝ}
    (hchange : ∀ i ∈ indices, |valueQ i - valueP i| ≤ coordinateBound) :
    |(∑ i ∈ indices, coefficient i * valueQ i) -
        ∑ i ∈ indices, coefficient i * valueP i| ≤
      (∑ i ∈ indices, |coefficient i|) * coordinateBound := by
  calc
    |(∑ i ∈ indices, coefficient i * valueQ i) -
        ∑ i ∈ indices, coefficient i * valueP i| =
        |∑ i ∈ indices, coefficient i * (valueQ i - valueP i)| := by
          apply congrArg abs
          rw [← Finset.sum_sub_distrib]
          apply Finset.sum_congr rfl
          intro i _
          ring
    _ ≤ (∑ i ∈ indices, |coefficient i|) * coordinateBound :=
      abs_linear_row_le_abs_row_sum
        indices coefficient (fun i => valueQ i - valueP i) hchange

/-- The difference of two component values in `[0, upperBound]` lies in the corresponding signed
net interval. -/
theorem net_value_bounds_of_component_bounds
    {informative misinformative upperBound : ℝ}
    (hinformative : 0 ≤ informative ∧ informative ≤ upperBound)
    (hmisinformative : 0 ≤ misinformative ∧ misinformative ≤ upperBound) :
    -upperBound ≤ informative - misinformative ∧
      informative - misinformative ≤ upperBound := by
  constructor <;> linarith

/-- A normalized nonnegative average of component values in `[0, upperBound]` remains in that
interval. -/
theorem component_weighted_average_bounds
    (indices : Finset ι) (weight component : ι → ℝ)
    {upperBound : ℝ}
    (hweightNonnegative : ∀ i ∈ indices, 0 ≤ weight i)
    (hweightSum : ∑ i ∈ indices, weight i = 1)
    (hcomponent : ∀ i ∈ indices, 0 ≤ component i ∧ component i ≤ upperBound) :
    0 ≤ ∑ i ∈ indices, weight i * component i ∧
      ∑ i ∈ indices, weight i * component i ≤ upperBound := by
  constructor
  · exact Finset.sum_nonneg fun i hi =>
      mul_nonneg (hweightNonnegative i hi) (hcomponent i hi).1
  · calc
      ∑ i ∈ indices, weight i * component i
          ≤ ∑ i ∈ indices, weight i * upperBound := by
            apply Finset.sum_le_sum
            intro i hi
            exact mul_le_mul_of_nonneg_left
              (hcomponent i hi).2 (hweightNonnegative i hi)
      _ = upperBound := by
        rw [← Finset.sum_mul, hweightSum, one_mul]

/-- A normalized nonnegative average of signed-net values formed from two `[0, upperBound]`
components lies in `[-upperBound, upperBound]`. -/
theorem net_weighted_average_bounds
    (indices : Finset ι)
    (weight informative misinformative : ι → ℝ)
    {upperBound : ℝ}
    (hweightNonnegative : ∀ i ∈ indices, 0 ≤ weight i)
    (hweightSum : ∑ i ∈ indices, weight i = 1)
    (hinformative :
      ∀ i ∈ indices, 0 ≤ informative i ∧ informative i ≤ upperBound)
    (hmisinformative :
      ∀ i ∈ indices, 0 ≤ misinformative i ∧ misinformative i ≤ upperBound) :
    -upperBound ≤
        ∑ i ∈ indices, weight i * (informative i - misinformative i) ∧
      ∑ i ∈ indices, weight i * (informative i - misinformative i) ≤
        upperBound := by
  have hnet :
      ∀ i ∈ indices,
        -upperBound ≤ informative i - misinformative i ∧
          informative i - misinformative i ≤ upperBound := by
    intro i hi
    exact net_value_bounds_of_component_bounds
      (hinformative i hi) (hmisinformative i hi)
  constructor
  · calc
      -upperBound =
          ∑ i ∈ indices, weight i * (-upperBound) := by
            rw [← Finset.sum_mul, hweightSum, one_mul]
      _ ≤ ∑ i ∈ indices,
          weight i * (informative i - misinformative i) := by
            apply Finset.sum_le_sum
            intro i hi
            exact mul_le_mul_of_nonneg_left
              (hnet i hi).1 (hweightNonnegative i hi)
  · calc
      ∑ i ∈ indices, weight i * (informative i - misinformative i)
          ≤ ∑ i ∈ indices, weight i * upperBound := by
            apply Finset.sum_le_sum
            intro i hi
            exact mul_le_mul_of_nonneg_left
              (hnet i hi).2 (hweightNonnegative i hi)
      _ = upperBound := by
        rw [← Finset.sum_mul, hweightSum, one_mul]

/-- For equal-total weights, a reference component in `[0, upperBound]` contributes at most
`L1-change * upperBound / 2`. -/
theorem abs_component_weight_change_le_half_range
    (indices : Finset ι) (pWeight qWeight componentP : ι → ℝ)
    {upperBound l1Bound : ℝ}
    (hpSum : ∑ i ∈ indices, pWeight i = 1)
    (hqSum : ∑ i ∈ indices, qWeight i = 1)
    (hupperNonnegative : 0 ≤ upperBound)
    (hl1Nonnegative : 0 ≤ l1Bound)
    (hcomponent :
      ∀ i ∈ indices, 0 ≤ componentP i ∧ componentP i ≤ upperBound)
    (hweightChange :
      ∑ i ∈ indices, |qWeight i - pWeight i| ≤ l1Bound) :
    |∑ i ∈ indices, (qWeight i - pWeight i) * componentP i| ≤
      l1Bound * upperBound / 2 := by
  simpa using
    abs_weight_change_against_bounded_values_le_half_range
      indices pWeight qWeight componentP hpSum hqSum hupperNonnegative
      hl1Nonnegative hcomponent hweightChange

/-- For equal-total weights, a reference net formed from two components in `[0, upperBound]`
contributes at most `L1-change * upperBound`. -/
theorem abs_net_weight_change_le_range
    (indices : Finset ι)
    (pWeight qWeight informativeP misinformativeP : ι → ℝ)
    {upperBound l1Bound : ℝ}
    (hpSum : ∑ i ∈ indices, pWeight i = 1)
    (hqSum : ∑ i ∈ indices, qWeight i = 1)
    (hupperNonnegative : 0 ≤ upperBound)
    (hl1Nonnegative : 0 ≤ l1Bound)
    (hinformative :
      ∀ i ∈ indices, 0 ≤ informativeP i ∧ informativeP i ≤ upperBound)
    (hmisinformative :
      ∀ i ∈ indices, 0 ≤ misinformativeP i ∧ misinformativeP i ≤ upperBound)
    (hweightChange :
      ∑ i ∈ indices, |qWeight i - pWeight i| ≤ l1Bound) :
    |∑ i ∈ indices,
        (qWeight i - pWeight i) *
          (informativeP i - misinformativeP i)| ≤
      l1Bound * upperBound := by
  have hnet :
      ∀ i ∈ indices,
        -upperBound ≤ informativeP i - misinformativeP i ∧
          informativeP i - misinformativeP i ≤ upperBound := by
    intro i hi
    exact net_value_bounds_of_component_bounds
      (hinformative i hi) (hmisinformative i hi)
  have hbound :=
    abs_weight_change_against_bounded_values_le_half_range
      indices pWeight qWeight
      (fun i => informativeP i - misinformativeP i)
      hpSum hqSum (by linarith) hl1Nonnegative hnet hweightChange
  convert hbound using 1
  ring

/-- A component-valued finite average combines a pointwise change with the sharper component
half-range weight term. -/
theorem abs_component_average_change_le
    (indices : Finset ι)
    (pWeight qWeight componentP componentQ : ι → ℝ)
    {upperBound pointwiseBound l1Bound : ℝ}
    (hqNonnegative : ∀ i ∈ indices, 0 ≤ qWeight i)
    (hpSum : ∑ i ∈ indices, pWeight i = 1)
    (hqSum : ∑ i ∈ indices, qWeight i = 1)
    (hupperNonnegative : 0 ≤ upperBound)
    (hpointwiseNonnegative : 0 ≤ pointwiseBound)
    (hl1Nonnegative : 0 ≤ l1Bound)
    (hchange :
      ∀ i ∈ indices, |componentQ i - componentP i| ≤ pointwiseBound)
    (hcomponent :
      ∀ i ∈ indices, 0 ≤ componentP i ∧ componentP i ≤ upperBound)
    (hweightChange :
      ∑ i ∈ indices, |qWeight i - pWeight i| ≤ l1Bound) :
    |(∑ i ∈ indices, qWeight i * componentQ i) -
        ∑ i ∈ indices, pWeight i * componentP i| ≤
      pointwiseBound + l1Bound * upperBound / 2 := by
  simpa using
    abs_weighted_average_change_le_pointwise_plus_half_range
      indices pWeight qWeight componentP componentQ
      hqNonnegative hpSum hqSum hupperNonnegative
      hpointwiseNonnegative hl1Nonnegative hchange hcomponent hweightChange

/-- A signed-net finite average combines a pointwise change with the full `L1-change * upperBound`
weight term implied by two bounded components. -/
theorem abs_net_average_change_le
    (indices : Finset ι)
    (pWeight qWeight informativeP misinformativeP netQ : ι → ℝ)
    {upperBound pointwiseBound l1Bound : ℝ}
    (hqNonnegative : ∀ i ∈ indices, 0 ≤ qWeight i)
    (hpSum : ∑ i ∈ indices, pWeight i = 1)
    (hqSum : ∑ i ∈ indices, qWeight i = 1)
    (hupperNonnegative : 0 ≤ upperBound)
    (hpointwiseNonnegative : 0 ≤ pointwiseBound)
    (hl1Nonnegative : 0 ≤ l1Bound)
    (hchange :
      ∀ i ∈ indices,
        |netQ i - (informativeP i - misinformativeP i)| ≤ pointwiseBound)
    (hinformative :
      ∀ i ∈ indices, 0 ≤ informativeP i ∧ informativeP i ≤ upperBound)
    (hmisinformative :
      ∀ i ∈ indices, 0 ≤ misinformativeP i ∧ misinformativeP i ≤ upperBound)
    (hweightChange :
      ∑ i ∈ indices, |qWeight i - pWeight i| ≤ l1Bound) :
    |(∑ i ∈ indices, qWeight i * netQ i) -
        ∑ i ∈ indices,
          pWeight i * (informativeP i - misinformativeP i)| ≤
      pointwiseBound + l1Bound * upperBound := by
  have hnet :
      ∀ i ∈ indices,
        -upperBound ≤ informativeP i - misinformativeP i ∧
          informativeP i - misinformativeP i ≤ upperBound := by
    intro i hi
    exact net_value_bounds_of_component_bounds
      (hinformative i hi) (hmisinformative i hi)
  have hbound :=
    abs_weighted_average_change_le_pointwise_plus_half_range
      indices pWeight qWeight
      (fun i => informativeP i - misinformativeP i) netQ
      hqNonnegative hpSum hqSum (by linarith)
      hpointwiseNonnegative hl1Nonnegative hchange hnet hweightChange
  convert hbound using 1
  ring

/-- A component average of one fixed linear row obeys the row-transferred coordinate bound plus
the component half-range weight term. The component range remains an explicit premise. -/
theorem abs_component_linear_row_average_change_le
    (cells : Finset ι) (coordinates : Finset κ)
    (pWeight qWeight : ι → ℝ) (coefficient : κ → ℝ)
    (valueP valueQ : ι → κ → ℝ)
    {upperBound coordinateBound l1Bound : ℝ}
    (hqNonnegative : ∀ cell ∈ cells, 0 ≤ qWeight cell)
    (hpSum : ∑ cell ∈ cells, pWeight cell = 1)
    (hqSum : ∑ cell ∈ cells, qWeight cell = 1)
    (hupperNonnegative : 0 ≤ upperBound)
    (hcoordinateNonnegative : 0 ≤ coordinateBound)
    (hl1Nonnegative : 0 ≤ l1Bound)
    (hcoordinateChange :
      ∀ cell ∈ cells, ∀ coordinate ∈ coordinates,
        |valueQ cell coordinate - valueP cell coordinate| ≤ coordinateBound)
    (hcomponentRange :
      ∀ cell ∈ cells,
        0 ≤ ∑ coordinate ∈ coordinates,
            coefficient coordinate * valueP cell coordinate ∧
          (∑ coordinate ∈ coordinates,
            coefficient coordinate * valueP cell coordinate) ≤ upperBound)
    (hweightChange :
      ∑ cell ∈ cells, |qWeight cell - pWeight cell| ≤ l1Bound) :
    |(∑ cell ∈ cells, qWeight cell *
          ∑ coordinate ∈ coordinates,
            coefficient coordinate * valueQ cell coordinate) -
        ∑ cell ∈ cells, pWeight cell *
          ∑ coordinate ∈ coordinates,
            coefficient coordinate * valueP cell coordinate| ≤
      (∑ coordinate ∈ coordinates, |coefficient coordinate|) *
          coordinateBound +
        l1Bound * upperBound / 2 := by
  apply abs_component_average_change_le
    cells pWeight qWeight
    (fun cell =>
      ∑ coordinate ∈ coordinates,
        coefficient coordinate * valueP cell coordinate)
    (fun cell =>
      ∑ coordinate ∈ coordinates,
        coefficient coordinate * valueQ cell coordinate)
    hqNonnegative hpSum hqSum hupperNonnegative
    (mul_nonneg
      (Finset.sum_nonneg fun coordinate _ => abs_nonneg (coefficient coordinate))
      hcoordinateNonnegative)
    hl1Nonnegative
  · intro cell hcell
    exact abs_mobius_row_change_le_abs_row_sum
      coordinates coefficient (valueP cell) (valueQ cell)
      (hcoordinateChange cell hcell)
  · exact hcomponentRange
  · exact hweightChange

/-- A net average of one fixed linear row obeys the row-transferred coordinate bound plus the full
net weight term. The two reference-component ranges remain explicit premises. -/
theorem abs_net_linear_row_average_change_le
    (cells : Finset ι) (coordinates : Finset κ)
    (pWeight qWeight : ι → ℝ) (coefficient : κ → ℝ)
    (informativeP misinformativeP : ι → ℝ)
    (netCoordinateP netCoordinateQ : ι → κ → ℝ)
    {upperBound coordinateBound l1Bound : ℝ}
    (hqNonnegative : ∀ cell ∈ cells, 0 ≤ qWeight cell)
    (hpSum : ∑ cell ∈ cells, pWeight cell = 1)
    (hqSum : ∑ cell ∈ cells, qWeight cell = 1)
    (hupperNonnegative : 0 ≤ upperBound)
    (hcoordinateNonnegative : 0 ≤ coordinateBound)
    (hl1Nonnegative : 0 ≤ l1Bound)
    (hcoordinateChange :
      ∀ cell ∈ cells, ∀ coordinate ∈ coordinates,
        |netCoordinateQ cell coordinate - netCoordinateP cell coordinate| ≤
          coordinateBound)
    (hnetRowP :
      ∀ cell ∈ cells,
        (∑ coordinate ∈ coordinates,
          coefficient coordinate * netCoordinateP cell coordinate) =
            informativeP cell - misinformativeP cell)
    (hinformative :
      ∀ cell ∈ cells,
        0 ≤ informativeP cell ∧ informativeP cell ≤ upperBound)
    (hmisinformative :
      ∀ cell ∈ cells,
        0 ≤ misinformativeP cell ∧ misinformativeP cell ≤ upperBound)
    (hweightChange :
      ∑ cell ∈ cells, |qWeight cell - pWeight cell| ≤ l1Bound) :
    |(∑ cell ∈ cells, qWeight cell *
          ∑ coordinate ∈ coordinates,
            coefficient coordinate * netCoordinateQ cell coordinate) -
        ∑ cell ∈ cells, pWeight cell *
          ∑ coordinate ∈ coordinates,
            coefficient coordinate * netCoordinateP cell coordinate| ≤
      (∑ coordinate ∈ coordinates, |coefficient coordinate|) *
          coordinateBound +
        l1Bound * upperBound := by
  have hchange :
      ∀ cell ∈ cells,
        |(∑ coordinate ∈ coordinates,
            coefficient coordinate * netCoordinateQ cell coordinate) -
          (informativeP cell - misinformativeP cell)| ≤
        (∑ coordinate ∈ coordinates, |coefficient coordinate|) *
          coordinateBound := by
    intro cell hcell
    rw [← hnetRowP cell hcell]
    exact abs_mobius_row_change_le_abs_row_sum
      coordinates coefficient (netCoordinateP cell) (netCoordinateQ cell)
      (hcoordinateChange cell hcell)
  have hbound := abs_net_average_change_le
    cells pWeight qWeight informativeP misinformativeP
    (fun cell =>
      ∑ coordinate ∈ coordinates,
        coefficient coordinate * netCoordinateQ cell coordinate)
    hqNonnegative hpSum hqSum hupperNonnegative
    (mul_nonneg
      (Finset.sum_nonneg fun coordinate _ => abs_nonneg (coefficient coordinate))
      hcoordinateNonnegative)
    hl1Nonnegative hchange hinformative hmisinformative hweightChange
  convert hbound using 1
  · apply congrArg abs
    congr 1
    apply Finset.sum_congr rfl
    intro cell hcell
    rw [hnetRowP cell hcell]

/-- An event mass on the segment from `referenceMass` to `nearbyMass` has the factorized floor
`floorMass * (1 - time * error / (2 * floorMass))`. -/
theorem segment_event_mass_lower_bound_factorized
    {referenceMass nearbyMass floorMass error time : ℝ}
    (hfloor : 0 < floorMass)
    (hreference : floorMass ≤ referenceMass)
    (htimeNonnegative : 0 ≤ time)
    (hchange : |nearbyMass - referenceMass| ≤ error / 2) :
    floorMass * (1 - time * (error / (2 * floorMass))) ≤
      (1 - time) * referenceMass + time * nearbyMass := by
  have hlower :
      -(error / 2) ≤ nearbyMass - referenceMass :=
    neg_le_of_abs_le hchange
  have hscaled :
      time * (-(error / 2)) ≤
        time * (nearbyMass - referenceMass) :=
    mul_le_mul_of_nonneg_left hlower htimeNonnegative
  have hfactor :
      floorMass * (1 - time * (error / (2 * floorMass))) =
        floorMass + time * (-(error / 2)) := by
    field_simp
    ring
  rw [hfactor]
  nlinarith

/-- Under the strict support margin, the factorized segment floor is positive for every
`time ∈ [0, 1]`; hence so is the segment mass. -/
theorem segment_event_mass_positive_of_floor
    {referenceMass nearbyMass floorMass error time : ℝ}
    (hfloor : 0 < floorMass)
    (hreference : floorMass ≤ referenceMass)
    (herrorNonnegative : 0 ≤ error)
    (hstrict : error < 2 * floorMass)
    (htimeNonnegative : 0 ≤ time)
    (htimeUpper : time ≤ 1)
    (hchange : |nearbyMass - referenceMass| ≤ error / 2) :
    0 < (1 - time) * referenceMass + time * nearbyMass := by
  have hratioNonnegative : 0 ≤ error / (2 * floorMass) := by positivity
  have hratioLtOne : error / (2 * floorMass) < 1 := by
    exact (div_lt_one (by positivity)).2 hstrict
  have htimeRatioLtOne :
      time * (error / (2 * floorMass)) < 1 := by
    calc
      time * (error / (2 * floorMass))
          ≤ 1 * (error / (2 * floorMass)) :=
            mul_le_mul_of_nonneg_right htimeUpper hratioNonnegative
      _ < 1 := by simpa using hratioLtOne
  have hfactorPositive :
      0 < floorMass *
        (1 - time * (error / (2 * floorMass))) :=
    mul_pos hfloor (sub_pos.mpr htimeRatioLtOne)
  exact hfactorPositive.trans_le
    (segment_event_mass_lower_bound_factorized
      hfloor hreference htimeNonnegative hchange)

end PidFiniteConvergence
